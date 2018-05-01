package org.nandor.spark;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.TimerTask;

import com.sun.org.apache.bcel.internal.generic.POP;

public class Methods {

	public static void DisplayData(Fog f) {
		/*for (Integer i : f.getApps().keySet()) {
			System.out.println(f.getApps().get(i).getInfo());
		}
		System.out.println(f.getApps().get(1).getAppLoad((float) 1) + " "
				+ f.getApps().get(1).getProcDelay((float) 56.0, (float) 1.0));
		*/
		System.out.println("----Displaying Fog----");
		System.out.println(f.toString());
		System.out.println("Apps: " + f.getApps());
		System.out.println("Apps of  1: "+f.getApps().get(1).getTotDelay());
		System.out.println("Gw1 1: "+f.getGateways().get(1).getInfo());
		System.out.println("Resource: " + f.getResources().toString());
		System.out.println("Gateways: " + f.getGateways().toString());
		System.out.println("Clusters: " + f.getClusters().toString());
		for (Integer i : f.getClusters().keySet()) {
			System.out.println("Cluster "+i+" Load: "+f.getClusters().get(i).getClusterLoad());
		}
		for (Integer i : f.getGateways().keySet()) {
			System.out.println("Gateway " + f.getGateways().get(i).getInfo());
			for (Integer j: f.getGateways().get(i).getCluster().keySet()){
				System.out.println("Gw "+i+" Cluster "+j+" Share: "+f.getGateways().get(i).getClusterShare(j));
			}
		}
		
		System.out.println("Fog Utility: "+f.getFogCompoundUtility());
		System.out.println("Fog Delay: "+f.getFogCompoundDelay());
		System.out.println("Fog Reliability: "+f.getFogCompoundReliability());
	}
	
	static TimerTask timerTask = new TimerTask() {
	    @Override
	    public void run() {
	    	Runtime runtime = Runtime.getRuntime();

	    	long maxMemory = runtime.maxMemory();
	    	long allocatedMemory = runtime.totalMemory();
	    	long freeMemory = runtime.freeMemory();
	    	System.out.println("-----Memory Use-----");
	    	System.out.println("free memory: " + (freeMemory / 1024.0/1024.0));
	    	System.out.println("allocated memory: " + (allocatedMemory / 1024.0/1024.0));
	    	System.out.println("max memory: " + (maxMemory / 1024.0/1024.0));
	    	System.out.println("total free memory: " + (freeMemory + (maxMemory - allocatedMemory))/1024.0/1024.0);
	    	System.out.println("-----End Memory Use-----");
	    }
	};
	
	public static Fog InitFog(int ClsCount, int cloudGw){
		//Initialization and Generation
		Fog f = new Fog("Main Fog");
		float[] lat = {(float)8.97,(float)30.897};
		float[] lat2 = {(float)37.37,(float)87.89};
		float[] lat3 = {(float)2.37,(float)6.89};
		f.generateNewFog(ClsCount,(float)30,(float)60,(float)0.1,(float)0.05,lat,cloudGw,lat2,lat3,7,1);
		//Analysis part, of distributing Gw's to clusters		
		return f;
	}
	


	public static Map<String,Float> ExhaustiveGlobal(Fog f) {
		Map<String,Float> data = new HashMap<>();
		System.out.println("----- Exhaustive Global -----");
		long start=System.currentTimeMillis();
		Genetic g = new Genetic(f);
		f.setDeplpyment(g.ExhaustiveAlloc());
		f.deployFog();
		data.put("Utility",f.getFogCompoundUtility());
		data.put("Time",(System.currentTimeMillis()-start)/(float)1000);
		System.out.println("Unalocated Apps: "+f.checkIfAppsAllocated());	
		System.out.println("Fog Utility: "+f.getFogCompoundUtility());
		System.out.println("Time Elapsed: "+(System.currentTimeMillis()-start)/(float)1000);
		return data;
	}
	
