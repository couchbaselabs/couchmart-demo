#!/usr/bin/env - python

import urllib, urllib2, cookielib, pprint, json, time, sys, codecs, base64, random
import settings
from create_dataset import PRODUCTS as PRODUCTS
from txcouchbase.bucket import Bucket

HOST="http://{}:8091".format(settings.NODES[0])
BUCKET_URL = HOST + "/pools/default/buckets"
NODE_URL = HOST + "/pools/default/serverGroups"
INDEX_URL = HOST + "/indexStatus"
SERVICE_URL = HOST + "/pools/default/nodeServices"
FTS_URL = "http://{}:8094/api/index/{}"
USERNAME=settings.ADMIN_USER
PASSWORD=settings.ADMIN_PASS
AUTH_STRING = base64.encodestring('%s:%s' % (USERNAME, PASSWORD)).replace('\n', '')

bucket_name=settings.BUCKET_NAME
user=settings.USERNAME
password=settings.PASSWORD
node=settings.NODES[0]
bucket=Bucket('couchbase://{0}/{1}'.format(node,bucket_name), username=user, password=password)

def getImageForProduct(product):
  for p in PRODUCTS:
    if p['name'] == product[8:]:   #8: is to chop off product:
      return p['image']
  return None


def get_URL(target_url, raise_exception=False):
  while True:
    try:
      req = urllib2.Request(target_url)
      req.add_header("Authorization", "Basic %s" % AUTH_STRING)   
      return urllib2.urlopen(req, timeout=0.1).read()
    except Exception as e:
      print ("Could not retrieve URL: " + str(target_url) + str(e))
      if raise_exception:
        raise
      time.sleep(1)

def getBucketStatus():
  bucket_response = json.loads(get_URL(BUCKET_URL))
  item_count = bucket_response[0]['basicStats']['itemCount']

# Returns a list of nodes and their statuses
def getNodeStatus():
  node_list = []
  node_response   = json.loads(get_URL(NODE_URL))
  for node in node_response['groups'][0]['nodes']:
    node_status = { "hostname": node['hostname'], "ops": 0}
    if node['status'] != "healthy" and node['clusterMembership'] == "active":
      node_status['status'] = "down"
    elif node['clusterMembership'] != "active":
       node_status['status'] = "failed"
    else:
      node_status['status'] = "ok"
      if "kv" in node['services']:
        node_status['ops'] = node['interestingStats']['cmd_get']

    node_list.append(node_status)    
  return node_list

def fts_node():
  response = json.loads(get_URL(SERVICE_URL))
  for node in response["nodesExt"]:
    if 'fts' in node['services']:
      return node['hostname']
  return None

def fts_enabled():
  node_to_query = fts_node()
  if not node:
    return False

  try:
    response = json.loads(get_URL(FTS_URL.format(node_to_query, 'English'), raise_exception=True))
  except Exception:
    return False
  else:
    return True

def n1ql_enabled():
  index_response = json.loads(get_URL(INDEX_URL))
  return 'indexes' in index_response and any(index['index'] == u'category' and index['status'] == u'Ready' for index in index_response['indexes'])


LAST_ORDER_QUERY=('SELECT META().id as order_id, name, `order` FROM `{}`'
                  'WHERE type = "order" AND name IS NOT MISSING AND `order` '
                  'IS NOT MISSING AND ts IS NOT MISSING ORDER by ts DESC LIMIT 1'.format(bucket_name))

def getLatestOrders():
    last_orders = yield bucket.n1qlQueryAll(LAST_ORDER_QUERY)
    for order in last_orders:
      msg = {"name": order['name'], "images" :[]}
      for prod in order['order']:
        msg['images'].append("./img/"+getImageForProduct(prod))
    yield msg
    return


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