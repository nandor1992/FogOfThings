package org.karaf.event_create;

import com.rabbitmq.client.*;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Dictionary;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Map;

import org.osgi.framework.BundleContext;
import org.osgi.framework.Constants;
import org.osgi.framework.ServiceReference;
import org.osgi.framework.ServiceRegistration;
import org.osgi.service.cm.ManagedService;
import org.osgi.service.event.Event;
import org.osgi.service.event.EventAdmin;

public class AmqpConnect extends Thread{
	private BundleContext bcontext = null;
	private ServiceReference sr = null;
	private EventAdmin ea = null;
	Event event = null;
	private Connection connection;
	private Channel channel;
	boolean sending = true;
	private Map data;
	private HashMap data2;
	private static final String DEVICE_QUEUE = "device/receive/";
	private static final String CLOUD_QUEUE = "cloud/receive/";
	private static final String REGION_QUEUE = "region/receive/";
	private static final String RESOURCE_QUEUE="resource/receive/";
	private static final String APP_SEND_QUEUE = "app/send/";
	private static final String APP_REC_QUEUE = "app/receive/";
	private final static String QUEUE_NAME = "karaf_app";
	// private static final String SEND_EVENT_QUEUE = "external/send";
	
	public AmqpConnect(BundleContext bc){
		this.bcontext = bc;
	}
	public void run() {
		
		// Retrieving the Event Admin service from the OSGi framework
		sr = this.bcontext.getServiceReference(EventAdmin.class.getName());
		try{
		if (sr == null) {
			throw new Exception("Failed to obtain EventAdmin service reference!");
		}
		ea = (EventAdmin) this.bcontext.getService(sr);
		if (ea == null) {
			throw new Exception("Failed to obtain EventAdmin service object!");
		}
		} catch (Exception e) {
			e.printStackTrace();
		}
			

		// AMQP Stuff
		ConnectionFactory factory = new ConnectionFactory();
		factory.setUsername("admin");
		factory.setPassword("hunter");
		factory.setVirtualHost("test");
		factory.setHost("localhost");
		factory.setPort(5672);
		try {
			connection = factory.newConnection();
			channel = connection.createChannel();
			channel.basicQos(1);
		} catch (IOException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		Consumer consumer = new DefaultConsumer(channel) {
			@Override
			public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties,
					byte[] body) throws IOException {
				String message = new String(body, "UTF-8");
				Map<String, Object> headers = properties.getHeaders();
				// display time and date using toString()
				try {
					sendEvent(message, headers);
				} catch (InterruptedException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				channel.basicAck(envelope.getDeliveryTag(), false);
			}
		};
		try {
			channel.basicConsume(QUEUE_NAME, false, consumer);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public void stopThis() {
		this.bcontext.ungetService(sr);
		try {
			channel.close();
			connection.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	private void sendEvent(String message, Map<String, Object> headers) throws InterruptedException {
		Dictionary props = new Hashtable();
		for (Map.Entry<String, Object> header : headers.entrySet()) {
			props.put(header.getKey(), header.getValue());
		}
		props.put("payload", message);
		if (props.get("device")!=null) {
			Event event = new Event(DEVICE_QUEUE + props.get("device"), props);
			ea.sendEvent(event);
		}else if (props.get("cloud")!=null) {
			Event event = new Event(CLOUD_QUEUE + props.get("app"), props);
			ea.sendEvent(event);
		}else if (props.get("region")!=null) {
			Event event = new Event(REGION_QUEUE + props.get("app"), props);
			ea.sendEvent(event);
		}else if (props.get("res")!=null) {
			Event event = new Event(RESOURCE_QUEUE + props.get("app"), props);
			ea.sendEvent(event);
		}else if (props.get("app")!=null){
			if (props.get("app_type")!=null && props.get("app_rec")!=null){
				if (props.get("app_type").toString().equals("receive")){
					String app=props.get("app_rec").toString();
					props.remove("app_type");
					props.remove("app_rec");
					Event event = new Event(APP_REC_QUEUE + app, props);
					ea.sendEvent(event);
				}else if (props.get("app_type").toString().equals("send")) {
					String app=props.get("app_rec").toString();
					props.remove("app_type");
					props.remove("app_rec");
					Event event = new Event(APP_SEND_QUEUE + app, props);
					ea.sendEvent(event);
				}
			}
		}
	}
}