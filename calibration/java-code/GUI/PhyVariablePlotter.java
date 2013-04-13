package GUI;

import java.awt.BorderLayout;
import java.awt.Dimension;

import javax.swing.BoxLayout;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTabbedPane;

import com.l2fprod.common.swing.JTaskPane;
import com.l2fprod.common.swing.JTaskPaneGroup;

public class PhyVariablePlotter {

	static JFrame f;

	// Yearly vairables
	public PlotterMode2 ts1TP;
	public PlotterMode2 vwc1TP;
	public PlotterMode2 etTP;
	public PlotterMode4 qinoutTP;
	
	public PlotterMode4 ts2TP;
	public PlotterMode4 vwc2TP;
	public PlotterMode3 aldwtbTP;
	public PlotterMode3 peatthickTP;

	// Monthly variables
	public PlotterMode2 mpptTP;
	public PlotterMode2 metTP;
	public PlotterMode2 mqoutTP;
	public PlotterMode2 mwtbdrgdTP;
	public PlotterMode2 mvwc1TP;
	public PlotterMode3 mvwc2TP;

	public PlotterMode1 mppfdTP;
	public PlotterMode1 mtaTP;
	public PlotterMode2 maldTP;
	public PlotterMode2 mts1TP;
	public PlotterMode3 mts2TP;

	public PhyVariablePlotter() {

		f = new JFrame("Physical Variable Plot Viewer");

		f.setLayout(new BorderLayout());

		try {

			f.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);

			JTabbedPane tp = new JTabbedPane();

			JPanel ylypanel  = getYearlyPanel();
			JPanel mly1panel = getMonthly1Panel();
			JPanel mly2panel = getMonthly2Panel();

			tp.add("Yealy Variables", ylypanel);
			tp.add("Monthly Variables - Hydrological", mly1panel);
			tp.add("Monthly Variables - Thermal", mly2panel);

			f.add(tp, BorderLayout.CENTER);

			f.setLocation(650, 51);
		} catch (Exception x) {

		}

