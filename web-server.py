#!/usr/bin/env python
import tornado.gen
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.platform.twisted
tornado.platform.twisted.install()
import time,random,datetime
from txcouchbase.bucket import Bucket

from tornado.ioloop import PeriodicCallback

import cb_status
import settings

IMAGE_LIST=["apples.png", "bonbons.png", "carambar.png", "cookie.png", "ham.png", "red_wine.png", "water.png", 
"bacon.png", "bread.png", "champagne.png", "crisps.png", "milk.png", "sausages.png", "whisky.png", "bananas.png", 
"burger.png", "cheese.png", "eggs.png", "oranges.png", "beer.png", "butter.png", "chocolate.png", "fish_fingers.png",
"pineapple.png", "strawberries.png"]


class MainHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("www/index.html")
    print "Got one"

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
      self.callback = tornado.ioloop.PeriodicCallback(self.getNodeStatus,5000)
      self.callback.start()

  def on_message(self, message):
    print "on_message received:" + message

  def on_close(self):
    print("WebSocket closed")
    self.callback.stop()

  def getNodeStatus(self):
    resp = cb_status.getNodeStatus()
    msg = {"nodes": resp}
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

  def send_orders(self):
    msg = {"name": "Billy", "images" :[]}
    for i in xrange(5):
      index = random.randint(0,len(IMAGE_LIST)-1)
      msg['images'].append("./img/"+IMAGE_LIST[index])
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
    yield bucket.upsert(key, data)

def make_app():
  return tornado.web.Application([
    (r"/", MainHandler),
    (r"/socket", CBStatusWebSocket),
    (r"/liveorders", LiveOrdersWebSocket),
    (r'/shop', ShopHandler),
    (r'/submit_order', SubmitHandler),
    (r'/(.*)', tornado.web.StaticFileHandler, {'path': "./www/"}),
    ], debug=True)

if __name__ == "__main__":
  print "Running at http://localhost:8888"
  app = make_app()
  app.listen(8888)
  tornado.ioloop.IOLoop.current().start()