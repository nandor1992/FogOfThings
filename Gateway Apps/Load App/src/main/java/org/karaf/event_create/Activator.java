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
import org.osgi.framework.ServiceReference;
import org.osgi.framework.ServiceRegistration;
import org.osgi.service.cm.ConfigurationException;
import org.osgi.service.cm.ManagedService;
import org.osgi.service.event.Event;
import org.osgi.service.event.EventAdmin;
import org.osgi.service.event.EventConstants;
import org.osgi.service.event.EventHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.rabbitmq.client.*;
import com.rabbitmq.client.impl.AMQBasicProperties;


public class Activator implements BundleActivator,ManagedService {
	
	private static BundleContext bcontext = null;
	private static final List<String> regs = Arrays.asList("device/send");
	private static String CONFIG_PID = "org.karaf.load_app";
	private ServiceRegistration ppcService;
	private Timer timer = new Timer();
	static Logger logger;
	private int delay = 1000;
	private static EventAdmin ea;
	private static String device = "Test_Dev1";
	private Integer load = 1000;
	private Integer msg = 1;
	private static String name = "Load_App";
	private Load l1;
	private boolean run=true;
	
	class Loading extends Thread{  
		public void run(){  
	    	l1.doMatrice(load);
	    	l1.doFiltering(load);
	    	l1.doFlops(load);
		} 
	}
	
	public class TimerTsk extends TimerTask {	
	    public void run(){
	    	Thread.currentThread().setName(name);
	    	//Do create load somehow
	    	if (run==true){
	    		if (load>0){
			    	long timeBefore = System.nanoTime();
		    		Loading t1=new Loading();  
		    		Loading t2=new Loading();  
		    		Loading t3=new Loading();  
		    		Loading t4=new Loading();  
		    		t1.start();
		    		t2.start();
		    		t3.start();
		    		t4.start();
		    		try {
						t1.join();
						t2.join();
		    			t3.join();
		    			t4.join();
					} catch (InterruptedException e) {
						// TODO Auto-generated catch block
						logger.warn("Interrupt :"+e.getMessage());
					}
			    	long timeAfter = System.nanoTime();
			    	long elapsed_time = timeAfter - timeBefore;
			    	//logger.warn("Tasks Took:"+elapsed_time/1000);
	    		}	
			    	for (int i=0;i<msg;i++){
			    		sendEvent(); 
			    	}
		    	timer.schedule(new TimerTsk(),1000);
		    	//Check if events need sending
	    	}
	    }
	}
	
	public void start(BundleContext context) throws Exception {
		bcontext=context;
		Thread.currentThread().setName(name);
		Dictionary props = new Hashtable();
		logger = LoggerFactory.getLogger(Activator.class.getName());
		ServiceReference sr = bcontext.getServiceReference(EventAdmin.class.getName());
		if (sr == null) {
			throw new Exception("Failed to obtain EventAdmin service reference!");
		}
		ea = (EventAdmin) bcontext.getService(sr);
		
		Dictionary props2 = new Hashtable();
		props2.put(Constants.SERVICE_PID, CONFIG_PID);
		ppcService = bcontext.registerService(ManagedService.class.getName(), this, props2);
		timer.schedule(new TimerTsk(), delay);
		l1=new Load();
		logger.warn("Started Loading!");
	}

	private static void sendEvent() {
		Dictionary props = new Hashtable();
		props.put("app", name);
		props.put("payload","{This is a test payload that is of an avarage size for payloads sent by such devices}");
		props.put("device",device);
		logger.debug("APP" +props.get("device"));
		Event event = new Event(regs.get(0), props);
		ea.sendEvent(event);	
	}
	
	public void stop(BundleContext context) throws Exception {
		ppcService.unregister();
		timer.cancel();
		timer.purge();
		logger.warn("Stopped Logging!");
	}

	@Override
	public void updated(Dictionary properties) throws ConfigurationException {
		device = properties.get("device").toString().trim();
		load = Integer.parseInt(properties.get("load").toString().trim());
		msg= Integer.parseInt(properties.get("msg").toString().trim());
		logger.warn("Params Received, Dev: "+device+" Load: "+load+" Msg Cnt: "+msg);
	}


}
