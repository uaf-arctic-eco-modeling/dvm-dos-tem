package GUI;

//TEM Calibration Runner GUI

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import java.io.BufferedReader;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.PrintStream;
import java.util.Vector;

import javax.swing.*;
import javax.swing.event.*;

//
import DATA.ConstCohort;

import ASSEMBLER.Runner;
import ASSEMBLER.TEMeqrunner;
import TEMJNI.soipar_bgc;
import TEMJNI.soipar_cal;
import TEMJNI.vegpar_cal;

public class TemCalGUI{
	TEMeqrunner Caliber = new TEMeqrunner();
	Configurer config;
	BioVariablePlotter var1plotter;
	PhyVariablePlotter var2plotter;

	public void setConfigurer(Configurer configure){
		config = configure;
	}

	public void setVarPlotter(BioVariablePlotter bvp){
		var1plotter = bvp;
	}

	public void setVar2Plotter(PhyVariablePlotter pvp){
		var2plotter = pvp;
	}

//////////////////////////////////////////////////////////////////////////
	JFrame fcontrol = new JFrame("TEM Calibrator Java Interface");

	// for model control file input

	JTextField controlfileTF = new JTextField();
    JButton selectControlfileB = new JButton("Browse");

	JTextField casenameTF  = new JTextField();

	JTextField configdirTF   = new JTextField();
	JButton selectConfigdirB = new JButton("Browse");
	JTextField outputdirTF   = new JTextField();
	JButton selectOutputdirB = new JButton("Browse");
	JTextField reginputdirTF = new JTextField();
	JButton selectReginputdirB = new JButton("Browse");
	JTextField grdinputdirTF   = new JTextField();
	JButton selectGrdinputdirB = new JButton("Browse");
	JTextField chtinputdirTF   = new JTextField();
	JButton selectChtinputdirB = new JButton("Browse");
	JTextField chtidinputTF    = new JTextField();

	JButton updateControlB = new JButton("Update Control File");

	// for model module switches
	JRadioButton[] envmodjrb= new JRadioButton[2];
	ButtonGroup envmodjbg = new ButtonGroup();

	JRadioButton[] bgcmodjrb= new JRadioButton[2];
	ButtonGroup bgcmodjbg = new ButtonGroup();
	JRadioButton[] nfeedjrb = new JRadioButton[2];
	ButtonGroup nfeedjbg = new ButtonGroup();
	JRadioButton[] avlnjrb= new JRadioButton[2];
	ButtonGroup avlnjbg = new ButtonGroup();
	JRadioButton[] baselinejrb= new JRadioButton[2];
	ButtonGroup baselinejbg = new ButtonGroup();

	JRadioButton[] dslmodjrb= new JRadioButton[2];
	ButtonGroup dslmodjbg = new ButtonGroup();

	JRadioButton[] dvmmodjrb= new JRadioButton[2];
	ButtonGroup dvmmodjbg = new ButtonGroup();
	JRadioButton[] updatelaijrb= new JRadioButton[2];
	ButtonGroup updatelaijbg = new ButtonGroup();

	JRadioButton[] firemodjrb= new JRadioButton[2];
	ButtonGroup firemodjbg = new ButtonGroup();

	// for model datalogger
    JTextField calbgcTF = new JTextField();
    JButton selectCalibgcfileB = new JButton("Browse");

    JTextField calparTF = new JTextField();
    JButton selectInitparfileB = new JButton("Browse");

    JTextField cmtcodeTF = new JTextField();
    JTextField pftcodeTF = new JTextField();
      
    JComboBox pickpftCB;

    JTable calparTB;
    JTable stateTB;
    JTable targetTB;

	// for model calibration operating

    JButton setupB = new JButton("Setup");
    JButton resetupB = new JButton("Re-Setup");
    JButton runmodeB = new JButton("Calibration");
    JButton exitB = new JButton("EXIT");
    JButton startpauseB = new JButton("Start");

    ParameterChanger cmaxChanger = new ParameterChanger("CMAX", 0., 1);
    ParameterChanger nmaxChanger = new ParameterChanger("NMAX", 0., 0);
    ParameterChanger cfalllChanger = new ParameterChanger("CFALLleaf", 0., -2);
    ParameterChanger cfallsChanger = new ParameterChanger("CFALLstem", 0., -2);
    ParameterChanger cfallrChanger = new ParameterChanger("CFALLroot", 0., -2);
    ParameterChanger nfalllChanger = new ParameterChanger("NFALLleaf", 0., -2);
    ParameterChanger nfallsChanger = new ParameterChanger("NFALLstem", 0., -3);
    ParameterChanger nfallrChanger = new ParameterChanger("NFALLroot", 0., -3);
    ParameterChanger frgChanger = new ParameterChanger("FRG", 0., -1);
    ParameterChanger kraChanger = new ParameterChanger("KRA", 0., -5);
    ParameterChanger krblChanger = new ParameterChanger("KRBleaf", 0., -2);
    ParameterChanger krbsChanger = new ParameterChanger("KRBstem", 0., -2);
    ParameterChanger krbrChanger = new ParameterChanger("KRBroot", 0., -2);
    ParameterChanger micbnupChanger = new ParameterChanger("MICBNUP", 0., -1);
    ParameterChanger kdcmosscChanger = new ParameterChanger("KDCmoss", 0., -2);
    ParameterChanger kdcrawcChanger = new ParameterChanger("KDCrawc", 0., -2);
    ParameterChanger kdcsomaChanger = new ParameterChanger("KDCsoma", 0., -3);
    ParameterChanger kdcsomprChanger = new ParameterChanger("KDCsompr", 0., -4);
    ParameterChanger kdcsomcrChanger = new ParameterChanger("KDCsomcr", 0., -5);

    JButton parresetB = new JButton("Reset to Init");
    JButton parrestoreB = new JButton("Reset to Prev");
    JButton paroutputB = new JButton("Output");

	public TemCalGUI(){

		fcontrol.setLayout(new BorderLayout());
		fcontrol.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);

		JTabbedPane controlTP = new JTabbedPane(); //container of tabbed panel (currently two: configuer, calibrator)

