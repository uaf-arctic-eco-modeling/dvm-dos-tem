package INPUT;
/*
 * 
 */
import java.io.File;
import java.io.IOException;

import ucar.ma2.Array;
import ucar.ma2.Index;
import ucar.nc2.NetcdfFile;
import ucar.nc2.Variable;

import DATA.ConstCohort;
import DATA.ConstLayer;
import DATA.DataRestart;

public class RestartInputer {
	
	Array chtidA;
	Array errcodeA;
	
	Array dsrA;
	Array firea2sorgnA;

	Array numpftA;
	Array ysfA;

	Array ifwoodyA;
	Array ifdeciwoodyA;
	Array ifperenialA;
	Array ifvascularA;
	Array vegageA;
	Array vegcovA;
	Array laiA;
	Array rootfracA;

	Array vegwaterA;
	Array vegsnowA;

	Array vegcA;
	Array labnA;
	Array strnA;
	Array deadcA;
	Array deadnA;
	Array unnormleafA;

    Array toptaA;

    Array eetmxaA;
    Array petmxaA;
    Array unnormleafmxaA;

    Array prvfoliagemxaA;

    Array numsnwlA;
    Array snwextramassA;
    Array TSsnowA;
    Array DZsnowA; 
    Array LIQsnowA;
    Array RHOsnowA; 
    Array ICEsnowA; 
    Array AGEsnowA;

    Array numslA;
    Array aldA;
    Array permafrostA;
    Array watertabA;

    Array DZsoilA;
    Array TYPEsoilA;
    Array TSsoilA; 
    Array LIQsoilA; 
    Array ICEsoilA;
    Array FROZENsoilA; 
    Array TEXTUREsoilA;

    Array TSrockA; 
    Array DZrockA;

    Array frontZA;
    Array frontFTA;
     
    Array wdebriscA;
    Array rawcA;
    Array somaA;
    Array somprA;
    Array somcrA;

    Array wdebrisnA;
    Array orgnA;
    Array avlnA;

    Array kdrawcA;        //input material C/N (already) adjusted kd
    Array kdsomaA;
    Array kdsomprA;
    Array kdsomcrA;

