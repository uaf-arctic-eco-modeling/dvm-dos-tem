package GUI;

//from cpp (for getting instant data)
import javax.swing.JTable;

import TEMJNI.CohortData;
import TEMJNI.EnvData;
import TEMJNI.BgcData;

//GUI
import GUI.BioVariablePlotter;
import GUI.PhyVariablePlotter;

public class PlotterUpdate {
		
	BioVariablePlotter var1plotter;
	PhyVariablePlotter var2plotter;
	JTable targetTB; 
	
	// methods	

	public void setPlotter(BioVariablePlotter bvp){
		var1plotter = bvp;
	}

	public void setPlotter2(PhyVariablePlotter pvp){
		var2plotter = pvp;
	}
	
	public void setTargetTB(JTable targettbp) {
		targetTB = targettbp;
	}
	
	public void updateYlyBioGraph(int yrcnt, CohortData cd, BgcData pftbd, int ipft, BgcData allbd){		//update plots

		if(yrcnt%1 ==0 && BioVariablePlotter.f.isVisible()){
			 
			double x = yrcnt;
			double y1 = 0.0, y2 = 0.0, y3 = 0.0, y4 = 0.0;
			 
			////////////// fluxes /////////////////////
			// the following is for 1 specified pft
			y1 = pftbd.getY_a2v().getIngppall();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_GPPt, ipft+1));		 
			y3 = pftbd.getY_a2v().getInnppall();
		    y4 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_INNPPt, ipft+1));		 
			var1plotter.ingnppTP.addPoint(x, y1, y2, y3, y4);
							
			y1 = pftbd.getY_a2v().getGppall();
			y2 = pftbd.getY_a2v().getNppall();
		    y3 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_NPPt, ipft+1));		 
			var1plotter.gnppTP.addPoint(x, y1, y2, y3);

			y1 = pftbd.getY_v2soi().getLtrfalcall();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_NPPt, ipft+1));	// litterfall's target is NPP	 
			var1plotter.ltrfalcTP.addPoint(x, y1, y2);
			
			y1 = pftbd.getY_soi2v().getInnuptake();
			var1plotter.innuptakeTP.addPoint(x, y1);
			
			y1 = pftbd.getY_soi2v().getSnuptakeall()+pftbd.getY_soi2v().getLnuptake();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_NUPTAKEt, ipft+1));	 
			var1plotter.nuptakeTP.addPoint(x, y1, y2);

			// The following are for ALL pfts
			y1 = allbd.getY_soi2a().getRhtot();
			y2=0;
			for (int ip=0; ip<targetTB.getColumnCount()-1; ip++){
				if (cd.getM_veg().getVegcov()[ip]>0.) {
					y2 += Double.valueOf((String)targetTB.getValueAt(Configurer.I_NPPt, ip+1));  // Soil heteorotrophic res. target is NPP
				}  
			}
			// So, basically at equilibrium, NPP = LitterFall = RH
			var1plotter.rhTP.addPoint(x, y1, y2);

			y1 = allbd.getY_v2soi().getLtrfalnall();
			y2 = allbd.getY_soi2soi().getNetnminsum();
			var1plotter.sorgnioTP.addPoint(x, y1, y2);

			y1 = allbd.getY_soi2soi().getNetnminsum();
			y2 = allbd.getY_soi2soi().getNimmobsum();
			var1plotter.soilnminTP.addPoint(x, y1+y2, y2);	
			
			////////////// Vegetation States (specified PFT) /////////////////////
			y1 = pftbd.getY_vegs().getC()[0];
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_VEGCLt, ipft+1));	 
			y3 = y2;
			var1plotter.vegclTP.addPoint(x, y1, y2);		
			
			y1 = pftbd.getY_vegs().getC()[1];
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_VEGCSt, ipft+1));	 
			y3 += y2;
			var1plotter.vegcsTP.addPoint(x, y1, y2);
					
			y1 = pftbd.getY_vegs().getC()[2];
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_VEGCRt, ipft+1));	 
			y3 += y2;
			var1plotter.vegcrTP.addPoint(x, y1, y2);

			y1 = pftbd.getY_vegs().getCall();
			var1plotter.vegcTP.addPoint(x, y1, y3);
			
			//
			y1 = pftbd.getY_vegs().getStrn()[0];
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_VEGNLt, ipft+1));	 
			y3 = y2;
			var1plotter.vegnlTP.addPoint(x, y1, y2);		
			
			y1 = pftbd.getY_vegs().getStrn()[1];
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_VEGNSt, ipft+1));	 
			y3 += y2;
			var1plotter.vegnsTP.addPoint(x, y1, y2);
					
			y1 = pftbd.getY_vegs().getStrn()[2];
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_VEGNRt, ipft+1));	 
			y3 += y2;
			var1plotter.vegnrTP.addPoint(x, y1, y2);

			y1 = pftbd.getY_vegs().getNall();
			var1plotter.vegnTP.addPoint(x, y1, y3);
			
			///////////// Soil States (all PFTs) ///////////////////////////
			y1 = allbd.getY_sois().getDmossc();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_DMOSSCt, 1));	 
			var1plotter.dmosscTP.addPoint(x, y1, y2);		

			y1 = allbd.getY_soid().getShlwc();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_FIBSOILCt, 1));	 
			y3 = y1;
		    y4 = y2;
			var1plotter.fibsoilcTP.addPoint(x, y1, y2);		

			y1 = allbd.getY_soid().getDeepc();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_HUMSOILCt, 1));	 
			y3+= y1;
			y4+= y2;
			var1plotter.humsoilcTP.addPoint(x, y1, y2);		
	
			y1 = allbd.getY_soid().getMineac() + allbd.getY_soid().getMinebc()
					+allbd.getY_soid().getMinecc();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_MINESOILCt, 1));	 
			y3+= y1;
			y4+= y2;
			var1plotter.minesoilcTP.addPoint(x, y1, y2);		

			var1plotter.soilcTP.addPoint(x, y3, y4);
			
			//
			y1 = cd.getY_soil().getMossthick();
			var1plotter.mossthickTP.addPoint(x, y1);				

			y1 = cd.getY_soil().getShlwthick();
			y2 = cd.getY_soil().getDeepthick();
			var1plotter.peatthickTP.addPoint(x, y1, y2);				

			y1 = allbd.getY_soid().getOrgnsum();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_SOILNt, 1));	 
			var1plotter.orgnTP.addPoint(x, y1, y2);				

			y1 = allbd.getY_soid().getAvlnsum();
		    y2 = Double.valueOf((String)targetTB.getValueAt(Configurer.I_AVLNt, 1));	 
			var1plotter.avlnTP.addPoint(x, y1, y2);				

		}
		
	};
		
	public void updateMlyBioGraph(int yrcnt, int im, BgcData pftbd, BgcData allbd){		//update plots
		if(BioVariablePlotter.f.isVisible()){
			 
			double x = (double)yrcnt+(double)im/12.0;
			double y1 = 0.0, y2 = 0.0, y3 = 0.0, y4 = 0.0;
			 
			// 1 pft C/N (mainly for veg)
							
			y1 = pftbd.getM_a2v().getGppall();
			y2 = pftbd.getM_a2v().getNppall();
			y3 = pftbd.getM_v2soi().getLtrfalcall();
			var1plotter.m_vcfluxTP.addPoint(x, y1, y2, y3);

			y1 = pftbd.getM_vegs().getC()[0];
			var1plotter.m_vegclTP.addPoint(x, y1);		
			
			y1 = pftbd.getM_vegs().getC()[1];
			var1plotter.m_vegcsTP.addPoint(x, y1);		
				
			y1 = pftbd.getM_vegs().getC()[2];
			var1plotter.m_vegcrTP.addPoint(x, y1);		
			
			y1 = pftbd.getM_soi2v().getSnuptakeall()+pftbd.getM_soi2v().getLnuptake();
			y2 = pftbd.getM_v2soi().getLtrfalnall();
			var1plotter.m_vnfluxTP.addPoint(x, y1, y2);

			y1 = pftbd.getM_vegs().getLabn();
			y2 = pftbd.getM_vegs().getStrn()[0];
			var1plotter.m_vegnlTP.addPoint(x, y1, y2);		
			
			y1 = pftbd.getM_vegs().getStrn()[1];
			var1plotter.m_vegnsTP.addPoint(x, y1);		
				
			y1 = pftbd.getM_vegs().getStrn()[2];
			var1plotter.m_vegnrTP.addPoint(x, y1);
			
			// all pfts - for soil
			y1 = allbd.getM_v2soi().getLtrfalcall();
			y2 = allbd.getM_soi2a().getRhtot();
			var1plotter.m_scfluxTP.addPoint(x, y1, y2);

			y1 = allbd.getM_soi2v().getSnuptakeall()+allbd.getM_soi2v().getLnuptake();
			y2 = allbd.getM_v2soi().getLtrfalnall();
			y3 = allbd.getM_soi2soi().getNetnminsum();
			y4 = allbd.getM_soi2soi().getNimmobsum();
			var1plotter.m_snfluxTP.addPoint(x, y1, y2, y3, y4);
						
		}	
	
	};

	public void updateYlyPhyGraph(int yrcnt, CohortData cd, EnvData alled){		//update plots
		
		if(PhyVariablePlotter.f.isVisible()){

		double x = yrcnt;
		double y1 = 0., y2 = 0., y3 = 0., y4 = 0.;
		
		//
		y1 = alled.getY_atms().getTa();
		y2 = alled.getY_soid().getTsave();
		var2plotter.ts1TP.addPoint(x, y1, y2);
		
		y1 = alled.getY_soid().getIcesum()/cd.getY_soil().getTotthick();
		y2 = alled.getY_soid().getLiqsum()/cd.getY_soil().getTotthick();
		var2plotter.vwc1TP.addPoint(x, y1, y2);
		
		y1 = alled.getY_l2a().getPet();
		y2 = alled.getY_l2a().getEet();
		var2plotter.etTP.addPoint(x, y1, y2);
		
		y1 = alled.getY_a2l().getRnfl();
		y2 = alled.getY_a2l().getSnfl();
		y3 = alled.getY_soi2l().getQover();
		y4 = alled.getY_soi2l().getQdrain();
		var2plotter.qinoutTP.addPoint(x, y1, y2, y3, y4);;
				
		y1 = alled.getY_soid().getTshlw();
		y2 = alled.getY_soid().getTdeep();
		y3 = alled.getY_soid().getTminea();
		y3 = alled.getY_soid().getTmineb();
		var2plotter.ts2TP.addPoint(x, y1, y2, y3, y4);;

		y1 = alled.getY_soid().getVwcshlw();
		y2 = alled.getY_soid().getVwcdeep();
		y3 = alled.getY_soid().getVwcminea();
		y3 = alled.getY_soid().getVwcmineb();
		var2plotter.vwc2TP.addPoint(x, y1, y2, y3, y4);;

		y1 = alled.getY_soid().getAld(); if (y1<=-9999) y1 = cd.getY_soil().getTotthick();
		y2 = alled.getY_sois().getWatertab();
		y3 = alled.getY_sois().getDraindepth();
		var2plotter.aldwtbTP.addPoint(x, y1, y2, y3);;

		y1 = cd.getY_soil().getMossthick();
		y2 = cd.getY_soil().getShlwthick();
		y3 = cd.getY_soil().getDeepthick();
		var2plotter.peatthickTP.addPoint(x, y1, y2, y3);

		}
		
	};
	
	public void updateMlyPhyGraph(int yrcnt, int im, EnvData alled){		//update plots

		if(PhyVariablePlotter.f.isVisible()){

		double x = (double)yrcnt+(double)im/12.;
		double y1 = 0., y2 = 0., y3 = 0.;
		
		//
		y1 = alled.getM_a2l().getRnfl();
		y2 = alled.getM_a2l().getSnfl();
		var2plotter.mpptTP.addPoint(x, y1, y2);
		
		y1 = alled.getM_l2a().getPet();
		y2 = alled.getM_l2a().getEet();
		var2plotter.metTP.addPoint(x, y1, y2);

		y1 = alled.getM_soi2l().getQover();
		y2 = alled.getM_soi2l().getQdrain();
		var2plotter.mqoutTP.addPoint(x, y1, y2);

		y1 = alled.getM_sois().getWatertab();
		y2 = alled.getM_sois().getDraindepth();
		var2plotter.mwtbdrgdTP.addPoint(x, y1, y2);
		
		y1 = alled.getM_soid().getVwcshlw();
		y2 = alled.getM_soid().getVwcdeep();
		var2plotter.mvwc1TP.addPoint(x, y1, y2);

		y1 = alled.getM_soid().getVwcminea();
		y2 = alled.getM_soid().getVwcmineb();
		y3 = alled.getM_soid().getVwcminec();
		var2plotter.mvwc2TP.addPoint(x, y1, y2, y3);

		//
		y1 = alled.getM_a2l().getPar();
		var2plotter.mppfdTP.addPoint(x, y1);

		y1 = alled.getM_atms().getTa();
		var2plotter.mtaTP.addPoint(x, y1);

		y1 = alled.getM_soid().getAld();
		y2 = alled.getM_soid().getAlc();
		var2plotter.maldTP.addPoint(x, y1, y2);

		y1 = alled.getM_soid().getTshlw();
		y2 = alled.getM_soid().getTdeep();
		var2plotter.mts1TP.addPoint(x, y1, y2);

		y1 = alled.getM_soid().getTminea();
		y2 = alled.getM_soid().getTmineb();
		y3 = alled.getM_soid().getTminec();
		var2plotter.mts2TP.addPoint(x, y1, y2, y3);
		
		}
	};
	
}
