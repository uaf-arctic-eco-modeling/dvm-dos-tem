#ifndef LAYERCONST_H_
	#define LAYERCONST_H_
	
	const int MAX_SNW_LAY =6; //maximum number of Snow Layer
	
	const int MAX_MOS_LAY =2; // maximum number of moss Layer involved in soil thermal/hydrological/bgc processes;
	const int MAX_SLW_LAY =3; // maximum number of shallow organic Layer
	const int MAX_DEP_LAY =3; // maximum number of deep organic Layer

	const int MAX_MIN_LAY =15; // maximum number of mineral Layer (0.1,0.1,0.1,0.1, 0.2,0.2,0.2,0.3,0.3,0.3, 0.3, 0.5, 0.5, 1, 1)
	const double MINETHICK[MAX_MIN_LAY] = {0.1,0.1,0.1, 0.1, 0.2,0.2,0.2, 0.3, 0.3, 0.3, 0.3, 0.5, 0.5, 1.0, 1.0};
	const int MINEZONE[3] = {2, 6, 14};    //the mineral layer index (from 0) of THREE soil zones
	                                       // e.g., here: minea - 0~0.3m, mineb - 0.3~1.0m, minec - 1m~

	const int MAX_ROC_LAY =5; // maximum number of rock Layer (
	const double ROCKTHICK[MAX_ROC_LAY] = {2.0, 4.0, 8.0, 16.0, 20.0};
	
	const int MAX_SOI_LAY =MAX_MOS_LAY+ MAX_SLW_LAY+MAX_DEP_LAY+MAX_MIN_LAY; // maximum number of soil layer
	const int MAX_GRN_LAY =MAX_SNW_LAY + MAX_SOI_LAY+ MAX_ROC_LAY; //maximumum number of Ground (soil+rock+snow) Layer
	
	const int MAX_NUM_FNT =10; // maximum number of fronts in all ground layers

	const int MAX_ROT_LAY =10;  //maximum number of fine root layers
	const double ROOTTHICK[MAX_ROT_LAY] = {0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1};

	const double MINSLWTHICK = 0.01;   //minium thickness (meter) for forming a shallow organic layer
	const double MINDEPTHICK = 0.01;   //minium thickness (meter) for forming a deep organic layer
    	 
#endif /*LAYERCONST_H_*/
