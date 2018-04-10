package main;

public class TestClass {
	
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		for (int i=0;i<300;i++){
			Load l1 = new Load();
			Integer load=1;
			long timeBefore = System.nanoTime();
	    	l1.doMatrice(load);
			l1.doFiltering(load);
			l1.doFlops(load);
	    	long timeAfter = System.nanoTime();
	    	long elapsed_time = timeAfter - timeBefore;
			System.out.println("Tasks Took:"+elapsed_time/1000);
		}
	}

}
