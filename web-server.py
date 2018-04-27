#!/usr/bin/env python
import random

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import BadRequest
from couchbase.bucket import Bucket
import couchbase.fulltext as FT

app = Flask(__name__)

# This is step 1, connect to the bucket
bkt = Bucket('couchbase://localhost/couchmart', username='Adminstrator', password='password')


@app.route('/', methods=['GET'])
def shop():
    # This is the bit the user has to fill in to get the items
    items = bkt.get("items")
    items = bkt.get_multi(items.value['items'])
    return render_template('shop.html', random=random, sorted=sorted,
                           items=items, display_url="")


@app.route('/submit_order', methods=['POST'])
def submit_order():
    name = request.form.get('name')
    order = request.form.getlist('order[]')

    if len(order) != 5:
        raise BadRequest('Must have 5 items in the order')

    # TODO: Save the order to Couchbase
    print name, 'ordered', order
    return '', 204


@app.route('/filter', methods=['GET'])
def filter_items():
    filter_type = request.args.get('type')
    keys = []

    # This is the bit the user would have to fill in
    result = bkt.n1ql_query(
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
    result = bkt.search('matt', FT.MatchQuery(search_term, fuzziness=1))
    for row in result:
        keys.append(row['id'])

    print 'Found matches', ', '.join(keys)
    return jsonify({'keys': keys})

app.run(host='0.0.0.0',port=8080)
