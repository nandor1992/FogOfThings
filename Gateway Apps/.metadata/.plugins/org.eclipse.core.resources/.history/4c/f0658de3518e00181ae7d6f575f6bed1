package org.nandor.spark;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

public class Resource {
	private String type;
	private String name;
	private static final AtomicInteger count = new AtomicInteger(0);
	private int id; 
	//Types of Resources: Cloud, Storage, LocalAccesPoint, Device
	private Gateway gateway=null;
	private Integer apps;
	float Amessages;
	//Initialization
	public Resource(String name,String type){
		this.type=type;
		this.name=name;
		this.id=count.incrementAndGet();
	}
	public Resource(int id, String name,String type){
		this.type=type;
		this.name=name;
		this.id=id;
		if (count.get()<id){
			count.set(id);
		}
	}
	
	
	public void addApps(App app,Float msg) {
		apps = app.getId();
		Amessages =  msg;
		
	}
	
	public Float getTotMsgs()
	{
		return Amessages;
	}
	
	public String toString(){
		return name;
}
	public String getInfo(){
		String ret=name+"; "
	    		 +"Type: "+type+"; ";
		if (gateway!=null){
	    		 ret+="GatewayID: "+gateway.getId()+"; ";
		}
	     		 ret+="App:"+apps;
	    return ret;
	}
	//Basic Setters and Getters for Resource
	public Gateway getGateway() {
		return this.gateway;
	}
	public void setGateway(Gateway gw) {
		this.gateway = gw;
	}
	
	public int getId() {
		return id;
	}

	public String getType() {
		return type;
	}


	public void setType(String type) {
		this.type = type;
	}


	public String getName() {
		return name;
	}


	public void setName(String name) {
		this.name = name;
	}


	public  Integer getApp() {
		return this.apps;
	}


	public void setApp(Integer apps) {
		this.apps = apps;
	}


	
}
