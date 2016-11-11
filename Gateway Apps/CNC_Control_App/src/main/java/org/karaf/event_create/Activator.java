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
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import edu.emory.mathcs.backport.java.util.Collections;

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

public class Activator extends Thread implements BundleActivator, ManagedService {

	private static String DEVICE_QUEUE = "device/receive/";
	private static String DEVICE_SEND = "device/send";
	private static String APP_QUEUE = "cloud/receive/";
	private static String CLOUD_QUEUE = "cloud/send";
	public static Integer MAX_RETRANSMIT = 20;
	private BundleContext bcontext = null;
	ServiceReference sr = null;
	EventAdmin ea = null;
	Event event = null;
	boolean sending = true;
	private Map data;
	private HashMap data2;
	private String app_name = "test1";
	private ServiceRegistration ppcService;
	private ServiceRegistration register2;
	// Device
	private List<ServiceRegistration> dev_reg = new ArrayList<ServiceRegistration>();
	List<String> dev_names = new ArrayList<String>();
	private static String CONFIG_PID = "org.karaf.event_create";
	static Logger logger;
	private boolean configured = false;
	private Resolver resolv;

	public void start(BundleContext bc) throws Exception {
		this.bcontext = bc;
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
	}

	public void stop(BundleContext bc) throws Exception {
		bc.ungetService(sr);
		register2.unregister();
		ppcService.unregister();
		for (ServiceRegistration reg : dev_reg) {
			reg.unregister();
		}
		dev_reg.clear();
		logger.warn("Stopped Bundle");

	}

	public class SendEventHandler implements EventHandler {

		public void handleEvent(Event event) {
			resolv.doDeviceMsg(event);
		}

	}

	public class SendEventHandler2 implements EventHandler {

		public void handleEvent(Event event) {
			resolv.doCloudMsg(event);
		}

	}

	public void cloudSendEvent(String payload) {
		Dictionary props = new Hashtable();
		props.put("payload", payload);
		props.put("app", app_name);
		Event event = new Event(CLOUD_QUEUE, props);
		ea.sendEvent(event);
	}

	public void deviceSendEvent(String payload, String device) {
		Dictionary props = new Hashtable();
		props.put("payload", payload);
		props.put("device", device);
		Event event = new Event(DEVICE_SEND, props);
		ea.sendEvent(event);
	}

	public void updated(Dictionary properties) throws ConfigurationException {
		// TODO Auto-generated method stub
		// TODO Add registration of services if non existant full
		logger.warn("Update Entered");
		if (properties != null) {
			logger.info("Properties not null");
			String value = (String) properties.get("device");
			String app = (String) properties.get("app_name");
			if (value != null && app != null) {
				String[] part = value.split("'");
				List<String> temp = new ArrayList<String>();
				for (int i = 0; i < part.length; i++) {
					if ((i % 2) == 1) {
						temp.add(part[i]);
					}
				}
				reconfigureDev(temp);
				reconfigureApp(app);
				resolv = new Resolver(this);
				configured=true;
			}
		}
	}

	public void reconfigureDev(List<String> temp) {
		dev_names = temp;
		if (configured) {
			for (ServiceRegistration reg : dev_reg) {
				reg.unregister();
			}
		}
		dev_reg.clear();
		for (String name : dev_names) {
			Dictionary dp = new Hashtable();
			dp.put(EventConstants.EVENT_TOPIC, DEVICE_QUEUE + name);
			logger.warn("New Device Registered:" + name);
			ServiceRegistration reg_temp = bcontext.registerService(EventHandler.class.getName(),
					new SendEventHandler(), dp);
			dev_reg.add(reg_temp);
		}
	}

	public void reconfigureApp(String name) {
		app_name = name;
		if (configured) {
			register2.unregister();
		}
		Dictionary dp2 = new Hashtable();
		dp2.put(EventConstants.EVENT_TOPIC, APP_QUEUE + app_name);
		logger.warn("New App Name Reg:" + name);
		register2 = bcontext.registerService(EventHandler.class.getName(), new SendEventHandler2(), dp2);
	}
}
