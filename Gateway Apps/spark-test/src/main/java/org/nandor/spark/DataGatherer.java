package org.nandor.spark;

import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.SortedSet;
import java.util.TreeSet;
import java.util.HashMap;


public class DataGatherer {

	
	boolean utilBool = true;
	boolean iterBool = true;
	boolean timeBool = true;
	String current = "Not Specified";
	Map<String,List<Float>> utility = new HashMap<>();//LinkedList<>();
	Map<String,List<Integer>> iteration = new HashMap<>();
	Map<String,List<Float>> execTime = new HashMap<>();
	
	//Set Test
	public void setTestType(String type) {
		
		switch (type) {
		case "Perf":
			utilBool = true;
			iterBool = false;
			timeBool = true;
			break;
		
		default:
			break;
		}
	}

	public void newDataSet(String string) {
		current = string;
		utility.put(current, new LinkedList<>());
		iteration.put(current, new LinkedList<>());
		execTime.put(current, new LinkedList<>());
		
	}

	//Add Components
	public void addUtility(float bestUtil) {
		if (utilBool){
			utility.get(current).add(bestUtil);
		}	
	}
	public void addIteration(int i) {
		if (iterBool){
			iteration.get(current).add(i);
		}
	}
	public void addTime(float f) {
		if (timeBool){
			execTime.get(current).add(f);
		}
	}
	
	public void reset() {
		utility = new HashMap<>();
		iteration = new HashMap<>();
		execTime = new HashMap<>();
	}
	//print out Results
	public void getPerfResults(int size,int type) {
		SortedSet<String> keys = new TreeSet<>(utility.keySet());
		for (String key:execTime.keySet()){
			//System.out.println("%"+key);
			System.out.print("X."+key+" = [");
			for (Float item:execTime.get(key)){
			System.out.print(item+" ");
			}
			System.out.println("];");
		}
		for (String key:utility.keySet()){
			System.out.print("Y"+key+" = [");
			for (Float item:utility.get(key)){
			System.out.print(item+" ");
			}
			System.out.println("];");
		}
		System.out.println("size = "+(size+1)+"; type = "+type+";");
		System.out.println("XMat(size,type) = X;");
		System.out.println("YMat(size,type) = Y;");
	}
	
	public void getSinglePerfResults(int size,int type) {
		SortedSet<String> keys = new TreeSet<String>(utility.keySet());
		String key = keys.first();
		System.out.print("X." + key + " = [");
		for (Float item : execTime.get(key)) {
			System.out.print(item + " ");
		}
		System.out.println("];");

		System.out.print("Y." + key + " = [");
		for (Float item : utility.get(key)) {
			System.out.print(item + " ");
		}
		System.out.println("];");
		System.out.println("size = " + (size+1) + "; type = " + type + ";");
		System.out.println("XMat(size,type)." + key + " = Xsmall;");
		System.out.println("YMat(size,type)." + key + " = Ysmall;");
	}

	public void getScaleResults(int i,int type) {
		i++;//Putting it in matlab form
		//Utility
		SortedSet<String> keys = new TreeSet<>(utility.keySet());
		int row = 0;
		float sum = (float) 0.0;
		int count = 0;
		for (String key : utility.keySet()) {
			//System.out.println("Key:" + key);
			if (row != Integer.parseInt(key.split("-")[0])) {
				//System.out.println("New Row");
				if (row != 0) {
					System.out.println("Util"+type+"(" + row + "," + i + ") = " + sum / (float) count+";");
					sum = (float) 0.0;
					count = 0;
				} else {
					sum = (float) 0.0;
					count = 0;
				}
				row = Integer.parseInt(key.split("-")[0]);
				sum += utility.get(key).get(utility.get(key).size() - 1);
				count++;
			} else {
				sum += utility.get(key).get(utility.get(key).size() - 1);
				count++;
			}
		}
		System.out.println("Util"+type+"(" + row + "," + i + ") = " + sum / (float) count+";");
		
		// Time
		keys = new TreeSet<>(execTime.keySet());
		row = 0;
		sum = (float) 0.0;
		count = 0;
		for (String key : execTime.keySet()) {
			//System.out.println("Key:" + key);
			if (row != Integer.parseInt(key.split("-")[0])) {
				//System.out.println("New Row");
				if (row != 0) {
					System.out.println("Time"+type+"(" + row + "," + i + ") = " + sum / (float) count+";");
					sum = (float) 0.0;
					count = 0;
				} else {
					sum = (float) 0.0;
					count = 0;
				}
				row = Integer.parseInt(key.split("-")[0]);
				sum += execTime.get(key).get(execTime.get(key).size() - 1);
				count++;
			} else {
				sum += execTime.get(key).get(execTime.get(key).size() - 1);
				count++;
			}
		}
		System.out.println("Time"+type+"(" + row + "," + i + ") = " + sum / (float) count+";");
	}
	
	public void getBestUtils(){
		System.out.println("Utilities...");
		for (String key:utility.keySet()){
			System.out.println(key+": "+utility.get(key).get(utility.get(key).size()-1));
		}
	}

}
