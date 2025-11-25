#!/usr/bin/env python
import asyncio
import datetime
import time
from collections import deque
from datetime import timedelta
from urllib.parse import quote

import couchbase.search as search
import tornado.escape
import tornado.gen
import tornado.ioloop
import tornado.web
import tornado.websocket
from acouchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import CouchbaseException
from couchbase.management.views import DesignDocumentNamespace
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions,
                               GetOptions, ViewOptions, SearchOptions)
from couchbase.views import ViewOrdering

import cb_status
import settings

socket_list = []
bucket_name = settings.BUCKET_NAME
user = settings.USERNAME
password = settings.PASSWORD
nodes = ','.join(settings.AWS_NODES)
cb_cluster = None
cb_bucket = None
cb_default_scope = None
cb_default_collection = None
live_order_callback = None

fts_nodes = None
fts_enabled = False
nodes = []
n1ql_enabled = False
xdcr_enabled = False

RECENT_ORDERS = deque(maxlen=50)
NEXT_CUSTOMER = 0
LATEST_TS = None


class NodeStatusHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("www/index.html")


class CBStatusWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print(self)
        if self not in socket_list:
            socket_list.append(self)
            self.red = 255
            print("WebSocket opened")
            self.callback = tornado.ioloop.PeriodicCallback(
                self.get_node_status, 1000)
            self.callback.start()
            self.get_node_status()

    def on_message(self, message):
        print("on_message received:" + message)

    def on_close(self):
        print("WebSocket closed")
        self.callback.stop()

    def get_node_status(self):
        msg = {"nodes": nodes, 'fts': fts_enabled,
               'n1ql': n1ql_enabled, 'xdcr': xdcr_enabled}
        self.write_message(msg)


class LiveOrdersWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        if self not in socket_list:
            socket_list.append(self)
            print("WebSocket opened")

    def on_message(self, message):
        print("on_message received:" + message)

    def on_close(self):
        print("WebSocket closed")
        if live_order_callback is not None:
            live_order_callback.stop()


class ShopHandler(tornado.web.RequestHandler):
    async def get(self):
        items = await cb_default_collection.get("items")
        # get_multi is not supported in acouchbase
        # use ascyncio.gather instead
        coroutines = [cb_default_collection.get(key, GetOptions(timeout=timedelta(seconds=5))) for key in
                      items.value['items']]
        items = await asyncio.gather(*coroutines)

        self.render("www/shop.html", items=items)


class SubmitHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)

        # Someone has sent us an invalid order, send a 400
        if 'name' not in data or 'order' not in data or \
                ('order' in data and len(data['order']) != 5):
            self.send_error(400)
            return

        key = "Order::{}::{}".format(data['name'], datetime.datetime.now(datetime.UTC))
        data['ts'] = int(time.time())
        data['type'] = "order"
        yield cb_default_collection.upsert(key, data)


class SearchHandler(tornado.web.RequestHandler):
    async def get(self):
        try:
            query = self.get_query_argument('q')
            query = query.replace('"', r'')
            query = quote(query)
            terms = query.split()
            query = ' '.join(["{}~1".format(term) for term in terms])
            query = search.QueryStringQuery(query)
            request = search.SearchRequest.create(query)
            result = cb_default_scope.search('English', request)
            keys = [row.id async for row in result.rows()]

            self.write({'keys': keys})
        except CouchbaseException as ex:
            import traceback
            traceback.print_exc()


class FilterHandler(tornado.web.RequestHandler):
    async def get(self):
        data = self.get_query_argument('type')
        results = cb_cluster.query(
            'SELECT meta().id FROM {} WHERE category = "{}"'
            .format(bucket_name, data))

        final_results = []
        async for row in results.rows():
            final_results.append(row['id'])

        self.write({'keys': final_results})