	public static Map<String,Float> GAGlobalStuff(Fog f,int size,int cnt,boolean safe){
		Map<String,Float> data = new HashMap<>();
		System.out.println("----- GA Stuff -----");
		long start=System.currentTimeMillis();
		Genetic g = new Genetic(f);
		f.setDeplpyment(g.GAGlobal(size,cnt,safe));
		f.deployFog();
		data.put("Utility",f.getFogCompoundUtility());
		data.put("Time",(System.currentTimeMillis()-start)/(float)1000);
		System.out.println("Unalocated Apps: "+f.checkIfAppsAllocated());	
		System.out.println("Fog Utility: "+f.getFogCompoundUtility());
		System.out.println("Time Elapsed: "+(System.currentTimeMillis()-start)/(float)1000);
		return data;
	}
	
	public static List<Map<Integer, Integer>> GAGlobal(Fog f,int size,int cnt,boolean safe){
		Map<String,Float> data = new HashMap<>();
		System.out.println("----- GA Stuff -----");
		long start=System.currentTimeMillis();
		Genetic g = new Genetic(f);
		f.setDeplpyment(g.GAGlobal(size,cnt,safe,10000));
		//System.out.println("Unalocated Apps: "+f.checkIfAppsAllocated());	
		//f.deployFog();
		//System.out.println("Fog Utility: "+f.getFogCompoundUtility());
		//System.out.println("Time Elapsed: "+(System.currentTimeMillis()-start)/(float)1000);
		if (f.checkIfAppsAllocated().size()!=0 || f.getFogCompoundUtility().isNaN()){
			return null;
		}else{
			return g.getBestGens();
		}
		/*System.out.println("Bests:");
		for ( Map<Integer,Integer> gen: g.getBestGens()){
			f.AssignAppsToGws(gen);
			float tmp = f.getFogCompoundUtility();
			//System.out.println(tmp);
			if (f.verifyIndValidity()){
				System.out.println("Util: "+tmp+" With Gen: "+gen);
			}
		}*/
	}

	public static Float getUtility(Fog f,Map<Integer, Integer> pop){
		f.clearAppToGws();
		f.deployFog();
		f.AssignAppsToGws(pop);
		return f.getFogCompoundUtility();
	}
	public static Map<String,String> GAClusStuff(Fog f,int size,int cnt,boolean safe){
		System.out.println("----- Clust GA Stuff -----");
		Map<String,String> data = new HashMap<>();
		long start=System.currentTimeMillis();
		Genetic g = new Genetic(f);
		//DisplayData(f);
		for (Integer i: f.getClusters().keySet()){
			f.getClusters().get(i).setDeployment(g.GACluster(size,cnt, f.getClusters().get(i),safe));
		}
		f.deployClusters();
		if (f.checkIfAppsAllocated().size()==0){
			data.put("1.Utility",f.getFogCompoundUtility().toString());
			data.put("2.Time",String.format("%.2f",(System.currentTimeMillis()-start)/(float)1000));
			data.put("3.ClusterSize",""+f.getClusters().size());
			//data.put("3.Cluster",f.getClusters().toString());
			//data.put("4.BestPop",f.getDeployment().toString());
			System.out.println("Unalocated Apps: "+f.checkIfAppsAllocated());
			System.out.println("Fog Utility: "+f.getFogCompoundUtility());
			System.out.println("Time Elapsed: "+(System.currentTimeMillis()-start)/(float)1000);
			//System.out.println("Cluster: "+f.getClusters());
			//System.out.println("BestPop: "+f.getDeployment());
			return data;}
		else{
				System.out.println(f.checkIfAppsAllocated());
				return null;
			}
	}
	
