#!/usr/bin/env - python

import urllib, urllib2, cookielib, pprint, json, time, sys, codecs, base64
import settings

HOST="http://{}:8091".format(settings.NODES[0])
BUCKET_URL = HOST + "/pools/default/buckets"
NODE_URL =   HOST + "/pools/default/serverGroups"
USERNAME=settings.ADMIN_USER
PASSWORD=settings.ADMIN_PASS
AUTH_STRING = base64.encodestring('%s:%s' % (USERNAME, PASSWORD)).replace('\n', '')


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