        // There are 3 tabbed panels: configP, datalogP, and caliP
        try {
		    SpringLayout slayout = new SpringLayout();

        	//Configuration Tab of Control Panel (configP)
        	JPanel configP = new JPanel();
			configP.setLayout(slayout);

			// 1) control file browsing

	        JLabel controlL = new JLabel(" ------------------- MODEL CONTROL FILE ------------------");
			controlL.setPreferredSize(new Dimension(450, 30));
			slayout.putConstraint(SpringLayout.NORTH, controlL, 5, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,controlL, 5, SpringLayout.WEST, configP);
			configP.add(controlL);
			controlfileTF.setPreferredSize(new Dimension(390, 30));
			slayout.putConstraint(SpringLayout.NORTH, controlfileTF, 30, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,controlfileTF, 10, SpringLayout.WEST, configP);
			configP.add(controlfileTF);
			controlfileTF.setToolTipText("A simplified TEM control file, in which only the following is as input");
			selectControlfileB.setPreferredSize(new Dimension(80, 30));
			slayout.putConstraint(SpringLayout.NORTH, selectControlfileB, 30, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,selectControlfileB, 405, SpringLayout.WEST, configP);
			configP.add(selectControlfileB);
		    selectControlfileB.addActionListener(new ControlSelector());
			selectControlfileB.setToolTipText("Browse to choose the model control file ...");

			// 2) run case name
	        JLabel casenameL = new JLabel("Run Case Title");
			casenameL.setPreferredSize(new Dimension(400, 30));
			slayout.putConstraint(SpringLayout.NORTH, casenameL, 60, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,casenameL, 5, SpringLayout.WEST, configP);
			configP.add(casenameL);
			casenameTF.setPreferredSize(new Dimension(380, 30));
			slayout.putConstraint(SpringLayout.NORTH, casenameTF, 85, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,casenameTF, 20, SpringLayout.WEST, configP);
			configP.add(casenameTF);
			casenameTF.addActionListener(new configUpdater());
			casenameTF.setToolTipText("editable if needed");

			// 3) config directory

	        JLabel configdirL = new JLabel("Model Config Diretory");
			configdirL.setPreferredSize(new Dimension(400, 30));
			slayout.putConstraint(SpringLayout.NORTH, configdirL, 115, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,configdirL, 5, SpringLayout.WEST, configP);
			configP.add(configdirL);
			configdirTF.setPreferredSize(new Dimension(380, 30));
			slayout.putConstraint(SpringLayout.NORTH, configdirTF, 140, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,configdirTF, 20, SpringLayout.WEST, configP);
			configP.add(configdirTF);
			configdirTF.addActionListener(new configUpdater());
			configdirTF.setToolTipText("where all parameters and default initial conditions files to be looking for ");
			selectConfigdirB.setPreferredSize(new Dimension(80, 30));
			slayout.putConstraint(SpringLayout.NORTH, selectConfigdirB, 140, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,selectConfigdirB, 405, SpringLayout.WEST, configP);
			configP.add(selectConfigdirB);
			selectConfigdirB.setEnabled(false);

			// 4) regional input directory

			JLabel reginputdirL = new JLabel("Regional data Input Directory");
			reginputdirL.setPreferredSize(new Dimension(400, 30));
			slayout.putConstraint(SpringLayout.NORTH, reginputdirL, 170, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,reginputdirL, 5, SpringLayout.WEST, configP);
			configP.add(reginputdirL);
			reginputdirTF.setPreferredSize(new Dimension(380, 30));
			slayout.putConstraint(SpringLayout.NORTH, reginputdirTF, 195, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,reginputdirTF, 20, SpringLayout.WEST, configP);
			configP.add(reginputdirTF);
			reginputdirTF.addActionListener(new configUpdater());
			reginputdirTF.setToolTipText("Diretory to read regional-level data");
			selectReginputdirB.setPreferredSize(new Dimension(80, 30));
			slayout.putConstraint(SpringLayout.NORTH, selectReginputdirB, 195, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,selectReginputdirB, 405, SpringLayout.WEST, configP);
			configP.add(selectReginputdirB);
			selectReginputdirB.setEnabled(false);

			// 5) regional input directory

	        JLabel grdinputdirL = new JLabel("Grided data Input Directory");
			grdinputdirL.setPreferredSize(new Dimension(400, 30));
			slayout.putConstraint(SpringLayout.NORTH, grdinputdirL, 225, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,grdinputdirL, 5, SpringLayout.WEST, configP);
			configP.add(grdinputdirL);
			grdinputdirTF.setPreferredSize(new Dimension(380, 30));
			slayout.putConstraint(SpringLayout.NORTH, grdinputdirTF, 250, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,grdinputdirTF, 20, SpringLayout.WEST, configP);
			configP.add(grdinputdirTF);
			grdinputdirTF.addActionListener(new configUpdater());
			grdinputdirTF.setToolTipText("Diretory to read geo-referenced but static data (gridded data)");
			selectGrdinputdirB.setPreferredSize(new Dimension(80, 30));
			slayout.putConstraint(SpringLayout.NORTH, selectGrdinputdirB, 250, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,selectGrdinputdirB, 405, SpringLayout.WEST, configP);
			configP.add(selectGrdinputdirB);
			selectGrdinputdirB.setEnabled(false);

			// 6) cohort input directory

	        JLabel chtinputdirL = new JLabel("Cohort (grided/dynamical) Input Directory");
			chtinputdirL.setPreferredSize(new Dimension(400, 30));
			slayout.putConstraint(SpringLayout.NORTH, chtinputdirL, 280, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,chtinputdirL, 5, SpringLayout.WEST, configP);
			configP.add(chtinputdirL);
			chtinputdirTF.setPreferredSize(new Dimension(380, 30));
			chtinputdirTF.setToolTipText("Diretory to read geo-referenced and/or dynamical data");
			slayout.putConstraint(SpringLayout.NORTH, chtinputdirTF, 305, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,chtinputdirTF, 20, SpringLayout.WEST, configP);
			configP.add(chtinputdirTF);
			chtinputdirTF.addActionListener(new configUpdater());
			selectChtinputdirB.setPreferredSize(new Dimension(80, 30));
			slayout.putConstraint(SpringLayout.NORTH, selectChtinputdirB, 305, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,selectChtinputdirB, 405, SpringLayout.WEST, configP);
			configP.add(selectChtinputdirB);
			selectChtinputdirB.setEnabled(false);
			
			// cohort id to be calibrated
	        JLabel chtidinputL = new JLabel("Cohort ID");
	        chtidinputL.setPreferredSize(new Dimension(400, 30));
			slayout.putConstraint(SpringLayout.NORTH, chtidinputL, 335, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,chtidinputL, 5, SpringLayout.WEST, configP);
			configP.add(chtidinputL);
			chtidinputTF.setPreferredSize(new Dimension(300, 30));
			chtidinputTF.setToolTipText("ID for the cohort to be calibrated/run)");
			slayout.putConstraint(SpringLayout.NORTH, chtidinputTF, 335, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,chtidinputTF, 100, SpringLayout.WEST, configP);
			configP.add(chtidinputTF);
			chtidinputTF.addActionListener(new configUpdater());
			
			//
			// 7) update the control file from configTab and thus model
			updateControlB.setPreferredSize(new Dimension(200, 30));
			slayout.putConstraint(SpringLayout.NORTH, updateControlB, 365, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, updateControlB, 100, SpringLayout.WEST, configP);
			configP.add(updateControlB);
			updateControlB.addActionListener(new controlUpdater());
			updateControlB.setToolTipText("If any of above modified, click this to re-setup GUI and model");
			updateControlB.setEnabled(false);

			// 8) module switches for TEM
			JLabel label1= new JLabel ("----------------- MODEL MODULE SWITCHES ---------------");
			label1.setPreferredSize(new Dimension(450, 30));
			slayout.putConstraint(SpringLayout.NORTH, label1, 400, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, label1, 0, SpringLayout.WEST, configP);
			configP.add(label1);

			JLabel envmodL= new JLabel ("Env-module");
			envmodL.setPreferredSize(new Dimension(80, 25));
			slayout.putConstraint(SpringLayout.NORTH, envmodL, 430, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, envmodL, 10, SpringLayout.WEST, configP);
			configP.add(envmodL);
			String envmodS[] = new String[2];
			envmodS[0] = "Off";
			envmodS[1] = "On";
			JPanel envmodP = getRBPanel(envmodjbg, 2, 200, 30, envmodjrb, envmodS);
			envmodP.setPreferredSize(new Dimension(200,30));
			slayout.putConstraint(SpringLayout.NORTH, envmodP, 430,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, envmodP, 85,SpringLayout.WEST, configP);
			configP.add(envmodP);
			envmodjrb[0].addActionListener(ProcessSwitcher);
			envmodjrb[1].addActionListener(ProcessSwitcher);
			envmodjrb[0].setEnabled(false);
			envmodjrb[1].setEnabled(false);
			envmodP.setToolTipText("(Bio)physical (hydrological and thermal) module, default is ON");

			JLabel bgcmodL= new JLabel ("Bgc-module");
			bgcmodL.setPreferredSize(new Dimension(80, 25));
			slayout.putConstraint(SpringLayout.NORTH, bgcmodL, 460,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, bgcmodL, 10 ,SpringLayout.WEST, configP);
			configP.add(bgcmodL);
			String bgcmodS[] = new String[2];
			bgcmodS[0] = "Off";
			bgcmodS[1] = "On";
			JPanel bgcmodP = getRBPanel(bgcmodjbg, 2, 150, 30, bgcmodjrb, bgcmodS);
			bgcmodP.setPreferredSize(new Dimension(150,30));
			slayout.putConstraint(SpringLayout.NORTH, bgcmodP, 460,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, bgcmodP, 85,SpringLayout.WEST, configP);
			configP.add(bgcmodP);
			bgcmodjrb[0].addActionListener(ProcessSwitcher);
			bgcmodjrb[1].addActionListener(ProcessSwitcher);
			bgcmodjrb[0].setEnabled(false);
			bgcmodjrb[1].setEnabled(false);
			bgcmodP.setToolTipText("Biogeochemical (C and/or N) module, default is OFF");

			JLabel nfeedL= new JLabel ("C-N coupled");
			nfeedL.setPreferredSize(new Dimension(100, 25));
			slayout.putConstraint(SpringLayout.NORTH, nfeedL, 485, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, nfeedL, 30, SpringLayout.WEST, configP);
			configP.add(nfeedL);
			String nfeedS[] = new String[2];
			nfeedS[0] = "No";
			nfeedS[1] = "Yes";
			JPanel nfeedP = getRBPanel(nfeedjbg, 2, 150, 30, nfeedjrb, nfeedS);
			nfeedP.setPreferredSize(new Dimension(150,30));
			slayout.putConstraint(SpringLayout.NORTH, nfeedP, 485, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,nfeedP, 140, SpringLayout.WEST, configP);
			configP.add(nfeedP);
			nfeedjrb[0].addActionListener(ProcessSwitcher);
			nfeedjrb[1].addActionListener(ProcessSwitcher);
			nfeedjrb[0].setEnabled(false);
			nfeedjrb[1].setEnabled(false);
			nfeedP.setToolTipText("N cycle module to regulate C cycle (N feedback), default is OFF");

			JLabel avlnL= new JLabel ("Inorg. N I/O Flag");
			avlnL.setPreferredSize(new Dimension(120, 25));
			slayout.putConstraint(SpringLayout.NORTH, avlnL, 510, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, avlnL, 60, SpringLayout.WEST, configP);
			configP.add(avlnL);
			String avlnS[] = new String[2];
			avlnS[0] = "No";
			avlnS[1] = "Yes";
			JPanel avlnP = getRBPanel(avlnjbg, 2, 150, 30, avlnjrb, nfeedS);
			avlnP.setPreferredSize(new Dimension(150,30));
			slayout.putConstraint(SpringLayout.NORTH, avlnP, 510, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,avlnP, 160, SpringLayout.WEST, configP);
			configP.add(avlnP);
			avlnjrb[0].addActionListener(ProcessSwitcher);
			avlnjrb[1].addActionListener(ProcessSwitcher);
			avlnjrb[0].setEnabled(false);
			avlnjrb[1].setEnabled(false);
			avlnP.setToolTipText("flag for setting mineral-N balance (I/O) method, default is by budget estimation");

			JLabel baselineL= new JLabel ("Org. N I/O Flag");
			baselineL.setPreferredSize(new Dimension(120, 25));
			slayout.putConstraint(SpringLayout.NORTH, baselineL, 535,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, baselineL, 60 ,SpringLayout.WEST, configP);
			configP.add(baselineL);
			String baselineS[] = new String[2];
			baselineS[0] = "No";
			baselineS[1] = "Yes";
			JPanel baselineP = getRBPanel(baselinejbg, 2, 150, 30, baselinejrb, nfeedS);
			baselineP.setPreferredSize(new Dimension(150,30));
			slayout.putConstraint(SpringLayout.NORTH, baselineP, 535, SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST,baselineP, 160,SpringLayout.WEST, configP);
			configP.add(baselineP);
			baselinejrb[0].addActionListener(ProcessSwitcher);
			baselinejrb[1].addActionListener(ProcessSwitcher);
			baselinejrb[0].setEnabled(false);
			baselinejrb[1].setEnabled(false);
			baselineP.setToolTipText("(baseline)flag for setting soil organic-N balance method, default is by retaining static SOM C/N");

			//
			JLabel dslmodL= new JLabel ("Dsl-module");
			dslmodL.setPreferredSize(new Dimension(80, 25));
			slayout.putConstraint(SpringLayout.NORTH, dslmodL, 565,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, dslmodL, 10 ,SpringLayout.WEST, configP);
			configP.add(dslmodL);
			String dslmodS[] = new String[2];
			dslmodS[0] = "Off";
			dslmodS[1] = "On";
			JPanel dslmodP = getRBPanel(dslmodjbg, 2, 150, 30, dslmodjrb, dslmodS);
			dslmodP.setPreferredSize(new Dimension(150,30));
			slayout.putConstraint(SpringLayout.NORTH, dslmodP, 565,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, dslmodP, 85,SpringLayout.WEST, configP);
			configP.add(dslmodP);
			dslmodjrb[0].addActionListener(ProcessSwitcher);
			dslmodjrb[1].addActionListener(ProcessSwitcher);
			dslmodjrb[0].setEnabled(false);
			dslmodjrb[1].setEnabled(false);
			dslmodP.setToolTipText("switch for dynamical organic soil layer module, otherwise static soil column is used");

			//
			JLabel dvmmodL= new JLabel ("Dvm-module");
			dvmmodL.setPreferredSize(new Dimension(90, 25));
			slayout.putConstraint(SpringLayout.NORTH, dvmmodL, 595,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, dvmmodL, 10 ,SpringLayout.WEST, configP);
			configP.add(dvmmodL);
			String dvmmodS[] = new String[2];
			dvmmodS[0] = "Off";
			dvmmodS[1] = "On";
			JPanel dvmmodP = getRBPanel(dvmmodjbg, 2, 150, 30, dvmmodjrb, dvmmodS);
			dvmmodP.setPreferredSize(new Dimension(150,30));
			slayout.putConstraint(SpringLayout.NORTH, dvmmodP, 595,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, dvmmodP, 85,SpringLayout.WEST, configP);
			configP.add(dvmmodP);
			dvmmodjrb[0].addActionListener(ProcessSwitcher);
			dvmmodjrb[1].addActionListener(ProcessSwitcher);
			dvmmodjrb[0].setEnabled(false);
			dvmmodjrb[1].setEnabled(false);
			dvmmodP.setToolTipText("switch for dynamical vegetation module, default is OFF");

			JLabel updatelaiL= new JLabel ("LAI dynamics");
			updatelaiL.setPreferredSize(new Dimension(120, 25));
			slayout.putConstraint(SpringLayout.NORTH, updatelaiL, 620,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, updatelaiL, 50 ,SpringLayout.WEST, configP);
			configP.add(updatelaiL);
			String updatelaiS[] = new String[2];
			updatelaiS[0] = "No";
			updatelaiS[1] = "Yes";
			JPanel updatelaiP = getRBPanel(updatelaijbg, 2, 150, 30, updatelaijrb, updatelaiS);
			updatelaiP.setPreferredSize(new Dimension(150,30));
			slayout.putConstraint(SpringLayout.NORTH, updatelaiP, 620,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, updatelaiP, 160,SpringLayout.WEST, configP);
			configP.add(updatelaiP);
			updatelaijrb[0].addActionListener(ProcessSwitcher);
			updatelaijrb[1].addActionListener(ProcessSwitcher);
			updatelaijrb[0].setEnabled(false);
			updatelaijrb[1].setEnabled(false);
			updatelaiP.setToolTipText("static or dynamical LAI");
			updatelaijrb[0].setToolTipText("static LAI is set as monthly envlai[] input in 'cmt_dimvegetation.txt'!");
			updatelaijrb[1].setToolTipText("LAI is changing with foliage C associated with vegetation BGC");		

			//
			JLabel firemodL= new JLabel ("Fire-module");
			firemodL.setPreferredSize(new Dimension(80, 25));
			slayout.putConstraint(SpringLayout.NORTH, firemodL, 650,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, firemodL, 10 ,SpringLayout.WEST, configP);
			configP.add(firemodL);
			String firemodS[] = new String[2];
			firemodS[0] = "Off";
			firemodS[1] = "On";
			JPanel firemodP = getRBPanel(firemodjbg, 2, 150, 30, firemodjrb, firemodS);
			firemodP.setPreferredSize(new Dimension(150,30));
			slayout.putConstraint(SpringLayout.NORTH, firemodP, 650,SpringLayout.NORTH, configP);
			slayout.putConstraint(SpringLayout.WEST, firemodP, 85,SpringLayout.WEST, configP);
			configP.add(firemodP);
			firemodjrb[0].addActionListener(ProcessSwitcher);
			firemodjrb[1].addActionListener(ProcessSwitcher);
			firemodjrb[0].setEnabled(false);
			firemodjrb[1].setEnabled(false);
			firemodP.setToolTipText("switch for wild fire disturbance module");

        	// End of configurer Panel //////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////////////////////////////////////

           // Begging of the Data Table Panel /////////////////////////////////////////////////////////////////////

        	JPanel datalogP = new JPanel();
			datalogP.setLayout(slayout);

			// 1) calibatible bgc parameter file
			JLabel calparL = new JLabel("Initial BGC Parameter Values:");
			calparL.setPreferredSize(new Dimension(400, 30));
			slayout.putConstraint(SpringLayout.NORTH, calparL, 10, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,calparL, 5, SpringLayout.WEST, datalogP);
			datalogP.add(calparL);
			calparTF.setPreferredSize(new Dimension(380, 30));
			slayout.putConstraint(SpringLayout.NORTH, calparTF, 35, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,calparTF, 20, SpringLayout.WEST, datalogP);
			datalogP.add(calparTF);
			calparTF.setToolTipText("file containing the initial estimation of BGC parameters to be calibrated");

			selectInitparfileB.setPreferredSize(new Dimension(80, 30));
			slayout.putConstraint(SpringLayout.NORTH, selectInitparfileB, 35, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,selectInitparfileB, 405, SpringLayout.WEST, datalogP);
			datalogP.add(selectInitparfileB);
		    selectInitparfileB.addActionListener(new InitCaliparSelector());

			// 2) calibrated bgc targetted state variable file
			JLabel calbgcL = new JLabel("Targetted BGC State/Flux Data:");
			calbgcL.setPreferredSize(new Dimension(400, 30));
			slayout.putConstraint(SpringLayout.NORTH, calbgcL, 70, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,calbgcL, 5, SpringLayout.WEST, datalogP);
			datalogP.add(calbgcL);
			calbgcTF.setPreferredSize(new Dimension(380, 30));
			slayout.putConstraint(SpringLayout.NORTH, calbgcTF, 95, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,calbgcTF, 20, SpringLayout.WEST, datalogP);
			datalogP.add(calbgcTF);
			calbgcTF.setToolTipText("file containing the targetted veg/soil BGC variables for calibrating");

			selectCalibgcfileB.setPreferredSize(new Dimension(80, 30));
			slayout.putConstraint(SpringLayout.NORTH, selectCalibgcfileB, 95, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,selectCalibgcfileB, 405,SpringLayout.WEST, datalogP);
			datalogP.add(selectCalibgcfileB);
		    selectCalibgcfileB.addActionListener(new CalibgcTargetSelector());

		    // 3) community type code
		    JLabel cmtL = new JLabel("Community Code - 'CMT??' followed by space and //comments):");
			cmtL.setPreferredSize(new Dimension(500, 30));
			slayout.putConstraint(SpringLayout.NORTH, cmtL, 130, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST, cmtL, 5, SpringLayout.WEST, datalogP);
			datalogP.add(cmtL);
			cmtcodeTF.setPreferredSize(new Dimension(500, 30));
			slayout.putConstraint(SpringLayout.NORTH, cmtcodeTF, 155, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,cmtcodeTF, 20, SpringLayout.WEST, datalogP);
			datalogP.add(cmtcodeTF);
			cmtcodeTF.setEnabled(false);

			// 4) PFT type code (name only)
		    JLabel pftcodeL = new JLabel("Community PFT names - for information only");
			pftcodeL.setPreferredSize(new Dimension(500, 30));
			slayout.putConstraint(SpringLayout.NORTH, pftcodeL, 180, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST, pftcodeL, 5, SpringLayout.WEST, datalogP);
			datalogP.add(pftcodeL);
			pftcodeTF.setPreferredSize(new Dimension(500, 30));
			slayout.putConstraint(SpringLayout.NORTH, pftcodeTF, 205, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,pftcodeTF, 20, SpringLayout.WEST, datalogP);
			datalogP.add(pftcodeTF);
			pftcodeTF.setEnabled(false);

			// 5) tabbed table for holding data reading from above 3 files
			JLabel bgctableL = new JLabel(" ---- Parameters/States to be Calibrated" +
					"----------------------------------- ");
			bgctableL.setPreferredSize(new Dimension(500, 30));
			slayout.putConstraint(SpringLayout.NORTH, bgctableL, 240, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST, bgctableL, 5, SpringLayout.WEST, datalogP);
			datalogP.add(bgctableL);

			String[] ColumnName = {"Variable Name", "PFT 0", "PFT 1", "PFT 2", "PFT 3", "PFT 4",
	        		                                "PFT 5", "PFT 6", "PFT 7", "PFT 8", "PFT 9"};
			JTabbedPane tableTP = new JTabbedPane();
			tableTP.setPreferredSize(new Dimension(500, 400));
			slayout.putConstraint(SpringLayout.NORTH, tableTP, 280, SpringLayout.NORTH, datalogP);
			slayout.putConstraint(SpringLayout.WEST,tableTP, 5, SpringLayout.WEST, datalogP);
			datalogP.add(tableTP);

	        //
			String[] calparName ={"CMAX", "NMAX", "CFALL-leaf", "CFALL-stem", "CFALL-root",
	        		           "NFALL-leaf","NFALL-stem","NFALL-root","KRA","KRB-leaf","KRB-stem","KRB-root","FRG",
	        		           " ", "MICBNUP", "KDCMOSSC", "KDCRAWC", "KDCSOMA", "KDCSOMPR", "KDCSOMCR"};

	        int rows1 = calparName.length;
	        int cols1 = ColumnName.length;
	        String[][] calValue = new String[rows1][cols1];
	        for(int ir=0; ir<rows1; ir++){
	        	calValue[ir][0] = calparName[ir];
	        	for(int ic =1; ic<cols1; ic++){
	        		calValue[ir][ic] =" ";
	        	}
	        }
	        calparTB = new JTable(calValue, ColumnName);
	        calparTB.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
	        calparTB.getColumnModel().getColumn(0).setPreferredWidth(100);
			JScrollPane calparSP = new JScrollPane(calparTB);
			calparSP.setPreferredSize(new Dimension(100, 100));
			tableTP.add("Parameters to calibrate", calparSP);

			//
	        String[] targetsName ={"GPP", "INNPP", "NPP", "NUPTAKE"," ",
                    "VEGC-leaf","VEGC-stem","VEGC-root",
                    "VEGN-leaf","VEGN-stem","VEGN-root",
                    " ", "C-dmoss","SOMC-fib","SOMC-hum","SOMC-min","SOILN","AVLN"};
	        int rows2 = targetsName.length;
	        int cols2 = ColumnName.length;
	        String[][] targetValue = new String[rows2][cols2];
	        for(int ir=0; ir<rows2; ir++){
	        	targetValue[ir][0] = targetsName[ir];
	        	for(int ic =1; ic<cols2; ic++){
	        		targetValue[ir][ic] =" ";
	        	}
	        }
	        targetTB = new JTable(targetValue, ColumnName);
			targetTB.getModel().addTableModelListener(tabvalueChanger);
	        targetTB.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
	        targetTB.getColumnModel().getColumn(0).setPreferredWidth(100);

			JScrollPane targetSP = new JScrollPane(targetTB);
			targetSP.setPreferredSize(new Dimension(100, 100));
			tableTP.add("Targetted States/Fluxes", targetSP);

			//
	        String[] initstateName ={"VEGC-leaf","VEGC-stem","VEGC-root",
	        	       "VEGN-leaf","VEGN-stem","VEGN-root","DEADC","DEADN",
	        	       " ", "THICK-dmoss","THICK-fib", "THICK-hum", 
	        	       "C-dmoss","SOMC-fib","SOMC-hum","SOMC-min","SOILN","AVLN"};
	        int rows3 = initstateName.length;
	        int cols3 = ColumnName.length;
	        String[][] initstateValue = new String[rows3][cols3];
	        for(int ir=0; ir<rows3; ir++){
	        	initstateValue[ir][0] = initstateName[ir];
	        	for(int ic =1; ic<cols3; ic++){
	        		initstateValue[ir][ic] =" ";
	        	}
	        }
	        stateTB = new JTable(initstateValue, ColumnName);
	        stateTB.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
	        stateTB.getColumnModel().getColumn(0).setPreferredWidth(100);
			JScrollPane stateSP = new JScrollPane(stateTB);
			stateSP.setPreferredSize(new Dimension(100, 100));
			tableTP.add("Initial States", stateSP);
			

		// End of Data Table Panel //////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		// Begging of the Calibrator Pannel /////////////////////////////////////////////////////////////////////

			JPanel caliP = new JPanel();
			caliP.setLayout(slayout);


			// 2) Buttons for Run Model
			JLabel label2= new JLabel ("------------- MODEL RUN CONTROLS --------------------------------");
			label2.setPreferredSize(new Dimension(540, 30));
			slayout.putConstraint(SpringLayout.NORTH, label2, 5, SpringLayout.NORTH, caliP);
			slayout.putConstraint(SpringLayout.WEST, label2, 0, SpringLayout.WEST, caliP);
			caliP.add(label2);

			runmodeB.setPreferredSize(new Dimension(100, 35));
			slayout.putConstraint(SpringLayout.NORTH, runmodeB, 40,SpringLayout.NORTH, caliP);
			slayout.putConstraint(SpringLayout.WEST,runmodeB, 50,SpringLayout.WEST, caliP);
			caliP.add(runmodeB);
		    runmodeB.addActionListener(new RunMode());
		    runmodeB.setEnabled(false);
			runmodeB.setToolTipText("Calibration mode OR Testing mode, by flipping the button");

			setupB.setPreferredSize(new Dimension(100, 35));
			slayout.putConstraint(SpringLayout.NORTH, setupB, 40,SpringLayout.NORTH, caliP);
			slayout.putConstraint(SpringLayout.WEST,setupB, 180,SpringLayout.WEST, caliP);
			caliP.add(setupB);
		    setupB.addActionListener(new Setup());
		    setupB.setEnabled(false);
			setupB.setToolTipText("By clicking it, will update model switches and parameters only");

			resetupB.setPreferredSize(new Dimension(120, 35));
			slayout.putConstraint(SpringLayout.NORTH, resetupB, 40,SpringLayout.NORTH, caliP);
			slayout.putConstraint(SpringLayout.WEST,resetupB, 310,SpringLayout.WEST, caliP);
			caliP.add(resetupB);
		    resetupB.addActionListener(new Resetup());
		    resetupB.setEnabled(false);
			resetupB.setToolTipText("By clicking it, will re-setup model from very begining");

			startpauseB.setPreferredSize(new Dimension(70, 40));
			slayout.putConstraint(SpringLayout.NORTH, startpauseB, 80,SpringLayout.NORTH, caliP);
			slayout.putConstraint(SpringLayout.WEST,startpauseB, 150,SpringLayout.WEST, caliP);
			caliP.add(startpauseB);
		    startpauseB.addActionListener(new StartPause());
		    startpauseB.setEnabled(false);
			startpauseB.setToolTipText("start model run or pause it - by default model will pause first five 100 yrs and then every 500 yrs");

		    exitB.setPreferredSize(new Dimension(70, 40));
			slayout.putConstraint(SpringLayout.NORTH, exitB, 80,SpringLayout.NORTH, caliP);
			slayout.putConstraint(SpringLayout.WEST,exitB, 250,SpringLayout.WEST, caliP);
			caliP.add(exitB);
		    exitB.addActionListener(new Exit());
		    exitB.setEnabled(true);
			exitB.setToolTipText("By clicking it, the GUI will turn off and quit!");

			// 3) Input Box for the Parameters to be calibrated
			JLabel label3= new JLabel ("------------- PARAMETERS for VEGETATION " +
					"---------------------------------");
				label3.setPreferredSize(new Dimension(540, 30));
				slayout.putConstraint(SpringLayout.NORTH, label3, 125,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST, label3, 0 ,SpringLayout.WEST, caliP);
				caliP.add(label3);

			JLabel pftL= new JLabel ("Please Select PFT index (0 - 9)");
				pftL.setPreferredSize(new Dimension(250, 30));
				slayout.putConstraint(SpringLayout.NORTH, pftL, 150,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST, pftL, 30 ,SpringLayout.WEST, caliP);
				caliP.add(pftL);

				Vector<Integer> pftindxV = new Vector<Integer>();
				for (int i=0; i<Configurer.I_PFT.length; i++) {
					pftindxV.add(Integer.valueOf(Configurer.I_PFT[i]));
				}
				pickpftCB = new JComboBox(pftindxV);
				pickpftCB.setPreferredSize(new Dimension(90, 25));
				slayout.putConstraint(SpringLayout.NORTH, pickpftCB, 155,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,pickpftCB, 250,SpringLayout.WEST, caliP);
				caliP.add(pickpftCB);
				pickpftCB.setSelectedIndex(0);
				pickpftCB.addActionListener(new pftSelector());
				pickpftCB.setEnabled(false);
				pickpftCB.setToolTipText("By scrolling and picking up the PFT index to calibrate it ");

			JPanel cmaxP = cmaxChanger.getPanel();
				cmaxP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, cmaxP, 175,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,cmaxP, 5,SpringLayout.WEST, caliP);
				caliP.add(cmaxP);
			    cmaxChanger.pmmTF.addActionListener(ParameterChanged);
			    cmaxChanger.setEnabled(false);