	public static List<Map<Integer, Integer>> GAClus(Fog f,int size,int cnt,boolean safe){
		//System.out.println("----- Clust GA Stuff -----");
		Map<String,String> data = new HashMap<>();
		long start=System.currentTimeMillis();
		Genetic g = new Genetic(f);
		//DisplayData(f);
		for (Integer i: f.getClusters().keySet()){
			Map<Integer, Integer> tmp = g.GACluster(size,cnt, f.getClusters().get(i),safe,5000);
			if (tmp!=null){
				f.getClusters().get(i).setDeployment(tmp);
			}else{
				return null;
			}
		}
		f.deployClusters();
		if (f.checkIfAppsAllocated().size()==0){
			//data.put("1.Utility",f.getFogCompoundUtility().toString());
			//data.put("2.Time",String.format("%.2f",(System.currentTimeMillis()-start)/(float)1000));
			//data.put("3.ClusterSize",""+f.getClusters().size());
			//data.put("3.Cluster",f.getClusters().toString());
			//data.put("4.BestPop",f.getDeployment().toString());
			//System.out.println("Unalocated Apps: "+f.checkIfAppsAllocated());
			System.out.println("Fog Utility: "+f.getFogCompoundUtility());
			//System.out.println("Time Elapsed: "+(System.currentTimeMillis()-start)/(float)1000);
			//System.out.println("Cluster: "+f.getClusters());
			//System.out.println("BestPop: "+f.getDeployment());
			return g.getBestClsGens();}
		else{
				System.out.println("Failed with Unallocated: "+f.checkIfAppsAllocated());
				return null;
			}
	}
	
	public static List<Map<Integer, Integer>> sampGAClus(Fog f,int size,int cnt,boolean safe){
		//System.out.println("----- Clust GA Stuff -----");
		Map<String,String> data = new HashMap<>();
		long start=System.currentTimeMillis();
		Genetic g = new Genetic(f);
		//DisplayData(f);
		for (Integer i: f.getClusters().keySet()){
			Map<Integer, Integer> tmp = g.GACluster(size,cnt, f.getClusters().get(i),safe,5000);
			if (tmp!=null){
				f.getClusters().get(i).setDeployment(tmp);
				f.deployClusters();
				return g.getBestClsGens();
			}else{
				return null;
			}
		}
		return null;
	}
	
	public static float clusteredDeployment(Fog f,int eps, int minPts,int size,int cnt,boolean safe){
		System.out.println("----- Clust GA Stuff -----");
		Genetic g = new Genetic(f);
		long start=System.currentTimeMillis();
		Clustering(f,eps,minPts);
		ResourceAllocation(f);
		//CLustered GA
		//DisplayData(f);
		for (Integer i: f.getClusters().keySet()){
			f.getClusters().get(i).setDeployment(g.GACluster(size,cnt, f.getClusters().get(i),safe));
		}
		f.deployClusters();
		float tot_sec=(System.currentTimeMillis()-start)/(float)1000;
		System.out.println("Fog Utility: "+f.getFogCompoundUtility());
		System.out.println("Finished Clusering Part in:"+tot_sec);
		System.out.println("Unalocated Apps: "+f.checkIfAppsAllocated());
		start=System.currentTimeMillis();
		//Exchaustive Clustering
		System.out.println("----- Clust Exhaustive Stuff -----");
		for (Integer i: f.getClusters().keySet()){
			f.getClusters().get(i).setDeployment(g.ExhaustiveCluster(f.getClusters().get(i)));
		}
		f.deployClusters();
		tot_sec=(System.currentTimeMillis()-start)/(float)1000;
		System.out.println("Fog Utility: "+f.getFogCompoundUtility());
		System.out.println("Finished Exhaustive Part in:"+tot_sec);
		System.out.println("Unalocated Apps: "+f.checkIfAppsAllocated());
		return tot_sec;
	}
	
	public static void ExhaustiveClusStuff(Fog f){
		System.out.println("----- Clust GA Stuff -----");
		Genetic g = new Genetic(f);
		//DisplayData(f);
		for (Integer i: f.getClusters().keySet()){
			f.getClusters().get(i).setDeployment(g.ExhaustiveCluster(f.getClusters().get(i)));
		}
		f.deployClusters();
		System.out.println("Fog Utility: "+f.getFogCompoundUtility());
		System.out.println("Unalocated Apps: "+f.checkIfAppsAllocated());
	}
	
	
	public static boolean Clustering(Fog f,float eps, int minPts){
		System.out.println("----- Clustering -----");
		f.clearGwClustConns();
		f.removeClusters();
		Clustering cls = new Clustering(f);
		f.createClusters(cls.DBScan(eps,minPts));//eps, minPts
		for (Integer i : f.getClusters().keySet()) {
			System.out.println("Cluster "+i+" Apps: "+f.getClusters().get(i).getApps().keySet());
		}
		if(f.checkIfAppsAllocated().size()!=0 || f.getClusters().size()<=1){
			return false;
		}else{
			return true;
		}
		
	}
	
