#!/usr/bin/env - python

import tornado.ioloop
import tornado.web
import tornado.websocket
import time,random
from tornado.ioloop import PeriodicCallback



class MainHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("index.html")
    print "Got one"

socket_list = []

class CBStatusWebSocket(tornado.websocket.WebSocketHandler):
  def open(self):
    print self
    if self not in socket_list:
      socket_list.append(self)
      self.red = 255
      print("WebSocket opened")
      self.callback = tornado.ioloop.PeriodicCallback(self.change_colour,1000)
      self.callback.start()

  def on_message(self, message):
    print "on_message received:" + message

  def on_close(self):
    print("WebSocket closed")
    self.callback.stop()

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


def make_app():
  return tornado.web.Application([
    (r"/", MainHandler),
    (r'/js/(.*)', tornado.web.StaticFileHandler, {'path': "./js/"}),
    (r"/socket", CBStatusWebSocket),
    ])

if __name__ == "__main__":
  app = make_app()
  app.listen(8888)
  tornado.ioloop.IOLoop.current().start()