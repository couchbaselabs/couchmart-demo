#!/usr/bin/env - python

import urllib, urllib2, cookielib, pprint, json, time, sys, codecs

HOST="http://10.142.162.101:8091"
BUCKET_URL = HOST + "/pools/default/buckets"
NODE_URL =   HOST + "/pools/nodes"



def get_URL(target_url):
  while True:
    try:
      req = urllib2.Request(target_url)
      return urllib2.urlopen(req, timeout=0.1).read()
    except Exception as e:
      print ("Could not retrieve URL: " + str(target_url) + str(e))
      time.sleep(1)




def main(args):
  while True:
    bucket_response = json.loads(get_URL(BUCKET_URL))
    node_response   = json.loads(get_URL(NODE_URL))
    item_count = bucket_response[0]['basicStats']['itemCount']
    print "Charlie has {0} items".format(item_count)
    for node in node_response['nodes']:
      print "{0} is {1}".format(node['hostname'], node['status'])
    time.sleep(0.1)


if __name__=='__main__':
  sys.exit(main(sys.argv))