	public static boolean AdvClustering(Fog f,float eps, int minPts){
		//System.out.println("----- Clustering -----");
		f.clearGwClustConns();
		f.removeClusters();
		AdvancedCls cls = new AdvancedCls(f);
		f.createClusters(cls.DBScan(eps,minPts));//eps, minPts
		for (Integer i : f.getClusters().keySet()) {
			System.out.println("Cluster "+i+" Apps: "+f.getClusters().get(i).getApps().keySet());
		}
		//System.out.println(f.checkIfAppsAllocated());
		//System.out.println(f.getClusters().size());
		if(f.checkIfAppsAllocated().size()!=0 || f.getClusters().size()<=1){
			return false;
		}else{
			return true;
		}
		
	}
	

	public static boolean WeightedClustering(Fog f, WeightedCls cls,float eps, int minPts,int maxPts) {
		System.out.println("----- Clustering -----");
		f.clearGwClustConns();
		f.removeClusters();
		f.createClusters(cls.DBScan(eps,minPts,maxPts));//eps, minPts
		for (Integer i : f.getClusters().keySet()) {
			System.out.println("Cluster "+i+" Apps: "+f.getClusters().get(i).getApps().keySet());
		}
		System.out.println("Unallocated Apps: "+f.checkIfAppsAllocated());
		if(f.checkIfAppsAllocated().size()!=0 || f.getClusters().size()<=1){
			System.out.println("Clustering Failed!");
			return false;
		}else{
			return true;
		}
		
	}
	
	public static boolean WeightedClustering(Fog f, WeightedCls cls, int minPts) {
		System.out.println("----- Clustering -----");
		f.clearGwClustConns();
		f.removeClusters();
		f.createClusters(cls.DBScan(minPts));//eps, minPts
		for (Integer i : f.getClusters().keySet()) {
			System.out.println("Cluster "+i+" Apps: "+f.getClusters().get(i).getApps().keySet());
		}
		System.out.println("Unallocated Apps: "+f.checkIfAppsAllocated());
		if(f.checkIfAppsAllocated().size()!=0 || f.getClusters().size()<=1){
			System.out.println("Clustering Failed!");
			return false;
		}else{
			return true;
		}
		
	}
	
	public static boolean RandomClustering(Fog f, WeightedCls cls, int minPts,int maxPts) {
		System.out.println("-> Clustering");
		f.clearGwClustConns();
		f.removeClusters();
		f.createClusters(cls.DBScan((float)0.0,minPts,maxPts));//eps, minPts
		for (Integer i : f.getClusters().keySet()) {
			System.out.println("Cluster "+i+" Apps: "+f.getClusters().get(i).getApps().keySet());
		}
		System.out.println("Unallocated Apps: "+f.checkIfAppsAllocated());
		if(f.checkIfAppsAllocated().size()!=0 || f.getClusters().size()<=1){
			System.out.println("Clustering Failed!");
			return false;
		}else{
			return true;
		}
		
	}
	
