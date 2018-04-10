package org.karaf.event_create;

import java.util.Random;

public class Load {

	public void doMatrice(int qty){
		for( int i=0;i<qty;i++){
			int m1[][];
			int m2[][];		
			int tmp[][];
			m1=randMatrice();
			m2=randMatrice();
			tmp=addMatrice(m1, m2);
			tmp=multMatrice(m1, m2);
		}
	}
	
	public int[][] randMatrice(){
		int m1[][];		
		Random rand = new Random();
		m1=new int[20][20];
		for (int i=0;i<20;i++){
			for (int j=0;j<20;j++){
				m1[i][j] = rand.nextInt(200);
			}
		}
		return m1;
	}
	
	public int[][] addMatrice(int[][] a, int[][] b)
	{
		int ret[][];
		ret=new int[20][20];
		for (int i=0;i<20;i++){
			for (int j=0;j<20;j++){
				ret[i][j]=a[i][j]+b[i][j];
			}
		}
		return ret;
	}
	
	public int[][] multMatrice(int[][] a, int[][] b)
	{
		int ret[][];
		ret=new int[20][20];
		for (int i=0;i<20;i++){
			for (int j=0;j<20;j++){
				for (int k=0;k<20;k++)
				{
					ret[i][j]=ret[i][j]+a[i][k]+b[k][j];
				}
			}
		}
		return ret;
	}
	
	public void displayMatrice(int[][] a)
	{
		System.out.println("Displaying Matrice");
		for (int i=0;i<20;i++){
			for (int j=0;j<20;j++){
				System.out.print(a[i][j]+" ");
			}
			System.out.println();
		}
	}
	/*------------Filtering Operations-----------*/
	
	public void doFiltering(int qty){
		for( int i=0;i<qty;i++){
			int data[];
			int minmax[]=new int[2];
			data=randData();
			float sma[]=smaData(data);
			float avg=avgData(data);
			minmax=minmaxData(data);
			sortData(data,true);
			sortData(data,false);
		}
	}
	
	public int[] sortData(int data[],boolean type){
		int tmp=0;
		for (int i=0;i<99;i++)
		{
			for (int j=i;j<100;j++)
			{
				if (!(data[i]>data[j] ^ type)){
					tmp=data[j];
					data[j]=data[i];
					data[i]=tmp;
				}
			}
		}
		return data;
	}
	public float avgData(int data[]){
		int avg=0;
		for (int i=0;i<100;i++){
			avg=avg+data[i]/100;
		}
		return avg;
	}
	
	public int[] minmaxData(int data[]){
		int ext[]=new int[2];
		ext[0]=data[0];
		ext[1]=data[0];
		for (int i=1;i<100;i++){
			if (data[i]<ext[0]){
				ext[0]=data[i];
			}
			if (data[i]>ext[1]){
				ext[1]=data[i];
			}
		}
		return ext;
	}
	public float[] smaData(int data[]){
		///Simple moving average
		float sma[] = new float[100];
		float sma_tmp=0;
		int curr=4;
		//Length of sma =5;
		for (int i=0;i<5;i++)
		{
			sma_tmp=sma_tmp+data[i];
		}
		sma_tmp=sma_tmp/5;
		sma[4]=sma_tmp;
		sma[0]=sma_tmp;
		sma[1]=sma_tmp;
		sma[2]=sma_tmp;
		sma[3]=sma_tmp;
		while (curr<99){
			sma_tmp=sma_tmp-(data[curr-4]/5)+(data[curr+1]/5);
			sma[curr]=sma_tmp;
			curr++;
		}
		sma[99]=sma_tmp;
		return sma;
	}
	
	public int[] randData(){
		int data[];
		Random rand = new Random();
		data=new int[100];
		for (int i=0;i<100;i++)
		{
			data[i]=rand.nextInt(1024);
		}
		return data;
	}
	
	public void printData(int data[]){
		System.out.println("Printing Data");
		for (int i=0;i<100;i++){
			System.out.print(data[i]+" ");
		}
		System.out.println();
	}
	
	public void printData(float data[]){
		System.out.println("Printing Data");
		int len=data.length;
		for (int i=0;i<len;i++){
			System.out.print(String.format("%5.4f",data[i])+" ");
		}
		System.out.println();
	}
	/*--------------Part For Flops--------------*/
	public void doFlops(int qty){
		for( int i=0;i<qty;i++){
			float d1[];
			float d2[];
			d1=randFloat();
			d2=randFloat();
			float ret[][]=doFloatOps(d1, d2);
		}
	}
	
	public float[][] doFloatOps(float[] d1,float[] d2)
	{
		float ret[][]=new float[4][1000];
		for (int i=0; i<1000;i++){
			ret[0][i]=d1[i]+d2[i];
			ret[1][i]=d1[i]-d2[i];
			ret[2][i]=d1[i]*d2[i];
			ret[3][i]=d1[i]/d2[i];
		}
		return ret;
	}
	
	public float[] randFloat(){
		float data[];
		Random rand = new Random();
		data=new float[1000];
		for (int i=0;i<1000;i++)
		{
			data[i]=rand.nextFloat();
		}
		return data;
	}
}