	public void init(String restartfile){
 	
		NetcdfFile ncfile = null;
		File file = new File(restartfile);
		if (file.exists()){
			try {
				ncfile = NetcdfFile.open(restartfile);

				Variable chtidV = ncfile.findVariable("CHTID");
				chtidA = chtidV.read();
				
				Variable dsrV = ncfile.findVariable("DSR"); 
				dsrA = dsrV.read();
				
				Variable firea2sorgnV = ncfile.findVariable("FIREA2SORGN"); 
				firea2sorgnA = firea2sorgnV.read();

				Variable numpftV = ncfile.findVariable("NUMPFT"); 
				numpftA = numpftV.read();
				
				Variable ysfV = ncfile.findVariable("YSF"); 
				ysfA = ysfV.read();

				Variable ifwoodyV = ncfile.findVariable("IFWOODY"); 
				ifwoodyA = ifwoodyV.read();
				
				Variable ifdeciwoodyV = ncfile.findVariable("IFDECIWOODY"); 
				ifdeciwoodyA = ifdeciwoodyV.read();
				
				Variable ifperenialV = ncfile.findVariable("IFPERENIAL"); 
				ifperenialA = ifperenialV.read();
				
				Variable ifvascularV = ncfile.findVariable("IFVASCULAR"); 
				ifvascularA = ifvascularV.read();
				
				Variable vegageV = ncfile.findVariable("VEGAGE"); 
				vegageA = vegageV.read();
				
				Variable vegcovV = ncfile.findVariable("VEGCOV"); 
				vegcovA = vegcovV.read();
				
				Variable laiV = ncfile.findVariable("LAI"); 
				laiA = laiV.read();
				
				Variable rootfracV = ncfile.findVariable("ROOTFRAC"); 
				rootfracA = rootfracV.read();

				Variable vegwaterV = ncfile.findVariable("VEGWATER");
				vegwaterA = vegwaterV.read();

				Variable vegsnowV = ncfile.findVariable("VEGSNOW"); 
				vegsnowA = vegsnowV.read();

				Variable vegcV = ncfile.findVariable("VEGC"); 
				vegcA = vegcV.read();

				Variable labnV = ncfile.findVariable("LABN"); 
				labnA = labnV.read();
				
				Variable strnV = ncfile.findVariable("STRN"); 
				strnA = strnV.read();
				
				Variable deadcV = ncfile.findVariable("DEADC"); 
				deadcA = deadcV.read();
				
				Variable deadnV = ncfile.findVariable("DEADN"); 
				deadnA = deadnV.read();
				
				Variable unnormleafV = ncfile.findVariable("UNNORMLEAF"); 
				unnormleafA = unnormleafV.read();

				Variable toptaV = ncfile.findVariable("TOPTA");  
				toptaA = toptaV.read();

				Variable eetmxaV = ncfile.findVariable("EETMXA");  
				eetmxaA = eetmxaV.read();
				
				Variable petmxaV = ncfile.findVariable("PETMXA");  
				petmxaA = petmxaV.read();
				
				Variable unnormleafmxaV = ncfile.findVariable("UNNORMLEAFMXA");  
				unnormleafmxaA = unnormleafmxaV.read();

				Variable prvfoliagemxaV = ncfile.findVariable("PRVFOLIAGEMXA");  
				prvfoliagemxaA = prvfoliagemxaV.read();

				//
		    	Variable numsnwlV = ncfile.findVariable("NUMSNWL"); 
		    	numsnwlA = numsnwlV.read();
	
		    	Variable snwextramassV = ncfile.findVariable("SNWEXTRAMASS"); 
		    	snwextramassA = snwextramassV.read();
			    
		    	Variable TSsnowV = ncfile.findVariable("TSsnow"); 
		    	TSsnowA = TSsnowV.read();
			    
		    	Variable DZsnowV = ncfile.findVariable("DZsnow"); 
		    	DZsnowA = DZsnowV.read(); 
			    
		    	Variable LIQsnowV = ncfile.findVariable("LIQsnow"); 
		    	LIQsnowA = LIQsnowV.read();
			    
		    	Variable RHOsnowV = ncfile.findVariable("RHOsnow"); 
		    	RHOsnowA = RHOsnowV.read(); 
			    
		    	Variable ICEsnowV = ncfile.findVariable("ICEsnow"); 
		    	ICEsnowA = ICEsnowV.read(); 
			    	
		    	Variable AGEsnowV = ncfile.findVariable("AGEsnow"); 
		    	AGEsnowA = AGEsnowV.read();

		    	//
		    	Variable numslV = ncfile.findVariable("NUMSL"); 
		    	numslA = numslV.read();

		    	Variable aldV = ncfile.findVariable("ALD"); 
		    	aldA = aldV.read();
			    
		    	Variable permafrostV = ncfile.findVariable("PERMAFROST"); 
		    	permafrostA = permafrostV.read();
			    
		    	Variable watertabV = ncfile.findVariable("WATERTAB"); 
		    	watertabA = watertabV.read();

			    Variable DZsoilV = ncfile.findVariable("DZsoil"); 
			    DZsoilA = DZsoilV.read();
			    
			    Variable TYPEsoilV = ncfile.findVariable("TYPEsoil"); 
			    TYPEsoilA = TYPEsoilV.read();
			    
			    Variable TSsoilV = ncfile.findVariable("TSsoil"); 
			    TSsoilA = TSsoilV.read(); 
			    
			    Variable LIQsoilV = ncfile.findVariable("LIQsoil"); 
			    LIQsoilA = LIQsoilV.read(); 
			    
			    Variable ICEsoilV = ncfile.findVariable("ICEsoil"); 
			    ICEsoilA = ICEsoilV.read();
			    
			    Variable FROZENsoilV = ncfile.findVariable("FROZENsoil"); 
			    FROZENsoilA = FROZENsoilV.read(); 
			    
			    Variable TEXTUREsoilV = ncfile.findVariable("TEXTUREsoil"); 
			    TEXTUREsoilA = TEXTUREsoilV.read();

			    Variable TSrockV = ncfile.findVariable("TSrock"); 
			    TSrockA = TSrockV.read(); 
			    
			    Variable DZrockV = ncfile.findVariable("DZrock"); 
			    DZrockA = DZrockV.read();

			    Variable frontZV = ncfile.findVariable("frontZ"); 
			    frontZA = frontZV.read();
			    
			    Variable frontFTV = ncfile.findVariable("frontFT"); 
			    frontFTA = frontFTV.read();
			     
			    Variable wdebriscV = ncfile.findVariable("WDEBRISC"); 
			    wdebriscA = wdebriscV.read();
			    
			    Variable rawcV = ncfile.findVariable("RAWC"); 
			    rawcA = rawcV.read();
			    
			    Variable somaV = ncfile.findVariable("SOMA"); 
			    somaA = somaV.read();
			    
			    Variable somprV = ncfile.findVariable("SOMPR"); 
			    somprA = somprV.read();
			    
			    Variable somcrV = ncfile.findVariable("SOMCR"); 
			    somcrA = somcrV.read();

			    Variable wdebrisnV = ncfile.findVariable("WDEBRISN"); 
			    wdebrisnA = wdebrisnV.read();
			    
			    Variable orgnV = ncfile.findVariable("ORGN"); 
			    orgnA = orgnV.read();
			    
			    Variable avlnV = ncfile.findVariable("AVLN"); 
			    avlnA = avlnV.read();

		    	Variable kdrawcV = ncfile.findVariable("KDRAWC"); 
		    	kdrawcA = kdrawcV.read(); 

		    	Variable kdsomaV = ncfile.findVariable("KDSOMA"); 
		    	kdsomaA = kdsomaV.read();
			    
		    	Variable kdsomprV = ncfile.findVariable("KDSOMPR"); 
		    	kdsomprA = kdsomprV.read();
			    
		    	Variable kdsomcrV = ncfile.findVariable("KDSOMCR"); 
		    	kdsomcrA = kdsomcrV.read();
		
			} catch (IOException ioe) {
				System.out.println(ioe.getMessage());
			} finally {
				if (ncfile != null) {
					try {
						ncfile.close();
					} catch (IOException ioee) {
						System.out.println(ioee.getMessage());
					}
				}
			}
		}else {   //file not exist
			System.out.println("Input file: "+restartfile+" NOT existed");
		}

	};
	
