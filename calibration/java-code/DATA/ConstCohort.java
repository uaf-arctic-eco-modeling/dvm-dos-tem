package DATA;

import TEMJNI.temcore;

public class ConstCohort {

	public final static int NUM_CMT      = temcore.getNUM_CMT(); //
	public final static int NUM_PFT      = temcore.getNUM_PFT(); //
	public final static int NUM_PFT_PART = temcore.getNUM_PFT_PART(); //
	public final static int MAX_DRG_TYPE = temcore.getMAX_DRG_TYPE(); //
	public final static int NUM_FSEVR    = temcore.getNUM_FSEVR(); //
	public final static int NUM_FSEASON  = temcore.getNUM_FSEASON(); //
	public final static int NUM_FSIZE    = temcore.getNUM_FSIZE(); //

	public final static int MISSING_I    = temcore.getMISSING_I();    //missing value (INT) used in the code
	public final static float MISSING_F  = temcore.getMISSING_F();   //missing value (FLOAT) used in the code
	public final static double MISSING_D = temcore.getMISSING_D();   //missing value (DOUBLE) used in the code

}
