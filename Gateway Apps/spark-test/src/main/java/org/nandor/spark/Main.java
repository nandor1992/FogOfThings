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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.spark.SparkConf;

public class Main {
  private static int NUM_SAMPLES = 10000;

public static void main(String[] args) {
	//Logger logger = Logger.getRootLogger();
    SparkConf conf = new SparkConf();
    JavaSparkContext sc = new JavaSparkContext(conf);
    for (String s :args){
    	NUM_SAMPLES = Integer.parseInt(s);
    }
    List<Integer> l = new ArrayList<>(NUM_SAMPLES);
    for (int i = 0; i < NUM_SAMPLES; i++) {
      l.add(i);
    }

    long count = sc.parallelize(l).filter(i -> {
      double x = Math.random();
      double y = Math.random();
      return x*x + y*y < 1;
    }).count();
    System.out.println("Pi is roughly " + 4.0 * count / NUM_SAMPLES);
    System.out.println("-------Reduce Results-------");
   // System.out.println(counts.collect());
    sc.stop();
  }
}
