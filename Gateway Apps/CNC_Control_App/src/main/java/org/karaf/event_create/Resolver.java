package org.karaf.event_create;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

import org.osgi.service.event.Event;

import com.jcraft.jsch.Logger;

public class Resolver {

	private Activator mainA;
	private HashMap<String, Device> devList = new HashMap<String, Device>();
	private HashMap<String, Timer> timerList = new HashMap<String, Timer>();

	public Resolver(Activator mainA) {
		this.mainA = mainA;
		init();
	}

	public void init() {
		for (String name : mainA.dev_names) {
			devList.put(name, new Device(name));
			timerList.put(name, new Timer());
		}
	}

	public void doCloudMsg(Event event) {
		String value = event.getProperty("payload").toString();
		String type = event.getProperty("type").toString();
		mainA.logger.warn("Type : " + type + " Payload :" + value);
		if (type.equals("task")) {
			String[] tokens = value.split(":");
			devList.get(tokens[0].trim()).addTask(tokens[1].trim());
			mainA.cloudSendEvent(tokens[0] + ": Task :" + devList.get(tokens[0].trim()).getTaskSize());
		}
		if (type.equals("start")) {
			String[] tokens = value.split(":");
			if (devList.get(tokens[0].trim()).canStart()) {
				devList.get(tokens[0].trim()).doStart();
				mainA.cloudSendEvent(tokens[0] + ": Starting");
				String payload = "{'n':'Gcode','v':'" + devList.get(tokens[0].trim()).getNextStep() + "'}";
				Timer t1=new Timer();
				t1.schedule(new myTimer(payload, tokens[0].trim(), devList.get(tokens[0].trim()).getProgress()), 5000);
				timerList.put(tokens[0].trim(),t1);
				mainA.deviceSendEvent(payload, tokens[0].trim());
			} else {
				mainA.cloudSendEvent(tokens[0] + ": Can't Start");
			}
		}
		if (type.equals("stop")) {
			String[] tokens = value.split(":");
			devList.get(tokens[0].trim()).doStop();
			devList.get(tokens[0].trim()).retransmit = 0;
			timerList.get(tokens[0].trim()).cancel();
			timerList.get(tokens[0].trim()).purge();
			mainA.cloudSendEvent(tokens[0] + ": Stopping");
		}
	}

	public class myTimer extends TimerTask {
		private String payload;
		private String device;
		private Float progress;

		public myTimer(String payload, String device, Float progress) {
			this.device = device;
			this.payload = payload;
			this.progress=progress;
		}

		@Override
		public void run() {
			mainA.logger.warn("Timer Fired for :" + device + "payload:" + payload);
			if (progress == devList.get(device).getProgress()) {
				if (devList.get(device).retransmit < mainA.MAX_RETRANSMIT - 1) {
					devList.get(device).retransmit += 1;
					mainA.deviceSendEvent(payload, device);
					Timer t1=new Timer();
					t1.schedule(new myTimer(payload, device, progress), 5000);
					timerList.put(device,t1);
				} else {
					mainA.cloudSendEvent(device + ": Max Retransmit");
					devList.get(device).doStop();
				}
			} else {
				mainA.logger.warn("Wrong task reschedule");
			}
		}

	}

	public void doDeviceMsg(Event event) {
		String dev_name = event.getProperty("device").toString();
		String payload = event.getProperty("payload").toString();
		Integer index_start = payload.indexOf("'", payload.indexOf("'v'") + 3);
		Integer index_stop = payload.indexOf("',", index_start);
		String response = payload.substring(index_start + 1, index_stop);
		devList.get(dev_name).retransmit = 0;
		timerList.get(dev_name).cancel();
		timerList.get(dev_name).purge();
		if (response.substring(0, 2).equals("Hu")) {
			mainA.cloudSendEvent(dev_name + ": Didn't Recognize G: " + response);
		} else {
			if (!response.equals("ok")) {
				mainA.cloudSendEvent(dev_name + ": Other stuff probs temp: " + response);
				mainA.logger.info("Data Received[ " + dev_name + "] Value:" + response);
			}
			if (devList.get(dev_name).canStart()) {
				mainA.logger.info("Progess[ " + dev_name + "] Perc:" + devList.get(dev_name).getProgress());
				String payload2 = "{'n':'Gcode','v':'" + devList.get(dev_name).getNextStep() + "'}";
				Timer t1=new Timer();
				t1.schedule(new myTimer(payload2, dev_name, devList.get(dev_name).getProgress()),5000);
				timerList.put(dev_name,t1);
				mainA.deviceSendEvent(payload2, dev_name);
			} else {
				mainA.logger.info("Progess[ " + dev_name + "] Done");
				mainA.cloudSendEvent(dev_name + ": Done : " + response);
			}
		}
	}

}