			JPanel nmaxP = nmaxChanger.getPanel();
				nmaxP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, nmaxP, 175,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,nmaxP,  355,SpringLayout.WEST, caliP);
				caliP.add(nmaxP);
			    nmaxChanger.pmmTF.addActionListener(ParameterChanged);
			    nmaxChanger.setEnabled(false);

			JPanel kraP = kraChanger.getPanel();
				kraP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, kraP, 225,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,kraP,  5,SpringLayout.WEST, caliP);
				caliP.add(kraP);
			    kraChanger.pmmTF.addActionListener(ParameterChanged);
			    kraChanger.setEnabled(false);
			    
			JPanel frgP = frgChanger.getPanel();
				frgP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, frgP, 225,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST, frgP, 180,SpringLayout.WEST, caliP);
				caliP.add(frgP);
			    frgChanger.pmmTF.addActionListener(ParameterChanged);
			    frgChanger.setEnabled(false);
			    
			    
			JPanel krblP = krblChanger.getPanel();
				krblP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, krblP, 275,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,krblP, 5,SpringLayout.WEST, caliP);
				caliP.add(krblP);
			    krblChanger.pmmTF.addActionListener(ParameterChanged);
			    krblChanger.setEnabled(false);

			JPanel krbsP = krbsChanger.getPanel();
				krbsP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, krbsP, 325,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,krbsP, 5,SpringLayout.WEST, caliP);
				caliP.add(krbsP);
			    krbsChanger.pmmTF.addActionListener(ParameterChanged);
			    krbsChanger.setEnabled(false);

			JPanel krbrP = krbrChanger.getPanel();
				krbrP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, krbrP, 375,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,krbrP, 5,SpringLayout.WEST, caliP);
				caliP.add(krbrP);
			    krbrChanger.pmmTF.addActionListener(ParameterChanged);
			    krbrChanger.setEnabled(false);

			JPanel cfalllP = cfalllChanger.getPanel();
				cfalllP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, cfalllP, 275,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,cfalllP, 180,SpringLayout.WEST, caliP);
				caliP.add(cfalllP);
			    cfalllChanger.pmmTF.addActionListener(ParameterChanged);
			    cfalllChanger.setEnabled(false);

			JPanel cfallsP = cfallsChanger.getPanel();
				cfallsP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, cfallsP, 325,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,cfallsP, 180,SpringLayout.WEST, caliP);
				caliP.add(cfallsP);
			    cfallsChanger.pmmTF.addActionListener(ParameterChanged);
			    cfallsChanger.setEnabled(false);

			JPanel cfallrP = cfallrChanger.getPanel();
				cfallrP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, cfallrP, 375,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,cfallrP, 180,SpringLayout.WEST, caliP);
				caliP.add(cfallrP);
			    cfallrChanger.pmmTF.addActionListener(ParameterChanged);
			    cfallrChanger.setEnabled(false);

			JPanel nfalllP = nfalllChanger.getPanel();
				nfalllP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, nfalllP, 275,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,nfalllP, 355,SpringLayout.WEST, caliP);
				caliP.add(nfalllP);
			    nfalllChanger.pmmTF.addActionListener(ParameterChanged);
			    nfalllChanger.setEnabled(false);

			JPanel nfallsP = nfallsChanger.getPanel();
				nfallsP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, nfallsP, 325,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,nfallsP, 355,SpringLayout.WEST, caliP);
				caliP.add(nfallsP);
			    nfallsChanger.pmmTF.addActionListener(ParameterChanged);
			    nfallsChanger.setEnabled(false);

			JPanel nfallrP = nfallrChanger.getPanel();
				nfallrP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, nfallrP, 375,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,nfallrP, 355,SpringLayout.WEST, caliP);
				caliP.add(nfallrP);
			    nfallrChanger.pmmTF.addActionListener(ParameterChanged);
			    nfallrChanger.setEnabled(false);

			JLabel label5= new JLabel ("------------- PARAMETERS for GROUND/SOIL " +
					"----------------------------------");
				label5.setPreferredSize(new Dimension(540, 30));
				slayout.putConstraint(SpringLayout.NORTH, label5, 440,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST, label5, 0 ,SpringLayout.WEST, caliP);
				caliP.add(label5);

			JPanel kdcmossP = kdcmosscChanger.getPanel();
				kdcmossP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, kdcmossP, 470,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,kdcmossP, 5,SpringLayout.WEST, caliP);
				caliP.add(kdcmossP);
			    kdcmosscChanger.pmmTF.addActionListener(ParameterChanged);
			    kdcmosscChanger.setEnabled(false);

			JPanel kdcfibP = kdcrawcChanger.getPanel();
				kdcfibP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, kdcfibP, 470,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,kdcfibP, 180,SpringLayout.WEST, caliP);
				caliP.add(kdcfibP);
			    kdcrawcChanger.pmmTF.addActionListener(ParameterChanged);
			    kdcrawcChanger.setEnabled(false);
			    
			JPanel kdcsomaP = kdcsomaChanger.getPanel();
				kdcsomaP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, kdcsomaP, 520,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,kdcsomaP, 5,SpringLayout.WEST, caliP);
				caliP.add(kdcsomaP);
			    kdcsomaChanger.pmmTF.addActionListener(ParameterChanged);
			    kdcsomaChanger.setEnabled(false);

			JPanel kdcsomprP = kdcsomprChanger.getPanel();
				kdcsomprP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, kdcsomprP, 570,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,kdcsomprP, 5,SpringLayout.WEST, caliP);
				caliP.add(kdcsomprP);
			    kdcsomprChanger.pmmTF.addActionListener(ParameterChanged);
			    kdcsomprChanger.setEnabled(false);

			JPanel kdcsomcrP = kdcsomcrChanger.getPanel();
				kdcsomcrP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, kdcsomcrP, 570,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,kdcsomcrP, 180,SpringLayout.WEST, caliP);
				caliP.add(kdcsomcrP);
			    kdcsomcrChanger.pmmTF.addActionListener(ParameterChanged);
			    kdcsomcrChanger.setEnabled(false);

			JPanel micbnupP = micbnupChanger.getPanel();
				micbnupP.setPreferredSize(new Dimension(170, 50));
				slayout.putConstraint(SpringLayout.NORTH, micbnupP, 520, SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST, micbnupP, 355, SpringLayout.WEST, caliP);
				caliP.add(micbnupP);
			    micbnupChanger.pmmTF.addActionListener(ParameterChanged);
			    micbnupChanger.setEnabled(false);

			// 5) Buttons for Operating the Calibrated Parameters
			JLabel label6= new JLabel ("------------- PARAMETER OPERATIONS " +
					"-----------------------------");
				label6.setPreferredSize(new Dimension(540, 30));
				slayout.putConstraint(SpringLayout.NORTH, label6, 630, SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST, label6, 0, SpringLayout.WEST, caliP);
				caliP.add(label6);

				parresetB.setPreferredSize(new Dimension(120, 30));
				slayout.putConstraint(SpringLayout.NORTH, parresetB, 660, SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,parresetB, 60, SpringLayout.WEST, caliP);
				caliP.add(parresetB);
			    parresetB.addActionListener(new ParameterResetter());
			    parresetB.setEnabled(false);
				parresetB.setToolTipText("By clicking it, parameters will be re-read from the initial calpar file");

				parrestoreB.setPreferredSize(new Dimension(120, 30));
				slayout.putConstraint(SpringLayout.NORTH, parrestoreB, 660,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,parrestoreB, 210,SpringLayout.WEST, caliP);
				caliP.add(parrestoreB);
			    parrestoreB.addActionListener(new ParameterRestorer());
			    parrestoreB.setEnabled(false);
				parrestoreB.setToolTipText("By clicking it, parameters on Changers will be restored to the prevously stored values");

				paroutputB.setPreferredSize(new Dimension(120, 30));
				slayout.putConstraint(SpringLayout.NORTH, paroutputB, 660,SpringLayout.NORTH, caliP);
				slayout.putConstraint(SpringLayout.WEST,paroutputB, 360,SpringLayout.WEST, caliP);
				caliP.add(paroutputB);
			    paroutputB.addActionListener(new ParameterOutputer());
			    paroutputB.setEnabled(false);
				paroutputB.setToolTipText("By clicking it, parameters will be saved into file: 'calibration_outpar.txt', which can be appended into 'cmt_calparbgc.txt' for application! ");

    // End of Calibrator Panel //////////////////////////////////////////////////////////////////////////////

			controlTP.add("Configurer", configP);
			controlTP.add("Datalogger", datalogP);
			controlTP.add("Calibrator", caliP);

		    fcontrol.add(controlTP, BorderLayout.CENTER);

		    fcontrol.setLocation(1,150);
		    fcontrol.setPreferredSize(new Dimension(600, 900));
		    fcontrol.setSize(540, 760);
		    fcontrol.setVisible(true);
		}catch (Exception e){
		   System.out.println(e.getMessage());
		} finally {
			//System.out.println("In final");
		}
	}

	private JPanel getRBPanel(ButtonGroup jbg, int rbnum, int bglength, int rbheight,
			JRadioButton jrb[], String rb[]){
		JPanel rbP = new JPanel();
		SpringLayout slayout = new SpringLayout();
		rbP.setLayout(slayout);
		int j=0;
		int ilength=0;
		for(int i= 0; i<rbnum;i++){
			jrb[i] = new JRadioButton(rb[i]);
			int rblength = Math.max(60, rb[i].length()*10);

			ilength+=rblength+10;
			if(ilength>bglength){
				j+=1;
				ilength=0;
			}

			jrb[i].setPreferredSize(new Dimension(rblength, rbheight));
			slayout.putConstraint(SpringLayout.NORTH, jrb[i], j,SpringLayout.NORTH, rbP);
			slayout.putConstraint(SpringLayout.WEST, jrb[i], ilength-rblength,SpringLayout.WEST, rbP);
			rbP.add(jrb[i]);
			jbg.add(jrb[i]);

		}
		jrb[0].setSelected(true);

		return rbP;
	};


