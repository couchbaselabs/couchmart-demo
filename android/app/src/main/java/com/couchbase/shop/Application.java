package com.couchbase.shop;

import android.content.Intent;
import android.os.Handler;
import android.os.StrictMode;
import android.util.Log;
import android.widget.Toast;

import com.couchbase.lite.Attachment;
import com.couchbase.lite.CouchbaseLiteException;
import com.couchbase.lite.Database;
import com.couchbase.lite.DatabaseOptions;
import com.couchbase.lite.Document;
import com.couchbase.lite.DocumentChange;
import com.couchbase.lite.LiveQuery;
import com.couchbase.lite.Manager;
import com.couchbase.lite.Query;
import com.couchbase.lite.QueryEnumerator;
import com.couchbase.lite.QueryRow;
import com.couchbase.lite.SavedRevision;
import com.couchbase.lite.TransactionalTask;
import com.couchbase.lite.UnsavedRevision;
import com.couchbase.lite.android.AndroidContext;
import com.couchbase.lite.auth.Authenticator;
import com.couchbase.lite.auth.AuthenticatorFactory;
import com.couchbase.lite.replicator.Replication;
import com.couchbase.lite.util.ZipUtils;
import com.facebook.stetho.Stetho;
import com.robotpajamas.stetho.couchbase.CouchbaseInspectorModulesProvider;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static android.content.Intent.FLAG_ACTIVITY_NEW_TASK;
import static java.lang.Math.min;

public class Application extends android.app.Application {
    public static final String TAG = "CouchMart";
    public static final String LOGIN_FLOW_ENABLED = "login_flow_enabled";

    private Boolean mLoginFlowEnabled = true;
    private Boolean mEncryptionEnabled = false;
    private Boolean mSyncEnabled = true;
    private String mSyncGatewayUrl = "http://localhost:4984/couchmart/";
    private Boolean mUsePrebuiltDb = false;
    private Boolean mConflictResolution = false;

    public Database getDatabase() {
        return database;
    }

    private Manager manager;
    private Database database;
    private Replication pusher;
    private Replication puller;
    private ArrayList<Document> accessDocuments = new ArrayList<Document>();

    private String mUsername;

