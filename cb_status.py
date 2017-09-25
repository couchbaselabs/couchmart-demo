#!/usr/bin/env - python

import urllib, urllib2, cookielib, pprint, json, time, sys, codecs, base64, random
import settings
from create_dataset import PRODUCTS as PRODUCTS
from txcouchbase.bucket import Bucket
import tornado.escape
import tornado.gen
import tornado.httpclient
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

HOST="http://{}:8091".format(settings.NODES[0])
BUCKET_URL = HOST + "/pools/default/buckets"
NODE_URL = HOST + "/pools/default/serverGroups"
INDEX_URL = HOST + "/indexStatus"
SERVICE_URL = HOST + "/pools/default/nodeServices"
FTS_URL = "http://{}:8094/api/index/{}"
XDCR_URL = HOST + "/pools/default/remoteClusters"
USERNAME=settings.ADMIN_USER
PASSWORD=settings.ADMIN_PASS

bucket_name=settings.BUCKET_NAME
user=settings.USERNAME
password=settings.PASSWORD
if settings.AWS:
  node=settings.AWS_NODES[0]
else:
  node=settings.AZURE_NODES[0]
aws=settings.AWS
bucket=Bucket('couchbase://{0}/{1}'.format(node,bucket_name), username=user, password=password)
http_client = AsyncHTTPClient()

def getImageForProduct(product):
  for p in PRODUCTS:
    if p['name'] == product[8:]:   #8: is to chop off product:
      return p['image']
  return None

@tornado.gen.coroutine
def get_URL(target_url, raise_exception=False):
  while True:
    request = HTTPRequest(
      url=target_url,
      auth_username=USERNAME,
      auth_password=PASSWORD,
      auth_mode='basic', request_timeout=0.3)
    try:
      response = yield http_client.fetch(request)
      raise tornado.gen.Return(tornado.escape.json_decode(response.body))
    except tornado.httpclient.HTTPError as e:
      if raise_exception:
        raise
      print ("Could not retrieve URL: " + str(target_url) + str(e))
      yield tornado.gen.sleep(1)

# Returns a list of nodes and their statuses
@tornado.gen.coroutine
def getNodeStatus():
  default_status = { "hostname": "n/a", "ops": 0, "status": "out"}

  node_list = [dict(default_status) for x in range(5)]
  if not aws:
    raise tornado.gen.Return(node_list)

  kv_nodes = index = 0
  node_response = yield get_URL(NODE_URL)
  for node in node_response['groups'][0]['nodes']:
    if "kv" in node['services']:
      index = kv_nodes
      kv_nodes += 1
    elif "n1ql" in node['services']:
      index = 3
    elif "fts" in node['services']:
      index = 4
    node_list[index]['hostname'] = node['hostname']
    # First check for nodes that are fully fledged members of the cluster
    # And if they are KV nodes, check how many ops they're doing
    if node['status'] == "healthy" and node['clusterMembership'] == "active":
      node_list[index]['status'] = "ok"
      if "kv" in node['services'] and 'cmd_get' in node['interestingStats']:
        node_list[index]['ops'] = node['interestingStats']['cmd_get']
    # Check for cluster members that are unhealthy (in risk of being failed)
    # We will highlight these with a red border
    elif node['clusterMembership'] == "active" and \
         node['status'] == "unhealthy":
       node_list[index]['status'] = "trouble"
    # Then, nodes that are either failed over, warming up or not rebalanced in
    # These will appear as faded
    elif node['clusterMembership'] == "inactiveFailed" or \
         node['clusterMembership'] == "inactiveAdded" or \
         (node['clusterMembership'] == "active" and \
         node['status'] == "warmup"):
       node_list[index]['status'] = "dormant"
    # Any other status we'll just hide
    else:
      node_list[index]['status'] = "out"
  raise tornado.gen.Return(node_list)

@tornado.gen.coroutine
def fts_node():
  response = yield get_URL(SERVICE_URL)
  for node in response["nodesExt"]:
    if 'fts' in node['services']:
      raise tornado.gen.Return(node['hostname'])
  raise tornado.gen.Return(None)

@tornado.gen.coroutine
def fts_enabled():
  node_to_query = yield fts_node()
  if not node:
    raise tornado.gen.Return(False)

  try:
    response = yield get_URL(FTS_URL.format(node_to_query, 'English'),
                             raise_exception=True)
  except Exception:
    raise tornado.gen.Return(False)
  else:
    raise tornado.gen.Return(True)

@tornado.gen.coroutine
def n1ql_enabled():
  index_response = yield get_URL(INDEX_URL)
  raise tornado.gen.Return('indexes' in index_response and any(index['index'] == u'category' and index['status'] == u'Ready' for index in index_response['indexes']))


@tornado.gen.coroutine
def xdcr_enabled():
  if not aws:
    raise tornado.gen.Return(True)
  xdcr_response = yield get_URL(XDCR_URL)
  raise tornado.gen.Return(len(xdcr_response) > 0)


def main(args):
  while True:
    node_list = getNodeStatus()
    for node in node_list:
      if node['status'] == "broken":
        print "{0} has problems".format(node['hostname'])
      else:
        print "{0} is doing {1} ops".format(node['hostname'], node['ops'] )   
    time.sleep(5.0)


if __name__=='__main__':
  sys.exit(main(sys.argv))
