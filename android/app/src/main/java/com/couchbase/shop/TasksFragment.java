package com.couchbase.shop;

import android.Manifest;
import android.app.AlertDialog;
import android.content.ContentResolver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.AssetFileDescriptor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Paint;
import android.media.ThumbnailUtils;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.support.design.widget.FloatingActionButton;
import android.support.v4.app.Fragment;
import android.support.v4.content.ContextCompat;
import android.view.LayoutInflater;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.PopupMenu;
import android.widget.TextView;
import android.widget.Toast;

import com.couchbase.lite.Attachment;
import com.couchbase.lite.CouchbaseLiteException;
import com.couchbase.lite.Database;
import com.couchbase.lite.Document;
import com.couchbase.lite.Emitter;
import com.couchbase.lite.LiveQuery;
import com.couchbase.lite.Mapper;
import com.couchbase.lite.Query;
import com.couchbase.lite.SavedRevision;
import com.couchbase.lite.UnsavedRevision;
import com.couchbase.lite.util.Log;
import com.couchbase.shop.util.LiveQueryAdapter;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static android.app.Activity.RESULT_OK;
import static com.couchbase.shop.ListDetailActivity.INTENT_LIST_ID;


public class TasksFragment extends Fragment {

    private ListView mListView;

    private Database mDatabase;
    private String mUsername;
    public Document mTaskList;

    LiveQuery listsLiveQuery = null;

    private android.view.LayoutInflater mInflater;
    private View mainView;

    private static final int PERMISSION_REQUESTS = 1010;
    private static final int REQUEST_TAKE_PHOTO = 1;
    private static final int REQUEST_CHOOSE_PHOTO = 2;
    private static final int THUMBNAIL_SIZE = 150;
    private static final int MOBILE_TS_BIAS = 30;


    private static int itemsSelected = 0;
    private static List<String> shoppingBasket = new ArrayList<String>();

    private String mImagePathToBeAttached;
    private Document selectedTask;

    public TasksFragment() {
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        if (listsLiveQuery != null) {
            listsLiveQuery.stop();
            listsLiveQuery = null;
        }
    }

    @Nullable
    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {

        mInflater = inflater;
        mainView = inflater.inflate(R.layout.fragment_tasks, null);

        mListView = (ListView) mainView.findViewById(R.id.list);

        FloatingActionButton fab = (FloatingActionButton) mainView.findViewById(R.id.fab);
        fab.setOnClickListener(new android.view.View.OnClickListener() {
            @Override
            public void onClick(android.view.View view) {
                submitShoppingBasket(mListView);
            }
        });

        FloatingActionButton profilePic = (FloatingActionButton) mainView.findViewById(R.id.profile_pic);
        profilePic.setOnClickListener(new android.view.View.OnClickListener() {
            @Override
            public void onClick(android.view.View view) {
                displayAttachImageDialog(null);
            }
        });



        Application application = (Application) getActivity().getApplication();
        mDatabase = application.getDatabase();
        mUsername = application.getUsername();
        Intent intent = getActivity().getIntent();
        mTaskList = mDatabase.getDocument(intent.getStringExtra(INTENT_LIST_ID));

        setupViewAndQuery();

        return mainView;
    }


    // For a given task-list ID, check which tasks match
    private void setupViewAndQuery() {
        com.couchbase.lite.View view = mDatabase.getView("products/productsByCreatedAt");
        if (view.getMap() == null) {
            view.setMap(new Mapper() {
                @Override
                public void map(Map<String, Object> document, Emitter emitter) {
                    String type = (String) document.get("type");
                    if ("product".equals(type)) {
                        Map<String, Object> taskList = (Map<String, Object>) document.get("productList");
                        String listId = (String) taskList.get("id");
                        String task = (String) document.get("product");
                        ArrayList<String> key = new ArrayList<String>();
                        key.add(listId);
                        key.add(task);
                        String value = (String) document.get("_rev");
                        emitter.emit(key, value);
                    }
                }
            }, "5.0");
        }

        Query query = view.createQuery();

        ArrayList<String> key = new ArrayList<String>();
        key.add(mTaskList.getId());
        query.setStartKey(key);
        query.setEndKey(key);
        query.setPrefixMatchLevel(1);
        query.setDescending(false);
        listsLiveQuery = query.toLiveQuery();

        final TasksFragment.TaskAdapter mAdapter = new TasksFragment.TaskAdapter(getActivity(), listsLiveQuery);

        mListView.setAdapter(mAdapter);


    }


    private class TaskAdapter extends LiveQueryAdapter {
        public TaskAdapter(Context context, LiveQuery query) {
            super(context, query);
        }


