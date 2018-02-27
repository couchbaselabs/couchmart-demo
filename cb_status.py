#!/usr/bin/env - python

import tornado.escape
import tornado.gen
import tornado.httpclient
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from txcouchbase.bucket import Bucket

import settings
from create_dataset import PRODUCTS as PRODUCTS

if settings.AWS:
    BOOTSTRAP_NODES = settings.AWS_NODES
else:
    BOOTSTRAP_NODES = settings.AZURE_NODES

BUCKET_URL = "/pools/default/buckets"
NODE_URL = "/pools/default/serverGroups"
INDEX_URL = "/indexStatus"
SERVICE_URL = "/pools/default/nodeServices"
FTS_URL = "/api/index/English"
XDCR_URL = "/pools/default/remoteClusters"
USERNAME = settings.ADMIN_USER
PASSWORD = settings.ADMIN_PASS

bucket_name = settings.BUCKET_NAME
user = settings.USERNAME
password = settings.PASSWORD

aws = settings.AWS
bucket = Bucket('couchbase://{0}/{1}'.format(",".join(BOOTSTRAP_NODES),
                                             bucket_name),
                username=user,
                password=password)
http_client = AsyncHTTPClient()


def get_image_for_product(product):
    for p in PRODUCTS:
        if p['name'] == product[8:]:  # 8: is to chop off product:
            return p['image']
    return None


@tornado.gen.coroutine
def get_url(endpoint, host_list=bucket.server_nodes, raise_exception=False):
    exceptions = []
    while True:
        for host in host_list:
            host = "http://" + host
            target_url = host + endpoint
            request = HTTPRequest(
                url=target_url,
                auth_username=USERNAME,
                auth_password=PASSWORD,
                auth_mode='basic', request_timeout=0.3)
            try:
                response = yield http_client.fetch(request)
                raise tornado.gen.Return((tornado.escape.json_decode(response.body), host))
            except tornado.httpclient.HTTPError as e:
                print ("Could not retrieve URL: " + str(target_url) + str(e))
                exceptions.append(e)

        if exceptions == len(host_list) and raise_exception:
            raise exceptions[0]
        else:
            exceptions = []

        yield tornado.gen.sleep(1)


# Returns a list of nodes and their statuses
@tornado.gen.coroutine
def get_node_status():
    default_status = {"hostname": "n/a", "ops": 0, "status": "out"}

    node_list = [dict(default_status) for _ in xrange(5)]
    if not aws:
        node_list[0]['ops'] = 400
        raise tornado.gen.Return(node_list)

    kv_nodes = index = 0
    node_response, _ = yield get_url(NODE_URL)

    for node_info in node_response['groups'][0]['nodes']:
        if "kv" in node_info['services']:
            index = kv_nodes
            kv_nodes += 1
        elif "n1ql" in node_info['services']:
            index = 3
        elif "fts" in node_info['services']:
            index = 4
        node_list[index]['hostname'] = node_info['hostname']
        # First check for nodes that are fully fledged members of the cluster
        # And if they are KV nodes, check how many ops they're doing
        if node_info['status'] == "healthy" and node_info[
            'clusterMembership'] == "active":
            node_list[index]['status'] = "ok"
            if "kv" in node_info['services'] and 'cmd_get' in node_info[
                'interestingStats']:
                node_list[index]['ops'] = node_info['interestingStats']['cmd_get']
        # Check for cluster members that are unhealthy (in risk of being failed)
        # We will highlight these with a red border
        elif node_info['clusterMembership'] == "active" and \
                        node_info['status'] == "unhealthy":
            node_list[index]['status'] = "trouble"
        # Then, nodes that are either failed over, warming up or not rebalanced in
        # These will appear as faded
        elif node_info['clusterMembership'] == "inactiveFailed" or \
                        node_info['clusterMembership'] == "inactiveAdded" or \
                (node_info['clusterMembership'] == "active" and
                         node_info['status'] == "warmup"):
            node_list[index]['status'] = "dormant"
        # Any other status we'll just hide
        else:
            node_list[index]['status'] = "out"
    raise tornado.gen.Return(node_list)


@tornado.gen.coroutine
def fts_nodes():
    response, node = yield get_url(SERVICE_URL)
    fts_nodes = []
    for node_info in response["nodesExt"]:
        if 'fts' in node_info['services']:
            if 'thisNode' in node_info and node_info['thisNode']:
                fts_nodes.append(node)
            else:
                fts_nodes.append(node_info['hostname'])

    raise tornado.gen.Return(fts_nodes)


@tornado.gen.coroutine
def fts_enabled():
    nodes_to_query = yield fts_nodes()
    nodes_to_query = ["{}:8094".format(node) for node in nodes_to_query]
    if not nodes_to_query:
        raise tornado.gen.Return(False)

    try:
        yield get_url(FTS_URL, host_list=nodes_to_query,
                      raise_exception=True)
    except Exception:
        raise tornado.gen.Return(False)
    else:
        raise tornado.gen.Return(True)


@tornado.gen.coroutine
def n1ql_enabled():
    index_response, _ = yield get_url(INDEX_URL)
    raise tornado.gen.Return('indexes' in index_response and any(
        index['index'] == u'category' and index['status'] == u'Ready' for index
        in index_response['indexes']))


@tornado.gen.coroutine
def xdcr_enabled():
    if not aws:
        raise tornado.gen.Return(True)
    xdcr_response, _ = yield get_url(XDCR_URL)
    raise tornado.gen.Return(len(xdcr_response) > 0)
