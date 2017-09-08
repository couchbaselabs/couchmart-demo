package com.couchbase.shop.util;

import android.support.v4.app.Fragment;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.FragmentPagerAdapter;
import android.util.Log;

import com.couchbase.shop.TasksFragment;

public class ListFragmentPagerAdapter extends FragmentPagerAdapter {
    final int PAGE_COUNT;

    public ListFragmentPagerAdapter(FragmentManager fm) {
        super(fm);

        PAGE_COUNT = 1;
    }

    @Override
    public int getCount() {
        return PAGE_COUNT;
    }

    @Override
    public Fragment getItem(int position) {
        switch (position) {
            case 0:
                return new TasksFragment();
            case 1:
                Log.d("oops", "OK");
                return new TasksFragment();
                //return new UsersFragment();
            default:
                return null;
        }
    }

    @Override
    public CharSequence getPageTitle(int position) {
        // Generate title based on item position
        return "Select 5 items";
    }
}
