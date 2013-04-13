package GUI;

import info.monitorenter.gui.chart.*;
import info.monitorenter.gui.chart.traces.Trace2DLtd;

import info.monitorenter.gui.chart.io.ADataCollector;
import info.monitorenter.gui.chart.Chart2D;
import info.monitorenter.gui.chart.ITrace2D;

import java.awt.*;
import javax.swing.JPanel;

public class PlotterMode3 {
	
	Chart2D chart;
	String name;

	ITrace2D trace1;
	ITrace2D trace2;
	ITrace2D trace3;
	
	ADataCollector collector;
	
	public PlotterMode3(String name1, String name2, String name3, int points){
		
		 chart = new Chart2D();
		 trace1 = new Trace2DLtd(points, name1);
		 trace1.setColor(Color.BLUE);
		 chart.addTrace(trace1);

		 trace2 = new Trace2DLtd(points, name2);
		 trace2.setColor(Color.RED);
		 chart.addTrace(trace2);

		 trace3 = new Trace2DLtd(points, name3);
		 trace3.setColor(Color.GREEN);
		 chart.addTrace(trace3);

	}
	
	public void reset(){		
		trace1.removeAllPoints();
		trace2.removeAllPoints();
		trace3.removeAllPoints();
	}
		
	public JPanel getPanel(){
		JPanel content = new JPanel(new BorderLayout());          
        content.add(chart);
		return content;
	}
		
	public void addPoint(double  x, double y1, double y2, double y3){
		TracePoint2D point1 = new TracePoint2D(x, y1);
		trace1.addPoint(point1);

		TracePoint2D point2 = new TracePoint2D(x, y2);
		trace2.addPoint(point2);

		TracePoint2D point3 = new TracePoint2D(x, y3);
		trace3.addPoint(point3);
				
	}	 

}