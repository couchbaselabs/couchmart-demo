#!/usr/bin/env python
import random

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import BadRequest
from couchbase.cluster import Cluster
from couchbase.cluster import PasswordAuthenticator
import couchbase.fulltext as FT

app = Flask(__name__)

# Lab 2: Connect to the cluster
cluster = Cluster('couchbase://')
authenticator = PasswordAuthenticator('Administrator', 'password')
cluster.authenticate(authenticator)
bucket = cluster.open_bucket('couchmart')

@app.route('/', methods=['GET'])
def shop():
    # Lab 2: Retrieve items document from the bucket
    itemsDoc = bucket.get("items")
    items = bucket.get_multi(itemsDoc.value['items'])
    return render_template('shop.html', random=random, sorted=sorted,
                           items=items, display_url="")


@app.route('/submit_order', methods=['POST'])
def submit_order():
    name = request.form.get('name')
    order = request.form.getlist('order[]')

    # Lab 3: Insert the order document into the bucket
    #if len(order) != 5:
    #    raise BadRequest('Must have 5 items in the order')

    #key = "Order::{}::{}".format(data['name'],
    #                                 datetime.datetime.utcnow().isoformat())
    #    data['ts'] = int(time.time())
    #    data['type'] = "order"
    #    yield bucket.upsert(key, data)

    # TODO: Save the order to Couchbase
    print name, 'ordered', order
    return '', 204


@app.route('/filter', methods=['GET'])
def filter_items():
    filter_type = request.args.get('type')
    keys = []

    # Lab 4: Use N1QL to query the bucket
    result = bucket.n1ql_query(
        'SELECT meta().id FROM matt WHERE category = "{}"'.format(filter_type))
    for row in result:
        keys.append(row['id'])

    print 'Found results:', ', '.join(keys), 'for type', filter_type
    return jsonify({'keys': keys})


@app.route('/search', methods=['GET'])
def search():
    search_term = request.args.get('q')
    print 'User searched for', search_term
    keys = []

    # This is the part the user has to fill in
    # Bonus points for fuzzy searching
    # They can make this as simple or complex as they want
    result = bucket.search('matt', FT.MatchQuery(search_term, fuzziness=1))
    for row in result:
        keys.append(row['id'])

    print 'Found matches', ', '.join(keys)
    return jsonify({'keys': keys})

app.run(host='0.0.0.0',port=8080)
