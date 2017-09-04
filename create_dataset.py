#!/usr-bin/env - python

from couchbase.bucket import Bucket
import couchbase
import uuid
import datetime

BUCKET_NAME = 'charlie'
SDK_CLIENT = Bucket('couchbase://dhaikney-server-1/{}'.format(BUCKET_NAME), username='charlie', password='password')
SDK_CLIENT.timeout = 15

# LIST_DOC="david.3501d7e0-9057-4c74-8de0-259ac8af09ee"
LIST_DOC="david.all_the_products"


PRODUCTS = [
{ "name": "eggs", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg", "stock": 100},
{ "name": "cheese", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg","stock": 100},
{ "name": "wine", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg", "stock": 100},
{ "name": "ham", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg", "stock": 100},
{ "name": "sausages", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg", "stock": 100},
{ "name": "bacon", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg", "stock": 100},
{ "name": "crisps", "description": "Smelly pong", "price": 1.00,"category": "dairy", "image": "picture.jpg", "stock": 100}]
	
   
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

    i = 12000
    for product in PRODUCTS:
        product_id = "product:" + product['name'] 
        product['type'] = "product"
        product['complete'] = False
        # product['createdAt'] = str(datetime.datetime.now())
        product['createdAt'] = i
        i+=1
        product['product'] = product['name'] 
        product['productList'] = {"id": LIST_DOC, "owner": "david"}
        SDK_CLIENT.upsert(product_id, product)

        # img_filename="./img/"+product['name']+".png"
        # with open(img_filename, "rb") as image_file:
        #     f = image_file.read()
        #     image_bytes = bytearray(f)
        #     SDK_CLIENT.upsert("img:"+product['name'], image_bytes,  format=couchbase.FMT_BYTES)


add_products()
