package com.example.nandor.thermostatapp;

import android.content.Intent;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.*;

public class Messaging extends AppCompatActivity {
    private Button button_connect;
    private EditText addr;
    private EditText port;
    private EditText user;
    private EditText pass;
    private EditText gw;
    private EditText app;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_messaging);
        button_connect = (Button) findViewById(R.id.button5);
        addr = (EditText) findViewById(R.id.editText6);
        port = (EditText) findViewById(R.id.editText5);
        user = (EditText) findViewById(R.id.editText3);
        pass = (EditText) findViewById(R.id.editText);
        gw = (EditText) findViewById(R.id.editText2);
        app =(EditText) findViewById(R.id.editText4);

        button_connect.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent myIntent = new Intent(Messaging.this, MqttActivity.class);
                String conn= ""+addr.getText().toString()+" "+port.getText().toString()+" "+user.getText().toString()+" "+pass.getText().toString()+" "+gw.getText().toString()+" "+app.getText().toString();
                myIntent.putExtra("conn", conn);
                Messaging.this.startActivity(myIntent);
            }
        });

    }
}
