#!/usr/bin/env python
import tornado.gen
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.platform.twisted
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import urllib
tornado.platform.twisted.install()
import time,random,datetime
from txcouchbase.bucket import Bucket

from tornado.ioloop import PeriodicCallback

import cb_status
import settings

class NodeStatusHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("www/index.html")

socket_list = []
bucket_name=settings.BUCKET_NAME
user=settings.USERNAME
password=settings.PASSWORD
node=settings.NODES[0]
bucket=Bucket('couchbase://{0}/{1}'.format(node,bucket_name), username=user, password=password)

class CBStatusWebSocket(tornado.websocket.WebSocketHandler):
  def open(self):
    print self
    if self not in socket_list:
      socket_list.append(self)
      self.red = 255
      print("WebSocket opened")
      self.callback = tornado.ioloop.PeriodicCallback(self.getNodeStatus,1000)
      self.callback.start()
      self.getNodeStatus()

  def on_message(self, message):
    print "on_message received:" + message

  def on_close(self):
    print("WebSocket closed")
    self.callback.stop()

  def getNodeStatus(self):
    nodes = cb_status.getNodeStatus()
    fts_enabled = cb_status.fts_enabled()
    n1ql_enabled = cb_status.n1ql_enabled()
    msg = {"nodes": nodes, 'fts': fts_enabled, 'n1ql': n1ql_enabled}
    self.write_message(msg)

  def change_colour(self):
    self.red = random.randint(0,255)
    self.green = random.randint(0,255)
    self.blue = random.randint(0,255)

    col =  '#%02x%02x%02x' % (self.red, self.green, self.blue)
    status_cols = {'node1': col,
                   'node2': "#FFFF00",
                   'node3': "#FF00FF",
                   'node4': "#FFFFFF",
                  }
    self.write_message(status_cols)


class LiveOrdersWebSocket(tornado.websocket.WebSocketHandler):
  def open(self):
    print self
    if self not in socket_list:
      socket_list.append(self)
      self.red = 255
      print("WebSocket opened")
      self.callback = tornado.ioloop.PeriodicCallback(self.send_orders,5000)
      self.callback.start()

  def on_message(self, message):
    print "on_message received:" + message

  def on_close(self):
    print("WebSocket closed")
    self.callback.stop()

  LAST_ORDER_QUERY=("SELECT META(charlie).id as order_id, name, `order`" 
                  "FROM charlie WHERE type == \"order\" "
                  "ORDER by ts DESC LIMIT 1")
  @tornado.gen.coroutine
  def send_orders(self):
    last_orders = yield bucket.n1qlQueryAll(self.LAST_ORDER_QUERY)
    for order in last_orders:
      msg = {"name": order['name'], "images" :[]}
      for prod in order['order']:
        msg['images'].append("./img/"+cb_status.getImageForProduct(prod))
    self.write_message(msg)  
    
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
    if 'name' not in data or 'order' not in data or \
            ('order' in data and len(data['order']) != 5):
      self.send_error(400)
      return

    key = "Order::{}::{}".format(data['name'], datetime.datetime.utcnow().isoformat())
    data['ts'] = int(time.time())
    data['type'] = "order"
    yield bucket.upsert(key, data)

class SearchHandler(tornado.web.RequestHandler):
  http_client = AsyncHTTPClient()

  @tornado.gen.coroutine
  def get(self):
    query = self.get_query_argument('q')
    query = query.replace('"', r'')
    query = urllib.quote(query)
    terms = query.split()
    query = ' '.join(["{}~1".format(term) for term in terms])
    data = '{"query": {"query": "' + query + '"}, "highlight": null, "fields": null, "facets": null, "explain": false}'
    request = HTTPRequest(url='http://{}:8094/api/index/English/query'.format(node), method='POST',
                          body=data, auth_username='Administrator', auth_password='password', auth_mode='basic', user_agent="test",
                          headers={'Content-Type': 'application/json'})
    response = yield self.http_client.fetch(request)

    response = tornado.escape.json_decode(response.body)

    final_results = []
    for hit in response['hits']:
      final_results.append(hit['id'])

    self.write({'keys': final_results})

class FilterHandler(tornado.web.RequestHandler):
  @tornado.gen.coroutine
  def get(self):
    data = self.get_query_argument('type')
    results = yield bucket.n1qlQueryAll('SELECT meta().id FROM {} WHERE category = "{}"'
                                        .format(bucket_name, data))
    final_results=[]
    for row in results:
      final_results.append(row['id'])

    self.write({'keys': final_results})


def make_app():
  return tornado.web.Application([
    (r"/", ShopHandler),
    (r"/nodestatus", CBStatusWebSocket),
    (r"/liveorders", LiveOrdersWebSocket),
    (r'/nodes', NodeStatusHandler),
    (r'/submit_order', SubmitHandler),
    (r'/search', SearchHandler),
    (r'/filter', FilterHandler),
    (r'/(.*)', tornado.web.StaticFileHandler, {'path': "./www/"}),
    ], debug=True)

if __name__ == "__main__":
  print "Running at http://localhost:8888"
  app = make_app()
  app.listen(8888)
  tornado.ioloop.IOLoop.current().start()