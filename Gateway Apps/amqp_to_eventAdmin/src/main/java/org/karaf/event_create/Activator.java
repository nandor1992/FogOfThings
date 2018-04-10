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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Dictionary;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.List;
import java.util.ListIterator;

import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.Constants;
import org.osgi.framework.ServiceRegistration;
import org.osgi.service.cm.ConfigurationException;
import org.osgi.service.cm.ManagedService;
import org.osgi.service.event.EventConstants;
import org.osgi.service.event.EventHandler;

public class Activator implements BundleActivator,ManagedService{
	private List<AmqpConnect> ac = new ArrayList<AmqpConnect>();
	private int cnt=5;
	private BundleContext bcontext;
	private static String CONFIG_PID = "org.karaf.amqp2event";
	private ServiceRegistration ppcService;
	
	public void start(BundleContext bc) throws Exception {
		this.bcontext=bc;
		Dictionary props2 = new Hashtable();
		props2.put(Constants.SERVICE_PID, CONFIG_PID);
		ppcService = bcontext.registerService(ManagedService.class.getName(), this, props2);
		for (int i=0;i<this.cnt;i++)
		{
			AmqpConnect ac1=new AmqpConnect(bc);
			ac1.start();
			ac.add(ac1);
		}
	}

	public void stop(BundleContext bc) throws Exception {
		for (AmqpConnect a:ac)
		{
			a.stopThis();
		}
		ac.clear();
		ppcService.unregister();
	}

	public void updated(Dictionary properties) throws ConfigurationException {
		
		cnt = Integer.parseInt(properties.get("cnt").toString().trim());
		this.cnt=cnt;
		for (AmqpConnect a:ac)
		{
			a.stopThis();
		}
		ac.clear();
		for (int i=0;i<this.cnt;i++)
		{
			AmqpConnect ac1=new AmqpConnect(this.bcontext);
			ac1.start();
			ac.add(ac1);
		}
	}


}