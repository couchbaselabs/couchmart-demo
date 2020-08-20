#!/usr/bin/env python
from collections import deque
import datetime
import random
import time
import urllib

import tornado.gen
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.platform.twisted
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

#install this before importing anything else, or VERY BAD THINGS happen
tornado.platform.twisted.install()

from txcouchbase.bucket import Bucket

import cb_status
import settings


socket_list = []
bucket_name = settings.BUCKET_NAME
user = settings.USERNAME
password = settings.PASSWORD
nodes = ','.join(settings.AWS_NODES)

bucket = Bucket('couchbase://{0}/{1}'.format(nodes, bucket_name),
                username=user, password=password)
fts_nodes = None
fts_enabled = False
nodes = []
n1ql_enabled = False
xdcr_enabled = False


class NodeStatusHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("www/index.html")


class CBStatusWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print self
        if self not in socket_list:
            socket_list.append(self)
            self.red = 255
            print("WebSocket opened")
            self.callback = tornado.ioloop.PeriodicCallback(
                self.get_node_status, 1000)
            self.callback.start()
            self.get_node_status()

    def on_message(self, message):
        print "on_message received:" + message

    def on_close(self):
        print("WebSocket closed")
        self.callback.stop()

    def get_node_status(self):
        msg = {"nodes": nodes, 'fts': fts_enabled,
               'n1ql': n1ql_enabled, 'xdcr': xdcr_enabled}
        self.write_message(msg)


class LiveOrdersWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.RECENT_ORDERS = deque(maxlen=50)
        self.NEXT_CUSTOMER = 0
        self.LATEST_TS = 0
        if self not in socket_list:
            socket_list.append(self)
            print("WebSocket opened")
            self.callback = tornado.ioloop.PeriodicCallback(self.send_orders,
                                                            5000)
            self.callback.start()

    def on_message(self, message):
        print "on_message received:" + message

    def on_close(self):
        print("WebSocket closed")
        self.callback.stop()

    @tornado.gen.coroutine
    def send_orders(self):
        res = yield bucket.queryAll(settings.DDOC_NAME, settings.VIEW_NAME,
                                    include_docs=True, descending=False, limit=50,
                                    startkey=self.LATEST_TS, stale=False)
        new_order = False
        for order in res:
            new_order = True
            self.RECENT_ORDERS.appendleft(order.doc.value)
            print order.key, order.doc.value['name']

        if new_order:
            self.NEXT_CUSTOMER = 0  # back to the start
            self.LATEST_TS = self.RECENT_ORDERS[0]['ts'] + 1
        elif self.NEXT_CUSTOMER >= (len(self.RECENT_ORDERS) - 1):
            self.NEXT_CUSTOMER = 0  # back to the start
        else:
            self.NEXT_CUSTOMER += 1

        if len(self.RECENT_ORDERS) > 0:
            display_order = self.RECENT_ORDERS[self.NEXT_CUSTOMER]
            msg = {"name": display_order['name'], "images": []}
            for prod in display_order['order']:
                msg['images'].append("./img/" + cb_status.get_image_for_product(prod))
            self.write_message(msg)
            if display_order['name'] == 'Couchbase Demo Phone' and self.NEXT_CUSTOMER == 0:
                self.callback.stop()
                yield tornado.gen.sleep(5)
                self.callback.start()


class ShopHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        items = yield bucket.get("items")
        items = yield bucket.get_multi(items.value['items'])
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

        key = "Order::{}::{}".format(data['name'],
                                     datetime.datetime.utcnow().isoformat())
        data['ts'] = int(time.time())
        data['type'] = "order"
        yield bucket.upsert(key, data)


class SearchHandler(tornado.web.RequestHandler):
    http_client = AsyncHTTPClient()

    @tornado.gen.coroutine
    def get(self):

        if fts_nodes:
            query = self.get_query_argument('q')
            query = query.replace('"', r'')
            query = urllib.quote(query)
            terms = query.split()
            query = ' '.join(["{}~1".format(term) for term in terms])
            data = '{"query": {"query": "' + query + '"}, "highlight": null, "fields": null, "facets": null, "explain": false}'
            fts_node = random.choice(fts_nodes)
            request = HTTPRequest(
                url='http://{}:8094/api/index/English/query'.format(fts_node),
                method='POST', body=data, auth_username=settings.ADMIN_USER,
                auth_password=settings.ADMIN_PASS, auth_mode='basic',
                headers={'Content-Type': 'application/json'})
            response = yield self.http_client.fetch(request)

            response = tornado.escape.json_decode(response.body)

            final_results = []
            for hit in response['hits']:
                final_results.append(hit['id'])

            self.write({'keys': final_results})
        else:
            raise Exception('No FTS node found')


class FilterHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        data = self.get_query_argument('type')
        results = yield bucket.n1qlQueryAll(
            'SELECT meta().id FROM {} WHERE category = "{}"'
            .format(bucket_name, data))

        final_results = []
        for row in results:
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


if __name__ == "__main__":
    print "Running at http://localhost:8888"
    app = make_app()
    app.listen(8888)

    tornado.ioloop.IOLoop.current().spawn_callback(update_cb_status)
    tornado.ioloop.IOLoop.current().start()
