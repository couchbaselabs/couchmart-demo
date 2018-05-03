#!/usr/bin/env python
import random
import datetime
import time

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import BadRequest
from couchbase.cluster import Cluster
from couchbase.cluster import PasswordAuthenticator
import couchbase.fulltext as FT
import couchbase.exceptions as E

app = Flask(__name__)

# Lab 2: Connect to the cluster
cluster = Cluster('couchbase://<Couchbase node>')
authenticator = PasswordAuthenticator('Administrator', 'password')
cluster.authenticate(authenticator)
bucket = cluster.open_bucket('couchmart')

@app.route('/', methods=['GET'])
def shop():
    # Lab 2: Retrieve items document from the bucket
    itemsDoc = bucket.get("items")
    items = bucket.get_multi(itemsDoc.value['items'])

    return render_template('shop.html', random=random, sorted=sorted,
                           display_url="", items=items)


@app.route('/submit_order', methods=['POST'])
def submit_order():
    name = request.form.get('name')
    order = request.form.getlist('order[]')
    print 'name=', name
    print 'order=', order

    if len(order) != 5:
        raise BadRequest('Must have 5 items in the order')

    # Lab 3: Insert the order document into the bucket
    key = "Order::{}::{}".format(name,
                                 datetime.datetime.utcnow().isoformat())
    data = {
        'type':'order',
        'name':name,
        'ts':int(time.time()),
        'order':order
    }
    print 'key=', key, '- data=', data
    try:
        bucket.upsert(key, data)
    except E:
        raise BadRequest('Failed to submit order')

    return '', 204


@app.route('/filter', methods=['GET'])
def filter_items():
    filter_type = request.args.get('type')
    keys = []
    print 'type=', filter_type

    # Lab 4: Use N1QL to retrieve products that match the requested category
    result = bucket.n1ql_query(
        'SELECT meta().id FROM couchmart WHERE category = "{}"'
           .format(filter_type))
    for row in result:
        keys.append(row['id'])

    print 'Found results:', ', '.join(keys), 'for type', filter_type
    return jsonify({'keys': keys})


@app.route('/search', methods=['GET'])
def search():
    search_term = request.args.get('q')
    print 'User searched for', search_term
    keys = []

    # Lab 5: Use the English FTS index to search with the term provided
    result = bucket.search('English', FT.MatchQuery(search_term, fuzziness=1))
    for row in result:
        keys.append(row['id'])

    print 'Found matches', ', '.join(keys)
    return jsonify({'keys': keys})

app.run(host='0.0.0.0',port=8080)