	/* Section for the weighted/CorrelationBased/Clustering GA
	 * This hold all the methods we need
	 */
	public static void weightedDistanceClusteringOptimization(Fog f){
		
		//Init
		WeightedCls cls = new WeightedCls(f);
		Map<Integer,Integer> bestSolution = new HashMap<>();
		Double bestUtil = 0.0;
		cls.initTrain(10,2);
		Map<String,Float> prog = new HashMap<String,Float>();
		boolean nextStep = true;
		//Random Population Initialization using Initial Weights
		List<Map<Integer, Integer>> bests = randomClustGA(f,cls,60,30);
		//List<Map<Integer, Integer>> bests = GAGlobal(f, 60, 50, true);
		Map<String,Double> corrApp = cls.Correlation("Deployment",cls.allAppSimilarities(bests));
		Map<String,Double> corrGw = cls.Correlation("Deployment",cls.allGwSimilarities(bests));
		if (bests == null){ System.out.println("Initial Random Clustering Failed!");return;}
		prog.put("Init",getUtility(f,bests.get(0)));
		bestUtil = getUtility(f,bests.get(0)).doubleValue();
		bestSolution = bests.get(0);
		cls.getWeight().attemptResult(getUtility(f,bests.get(0)));
		//Loop here while Weighting Algorithm knows what to do next
		while (cls.getWeight().getNextStep()){
			long start = System.currentTimeMillis();
			//Put values to the new weights Calculation
			weightsCorrBasedTraining(cls,bests);
			System.out.println("---------- New iter for Opt Started with: "+cls.getWeight().getChar()+" ----------");
			//Try Clustering based on given weights If all eps failes then weights fail
			if (WeightedClustering(f, cls,5)) {	
				weightedResourceAlloc(f, cls, 2, 0.3);
				displayClsAndRes(f);
				//Do weighted Resource Allocation based algorithm
				//Do Local GA, if Any fail then the method fails 
				List<Map<Integer, Integer>> tmpbests = Methods.GAClus(f, 60, 30, true);
				if (tmpbests == null){
						System.out.println("Direction Clustering Failed!");
						cls.getWeight().setFailed();
					}else{
						System.out.println("Direction Clustering Done in :"+((System.currentTimeMillis()-start)/1000.0));
						bests=tmpbests;
						prog.put("Clust["+cls.getWeight().getChar()+"]",getUtility(f,bests.get(0)));
						if (getUtility(f,bests.get(0))>bestUtil){
							bestUtil = getUtility(f,bests.get(0)).doubleValue();
							bestSolution = bests.get(0);
						}
						cls.getWeight().attemptResult(getUtility(f,bests.get(0)));
					}
			}else{
				System.out.println("Direction Clustering Failed!");
				cls.getWeight().setFailed();
			}
		}
		System.out.println("Results: ");
		for (String name: prog.keySet()){
			System.out.println(name+ " = "+ prog.get(name));
		}
		//ExtraTODO: If anything failes give me full info, have a function for that 
		
	}
	