		f.setSize(760, 810);
		f.setVisible(true);

	}

	private JPanel getYearlyPanel() {
		JPanel targetPanel = new JPanel();
		targetPanel.setLayout(new BoxLayout(targetPanel, BoxLayout.X_AXIS));

		JTaskPane leftJTP = new JTaskPane();

		ts1TP = new PlotterMode2("Tair", "Ts_ave", 500);
		JPanel ts1Panel = ts1TP.getPanel();
		ts1Panel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup ts1TG = new JTaskPaneGroup();
		ts1TG.setSpecial(false);
		ts1TG.setExpanded(true);
		ts1TG.setTitle("Soil temperature 1");
		ts1TG.add(ts1Panel);
		leftJTP.add(ts1TG);

		vwc1TP = new PlotterMode2("iceVWCave", "liqVWCave", 500);
		JPanel vwc1Panel = vwc1TP.getPanel();
		vwc1Panel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup vwc1TG = new JTaskPaneGroup();
		vwc1TG.setSpecial(false);
		vwc1TG.setExpanded(true);
		vwc1TG.setTitle("Soil water/ice volume content");
		vwc1TG.add(vwc1Panel);
		leftJTP.add(vwc1TG);

		etTP = new PlotterMode2("PET", "EET", 1000);
		JPanel etPanel = etTP.getPanel();
		etPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup etTG = new JTaskPaneGroup();
		etTG.setSpecial(false);
		etTG.setExpanded(true);
		etTG.setTitle("Evapotranspiration");
		etTG.add(etPanel);
		leftJTP.add(etTG);

		qinoutTP = new PlotterMode4("Snow","Rain","Runoff", "Drainage", 500);
		JPanel qoutPanel = qinoutTP.getPanel();
		qoutPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup qoutTG = new JTaskPaneGroup();
		qoutTG.setSpecial(false);
		qoutTG.setExpanded(true);
		qoutTG.setTitle("Water In/Outflow");
		qoutTG.add(qoutPanel);
		leftJTP.add(qoutTG);
				
		JTaskPane rightJTP = new JTaskPane();

		ts2TP = new PlotterMode4("Ts_fib", "Ts_hum", "Ts_min20", "Ts_min100", 500);
		JPanel ts2Panel = ts2TP.getPanel();
		ts2Panel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup ts2TG = new JTaskPaneGroup();
		ts2TG.setSpecial(false);
		ts2TG.setExpanded(true);
		ts2TG.setTitle("Soil Temperature 2");
		ts2TG.add(ts2Panel);
		rightJTP.add(ts2TG);
		
		vwc2TP = new PlotterMode4("VWC_fib", "VWC_hum", "VWC_min20", "VWC_min100", 500);
		JPanel vwc2Panel = vwc2TP.getPanel();
		vwc2Panel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup vwc2TG = new JTaskPaneGroup();
		vwc2TG.setSpecial(false);
		vwc2TG.setExpanded(true);
		vwc2TG.setTitle("Soil Volume Water Content%");
		vwc2TG.add(vwc2Panel);
		rightJTP.add(vwc2TG);

		aldwtbTP = new PlotterMode3("Ald", "WTB", "DrgDepth", 1000);
		JPanel aldwtbPanel = aldwtbTP.getPanel();
		aldwtbPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup aldwtbTG = new JTaskPaneGroup();
		aldwtbTG.setSpecial(false);
		aldwtbTG.setExpanded(true);
		aldwtbTG.setTitle("Thermal/Hydraulic interfaces");
		aldwtbTG.add(aldwtbPanel);
		rightJTP.add(aldwtbTG);

		peatthickTP = new PlotterMode3("MOSSTHICK", "FIBTHICK", "HUMTHICK", 1000);
		JPanel peatthickPanel = peatthickTP.getPanel();
		peatthickPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup peatthickTG = new JTaskPaneGroup();
		peatthickTG.setSpecial(false);
		peatthickTG.setExpanded(true);
		peatthickTG.setTitle("Moss/OSL Thickness");
		peatthickTG.add(peatthickPanel);
		rightJTP.add(peatthickTG);


		targetPanel.add(leftJTP);
		targetPanel.add(rightJTP);
		
		targetPanel.setPreferredSize(new Dimension(320, 900));
		return targetPanel;
	}

	private JPanel getMonthly1Panel() {
		JPanel targetPanel = new JPanel();
		targetPanel.setLayout(new BoxLayout(targetPanel, BoxLayout.X_AXIS));

		JTaskPane leftJTP = new JTaskPane();

		mpptTP = new PlotterMode2("RAINFALL", "SNOWFALL", 24);
		JPanel mpptPanel = mpptTP.getPanel();
		mpptPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mpptTG = new JTaskPaneGroup();
		mpptTG.setSpecial(false);
		mpptTG.setExpanded(true);
		mpptTG.setTitle("Precipitation");
		mpptTG.add(mpptPanel);
		leftJTP.add(mpptTG);

		metTP = new PlotterMode2("PET", "EET", 24);
		JPanel metPanel = metTP.getPanel();
		metPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup metTG = new JTaskPaneGroup();
		metTG.setSpecial(false);
		metTG.setExpanded(true);
		metTG.setTitle("ET");
		metTG.add(metPanel);
		leftJTP.add(metTG);

		mqoutTP = new PlotterMode2("RUNOFF", "DRAINAGE", 24);
		JPanel mqoutPanel = mqoutTP.getPanel();
		mqoutPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mqoutTG = new JTaskPaneGroup();
		mqoutTG.setSpecial(false);
		mqoutTG.setExpanded(true);
		mqoutTG.setTitle("Water Outflow");
		mqoutTG.add(mqoutPanel);
		leftJTP.add(mqoutTG);
		
		JTaskPane rightJTP = new JTaskPane();
		
		mwtbdrgdTP = new PlotterMode2("Water Table", "Drainage Depth", 24);
		JPanel mwtbdrgdPanel = mwtbdrgdTP.getPanel();
		mwtbdrgdPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mwtbdrgdTG = new JTaskPaneGroup();
		mwtbdrgdTG.setSpecial(false);
		mwtbdrgdTG.setExpanded(true);
		mwtbdrgdTG.setTitle("Water Table/Drainage Depth");
		mwtbdrgdTG.add(mwtbdrgdPanel);
		rightJTP.add(mwtbdrgdTG);
	
		mvwc1TP = new PlotterMode2("Shlw", "Deep", 24);
		JPanel mvwc1Panel = mvwc1TP.getPanel();
		mvwc1Panel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvwc1TG = new JTaskPaneGroup();
		mvwc1TG.setSpecial(false);
		mvwc1TG.setExpanded(true);
		mvwc1TG.setTitle("Org. Layer VWC");
		mvwc1TG.add(mvwc1Panel);
		rightJTP.add(mvwc1TG);
				
		mvwc2TP = new PlotterMode3("Mine-20", "Mine-100", "Mine-below100", 24);
		JPanel mvwc2Panel = mvwc2TP.getPanel();
		mvwc2Panel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvwc2TG = new JTaskPaneGroup();
		mvwc2TG.setSpecial(false);
		mvwc2TG.setExpanded(true);
		mvwc2TG.setTitle("Mineral Layer VWC");
		mvwc2TG.add(mvwc2Panel);
		rightJTP.add(mvwc2TG);

		targetPanel.add(leftJTP);
		targetPanel.add(rightJTP);

		targetPanel.setPreferredSize(new Dimension(750, 900));
		return targetPanel;
	}

	private JPanel getMonthly2Panel() {
		JPanel targetPanel = new JPanel();
		targetPanel.setLayout(new BoxLayout(targetPanel, BoxLayout.X_AXIS));

		JTaskPane leftJTP = new JTaskPane();

		mppfdTP = new PlotterMode1("PAR", 24);
		JPanel mrecoPanel = mppfdTP.getPanel();
		mrecoPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mrecoTG = new JTaskPaneGroup();
		mrecoTG.setSpecial(false);
		mrecoTG.setExpanded(true);
		mrecoTG.setTitle("PAR");
		mrecoTG.add(mrecoPanel);
		leftJTP.add(mrecoTG);

		mtaTP = new PlotterMode1("Tair", 24);
		JPanel mtaPanel = mtaTP.getPanel();
		mtaPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mtaTG = new JTaskPaneGroup();
		mtaTG.setSpecial(false);
		mtaTG.setExpanded(true);
		mtaTG.setTitle("Tair");
		mtaTG.add(mtaPanel);
		leftJTP.add(mtaTG);
		
		JTaskPane rightJTP = new JTaskPane();
		
		maldTP = new PlotterMode2("ALD", "ALC", 24);
		JPanel maldPanel = maldTP.getPanel();
		maldPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup maldTG = new JTaskPaneGroup();
		maldTG.setSpecial(false);
		maldTG.setExpanded(true);
		maldTG.setTitle("Active Layer Depth/Cap");
		maldTG.add(maldPanel);
		rightJTP.add(maldTG);

		mts1TP = new PlotterMode2("Shlw", "Deep", 24);
		JPanel mts1Panel = mts1TP.getPanel();
		mts1Panel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mts1TG = new JTaskPaneGroup();
		mts1TG.setSpecial(false);
		mts1TG.setExpanded(true);
		mts1TG.setTitle("Org. Layer Temperature");
		mts1TG.add(mts1Panel);
		rightJTP.add(mts1TG);
				
		mts2TP = new PlotterMode3("Mine-20", "Mine-100", "Mine-below100", 24);
		JPanel mts2Panel = mts2TP.getPanel();
		mts2Panel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mts2TG = new JTaskPaneGroup();
		mts2TG.setSpecial(false);
		mts2TG.setExpanded(true);
		mts2TG.setTitle("Mineral Layer Temperature");
		mts2TG.add(mts2Panel);
		rightJTP.add(mts2TG);
		
		targetPanel.add(leftJTP);
		targetPanel.add(rightJTP);

		targetPanel.setPreferredSize(new Dimension(750, 900));
		return targetPanel;
	}

	public void reset() {
		ts1TP.reset();
		vwc1TP.reset();
		etTP.reset();
		qinoutTP.reset();
		
		ts2TP.reset();
		vwc2TP.reset();
		aldwtbTP.reset();
		peatthickTP.reset();
		
		mpptTP.reset();
		mppfdTP.reset();
		mtaTP.reset();
		metTP.reset();
		mqoutTP.reset();

		mwtbdrgdTP.reset();
		maldTP.reset();
		mts1TP.reset();
		mts2TP.reset();
		mvwc1TP.reset();
		mvwc2TP.reset();
		
	}

}