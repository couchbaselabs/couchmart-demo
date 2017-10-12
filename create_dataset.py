#!/usr/bin/env - python
from __future__ import print_function

from couchbase.bucket import Bucket
import settings
import random

bucket_name = settings.BUCKET_NAME
user = settings.USERNAME
password = settings.PASSWORD
if settings.AWS:
    node = settings.AWS_NODES[0]
else:
    node = settings.AZURE_NODES[0]

SDK_CLIENT = Bucket('couchbase://{0}/{1}'.format(node, bucket_name),
                    username=user, password=password)

SDK_CLIENT.timeout = 15

LIST_DOC = "david.all_the_products"

PRODUCTS = [
    {"name": "burger", "description": "Mmmm. That IS a tasty burger",
     "price": 1.00, "category": "meat", "image": "burger.png", "stock": 100},
    {"name": "ham", "description": "Du jambon", "price": 1.00,
     "category": "meat", "image": "ham.png", "stock": 100},
    {"name": "sausages", "description": "A string of bangers",
     "price": 1.00, "category": "meat", "image": "sausages.png", "stock": 100},
    {"name": "water", "description": "h20", "price": 1.00,
     "category": "drinks", "image": "water.png", "stock": 100},
    {"name": "champagne", "description": "Lovely bubbly", "price": 1.00,
     "category": "drinks", "image": "champagne.png", "stock": 100},
    {"name": "red wine", "description": "Vin Rouge", "price": 1.00,
     "category": "drinks", "image": "red_wine.png", "stock": 100},
    {"name": "beer", "description": "amber nectar", "price": 1.00,
     "category": "drinks", "image": "beer.png", "stock": 100},
    {"name": "cookie", "description": "chocloate chip", "price": 1.00,
     "category": "snacks", "image": "cookie.png", "stock": 100},
    {"name": "chocolate", "description": "milk, dark or white", "price": 1.00,
     "category": "snacks", "image": "chocolate.png", "stock": 100},
    {"name": "crisps", "description": "A flavour for everyone", "price": 1.00,
     "category": "snacks", "image": "crisps.png", "stock": 100},
    {"name": "cheese", "description": "Smelly pong", "price": 1.00,
     "category": "snacks", "image": "cheese.png", "stock": 100},
    {"name": "eggs", "description": "Don't put all these in one basket",
     "price": 1.00, "category": "basics", "image": "eggs.png", "stock": 100},
    {"name": "bread", "description": "The best thing since sliced...",
     "price": 1.00, "category": "basics", "image": "bread.png", "stock": 100},
    {"name": "butter", "description": "Put on a good spread", "price": 1.00,
     "category": "basics", "image": "butter.png", "stock": 100},
    {"name": "milk", "description": "No sense crying over this", "price": 1.00,
     "category": "basics", "image": "milk.png", "stock": 100},
    {"name": "bananas", "description": "You'll go crazy for these bananas",
     "price": 1.00, "category": "fruit", "image": "bananas.png", "stock": 100},
    {"name": "pineapple", "description": "Totally tropical taste",
     "price": 1.00, "category": "fruit", "image": "pineapple.png", "stock": 100},
    {"name": "tea bags", "description": "Go well with cream at Wimbledon",
     "price": 1.00, "category": "british", "image": "tea_bags.png", "stock": 100},
    {"name": "apples", "description": "Granny smiths and golden delicious",
     "price": 1.00, "category": "fruit", "image": "apples.png", "stock": 100},
    {"name": "fish fingers",
     "description": "Only the best at the captain's table", "price": 1.00,
     "category": "british", "image": "fish_fingers.png", "stock": 100},
    {"name": "pot noodle", "description": "The finest of snacks - all you need is a kettle and a student",
     "price": 1.00, "category": "british", "image": "pot_noodle.png", "stock": 100},
    {"name": "baked beans",
     "description": "Beans, beans the musical fruit, the more you eat...",
     "price": 1.00, "category": "british", "image": "beans.png", "stock": 100},
    {"name": "scotch egg",
     "description": "Perfect for picnics - a boiled egg, shrouded in meat and breadcrumbs",
     "price": 1.00, "category": "british", "image": "scotch_egg.png", "stock": 100},
    {"name": "marmite", "description": "Love it or hate it, it goes well on toast",
     "price": 1.00, "category": "british", "image": "marmite.png", "stock": 100},
]


def check_and_create_view():
    design_doc = {
        'views': {
            'by_timestamp': {
                'map': '''
                function(doc, meta) {
                    if (doc.type && doc.type== "order" && doc.ts) {
                        emit(doc.ts, null)
                    }
                    }
                '''
                }
            }
        }

    mgr = SDK_CLIENT.bucket_manager()
    mgr.design_create(settings.DDOC_NAME, design_doc, use_devmode=False)
    res = SDK_CLIENT.query(settings.DDOC_NAME, settings.VIEW_NAME)
    for row in res:
        print (row)


list_doc = {"type": "product-list", "owner": "david",
            "name": "big fat shopping list"}


def add_products():
    SDK_CLIENT.upsert(LIST_DOC, list_doc)

    i = 12000
    items = []
    for product in PRODUCTS:
        product_id = "product:" + product['name'] 
        items.append(product_id)
        product['type'] = "product"
        product['complete'] = False
        product['price'] = round(random.uniform(0.25, 4.99), 2)
        product['createdAt'] = i
        i += 1
        product['product'] = product['name'] 
        product['productList'] = {"id": LIST_DOC, "owner": "david"}
        SDK_CLIENT.upsert(product_id, product)
    SDK_CLIENT.upsert("items", {"items": items})


if __name__ == '__main__':
    add_products()
    check_and_create_view()
    print("Successfully populated dataset")