	public static Map<Integer, Integer> SampleWeDiCOptimization(Fog f) {
		// TODO Auto-generated method stub
		//Init
		WeightedCls cls = new WeightedCls(f);
		Map<Integer,Integer> bestSolution = new HashMap<>();
		Double bestUtil = 0.0;
		cls.initTrain(10,2);
		Map<String,Float> prog = new HashMap<String,Float>();
		boolean nextStep = true;
		//Random Population Initialization using Initial Weights
		//Create Random Cluster and Optimize that, it needs to have a certain size 
		List<Map<Integer, Integer>> bests = sampleClustGA(f,cls,60,50,0.1);
		//List<Map<Integer, Integer>> bests = randomClustGA(f,cls,60,30);
		//List<Map<Integer, Integer>> bests = GAGlobal(f, 60, 50, true);
		Map<String,Double> corrApp = cls.Correlation("Deployment",cls.allAppSimilarities(bests));
		Map<String,Double> corrGw = cls.Correlation("Deployment",cls.allGwSimilarities(bests));
		if (bests == null){ System.out.println("Initial Random Clustering Failed!");return null;}
		//prog.put("Init",getUtility(f,bests.get(0)));
		//bestUtil = getUtility(f,bests.get(0)).doubleValue();
		//bestSolution = bests.get(0);
		cls.getWeight().attemptResult(getUtility(f,bests.get(0)));
		//Loop here while Weighting Algorithm knows what to do next
		while (cls.getWeight().getNextStep()){
			long start = System.currentTimeMillis();
			//Put values to the new weights Calculation
			weightsCorrBasedTraining(cls,bests);
			System.out.println("---------- New iter for Opt Started with: "+cls.getWeight().getChar()+" ----------");
			//Try Clustering based on given weights If all eps failes then weights fail
			if (WeightedClustering(f, cls,7)) {	
				weightedResourceAlloc(f, cls, 2, 0.3);
				//displayClsAndRes(f);
				//Do weighted Resource Allocation based algorithm
				//Do Local GA, if Any fail then the method fails 
				List<Map<Integer, Integer>> tmpbests = Methods.GAClus(f, 60, 150, true);
				if (tmpbests == null){
						System.out.println("Direction Clustering Failed!");
						cls.getWeight().setFailed();
					}else{
						System.out.println("Direction Clustering Done in :"+((System.currentTimeMillis()-start)/1000.0));
						bests=tmpbests;
						prog.put("Clust["+cls.getWeight().getChar()+"]",getUtility(f,bests.get(0)));
						if (getUtility(f,bests.get(0))>bestUtil){
							bestUtil = getUtility(f,bests.get(0)).doubleValue();
							bestSolution = bests.get(0);
						}
						cls.getWeight().attemptResult(getUtility(f,bests.get(0)));
					}
			}else{
				System.out.println("Direction Clustering Failed!");
				cls.getWeight().setFailed();
			}
		}
		System.out.println("Results: ");
		for (String name: prog.keySet()){
			System.out.println(name+ " = "+ prog.get(name));
		}
		return bests.get(0);
	}



	private static void weightsCorrBasedTraining(WeightedCls cls,List<Map<Integer, Integer>> bests) {
		//TODO: Fix to actually have a training alogrithm
		//Parameter Correlation Calculation based on Distance Clustering
		if (bests==null){
			cls.getWeight().correlationResults(new HashMap<>(),new HashMap<>());
		}else{
			Map<String,Double> corrApp = cls.Correlation("Deployment",cls.allAppSimilarities(bests));
			Map<String,Double> corrGw = cls.Correlation("Deployment",cls.allGwSimilarities(bests));
			//SetCorrelation
			System.out.println("Rand Apps Correlations: "+corrApp);
			System.out.println("Rand Gws Correlations: "+corrGw);
			cls.getWeight().correlationResults(corrApp,corrGw);
		}
		cls.setCorrelation(cls.getWeight().appWeights(),cls.getWeight().gwWeights());
		//cls.setCorrelation(corrApp,corrGw,0.3);
	}



	private static List<Map<Integer, Integer>> randomClustGA(Fog f, WeightedCls cls,int size, int cnt) {
		long start = System.currentTimeMillis();
		if (RandomClustering(f, cls,5,15)) {	
			weightedResourceAlloc(f, cls, 3, 0.05);
			displayClsAndRes(f);
			List<Map<Integer, Integer>> tmp = Methods.GAClus(f, size, cnt, true);
			System.out.println("Random Clust finished in :"+((System.currentTimeMillis()-start)/1000.0));
			return tmp;
		}else{
			return null;
		}
	}
	
	private static List<Map<Integer, Integer>> sampleClustGA(Fog f, WeightedCls cls, int count, int size, double proc) {
		// TODO Auto-generated method stub
		//Gnerate new Cluster Randomply Random select Apps, the size will be of 
		long start = System.currentTimeMillis();
		System.out.println("-> SampleClustering");
		List<Integer> apps = new ArrayList<>();
		List<Integer> totApps = new ArrayList<Integer>(f.getApps().keySet());
		while (apps.size()<proc*totApps.size()){
			//Get Random app add it to list
			Collections.shuffle(totApps);
				apps.add(totApps.get(0));
			
		}
		f.clearGwClustConns();
		f.removeClusters();
		List<Set<Integer>> tmpList= new ArrayList<>();
		tmpList.add(new HashSet<Integer>(apps));
		f.createClusters(tmpList);//eps, minPts
		cls.resetGwWeights(1.0);
		cls.resetAppWeights(1.0);
		sampleResourceAlloc(f,cls);
		//displayClsAndRes(f);
		List<Map<Integer, Integer>> tmp = Methods.sampGAClus(f, size, count, true);
		cls.clearWeights();
		System.out.println("Sample Clustering finished in :"+((System.currentTimeMillis()-start)/1000.0));
		return tmp;
	}


