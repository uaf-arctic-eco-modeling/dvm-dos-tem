package GUI;

import info.monitorenter.gui.chart.*;
import info.monitorenter.gui.chart.traces.Trace2DLtd;

import info.monitorenter.gui.chart.io.ADataCollector;
import info.monitorenter.gui.chart.Chart2D;
import info.monitorenter.gui.chart.ITrace2D;

import java.awt.*;
import javax.swing.JPanel;

public class PlotterMode1 {
	
	Chart2D chart;
	String name;

	ITrace2D trace;
	
	ADataCollector collector;

	public PlotterMode1(String name, int points){
		
		 chart = new Chart2D();
		 trace = new Trace2DLtd(points, name);
		 trace.setColor(Color.BLUE);
		 chart.addTrace(trace);
		         
	}
		
	public void reset(){		
		trace.removeAllPoints();
	}
		
	public JPanel getPanel(){
		JPanel content = new JPanel(new BorderLayout());          
        content.add(chart);
		return content;
	}
		
	public void addPoint(double  x, double y){
		TracePoint2D point = new TracePoint2D(x, y);
		trace.addPoint(point);
				
	}	 

}