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

public class Activator extends Thread implements BundleActivator, ManagedService {

	private static final String DEVICE_QUEUE = "device/receive/";
	private static final String CLOUD_QUEUE = "cloud/receive/";
	private static final String REGION_QUEUE = "region/receive/";
	private static final String RESOURCE_QUEUE="resource/receive/";
	private static final String DEVICE_SEND = "device/send";
	private static final String CLOUD_SEND = "cloud/send";
	private static final String REGION_SEND = "region/send/";
	private static final String RESOURCE_SEND="resource/send/";
	
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
	private Schedule mySched;
	// Device
	private List<ServiceRegistration> dev_reg = new ArrayList<ServiceRegistration>();
	List<String> dev_names = new ArrayList<String>();
	private static String CONFIG_PID = "org.karaf.thermostat";
	static Logger logger;
	private boolean configured = false;
	private Timer t1;
	private String mqtt_conn="mqtt_conn1";
	//App Values
	private int relayValue=0;
	private int proprelayValue=0;
	private int confirm_rel=0;
	//Avarage n stuff
	private double recVal = 0.0;
	private int recCount = 0;
	private double recAvg = 0.0;
	
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
		mySched = new Schedule();
		t1=new Timer();
		t1.scheduleAtFixedRate(new TimerTsk(), 300000, 300000);
		//Add control loop here 
	}

	public void stop(BundleContext bc) throws Exception {
		bc.ungetService(sr);
		ppcService.unregister();
		register2.unregister();
		for (ServiceRegistration reg : dev_reg) {
			reg.unregister();
		}
		dev_reg.clear();
		t1.cancel();
		logger.warn("Stopped Bundle");
		
	}

	public class TimerTsk extends TimerTask {
		
		    public void run(){
		        //toy implementation
				logger.warn("Timer Task Running");
				Date dt = new Date(); 
				int hours=dt.getHours();
				if (recCount > 0){
				recAvg=recVal/recCount;
				recCount=0;
				recVal=0;
				}
				logger.warn("For time and temp:"+String.valueOf(hours)+":"+mySched.getTemp(hours)+"curr tmp:"+recAvg);
				logger.warn("Params: "+confirm_rel+" : "+String.valueOf(relayValue)+" : "+String.valueOf(proprelayValue));
				if ( (recAvg > 0.0) && (recAvg+1.0)<=mySched.getTemp(hours)){
					if((confirm_rel==1) && (relayValue==0)){
					deviceSendEvent("[{'n':'relay','v':'1'}]", dev_names.get(2));
					proprelayValue=1;
					}else if (confirm_rel==0){
						deviceSendEvent("[{'n':'relay','v':'1'}]", dev_names.get(2));
						proprelayValue=1;
					}
				} 
				if ((recAvg > 0.0) && (recAvg>=mySched.getTemp(hours))){
					if((confirm_rel==1) && (relayValue==1)){
					deviceSendEvent("[{'n':'relay','v':'0'}]", dev_names.get(2));
					proprelayValue=0;
					}else if (confirm_rel==0){
						deviceSendEvent("[{'n':'relay','v':'0'}]", dev_names.get(2));
						proprelayValue=0;
					}
				}
		    }
	}
	public class SendEventHandler implements EventHandler {

		public void handleEvent(Event event) {
			//What happens when devices send messages
			String value = event.getProperty("payload").toString();
			String comm = event.getProperty("device").toString();
			String send="";
			String commun = event.getProperty("comm").toString();
			int dev_ind=dev_names.indexOf(comm.trim());
			if (dev_ind==0)
			{
			//ard Uno Temp Msg
				int ind1=value.indexOf("'v':");
				int ind2=value.indexOf("'",ind1+8);
				String command=value.substring(ind1+5,ind2);
				recVal+=Double.parseDouble(command);
				recCount+=1;
				logger.warn("Received: "+command+" New value="+String.valueOf(recVal/recCount));
			}
			else if (dev_ind==1)
			{
				int ind1=value.indexOf("'v':");
				int ind2=value.indexOf("'",ind1+8);
				String command=value.substring(ind1+6,ind2);
				String resp=resolveCmd(command);
				if (!resp.equals("ok")){
					deviceSendEvent("[{'v':'"+resp+"','n':'Resp'}]", comm.trim());
				}
			}
			else if (dev_ind==2)
			{
				//Relay 
				//Confirm that it's okay, if it's okay and save value as confirmed
				if (value.equals("[{'v':'ok','n':'Resp'}]")){
					confirm_rel=1;
					relayValue=proprelayValue;
				}
			}
			logger.warn("Received from: "+comm+"what"+value);
		
		}

	}
	
	public class CloudEventHandler implements EventHandler {

		public void handleEvent(Event event) {
			String value = event.getProperty("payload").toString();
			String resp=resolveCmd(value);
			if (!resp.equals("ok")){
				cloudSendEvent(resp);
			}
		}
	}

	
	public String resolveCmd(String command)
	{
		String parts[] = command.split(":");
		if (parts[0].equals("get")){
			if (parts[1].equals("temp"))
			{
				return "Temp: "+String.format("%.2f", recAvg);
			}else if (parts[1].equals("ref"))
			{
				return "Sched Period:"+mySched.getSched();
			}
			else if (parts[1].equals("state"))
			{
				String boiler="";
				if (relayValue==1){
					boiler="On";
				} else{
					boiler="Off";
				}
				return "Temperature: "+String.format("%.2f", recAvg)+" Boiler: "+boiler;
			}
		}else if (parts[0].equals("set"))
		{
			mySched.setSched(parts[1]);
		}
		return "ok";	
	}
	
	public void cloudSendEvent(String payload) {
		Dictionary props = new Hashtable();
		props.put("payload", payload);
		props.put("app", app_name);
		props.put("cloud",mqtt_conn);
		Event event = new Event(CLOUD_SEND, props);
		ea.sendEvent(event);
	}
	
	public void deviceSendEvent(String payload, String device) {
		//Send event to device
		Dictionary props = new Hashtable();
		props.put("app", app_name);
		props.put("payload", payload);
		props.put("device", device);
		int dev_ind=dev_names.indexOf(device);
		if (dev_ind==2){
			props.put("qos","1");
		}
		Event event = new Event(DEVICE_SEND, props);
		ea.sendEvent(event);
	}

	public void updated(Dictionary properties) throws ConfigurationException {
		// TODO Auto-generated method stub
		// TODO Add registration of services if non existant full
		logger.warn("Update Entered");
		if (properties != null) {
			logger.info("Properties not null");
			String devs1 = (String) properties.get("dev_ardUnoTemp");
			String devs2 = (String) properties.get("dev_AndroidPhone");
			String devs3 = (String) properties.get("dev_ardRelayBoiler");
			String app = (String) properties.get("name");
			String clouds = (String) properties.get("cloud");
			if (devs1 != null && devs2 != null && devs3 != null && app != null && clouds !=null) {
				reconfigureDev(devs1.trim(),devs2.trim(),devs3.trim());
				reconfigureApp(app.trim());
				mqtt_conn=clouds;
				configured=true;
			}
		}
	}

	public void reconfigureDev(String dev1, String dev2, String dev3) {
		if (configured) {
			for (ServiceRegistration reg : dev_reg) {
				reg.unregister();
				dev_names.clear();	
			}
		}
		dev_names.add(dev1);
		dev_names.add(dev2);
		dev_names.add(dev3);
		dev_reg.clear();
		Dictionary dp = new Hashtable();
		dp.put(EventConstants.EVENT_TOPIC, DEVICE_QUEUE + dev1);
		logger.warn("New Device Registered:" + dev1);
		ServiceRegistration reg_temp = bcontext.registerService(EventHandler.class.getName(),
				new SendEventHandler(), dp);
		dev_reg.add(reg_temp);
		
		Dictionary dp2 = new Hashtable();
		dp2.put(EventConstants.EVENT_TOPIC, DEVICE_QUEUE + dev2);
		logger.warn("New Device Registered:" + dev2);
		ServiceRegistration reg_temp2 = bcontext.registerService(EventHandler.class.getName(),
				new SendEventHandler(), dp2);
		dev_reg.add(reg_temp2);
		
		Dictionary dp3 = new Hashtable();
		dp3.put(EventConstants.EVENT_TOPIC, DEVICE_QUEUE + dev3);
		logger.warn("New Device Registered:" + dev3);
		ServiceRegistration reg_temp3 = bcontext.registerService(EventHandler.class.getName(),
				new SendEventHandler(), dp3);
		dev_reg.add(reg_temp3);
	}
	
	public void reconfigureApp(String name) {
		app_name = name;
		if (configured) {
			register2.unregister();
		}
		Dictionary dp = new Hashtable();
		dp.put(EventConstants.EVENT_TOPIC, CLOUD_QUEUE + app_name);
		logger.warn("New App Name Reg:" + name);
		register2 = bcontext.registerService(EventHandler.class.getName(), new CloudEventHandler(), dp);
	}
}