//--------------Operations on Configure Tab of Control Panel --------------------------------------
	//
	private ActionListener ProcessSwitcher = new ActionListener (){

		public void actionPerformed(ActionEvent e) {
			startpauseB.setEnabled(false);    //any selection will (re-)setup model run before run
			resetupB.setEnabled(true);
			setupB.setEnabled(true);
			
			if (bgcmodjrb[0].isSelected()) {
				nfeedjrb[0].setSelected(true);
				nfeedjrb[1].setSelected(false);
				nfeedjrb[0].setEnabled(false);
				nfeedjrb[1].setEnabled(false);
			} else if (bgcmodjrb[1].isSelected()) {
				nfeedjrb[0].setEnabled(true);
				nfeedjrb[1].setEnabled(true);
			}

			if (nfeedjrb[0].isSelected()) {
				avlnjrb[0].setSelected(true);
				avlnjrb[1].setSelected(false);
				avlnjrb[0].setEnabled(false);
				avlnjrb[1].setEnabled(false);

				baselinejrb[0].setSelected(true);
				baselinejrb[1].setSelected(false);
				baselinejrb[0].setEnabled(false);
				baselinejrb[1].setEnabled(false);
			} else if (nfeedjrb[1].isSelected()) {
				avlnjrb[0].setEnabled(true);
				avlnjrb[1].setEnabled(true);
				baselinejrb[0].setEnabled(true);
				baselinejrb[1].setEnabled(true);
			}
			
			if (dvmmodjrb[0].isSelected() || (!dvmmodjrb[1].isEnabled())) {
				updatelaijrb[0].setSelected(true);
				updatelaijrb[1].setSelected(false);
				updatelaijrb[0].setEnabled(false);
				updatelaijrb[1].setEnabled(false);
			} else if (dvmmodjrb[1].isEnabled()){
				updatelaijrb[0].setEnabled(true);
				updatelaijrb[1].setEnabled(true);
			}
							
		}

	};

	private TableModelListener tabvalueChanger = new TableModelListener() {
		public void tableChanged(TableModelEvent e) {
		    startpauseB.setEnabled(false);    //any selection will re-set model run
			resetupB.setEnabled(true);
			setupB.setEnabled(false);

		}

	};

	private ActionListener ParameterChanged = new ActionListener (){

		public void actionPerformed(ActionEvent e) {

			startpauseB.setEnabled(false);    //any modification on parameter value(s) will re-set model run
			resetupB.setEnabled(true);
			setupB.setEnabled(true);

			//store parameters to old values
			 cmaxChanger.storeOldValue();
			 nmaxChanger.storeOldValue();
			 cfalllChanger.storeOldValue();
			 cfallsChanger.storeOldValue();
			 cfallrChanger.storeOldValue();
			 nfalllChanger.storeOldValue();
			 nfallsChanger.storeOldValue();
			 nfallrChanger.storeOldValue();
			 kraChanger.storeOldValue();
			 krblChanger.storeOldValue();
			 krbsChanger.storeOldValue();
			 krbrChanger.storeOldValue();
			 frgChanger.storeOldValue();

			 micbnupChanger.storeOldValue();
			 kdcmosscChanger.storeOldValue();
			 kdcrawcChanger.storeOldValue();
			 kdcsomaChanger.storeOldValue();
			 kdcsomprChanger.storeOldValue();
			 kdcsomcrChanger.storeOldValue();

		}

	};

	public class ControlSelector implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {
			//open file chooser
			String defaultdir = "config/";
			JFileChooser fc = new JFileChooser(defaultdir);
			int returnVal =fc.showOpenDialog(selectControlfileB);
			if (returnVal == JFileChooser.APPROVE_OPTION) {
	            File file = fc.getSelectedFile();

	            //set-up control file in the configurer Tab of Control Panel
	            controlfileTF.setText(file.getPath());
	            config.controlfile = controlfileTF.getText();
	            readconfig();

	            //
	            enableGUI();
	            
		    	//initializing TEM eqrunner
		    	runnerinit();
	            
	        	getDefaultvarparFromTEM();
	            
	            // set the pick-pft list and default index
	            pickpftCB.setSelectedIndex(Caliber.ipft); // Caliber.ipft has already set 

			}
		}
	};

		private void readconfig() {
		    String status ="";
		    try {
			    status ="reading model control file";
			    File ctrlF = new File(config.controlfile);
			    if(!ctrlF.exists()){
			    	JOptionPane.showMessageDialog(fcontrol, status+" not exist");
			    } else {
	
			    	//reading data from file
			    	BufferedReader input =  new BufferedReader(new FileReader(config.controlfile));
	
			    	String dummy="";
	
			    	dummy = input.readLine();
			    	dummy = dummy.split(" /*", 2)[0];
			    	config.casename = dummy.trim();
			    	casenameTF.setText(config.casename);
	
			    	dummy = input.readLine();
			    	dummy = dummy.split(" /*", 2)[0];
			    	config.configdir = dummy.trim();
			    	configdirTF.setText(config.configdir);
	
			    	dummy = input.readLine();
			    	dummy = dummy.split(" /*", 2)[0];
			    	config.outputdir = dummy.trim();
			    	outputdirTF.setText(config.outputdir);
	
			    	dummy = input.readLine();
			    	dummy = dummy.split(" /*", 2)[0];
			    	config.reginputdir = dummy.trim();
			    	reginputdirTF.setText(config.reginputdir);
	
			    	dummy = input.readLine();
			    	dummy = dummy.split(" /*", 2)[0];
			    	config.grdinputdir = dummy.trim();
			    	grdinputdirTF.setText(config.grdinputdir);
	
			    	dummy = input.readLine();
			    	dummy = dummy.split(" /*", 2)[0];
			    	config.chtinputdir = dummy.trim();
			    	chtinputdirTF.setText(config.chtinputdir);
	
			    	dummy = input.readLine();
			    	dummy = dummy.split(" /*", 2)[0];
			    	chtidinputTF.setText(dummy.trim());
			    	config.chtidinput = Integer.valueOf((String)chtidinputTF.getText());
			    	
			    	input.close();
	
			    }
	
		    } catch (Exception e){
		    	JOptionPane.showMessageDialog(fcontrol, status+" failed");
		    }
	
		};

		// enable GUI
		private void enableGUI() {
			try {

	            //set-up the model options block of Calibration Panel

				envmodjrb[0].setEnabled(true);
				envmodjrb[1].setEnabled(true);
				envmodjrb[1].doClick();

				bgcmodjrb[0].setEnabled(true);
				bgcmodjrb[1].setEnabled(true);
				bgcmodjrb[0].doClick();   //set this as the default, and will set other N options
								
				dslmodjrb[0].setEnabled(true);
				dslmodjrb[1].setEnabled(true);
				dslmodjrb[0].doClick();   //set this as the default

				firemodjrb[0].setEnabled(true);
				firemodjrb[1].setEnabled(true);
				firemodjrb[0].doClick();   //set this as the default

				dvmmodjrb[0].setEnabled(false);  // always let DVM on
				dvmmodjrb[1].setEnabled(true);
				dvmmodjrb[1].doClick();   //set this as the default, and will set LAI option

		        //set-up plot viewers
		        var1plotter.reset();
	            var2plotter.reset();

				PhyVariablePlotter.f.setVisible(true);     //by default, showing this plot
				BioVariablePlotter.f.setVisible(true);      //by default, showing this plot

		        Caliber.plotting.setPlotter(var1plotter);
		    	Caliber.plotting.setPlotter2(var2plotter);

	            //model running control Tab
		    	runmodeB.setEnabled(true);
	            resetupB.setEnabled(true);
	            setupB.setEnabled(true);

	            startpauseB.setEnabled(true);
	            
	            //pickpftCB.setEnabled(true); // this will be enabled when it is selected
	            
		    } catch (Exception e){
		    	JOptionPane.showMessageDialog(fcontrol, " model setup failed!");
			}
		};

		private void runnerinit() {
			try {
		    	//initialize the Caliber.eqrunner
				Caliber.eqrunner = new Runner();
				Caliber.eqrunner.jconfigin = config;
				
				Caliber.plotting.setTargetTB(targetTB);  // need to pass the data in 'targetTB' to PlotterUpdate.java

		        Caliber.eqrunner.chtid = Integer.valueOf(chtidinputTF.getText());
				Caliber.prerun(); //default control options/parameters included
		        
	        } catch (Exception e) {
		    	System.err.println("TEM initializaion failed! - "+e);
	        }

		};

		//model default states and parameters after model initialization
	    private void getDefaultvarparFromTEM(){
	    	try {
	    		//Calibratible parameters
	    		double[] vegcov = Caliber.eqrunner.runcht.cht.getCd().getM_veg().getVegcov();
				vegpar_cal dumvpar = new vegpar_cal();
				soipar_cal dumspar = new soipar_cal();
	    		
	    		for (int ipft=0; ipft<ConstCohort.NUM_PFT; ipft++) {
	    			
	    			if (vegcov[ipft]>0.) {
	    			
	    				Caliber.temcj.getVbCalPar1pft(ipft);   // pass TEM read-in pars to 'temcj' for passing below
	    				dumvpar = Caliber.temcj.getVcalpar1pft();  // passing pars from 'temcj' to GUI

	    				calparTB.setValueAt(Double.toString(dumvpar.getCmax()), Configurer.I_CMAX, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getNmax()), Configurer.I_NMAX, ipft+1);

	    				calparTB.setValueAt(Double.toString(dumvpar.getCfall()[0]), Configurer.I_CFALLL, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getCfall()[1]), Configurer.I_CFALLS, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getCfall()[2]), Configurer.I_CFALLR, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getNfall()[0]), Configurer.I_NFALLL, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getNfall()[1]), Configurer.I_NFALLS, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getNfall()[2]), Configurer.I_NFALLR, ipft+1);

	    				calparTB.setValueAt(Double.toString(dumvpar.getKra()), Configurer.I_KRA, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getKrb()[0]), Configurer.I_KRBL, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getKrb()[1]), Configurer.I_KRBS, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getKrb()[2]), Configurer.I_KRBR, ipft+1);
	    				calparTB.setValueAt(Double.toString(dumvpar.getFrg()), Configurer.I_FRG, ipft+1);
	    			
	    			}

	    		}
	    		
	    		Caliber.temcj.getSbCalPar();   // pass TEM read-in par to 'temcj' for passing below
	    		dumspar = Caliber.temcj.getScalpar();  // passing pars from 'temcj' to GUI

				calparTB.setValueAt(Double.toString(dumspar.getMicbnup()), Configurer.I_MICBNUP, 1);
	    		calparTB.setValueAt(Double.toString(dumspar.getKdcmoss()), Configurer.I_KDCMOSS, 1);
	    		calparTB.setValueAt(Double.toString(dumspar.getKdcrawc()), Configurer.I_KDCRAWC, 1);
	    		calparTB.setValueAt(Double.toString(dumspar.getKdcsoma()), Configurer.I_KDCSOMA, 1);
	    		calparTB.setValueAt(Double.toString(dumspar.getKdcsompr()), Configurer.I_KDCSOMPR, 1);
	    		calparTB.setValueAt(Double.toString(dumspar.getKdcsomcr()), Configurer.I_KDCSOMCR, 1);

	    		// initial states
	    		for (int ipft=0; ipft<ConstCohort.NUM_PFT; ipft++) {
	    			if (vegcov[ipft]>0.) {
	    				Caliber.temcj.getInitVbState1pft(ipft);

	    				stateTB.setValueAt(Double.toString(Caliber.temcj.getInitvegc()[0]), Configurer.I_VEGCL, ipft+1);
	    				stateTB.setValueAt(Double.toString(Caliber.temcj.getInitvegc()[1]), Configurer.I_VEGCS, ipft+1);
	    				stateTB.setValueAt(Double.toString(Caliber.temcj.getInitvegc()[2]), Configurer.I_VEGCR, ipft+1);
	    		
	    				stateTB.setValueAt(Double.toString(Caliber.temcj.getInitvegn()[0]), Configurer.I_VEGNL, ipft+1);
	    				stateTB.setValueAt(Double.toString(Caliber.temcj.getInitvegn()[1]), Configurer.I_VEGNS, ipft+1);
	    				stateTB.setValueAt(Double.toString(Caliber.temcj.getInitvegn()[2]), Configurer.I_VEGNR, ipft+1);

	    				stateTB.setValueAt(Double.toString(Caliber.temcj.getInitdeadc()), Configurer.I_DEADC, ipft+1);
	    				stateTB.setValueAt(Double.toString(Caliber.temcj.getInitdeadn()), Configurer.I_DEADN, ipft+1);
	    			}
	    		}
	    		
	    		Caliber.temcj.getInitSbState();
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInitdmossthick()), Configurer.I_DMOSSTHICK, 1);
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInitfibthick()), Configurer.I_FIBTHICK, 1);
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInithumthick()), Configurer.I_HUMTHICK, 1);
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInitdmossc()), Configurer.I_DMOSSC, 1);
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInitshlwc()), Configurer.I_FIBSOILC, 1);
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInitdeepc()), Configurer.I_HUMSOILC, 1);
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInitminec()), Configurer.I_MINESOILC, 1);
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInitsoln()), Configurer.I_SOILN, 1);
	    		stateTB.setValueAt(Double.toString(Caliber.temcj.getInitavln()), Configurer.I_AVLN, 1);
	    			    		
	        } catch (Exception e) {
		    	System.err.println("reading Calpar from TEM failed! - "+e);
	        }

	    };