    @Override
    public void onCreate() {
        super.onCreate();

        StrictMode.VmPolicy.Builder builder = new StrictMode.VmPolicy.Builder();
        StrictMode.setVmPolicy(builder.build());

        if (BuildConfig.DEBUG) {
            Stetho.initialize(
                    Stetho.newInitializerBuilder(this)
                            .enableDumpapp(Stetho.defaultDumperPluginsProvider(this))
                            .enableWebKitInspector(new CouchbaseInspectorModulesProvider(this))
                            .build());
        }

            login();


        try {
            manager = new Manager(new AndroidContext(getApplicationContext()), Manager.DEFAULT_OPTIONS);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // Logging

    private void enableLogging() {
        Manager.enableLogging(TAG, Log.VERBOSE);
        Manager.enableLogging(com.couchbase.lite.util.Log.TAG, Log.VERBOSE);
        Manager.enableLogging(com.couchbase.lite.util.Log.TAG_SYNC_ASYNC_TASK, Log.VERBOSE);
        Manager.enableLogging(com.couchbase.lite.util.Log.TAG_SYNC, Log.VERBOSE);
        Manager.enableLogging(com.couchbase.lite.util.Log.TAG_QUERY, Log.VERBOSE);
        Manager.enableLogging(com.couchbase.lite.util.Log.TAG_VIEW, Log.VERBOSE);
        Manager.enableLogging(com.couchbase.lite.util.Log.TAG_DATABASE, Log.VERBOSE);
    }

    // Session

    private void startSession(String username, String password, String newPassword) {
        enableLogging();
        installPrebuiltDb();
        openDatabase(username, password, newPassword);
        mUsername = username;
        startReplication(username, password);
        showApp();
    }

    private void installPrebuiltDb() {
        if (!mUsePrebuiltDb) {
            return;
        }

        try {
            manager = new Manager(new AndroidContext(getApplicationContext()), Manager.DEFAULT_OPTIONS);
        } catch (IOException e) {
            e.printStackTrace();
        }
        try {
            database = manager.getExistingDatabase("todo");
        } catch (CouchbaseLiteException e) {
            e.printStackTrace();
        }
        if (database == null) {
            try {
                ZipUtils.unzip(getAssets().open("todo.zip"), manager.getContext().getFilesDir());
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private void openDatabase(String username, String key, String newKey) {
        String dbname = "couchmart";
        DatabaseOptions options = new DatabaseOptions();
        options.setCreate(true);

        if (mEncryptionEnabled) {
            options.setEncryptionKey(key);
        }

        Manager manager = null;
        try {
            manager = new Manager(new AndroidContext(getApplicationContext()), Manager.DEFAULT_OPTIONS);
        } catch (IOException e) {
            e.printStackTrace();
        }
        try {
            database = manager.openDatabase(dbname, options);
        } catch (CouchbaseLiteException e) {
            e.printStackTrace();
        }
        if (newKey != null) {
            try {
                database.changeEncryptionKey(newKey);
            } catch (CouchbaseLiteException e) {
                e.printStackTrace();
            }
        }

        database.addChangeListener(new Database.ChangeListener() {
            @Override
            public void changed(Database.ChangeEvent event) {
                if(!event.isExternal()) {
                    return;
                }

                for(final DocumentChange change : event.getChanges()) {
                    if(!change.isCurrentRevision()) {
                        continue;
                    }

                    Document changedDoc = database.getExistingDocument(change.getDocumentId());
                    if(changedDoc == null) {
                        return;
                    }

                    String docType = (String) changedDoc.getProperty("type");
                    if(!docType.equals("product-list.user")) {
                        continue;
                    }

                    String username = (String) changedDoc.getProperty("username");
                    if(!username.equals(getUsername())) {
                        continue;
                    }

                    accessDocuments.add(changedDoc);
                    changedDoc.addChangeListener(new Document.ChangeListener() {
                        @Override
                        public void changed(Document.ChangeEvent event) {
                            Document changedDoc = database.getDocument(event.getChange().getDocumentId());
                            if (!changedDoc.isDeleted()) {
                                return;
                            }

                            try {
                                SavedRevision deletedRev = changedDoc.getLeafRevisions().get(0);
                                String listId = (String) ((HashMap<String, Object>) deletedRev.getProperty("productList")).get("id");
                                Document listDoc = database.getExistingDocument(listId);
                                accessDocuments.remove(changedDoc);
                                listDoc.purge();
                                changedDoc.purge();
                            } catch (CouchbaseLiteException e) {
                                Log.e(TAG, "Failed to get deleted rev in document change listener");
                            }
                        }
                    });
                }
            }
        });
    }

    private void closeDatabase() {
        // TODO: stop conflicts live query
        database.close();
    }

    // Login

    private void login() {
login("david", "quality");
    }

    private void showApp() {
        Intent intent = new Intent();
        intent.setFlags(FLAG_ACTIVITY_NEW_TASK);
        intent.setClass(getApplicationContext(), ListsActivity.class);
        intent.putExtra(LOGIN_FLOW_ENABLED, mLoginFlowEnabled);
        startActivity(intent);
    }

    public void login(String username, String password) {
        mUsername = username;
        Log.d("HELLO","About to Start Session");
        startSession(username, password, null);
    }

//    public void logout() {
//        runOnUiThread(new Runnable() {
//            @Override
//            public void run() {
//                stopReplication();
//                closeDatabase();
//                login();
//            }
//        });
//    }

    // Replication
    private void startReplication(String username, String password) {
        if (!mSyncEnabled) {
            return;
        }

        URL url = null;
        try {
            url = new URL(mSyncGatewayUrl);
        } catch (MalformedURLException e) {
            e.printStackTrace();
        }

        ReplicationChangeListener changeListener = new ReplicationChangeListener(this);

        pusher = database.createPushReplication(url);
        pusher.setContinuous(true); // Runs forever in the background
        pusher.addChangeListener(changeListener);

        puller = database.createPullReplication(url);
        puller.setContinuous(true); // Runs forever in the background
        puller.addChangeListener(changeListener);

        if (mLoginFlowEnabled) {
            Authenticator authenticator = AuthenticatorFactory.createBasicAuthenticator(username, password);
            pusher.setAuthenticator(authenticator);
            puller.setAuthenticator(authenticator);
        }

        pusher.start();
        puller.start();
    }

    private void stopReplication() {
        if (!mSyncEnabled) {
            return;
        }

        pusher.stop();
        puller.stop();
    }


    public String getUsername() {
        return mUsername;
    }

    public void setUsername(String mUsername) {
        this.mUsername = mUsername;
    }

    public void showErrorMessage(final String errorMessage, final Throwable throwable) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                android.util.Log.e(TAG, errorMessage, throwable);
                String msg = String.format("%s",
                        errorMessage);
                Toast.makeText(getApplicationContext(), msg, Toast.LENGTH_LONG).show();
            }
        });
    }

    private void runOnUiThread(Runnable runnable) {
        Handler mainHandler = new Handler(getApplicationContext().getMainLooper());
        mainHandler.post(runnable);
    }


}
