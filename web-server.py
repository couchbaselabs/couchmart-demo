#!/usr/bin/env - python

import tornado.ioloop
import tornado.web
import tornado.websocket
import time,random
from tornado.ioloop import PeriodicCallback

import cb_status

IMAGE_LIST=["apples.png", "bonbons.png", "carambar.png", "cookie.png", "ham.png", "red_wine.png", "water.png", 
"bacon.png", "bread.png", "champagne.png", "crisps.png", "milk.png", "sausages.png", "whisky.png", "bananas.png", 
"burger.png", "cheese.png", "eggs.png", "oranges.png", "beer.png", "butter.png", "chocolate.png", "fish_fingers.png",
"pineapple.png", "strawberries.png"]


class MainHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("www/index.html")
    print "Got one"

socket_list = []

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

def make_app():
  return tornado.web.Application([
    (r"/", MainHandler),
    (r"/socket", CBStatusWebSocket),
    (r"/liveorders", LiveOrdersWebSocket),
    (r'/(.*)', tornado.web.StaticFileHandler, {'path': "./www/"}),
    ])

if __name__ == "__main__":
  print "Running at http://localhost:8888"
  app = make_app()
  app.listen(8888)
  tornado.ioloop.IOLoop.current().start()