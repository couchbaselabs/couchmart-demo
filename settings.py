BUCKET_NAME = "couchmart"
# The list of nodes to use as 'AWS' nodes
AWS_NODES = ["10.142.170.101", "10.142.170.102"]
# The list of nodes to use as 'Azure' nodes
AZURE_NODES = [""]
# Whether the current cluster is on AWS
AWS = True
# Username of the data user
USERNAME = "Administrator"
# Password of the data user
PASSWORD = "password"
# Administrator username
ADMIN_USER = "Administrator"
# Administrator password
ADMIN_PASS = "password"
# Name of the design doc
DDOC_NAME = "orders"
# Name of the view
VIEW_NAME = "by_timestamp"
# Use ACID RPC service True/False
ACID = True
# Address for RPC ACID service
RPC_ADDRESS = "http://127.0.0.1:8889/submitorder"
