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
import java.util.Date;
import java.util.Dictionary;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Map;
import java.util.Random;

import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.ServiceReference;
import org.osgi.framework.ServiceRegistration;
import org.osgi.service.event.Event;
import org.osgi.service.event.EventAdmin;
import org.osgi.service.event.EventConstants;
import org.osgi.service.event.EventHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Activator extends Thread implements BundleActivator {

	private static final String DEVICE_QUEUE = "device/receive/";
	private static final String DEVICE_SEND = "device/send";
	private static final String DEVICE = "dummy1";
	private static final String APP_NAME = "cnc_dev_app_dummy";
	private BundleContext bcontext = null;
	ServiceReference sr = null;
	EventAdmin ea = null;
	Event event = null;
	boolean sending = true;
	private Map data;
	private HashMap data2;
	private String dev_name = "OqfPAajc";
	private ServiceRegistration register;
	static Logger logger;
	Random rand = new Random();
	
	public void start(BundleContext bc) throws Exception {
		this.bcontext = bc;
		
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
		Dictionary dp = new Hashtable();
		dp.put(EventConstants.EVENT_TOPIC, DEVICE_SEND);
		register = bcontext.registerService(EventHandler.class.getName(), new SendEventHandler(), dp);

	}

	public void stop(BundleContext bc) throws Exception {
		bc.ungetService(sr);
		register.unregister();

	}

	public class SendEventHandler implements EventHandler {

		public void handleEvent(Event event) {
			long sleepy = 0;
			double chance_retr = Math.random() * 100;
			if (chance_retr > 2.0) {
				long delay=(long)(rand.nextGaussian()*220);
				if (delay<-430)
				{
					delay=-430;
				}
				try {
					Thread.sleep(470+delay);
				} catch (InterruptedException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				mysendEvent("[{'v':'ok','n':'Resp'}]");
			}
		}

	}

	private void mysendEvent(String payload) {
		Dictionary props = new Hashtable();
		props.put("payload", payload);
		props.put("device", DEVICE);
		Event event = new Event(DEVICE_QUEUE + DEVICE, props);
		ea.sendEvent(event);
	}

}