/////////////////////////////////////////////////////////////////////
	    public class configUpdater implements ActionListener{

			public void actionPerformed(ActionEvent arg0) {

				//make sure all directory name is ending with "/"

				if (!configdirTF.getText().endsWith("/"))
		            configdirTF.setText(configdirTF.getText()+"/");

				if (!outputdirTF.getText().endsWith("/"))
		            outputdirTF.setText(outputdirTF.getText()+"/");

				if (!reginputdirTF.getText().endsWith("/"))
		            reginputdirTF.setText(reginputdirTF.getText()+"/");

				if (!grdinputdirTF.getText().endsWith("/"))
		            grdinputdirTF.setText(grdinputdirTF.getText()+"/");

				if (!chtinputdirTF.getText().endsWith("/"))
		            chtinputdirTF.setText(chtinputdirTF.getText()+"/");

				String chtidtxt =(String)chtidinputTF.getText();
				if (!chtidtxt.matches("^-?[0-9]+(\\.[0-9]+)?$")) {
		            System.err.print("not a valid integer number");
					chtidinputTF.setText(String.valueOf(config.chtidinput));
				}
				disableGUI();  // must disable GUI options for re-doing
				updateControlB.setEnabled(true);
					
			}
	    };
	    
			// disable GUI
			private void disableGUI() {
				try {
	
		            //the model options block of Calibration Panel
					envmodjrb[0].setSelected(false);
					envmodjrb[1].setSelected(true);
					envmodjrb[0].setEnabled(false);
					envmodjrb[1].setEnabled(false);
	
					bgcmodjrb[0].doClick();
					bgcmodjrb[1].setSelected(false);
					bgcmodjrb[0].setEnabled(false);
					bgcmodjrb[1].setEnabled(false);
					
					dslmodjrb[0].setSelected(true);
					dslmodjrb[1].setSelected(false);
					dslmodjrb[0].setEnabled(false);
					dslmodjrb[1].setEnabled(false);
	
					firemodjrb[0].setSelected(true);
					firemodjrb[1].setSelected(false);
					firemodjrb[0].setEnabled(false);
					firemodjrb[1].setEnabled(false);
	
					dvmmodjrb[0].setSelected(false);
					dvmmodjrb[1].setSelected(true);   //dvm always on
					dvmmodjrb[0].setEnabled(false);
					dvmmodjrb[1].setEnabled(false);

					updatelaijrb[0].setSelected(true);
					updatelaijrb[1].setSelected(false);
					updatelaijrb[0].setEnabled(false);
					updatelaijrb[1].setEnabled(false);

			        //set-up plot viewers
			        var1plotter.reset();
		            var2plotter.reset();
	
		            //model running control Tab
			    	runmodeB.setEnabled(false);
		            resetupB.setEnabled(false);
		            setupB.setEnabled(false);
	
		            startpauseB.setEnabled(false);
		            
		            pickpftCB.setEnabled(false);
		            
			    } catch (Exception e){
			    	JOptionPane.showMessageDialog(fcontrol, " model setup failed!");
				}
			};

		/////////////////////////////////////////////////////////////////////////
	    public class controlUpdater implements ActionListener{

			public void actionPerformed(ActionEvent e) {

				// modify and update control file
				try {
					config.casename    = casenameTF.getText();
					config.configdir   = configdirTF.getText();
					config.outputdir   = outputdirTF.getText();
					config.reginputdir = reginputdirTF.getText();
					config.grdinputdir = grdinputdirTF.getText();
					config.chtinputdir = chtinputdirTF.getText();
					config.chtidinput  = Integer.valueOf((String)chtidinputTF.getText());

					ControlfileOutputer();
					
					// re-setup GUI and model initialization
					enableGUI();
					runnerinit();
					getDefaultvarparFromTEM();
					
		            // reset the pick-pft list and default index
		            pickpftCB.setSelectedIndex(Caliber.ipft);
		            
		            updateControlB.setEnabled(false);
					
				} catch (Exception ex) {
					//
				}

			}
	    };

	    
			private void ControlfileOutputer (){
				
				//re-write model control file, if modifying it in configTab
				try {
				      
				    BufferedReader input =  new BufferedReader(new FileReader(config.controlfile));  // for getting comments
				    
			    	String dummy1 = input.readLine().split(" /*", 2)[1];             // Line 1 - "/*" is delimiter for comments
			    	String dummy2 = input.readLine().split(" /*", 2)[1];             // Line 2 - "/*" is delimiter for comments
			    	String dummy3 = input.readLine().split(" /*", 2)[1];             // Line 3 - "/*" is delimiter for comments
			    	String dummy4 = input.readLine().split(" /*", 2)[1];             // Line 4 - "/*" is delimiter for comments
			    	String dummy5 = input.readLine().split(" /*", 2)[1];             // Line 5 - "/*" is delimiter for comments
			    	String dummy6 = input.readLine().split(" /*", 2)[1];             // Line 6 - "/*" is delimiter for comments
			    	String dummy7 = input.readLine().split(" /*", 2)[1];             // Line 7 - "/*" is delimiter for comments
				    input.close();

				    ///////////////////////////
					PrintStream output = new PrintStream(new FileOutputStream(config.controlfile));  // this is the output file

			    	output.printf(casenameTF.getText());
				    output.print(dummy1 + "\n");

			    	output.printf(configdirTF.getText());
				    output.print(dummy2 + "\n");

			    	output.printf(outputdirTF.getText());
				    output.print(dummy3 + "\n");

				    output.printf(reginputdirTF.getText());
				    output.print(dummy4 + "\n");

			    	output.printf(grdinputdirTF.getText());
				    output.print(dummy5 + "\n");
				    
			    	output.printf(chtinputdirTF.getText());
				    output.print(dummy6 + "\n");

			    	output.printf(chtidinputTF.getText());
				    output.print(dummy7 + "\n");

				    output.close();

				 } catch (Exception e) {
				    	JOptionPane.showMessageDialog(fcontrol, e.getMessage());
				 }

			};