        @Override
        public boolean isEnabled(int position){
            final Document product = (Document) getItem(position);
            int stockLevel = (int) product.getProperty("stock");
            return (stockLevel > 0);
        }

        @Override
        public android.view.View getView(int position, android.view.View convertView, ViewGroup parent) {
            if (convertView == null) {
                LayoutInflater inflater = (LayoutInflater) parent.getContext().
                        getSystemService(Context.LAYOUT_INFLATER_SERVICE);
                convertView = inflater.inflate(R.layout.view_task, null);
            }
            final Document product = (Document) getItem(position);
            if (product == null || product.getCurrentRevision() == null) {
                return convertView;
            }
            ImageView imageView = (ImageView) convertView.findViewById(R.id.photo);
            String productName = (String) product.getProperty("product");
            switch (productName) {
                case "apples":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_apples));
                    break;
                case "bacon":
                    if (isEnabled(position))
                        imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_bacon));
                    else
                        imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_no_bacon));
                    break;
                case "bananas":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_bananas));
                    break;
                case "beer":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_beer));
                    break;
                case "bonbons":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_bonbons));
                    break;
                case "bread":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_bread));
                    break;
                case "burger":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_burger));
                    break;
                case "butter":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_butter));
                    break;
                case "carambars":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_carambars));
                    break;
                case "champagne":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_champagne));
                    break;
                case "cheese":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_cheese));
                    break;
                case "chocolate":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_chocolate));
                    break;
                case "cookie":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_cookie));
                    break;
                case "crisps":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_crisps));
                    break;
                case "eggs":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_eggs));
                    break;
                case "fish fingers":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_fish_fingers));
                    break;
                case "ham":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_ham));
                    break;
                case "milk":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_milk));
                    break;
                case "oranges":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_oranges));
                    break;
                case "pineapples":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_pineapple));
                    break;
                case "red wine":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_red_wine));
                    break;
                case "sausages":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_sausages));
                    break;
                case "strawberries":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_strawberries));
                    break;
                case "water":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_water));
                    break;
                case "whisky":
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_whisky));
                    break;
                default:
                    imageView.setImageDrawable(getResources().getDrawable(R.drawable.ic_note));
            }

            TextView text = (TextView) convertView.findViewById(R.id.text);
            text.setText((String) product.getProperty("product"));
            if (isEnabled(position)) {
                text.setPaintFlags(text.getPaintFlags() & (~ Paint.STRIKE_THRU_TEXT_FLAG));
                imageView.setColorFilter(null);
            } else {
                text.setPaintFlags(text.getPaintFlags() | Paint.STRIKE_THRU_TEXT_FLAG);
                imageView.setColorFilter(Color.argb(200,200,200,200));
            }
            final CheckBox checkBox = (CheckBox) convertView.findViewById(R.id.checked);
            checkBox.setChecked(shoppingBasket.contains((product.getId())));
            checkBox.setEnabled(isEnabled(position));

            checkBox.setOnClickListener(new android.view.View.OnClickListener() {
                @Override
                public void onClick(android.view.View view) {
                    updateCheckedStatus(product, checkBox);
                }
            });

            convertView.setOnClickListener(new android.view.View.OnClickListener() {
                @Override
                public void onClick(android.view.View view) {
                    checkBox.setChecked(!checkBox.isChecked());
                    updateCheckedStatus(product, checkBox);
                }
            });

            return convertView;
        }

        private void updateCheckedStatus(Document product, CheckBox checkBox) {
            Map<String, Object> properties = new HashMap<String, Object>();
            properties.putAll(product.getProperties());
            Boolean checked = checkBox.isChecked();
            properties.put("complete", checked);
            if (checked) {
                if (itemsSelected >= 5) {
                    checkBox.setChecked(false);
                    Toast.makeText(getContext(), "No more than 5 can be selected", Toast.LENGTH_LONG).show();
                } else {
                    shoppingBasket.add(product.getId());
                    itemsSelected++;
                }
            } else { //deselecting
                shoppingBasket.remove(product.getId());
                itemsSelected--;
            }

        }
    }

    private void submitShoppingBasket(ListView view) {
        if (itemsSelected != 5)
        {
            int moreItems = 5 - itemsSelected;
            Toast.makeText(getContext(), "Please select " + moreItems + " more item(s)", Toast.LENGTH_LONG).show();
            return;
        }
        Map<String, Object> properties = new HashMap<String, Object>();
        properties.put("type", "order");
        properties.put("order", shoppingBasket);
        properties.put("ts", MOBILE_TS_BIAS + (long) new Date().getTime() / 1000);
        properties.put("name", "Couchbase Demo Phone");
        String docId = "david" + "." + "basket" + UUID.randomUUID();
        Document document = mDatabase.getDocument(docId);
//        Document document = mDatabase.createDocument();
        try {
             document.putProperties(properties);
            Toast.makeText(getContext(), "Order Submitted!", Toast.LENGTH_LONG).show();
            shoppingBasket.clear();
            itemsSelected = 0;
            view.invalidateViews();

        } catch (CouchbaseLiteException e) {
            e.printStackTrace();
        }    }


    private void attachImage(Document task, Bitmap image) {
        UnsavedRevision revision = task.createRevision();
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        image.compress(Bitmap.CompressFormat.JPEG, 50, out);
        ByteArrayInputStream in = new ByteArrayInputStream(out.toByteArray());
        revision.setAttachment("image", "image/jpg", in);

        try {
            revision.save();
        } catch (CouchbaseLiteException e) {
            e.printStackTrace();
        }
    }

    private void dispatchTakePhotoIntent() {
        Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        if (takePictureIntent.resolveActivity(this.getActivity().getPackageManager()) != null) {
            File photoFile = null;
            try {
                photoFile = createImageFile();
            } catch (IOException e) {
                e.printStackTrace();
            }

            if (photoFile != null) {
                takePictureIntent.putExtra(MediaStore.EXTRA_OUTPUT, Uri.fromFile(photoFile));
                startActivityForResult(takePictureIntent, REQUEST_TAKE_PHOTO);
            }
        }
    }

    private File createImageFile() throws IOException {
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
        String fileName = "TODO_LITE-" + timeStamp + "_";
        File storageDir = getActivity().getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        File image = File.createTempFile(fileName, ".jpg", storageDir);
        mImagePathToBeAttached = image.getAbsolutePath();
        return image;
    }

    private void dispatchChoosePhotoIntent() {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Audio.Media.EXTERNAL_CONTENT_URI);
        intent.setType("image/*");
        startActivityForResult(Intent.createChooser(intent, "Select File"), REQUEST_CHOOSE_PHOTO);
    }

    private void deleteCurrentPhoto(Document task) {
        UnsavedRevision unsavedRevision = task.getCurrentRevision().createRevision();
        unsavedRevision.removeAttachment("image");
        try {
            unsavedRevision.save();
        } catch (CouchbaseLiteException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        switch (requestCode) {
            case PERMISSION_REQUESTS: {
                if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    showImagePickerDialog();
                }
            }
        }
    }

    private void displayAttachImageDialog(final Document task) {
        selectedTask = task;
        if (ContextCompat.checkSelfPermission(getActivity(), Manifest.permission.READ_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.CAMERA}, PERMISSION_REQUESTS);
        } else {
            showImagePickerDialog();
        }
    }

    private void showImagePickerDialog() {
        CharSequence[] items;
        items = new CharSequence[]{ "Take photo", "Choose photo", "Delete photo" };

        AlertDialog.Builder builder = new AlertDialog.Builder(getActivity());
        builder.setTitle("Add picture");
        builder.setItems(items, new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int item) {
                if (item == 0) {
                    dispatchTakePhotoIntent();
                } else if (item == 1) {
                    dispatchChoosePhotoIntent();
                } else {
                    deleteCurrentPhoto(selectedTask);
                }
            }
        });
        builder.show();
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (resultCode != RESULT_OK) {
            return;
        }

        final int size = THUMBNAIL_SIZE;
        Bitmap thumbnail = null;
        if (requestCode == REQUEST_TAKE_PHOTO) {
            File file = new File(mImagePathToBeAttached);
            if (file.exists()) {
                BitmapFactory.Options options = new BitmapFactory.Options();
                options.inJustDecodeBounds = true;
                BitmapFactory.decodeFile(mImagePathToBeAttached, options);
                options.inJustDecodeBounds = false;
                Bitmap mImage = BitmapFactory.decodeFile(mImagePathToBeAttached, options);
                thumbnail = ThumbnailUtils.extractThumbnail(mImage, size, size);
                file.delete();
            }
        } else if (requestCode == REQUEST_CHOOSE_PHOTO) {
            Uri uri = data.getData();
            ContentResolver resolver = getActivity().getContentResolver();
            Bitmap mImage = null;
            try {
                mImage = MediaStore.Images.Media.getBitmap(resolver, uri);
            } catch (IOException e) {
                e.printStackTrace();
            }
            AssetFileDescriptor asset = null;
            try {
                asset = resolver.openAssetFileDescriptor(uri, "r");
            } catch (FileNotFoundException e) {
                e.printStackTrace();
            }
            thumbnail = ThumbnailUtils.extractThumbnail(mImage, size, size);
        }

        attachImage(selectedTask, thumbnail);
    }
}
