package com.example.nandor.blutetest;

import android.bluetooth.BluetoothSocket;
import android.os.Handler;
import android.renderscript.RenderScript;
import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.util.Random;

/**
 * Created by Nandor on 9/6/2016.
 */
class ConnectedThread extends Thread {
    private final BluetoothSocket mmSocket;
    private final InputStream mmInStream;
    private final OutputStream mmOutStream;
    private Handler mHandler;
    private int rand;
    private String uuid;
    public ConnectedThread(BluetoothSocket socket,Handler h1) {
        mmSocket = socket;
        this.mHandler=h1;
        InputStream tmpIn = null;
        OutputStream tmpOut = null;

        // Get the input and output streams, using temp objects because
        // member streams are final
        try {
            tmpIn = socket.getInputStream();
            tmpOut = socket.getOutputStream();
        } catch (IOException e) { }

        mmInStream = tmpIn;
        mmOutStream = tmpOut;
    }

    public void run() {
        byte[] buffer = new byte[1024];  // buffer store for the stream
        int bytes; // bytes returned from read()

        // Keep listening to the InputStream until an exception occurs
        while (true) {
            try {
                // Read from the InputStream
                bytes = mmInStream.read(buffer);
                String readMessage = new String(buffer, 0, bytes);
                Log.i("Input BLuetooth", "Length:"+bytes+"value:"+readMessage);
                if (readMessage.charAt(0) == 'x')
                {
                    Random rnd = new Random(System.currentTimeMillis());
                    rand=rnd.nextInt(900) + 100;
                    String msg="{'e':[{'n':'cmd','u':'Anything'}],'bn':['urn:dev:type:AndroidPhone','urn:dev:mac:Android1','trans:id:"+rand+"'],'ver':'1'}\n";
                    Log.i("Received Reg-Sending",msg);
                    this.write(msg.getBytes());
                }else {
                    int ind1=readMessage.indexOf("urn:dev:id:");
                    if (readMessage.indexOf("trans:id")>0)
                    {
                        //Registered Stuff received
                        int ind2=readMessage.indexOf("'",ind1+6);
                        String uuid=readMessage.substring(ind1+11,ind2);
                        this.uuid=uuid;
                        Log.i("Register Resolve","Chars at indexes:"+readMessage.charAt(ind1+11)+" "+readMessage.charAt(ind2)+"String "+uuid);
                        mHandler.obtainMessage(2,uuid).sendToTarget();
                    }
                    else {
                        //Normals Messages
                        int ind_2=readMessage.indexOf("}]");
                        int ind_1=readMessage.indexOf("[{");
                        String msg=readMessage.substring(ind_1+1,ind_2+1);
                        mHandler.obtainMessage(1,msg).sendToTarget();
                        //TODO Add response maybe to messages received since it's a stupid device
                    }
                }
            } catch (IOException e) {
                break;
            }
        }
    }

    private void write(byte[] bytes)
    {
        try {
            mmOutStream.write(bytes);
        } catch (IOException e) { }
    }

    /* Call this from the main activity to send data to the remote device */
    public void write(String msg) {
        try {
            String send="{'e':[{'n':'cmd','v':'"+msg+"'}],'bn':'urn:dev:id:"+uuid+"'}\n";
            Log.i("Sending",send);

            mmOutStream.write(send.getBytes());
        } catch (IOException e) { }
    }

    /* Call this from the main activity to shutdown the connection */
    public void cancel() {
        try {
                mmSocket.close();
        } catch (IOException e) { }
    }
}