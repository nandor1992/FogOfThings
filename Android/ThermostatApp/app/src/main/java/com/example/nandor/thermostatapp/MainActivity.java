package com.example.nandor.thermostatapp;

import android.content.Intent;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageButton;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        ImageButton button_local= (ImageButton) findViewById(R.id.imageButton);
        ImageButton button_remote= (ImageButton) findViewById(R.id.imageButton2);
        button_local.setBackgroundColor(0);
        button_remote.setBackgroundColor(0);
        button_local.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent myIntent = new Intent(MainActivity.this, BlueMain.class);
                MainActivity.this.startActivity(myIntent);
            }
        });
        button_remote.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent myIntent = new Intent(MainActivity.this, Messaging.class);
                MainActivity.this.startActivity(myIntent);
            }
        });
    }
}