	//End of Weighted Part

	public static void IterativeCorrelationClustering(Fog f,Integer iter) {
		long start = System.currentTimeMillis();
		WeightedCls cls = new WeightedCls(f);
		Map<String,Float> prog = new HashMap<String,Float>();
		List<Map<Integer, Integer>> bests = Methods.GAGlobal(f, 120, 500, true);
		prog.put("Global",getUtility(f,bests.get(0)));
		if (bests==null){		
			//displayClsAndRes(f);
			System.out.println("Failed Global GA");
		}
		System.out.println("GlobalGA Time Elapsed: " + (System.currentTimeMillis() - start) / (float) 1000);
		Map<String,Double> corrApp = cls.Correlation("Deployment",cls.allAppSimilarities(bests));
		Map<String,Double> corrGw = cls.Correlation("Deployment",cls.allGwSimilarities(bests));
		System.out.println("Apps Correlations: "+corrApp);
		System.out.println("Gws Correlations: "+corrGw);
		start = System.currentTimeMillis();
		//Map<String,Double> corrApp = new HashMap<String,Double>();
		//Map<String,Double> corrGw = new HashMap<String,Double>();
		//List<Map<Integer, Integer>> bests = new ArrayList<>();
		if (RandomClustering(f, cls,5,20)) {	
			weightedResourceAlloc(f, cls, 3, 0.05);
			// displayClsAndRes(f);
			bests = Methods.GAClus(f, 40, 150, true);
			System.out.println("Rand Clust Elapsed: " + (System.currentTimeMillis() - start) / (float) 1000);
			corrApp = cls.Correlation("Deployment", cls.allAppSimilarities(bests));
			corrGw = cls.Correlation("Deployment", cls.allGwSimilarities(bests));
			System.out.println("Apps Correlations: "+corrApp);
			System.out.println("Gws Correlations: "+corrGw);
			cls.setCorrelation(corrApp,corrGw,0.3);
		}else{
			System.out.println("Not even Ranomd FAIL!");
		}
		for (int i = 0; i < iter; i++) {
			long start2 = System.currentTimeMillis();
			System.out.println("----- Training Iteration nr. "+i+" -----");
			cls.setCorrelation(corrApp,corrGw,0.3);
			if (WeightedClustering(f, cls,5)) {	
				weightedResourceAlloc(f, cls, 3, 0.05);
				// displayClsAndRes(f);
				bests = Methods.GAClus(f, 40, 100, true);
				System.out.println("Clustering Time: " + (System.currentTimeMillis() - start2) / (float) 1000);
				if (bests == null) {
					System.out.println("Failed Clustering GA");
				} else {
					prog.put("Clust["+i+"]",getUtility(f,bests.get(0)));
					corrApp = cls.Correlation("Deployment", cls.allAppSimilarities(bests));
					corrGw = cls.Correlation("Deployment", cls.allGwSimilarities(bests));
					System.out.println("Apps Correlations: "+corrApp);
					System.out.println("Gws Correlations: "+corrGw);
				}
			} else{
					System.out.println("Failed Everything");
				}
		}
		System.out.println("Clustering Time Elapsed: " + (System.currentTimeMillis() - start) / (float) 1000);
		System.out.println("Props: "+prog);
	}
	
