package org.karaf.event_create;

import java.util.ArrayList;
import java.util.List;

public class Schedule {
	
	private List<Integer> start= new ArrayList<Integer>(); 
	private List<Integer> value= new ArrayList<Integer>(); 
	private String sched="";
	public Schedule()
	{
		this.setSched("00-18,06-20,10-18,17-20,23-18");
		this.sched=("00-18,06-20,10-18,17-20,23-18");
	}

	public void setSched(String string) {
		start.clear();
		value.clear();
		for (String parts : string.split(","))
		{
			String p[]=parts.split("-");
			start.add(Integer.parseInt(p[0]));
			value.add(Integer.parseInt(p[1]));
		}
		this.sched=string;	
	}
	
	public String getSched()
	{
		return sched;
	}
	
	public int getTemp(int time){
		int next=0;
		for (int parts : start){
			if (parts <= time){ next=parts;}
			if (parts >time) {break;}
		}	
		return value.get(start.indexOf(next));
	}
}
