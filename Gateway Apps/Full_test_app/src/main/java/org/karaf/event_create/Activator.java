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

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.Dictionary;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.Timer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import edu.emory.mathcs.backport.java.util.Collections;

import org.karaf.event_create.Activator.CloudEventHandler;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.Constants;
import org.osgi.framework.ServiceReference;
import org.osgi.framework.ServiceRegistration;
import org.osgi.service.cm.ConfigurationException;
import org.osgi.service.cm.ManagedService;
import org.osgi.service.event.Event;
import org.osgi.service.event.EventAdmin;
import org.osgi.service.event.EventConstants;
import org.osgi.service.event.EventHandler;
import java.util.TimerTask;

public class Activator implements BundleActivator, ManagedService {

	private static final String DEVICE_QUEUE = "device/receive/";
	private static final String CLOUD_QUEUE = "cloud/receive/";
	private static final String REGION_QUEUE = "region/receive/";
	private static final String RESOURCE_QUEUE="resource/receive/";
	private static final String APP_QUEUE = "app/receive";
	private static final String APP_SEND = "app/send";
	private static final String DEVICE_SEND = "device/send";
	private static final String CLOUD_SEND = "cloud/send";
	private static final String REGION_SEND = "region/send";
	private static final String RESOURCE_SEND="resource/send";
	
	private BundleContext bcontext = null;
	ServiceReference sr = null;
	EventAdmin ea = null;
	private String app_name = "test1";
	private String reg_name = "";
	private String reg_api = "";
	private String dev_msg = "test";
	private List<String> devs = new ArrayList<String>();
	private List<String> apps = new ArrayList<String>();
	private ServiceRegistration ppcService;
	// Device
	private List<ServiceRegistration> reg = new ArrayList<ServiceRegistration>();
	private static String CONFIG_PID = "org.karaf.full_test2";
	static Logger logger;
	private boolean configured = false;
	
	public void start(BundleContext bc) throws Exception {
		this.bcontext = bc;
		Thread.currentThread().setName("Test_App2");
		logger = LoggerFactory.getLogger(Activator.class.getName());
		// Context stuff
		Dictionary props = new Hashtable();
		props.put(Constants.SERVICE_PID, CONFIG_PID);
		ppcService = bcontext.registerService(ManagedService.class.getName(), this, props);

		// Other more Event Admin and basic stuff;
		// Retrieving the Event Admin service from the OSGi framework
		sr = bc.getServiceReference(EventAdmin.class.getName());
		if (sr == null) {
			throw new Exception("Failed to obtain EventAdmin service reference!");
		}
		ea = (EventAdmin) bc.getService(sr);
		if (ea == null) {
			throw new Exception("Failed to obtain EventAdmin service object!");
		}
		//Add control loop here 
	}

	public void stop(BundleContext bc) throws Exception {
		bc.ungetService(sr);
		ppcService.unregister();
		for (ServiceRegistration r : reg) {
			r.unregister();
		}
		reg.clear();
		logger.warn("Stopped Bundle");
		
	}

	public class MainEventHandler implements EventHandler {

		public void handleEvent(Event event) {
			//What happens when devices send messages
			Thread.currentThread().setName("Test_App2");
			String value = event.getProperty("payload").toString();
			String topic = event.getTopic();
			String params[] = event.getPropertyNames();
			Dictionary send = new Hashtable();
			for (String param : params){
				if (!param.equals("event.topics")){
					send.put(param,event.getProperty(param).toString());
				}
			}
			logger.warn("Received from: "+topic+" what: "+value);
			CloudSendEvent(send);
		}

	}

	public class CloudEventHandler implements EventHandler {