	public static boolean CorrelationClusterin(Fog f){
		long start = System.currentTimeMillis();
		WeightedCls cls = new WeightedCls(f);
		List<Map<Integer, Integer>> bests = Methods.GAGlobal(f, 60, 500, true);
		/*if (bests==null){		
			displayClsAndRes(f);
			System.out.println("Failed Global GA");
			return false;
		}
		System.out.println("GlobalGA Time Elapsed: " + (System.currentTimeMillis() - start) / (float) 1000);
		Map<String,Double> corrApp = cls.Correlation("Deployment",cls.allAppSimilarities(bests));
		Map<String,Double> corrGw = cls.Correlation("Deployment",cls.allGwSimilarities(bests));
		System.out.println("Apps Correlations: "+corrApp);
		System.out.println("Gws Correlations: "+corrGw);
		cls.setCorrelation(corrApp,corrGw,0.05,0.1);*/
		if (WeightedClustering(f, cls,(float)0.9, 6,12)){
			weightedResourceAlloc(f,cls,3,0.1);
			//displayClsAndRes(f);
			System.out.println("Clustering and Alloc Time: " + (System.currentTimeMillis() - start) / (float) 1000);
			if (Methods.GAClus(f, 40, 150, true)==null){
				System.out.println("Failed Clustering GA");
				return false;
			}
		}else{
			System.out.println("Failed Clustering");
			return false;
		}
		System.out.println("Clustering Time Elapsed: " + (System.currentTimeMillis() - start) / (float) 1000);
		return true;
	}
	
	public static void ResourceAllocation(Fog f){
		f.clearAppToGws();
		f.distributeGw2Cluster();	
	}
	
	public static void nandorsAlphaResourceAlloc(Fog f){
		f.clearAppToGws();
		AdvancedCls cls = new AdvancedCls(f);
		cls.distributeGw2Cluster();
		//displayClsAndRes(f);
		cls.resolveAnomalies();
		displayClsAndRes(f);
	}
	
	public static void weightedResourceAlloc(Fog f, WeightedCls cls,int maxShare,double shareThreshold) {
		f.clearAppToGws();
		cls.distributeGw2Cluster(maxShare,shareThreshold);
		//displayClsAndRes(f);
		cls.resolveApptoGwNoise();
		//displayClsAndRes(f);
	}
	
	public static void sampleResourceAlloc(Fog f, WeightedCls cls) {
		f.clearAppToGws();
		cls.sampleGw2Cluster();
	}
	
	public static void displayClsAndRes(Fog f){
		System.out.println("-> Cluster Share Apps and Load-----");
		System.out.println("Total Load on System: " + f.getTotalLoad());
		System.out.println("Total Free Space on System: " + f.getTotalFreeCapacity());
		for (Integer i : f.getClusters().keySet()) {
			System.out.print("Cluster "+i+" Load: "+f.getClusters().get(i).getClusterLoad()+" AllocatedRes: "+f.getClusters().get(i).getTotResShare()+" Rate: "+f.getClusters().get(i).ShareRate());
			System.out.println(" Apps: "+f.getClusters().get(i).getApps().keySet()+" Gateways: "+f.getClusters().get(i).getGateways().keySet());
			System.out.print("Gw Shares: ");
			for (Integer g : f.getClusters().get(i).getGateways().keySet()){
				System.out.print(" | " + String.format("%.1f",f.getGateways().get(g).getClusterShare(i)));
			}
			System.out.println();
		}
		for (Integer g:f.getGateways().keySet()){
			System.out.print("Gateway "+g+" Shares: ");
			Float tot = (float)0.0;
			tot+=f.getGateways().get(g).getGwBaseLoad();
			System.out.print( String.format("%.1f",f.getGateways().get(g).getGwBaseLoad())+" |");
			for (Integer c:f.getGateways().get(g).getCluster().keySet()){
				System.out.print("| " + String.format("%.1f",f.getGateways().get(g).getClusterShare(c))+" ");
				tot+=f.getGateways().get(g).getClusterShare(c);
			}
			System.out.println(" || "+tot);
		}
		System.out.println("Unallocated Apps:"+f.checkIfAppsAllocated());
		System.out.println("OverAllocatedApps:"+f.checkIfAppsOverAlloc());
		System.out.println("Cumulative share Rate:"+f.cumClustShare());
	}



	
}