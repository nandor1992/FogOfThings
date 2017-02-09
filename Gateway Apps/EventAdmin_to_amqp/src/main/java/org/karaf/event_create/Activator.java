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
import java.util.ArrayList;
import java.util.Dictionary;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.Constants;
import org.osgi.framework.ServiceRegistration;
import org.osgi.service.cm.ConfigurationException;
import org.osgi.service.cm.ManagedService;
import org.osgi.service.event.Event;
import org.osgi.service.event.EventConstants;
import org.osgi.service.event.EventHandler;

import com.rabbitmq.client.*;
import com.rabbitmq.client.impl.AMQBasicProperties;

public class Activator implements BundleActivator, EventHandler, ManagedService {
	
	private static BundleContext bcontext = null;
	private static final String DEVICE_QUEUE = "device/send";
	private static final String CLOUD_QUEUE = "cloud/send";
	private static final String REGION_QUEUE = "region/send";
	private static final String RESOURCE_QUEUE="resource/send";
	private static final String APP__REC_QUEUE = "app/receive/";
	private static final String APP__SEND_QUEUE = "app/send/";
	private static String CONFIG_PID = "org.karaf.messaging";
	ServiceRegistration register;
	ServiceRegistration register2;
	ServiceRegistration register3;
	ServiceRegistration register4;
	private static Connection connection;
	private static Channel channel;
	private ServiceRegistration ppcService;
	private static boolean configured=false;
	private List<ServiceRegistration> app_reg = new ArrayList<ServiceRegistration>();
	private List<String> send_apps = new ArrayList<String>();
	private List<String> rec_apps = new ArrayList<String>();
	
	public void start(BundleContext context) throws Exception {
		bcontext=context;
		Dictionary props = new Hashtable();
		props.put(Constants.SERVICE_PID, CONFIG_PID);
		ppcService = bcontext.registerService(ManagedService.class.getName(), this, props);
		
		System.out.println("Starting EventAdmin to AMQP");
		Dictionary cp = new Hashtable();
		cp.put(EventConstants.EVENT_TOPIC, CLOUD_QUEUE);
		Dictionary dp = new Hashtable();
		dp.put(EventConstants.EVENT_TOPIC, DEVICE_QUEUE);
		Dictionary rsp = new Hashtable();
		rsp.put(EventConstants.EVENT_TOPIC, RESOURCE_QUEUE);
		Dictionary rgp = new Hashtable();
		rgp.put(EventConstants.EVENT_TOPIC, REGION_QUEUE );
		// AMQP Stuff
		ConnectionFactory factory = new ConnectionFactory();
		factory.setUsername("admin");
		factory.setPassword("hunter");
		factory.setVirtualHost("test");
		factory.setHost("localhost");
		factory.setPort(5672);
		connection = factory.newConnection();
		channel = connection.createChannel();

		register = context.registerService(EventHandler.class.getName(), this, dp);
		register2 = context.registerService(EventHandler.class.getName(), this, cp);
		register3 = context.registerService(EventHandler.class.getName(), this, rsp);
		register4 = context.registerService(EventHandler.class.getName(), this, rgp);
	}

	public void handleEvent(Event event) {
		String[] names = event.getPropertyNames();
		String route_amqp = "";
		String type = event.getProperty("event.topics").toString();
		AMQP.BasicProperties.Builder builder = new AMQP.BasicProperties().builder();
		Map<String, Object> headerMap = new HashMap<String, Object>();
		for (String name : names) {
			if (!name.equals("event.topics") && !name.equals("payload")) {
				headerMap.put(name, event.getProperty(name).toString());
			}
			if (!name.equals("event.topics")){
				String rec_app=event.getProperty("event.topics").toString();
				String prts[]=rec_app.split("/");
				if (prts.length==3){
					if (send_apps.contains(prts[2])){
						headerMap.put("app_type", "send");
						headerMap.put("app_rec",prts[2]);
					}else if (rec_apps.contains(prts[2])){
						headerMap.put("app_type", "receive");
						headerMap.put("app_rec",prts[2]);
					}
				}
			}
		}
		builder.headers(headerMap);
		try {
			channel.basicPublish("apps", route_amqp, builder.build(), event.getProperty("payload").toString().getBytes());
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

	public void stop(BundleContext context) throws Exception {
		register.unregister();
		register2.unregister();
		channel.close();
		connection.close();
		System.out.println("Stopped EventAdmin to AMQP");
	}

	public void updated(Dictionary properties) throws ConfigurationException {
		// TODO Auto-generated method stub
		if (properties != null) {
			String apps = (String) properties.get("forward");
			String apps2 = (String) properties.get("proxy_back");
			if (apps!=null) {
				String [] app_name = apps.split(":");
				if (!configured) {
					for( ServiceRegistration reg : app_reg){
						reg.unregister();
					}
					send_apps.clear();
					rec_apps.clear();
				}
				for (String app : app_name){
					Dictionary dp = new Hashtable();
					dp.put(EventConstants.EVENT_TOPIC, APP__SEND_QUEUE + app);
					ServiceRegistration s_reg = bcontext.registerService(EventHandler.class.getName(), this, dp);
					app_reg.add(s_reg);
					send_apps.add(app);
				}
				app_name = apps2.split(":");
				for (String app : app_name){
					Dictionary dp = new Hashtable();
					dp.put(EventConstants.EVENT_TOPIC, APP__REC_QUEUE+ app);
					ServiceRegistration s_reg = bcontext.registerService(EventHandler.class.getName(), this, dp);
					app_reg.add(s_reg);
					rec_apps.add(app);
				}
			}
		}
		
	}

}
