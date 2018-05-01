package org.nandor.spark;

import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.Timer;

import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaSparkContext;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import scala.collection.mutable.HashMap;

public class Testing {

	public static JSONObject readJson(String file) {
		JSONParser parser = new JSONParser();
		JSONObject a = new JSONObject();
		try {
			a = (JSONObject) parser.parse(new FileReader(file));
		} catch (IOException | ParseException e) {
			e.printStackTrace();
		}
		return a;
	}

	public static void writeJson(String file, JSONObject json) {
		FileWriter f;
		try {
			f = new FileWriter(file);
			f.write(json.toJSONString());
			f.flush();
			f.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public static void main2(String[] args) {
		// Timer

		Timer timer = new Timer();
		// timer.schedule(Methods.timerTask, 300, 600000);

		// Init
		Fog f = Methods.InitFog(80, 0);// Cluster Count, Cloud Gw Count
		// Fog
		// f=Exporter.readJsonFog(readJson("C:/Users/Nandor/Documents/FogOfThings/Gateway
		// Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json"));
		// writeJson("C:/Users/Nandor/Documents/FogOfThings/Gateway
		// Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json",Exporter.writeJsonFog(f));

		// DisplayData(f);
		// Global Optimization
		//Map<String, Float> data = Methods.GAGlobalStuff(f, 60, 1000, true);// Fog,
																			// Generation
																			// Size,
																			// Generation
																			// Cunt

		// Clustering
		long start = System.currentTimeMillis();
		//Methods.displayClsAndRes(f);
		Map<String, Map<String, String>> results = new java.util.HashMap<>();
		/*for (int i = 1; i <=1 ; i++) {
			for (int j = 6; j <=10; j++) {
				start = System.currentTimeMillis();
				if (Methods.Clustering(f, i, j)) {
					// Methods.ResourceAllocation(f);
					Methods.nandorsAlphaResourceAlloc(f);
					//Methods.displayClsAndRes(f);
					results.put("Old-Eps:" + i + "MinPts" + j, Methods.GAClusStuff(f, 20, 40, true));
					System.out.println("Clustering Old Time Elapsed: " + (System.currentTimeMillis() - start) / (float) 1000);
				}else{
					System.out.println("Clustering Old with "+i+" and "+j+" failed!");
					start = System.currentTimeMillis();
				}
			}
		}*/
		for (int i = 5; i <= 5; i++) {
			for (int j = 11; j <= 11; j++) {
				if (Methods.AdvClustering(f, (float)i/(float)10.0, j)) {
					// Methods.ResourceAllocation(f);
					Methods.nandorsAlphaResourceAlloc(f);
					Methods.displayClsAndRes(f);
					results.put("New-Eps:" + (float)i/(float)10.0 + "MinPts" + j, Methods.GAClusStuff(f, 20, 40, true));
					System.out.println("Clustering New Time Elapsed: " + (System.currentTimeMillis() - start) / (float) 1000);
				}else{
					System.out.println("Clustering New  with "+(float)i/(float)10.0+" and "+j+" failed!");
					start = System.currentTimeMillis();
				}
				
			}
		}
		// GA Cluster Stuff
		// Map<String,Float> data2 = Methods.GAClusStuff(f, 60, 200,true);
		System.out.println("All cls GA: " + results);
		//System.out.println("Global GA: " + data);
		System.out.print("Best Clustr GA: ");
		Map<String, String> bestMethod = new java.util.HashMap<>();
		float bestUtil = (float) 0.0;
		String bestConfig = "";
		for (String d : results.keySet()) {
			// System.out.println(results.get(d));
			if (results.get(d) != null) {
				if (Float.parseFloat(results.get(d).get("1.Utility")) > bestUtil) {
					bestUtil = Float.parseFloat(results.get(d).get("1.Utility"));
					bestMethod = results.get(d);
					bestConfig = d;
				}
			}
		}
		System.out.println("Config: "+bestConfig+" Res: "+bestMethod+" AvgUtility: "+(bestUtil/f.getApps().size()));
		/*
		 * //Exhaustive Cluster Stuff start=System.currentTimeMillis();
		 * Methods.ExhaustiveClusStuff(f); System.out.println("Time Elapsed: "
		 * +(System.currentTimeMillis()-start)/(float)1000);
		 * start=System.currentTimeMillis();
		 */

		// writeJson("C:/Users/Nandor/Documents/FogOfThings/Gateway
		// Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json",Exporter.writeJsonFog(f));
		timer.cancel();
	}

	
	public static void mainBig(String[] args) {
		//Init
		//Fog f=Exporter.readJsonFog(readJson("C:/Users/Nandor/Documents/FogOfThings/Gateway Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json"));
		Fog f = Methods.InitFog(10, 0);
		
		//Global GA
		List<Map<Integer, Integer>> bests = Methods.GAGlobal(f, 60, 150, true);
		
		//Clustering GA
		Methods.Clustering(f, 1, 7);
		Methods.ResourceAllocation(f);
		Methods.displayClsAndRes(f);
		List<Map<Integer, Integer>> bestsCls = Methods.GAClus(f, 40, 60, true);
		
		//lustering GA2
		Methods.nandorsAlphaResourceAlloc(f);
		Methods.displayClsAndRes(f);
		List<Map<Integer, Integer>> bestsCls2 = Methods.GAClus(f, 40, 60, true);
		//Correlation `
		WeightedCls cls = new WeightedCls(f);
		WeightedCls cls2 = new WeightedCls(f);
		WeightedCls clsGlob = new WeightedCls(f);
		//Global
		System.out.println("Global Correlation");
		System.out.println("Corr for App Distance: "+clsGlob.Correlation("Deployment",clsGlob.allAppSimilarities(bests)));
		System.out.println("Corr for Gw Distance: "+clsGlob.Correlation("Deployment",clsGlob.allGwSimilarities(bests)));
		//Cluster
		System.out.println("Clustering - Orig Correlation");
		System.out.println("Corr for App Distance: "+cls.Correlation("Deployment",cls.allAppSimilarities(bestsCls)));
		System.out.println("Corr for Gw Distance: "+cls.Correlation("Deployment",cls.allGwSimilarities(bestsCls)));
		//Cluster
		System.out.println("Clustering - NanAlloc Correlation");
		System.out.println("Corr for App Distance: "+cls2.Correlation("Deployment",cls2.allAppSimilarities(bestsCls2)));
		System.out.println("Corr for Gw Distance: "+cls2.Correlation("Deployment",cls2.allGwSimilarities(bestsCls2)));

	}
	
	public static void main222(String[] args) {
		//Fog f=Exporter.readJsonFog(readJson("C:/Users/Nandor/Documents/FogOfThings/Gateway Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json"));
		Fog f = Methods.InitFog(60, 0);
		WeightedCls cls = new WeightedCls(f);
		/*List<Map<Integer, Integer>> bests = Methods.GAGlobal(f, 60, 150, true);
		if (bests == null) {
			System.out.println("Failed Global GA");
		}
		//writeJson("C:/Users/Nandor/Documents/FogOfThings/Gateway Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json",Exporter.writeJsonFog(f));
		Map<String, Double> corrApp = cls.Correlation("Deployment", cls.allAppSimilarities(bests));
		Map<String, Double> corrGw = cls.Correlation("Deployment", cls.allGwSimilarities(bests));
		System.out.println("Apps Correlations: "+corrApp);
		System.out.println("Gws Correlations: "+corrGw);
		cls.setCorrelation(corrApp, corrGw,0.3);*/
		cls.appWeights = new java.util.HashMap<>();
		cls.gwWeights = new java.util.HashMap<>();
		cls.appWeights.put("Constraints",0.1581055177966246);
		cls.appWeights.put("RequirementSim",0.2830447252327823);
		cls.appWeights.put("ResourceShare",0.2492529182282662);
		cls.appWeights.put("Distance",0.30959683874232696);
		cls.gwWeights.put("SharedRes",1.0);
		//System.out.println(cls.getNeighbours(f.getApps().get(1).getId(),(float)2.7,0));
		double start = System.currentTimeMillis();
		if (Methods.WeightedClustering(f, cls, 7)) {	
			Methods.weightedResourceAlloc(f, cls, 2, 0.5);
			Methods.displayClsAndRes(f);
			//Methods.GAClus(f, 40, 100, true);
		}
		System.out.println("Time finished: "+((System.currentTimeMillis()-start)/1000.0));
	}
	
	public static void main(String[] args) {
		//Fog f=Exporter.readJsonFog(readJson("C:/Users/Nandor/Documents/FogOfThings/Gateway Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json"));
		Fog f = Methods.InitFog(12, 0);
		//Methods.CorrelationClusterin(f);
		//Methods.GAGlobal(f, 100, 50, true);
		//Methods.weightedDistanceClusteringOptimization(f);
		f.setDeplpyment(Methods.SampleWeDiCOptimization(f));
		f.deployFog();
		writeJson("C:/Users/Nandor/Documents/FogOfThings/Gateway Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json",Exporter.writeJsonFog(f));
		//Methods.IterativeCorrelationClustering(f,5);
	}
	
	
}