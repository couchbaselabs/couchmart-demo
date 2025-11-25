from datetime import timedelta

# needed for any cluster connection
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
# needed for options -- cluster, timeout, SQL++ (N1QL) query, etc.
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions,
                               QueryOptions)

import settings

# Update this to your cluster
bucket_name = settings.BUCKET_NAME
username = settings.USERNAME
password = settings.PASSWORD

if settings.AWS:
    node = settings.AWS_NODES[0]
else:
    node = settings.AZURE_NODES[0]
# User Input ends here.

# Connect options - authentication
auth = PasswordAuthenticator(
    username,
    password,
)
timeout_opts = ClusterTimeoutOptions(connect_timeout=timedelta(seconds=15))

# Get a reference to our cluster
# NOTE: For TLS/SSL connection use 'couchbases://<your-ip-address>' instead
cluster = Cluster(
    'couchbase://{0}/{1}'.format(node, bucket_name),
    ClusterOptions(auth, timeout_options=timeout_opts)
)

# Wait until the cluster is ready for use.
cluster.wait_until_ready(timedelta(seconds=5))

# get a reference to our bucket
cb = cluster.bucket(bucket_name)

# Get a reference to the default collection, required for older Couchbase server versions
cb_coll_default = cb.default_collection()

# print(cluster.ping())
