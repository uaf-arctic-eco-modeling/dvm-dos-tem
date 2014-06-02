package GUI;

import java.awt.BorderLayout;
import java.awt.Dimension;
//import java.awt.Label;

import javax.swing.BoxLayout;
import javax.swing.JFrame;
//import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTabbedPane;
//import javax.swing.SpringLayout;

import com.l2fprod.common.swing.JTaskPane;
import com.l2fprod.common.swing.JTaskPaneGroup;

public class BioVariablePlotter {

	static JFrame f;

	// flux vairables at yearly time-step
	public PlotterMode4 ingnppTP;
	public PlotterMode3 gnppTP;
	public PlotterMode2 ltrfalcTP;
	public PlotterMode2 rhTP;	

	public PlotterMode1 innuptakeTP;
	public PlotterMode2 nuptakeTP;
	public PlotterMode2 sorgnioTP;
	public PlotterMode2 soilnminTP;
	
	// State variables at yearly time-step
	public PlotterMode2 vegclTP;
	public PlotterMode2 vegcsTP;
	public PlotterMode2 vegcrTP;
	public PlotterMode2 vegcTP;	
	
	public PlotterMode2 dmosscTP;
	public PlotterMode2 fibsoilcTP;
	public PlotterMode2 humsoilcTP;
	public PlotterMode2 minesoilcTP;
	public PlotterMode2 soilcTP;

	public PlotterMode2 vegnlTP;
	public PlotterMode2 vegnsTP;
	public PlotterMode2 vegnrTP;
	public PlotterMode2 vegnTP;

	public PlotterMode1 mossthickTP;
	public PlotterMode2 peatthickTP;
	public PlotterMode2 avlnTP;
	public PlotterMode2 orgnTP;	

	// A few flux/state vairables at monthly time-step
	public PlotterMode3 m_vcfluxTP;
	public PlotterMode2 m_vnfluxTP;
	public PlotterMode2 m_scfluxTP;
	public PlotterMode4 m_snfluxTP;
	
	public PlotterMode1 m_vegclTP;
	public PlotterMode1 m_vegcsTP;
	public PlotterMode1 m_vegcrTP;
	
	public PlotterMode2 m_vegnlTP;
	public PlotterMode1 m_vegnsTP;
	public PlotterMode1 m_vegnrTP;


	public BioVariablePlotter() {

		f = new JFrame("Biological Variable Plot Viewer");

		f.setLayout(new BorderLayout());

		try {

			f.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);

			JTabbedPane tp = new JTabbedPane();

			JPanel fluxpanel = getFluxPanel();
			JPanel vstatepanel = getVstatePanel();
			JPanel sstatepanel = getSstatePanel();
			JPanel monthlypanel = getMonthPanel();

			tp.add("Yearly Fluxes", fluxpanel);
			tp.add("Yearly Veg. States", vstatepanel);
			tp.add("Yearly Soil States", sstatepanel);
			tp.add("Monthly Checking", monthlypanel);

			f.add(tp, BorderLayout.CENTER);

			f.setLocation(580, 1);
		} catch (Exception x) {

		}

