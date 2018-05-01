package org.nandor.spark;

import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.JavaSparkContext;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.FileUtil;
import org.apache.hadoop.fs.Path;

public class Spark{

	public static void writeHDFS(JavaSparkContext sc, String loc,String title, String data){
		Configuration hadoopConfig = new Configuration();
		hadoopConfig.set("fs.defaultFS","hdfs://10.0.0.7:9000"); 
		FileSystem hdfs;
		try {
			hdfs = FileSystem.get(hadoopConfig);
			FileUtil.fullyDelete(hdfs,new Path("/data/"+loc+"/"+title));
			FileUtil.fullyDelete(hdfs,new Path("/data/"+loc+"/"+title+".json"));
			//Data Save
			List<String> dat = new ArrayList<String>();
			dat.add(data);
			JavaRDD<String> writer = sc.parallelize(dat);
			writer.collect();
			writer.repartition(1).saveAsTextFile("hdfs://10.0.0.7:9000/data/"+loc+"/"+title);
			//Data Merge
			FileUtil.copyMerge(hdfs, new Path("/data/"+loc+"/"+title), hdfs, new Path("/data/"+loc+"/"+title+".json"), false, hadoopConfig, null);
			FileUtil.fullyDelete(hdfs,new Path("/data/"+loc+"/"+title));
		} catch (IllegalArgumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		}

	public static void createFolder(JavaSparkContext sc, String loc){
		Configuration hadoopConfig = new Configuration();
		hadoopConfig.set("fs.defaultFS","hdfs://10.0.0.7:9000"); 
		FileSystem hdfs;
		try {
			hdfs = FileSystem.get(hadoopConfig);
			hdfs.mkdirs(new Path("/data/"+loc));
		} catch (IllegalArgumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public static String readHDFS(JavaSparkContext sc,String file){
		JavaRDD<String> dataRDD = sc.textFile("hdfs://10.0.0.7:9000/data/"+file+".json");
		String data = dataRDD.collect().toString();
		return data;	
	}

	public static void mainOld(String[] args) {
		//Logger logger = Logger.getRootLogger();
	    SparkConf conf = new SparkConf();
	    JavaSparkContext sc = new JavaSparkContext(conf);
	    String fogFile = "";
	    for (String s :args){
	    	fogFile = s;
	    }
	    createFolder(sc,fogFile);
	    
		Fog f = Methods.InitFog(4,0);//Cluster Count, Cloud Gw Count
		writeHDFS(sc,fogFile,"Init",Exporter.writeStringFog(f));	
		//Fog f=Exporter.readJsonFog(readHDFS(sc,fogFile));
	    //readHDFS(sc,fogFile);
		//Global Optimization
		//Methods.GAGlobalStuff(f, 20, 20,true);//Fog, Generation Size, Generation Cunt
		//writeHDFS(sc,fogFile,"GlobalGA",Exporter.writeStringFog(f));
		// CLustering based GA
		//Methods.GAClusStuff(f, 20, 20,true);//Fog, Generation Size, Generation Count
		//writeHDFS(sc,fogFile,"ClustGA",Exporter.writeStringFog(f));	    
		
		//Testing
	     //Fog f = Methods.InitFog(Integer.parseInt(fogFile),Integer.parseInt(fogFile)/4);//Cluster Count, Cloud Gw Count
	    //Fog f=Exporter.readJsonFog(readJson("C:/Users/Nandor/Documents/FogOfThings/Gateway Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json"));
		//writeJson("C:/Users/Nandor/Documents/FogOfThings/Gateway Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json",Exporter.writeJsonFog(f));
		 
	    //DisplayData(f);
		//Global Optimization
	    Methods.GAGlobalStuff(f, 60, 100,true);
	    if (f.checkIfAppsAllocated().size()==0){
	    	writeHDFS(sc,fogFile,"GlobalGA",Exporter.writeStringFog(f)); 
	    }
		
		
	     if (Methods.AdvClustering(f, (float)1.2, 8)) {
				// Methods.ResourceAllocation(f);
				Methods.nandorsAlphaResourceAlloc(f);
				Methods.displayClsAndRes(f);
				System.out.println(Methods.GAClusStuff(f, 40, 1000, true));
			}else{
				System.out.println("Clustering New  with "+1.2+" and "+8+" failed!");
			}
	    f.deployFog();
	    if (f.checkIfAppsAllocated().size()==0){
		    writeHDFS(sc,fogFile,"ClustAdvGA",Exporter.writeStringFog(f));
	    }
	    
	    if (Methods.Clustering(f, 1, 8)) {
			// Methods.ResourceAllocation(f);
			Methods.nandorsAlphaResourceAlloc(f);
			Methods.displayClsAndRes(f);
			System.out.println(Methods.GAClusStuff(f, 40, 1000, true));
		}else{
			System.out.println("Clustering Old with "+1+" and "+8+" failed!");
		}
	    f.deployFog();;
	    if (f.checkIfAppsAllocated().size()==0){
		    writeHDFS(sc,fogFile,"ClustOldGA",Exporter.writeStringFog(f));
	    }
	    
	    sc.stop();
	  }
	
	public static void main(String[] args) {
		//Fog f=Exporter.readJsonFog(readJson("C:/Users/Nandor/Documents/FogOfThings/Gateway Apps/spark-test/src/main/java/org/nandor/spark/deploy-W.json"));
	    SparkConf conf = new SparkConf();
	    JavaSparkContext sc = new JavaSparkContext(conf);
	    String fogFile = args[0];    
		Fog f = Methods.InitFog(Integer.valueOf(args[0]), 0);
		//Methods.CorrelationClusterin(f);
		Methods.GAGlobal(f, 150, 500, true);
		//Methods.weightedDistanceClusteringOptimization(f);
		Methods.SampleWeDiCOptimization(f);
	}
	
}