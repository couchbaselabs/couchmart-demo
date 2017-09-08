package com.couchbase.shop;

import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.support.design.widget.FloatingActionButton;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.PopupMenu;
import android.widget.TextView;

import com.couchbase.lite.CouchbaseLiteException;
import com.couchbase.lite.Database;
import com.couchbase.lite.Document;
import com.couchbase.lite.Emitter;
import com.couchbase.lite.LiveQuery;
import com.couchbase.lite.Mapper;
import com.couchbase.lite.QueryEnumerator;
import com.couchbase.lite.QueryRow;
import com.couchbase.lite.Reducer;
import com.couchbase.lite.SavedRevision;
import com.couchbase.lite.UnsavedRevision;
import com.couchbase.lite.util.Log;
import com.couchbase.shop.util.LiveQueryAdapter;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class ListsActivity extends AppCompatActivity {

    private Database mDatabase;
    private String mUsername;
    private Map<String, Object> incompCounts;

    private LiveQuery listsLiveQuery = null;
    private LiveQuery incompTasksCountLiveQuery = null;

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (listsLiveQuery != null) {
            listsLiveQuery.stop();
            listsLiveQuery = null;
        }
        if (incompTasksCountLiveQuery != null) {
            incompTasksCountLiveQuery.stop();
            incompTasksCountLiveQuery = null;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_lists);

        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        toolbar.setTitle(getTitle());

        Application application = (Application) getApplication();
        mDatabase = application.getDatabase();
        mUsername = application.getUsername();
//        Document list = mDatabase.getDocument("david.3501d7e0-9057-4c74-8de0-259ac8af09ee");
        Document list = mDatabase.getDocument("david.all_the_products");
        showTasks(list);



    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        return super.onCreateOptionsMenu(menu);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case R.id.logout:
                Application application = (Application) getApplication();
                //application.logout();
                return true;
            default:
                // If we got here, the user's action was not recognized.
                // Invoke the superclass to handle it.
                return super.onOptionsItemSelected(item);
        }
    }


    private void showTasks(Document list) {
        Intent intent = new Intent(this, ListDetailActivity.class);
        intent.putExtra(ListDetailActivity.INTENT_LIST_ID, list.getId());
        startActivity(intent);
    }


}
