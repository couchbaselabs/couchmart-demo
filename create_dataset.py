#!/usr-bin/env - python

from couchbase.bucket import Bucket
import couchbase
import uuid
import datetime
import settings

bucket_name=settings.BUCKET_NAME
user=settings.USERNAME
password=settings.PASSWORD
node=settings.NODES[0]
SDK_CLIENT = Bucket('couchbase://10.142.170.101/{}'.format(bucket_name), username=user, password=password)
SDK_CLIENT.timeout = 15

# LIST_DOC="david.3501d7e0-9057-4c74-8de0-259ac8af09ee"
LIST_DOC="david.all_the_products"


PRODUCTS = [
{ "name": "fish fingers", "description": "Only the best at the captain's table", "price": 1.00,"category": "meat", "image": "finsh_fingers.png", "stock": 100},
{ "name": "burger", "description": "Mmmm. That IS a tasty burger", "price": 1.00,"category": "meat", "image": "burger.png","stock": 100},
{ "name": "ham", "description": "Du jambon", "price": 1.00,"category": "dairy", "image": "ham.png", "stock": 100},
{ "name": "bacon", "description": "Smashing in a butty", "price": 1.00,"category": "meat", "image": "bacon.png", "stock": 100},
{ "name": "sausages", "description": "A string of bangers", "price": 1.00,"category": "meat", "image": "sausages.png", "stock": 100},
{ "name": "whisky", "description": "A wee dram", "price": 1.00,"category": "drinks", "image": "whisky.png", "stock": 100},
{ "name": "water", "description": "h20", "price": 1.00,"category": "drinks", "image": "water.png", "stock": 100},
{ "name": "champagne", "description": "Lovely bubbly", "price": 1.00,"category": "drinks", "image": "champagne.png", "stock": 100},
{ "name": "red wine", "description": "Vin Rouge", "price": 1.00,"category": "drinks", "image": "red_wine.png", "stock": 100},
{ "name": "beer", "description": "amber nectar", "price": 1.00,"category": "drinks", "image": "beer.png", "stock": 100},
{ "name": "bonbons", "description": "What's French for....?", "price": 1.00,"category": "snacks", "image": "bonbons.png", "stock": 100},
{ "name": "cookie", "description": "chocloate chip", "price": 1.00,"category": "dairy", "image": "cookie", "stock": 100},
{ "name": "carambars", "description": "Eat Your Sweet!", "price": 1.00,"category": "snacks", "image": "carambars.png", "stock": 100},
{ "name": "chocolate", "description": "milk, dark or white", "price": 1.00,"category": "snacks", "image": "chocolate.png", "stock": 100},
{ "name": "crisps", "description": "A flavour for everyone", "price": 1.00,"category": "snacks", "image": "crisps.png", "stock": 100},
{ "name": "butter", "description": "Put on a good spread", "price": 1.00,"category": "basics", "image": "butter.png", "stock": 100},
{ "name": "cheese", "description": "Smelly pong", "price": 1.00,"category": "basics", "image": "cheese.png", "stock": 100},
{ "name": "milk", "description": "No sense crying over this", "price": 1.00,"category": "basics", "image": "milk.png", "stock": 100},
{ "name": "eggs", "description": "Don't put all these in one basket", "price": 1.00,"category": "basics", "image": "eggs.png", "stock": 100},
{ "name": "bread", "description": "The best thing since sliced...", "price": 1.00,"category": "basics", "image": "bread.png", "stock": 100},
{ "name": "bananas", "description": "You'll go crazy for these bananas", "price": 1.00,"category": "fruit", "image": "bananas.png", "stock": 100},
{ "name": "pineapples", "description": "Totally tropical taste", "price": 1.00,"category": "fruit", "image": "pineapple.png", "stock": 100},
{ "name": "strawberries", "description": "Go well with cream at Wimbledon", "price": 1.00,"category": "fruit", "image": "strawberries", "stock": 100},
{ "name": "apples", "description": "Granny smiths and golden delicious", "price": 1.00,"category": "fruit", "image": "apples.png", "stock": 100},
{ "name": "oranges", "description": "Not the only fruit", "price": 1.00,"category": "fruit", "image": "oranges.png", "stock": 100}]








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

def do_queries():
    for row in SDK_CLIENT.n1ql_query('SELECT  name,stock FROM charlie WHERE type == "product" ORDER BY stock DESC LIMIT 5'):
        print row


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
do_queries()
