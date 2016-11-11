package com.example.nandor.blutetest;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Handler;
import android.os.Message;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.*;

import java.util.ArrayList;
import java.util.Collections;

public class TalkActivity extends AppCompatActivity {
    private BluetoothAdapter mBluetoothAdapter;
    private String uuid="";
    private Handler mHandler;
    private ConnectThread t1;
    private Context context;
    private ArrayList<String> msgList= new ArrayList<String>();
    private ArrayList<String> recList= new ArrayList<String>();
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_talk);
        Intent intent = getIntent();
        this.context=this;
        String device_info = intent.getStringExtra("name"); //if it's a string you stored.
        String hw_info = intent.getStringExtra("hwaddr");
        final TextView title = (TextView) findViewById(R.id.textView);
        final TextView send_m = (TextView) findViewById(R.id.textmsg);
        final TextView cmmd = (TextView) findViewById(R.id.textViewCommands);
        cmmd.setVisibility(View.GONE);
        send_m.setVisibility(View.GONE);
        final TextView dev = (TextView) findViewById(R.id.textView2);
        dev.setText(device_info + "-" + hw_info);
        final Button button= (Button) findViewById(R.id.button2);
        button.setEnabled(false);
        final EditText edit= (EditText) findViewById(R.id.editText);
        final ListView listView = (ListView) findViewById(R.id.listView);
        final ListView recView = (ListView) findViewById(R.id.listView2);
        mHandler = new Handler() {
            @Override
            public void handleMessage(Message msg) {
                switch (msg.what) {
                    case 1:
                        //received.setText(""+msg.obj);
                        Collections.reverse(recList);
                        recList.add(""+msg.obj);
                        Collections.reverse(recList);
                        recView.setAdapter(new ArrayAdapter<String>(context,android.R.layout.simple_list_item_1, recList));
                        toastPost("Received Message");
                        break;
                    case 2:
                        uuid= (String) msg.obj;
                        title.setText("Connected as "+msg.obj);
                        send_m.setVisibility(View.VISIBLE);
                        title.setBackgroundColor(getResources().getColor(R.color.colorConnect));
                        button.setEnabled(true);
                        break;
                }
            }
        };

        mBluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        t1 = new ConnectThread(mBluetoothAdapter.getRemoteDevice(hw_info), mBluetoothAdapter, mHandler);
        t1.start();

        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String mssg=edit.getText().toString();
                if (mssg.indexOf("'")<0 && mssg.indexOf('"')<0 ) {
                    t1.sendMsg(mssg);
                    if (msgList.indexOf(mssg)<0) {
                        Collections.reverse(msgList);
                        msgList.add(mssg);
                        Collections.reverse(msgList);
                        listView.setAdapter(new ArrayAdapter<String>(context, android.R.layout.simple_list_item_1, msgList));
                    }
                    edit.setText("");
                    edit.clearFocus();
                }else{
                    toastPost("Message not Acceptable");
                }
            }
        });

        listView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position,
                                    long id) {
                int total=msgList.size();
                Log.i("Clicked","Size:"+total+" pos:"+position);
                edit.setText(msgList.get(position));
                edit.animate();
            }
        });

    }

    public void toastPost(String str)
    {
        Toast.makeText(getApplicationContext(), str, Toast.LENGTH_SHORT).show();
    }
    @Override
    public void onBackPressed() {
        // your code.
        t1.cancel();
        finish();
    }
}
