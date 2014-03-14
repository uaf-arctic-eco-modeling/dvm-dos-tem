package GUI;

public class Configurer{
	
	// for calibration use
	public String calibgcfile = "";
	public String iniparfile  = "";
	public String outparfile  = "";
	
	// controller information (default value)
	public int runmode = 1;
	public String controlfile= "";
  	public String casename   = "default";
  	public String configdir  = "config";
  	public String runchtfile = "";
	public String outputdir  = "";
  	public String reginputdir= "";
  	public String grdinputdir= "";
  	public String chtinputdir= "";

  	public String runstages  = "eq";
  	public String initmodes  = "default";
  	public String initialfile= "";
 
  	// options
  	public int changeclimate = 0;
  	public int changeco2     = 0; 	
  	public boolean updatelai  = false;   
  	public boolean useseverity= false;
  	
  	// output options
  	public int outstartyr = -9999;     //
  	public boolean outsiteday   = false;    //only for Single-site run
  	public boolean outsitemonth = false;    //only for Single-site run
  	public boolean outsiteyear  = false;    //only for Single-site run
   	public boolean outregn      = false;        //for multi-sites run (i.e., TEMregioner)
 	
  	public boolean OGRAPH       = false;   //only if no file output
  	public boolean OBGRAPH      = false;   //showing bio. var. graphs only if no file output
  	public boolean OPGRAPH      = false;   //showing phy. var. graphs only if no file output
  	
  	public int chtidinput = -9999; // input chtid
	
	//
  	public static int I_CHTID=0;
  	public static int I_INITCHTID=1;
	public static int I_GRDID=2;
	public static int I_CLMID=3;
	public static int I_VEGID=4;
	public static int I_FIREID=5;
	public static int I_CMTTYPE=6;

	//PFT index
	public static int I_PFT[] ={0, 1, 2, 3, 4, 5, 6, 7, 8, 9};

	//calibratible Parameter Index (in table)
	public static int I_CMAX   =0;
	public static int I_NMAX   =1;
	public static int I_CFALLL =2;
	public static int I_CFALLS =3;
	public static int I_CFALLR =4;
	public static int I_NFALLL =5;
	public static int I_NFALLS =6;
	public static int I_NFALLR =7;
	public static int I_KRA    =8;
	public static int I_KRBL   =9;
	public static int I_KRBS   =10;
	public static int I_KRBR   =11;
	public static int I_FRG    =12;
    // one row empty as break line	
	public static int I_MICBNUP =14;
	public static int I_KDCMOSS =15;
	public static int I_KDCRAWC =16;
	public static int I_KDCSOMA =17;
	public static int I_KDCSOMPR=18;
	public static int I_KDCSOMCR=19;
 
	//BGC targetted flux/state variable Index (in table)
	public static int I_GPPt    =0;
	public static int I_INNPPt  =1;
	public static int I_NPPt    =2;
	public static int I_NUPTAKEt=3;
    // one row empty as break line
	public static int I_VEGCLt =5;
	public static int I_VEGCSt =6;
	public static int I_VEGCRt =7;
	public static int I_VEGNLt =8;
	public static int I_VEGNSt =9;
	public static int I_VEGNRt =10;
       // one row empty as break line
	public static int I_DMOSSCt   =12;
	public static int I_FIBSOILCt =13;
	public static int I_HUMSOILCt =14;
	public static int I_MINESOILCt=15;
	public static int I_SOILNt    =16;
	public static int I_AVLNt     =17;
	
	//BGC intial state variable Index (in table)
	public static int I_VEGCL =0;
	public static int I_VEGCS =1;
	public static int I_VEGCR =2;
	public static int I_VEGNL =3;
	public static int I_VEGNS =4;
	public static int I_VEGNR =5;
	public static int I_DEADC =6;
	public static int I_DEADN =7;
       // one row empty as break line
	public static int I_DMOSSTHICK =9;
	public static int I_FIBTHICK   =10;
	public static int I_HUMTHICK   =11;
	public static int I_DMOSSC     =12;
	public static int I_FIBSOILC   =13;
	public static int I_HUMSOILC   =14;
	public static int I_MINESOILC  =15;
	public static int I_SOILN      =16;
	public static int I_AVLN       =17;

	public Configurer(){
		 
	}	
	
}