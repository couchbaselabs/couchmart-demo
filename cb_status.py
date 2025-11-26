#!/usr/bin/env - python
import os
import tornado.escape
import tornado.gen
import tornado.httpclient
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from couchbase.diagnostics import ServiceType

import config as settings
from cb_connection import cluster
from create_dataset import PRODUCTS as PRODUCTS

BUCKET_URL = "/pools/default/buckets"
NODE_URL = "/pools/default/serverGroups"
INDEX_URL = "/indexStatus"
SERVICE_URL = "/pools/default/nodeServices"
FTS_URL = "/api/index/couchmart._default.English"
XDCR_URL = "/pools/default/remoteClusters"
USERNAME = settings.ADMIN_USER
PASSWORD = settings.ADMIN_PASS

aws = settings.AWS
http_client = AsyncHTTPClient()
ping_result = cluster.ping()
server_nodes = []

if os.environ.get('DEBUG_LOGS') == 'true':
    print(f"DEBUG: Ping result: {ping_result.endpoints}")

for endpoint, reports in ping_result.endpoints.items():
    if endpoint == ServiceType.Management:
        for report in reports:
            server_nodes.append(report.remote)

if os.environ.get('DEBUG_LOGS') == 'true':
    print(f"DEBUG: Server nodes: {server_nodes}")
    if not server_nodes:
        print("WARNING: No server nodes found! 'get_url' might hang.")


def get_image_for_product(product):
    for p in PRODUCTS:
        if p['name'] == product[8:]:  # 8: is to chop off product:
            return p['image']
    return None


@tornado.gen.coroutine
def get_url(endpoint, host_list=server_nodes, raise_exception=False):
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
                print("Could not retrieve URL: " + str(target_url) + str(e))
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

    node_list = [dict(default_status) for _ in range(5)]
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
                # node comes from get_url and has 'http://' prefix, strip it
                hostname = node.replace('http://', '')
                fts_nodes.append(hostname)
            else:
                fts_nodes.append(node_info['hostname'])

    raise tornado.gen.Return(fts_nodes)


@tornado.gen.coroutine
def fts_enabled():
    nodes_to_query = yield fts_nodes()
    # Replace port 8091 with 8094 for FTS queries
    nodes_to_query = [
        node.replace(':8091', ':8094') if ':8091' in node else node + ':8094'
        for node in nodes_to_query
    ]
    if os.environ.get('DEBUG_LOGS') == 'true':
        print(f"DEBUG: FTS nodes to query: {nodes_to_query}")
        print(f"DEBUG: FTS_URL: {FTS_URL}")
    if not nodes_to_query:
        raise tornado.gen.Return(False)

    try:
        result = yield get_url(FTS_URL, host_list=nodes_to_query,
                      raise_exception=True)
        if os.environ.get('DEBUG_LOGS') == 'true':
            print(f"DEBUG: FTS query succeeded: {result}")
    except Exception as e:
        if os.environ.get('DEBUG_LOGS') == 'true':
            print(f"DEBUG: FTS query failed: {e}")
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
