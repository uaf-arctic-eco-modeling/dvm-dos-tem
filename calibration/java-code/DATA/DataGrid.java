package DATA;

public class DataGrid {
  
    public int gid;
    public float lat;
    public float lon;
    public float alldaylengths[] = new float[365]; 

    public int drainageid;
	public int drgtype;

    public int soilid;
    public int topsoil;
    public int botsoil;

    public int gfireid;
    public int fri;
	public double pfsize[]   = new double [ConstCohort.NUM_FSIZE];
	public double pfseason[] = new double [ConstCohort.NUM_FSEASON];

};