@tornado.gen.coroutine
def update_cb_status():
    global nodes, fts_enabled, n1ql_enabled, xdcr_enabled, fts_nodes
    # Update the cached node info every 500ms
    while True:
        nodes = yield cb_status.get_node_status()
        n1ql_enabled = yield cb_status.n1ql_enabled()
        xdcr_enabled = yield cb_status.xdcr_enabled()
        fts_nodes = yield cb_status.fts_nodes()
        fts_enabled = yield cb_status.fts_enabled()
        yield tornado.gen.sleep(0.5)


def make_app():
    return tornado.web.Application([
        (r"/", ShopHandler),
        (r"/nodestatus", CBStatusWebSocket),
        (r"/liveorders", LiveOrdersWebSocket),
        (r'/nodes', NodeStatusHandler),
        (r'/submit_order', SubmitHandler),
        (r'/search', SearchHandler),
        (r'/filter', FilterHandler),
        # This is lazy, but will work fine for our purposes
        (r'/(.*)', tornado.web.StaticFileHandler, {'path': "./www/"}),
    ], debug=True)


async def run_view_query_broadcast():
    global NEXT_CUSTOMER, LATEST_TS, RECENT_ORDERS

    websocket = None
    for ws in socket_list:
        if isinstance(ws, LiveOrdersWebSocket):
            websocket = ws
            break
    if websocket is None:
        return

    options = ViewOptions(limit=50, order=ViewOrdering.ASCENDING,
                          namespace=DesignDocumentNamespace.PRODUCTION,
                          startkey=LATEST_TS)
    results = cb_bucket.view_query(settings.DDOC_NAME, settings.VIEW_NAME, options)
    new_order = False
    order_data = None

    async for order in results:
        new_order = True
        if order.document is not None:
            order_data = order.document
        else:
            query_res = await cb_default_collection.get(order.id)
            order_data = query_res.content_as[dict]

        RECENT_ORDERS.appendleft(order_data)
        print(order.key, order_data['name'])

    if new_order:
        NEXT_CUSTOMER = 0  # back to the start
        LATEST_TS = RECENT_ORDERS[0]['ts'] + 1
    elif NEXT_CUSTOMER >= (len(RECENT_ORDERS) - 1):
        NEXT_CUSTOMER = 0  # back to the start
    else:
        NEXT_CUSTOMER += 1

    if len(RECENT_ORDERS) > 0:
        display_order = RECENT_ORDERS[NEXT_CUSTOMER]
        msg = {"name": display_order['name'], "images": []}
        for prod in display_order['order']:
            msg['images'].append("./img/" + cb_status.get_image_for_product(prod))

        await websocket.write_message(msg)

        if display_order['name'] == 'Couchbase Demo Phone' and NEXT_CUSTOMER == 0:
            live_order_callback.stop()
            await tornado.gen.sleep(5)
            live_order_callback.start()


async def main():
    """Initializes services and starts the web server."""
    global cb_cluster, cb_bucket, cb_default_collection, live_order_callback, cb_default_scope

    # The `Cluster.connect` method is now a coroutine
    hosts = ','.join(settings.AWS_NODES)
    conn_str = f"couchbase://{hosts}"
    auth = PasswordAuthenticator(
        user,
        password,
    )
    timeout_opts = ClusterTimeoutOptions(connect_timeout=timedelta(seconds=15))
    cb_cluster = await Cluster.connect(conn_str, ClusterOptions(auth, timeout_options=timeout_opts))
    # It is recommended to wait for the connection to be ready
    await cb_cluster.wait_until_ready(timedelta(seconds=15))

    cb_bucket = cb_cluster.bucket(bucket_name)
    cb_default_collection = cb_bucket.default_collection()
    cb_default_scope = cb_bucket.default_scope()

    app = make_app()
    app.listen(8888)
    print("Server started on http://localhost:8888")

    tornado.ioloop.IOLoop.current().spawn_callback(update_cb_status)
    live_order_callback = tornado.ioloop.PeriodicCallback(run_view_query_broadcast, timedelta(seconds=5))
    live_order_callback.start()

    # Keep the application running
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.current().stop()
        print("\nServer shutting down.")
