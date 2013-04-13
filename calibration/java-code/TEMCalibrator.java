
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;

import javax.swing.JFrame;
import javax.swing.JTextArea;
import javax.swing.SpringLayout;

import ASSEMBLER.Runner;
import GUI.TemCalGUI;
import GUI.Configurer;
import GUI.BioVariablePlotter;
import GUI.PhyVariablePlotter;

public class TEMCalibrator {
	
	// using GUI or not to run Calibration mode   
	static boolean GUI = true;

	public static void main(String[] args) throws Exception{	
		System.loadLibrary("temcore");
		
		//message box for information
		try {
			JFrame f = new JFrame("TEM Run Info");
			f.setLayout(new BorderLayout());
			f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		
			JTextArea teminfoTA = new JTextArea();
			teminfoTA.append(null);
			
			SpringLayout slayout = new SpringLayout();
			slayout.putConstraint(SpringLayout.NORTH, teminfoTA, 5,SpringLayout.NORTH, f);
			slayout.putConstraint(SpringLayout.WEST,teminfoTA, 0,SpringLayout.WEST, f);

			f.add(teminfoTA, BorderLayout.CENTER);
			
			f.setLocation(2,1);
			f.setPreferredSize(new Dimension(500, 800));
			f.setSize(540, 125);
			f.setVisible(true);
	    
			MessageConsole mc = new MessageConsole(teminfoTA);
			mc.redirectOut(null, System.out);
			mc.redirectErr(Color.RED, null);
			mc.setMessageLines(6);

		} catch (Exception e){	  	
			System.out.println(e.getMessage());
		} finally {
			//System.out.println("In final");
		}

		System.out.println("DVM-DOS-TEM Calibrator - Java Version 2.0");
		System.out.println("F.-M. YUAN");
		System.out.println("Climate Change Science Institute, ORNL; and");
		System.out.println("The Spatial Ecological Laboratory, University of Alaska Fairbanks");
		
		//logger
		org.apache.log4j.BasicConfigurator.configure();
	    org.apache.log4j.Logger logger = org.apache.log4j.Logger.getRootLogger();
	    logger.setLevel(org.apache.log4j.Level.OFF);	

	    //			
		if (GUI) {			
						
			TemCalGUI caligui = new TemCalGUI();
			Configurer config = new Configurer();
			BioVariablePlotter bvplotter = new BioVariablePlotter();
			PhyVariablePlotter pvplotter = new PhyVariablePlotter();
			
			caligui.setConfigurer(config);
			caligui.setVarPlotter(bvplotter);
			caligui.setVar2Plotter(pvplotter);

								
		} else {			//TEM run 

			Runner Siter = new Runner();
			
			//TEM I/O options
			String controlfile = "config/controlfile_site.txt";
			String runmode = "siter";
						
			Siter.chtid = 1;
			
			//TEM general initialization and data-reading
			Siter.initInput(controlfile, runmode);
			Siter.initOutput();
			Siter.setupData();
			Siter.setupIDs();
			
			//run
			int error = Siter.run_siter();
			
			if (error ==0) {
				System.out.println("run TEM stand-alone - sucessfully done!");
			} else {
				System.out.println("run TEM stand-alone - incorrectly done!");				
			}
		}
	
	}

}