	//Yuan: RecordId is the record id (starting from ZERO), but not cohort id (chtid) in the .nc file
	public int getRecordId(int reschtid){

		Index ind = chtidA.getIndex();
		for (int i=0; i<(int)ind.getSize(); i++){
			int chtid = chtidA.getInt(ind.set(i));
			if (chtid == reschtid) return i;
		}	
			 
		return -1;
	}

	public void getErrcode(int errcode, int cid){
		Index ind = errcodeA.getIndex();
		errcode = errcodeA.getInt(ind.set(cid));
	}
	
	public void getRestartData(DataRestart resid, int cid) { 

		Index ind1 = dsrA.getIndex(); 
		resid.dsr = dsrA.getInt(ind1.set(cid));
		
		Index ind2 = firea2sorgnA.getIndex(); 
		resid.firea2sorgn = firea2sorgnA.getDouble(ind2.set(cid));

		Index ind3 = numpftA.getIndex(); 
		resid.numpft = numpftA.getInt(ind3.set(cid));
		
		Index ind4 = ysfA.getIndex(); 
		resid.ysf = ysfA.getInt(ind4.set(cid));

		for (int il = 0; il < ConstCohort.NUM_PFT; il++) {

			Index ind5 = ifwoodyA.getIndex(); 
			resid.ifwoody[il] = ifwoodyA.getInt(ind5.set(cid, il));
		
			Index ind6 = ifdeciwoodyA.getIndex(); 
			resid.ifdeciwoody[il] = ifdeciwoodyA.getInt(ind6.set(cid, il));
		
			Index ind7 = ifperenialA.getIndex(); 
			resid.ifperenial[il] = ifperenialA.getInt(ind7.set(cid, il));
		
			Index ind8 = ifvascularA.getIndex(); 
			resid.ifvascular[il] = ifvascularA.getInt(ind8.set(cid, il));
		
			Index ind9 = vegageA.getIndex(); 
			resid.vegage[il] = vegageA.getInt(ind9.set(cid, il));
		
			Index ind10 = vegcovA.getIndex(); 
			resid.vegcov[il] = vegcovA.getDouble(ind10.set(cid, il));
		
			Index ind11 = laiA.getIndex(); 
			resid.lai[il] = laiA.getDouble(ind11.set(cid, il));
		
			Index ind12 = rootfracA.getIndex(); 
			for (int i=0; i<ConstLayer.MAX_ROC_LAY; i++){
				resid.rootfrac[i][il] = rootfracA.getDouble(ind12.set(cid, i, il));
			}
			
			Index ind13 = vegwaterA.getIndex(); 
			resid.vegwater[il] = vegwaterA.getDouble(ind13.set(cid, il));
		
			Index ind14 = vegsnowA.getIndex(); 
			resid.vegsnow[il] = vegsnowA.getDouble(ind14.set(cid, il));

			Index ind15 = vegcA.getIndex(); 
			for (int i=0; i<ConstCohort.NUM_PFT_PART; i++){
				resid.vegc[i][il] = vegcA.getDouble(ind15.set(cid, i, il));
			}
			
			Index ind16 = labnA.getIndex(); 
			resid.labn[il] = labnA.getDouble(ind16.set(cid, il));
		
			Index ind17 = strnA.getIndex(); 
			for (int i=0; i<ConstCohort.NUM_PFT_PART; i++){
				resid.strn[i][il] = strnA.getDouble(ind17.set(cid, i, il));
			}
			
			Index ind18 = deadcA.getIndex(); 
			resid.deadc[il] = deadcA.getDouble(ind18.set(cid, il));
		
			Index ind19 = deadnA.getIndex(); 
			resid.deadn[il] = deadnA.getDouble(ind19.set(cid, il));
		
			Index ind20 = unnormleafA.getIndex(); 
			resid.unnormleaf[il] = unnormleafA.getDouble(ind20.set(cid, il));

			Index ind21 = toptaA.getIndex();
			for (int i=0; i<10; i++){
				resid.toptA[i][il] = toptaA.getDouble(ind21.set(cid, i, il));
			}
			
			Index ind22 = eetmxaA.getIndex(); 
			for (int i=0; i<10; i++){
				resid.eetmxA[i][il] = eetmxaA.getDouble(ind22.set(cid, i, il));
			}
			
			Index ind23 = petmxaA.getIndex(); 
			for (int i=0; i<10; i++){
				resid.petmxA[i][il] = petmxaA.getDouble(ind23.set(cid, i, il));
			}
			
			Index ind24 = unnormleafmxaA.getIndex(); 
			for (int i=0; i<10; i++){
				resid.unnormleafmxA[i][il] = unnormleafmxaA.getDouble(ind24.set(cid, i, il));
			}
			
			Index ind25 = prvfoliagemxaA.getIndex(); 
			resid.prvfoliagemxA[il] = prvfoliagemxaA.getDouble(ind25.set(cid, il));
		}
		
	    //
	    Index ind26 = numsnwlA.getIndex(); 
	    resid.numsnwl = numsnwlA.getInt(ind26.set(cid));
	    
	    Index ind27 = snwextramassA.getIndex(); 
	    resid.snwextramass = snwextramassA.getInt(ind27.set(cid));
	    
		for (int il = 0; il < ConstLayer.MAX_SNW_LAY; il++) {

		    Index ind28 = DZsnowA.getIndex(); 
		    resid.DZsnow[il] = DZsnowA.getDouble(ind28.set(cid, il)); 

		    Index ind29 = TSsnowA.getIndex(); 
		    resid.TSsnow[il] = TSsnowA.getDouble(ind29.set(cid, il));
	    
	        Index ind30 = LIQsnowA.getIndex(); 
	        resid.LIQsnow[il] = LIQsnowA.getDouble(ind30.set(cid, il));
	    
	        Index ind31 = RHOsnowA.getIndex(); 
	        resid.RHOsnow[il] = RHOsnowA.getDouble(ind31.set(cid, il)); 
	    
	        Index ind32 = ICEsnowA.getIndex(); 
	        resid.ICEsnow[il] = ICEsnowA.getDouble(ind32.set(cid, il)); 
	    
	        Index ind33 = AGEsnowA.getIndex(); 
	        resid.AGEsnow[il] = AGEsnowA.getDouble(ind33.set(cid, il));
		}
	    
		//
	    Index ind34 = numslA.getIndex(); 
	    resid.numsl = numslA.getInt(ind34.set(cid));
	    
	    Index ind35 = aldA.getIndex(); 
	    resid.ald = aldA.getInt(ind35.set(cid));
	    
	    Index ind36 = permafrostA.getIndex(); 
	    resid.permafrost = permafrostA.getInt(ind36.set(cid));
	    
	    Index ind37 = watertabA.getIndex(); 
	    resid.watertab = watertabA.getDouble(ind37.set(cid));

		for (int il = 0; il < ConstLayer.MAX_SOI_LAY; il++) {
			Index ind38 = DZsoilA.getIndex(); 
			resid.DZsoil[il] = DZsoilA.getDouble(ind38.set(cid, il));
	    
			Index ind39 = TYPEsoilA.getIndex(); 
			resid.TYPEsoil[il] = TYPEsoilA.getInt(ind39.set(cid, il));
	    
			Index ind40 = TSsoilA.getIndex(); 
			resid.TSsoil[il] = TSsoilA.getDouble(ind40.set(cid, il)); 
	    
			Index ind41 = LIQsoilA.getIndex(); 
			resid.LIQsoil[il] = LIQsoilA.getDouble(ind41.set(cid, il)); 
	    
			Index ind42 = ICEsoilA.getIndex(); 
			resid.ICEsoil[il] = ICEsoilA.getDouble(ind42.set(cid, il));
	    
			Index ind43 = FROZENsoilA.getIndex(); 
			resid.FROZENsoil[il] = FROZENsoilA.getInt(ind43.set(cid, il)); 
	    
			Index ind44 = TEXTUREsoilA.getIndex(); 
			resid.TEXTUREsoil[il] = TEXTUREsoilA.getInt(ind44.set(cid, il));
		}
		
		for (int il = 0; il < ConstLayer.MAX_ROC_LAY; il++) {
			Index ind45 = DZrockA.getIndex(); 
			resid.DZrock[il] = DZrockA.getInt(ind45.set(cid, il));

			Index ind46 = TSrockA.getIndex(); 
			resid.TSrock[il] = TSrockA.getInt(ind46.set(cid, il)); 
		}	    

		for (int il = 0; il < ConstLayer.MAX_NUM_FNT; il++) {
			Index ind47 = frontZA.getIndex(); 
			resid.frontZ[il] = frontZA.getDouble(ind47.set(cid, il));
	    
			Index ind48 = frontFTA.getIndex(); 
			resid.frontFT[il] = frontFTA.getInt(ind48.set(cid, il));
		}
		
		Index ind49 = wdebriscA.getIndex(); 
	    resid.wdebrisc = wdebriscA.getDouble(ind49.set(cid));
	    
		for (int il = 0; il < ConstLayer.MAX_SOI_LAY; il++) {
			Index ind50 = rawcA.getIndex(); 
			resid.rawc[il] = rawcA.getDouble(ind50.set(cid, il));
	    
			Index ind51 = somaA.getIndex(); 
			resid.soma[il] = somaA.getDouble(ind51.set(cid, il));
	    
			Index ind52 = somprA.getIndex(); 
			resid.sompr[il] = somprA.getDouble(ind52.set(cid, il));
	    
			Index ind53 = somcrA.getIndex(); 
			resid.somcr[il] = somcrA.getDouble(ind53.set(cid, il));
		}
		
		Index ind54 = wdebrisnA.getIndex(); 
		resid.wdebrisn = wdebrisnA.getDouble(ind54.set(cid));

		for (int il = 0; il < ConstLayer.MAX_SOI_LAY; il++) {
	    
			Index ind55 = orgnA.getIndex(); 
			resid.orgn[il] = orgnA.getInt(ind55.set(cid));
	    
			Index ind56 = avlnA.getIndex(); 
			resid.avln[il] = avlnA.getInt(ind56.set(cid));

			Index ind57 = kdrawcA.getIndex(); 
			resid.kdrawc[il] = kdrawcA.getInt(ind57.set(cid));
	    
			Index ind58 = kdsomaA.getIndex(); 
			resid.kdsoma[il] = kdsomaA.getInt(ind58.set(cid));
	    
			Index ind59 = kdsomprA.getIndex(); 
			resid.kdsompr[il] = kdsomprA.getDouble(ind59.set(cid));
	    
			Index ind60 = kdsomcrA.getIndex(); 
			resid.kdsomcr[il] = kdsomcrA.getDouble(ind60.set(cid, il));
		}
	};

}