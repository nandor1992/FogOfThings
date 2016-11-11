package org.rabbitmq.test;

import com.rabbitmq.client.*;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Dictionary;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Map;
import org.json.*;

import org.osgi.framework.BundleContext;
import org.osgi.framework.ServiceReference;
import org.osgi.service.event.Event;
import org.osgi.service.event.EventAdmin;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AmqpConnect {
	private static BundleContext bcontext = null;
	static ServiceReference sr = null;
	static EventAdmin ea = null;
	Event event = null;
	private static Connection connection;
	private static Channel channel;
	boolean sending = true;
	private Map data;
	private HashMap data2;
	private static final String DEVICE_QUEUE = "device/receive/";
	private static final String CLOUD_QUEUE = "cloud/receive/";
	private final static String QUEUE_NAME = "karaf_app";
	private static Logger logger;
	// private static final String SEND_EVENT_QUEUE = "external/send";

	public static void startThis(BundleContext bc) throws Exception {
		bcontext = bc;
		logger = LoggerFactory.getLogger(Activator.class.getName());
		// Retrieving the Event Admin service from the OSGi framework
		sr = bc.getServiceReference(EventAdmin.class.getName());
		if (sr == null) {
			throw new Exception("Failed to obtain EventAdmin service reference!");
		}
		ea = (EventAdmin) bc.getService(sr);
		if (ea == null) {
			throw new Exception("Failed to obtain EventAdmin service object!");
		}

		// AMQP Stuff
		ConnectionFactory factory = new ConnectionFactory();
		factory.setUsername("admin");
		factory.setPassword("hunter");
		factory.setVirtualHost("/");
		factory.setHost("10.0.0.133");
		factory.setPort(5672);
		connection = factory.newConnection();
		channel = connection.createChannel();
		Consumer consumer = new DefaultConsumer(channel) {
			@Override
			public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties,
					byte[] body) throws IOException {
				String message = new String(body, "UTF-8");
				Map<String, Object> headers = properties.getHeaders();
				// display time and date using toString()
				try {
					sendEvent(message, envelope.getRoutingKey());
				} catch (InterruptedException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		};
		channel.basicConsume(QUEUE_NAME, true, consumer);
	}

	public static void stopThis() {
		bcontext.ungetService(sr);
		try {
			channel.close();
			connection.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	private static void sendEvent(String message, String routingKey) throws InterruptedException {
		Dictionary props = new Hashtable();
		try {
			JSONObject obj = new JSONObject(message);
			String[] elementNames = JSONObject.getNames(obj);
			for (String name : elementNames) {
				props.put(name, obj.get(name).toString());
				logger.debug(name +" + "+ obj.get(name).toString());
			}
			if (props.get("device") != null) {
				logger.debug("Device" +props.get("device"));
				Event event = new Event(DEVICE_QUEUE + props.get("device"), props);
				ea.sendEvent(event);
			}
			if (props.get("app") != null) {
				logger.debug("APP" +props.get("device"));
				Event event = new Event(CLOUD_QUEUE + props.get("app"), props);
				ea.sendEvent(event);
			}
		} catch (JSONException e) {
			// TODO Auto-generated catch block
			logger.error("Json"+e.toString());
		}
	}
}