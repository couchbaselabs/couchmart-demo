from datetime import timedelta

# needed for any cluster connection
from cb_connection import cb, cb_coll_default
from couchbase.management.views import DesignDocumentNamespace, DesignDocument, View
import random
import settings

LIST_DOC = "david.all_the_products"

list_doc = {"type": "product-list", "owner": "david", "name": "big fat shopping list"}
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

def add_products():
    cb_coll_default.upsert(LIST_DOC, list_doc)

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
        cb_coll_default.upsert(product_id, product)
    cb_coll_default.upsert("items", {"items": items})

def check_and_create_view():
    view_manager = cb.view_indexes()
    # Create a DesignDocument with one view
    design_doc = DesignDocument(
        name=settings.DDOC_NAME,
        views={
            "by_timestamp": View(
                map="function (doc, meta) { if (doc.type && doc.type == 'order') { emit(doc.ts, null); } }"
            )
        }
    )
    view_manager.upsert_design_document(design_doc, DesignDocumentNamespace.PRODUCTION)
    res = cb.view_query(settings.DDOC_NAME, settings.VIEW_NAME)
    for row in res.rows():
        print (row)

if __name__ == '__main__':
    add_products()
    check_and_create_view()
    res = cb_coll_default.get("items")
    print("Successfully populated dataset")
