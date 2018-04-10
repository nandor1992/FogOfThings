package org.karaf.event_create;

import java.lang.management.ClassLoadingMXBean;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.OperatingSystemMXBean;
import java.lang.management.RuntimeMXBean;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;

import java.lang.Integer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.Date;
import java.util.LinkedList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Iterator;
import java.util.Formatter;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

import static java.util.concurrent.TimeUnit.*;

import java.io.IOException;

public class Threads{
	
	private Map<Long, Long> previousThreadCPUTime = new HashMap<Long, Long>();
	private List<String> apps = new ArrayList<String>();
	private long lastUpTime = 0;
	private int sortIndex = 3;
	private RuntimeMXBean runtime = ManagementFactory.getRuntimeMXBean();
	private OperatingSystemMXBean os = ManagementFactory.getOperatingSystemMXBean();
	private ThreadMXBean threads = ManagementFactory.getThreadMXBean();
	private MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
	private ClassLoadingMXBean cl = ManagementFactory.getClassLoadingMXBean();
	
	public Threads(List<String> apps)
	{
		this.apps=apps;
	}
	
	public void run(){  
		System.out.println("thread is running...");  
		}  
	
	public Map<String,Double> getThreadsInfo(){
		 try {
			return printTopThreads(threads, runtime);
		} catch (Exception e) {
			e.printStackTrace();
		}
		 return null;
	}
	
    
    private Map<String,Double> printTopThreads(ThreadMXBean threads, RuntimeMXBean runtime) throws InterruptedException, IOException {
        // Test if this JVM supports telling us thread stats!
        if (threads.isThreadCpuTimeSupported()) {

            long uptime = runtime.getUptime();
            long deltaUpTime = uptime - lastUpTime;
            lastUpTime = uptime;

            Map<Long, Object[]> stats = getThreadStats(threads, deltaUpTime);

            List<Long> sortedKeys = sortByValue(stats);

            // Display threads
            return printThreads(sortedKeys, stats);

        } else {
        	return null;
        }
    }
    
    private Map<String,Double> printThreads(List<Long> sortedKeys, Map<Long, Object[]> stats) {
        int displayedThreads = 0;
       	Map<String,Double>  ret = new Hashtable();
        for (Long tid : sortedKeys) {
            if (displayedThreads > 30) {
                break; // We're done displaying threads.
            }
            if (apps.contains(stats.get(tid)[1].toString())){
            	String name=stats.get(tid)[1].toString();
            	if (ret.containsKey(name)){
            		ret.put(name,ret.get(name)+Double.parseDouble(stats.get(tid)[3].toString()));
            	}else
            	{
            		ret.put(name,Double.parseDouble(stats.get(tid)[3].toString()));
            	}
            }
            displayedThreads++;
            }
        return ret;
    }
    
    private Map<Long, Object[]> getThreadStats(ThreadMXBean threads, long deltaUpTime) {
        Map<Long, Object[]> allStats = new HashMap<Long, Object[]>();

        for (Long tid : threads.getAllThreadIds()) {

            ThreadInfo info = threads.getThreadInfo(tid);
            if (info != null) {
                Object[] stats = new Object[6];
                long threadCpuTime = threads.getThreadCpuTime(tid);
                long deltaThreadCpuTime;

                if (previousThreadCPUTime.containsKey(tid)) {
                    deltaThreadCpuTime = threadCpuTime - previousThreadCPUTime.get(tid);
                }
                else {
                    deltaThreadCpuTime = threadCpuTime;
                }

                previousThreadCPUTime.put(tid, threadCpuTime);

                String name = info.getThreadName();
                stats[0] = "";
                stats[1] = name.substring(0, Math.min(name.length(), 40));
                stats[2] = "";
                stats[3] = getThreadCPUUtilization(deltaThreadCpuTime, deltaUpTime);
                stats[4] = "";
                stats[5] = "";

                allStats.put(tid, stats);
            }
        }

        return allStats;
    }

    private double getThreadCPUUtilization(long deltaThreadCpuTime, long totalTime) {
        return getThreadCPUUtilization(deltaThreadCpuTime, totalTime, 1000 * 1000);
    }

    private double getThreadCPUUtilization(long deltaThreadCpuTime, long totalTime, double factor) {
        if (totalTime == 0) {
            return 0;
        }
        return deltaThreadCpuTime / factor / totalTime * 100d;
    }
    
    public String timeUnitToMinutesSeconds(TimeUnit timeUnit, long value) {
        if (value == -1) {
            return "0";
        }
        long valueRemaining = value;
        StringBuilder sb = new StringBuilder();
        Formatter formatter = new Formatter(sb);

        long minutes = MINUTES.convert(valueRemaining, timeUnit);
        valueRemaining = valueRemaining - timeUnit.convert(minutes, MINUTES);
        long seconds = SECONDS.convert(valueRemaining, timeUnit);
        valueRemaining = valueRemaining - timeUnit.convert(seconds, SECONDS);
        long nanoseconds = NANOSECONDS.convert(valueRemaining, timeUnit);
        // min so that 99.5+ does not show up as 100 hundredths of a second
        int hundredthsOfSecond = Math.min(Math.round(nanoseconds / 10000000f), 99);
        formatter.format("%2d:%02d.%02d", minutes, seconds, hundredthsOfSecond);
        return sb.toString();
    }
 
    public List sortByValue(Map map) {
        List<Map.Entry> list = new LinkedList(map.entrySet());
        Collections.sort(list, new Comparator<Map.Entry>() {

            public int compare(Map.Entry o1, Map.Entry o2) {
                Comparable c1 = ((Comparable) (((Object[]) o1.getValue())[sortIndex]));
                Comparable c2 = ((Comparable) (((Object[]) o2.getValue())[sortIndex]));
                return c1.compareTo(c2);
            }
        });
        Collections.reverse(list);
        
        List result = new ArrayList();
        for (Iterator<Map.Entry> it = list.iterator(); it.hasNext();) {
            result.add(it.next().getKey());
        }
        return result;
    }
    
}
