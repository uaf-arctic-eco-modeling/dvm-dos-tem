package ASSEMBLER;

//from java
import DATA.ConstTime;

//GUI
import GUI.PlotterUpdate;
import TEMJNI.TEMccjava;
import TEMJNI.soipar_cal;
import TEMJNI.vegpar_cal;
import TEMJNI.BgcData;
import TEMJNI.EnvData;

public class TEMeqrunner implements Runnable{
		
	// model-run entities
	public Runner eqrunner;
	
	// model options
	public boolean friderived = false;
	
	// parameters to be calibrated
	public int ipft;
	public vegpar_cal jvcalpar = new vegpar_cal();
	public soipar_cal jscalpar = new soipar_cal();

	public TEMccjava temcj = new TEMccjava();   //c++ module for data/module connection between java and temcore lib
	public BgcData jbd = new BgcData();  // these two are for extracting ONE PFT's 'bd' and 'ed' data
	public EnvData jed = new EnvData();
	
///////////////////////////////////////////////////////////////////////////////////////
	
	// Model Running process operations for calibration using GUI
	private boolean m_stop = true;
	private Thread m_thread;
	
	public PlotterUpdate plotting = new PlotterUpdate();
	
//////////////////////////////////////////////////////////////////////////////////////////
//The following TEM run is for calibration in TCGUI
/////////////////////////////////////////////////////////////////////////////////////////

	public int yrcnt =0;
	
	public void prerun(){
		
		//for calibration, only ONE run-cohort exists, AND must be "eq" run

		String controlfile = eqrunner.jconfigin.controlfile;
   	 	eqrunner.initInput(controlfile,"GUI");				
		eqrunner.initOutput();
		eqrunner.setupData();
		eqrunner.setupIDs();
		
		temcj.setCohort(eqrunner.runcht.cht);
		
		try {
			//read-in region-level data (Yuan: this is the portal for multiple region run, if needed in the future)
			int error = eqrunner.runreg.reinit(0);          //can be modified, if more than 1 record of data
			if (error!=0){
				System.out.println("problem in reinitialize regional-module");
				System.exit(-1);
			}
		
			//IDs for ONE single cohort
			int eqchtid = eqrunner.chtid;  // this is input from configurer in GUI
			eqrunner.runcht.cht.getCd().setChtid(eqchtid);
			
			// assgning the record no. for all needed data IDs to run 'chtid'
			// for 'siter', all record no. are in the first position of the lists
			// because, 'chtid' is the only one in 'runchtlist', which are synchorized with all the lists.
			eqrunner.rungrd.gridrecno  = eqrunner.reclistgrid.get(0);
			eqrunner.rungrd.drainrecno = eqrunner.reclistdrain.get(0);
			eqrunner.rungrd.soilrecno  = eqrunner.reclistsoil.get(0);
			eqrunner.rungrd.gfirerecno = eqrunner.reclistgfire.get(0);

			eqrunner.runcht.initrecno  = eqrunner.reclistinit.get(0);
			eqrunner.runcht.clmrecno   = eqrunner.reclistclm.get(0);
			eqrunner.runcht.vegrecno   = eqrunner.reclistveg.get(0);
			eqrunner.runcht.firerecno  = eqrunner.reclistfire.get(0);

			//getting the grided data for ONE single cohort
			error = eqrunner.rungrd.readData();
			if (error!=0){
				System.out.println("problem in reinitialize grid-module");
				System.exit(-1);
			}
				
			//getting the cohort data
			error = eqrunner.runcht.readData();

			error = eqrunner.runcht.reinit();

			if (error!=0) {
				System.out.println("Error for reinit cohort: "+ eqrunner.runcht.jcd.chtid +" - will exit! ");
				System.exit(-3);
			} else {
				System.out.println("cohort: " + eqrunner.runcht.jcd.chtid +" - will be running! ");
		   	 	
		   	 	yrcnt = 0;
			}

			//getting the default pft index (first PFT with vegcov > 0)
			ipft = 0;
	    	double[] vegcov = eqrunner.runcht.cht.getCd().getM_veg().getVegcov();	    	
	    	while (vegcov[ipft]<=0.0) {
	    		ipft+=1;
	    	}
		
		} catch (Exception ex) {
	  		System.err.println("Error in Runner::run() " + ex);
		} 

	        
	};

//--------------------------------------------------------------------------------------			
	//TEM run for updating calibration driver
	public void updatedriver(){					
		//
		eqrunner.runcht.cht.getTimer().reset();
		    	 		 	
		//Turn Env-Module only on
		eqrunner.runcht.cht.getMd().setEnvmodule(true);
		eqrunner.runcht.cht.getMd().setBgcmodule(false);
		eqrunner.runcht.cht.getMd().setDsbmodule(false);
		eqrunner.runcht.cht.getMd().setDslmodule(false);
		
		eqrunner.runcht.cht.getMd().setUpdatelai(false);
		eqrunner.runcht.cht.getFd().setYsf(1000);
		
		//option of dynamic soil organic layer thickness for testing code
		boolean dsl = false;
		float moss = 0.001f;
		float fib  = 0.02f;
		float hum  = 0.02f;

		System.out.println("TEM Env-Module only RUN ... ");

		for (int iyr=0; iyr<100; iyr++) {
			
			//reset soil organic layer thickness as desired
			if (dsl) {
				moss+=0.001;
//				fib+=0.005;
//				hum+=0.005;
				resetOMthickness(moss, fib, hum);
			}

			yearlyrun();
		}		
		
		System.out.println("Done!");
		
	};

