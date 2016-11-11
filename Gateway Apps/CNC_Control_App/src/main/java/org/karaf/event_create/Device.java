package org.karaf.event_create;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class Device {

	private String name;
	private List<String> task = new ArrayList<String>();
	private Integer task_progress = 0;
	public Integer retransmit=0;
	public boolean start = false;

	public Device(String name) {
		this.name = name;
	}

	public void addTask(String data) {
		String[] tokens = data.split(";");
		task.clear();
		for (String value : tokens) {
			task.add(value.trim());
		}
		task_progress = 0;
		retransmit=0;
	}

	public String getNextStep() {
		if (task_progress < task.size()) {
			task_progress += 1;
			return task.get(task_progress - 1);
		}
		return null;
	}

	public String resendStep(){
		if (task_progress < task.size()) {
			return task.get(task_progress);
		}
		return null;
	}
	public Integer getTaskSize() {
		return task.size();
	}

	public float getProgress() {
		return (float)task_progress/task.size()*100;
	}

	public boolean canStart() {
		if (!task.isEmpty()) {
			if (task_progress < task.size()) {
				return true;
			} else
				return false;
		} else
			return false;
	}

	public void doStart() {
		start = true;
	}

	public void doStop() {
		start = false;
	}

	public String getName() {
		return name;
	}

}