//////////////////////////////////////////////////////////////////////////////
	public class pftSelector implements ActionListener{

			public void actionPerformed(ActionEvent arg0) {

				// store the current par
				int prepft = Caliber.ipft;
				saveoldpar(); 
				if (pickpftCB.isEnabled()) {					
					getCalparFromChangerToTable(Caliber.ipft);  
					//back-up current changer to table, here Caliber.ipft is the old one
				} else { // if pft scroll control not enable yet 
					pickpftCB.setEnabled(true);
				}
				
				// new PFT
				int newpft = pickpftCB.getSelectedIndex();
				int err=assignCalparTableToChanger(newpft);					
				if (err==0){
					Caliber.ipft = newpft;
					setTEMcalparsFromChanger();
				} else {
		            pickpftCB.setSelectedIndex(prepft); // set it back 
				}
			}
	}

	// pass the parameters to config-Tab in Control Pannel from changers in Calibration Pannel
	private void getCalparFromChangerToTable(int ipft){
		
		try {

			calparTB.setValueAt(String.valueOf(cmaxChanger.getValue()), Configurer.I_CMAX, ipft+1);
			calparTB.setValueAt(String.valueOf(nmaxChanger.getValue()), Configurer.I_NMAX, ipft+1);

			calparTB.setValueAt(String.valueOf(cfalllChanger.getValue()), Configurer.I_CFALLL, ipft+1);
			calparTB.setValueAt(String.valueOf(cfallsChanger.getValue()), Configurer.I_CFALLS, ipft+1);
			calparTB.setValueAt(String.valueOf(cfallrChanger.getValue()), Configurer.I_CFALLR, ipft+1);

			calparTB.setValueAt(String.valueOf(nfalllChanger.getValue()), Configurer.I_NFALLL, ipft+1);
			calparTB.setValueAt(String.valueOf(nfallsChanger.getValue()), Configurer.I_NFALLS, ipft+1);
			calparTB.setValueAt(String.valueOf(nfallrChanger.getValue()), Configurer.I_NFALLR, ipft+1);

			calparTB.setValueAt(String.valueOf(kraChanger.getValue()), Configurer.I_KRA, ipft+1);
			calparTB.setValueAt(String.valueOf(krblChanger.getValue()), Configurer.I_KRBL, ipft+1);
			calparTB.setValueAt(String.valueOf(krbsChanger.getValue()), Configurer.I_KRBS, ipft+1);
			calparTB.setValueAt(String.valueOf(krbrChanger.getValue()), Configurer.I_KRBR, ipft+1);
			calparTB.setValueAt(String.valueOf(frgChanger.getValue()), Configurer.I_FRG, ipft+1);

			calparTB.setValueAt(String.valueOf(micbnupChanger.getValue()), Configurer.I_MICBNUP, 1);
			calparTB.setValueAt(String.valueOf(kdcmosscChanger.getValue()), Configurer.I_KDCMOSS, 1);
			calparTB.setValueAt(String.valueOf(kdcrawcChanger.getValue()), Configurer.I_KDCRAWC, 1);
			calparTB.setValueAt(String.valueOf(kdcsomaChanger.getValue()), Configurer.I_KDCSOMA, 1);
			calparTB.setValueAt(String.valueOf(kdcsomprChanger.getValue()), Configurer.I_KDCSOMPR, 1);
			calparTB.setValueAt(String.valueOf(kdcsomcrChanger.getValue()), Configurer.I_KDCSOMCR, 1);

		} catch (Exception e){
	    	JOptionPane.showMessageDialog(fcontrol, " assigning Calibration parameters to Changer failed");
	    }

	}

	// read and set-up target state variables for calibration
	public class CalibgcTargetSelector implements ActionListener{

			public void actionPerformed(ActionEvent arg0) {
				//open file chooser
				String defaultdir = "config/";
				JFileChooser fc = new JFileChooser(defaultdir);
				int returnVal =fc.showOpenDialog(selectCalibgcfileB);
				if (returnVal == JFileChooser.APPROVE_OPTION) {
		            File file = fc.getSelectedFile();

		            //set-up target/initial bgc variables in the configurer Tab of Control Panel
		            calbgcTF.setText(file.getPath());
		            config.calibgcfile = calbgcTF.getText();
		            readCalbgcFromFile();

				}
			}
	};

		// read Bgc target and calibratable parameter files, called by Class ConfigureSelector
		private void readCalbgcFromFile(){


		    String status ="";
		    try {
			    status ="reading target variable file";
			    File drvF = new File(config.calibgcfile);
			    if(!drvF.exists()){
			    	JOptionPane.showMessageDialog(fcontrol, status+" not exist");
			    } else {

			    	double[] vegcov = Caliber.eqrunner.runcht.cht.getCd().getM_veg().getVegcov();
			    	
			    	//reading data from file
			    	BufferedReader input =  new BufferedReader(new FileReader(config.calibgcfile));

			    	String dummy="";
			    	dummy = input.readLine();  // comment
			    	dummy = input.readLine();  // comment

			    	String element[] = new String[ConstCohort.NUM_PFT];

			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_GPPt, ic);
			    	}
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_INNPPt, ic);
			    	}
			    					    
			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_NPPt, ic);
			    	}
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("\\s+");
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_NUPTAKEt, ic);
			    	}

			    	dummy = input.readLine();			    	
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_VEGCLt, ic);
			    	}
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_VEGCSt, ic);
			    	}
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_VEGCRt, ic);
			    	}
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_VEGNLt, ic);
			    	}
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_VEGNSt, ic);
			    	}
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	element = element[0].split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		targetTB.setValueAt(element[ic-1].trim(), Configurer.I_VEGNRt, ic);
			    	}

			    	// soil //////////////////////////////////////////
			    	dummy = input.readLine();

			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	targetTB.setValueAt(element[0].trim(), Configurer.I_DMOSSCt, 1);

			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	targetTB.setValueAt(element[0].trim(), Configurer.I_FIBSOILCt, 1);
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("//", 2);
			    	targetTB.setValueAt(element[0].trim(), Configurer.I_HUMSOILCt, 1);
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("\\s+");
			    	targetTB.setValueAt(element[0].trim(), Configurer.I_MINESOILCt, 1);
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("\\s+");
			    	targetTB.setValueAt(element[0].trim(), Configurer.I_SOILNt, 1);
			    	
			    	dummy = input.readLine();
			    	element = dummy.split("\\s+");
			    	targetTB.setValueAt(element[0].trim(), Configurer.I_AVLNt, 1);
			    }

		    } catch (Exception e){
		    	JOptionPane.showMessageDialog(fcontrol, status+" failed");
		    }

		};


	// initial calibratable parameter file reading for setting-up
	public class InitCaliparSelector implements ActionListener{

			public void actionPerformed(ActionEvent arg0) {
				//open file chooser
				String defaultdir = "config/";
				JFileChooser fc = new JFileChooser(defaultdir);
				int returnVal =fc.showOpenDialog(selectInitparfileB);
				if (returnVal == JFileChooser.APPROVE_OPTION) {
		            File file = fc.getSelectedFile();

		            //set-up parameter file input box in the configurer Tab of Control Panel
		            calparTF.setText(file.getPath());
		            config.iniparfile = calparTF.getText();
		            readInitparFromFile();
		            
		            config.outparfile = defaultdir+"calibration_outpar.txt";

		            //set-up the changer boxes in the Calibration Panel
					cmaxChanger.setEnabled(true);
			        nmaxChanger.setEnabled(true);

			        cfalllChanger.setEnabled(true);
			        cfallsChanger.setEnabled(true);
			        cfallrChanger.setEnabled(true);

			        nfalllChanger.setEnabled(true);
			        nfallsChanger.setEnabled(true);
			        nfallrChanger.setEnabled(true);

			        krblChanger.setEnabled(true);
			        krbsChanger.setEnabled(true);
			        krbrChanger.setEnabled(true);
			        frgChanger.setEnabled(true);

			        micbnupChanger.setEnabled(true);
			        kdcmosscChanger.setEnabled(true);
			        kdcrawcChanger.setEnabled(true);
			        kdcsomaChanger.setEnabled(true);
			        kdcsomprChanger.setEnabled(true);
			        kdcsomcrChanger.setEnabled(true);

			        
			        assignCalparTableToChanger(Caliber.ipft); //

			    	// ready to produce new set of parameters for the calibrated community
			        parresetB.setEnabled(true);
			        parrestoreB.setEnabled(true);
			        paroutputB.setEnabled(true);

			    	//parameter values reading from configurer Tabs
			        setTEMparsFromTable();

				}
			}
		};

		// read Bgc calibratable parameter files
		private void readInitparFromFile(){

		    String status ="";

		    try {
		    	status ="reading initial parameter file";
			    File parF = new File(config.iniparfile);
			    if(!parF.exists()){
			    	JOptionPane.showMessageDialog(fcontrol, status+" not exist");

			    }else{

			    	double[] vegcov = Caliber.eqrunner.runcht.cht.getCd().getM_veg().getVegcov();

			    	//reading data from calibratable par file

			    	BufferedReader input =  new BufferedReader(new FileReader(config.iniparfile));

			    	String dummy="";
			    	dummy = input.readLine(); // community type code may be included
			    	cmtcodeTF.setText(dummy.substring(0, 30));
			    	
			    	dummy = input.readLine(); // PFT name code may be included
			    	dummy = dummy.replaceAll("\\s+", ",");
			    	pftcodeTF.setText(dummy);
			    	
			    	String element[] = new String[ConstCohort.NUM_PFT];
			    	dummy = input.readLine().split("//", 2)[0];  // "//" is delimiter for comments
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);    // unknown number white space as data delimiter
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		calparTB.setValueAt(element[ic-1].trim(), Configurer.I_CMAX, ic);
			    	}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		calparTB.setValueAt(element[ic-1].trim(), Configurer.I_NMAX, ic);
			    	}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
			    	for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
			    		calparTB.setValueAt(element[ic-1].trim(), Configurer.I_CFALLL, ic);
			    	}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_CFALLS, ic);
		      		}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_CFALLR, ic);
		      		}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_NFALLL, ic);
		      		}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_NFALLS, ic);
		      		}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_NFALLR, ic);
		      		}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_KRA, ic);
		      		}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_KRBL, ic);
		      		}

		      		dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_KRBS, ic);
		      		}

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_KRBR, ic);
		      		}

		      		dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", ConstCohort.NUM_PFT);
		      		for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){
			    		if (vegcov[ic-1]>0.)			    		
		      			calparTB.setValueAt(element[ic-1].trim(), Configurer.I_FRG, ic);
		      		}

		      		// soil bgc pars to be calibrated
		      		dummy = input.readLine();
		      		
			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", 2);
		      		calparTB.setValueAt(element[0].trim(), Configurer.I_MICBNUP, 1);

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", 2);
		      		calparTB.setValueAt(element[0].trim(), Configurer.I_KDCMOSS, 1);

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", 2);
		      		calparTB.setValueAt(element[0].trim(), Configurer.I_KDCRAWC, 1);

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", 2);
		      		calparTB.setValueAt(element[0].trim(), Configurer.I_KDCSOMA, 1);

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", 2);
		      		calparTB.setValueAt(element[0].trim(), Configurer.I_KDCSOMPR, 1);

			    	dummy = input.readLine().split("//", 2)[0];
			    	element = dummy.split("\\s+", 2);
		      		calparTB.setValueAt(element[0].trim(), Configurer.I_KDCSOMCR, 1);
		      		
		      		input.close();
			    }

		    } catch (Exception e){
		    	JOptionPane.showMessageDialog(fcontrol, status+" failed");
		    }

		};

		// pass the parameters from config-Tab in Control Pannel to changers in Calibration Pannel
		private int assignCalparTableToChanger(int ipft){
			
			try {

				cmaxChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_CMAX, ipft+1)), 1);
				nmaxChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_NMAX, ipft+1)), 0);

				cfalllChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_CFALLL, ipft+1)), -2);
				cfallsChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_CFALLS, ipft+1)), -2);
				cfallrChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_CFALLR, ipft+1)), -2);

				nfalllChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_NFALLL, ipft+1)), -2);
				nfallsChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_NFALLS, ipft+1)), -2);
				nfallrChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_NFALLR, ipft+1)), -2);

				kraChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KRA, ipft+1)), -5);
				krblChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KRBL, ipft+1)), -1);
				krbsChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KRBS, ipft+1)), -1);
				krbrChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KRBR, ipft+1)), -1);
				frgChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_FRG, ipft+1)), -2);

				micbnupChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_MICBNUP, 1)), -2);
				kdcmosscChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCMOSS, 1)), -2);
				kdcrawcChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCRAWC, 1)), -2);
				kdcsomaChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCSOMA, 1)), -3);
				kdcsomprChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCSOMPR, 1)), -4);
				kdcsomcrChanger.updateValue(Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCSOMCR, 1)), -5);

			} catch (Exception e){
		    	JOptionPane.showMessageDialog(fcontrol, " assigning Calibration parameters to Changer failed");
		    	return -1;
		    }
			
			return 0;

		}

		//pass the parameters from config-Tab of Control Panel to TEM model
		private void setTEMparsFromTable(){
	    	
			double[] vegcov = Caliber.eqrunner.runcht.cht.getCd().getM_veg().getVegcov();
			vegpar_cal dvcalpar = new vegpar_cal();
			soipar_cal dscalpar = new soipar_cal();
			
			// veg. parameters needed for all PFTs
			for (int ip=0; ip<ConstCohort.NUM_PFT; ip++) {
				double parval = 0.;
				double parval2[] = new double [ConstCohort.NUM_PFT_PART];

				if (vegcov[ip]>0.) {
					parval=Double.valueOf((String) calparTB.getValueAt(Configurer.I_CMAX, ip+1));
					dvcalpar.setCmax(parval);
					parval=Double.valueOf((String) calparTB.getValueAt(Configurer.I_NMAX, ip+1));
					dvcalpar.setNmax(parval);

					parval2[0]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_CFALLL, ip+1));
					parval2[1]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_CFALLS, ip+1));
					parval2[2]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_CFALLR, ip+1));
					dvcalpar.setCfall(parval2);

					parval2[0]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_NFALLL, ip+1));
					parval2[1]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_NFALLS, ip+1));
					parval2[2]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_NFALLR, ip+1));
					dvcalpar.setNfall(parval2);

					parval=Double.valueOf((String) calparTB.getValueAt(Configurer.I_KRA, ip+1));
					dvcalpar.setKra(parval);

					parval2[0]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_KRBL, ip+1));
					parval2[1]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_KRBS, ip+1));
					parval2[2]=Double.valueOf((String) calparTB.getValueAt(Configurer.I_KRBR, ip+1));
					dvcalpar.setKrb(parval2);

					parval=Double.valueOf((String) calparTB.getValueAt(Configurer.I_FRG, ip+1));
					dvcalpar.setFrg(parval);

					// pass the parameters PFT by PFT
					Caliber.temcj.setVbCalPar1pft(ip, dvcalpar);
				}
			}

			// soil parameters
			double sparval = 0.;
			sparval = Double.valueOf((String) calparTB.getValueAt(Configurer.I_MICBNUP, 1));
			dscalpar.setMicbnup(sparval);
			sparval = Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCRAWC, 1));
			dscalpar.setKdcrawc(sparval);
			sparval = Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCSOMA, 1));
			dscalpar.setKdcsoma(sparval);
			sparval = Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCSOMPR, 1));
			dscalpar.setKdcsompr(sparval);
			sparval = Double.valueOf((String) calparTB.getValueAt(Configurer.I_KDCSOMCR, 1));
			dscalpar.setKdcsomcr(sparval);

			// pass the parameters of soil BGC
			Caliber.temcj.setSbCalPar(dscalpar);

		 };
		 
