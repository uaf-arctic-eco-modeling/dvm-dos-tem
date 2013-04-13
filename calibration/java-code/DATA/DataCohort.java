package DATA;

public class DataCohort{
  
	// real ID in the .nc data files
	public int chtid;
 	public int year;
 	public int month;
 	public int day;

	public int cmttype;   // vegetation community type
	public int ysdist;    // years since last disturbance
	public boolean hasnonvascular;

	public int act_vegset;
	public int vegyear[]   = new int[ConstTime.MAX_VEG_SET];
	public int vegtype[]   = new int[ConstTime.MAX_VEG_SET];
	public double vegfrac[]= new double[ConstTime.MAX_VEG_SET];

	public int act_fireset;
	public int fireyear[]    = new int[ConstTime.MAX_FIR_OCRNUM];
	public int fireseason[]  = new int[ConstTime.MAX_FIR_OCRNUM];
	public int firesize[]    = new int[ConstTime.MAX_FIR_OCRNUM];
	public int fireseverity[]= new int[ConstTime.MAX_FIR_OCRNUM];

    public int act_atm_drv_yr;
    public float tair[] = new float[ConstTime.MAX_ATM_DRV_YR*12];
    public float prec[] = new float[ConstTime.MAX_ATM_DRV_YR*12];
	public float nirr[] = new float[ConstTime.MAX_ATM_DRV_YR*12];
	public float vapo[] = new float[ConstTime.MAX_ATM_DRV_YR*12];

};