	// non-controlled run
	public void yearlyrun(){					
						    
			System.out.println("TEM CALIBRATION RUN: year "+yrcnt);

			// process module calling
			int yrindex = eqrunner.runcht.cht.getTimer().getCurrentYearIndex();   //starting from 0
			eqrunner.runcht.cht.getCd().setYear(eqrunner.runcht.cht.getTimer().getCalendarYear());

			int usedatmyr = Math.min(ConstTime.MAX_ATM_DRV_YR, ConstTime.MAX_ATM_NOM_YR);
			eqrunner.runcht.cht.prepareDayDrivingData(yrindex, usedatmyr);

			for (int im=0; im<12;im++){

				int currmind=  im;
				eqrunner.runcht.cht.getCd().setMonth(im+1);
				int dinmcurr = ConstTime.DINM[im];

				eqrunner.runcht.cht.updateMonthly(yrindex, currmind, dinmcurr);
				eqrunner.runcht.cht.getTimer().advanceOneMonth();

				temcj.getData1pft(ipft);
				
				plotting.updateMlyBioGraph(yrcnt, im, temcj.getBd1pft(), eqrunner.runcht.cht.getBdall());
				plotting.updateMlyPhyGraph(yrcnt, im, eqrunner.runcht.cht.getEdall());
			}
			plotting.updateYlyBioGraph(yrcnt, eqrunner.runcht.cht.getCd(), temcj.getBd1pft(), ipft, eqrunner.runcht.cht.getBdall());
			plotting.updateYlyPhyGraph(yrcnt, eqrunner.runcht.cht.getCd(), eqrunner.runcht.cht.getEdall());
			
			yrcnt++;
			
	};

	//the following will reset soil organic layer thickness when called
	private void resetOMthickness(float mossthick, float fibthick, float humthick){
	
		eqrunner.runcht.cht.getChtlu().setInitdmossthick(mossthick);
		eqrunner.runcht.cht.getChtlu().setInitfibthick(fibthick);
		eqrunner.runcht.cht.getChtlu().setInithumthick(humthick);
		
		temcj.setInitSbState();
	};
	
//-----------------------------------------------------------------------------
//TEM calibration run	
	public void run(){					
			
		//GUI error message
		if (Thread.currentThread() != this.m_thread) {
			throw new IllegalStateException(
			"you cannot start an own thread for running TEM");
		}

		//thread status initialization
		this.m_stop = false;
				    
		while (!this.m_stop){	
			System.out.println("TEM CALIBRATION RUN: year "+yrcnt);

			//reset calibration parameters
			//temcj.setVbCalPar1pft(ipft, jvcalpar);
			//temcj.setSbCalPar(jscalpar);

   	 		//reset disturbance options
			eqrunner.runcht.cht.getMd().setFriderived(friderived);
			if (!friderived) eqrunner.runcht.cht.getFd().setYsf(1000);			
			if (eqrunner.runcht.cht.getGd().getFri()<=0) eqrunner.runcht.cht.getFd().setYsf(1000);			
			
			int yrindex = eqrunner.runcht.cht.getTimer().getCurrentYearIndex();   //starting from 0
			eqrunner.runcht.cht.getCd().setYear(eqrunner.runcht.cht.getTimer().getCalendarYear());

			int usedatmyr = Math.min(ConstTime.MAX_ATM_DRV_YR, ConstTime.MAX_ATM_NOM_YR);
			eqrunner.runcht.cht.prepareDayDrivingData(yrindex, usedatmyr);

			for (int im=0; im<12;im++){

				int currmind=  im;
				eqrunner.runcht.cht.getCd().setMonth(im+1);
				int dinmcurr = ConstTime.DINM[im];

				eqrunner.runcht.cht.updateMonthly(yrindex, currmind, dinmcurr);
				eqrunner.runcht.cht.getTimer().advanceOneMonth();

				temcj.getData1pft(ipft);
				
				plotting.updateMlyBioGraph(yrcnt, im, temcj.getBd1pft(), eqrunner.runcht.cht.getBdall());
				plotting.updateMlyPhyGraph(yrcnt, im, eqrunner.runcht.cht.getEdall());
			}
			plotting.updateYlyBioGraph(yrcnt, eqrunner.runcht.cht.getCd(), temcj.getBd1pft(), ipft, eqrunner.runcht.cht.getBdall());
			plotting.updateYlyPhyGraph(yrcnt, eqrunner.runcht.cht.getCd(), eqrunner.runcht.cht.getEdall());

			yrcnt++;
			
			if (Thread.interrupted()) this.stop();
			if (yrcnt<500) {
				if (yrcnt%100==0) {
					try {
						Thread.sleep(100);
						this.stop();
					} catch (InterruptedException e) {
						this.stop();
					}
				}
			} else {
				if (yrcnt%500==0) {
					try {
						Thread.sleep(100);
						this.stop();
					} catch (InterruptedException e) {
						this.stop();
					}
				}
			}		
			
		}

	};

//////////////////////////////////////////////////////////////////////////////////////////
//The following are for controlling of model running process USING GUI
//////////////////////////////////////////////////////////////////////////////////////////		

	public void start() {
		if (this.m_stop) {
			this.m_thread = new Thread(this);
			this.m_thread.start();
		}
	};

	public void stop() {
		this.m_stop = true;
	};

	public void reset() {
		if (!this.m_stop) this.m_stop = true;
		this.m_thread = new Thread(this);
		
		System.out.println("\n TEM RUN will be reset for a new Model Run ...");
		
	};
	
}
