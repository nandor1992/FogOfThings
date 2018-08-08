package org.nandor.spark;

import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.SortedSet;
import java.util.TreeSet;

import javafx.scene.chart.PieChart.Data;
import scala.annotation.elidable;

import java.util.HashMap;


public class DataGatherer {

	
	boolean utilBool = true;
	boolean iterBool = true;
	boolean timeBool = true;
	String current = "Not Specified";
	Map<String,Integer> bestCorrs = new HashMap<>();
	Map<String,List<Float>> utility = new HashMap<>();//LinkedList<>();
	Map<String,List<Integer>> iteration = new HashMap<>();
	Map<String,List<Float>> execTime = new HashMap<>();
	Map<String,List<Map<String, Double>>> weightApp =  new HashMap<>();
	Map<String,List<Map<String, Double>>> weightGw =  new HashMap<>();
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
		weightApp.put(current, new LinkedList<>());
		weightGw.put(current, new LinkedList<>());
		
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
	
	public void addWeightApp(Map<String, Double> weightApp) {
		this.weightApp.get(current).add(weightApp);
	}
	
	public void addWeightGw(Map<String, Double> weightGw) {
		this.weightGw.get(current).add(weightGw);
	}
	
	public void reset() {
		utility = new HashMap<>();
		iteration = new HashMap<>();
		execTime = new HashMap<>();
		weightApp = new HashMap<>();
		weightGw = new HashMap<>();
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
			System.out.print("Y."+key+" = [");
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
		System.out.print("Xsmall" + key + " = [");
		for (Float item : execTime.get(key)) {
			System.out.print(item + " ");
		}
		System.out.println("];");

		System.out.print("Ysmall" + key + " = [");
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
	
	public void getDistResults() {
		System.out.println("Time Dist Results:");
		SortedSet<String> keys = new TreeSet<>(execTime.keySet());
		for (String key:keys){
			System.out.print("Time." + key + " = [");
			for (Float item:execTime.get(key)){
				System.out.print(item + " ");
			}
			System.out.println("];");
		}
	}
	
	
	public void getBestUtils(){
		System.out.println("Utilities...");
		for (String key:utility.keySet()){
			System.out.println(key+": "+utility.get(key).get(utility.get(key).size()-1));
		}
	}
	
	public void getWeights() {
		// TODO Auto-generated method stub
		List<String> appTypes = new LinkedList<>();
		appTypes.add("Constraints");appTypes.add("RequirementSim");appTypes.add("ResourceShare");appTypes.add("MessageRate");appTypes.add("UtilityWeights");appTypes.add("UnitLoad");appTypes.add("Distance");
		List<String> gwTypes = new LinkedList<>();
		gwTypes.add("Capabilities");gwTypes.add("SharedRes");gwTypes.add("PerfToULoad");gwTypes.add("BaseLoad");gwTypes.add("CapToULoad");
		SortedSet<String> keys = new TreeSet<>(weightApp.keySet());
		//Lables
		System.out.println("label1 = {");
			for (String key:appTypes){
				System.out.print("'"+key+"';");
			}
		System.out.println("};");
		System.out.println("label2 = {");
		for (String key:gwTypes){
			System.out.print("'"+key+"';");
		}
		System.out.println("};");
		int cnt = 0;
		for (String key:keys){
			cnt++;
			int i=1;
			int j=0;
			for (String keyInt:appTypes){
				j++;
					System.out.print("DataA"+cnt+"("+j+","+i+")= 0.0;");
			}
			System.out.println();
			for(Map<String,Double> wAInt :weightApp.get(key)){
				j = 0;
				i++;
				for (String keyInt:appTypes){
					j++;
					if (wAInt.containsKey(keyInt)){
						System.out.print("DataA"+cnt+"("+j+","+i+")="+wAInt.get(keyInt)+";");
					}else{
						System.out.print("DataA"+cnt+"("+j+","+i+")= 0.0;");
					}
				}
				System.out.println();
			}
			i=1;
			j=0;
			for (String keyInt:gwTypes){
				j++;
					System.out.print("DataGw"+cnt+"("+j+","+i+")= 0.0;");
			}
			System.out.println();
			for(Map<String,Double> wGwInt :weightGw.get(key)){
				j = 0;
				i++;
				for (String keyInt:gwTypes){
					j++;
					if (wGwInt.containsKey(keyInt)){
						System.out.print("DataGw"+cnt+"("+j+","+i+")="+wGwInt.get(keyInt)+";");
					}else{
						System.out.print("DataGw"+cnt+"("+j+","+i+")= 0.0;");
					}
				}
				System.out.println();
			}
		System.out.println("Best"+cnt+" = "+(bestCorrs.get(key)+1)+";");
		System.out.print("Time"+cnt+" = [ 0.0 0.0 0.0 0.0 ");
		for (Float time:execTime.get(key)){
			System.out.print(time+" ");
		}
		System.out.println("];");
		}
		
	}

	public void getAllData() {
		System.out.println("utility: "+utility);
		System.out.println("iteration: "+iteration);
		System.out.println("time: "+execTime);
		System.out.println("WApp: "+weightApp);
		System.out.println("WGw: "+weightGw);
		System.out.println("Best Iters:"+bestCorrs);
	}

	public int getCurrent() {
		return weightApp.get(current).size()-1;
	}

	public void setBestWeight(int currentBest) {
		//System.out.println("Best W:"+currentBest);
		//System.out.println(weightApp.get(current).get(currentBest));
		bestCorrs.put(current, currentBest);
	}

	public Map<String, Double> getBestWeApps() {
		return weightApp.get(current).get(bestCorrs.get(current));
	}

	public Map<String, Double> getBestWeGws() {
		return weightGw.get(current).get(bestCorrs.get(current));
	}

	public void printComponent(int type) {
		
		System.out.println("Time Dist Results:");
		SortedSet<String> keys = new TreeSet<>(execTime.keySet());
		System.out.println("%Keys:"+keys);
		System.out.print("Y1(:,1) = [");
		for (String key:keys){
			if (key!="Init"){
				if (type == 1){
					System.out.print((execTime.get(key).get(1)-execTime.get(key).get(0))+" ");
				}else{
					System.out.print(execTime.get(key).get(0)+" ");
				}
			}
		}
		System.out.println("];");
		System.out.print("Y1(:,2) = [");
		for (int i=0;i<(keys.size()-1);i++){
			System.out.print("0 ");
		}
		System.out.println("];");
		System.out.print("Y2(:,1) = [");
		for (int i=0;i<(keys.size()-1);i++){
			System.out.print("0 ");
		}
		System.out.println("];");
		System.out.print("Y2(:,2) = [");
		for (String key:keys){
			if (key!="Init"){
				System.out.print(utility.get(key).get(0)+" ");
			}
		}
		System.out.println("];");
	}

}
