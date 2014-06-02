package DATA;

public class DataRestart {

	public int chtid;
	
    // atm
	public int dsr;
	public double firea2sorgn;

	//vegegetation
	public int numpft;
	public int ysf;

	public int ifwoody[] = new int [ConstCohort.NUM_PFT];                  // - 'veg_dim'
	public int ifdeciwoody[] = new int [ConstCohort.NUM_PFT];
	public int ifperenial[] = new int [ConstCohort.NUM_PFT];
	public int ifvascular[] = new int [ConstCohort.NUM_PFT];
	public int vegage[] = new int [ConstCohort.NUM_PFT];
	public double vegcov[] = new double [ConstCohort.NUM_PFT];
	public double lai[] = new double [ConstCohort.NUM_PFT];
	public double rootfrac[][] = new double [ConstLayer.MAX_ROT_LAY][ConstCohort.NUM_PFT];

	public double vegwater[] = new double [ConstCohort.NUM_PFT];             //canopy water - 'vegs_env'
	public double vegsnow[] = new double [ConstCohort.NUM_PFT];              //canopy snow  - 'vegs_env'

	public double vegc[][] = new double [ConstCohort.NUM_PFT_PART][ConstCohort.NUM_PFT];   // - 'vegs_bgc'
	public double labn[] = new double [ConstCohort.NUM_PFT];
	public double strn[][] = new double [ConstCohort.NUM_PFT_PART][ConstCohort.NUM_PFT];
	public double deadc[] = new double [ConstCohort.NUM_PFT];
	public double deadn[] = new double [ConstCohort.NUM_PFT];
	public double unnormleaf[] = new double [ConstCohort.NUM_PFT];

    public double toptA[][] = new double [10][ConstCohort.NUM_PFT];           // this is for f(temp) in GPP to calculate the mean of the 10 previous values

    public double eetmxA[][] = new double [10][ConstCohort.NUM_PFT];           // this is for f(phenology) in GPP to calculate the mean of the 10 previous values
    public double petmxA[][] = new double [10][ConstCohort.NUM_PFT];
    public double unnormleafmxA[][] = new double [10][ConstCohort.NUM_PFT];

    public double prvfoliagemxA[] = new double [ConstCohort.NUM_PFT];        // this is for f(foliage) in GPP to be sure f(foliage) not going down

    //snow
    public int numsnwl;
    public double snwextramass;
    public double TSsnow[] = new double [ConstLayer.MAX_SNW_LAY];
    public double DZsnow[] = new double [ConstLayer.MAX_SNW_LAY]; 
    public double LIQsnow[] = new double [ConstLayer.MAX_SNW_LAY];
    public double RHOsnow[] = new double [ConstLayer.MAX_SNW_LAY]; 
    public double ICEsnow[] = new double [ConstLayer.MAX_SNW_LAY]; 
    public double AGEsnow[] = new double [ConstLayer.MAX_SNW_LAY];

    //ground-soil
    public int numsl;
    public double ald;
    public int permafrost;
    public double watertab;

    public double DZsoil[] = new double [ConstLayer.MAX_SOI_LAY];
    public int TYPEsoil[] = new int [ConstLayer.MAX_SOI_LAY];
    public double TSsoil[] = new double [ConstLayer.MAX_SOI_LAY]; 
    public double LIQsoil[] = new double [ConstLayer.MAX_SOI_LAY]; 
    public double ICEsoil[] = new double [ConstLayer.MAX_SOI_LAY];
    public int FROZENsoil[] = new int [ConstLayer.MAX_SOI_LAY]; 
    public int TEXTUREsoil[] = new int [ConstLayer.MAX_SOI_LAY];

    public double TSrock[] = new double [ConstLayer.MAX_ROC_LAY]; 
    public double DZrock[] = new double [ConstLayer.MAX_ROC_LAY];

    public double frontZ[] = new double [ConstLayer.MAX_NUM_FNT];
    public int frontFT[] = new int [ConstLayer.MAX_NUM_FNT];
     
    public double wdebrisc;
    public double rawc[] = new double [ConstLayer.MAX_SOI_LAY];
    public double soma[] = new double [ConstLayer.MAX_SOI_LAY];
    public double sompr[] = new double [ConstLayer.MAX_SOI_LAY];
    public double somcr[] = new double [ConstLayer.MAX_SOI_LAY];

    public double wdebrisn;
    public double orgn[] = new double [ConstLayer.MAX_SOI_LAY];
    public double avln[] = new double [ConstLayer.MAX_SOI_LAY];

    public double kdrawc[] = new double [ConstLayer.MAX_SOI_LAY];        //input material C/N (already) adjusted kd
    public double kdsoma[] = new double [ConstLayer.MAX_SOI_LAY];
    public double kdsompr[] = new double [ConstLayer.MAX_SOI_LAY];
    public double kdsomcr[] = new double [ConstLayer.MAX_SOI_LAY];
   	
};

