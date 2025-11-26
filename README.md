# Couchbase Connect EU Demo - Start a Revolution

This is the code for the live demo at Couchbase Connect EU -
'Start a Revolution'.

This code was created purely for demo purposes and does not necessarily
represent Couchbase best practices.

## Docker Compose

To start the application and Couchbase Server using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- Couchbase Server (available at http://localhost:8091)
- The Web Application (available at http://localhost:8888)

## Website Setup

### Initial Setup

1. [Install and setup](https://docs.couchbase.com/server/7.6/getting-started/do-a-quick-install.html) Couchbase Server 7.6+ on your nodes.

2. Install needed python modules. e.g:

    ```
    pip install --no-cache-dir -r requirements.txt
    ```
    
3. Adjust `settings.py` to point towards the servers/users/buckets that you 
are using for
'aws' and 'azure'. If not using XDCR, you can just point towards one cluster.

### Configuration

You can configure the application using environment variables. These will override the defaults in `settings.py`.

| Variable | Default | Description |
|----------|---------|-------------|
| `BUCKET_NAME` | `couchmart` | Name of the Couchbase bucket |
| `AWS_NODES` | `couchbase` | Comma-separated list of Couchbase nodes |
| `AWS` | `True` | Set to `True` if running on AWS (or local/K8s) |
| `USERNAME` | `Administrator` | Data user username |
| `PASSWORD` | `password` | Data user password |
| `ADMIN_USER` | `Administrator` | Admin username |
| `ADMIN_PASS` | `password` | Admin password |
| `DDOC_NAME` | `orders` | Design document name |
| `VIEW_NAME` | `by_timestamp` | View name |
| `DEBUG_LOGS` | `None` | Set to `true` to enable verbose debug logging |

4. Create the appropriate bucket on your server, ensuring that a user is created
with full access to that bucket.

5. Run the `create_dataset.py` script to populate the bucket with the necessary
documents:

    ```
    python create_dataset.py
    ```

6. Start the web server:

    ```
    python web-server.py
    ```
   
   (note: If running the web-server on port 80, you must run this using `sudo`)
   
7. Access the web page at `http://localhost:8888` 
(or whichever port you have chosen). The nodes visualiser can be accessed at
`/nodes` and the latest orders can be found at `/query_vis.html`. Note that the
node visualiser has been orchestrated specifically for the demo and may not 
display the correct output in all cases.

### Debugging

To enable verbose debug logging (including connection details and ping results), set the environment variable `DEBUG_LOGS=true`.

```bash
export DEBUG_LOGS=true
python web-server.py
```

### Query Setup

1. Add a Query/Index node into the cluster (if there is not one already).

2. Create the following index:

    ```
    CREATE INDEX category ON couchmart(category)
    ```

### Search Setup

1. Add a search node into the cluster (if there is not one already)

2. Create a search index called `English`.

## Mobile Setup

1. Start up Sync Gateway 1.5 against your cluster, using the configuration 
found at `android/sync-gateway-config-xattrs.json`. Ensure that you update the
access credentials to be correct for your environment.

2. Open the folder `android` in Android Studio.

3. Import the relevant dependencies and setup the project.

4. Set the `mSyncGatewayUrl` in 
`android/app/src/main/java/com/couchbase/shop/Application.java` to point 
towards your Sync Gateway.

5. 'Run' the project, either on a real android device or a simulator.

   
### Demo Queries
1. Find the most popular products that have been ordered:

    ```
    SELECT   COUNT(1) `order`, product
    FROM couchmart UNNEST `order` as product
    WHERE couchmart.`type` = "order"
    GROUP BY product
    ORDER BY COUNT(1) DESC 
    LIMIT 5;
    ```
    
2. Find out who had the most expensive shopping basket:

    ```
    SELECT b.name name, SUM(a.price) price, b.`order` basket FROM couchmart b 
    JOIN couchmart a ON KEYS b.`order`
    WHERE b.type="order"
    GROUP BY meta(b).id,b.name,b.`order`
    ORDER BY price DESC
    LIMIT 10
    ```
    
3. Set a category of items to be out of stock:

    ```
    UPDATE couchmart SET stock=0 WHERE category="drinks"
    ```