		f.setSize(760, 830);
		f.setVisible(true);

	}

	private JPanel getFluxPanel() {
		JPanel fluxPanel = new JPanel();
		fluxPanel.setLayout(new BoxLayout(fluxPanel, BoxLayout.X_AXIS));

		JTaskPane leftJTP = new JTaskPane();

		ingnppTP = new PlotterMode4("GPPsim", "GPPtar", "NPPsim", "NPPtar", 500);
		JPanel ingnppPanel = ingnppTP.getPanel();
		ingnppPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup ingnppTG = new JTaskPaneGroup();
		ingnppTG.setSpecial(false);
		ingnppTG.setExpanded(true);
		ingnppTG.setTitle("G/NPP w/o N");
		ingnppTG.add(ingnppPanel);
		leftJTP.add(ingnppTG);

		gnppTP = new PlotterMode3("GPPsim", "NPPsim", "NPPtar", 500);
		JPanel gnppPanel = gnppTP.getPanel();
		gnppPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup gnppTG = new JTaskPaneGroup();
		gnppTG.setSpecial(false);
		gnppTG.setExpanded(true);
		gnppTG.setTitle("G/NPP");
		gnppTG.add(gnppPanel);
		leftJTP.add(gnppTG);

		ltrfalcTP = new PlotterMode2("LTRCsim", "LTRCtar", 500);
		JPanel ltrfalcPanel = ltrfalcTP.getPanel();
		ltrfalcPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup ltrfalcTG = new JTaskPaneGroup();
		ltrfalcTG.setSpecial(false);
		ltrfalcTG.setExpanded(true);
		ltrfalcTG.setTitle("LitterFall-C");
		ltrfalcTG.add(ltrfalcPanel);
		leftJTP.add(ltrfalcTG);
		
		rhTP = new PlotterMode2("RHsim", "RHtar", 500);
		JPanel rhPanel = rhTP.getPanel();
		rhPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup rhTG = new JTaskPaneGroup();
		rhTG.setSpecial(false);
		rhTG.setExpanded(true);
		rhTG.setTitle("RH");
		rhTG.add(rhPanel);
		leftJTP.add(rhTG);

		JTaskPane rightJTP = new JTaskPane();

		innuptakeTP = new PlotterMode1("INNUPTAKEsim", 500);
		JPanel innuptakePanel = innuptakeTP.getPanel();
		innuptakePanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup innuptakeTG = new JTaskPaneGroup();
		innuptakeTG.setSpecial(false);
		innuptakeTG.setExpanded(true);
		innuptakeTG.setTitle("max. NUPTAKE");
		innuptakeTG.add(innuptakePanel);
		rightJTP.add(innuptakeTG);

		nuptakeTP = new PlotterMode2("NUPTAKEsim", "NUPTAKEtar", 500);
		JPanel nuptakePanel = nuptakeTP.getPanel();
		nuptakePanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup nuptakeTG = new JTaskPaneGroup();
		nuptakeTG.setSpecial(false);
		nuptakeTG.setExpanded(true);
		nuptakeTG.setTitle("NUPTAKE");
		nuptakeTG.add(nuptakePanel);
		rightJTP.add(nuptakeTG);

		sorgnioTP = new PlotterMode2("LTRNsim", "netNMINsim", 500);
		JPanel sorgnioPanel = sorgnioTP.getPanel();
		sorgnioPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup sorgnioTG = new JTaskPaneGroup();
		sorgnioTG.setSpecial(false);
		sorgnioTG.setExpanded(true);
		sorgnioTG.setTitle("Soil Org.-N I/O");
		sorgnioTG.add(sorgnioPanel);
		rightJTP.add(sorgnioTG);

		soilnminTP = new PlotterMode2("gNMINsim", "NIMMsim", 500);
		JPanel soilnminPanel = soilnminTP.getPanel();
		soilnminPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup soilnminTG = new JTaskPaneGroup();
		soilnminTG.setSpecial(false);
		soilnminTG.setExpanded(true);
		soilnminTG.setTitle("Soil gross N miner./immobil.");
		soilnminTG.add(soilnminPanel);
		rightJTP.add(soilnminTG);
		
		fluxPanel.add(leftJTP);
		fluxPanel.add(rightJTP);
		fluxPanel.setPreferredSize(new Dimension(420, 900));
		return fluxPanel;
	}

	private JPanel getVstatePanel() {
		JPanel targetPanel = new JPanel();
		targetPanel.setLayout(new BoxLayout(targetPanel, BoxLayout.X_AXIS));

		JTaskPane leftJTP = new JTaskPane();

		vegclTP = new PlotterMode2("model", "target", 200);
		JPanel vegclPanel = vegclTP.getPanel();
		vegclPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup vegclTG = new JTaskPaneGroup();
		vegclTG.setSpecial(false);
		vegclTG.setExpanded(true);
		vegclTG.setTitle("VEGC-leaf");
		vegclTG.add(vegclPanel);
		leftJTP.add(vegclTG);

		vegcsTP = new PlotterMode2("model", "target", 200);
		JPanel vegcsPanel = vegcsTP.getPanel();
		vegcsPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup vegcsTG = new JTaskPaneGroup();
		vegcsTG.setSpecial(false);
		vegcsTG.setExpanded(true);
		vegcsTG.setTitle("VEGC-stem");
		vegcsTG.add(vegcsPanel);
		leftJTP.add(vegcsTG);

		vegcrTP = new PlotterMode2("model", "target", 200);
		JPanel vegcrPanel = vegcrTP.getPanel();
		vegcrPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup vegcrTG = new JTaskPaneGroup();
		vegcrTG.setSpecial(false);
		vegcrTG.setExpanded(true);
		vegcrTG.setTitle("VEGC-root");
		vegcrTG.add(vegcrPanel);
		leftJTP.add(vegcrTG);

		vegcTP = new PlotterMode2("model", "target", 200);
		JPanel vegcPanel = vegcTP.getPanel();
		vegcPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup vegcTG = new JTaskPaneGroup();
		vegcTG.setSpecial(false);
		vegcTG.setExpanded(true);
		vegcTG.setTitle("VEGC-total");
		vegcTG.add(vegcPanel);
		leftJTP.add(vegcTG);

		///
		JTaskPane rightJTP = new JTaskPane();

		vegnlTP = new PlotterMode2("model", "target", 200);
		JPanel vegnlPanel = vegnlTP.getPanel();
		vegnlPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup vegnlTG = new JTaskPaneGroup();
		vegnlTG.setSpecial(false);
		vegnlTG.setExpanded(true);
		vegnlTG.setTitle("VEGN-leaf");
		vegnlTG.add(vegnlPanel);
		rightJTP.add(vegnlTG);

		vegnsTP = new PlotterMode2("model", "target", 200);
		JPanel vegnsPanel = vegnsTP.getPanel();
		vegnsPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup vegnsTG = new JTaskPaneGroup();
		vegnsTG.setSpecial(false);
		vegnsTG.setExpanded(true);
		vegnsTG.setTitle("VEGN-stem");
		vegnsTG.add(vegnsPanel);
		rightJTP.add(vegnsTG);

		vegnrTP = new PlotterMode2("model", "target", 200);
		JPanel vegnrPanel = vegnrTP.getPanel();
		vegnrPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup vegnrTG = new JTaskPaneGroup();
		vegnrTG.setSpecial(false);
		vegnrTG.setExpanded(true);
		vegnrTG.setTitle("VEGN-root");
		vegnrTG.add(vegnrPanel);
		rightJTP.add(vegnrTG);

		//
		vegnTP = new PlotterMode2("model", "target", 200);
		JPanel vegnPanel = vegnTP.getPanel();
		vegnPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup vegnTG = new JTaskPaneGroup();
		vegnTG.setSpecial(false);
		vegnTG.setExpanded(true);
		vegnTG.setTitle("VEGN-total");
		vegnTG.add(vegnPanel);
		rightJTP.add(vegnTG);

		targetPanel.add(leftJTP);
		targetPanel.add(rightJTP);
		
		targetPanel.setPreferredSize(new Dimension(420, 900));
		return targetPanel;
	}

	private JPanel getSstatePanel() {
		JPanel targetPanel = new JPanel();
		targetPanel.setLayout(new BoxLayout(targetPanel, BoxLayout.X_AXIS));

		JTaskPane leftJTP = new JTaskPane();

		dmosscTP = new PlotterMode2("model", "target", 1000);
		JPanel dmosscPanel = dmosscTP.getPanel();
		dmosscPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup dmosscTG = new JTaskPaneGroup();
		dmosscTG.setSpecial(false);
		dmosscTG.setExpanded(true);
		dmosscTG.setTitle("dead Moss C");
		dmosscTG.add(dmosscPanel);
		leftJTP.add(dmosscTG);

		fibsoilcTP = new PlotterMode2("model", "target", 1000);
		JPanel fibsoilcPanel = fibsoilcTP.getPanel();
		fibsoilcPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup fibsoilcTG = new JTaskPaneGroup();
		fibsoilcTG.setSpecial(false);
		fibsoilcTG.setExpanded(true);
		fibsoilcTG.setTitle("SOMC-fibrous");
		fibsoilcTG.add(fibsoilcPanel);
		leftJTP.add(fibsoilcTG);

		humsoilcTP = new PlotterMode2("model", "target", 1000);
		JPanel humsoilcPanel = humsoilcTP.getPanel();
		humsoilcPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup humsoilcTG = new JTaskPaneGroup();
		humsoilcTG.setSpecial(false);
		humsoilcTG.setExpanded(true);
		humsoilcTG.setTitle("SOMC-amorphous");
		humsoilcTG.add(humsoilcPanel);
		leftJTP.add(humsoilcTG);

		minesoilcTP = new PlotterMode2("model", "target", 1000);
		JPanel minesoilcPanel = minesoilcTP.getPanel();
		minesoilcPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup minesoilcTG = new JTaskPaneGroup();
		minesoilcTG.setSpecial(false);
		minesoilcTG.setExpanded(true);
		minesoilcTG.setTitle("SOMC-mineral");
		minesoilcTG.add(minesoilcPanel);
		leftJTP.add(minesoilcTG);

		soilcTP = new PlotterMode2("model", "target", 1000);
		JPanel soilcPanel = soilcTP.getPanel();
		soilcPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup soilcTG = new JTaskPaneGroup();
		soilcTG.setSpecial(false);
		soilcTG.setExpanded(true);
		soilcTG.setTitle("SOMC-total");
		soilcTG.add(soilcPanel);
		leftJTP.add(soilcTG);

		///
		JTaskPane rightJTP = new JTaskPane();

		mossthickTP = new PlotterMode1("model", 1000);
		JPanel mossthickPanel = mossthickTP.getPanel();
		mossthickPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mossthickTG = new JTaskPaneGroup();
		mossthickTG.setSpecial(false);
		mossthickTG.setExpanded(true);
		mossthickTG.setTitle("Ground-Moss-Thickness");
		mossthickTG.add(mossthickPanel);
		rightJTP.add(mossthickTG);

		peatthickTP = new PlotterMode2("fibrous", "amorphous",  1000);
		JPanel peatthickPanel = peatthickTP.getPanel();
		peatthickPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup peatthickTG = new JTaskPaneGroup();
		peatthickTG.setSpecial(false);
		peatthickTG.setExpanded(true);
		peatthickTG.setTitle("Ground-OSL");
		peatthickTG.add(peatthickPanel);
		rightJTP.add(peatthickTG);

		orgnTP = new PlotterMode2("model", "target", 1000);
		JPanel orgnPanel = orgnTP.getPanel();
		orgnPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup orgnTG = new JTaskPaneGroup();
		orgnTG.setSpecial(false);
		orgnTG.setExpanded(true);
		orgnTG.setTitle("Soil N");
		orgnTG.add(orgnPanel);
		rightJTP.add(orgnTG);

		avlnTP = new PlotterMode2("model", "target", 1000);
		JPanel avlnPanel = avlnTP.getPanel();
		avlnPanel.setPreferredSize(new Dimension(330, 125));

		JTaskPaneGroup avlnTG = new JTaskPaneGroup();
		avlnTG.setSpecial(false);
		avlnTG.setExpanded(true);
		avlnTG.setTitle("Soil Avail. N");
		avlnTG.add(avlnPanel);
		rightJTP.add(avlnTG);

		targetPanel.add(leftJTP);
		targetPanel.add(rightJTP);
		
		targetPanel.setPreferredSize(new Dimension(420, 900));
		return targetPanel;
	}

	private JPanel getMonthPanel() {
		JPanel targetPanel = new JPanel();
		targetPanel.setLayout(new BoxLayout(targetPanel, BoxLayout.X_AXIS));

		JTaskPane leftJTP = new JTaskPane();
		
		m_vcfluxTP = new PlotterMode3("GPPsim", "NPPsim", "LTRFsim", 36);
		JPanel mvcfluxPanel = m_vcfluxTP.getPanel();
		mvcfluxPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvcfluxTG = new JTaskPaneGroup();
		mvcfluxTG.setSpecial(false);
		mvcfluxTG.setExpanded(true);
		mvcfluxTG.setTitle("Veg. C fluxes");
		mvcfluxTG.add(mvcfluxPanel);
		leftJTP.add(mvcfluxTG);

		m_vegclTP = new PlotterMode1("modeled", 36);
		JPanel mvegclPanel = m_vegclTP.getPanel();
		mvegclPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvegclTG = new JTaskPaneGroup();
		mvegclTG.setSpecial(false);
		mvegclTG.setExpanded(true);
		mvegclTG.setTitle("VEGC-leaf");
		mvegclTG.add(mvegclPanel);
		leftJTP.add(mvegclTG);

		m_vegcsTP = new PlotterMode1("modeled", 36);
		JPanel mvegcsPanel = m_vegcsTP.getPanel();
		mvegcsPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvegcsTG = new JTaskPaneGroup();
		mvegcsTG.setSpecial(false);
		mvegcsTG.setExpanded(true);
		mvegcsTG.setTitle("VEGC-stem");
		mvegcsTG.add(mvegcsPanel);
		leftJTP.add(mvegcsTG);

		m_vegcrTP = new PlotterMode1("modeled", 36);
		JPanel mvegcrPanel = m_vegcrTP.getPanel();
		mvegcrPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvegcrTG = new JTaskPaneGroup();
		mvegcrTG.setSpecial(false);
		mvegcrTG.setExpanded(true);
		mvegcrTG.setTitle("VEGC-root");
		mvegcrTG.add(mvegcrPanel);
		leftJTP.add(mvegcrTG);

		m_scfluxTP = new PlotterMode2("tLTRFsim", "RHsim", 36);
		JPanel mscfluxPanel = m_scfluxTP.getPanel();
		mscfluxPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mscfluxTG = new JTaskPaneGroup();
		mscfluxTG.setSpecial(false);
		mscfluxTG.setExpanded(true);
		mscfluxTG.setTitle("Soil C fluxes");
		mscfluxTG.add(mscfluxPanel);
		leftJTP.add(mscfluxTG);

		///
		JTaskPane rightJTP = new JTaskPane();

		m_vnfluxTP = new PlotterMode2("Nuptake", "Nltrf", 24);
		JPanel mvnfluxPanel = m_vnfluxTP.getPanel();
		mvnfluxPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvnfluxTG = new JTaskPaneGroup();
		mvnfluxTG.setSpecial(false);
		mvnfluxTG.setExpanded(true);
		mvnfluxTG.setTitle("Veg. N fluxes");
		mvnfluxTG.add(mvnfluxPanel);
		rightJTP.add(mvnfluxTG);

		m_vegnlTP = new PlotterMode2("labile", "leaf", 24);
		JPanel mvegnlPanel = m_vegnlTP.getPanel();
		mvegnlPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvegnlTG = new JTaskPaneGroup();
		mvegnlTG.setSpecial(false);
		mvegnlTG.setExpanded(true);
		mvegnlTG.setTitle("VEGN-leaf/labile");
		mvegnlTG.add(mvegnlPanel);
		rightJTP.add(mvegnlTG);

		m_vegnsTP = new PlotterMode1("modeled", 24);
		JPanel mvegnsPanel = m_vegnsTP.getPanel();
		mvegnsPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvegnsTG = new JTaskPaneGroup();
		mvegnsTG.setSpecial(false);
		mvegnsTG.setExpanded(true);
		mvegnsTG.setTitle("VEGN-stem");
		mvegnsTG.add(mvegnsPanel);
		rightJTP.add(mvegnsTG);

		m_vegnrTP = new PlotterMode1("modeled", 24);
		JPanel mvegnrPanel = m_vegnrTP.getPanel();
		mvegnrPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup mvegnrTG = new JTaskPaneGroup();
		mvegnrTG.setSpecial(false);
		mvegnrTG.setExpanded(true);
		mvegnrTG.setTitle("VEGN-root");
		mvegnrTG.add(mvegnrPanel);
		rightJTP.add(mvegnrTG);
		
		m_snfluxTP = new PlotterMode4("tNuptake", "tNltrf", "netNmin","Nimmob",24);
		JPanel msnfluxPanel = m_snfluxTP.getPanel();
		msnfluxPanel.setPreferredSize(new Dimension(330, 125));
		JTaskPaneGroup msnfluxTG = new JTaskPaneGroup();
		msnfluxTG.setSpecial(false);
		msnfluxTG.setExpanded(true);
		msnfluxTG.setTitle("Soil N fluxes");
		msnfluxTG.add(msnfluxPanel);
		rightJTP.add(msnfluxTG);

		targetPanel.add(leftJTP);
		targetPanel.add(rightJTP);
		
		targetPanel.setPreferredSize(new Dimension(420, 900));
		return targetPanel;
	}

	public void reset() {
		ingnppTP.reset();
		gnppTP.reset();
		ltrfalcTP.reset();
		rhTP.reset();

		innuptakeTP.reset();
		nuptakeTP.reset();
		sorgnioTP.reset();
		soilnminTP.reset();
		
		vegclTP.reset();
		vegcsTP.reset();
		vegcrTP.reset();
		vegcTP.reset();
		
		vegnlTP.reset();
		vegnsTP.reset();
		vegnrTP.reset();
		vegnTP.reset();

		dmosscTP.reset();
		fibsoilcTP.reset();
		humsoilcTP.reset();
		minesoilcTP.reset();
		soilcTP.reset();
		
		mossthickTP.reset();
		peatthickTP.reset();
		avlnTP.reset();
		orgnTP.reset();
		
		m_vegclTP.reset();
		m_vegcsTP.reset();
		m_vegcrTP.reset();
		m_vcfluxTP.reset();
		m_scfluxTP.reset();
		
		m_vegnlTP.reset();
		m_vegnsTP.reset();
		m_vegnrTP.reset();
		m_vnfluxTP.reset();
		m_snfluxTP.reset();

				
	}

}