package com.example.nandor.thermostatapp;

import android.bluetooth.BluetoothAdapter;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.support.v7.app.AppCompatActivity;
import android.text.InputType;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.*;

import java.util.ArrayList;
import java.util.List;

public class MqttActivity extends AppCompatActivity {
        private MqttConnect mqttClient;
        private Handler mHandler;
        private Context context;
        private ArrayList<String> msgList= new ArrayList<String>();
        private ArrayList<String> recList= new ArrayList<String>();
        private Button button_state;
        private Button button_getSet;
        private Button button_updSet;
        private Button button_addRow;
        private TextView text_state;
        private TableLayout tl;
        private List<TableRow> tableR= new ArrayList<TableRow>();
        private List<Integer> hour= new ArrayList<Integer>();
        private List<Integer> temp= new ArrayList<Integer>();
        private View.OnClickListener mClickListener;
        @Override
        protected void onCreate(Bundle savedInstanceState) {
            super.onCreate(savedInstanceState);
            setContentView(R.layout.activity_talk);
            Intent intent = getIntent();
            this.context=this;
            String[] conn = intent.getStringExtra("conn").split(" "); //if it's a string you stored.
            final TextView title = (TextView) findViewById(R.id.textView);
            final TextView dev = (TextView) findViewById(R.id.textView2);
            dev.setText(conn[0]);
            button_state= (Button) findViewById(R.id.button2);
            button_getSet=(Button) findViewById(R.id.button3);
            button_updSet=(Button) findViewById(R.id.button);
            button_addRow=(Button) findViewById(R.id.button4);
            text_state = (TextView) findViewById(R.id.textView3);
            button_state.setEnabled(false);
            button_getSet.setEnabled(false);
            button_updSet.setEnabled(false);
            //Table add stuff
            tl = (TableLayout) findViewById(R.id.table_layout);

            button_updSet.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    String send="";
                    for (TableRow tr : tableR)
                    {
                        TextView t1=(TextView)tr.getChildAt(0);
                        TextView t2=(TextView)tr.getChildAt(1);
                        send=send.concat(t1.getText()+"-"+t2.getText()+",");
                    }
                    if (!send.equals("")) {
                        mqttClient.publish("set:" + send.substring(0, send.length() - 1));
                    }
                }
            });

            button_addRow.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    toastPost("Add Row");
                    TableRow tr = new TableRow(MqttActivity.this);
                    EditText text1 = new EditText(MqttActivity.this);
                    text1.setInputType(InputType.TYPE_CLASS_NUMBER);
                    text1.setText("00");
                    text1.setImeOptions(EditorInfo.IME_ACTION_DONE);
                    text1.setMaxWidth(130);
                    tr.addView(text1);
                    EditText text2 = new EditText(MqttActivity.this);
                    text2.setText("00");
                    text2.setInputType(InputType.TYPE_CLASS_NUMBER);
                    text2.setMaxWidth(130);
                    text2.setImeOptions(EditorInfo.IME_ACTION_DONE);
                    tr.addView(text2);
                    ImageButton img1 =new ImageButton(MqttActivity.this);
                    ((ImageButton) img1).setImageResource(R.drawable.trash);
                    img1.setBackgroundColor(0);
                    img1.setTag(tr);
                    img1.setOnClickListener(mClickListener);
                    tr.addView(img1);
                    tableR.add(tr);
                    tl.addView(tr,tableR.size());
                }
            });

            button_state.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    mqttClient.publish("get:state");
                }
            });

            button_getSet.setOnClickListener(new View.OnClickListener(){

                @Override
                public void onClick(View v) {
                    mqttClient.publish("get:ref");
                }
            });

            mClickListener = new View.OnClickListener() {
                @Override
                public void onClick(View view) {
                    tableR.remove((TableRow) view.getTag());
                    tl.removeView((TableRow)view.getTag());
                }
            };

            mHandler = new Handler() {
                @Override
                public void handleMessage(Message msg) {
                    switch (msg.what) {
                        case 1:
                            //received.setText(""+msg.obj);
                            String rec=""+msg.obj;
                            int ind1=rec.indexOf("payload");
                            int ind2=rec.indexOf('"',ind1+12);
                            String rec2=rec.substring(ind1+11,ind2);
                            resolveReceived(rec2.replace('_',' '));
                            toastPost("Received Message");
                            break;
                    }
                }
            };

            mqttClient = new MqttConnect(conn,mHandler);
            if (mqttClient.connect().equals("Success"))
            {
                title.setText("Connected!");
                title.setBackgroundColor(getResources().getColor(R.color.colorConnect));
                button_state.setEnabled(true);
                button_getSet.setEnabled(true);
                button_updSet.setEnabled(true);
            } else{
                title.setText("Connection Failed");
            }

        }

        public void resolveReceived(String str)
        {
            if (str.substring(0,4).equals("Temp")){
                text_state.setText(str);
            } else if (str.substring(0,4).equals("Sche"))
            {
                String[] comps=str.split(":")[1].split(",");
                resolveSched(comps);
            }
        }

        public void resolveSched(String[] comps)
        {
            int i=0;
            for ( TableRow table : tableR){
                tl.removeView(table);
            }
            tableR.clear();
            for (String str : comps){
                    String[] parts=str.split("-");
                    TableRow tr = new TableRow(this);
                    EditText text1 = new EditText(this);
                    text1.setInputType(InputType.TYPE_CLASS_NUMBER);
                    text1.setText(""+parts[0]);
                    text1.setImeOptions(EditorInfo.IME_ACTION_DONE);
                    tr.addView(text1);
                    EditText text2 = new EditText(this);
                    text2.setText(""+parts[1]);
                    text2.setInputType(InputType.TYPE_CLASS_NUMBER);
                    text2.setImeOptions(EditorInfo.IME_ACTION_DONE);
                    tr.addView(text2);
                    ImageButton img1 =new ImageButton(this);
                    ((ImageButton) img1).setImageResource(R.drawable.trash);
                    img1.setBackgroundColor(0);
                    img1.setTag(tr);
                    img1.setOnClickListener(mClickListener);
                    tr.addView(img1);
                    tableR.add(tr);
                    tl.addView(tr,i+1);
                    i++;
            }
        }
        public void toastPost(String str)
        {
            Toast.makeText(getApplicationContext(), str, Toast.LENGTH_SHORT).show();
        }
        @Override
        public void onBackPressed() {
            // your code.
            mqttClient.disconnect();
            finish();
        }
    }