///////////////////////////////////////////////////////////////////////////////////////////////
//------ Operations on Calibration Tab of Control Panel --------------------------------------
	public class Exit implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {
			System.exit(0);
		}

	};

	public class RunMode implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {
			//
			startpauseB.setEnabled(false);
			setupB.setEnabled(true);
			resetupB.setEnabled(true);

			PhyVariablePlotter.f.setVisible(true);
			BioVariablePlotter.f.setVisible(true);

			if(runmodeB.getText().equals("TestRunner")){
				runmodeB.setText("Calibration");
				enableGUI();

			}else if(runmodeB.getText().equals("Calibration")){
				runmodeB.setText("TestRunner");

			}

			System.out.println("\n"+runmodeB.getText()+" Mode Switched ON ...");

		}

	};

	public class StartPause implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {

			// 1) "Pause" - temporarily stop the in-progress run, in order to check or change setting-up
			if (startpauseB.getText().equals("Pause")){
				startpauseB.setText("Start");
				resetupB.setEnabled(true);
				setupB.setEnabled(true);
				exitB.setEnabled(true);

				Caliber.stop();

			// 2) after all above, Start the run as expected
			} else if(startpauseB.getText().equals("Start")){
				startpauseB.setText("Pause");
				resetupB.setEnabled(false);
				setupB.setEnabled(false);
				exitB.setEnabled(false);

				if (runmodeB.getText().equals("TestRunner")) {
					var1plotter.reset();
					var2plotter.reset();
					Caliber.testrun();
				} else if (runmodeB.getText().equals("Calibration")){
					Caliber.start();
				}
			}

		}

	};

	// Model "Resetup" - after modifying one or more model setting-up, first UPDATE the setting,
	//         then restart a new model run
	public class Resetup implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {
			setupB.setEnabled(true);
			startpauseB.setEnabled(true);
			startpauseB.setText("Start");

			var1plotter.reset();
			var2plotter.reset();

			Caliber.reset();
			runnerinit();  

			Caliber.ipft = Integer.valueOf(pickpftCB.getSelectedItem().toString());	

			assignCalparTableToChanger(Caliber.ipft);
			setTEMoptionsFromConfig();
			setTEMparsFromTable();
			setTEMinitstateFromTable();
		}

	};

	// the initital state variables to TEM model
	private void setTEMinitstateFromTable(){

		// vegetation
		double[] vegcov = Caliber.eqrunner.runcht.cht.getCd().getM_veg().getVegcov();
		for (int ip=0; ip<ConstCohort.NUM_PFT; ip++) {
	      double dummy[] = new double[3]; 
	      
	      if (vegcov[ip]>0.) {
	    	  dummy[0]=Double.valueOf((String) stateTB.getValueAt(Configurer.I_VEGCL, ip+1));
	    	  dummy[1]=Double.valueOf((String) stateTB.getValueAt(Configurer.I_VEGCS, ip+1));
	    	  dummy[2]=Double.valueOf((String) stateTB.getValueAt(Configurer.I_VEGCR, ip+1));
	    	  Caliber.temcj.setInitvegc(dummy);

	    	  dummy[0]=Double.valueOf((String) stateTB.getValueAt(Configurer.I_VEGNL, ip+1));
	    	  dummy[1]=Double.valueOf((String) stateTB.getValueAt(Configurer.I_VEGNS, ip+1));
	    	  dummy[2]=Double.valueOf((String) stateTB.getValueAt(Configurer.I_VEGNR, ip+1));
	    	  Caliber.temcj.setInitvegn(dummy);

	    	  Caliber.temcj.setInitdeadc(Double.valueOf((String) stateTB.getValueAt(Configurer.I_DEADC, ip+1)));
	    	  Caliber.temcj.setInitdeadc(Double.valueOf((String) stateTB.getValueAt(Configurer.I_DEADN, ip+1)));

	    	  Caliber.temcj.setInitVbState1pft(ip);
	      }
		}
		
	      // Soil	      
	      Caliber.temcj.setInitdmossc(Double.valueOf((String) stateTB.getValueAt(Configurer.I_DMOSSC, 1)));
	      Caliber.temcj.setInitshlwc(Double.valueOf((String) stateTB.getValueAt(Configurer.I_FIBSOILC, 1)));
	      Caliber.temcj.setInitdeepc(Double.valueOf((String) stateTB.getValueAt(Configurer.I_HUMSOILC, 1)));
	      Caliber.temcj.setInitminec(Double.valueOf((String) stateTB.getValueAt(Configurer.I_MINESOILC, 1)));
	      Caliber.temcj.setInitsoln(Double.valueOf((String) stateTB.getValueAt(Configurer.I_SOILN, 1)));
	      Caliber.temcj.setInitavln(Double.valueOf((String) stateTB.getValueAt(Configurer.I_AVLN, 1)));
	      
	      Caliber.temcj.setInitSbState();
	};

	// Model-run "update switches and changers' parameters" - after modifying any of changers,
	// UPDATE the setting from the Changer Tab of control panel
	public class Setup implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {

			startpauseB.setEnabled(true);
			startpauseB.setText("Start");

			Caliber.ipft = Integer.valueOf(pickpftCB.getSelectedItem().toString());	
			
			setTEMoptionsFromConfig();
			
			saveoldpar();
			setTEMcalparsFromChanger();

		}
	
	};		
	
		private void saveoldpar() {
				 cmaxChanger.storeOldValue();
				 nmaxChanger.storeOldValue();
				 cfalllChanger.storeOldValue();
				 cfallsChanger.storeOldValue();
				 cfallrChanger.storeOldValue();
				 nfalllChanger.storeOldValue();
				 nfallsChanger.storeOldValue();
				 nfallrChanger.storeOldValue();
				 krblChanger.storeOldValue();
				 krbsChanger.storeOldValue();
				 krbrChanger.storeOldValue();
	
				 micbnupChanger.storeOldValue();
				 kdcmosscChanger.storeOldValue();
				 kdcrawcChanger.storeOldValue();
				 kdcsomaChanger.storeOldValue();
				 kdcsomprChanger.storeOldValue();
				 kdcsomcrChanger.storeOldValue();
		
		}

		//after clicking setup, update the parameters to tem, called by Class: Setup/Resetup
		private void setTEMcalparsFromChanger(){
	
			//veg.
			Caliber.jvcalpar.setCmax(cmaxChanger.getValue());
			Caliber.jvcalpar.setNmax(nmaxChanger.getValue());
	
			double cfall[] = new double[ConstCohort.NUM_PFT_PART];
			cfall[0]=cfalllChanger.getValue();
			cfall[1]=cfallsChanger.getValue();
			cfall[2]=cfallrChanger.getValue();
			Caliber.jvcalpar.setCfall(cfall);
	
			double nfall[] = new double[ConstCohort.NUM_PFT_PART];
			nfall[0]=nfalllChanger.getValue();
			nfall[1]=nfallsChanger.getValue();
			nfall[2]=nfallrChanger.getValue();
			Caliber.jvcalpar.setCfall(nfall);
	
			double kra = kraChanger.getValue();
			Caliber.jvcalpar.setKra(kra);
			
			double krb[] = new double[ConstCohort.NUM_PFT_PART];
			krb[0]=krblChanger.getValue();
			krb[1]=krbsChanger.getValue();
			krb[2]=krbrChanger.getValue();
			Caliber.jvcalpar.setKrb(krb);
	
			double frg = frgChanger.getValue();
			Caliber.jvcalpar.setFrg(frg);
	
			//soil
			Caliber.jscalpar.setMicbnup(krblChanger.getValue());
	
			Caliber.jscalpar.setKdcmoss(kdcmosscChanger.getValue());
			Caliber.jscalpar.setKdcrawc(kdcrawcChanger.getValue());
			Caliber.jscalpar.setKdcsoma(kdcsomaChanger.getValue());
			Caliber.jscalpar.setKdcsompr(kdcsomprChanger.getValue());
			Caliber.jscalpar.setKdcsomcr(kdcsomcrChanger.getValue());
	
			//pass the parameters to c++ holders
			int ipft = Caliber.ipft;
			Caliber.temcj.setVbCalPar1pft(ipft, Caliber.jvcalpar);
			Caliber.temcj.setSbCalPar(Caliber.jscalpar);
	
		};

		//update model process switches to tem, called by Class: Setup/Resetup
		private void setTEMoptionsFromConfig(){
	
			//
			boolean envmodule = false;
			boolean bgcmodule = false;
			boolean dslmodule = false;
			boolean firemodule= false;
			boolean dvmmodule = false;
			if(envmodjrb[1].isSelected()) envmodule=true;
			if(bgcmodjrb[1].isSelected()) bgcmodule=true;
			if(dslmodjrb[1].isSelected()) dslmodule=true;
			if(dvmmodjrb[1].isSelected()) dvmmodule=true;
			if(firemodjrb[1].isSelected()) firemodule=true;
	
			//Turn Modules on/off
			Caliber.eqrunner.runcht.cht.getMd().setEnvmodule(envmodule);
			Caliber.eqrunner.runcht.cht.getMd().setBgcmodule(bgcmodule);
			Caliber.eqrunner.runcht.cht.getMd().setDslmodule(dslmodule);
			Caliber.eqrunner.runcht.cht.getMd().setDvmmodule(dvmmodule);
			Caliber.eqrunner.runcht.cht.getMd().setDsbmodule(firemodule);
	
			// pregnostic LAI or dynamical LAI
			boolean updatelai = false;
			if (dvmmodule) {
				if(updatelaijrb[1].isSelected()) updatelai = true;			
			}
			Caliber.eqrunner.runcht.cht.getMd().setUpdatelai(updatelai);
	
			// N modules control
			boolean nfeed   = false;
			boolean avlnflg = false;
			boolean baseline= false;
			if (bgcmodule) {
				if(nfeedjrb[1].isSelected()) nfeed = true;
				if(avlnjrb[1].isSelected())	avlnflg = true;
				if(baselinejrb[1].isSelected())	baseline = true;
			}
			Caliber.eqrunner.runcht.cht.getMd().setBaseline(baseline);
			Caliber.eqrunner.runcht.cht.getMd().setAvlnflg(avlnflg);
			Caliber.eqrunner.runcht.cht.getMd().setNfeed(nfeed);
	
			// fire module option
			if (firemodule) Caliber.eqrunner.runcht.cht.getMd().setFriderived(firemodule);
	
		};

	//reset calibration parameters to the initial values (i.e., from config files)
	public class ParameterResetter implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {

			readInitparFromFile();
			assignCalparTableToChanger(Caliber.ipft);
			setTEMparsFromTable();

			startpauseB.setEnabled(false);
			setupB.setEnabled(true);
			resetupB.setEnabled(true);

		}

	};

	//restore calibration parameters to the previous calibrated (NOT the initial values as Resetter does)
	public class ParameterRestorer implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {
			 cmaxChanger.restore();
			 nmaxChanger.restore();
			 cfalllChanger.restore();
			 cfallsChanger.restore();
			 cfallrChanger.restore();
			 nfalllChanger.restore();
			 nfallsChanger.restore();
			 nfallrChanger.restore();
			 krblChanger.restore();
			 krbsChanger.restore();
			 krbrChanger.restore();

			 micbnupChanger.restore();
			 kdcmosscChanger.restore();
			 kdcrawcChanger.restore();
			 kdcsomaChanger.restore();
			 kdcsomprChanger.restore();
			 kdcsomcrChanger.restore();

			 startpauseB.setEnabled(false);
			 setupB.setEnabled(true);
			 resetupB.setEnabled(true);

		}

	};

	public class ParameterOutputer implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {
			
			//output calibrated parameters
			try {
			      
				PrintStream output = new PrintStream(new FileOutputStream(config.outparfile));  // this is the output file

			    BufferedReader input =  new BufferedReader(new FileReader(config.iniparfile));  // for getting comments

			    String dummy="";
			    
			    dummy = "//===========================================================";  output.println(dummy);       // Line 0 (community separation line)
			    
			    dummy = input.readLine();  output.println(dummy);       // Line 1
			    dummy = input.readLine();  output.println(dummy);       // Line 2
			    	
		    	dummy = input.readLine().split("//", 2)[1];             // Line 3 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_CMAX, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 4 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_NMAX, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 5 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_CFALLL, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 6 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_CFALLS, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 7 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_CFALLR, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 8 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_NFALLL, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 9 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_NFALLS, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 10 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_NFALLR, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 11 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_KRA, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 12 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_KRBL, ic));
			    }
			    output.print("//" + dummy + "\n");
			    
		    	dummy = input.readLine().split("//", 2)[1];             // Line 13 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_KRBS, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 14 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_KRBR, ic));
			    }
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 15 - "//" is delimiter for comments
			    for(int ic =1; ic<=ConstCohort.NUM_PFT; ic++){			    	  
			    	output.printf("%-13s", calparTB.getValueAt(Configurer.I_FRG, ic));
			    }
			    output.print("//" + dummy + "\n");

			    //
			    dummy = input.readLine();  output.println(dummy);       // Line 16 - soil calibrated parameter (comments)
			    
		    	dummy = input.readLine().split("//", 2)[1];             // Line 17 - "//" is delimiter for comments
		    	output.printf("%-16s", calparTB.getValueAt(Configurer.I_MICBNUP, 1));
			    output.print("//" + dummy + "\n");

			    dummy = input.readLine().split("//", 2)[1];             // Line 18 - "//" is delimiter for comments
		    	output.printf("%-16s", calparTB.getValueAt(Configurer.I_KDCMOSS, 1));
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 19 - "//" is delimiter for comments
		    	output.printf("%-16s", calparTB.getValueAt(Configurer.I_KDCRAWC, 1));
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 20 - "//" is delimiter for comments
		    	output.printf("%-16s", calparTB.getValueAt(Configurer.I_KDCSOMA, 1));
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 21 - "//" is delimiter for comments
		    	output.printf("%-16s", calparTB.getValueAt(Configurer.I_KDCSOMPR, 1));
			    output.print("//" + dummy + "\n");

		    	dummy = input.readLine().split("//", 2)[1];             // Line 22 - "//" is delimiter for comments
		    	output.printf("%-16s", calparTB.getValueAt(Configurer.I_KDCSOMCR, 1));
			    output.print("//" + dummy + "\n");

			    //
			    input.close();
			    output.close();

			 } catch (Exception e) {
			    	JOptionPane.showMessageDialog(fcontrol, e.getMessage());
			 }

		}

	};

}