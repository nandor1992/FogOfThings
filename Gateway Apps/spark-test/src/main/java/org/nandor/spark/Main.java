package org.nandor.spark;

import org.apache.log4j.Logger;
/* SimpleApp.java */
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaPairRDD;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.api.java.function.FlatMapFunction;
import org.apache.spark.api.java.function.Function;
import org.apache.spark.api.java.function.Function2;
import org.apache.spark.api.java.function.PairFunction;

import com.fasterxml.jackson.core.format.DataFormatMatcher;



import java.util.Arrays;

import org.apache.spark.SparkConf;

public class Main {
  public static void main(String[] args) {
	Logger logger = Logger.getRootLogger();
    String logFile = "swift://spark.SparkTest/hughmungus.txt"; // Should be some file on your system
    SparkConf conf = new SparkConf().setAppName("Simple Application");
    JavaSparkContext sc = new JavaSparkContext(conf);
    JavaRDD<String> logData = sc.textFile(logFile,1);

    long numAs = logData.filter(new Function<String, Boolean>() {
      public Boolean call(String s) { return s.contains("a"); }
    }).count();

    long numBs = logData.filter(new Function<String, Boolean>() {
      public Boolean call(String s) { return s.contains("b"); }
    }).count();
    
    //Search
    JavaRDD<String> lines = logData.filter(s -> s.contains("this"));
    long numErrors = lines.count();
    
    //Word Count
  //  JavaRDD<String> words = logData.flatMap(line -> Arrays.asList(line.split(" ")).iterator());
    //JavaPairRDD<Object, Object> counts = words.mapToPair( t -> new Tuple( t, 1 ) ).reduceByKey( (x, y) -> (int)x + (int)y ).sortByKey();
 /*   logger.warn("Test - Warn");
    logger.error("Test - Error");
    logger.debug("Test - Debug");
    logger.info("Test - Info");
    logger.fatal("Test - Fatal");*/
  //  counts.saveAsTextFile("swift://spark.SparkTest/result");
    System.out.println("Output for Test");
    System.out.println("Lines with a: " + numAs + ", lines with b: " + numBs);
    System.out.println("Search Result: "+numErrors);
    System.out.println("-------Reduce Results-------");
   // System.out.println(counts.collect());
    sc.stop();
  }
}
