package com.example.nandor.thermostatapp;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.os.Handler;
import android.util.Log;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;


/**
 * Created by Nandor on 9/6/2016.
 */
class ConnectThread extends Thread {
    private final BluetoothSocket mmSocket;
    private final BluetoothDevice mmDevice;
    private BluetoothAdapter mBluetoothAdapter;
    private Handler mHandler;
    private ConnectedThread t1;
    private boolean error=false;
    public ConnectThread(BluetoothDevice device, BluetoothAdapter mBlue, Handler h1) {
        // Use a temporary object that is later assigned to mmSocket,
        // because mmSocket is final
        this.mHandler=h1;
        BluetoothSocket tmp = null;
        this.mmDevice = device;
        this.mBluetoothAdapter=mBlue;
        // Get a BluetoothSocket to connect with the given BluetoothDevice
            // MY_UUID is the app's UUID string, also used by the server code
            Method m = null;
            try {
                m = mmDevice.getClass().getMethod("createInsecureRfcommSocket", new Class[] {int.class});
            } catch (NoSuchMethodException e) {
                e.printStackTrace();
            }
            try {
                tmp = (BluetoothSocket) m.invoke(device, 1);
            } catch (IllegalAccessException e) {
                e.printStackTrace();
            } catch (InvocationTargetException e) {
                e.printStackTrace();
            }
            mmSocket = tmp;
    }

    public void run() {
        // Cancel discovery because it will slow down the connection
        mBluetoothAdapter.cancelDiscovery();

        try {
            // Connect the device through the socket. This will block
            // until it succeeds or throws an exception
            mmSocket.connect();
            Log.i("Connected","To Device"+ mmDevice.getName());
            t1=new ConnectedThread(mmSocket,this.mHandler);
            t1.start();
        } catch (IOException connectException) {
            // Unable to connect; close the socket and get out
            try {
                mmSocket.close();
                Log.i("Connected Exception",connectException.toString());
                error=true;
            } catch (IOException closeException) { }
            return;
        }

        // Do work to manage the connection (in a separate thread)
        //manageConnectedSocket(mmSocket);
    }

    public void sendMsg(String msg)
    {
        t1.write(msg);
    }
    /** Will cancel an in-progress connection, and close the socket */
    public void cancel() {
        if (!error) {
            t1.cancel();
        }
    }
}