#ifndef COHORTCONST_H_
	#define COHORTCONST_H_
	const int NUM_CMT = 8; //max. no. of community types
	const int NUM_PFT = 10; //max. no. of plant function types

	const int NUM_PFT_PART = 3; //max. no. of plant parts (e.g., leaves, stems, roots)
	enum VPARTKEY{I_leaf = 0, I_stem, I_root};

	enum VASCULARKEY{I_vascular = 0, I_sphagnum, I_feathermoss, I_other};

	const int MAX_DRG_TYPE = 2; //max. no. of drainage types

	const int NUM_FSEVR    = 5;   // no. of fire severity classes
		// the severity categories are from ALFRESCO:
		// 0 - no burning; 1 - low; 2 - moderate; 3 - high + low surface; 4 - high + high surface

	const int NUM_FSEASON  = 4;   // no. of fire season categories: season: 1 (pre-season), 2(early fire), 3(late fire), and 4 (after-season) with 3 months in the order
	const int NUM_FSIZE    = 5;   // no. of fire size categories

#endif /*COHORTCONST_H_*/
