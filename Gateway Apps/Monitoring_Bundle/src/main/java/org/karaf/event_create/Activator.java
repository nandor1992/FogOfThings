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
import java.util.Arrays;
import java.util.Dictionary;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Timer;
import java.util.TimerTask;

import org.apache.commons.collections.iterators.ArrayListIterator;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.Constants;
import org.osgi.framework.ServiceRegistration;
import org.osgi.service.cm.ConfigurationException;
import org.osgi.service.cm.ManagedService;
import org.osgi.service.event.Event;
import org.osgi.service.event.EventConstants;
import org.osgi.service.event.EventHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.rabbitmq.client.*;
import com.rabbitmq.client.impl.AMQBasicProperties;

public class Activator implements BundleActivator, EventHandler {
	
	private static BundleContext bcontext = null;
	private static final List<String> regs = Arrays.asList("device/send","device/receive/*",
															"cloud/send","cloud/receive/*",
															"region/send","region/receive/*",
															"resource/send","resource/receive/*",
															"app/receive/*","app/send/*");
	private static String CONFIG_PID = "org.karaf.messaging";
	private List <ServiceRegistration> register = new ArrayList<ServiceRegistration>();
	private static Connection connection;
	private static Channel channel;
	private static boolean configured=false;
	private List<String> send_apps = new ArrayList<String>();
	private List<String> rec_apps = new ArrayList<String>();
	private Timer timer = new Timer();
	private Monitor m1 = new Monitor();
	static Logger logger;
	
	private class Monitor{
		
		private Map<String, Integer>  device = new Hashtable();
		private Map<String, Integer>  cloud = new Hashtable();
		private Map<String, Integer>  resource = new Hashtable();
		private Map<String, Integer>  region = new Hashtable();
		private Map<String, Integer>  apps = new Hashtable();

		public String hashToJson(){
			String totString;
			totString="{'device':"+returnVars(device)+",";
			totString=totString+"'cloud':"+returnVars(cloud)+",";
			totString=totString+"'region':"+returnVars(region)+",";
			totString=totString+"'resource':"+returnVars(resource)+",";
			totString=totString+"'apps':"+returnVars(apps)+"}";
			return totString;
		}
		
		public String returnVars(Map<String, Integer>  map)
		{
			if( map.size()==0){
				return "{}";
			}else{
			String ret="{";
			for (Map.Entry<String, Integer> entry : map.entrySet()) {
				ret=ret.concat("'"+entry.getKey()+"':'"+entry.getValue()+"',");
			}	
			ret=ret.substring(0, ret.lastIndexOf(","))+"}";
			return ret;
			}
		}
		
		public void resolveAdd(String topic, String app, String dev)
		{
			String[] parts = topic.split("/");
			if (parts[0].equals("device"))
			{
				if (parts.length==3){
					addElement("device", parts[2]);
				}else{
					addElement("device", dev);
				}
				if (app!=null){
					addElement("device", app);
				}
			}else if (parts[0].equals("app")){
				if (parts.length==3){
					if (parts[2].equals(app)){
						addElement("apps", app);}
					else{
						addElement("apps", app);
						addElement("apps", parts[2]);
					}
				}else{addElement("apps",app);}
			}else{
				if (parts.length==3){
					addElement(parts[0],parts[2]);
				}
				else
				{
					addElement(parts[0], app);
				}
			}
		}
		
		public void clear()
		{
			device.clear();
			cloud.clear();
			resource.clear();
			region.clear();
			apps.clear();
		}
		private void addElement(String type,String app_dev)
		{
			
			if (type.equals("device")){
				if (device.get(app_dev)==null)
					device.put(app_dev, 1);
				else
					device.put(app_dev, device.get(app_dev));
			}
			if (type.equals("cloud")){
				if (cloud.get(app_dev)==null)
					cloud.put(app_dev, 1);
				else
					cloud.put(app_dev, cloud.get(app_dev));
			}
			if (type.equals("resource")){
				if (resource.get(app_dev)==null)
					resource.put(app_dev, 1);
				else
					resource.put(app_dev, resource.get(app_dev));
			};
			if (type.equals("region")){
				if (region.get(app_dev)==null)
					region.put(app_dev, 1);
				else
					region.put(app_dev, region.get(app_dev));
			}
			if (type.equals("apps")){
				if (apps.get(app_dev)==null)
					apps.put(app_dev, 1);
				else
					apps.put(app_dev, apps.get(app_dev));
			}
		}	
	}
	
	public class TimerTsk extends TimerTask {	
	    public void run(){
	    	publishMsg();
	    }
	}
	
	public void start(BundleContext context) throws Exception {
		bcontext=context;
		Dictionary props = new Hashtable();
		logger = LoggerFactory.getLogger(Activator.class.getName());
		// AMQP Stuff
		ConnectionFactory factory = new ConnectionFactory();
		factory.setUsername("admin");
		factory.setPassword("hunter");
		factory.setVirtualHost("test");
		factory.setHost("localhost");
		factory.setPort(5672);
		connection = factory.newConnection();
		channel = connection.createChannel();
		Dictionary dic;
		ServiceRegistration sr;
		for (String r: regs){
			dic = new Hashtable();
			dic.put(EventConstants.EVENT_TOPIC, r);
			sr = context.registerService(EventHandler.class.getName(), this, dic);
			register.add(sr);
		}
		
		timer.scheduleAtFixedRate(new TimerTsk(), 600000, 600000);
		logger.warn("Started Logging!");
	}

	public void publishMsg()
	{
		try {
			logger.warn("Published Log with"+m1.hashToJson());
			channel.basicPublish("", "monitor",null, m1.hashToJson().replace('\'', '"').getBytes());
			//m1.clear();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	
	public void handleEvent(Event event) {
		String type = event.getProperty("event.topics").toString();
		String app =(String) event.getProperty("app");
		String device =(String) event.getProperty("device");
		logger.warn("Event"+type+" "+app+" "+device);
		m1.resolveAdd(type, app, device);
	}
	
	public void stop(BundleContext context) throws Exception {
		for (ServiceRegistration s: register){
			s.unregister();
		}
		timer.cancel();
		channel.close();
		connection.close();
		logger.warn("Stopped EventAdmin to AMQP");
	}


}
