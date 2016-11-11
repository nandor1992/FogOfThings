/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.karaf.event_create;

import java.io.IOException;
import java.sql.Timestamp;
import java.util.Dictionary;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.json.*;

import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.ServiceRegistration;
import org.osgi.service.event.Event;
import org.osgi.service.event.EventConstants;
import org.osgi.service.event.EventHandler;

import com.rabbitmq.client.*;
import com.rabbitmq.client.impl.AMQBasicProperties;

public class Activator implements BundleActivator, EventHandler {

	private static final String DEVICE_QUEUE = "device/send";
	private static final String CLOUD_QUEUE = "cloud/send";
	ServiceRegistration register;
	ServiceRegistration register2;
	private static Connection connection;
	private static Channel channel;

	public void start(BundleContext context) throws Exception {
		System.out.println("Starting EventAdmin to AMQP");
		Dictionary cp = new Hashtable();
		cp.put(EventConstants.EVENT_TOPIC, CLOUD_QUEUE);
		Dictionary dp = new Hashtable();
		dp.put(EventConstants.EVENT_TOPIC, DEVICE_QUEUE);
		// AMQP Stuff
		ConnectionFactory factory = new ConnectionFactory();
		factory.setUsername("admin");
		factory.setPassword("hunter");
		factory.setHost("10.0.0.133");
		factory.setPort(5672);

		connection = factory.newConnection();
		channel = connection.createChannel();

		register = context.registerService(EventHandler.class.getName(), this, dp);
		register2 = context.registerService(EventHandler.class.getName(), this, cp);
	}

	public void handleEvent(Event event) {
		String[] names = event.getPropertyNames();
		String type = event.getProperty("event.topics").toString();
		String message = "";
		AMQP.BasicProperties.Builder builder = new AMQP.BasicProperties().builder();
		Map<String, Object> headerMap = new HashMap<String, Object>();
		headerMap.put("app", "hello");
		builder.headers(headerMap);
		JSONObject obj = new JSONObject();
		try {
			if (type == DEVICE_QUEUE) {

			}
			if (type == CLOUD_QUEUE) {
				for (String name : names) {
					if (name != "event.topics") {
						obj.put(name, event.getProperty(name).toString());
					}
				}
				message = obj.toString().replace("\\", "");
				message = obj.toString().replace("\'", "'");
				try {
					channel.basicPublish("amq.topic", "send.gateway2", builder.build(), message.getBytes());
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		} catch (JSONException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}

	}

	public void stop(BundleContext context) throws Exception {
		register.unregister();
		register2.unregister();
		channel.close();
		connection.close();
		System.out.println("Stopped EventAdmin to AMQP");
	}

}