		public void handleEvent(Event event) {
			//What happens when devices send messages
			Thread.currentThread().setName("Test_App2");
			String value = event.getProperty("payload").toString();
			String topic = event.getTopic();
			Dictionary send = new Hashtable();
			String params[]=value.split(":");
			logger.warn("Received from: "+topic+" what: "+value);
			switch(params[0]){
				case "device": 
					logger.warn("Device Message");
					int cnt=Integer.parseInt(params[1]);
					if (cnt < devs.size()){
						send.put("device", devs.get(cnt));
						send.put("payload",dev_msg);
						MainSendEvent(send,DEVICE_SEND);
					}
					break;
				case "app": 
					logger.warn("App Message");	
					int cnt2=Integer.parseInt(params[1]);
					if (cnt2 < apps.size()){
						send.put("payload",params[2]);
						MainSendEvent(send,APP_SEND+"/"+apps.get(cnt2));
					}
					break;
				case "resource": 
					logger.warn("Resource Message");
					send.put("payload",params[1]);
					send.put("res", "storage");
					send.put("task","add");
					MainSendEvent(send,RESOURCE_SEND);
					break;
				case "region": 
					logger.warn("Region Message");	
					send.put("payload",params[1]);
					send.put("region", reg_name);
					send.put("key",reg_api);
					MainSendEvent(send,REGION_SEND);
					break;
				default:
					logger.warn("Unknown Message");
					break;
			}
			
		}

	}
	
	public void MainSendEvent(Dictionary args,String location) {
		args.put("app", app_name);
		Event event = new Event(location, args);
		ea.sendEvent(event);
		logger.warn("Sending event to: "+location+"with payload"+args.get("payload"));
	}
	
	public void CloudSendEvent(Dictionary args) {
		args.put("app", app_name);
		Event event = new Event(CLOUD_SEND, args);
		ea.sendEvent(event);
		logger.warn("Sending event to cloud with payload"+args.get("payload"));
	}

	public void updated(Dictionary properties) throws ConfigurationException {
		// TODO Auto-generated method stub
		// TODO Add registration of services if non existant full
		logger.warn("Update Entered");
		Thread.currentThread().setName("Test_App2");
		if (properties != null) {
			logger.info("Properties not null");
			String devices =properties.get("dev_ardRF24CNC").toString().trim();
			devices=devices.concat(":"+properties.get("dev_AndroidPhone").toString().trim());
			app_name = properties.get("name").toString().trim();
			Thread.currentThread().setName(app_name);
			String resource =properties.get("resources").toString().trim();
			String clouds = properties.get("cloud").toString().trim();
			String region = properties.get("region").toString().trim();
			String loc_apps = properties.get("apps").toString().trim();
			dev_msg = properties.get("dev_message").toString();
			if (configured==true){
				for (ServiceRegistration r :reg){
					r.unregister();
				}
			}
			//Registering Events for components
			//Resource
			Dictionary dp = new Hashtable();
			dp.put(EventConstants.EVENT_TOPIC, RESOURCE_QUEUE + app_name);
			logger.warn("Resource Registered Storage");
			ServiceRegistration r = bcontext.registerService(EventHandler.class.getName(), new MainEventHandler(), dp);
			reg.add(r);
			//Device
			String d_parts[]=devices.split(":");
			for (String d:d_parts){
				devs.add(d);
				Dictionary dp_d = new Hashtable();
				dp_d.put(EventConstants.EVENT_TOPIC, DEVICE_QUEUE + d.trim());
				logger.warn("Device Registered as :"+d.trim());
				ServiceRegistration d_r = bcontext.registerService(EventHandler.class.getName(), new MainEventHandler(), dp_d);
				reg.add(d_r);
			}
			//Cloud
			dp = new Hashtable();
			dp.put(EventConstants.EVENT_TOPIC, CLOUD_QUEUE + app_name);
			logger.warn("Cloud Registered");
			r = bcontext.registerService(EventHandler.class.getName(), new CloudEventHandler(), dp);
			reg.add(r);
			//Region
			dp = new Hashtable();
			dp.put(EventConstants.EVENT_TOPIC, REGION_QUEUE + app_name);
			String regs[]=region.split(";");
			reg_api=regs[1];
			reg_name=regs[0];
			logger.warn("Region Registered as :"+reg_name+"with api:"+reg_api);
			r = bcontext.registerService(EventHandler.class.getName(), new MainEventHandler(), dp);
			reg.add(r);
			//apps
			String a_parts[]=loc_apps.split(":");
			for (String a:a_parts){
				apps.add(a);
				Dictionary dp_a = new Hashtable();
				dp_a.put(EventConstants.EVENT_TOPIC, APP_QUEUE+ a.trim());
				logger.warn("App Registered as :"+a.trim());
				ServiceRegistration d_r = bcontext.registerService(EventHandler.class.getName(), new MainEventHandler(), dp_a);
				reg.add(d_r);
			}
			configured=true;
		}
	}
	
}
