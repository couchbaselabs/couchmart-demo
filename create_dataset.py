#!/usr-bin/env - python

from couchbase.bucket import Bucket
import uuid
import datetime

BUCKET_NAME = 'charlie'
SDK_CLIENT = Bucket('couchbase://dhaikney-server-1/{}'.format(BUCKET_NAME), username='charlie', password='password')
SDK_CLIENT.timeout = 15

# LIST_DOC="david.3501d7e0-9057-4c74-8de0-259ac8af09ee"
LIST_DOC="david.all_the_products"


PRODUCTS = [
{ "name": "cheese", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg"},
{ "name": "wine", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg"},
{ "name": "ham", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg"},
{ "name": "eggs", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg"},
{ "name": "sausages", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg"},
{ "name": "bacon", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg"},
{ "name": "crisps", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg"}]
	
   
# {
#   "complete": false,
#   "createdAt": 1504112965508,
#   "task": "Help",
#   "taskList": {
#     "id": "david.fd2679d9-8647-45d4-91e2-8963385f3a34",
#     "owner": "david"
#   },
#   "type": "task"
# }

list_doc = {"type": "product-list", "owner": "david", "name": "big fat shopping list"}

def add_products():
    SDK_CLIENT.upsert(LIST_DOC, list_doc)


    for product in PRODUCTS:
        product_id = "product_" + product['name'] 
        product['type'] = "product"
        product['quantity'] = 100
        product['complete'] = False
        product['createdAt'] = str(datetime.datetime.now())
        product['product'] = product['name'] 
        product['productList'] = {"id": LIST_DOC, "owner": "david"}
        SDK_CLIENT.upsert(product_id, product)


add_products()
