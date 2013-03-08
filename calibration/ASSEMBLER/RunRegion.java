/*
 * RunRegion.java
 * 
 * Region-level initialization, run, and output (if any)
 * 		Note: the output modules are put here, so can be flexible for outputs
 * 
*/
package ASSEMBLER;

import TEMJNI.Region;

import DATA.DataRegion;
import INPUT.RegionInputer;

public class RunRegion {
  	public Region region = new Region();
	
	RegionInputer rinputer = new RegionInputer();
  	public DataRegion jrd = new DataRegion();
  	
  	public int reinit(int recid){
  		if (recid<0) return -1;
  		rinputer.getCO2(jrd);
  		
  		//
  		region.getRd().setAct_co2yr(jrd.act_co2yr);
  		region.getRd().setCo2year(jrd.co2year);
  		region.getRd().setCo2(jrd.co2);
  		
  		//
  		region.init();
  		region.getinitco2();

  		return 0;
  	};

}

