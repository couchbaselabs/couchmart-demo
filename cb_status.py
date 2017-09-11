#!/usr/bin/env - python

import urllib, urllib2, cookielib, pprint, json, time, sys, codecs, base64
import settings
from create_dataset import PRODUCTS as PRODUCTS
from couchbase.bucket import Bucket


HOST="http://{}:8091".format(settings.NODES[0])
BUCKET_URL = HOST + "/pools/default/buckets"
NODE_URL =   HOST + "/pools/default/serverGroups"
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


def get_URL(target_url):
  while True:
    try:
      req = urllib2.Request(target_url)
      req.add_header("Authorization", "Basic %s" % AUTH_STRING)   
      return urllib2.urlopen(req, timeout=0.1).read()
    except Exception as e:
      print ("Could not retrieve URL: " + str(target_url) + str(e))
      time.sleep(1)

def getBucketStatus():
  bucket_response = json.loads(get_URL(BUCKET_URL))
  item_count = bucket_response[0]['basicStats']['itemCount']

# Returns a list of nodes and their statuses
def getNodeStatus():
  node_list = []
  node_response   = json.loads(get_URL(NODE_URL))
  for node in node_response['groups'][0]['nodes']:
    node_status = { "hostname": node['hostname'] }
    if node['status'] != "healthy" or node['clusterMembership'] != "active":
      node_status['status'] = "broken"
      node_status['ops'] = 0
    else:
      node_status['status'] = "ok"
      node_status['ops'] = node['interestingStats']['cmd_get']
    node_list.append(node_status)    
  return node_list

def fts_enabled():
  bucket_response = json.loads(get_URL(BUCKET_URL))
  return any('fts' in node['services'] for bucket in bucket_response for node in bucket["nodes"])

LAST_ORDER_QUERY=("SELECT META(charlie).id as order_id, name, `order`" 
                  "FROM charlie WHERE type == \"order\" "
                  "ORDER by ts DESC LIMIT 1")

def getLatestOrders():
    last_orders =  bucket.n1ql_query(LAST_ORDER_QUERY)
    for order in last_orders:
      msg = {"name": order['name'], "images" :[]}
      for prod in order['order']:
        msg['images'].append("./img/"+getImageForProduct(prod))
    return msg


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