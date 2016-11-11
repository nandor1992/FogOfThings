package com.example.nandor.thermostatapp;

/**
 * Created by Nandor on 09-Nov-16.
 */
import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import android.os.Handler;

import java.util.Random;

public class MqttConnect implements MqttCallback {
    private String address;
    private String port;
    private String user_n;
    private String user_p;
    private String gateway_id;
    private String app;
    private MqttClient sampleClient;
    private Handler h1;

    public MqttConnect(String[] variables, Handler h1){
        this.address=variables[0];
        this.port=variables[1];
        this.user_n=variables[2];
        this.user_p=variables[3];
        this.gateway_id=variables[4];
        this.app=variables[5];
        this.h1=h1;
        this.connect();
    }

    public String disconnect(){
        try {
            sampleClient.disconnect();
        } catch (MqttException e) {
            e.printStackTrace();
        }
        System.out.println("Disconnected");
        return "Success";
    }

    public String publish(String data){
        System.out.println("Publishing message: "+data);
        String msg="{\"app\":\""+this.app+"\",\"payload\":\""+data+"\"}";
        MqttMessage message = new MqttMessage();
        message.setPayload(msg.getBytes());
        message.setQos(0);
        String topic = "receive/"+this.gateway_id;
        try {
            sampleClient.publish(topic, message);
        } catch (MqttException e) {
            e.printStackTrace();
            return "Error";
        }
        System.out.println("Message published");
        return "Success";
    }

    public String connect() {

        String topic_list    = "send/"+this.gateway_id;
        String broker       = "tcp://"+this.address+":"+port;
        Random r = new Random();
        String clientId     = "Android App"+String.valueOf(r.nextInt(1000));
        MemoryPersistence persistence = new MemoryPersistence();

        try {
            sampleClient = new MqttClient(broker, clientId, persistence);
            MqttConnectOptions connOpts = new MqttConnectOptions();
            connOpts.setCleanSession(true);
            connOpts.setUserName(this.user_n);
            connOpts.setPassword(this.user_p.toCharArray());
            System.out.println("Connecting to broker: "+broker);
            sampleClient.connect(connOpts);
            System.out.println("Connected");
            sampleClient.setCallback(this);
            sampleClient.subscribe(topic_list);
            return "Success";
        } catch(MqttException me) {
            System.out.println("reason "+me.getReasonCode());
            System.out.println("msg "+me.getMessage());
            System.out.println("loc "+me.getLocalizedMessage());
            System.out.println("cause "+me.getCause());
            System.out.println("excep "+me);
            me.printStackTrace();
            return "Errors";
        }
    }

    @Override
    public void connectionLost(Throwable cause) {
        try {
            sampleClient.reconnect();
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void messageArrived(String topic, MqttMessage message) throws Exception {
        String msg=message.toString();
        System.out.println(msg);
        h1.obtainMessage(1,msg).sendToTarget();
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {

    }
}