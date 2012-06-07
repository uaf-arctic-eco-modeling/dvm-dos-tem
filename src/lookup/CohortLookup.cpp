
#include "CohortLookup.h"

CohortLookup::CohortLookup(){
   
};

CohortLookup::~CohortLookup(){

};

void CohortLookup::init(){
	assignBgcCalpar(dircmtname);

	assignVegDimension(dircmtname);
	assignGroundDimension(dircmtname);

	assignEnv4Canopy(dircmtname);
	assignBgc4Vegetation(dircmtname);

	assignEnv4Ground(dircmtname);
	assignBgc4Ground(dircmtname);

	assignFirePar(dircmtname);
  
};

void CohortLookup::assignBgcCalpar(string & dircmt){

	string parfilecal = dircmt+"_calparbgc.txt";
	ifstream fctrcomm;
	fctrcomm.open(parfilecal.c_str(),ios::in );
	bool isOpen = fctrcomm.is_open();
	if ( !isOpen ){
  		cout << "\nCannot open " << parfilecal << "  \n" ;
  		exit( -1 );
	}

	string str;
	getline(fctrcomm, str);     //comments in the file
	getline(fctrcomm, str);     //comments in the file
	getline(fctrcomm, str);     //comments in the file

	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> cmax[ip];  getline(fctrcomm, str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> nmax[ip];  getline(fctrcomm, str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> cfall[I_leaf][ip]; getline(fctrcomm, str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> cfall[I_stem][ip]; getline(fctrcomm, str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> cfall[I_root][ip]; getline(fctrcomm, str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> nfall[I_leaf][ip];  getline(fctrcomm, str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> nfall[I_stem][ip];  getline(fctrcomm, str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> nfall[I_root][ip];  getline(fctrcomm, str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> kra[ip]; getline(fctrcomm, str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> krb[I_leaf][ip]; getline(fctrcomm, str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> krb[I_stem][ip]; getline(fctrcomm, str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> krb[I_root][ip]; getline(fctrcomm, str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrcomm >> frg[ip]; getline(fctrcomm, str);

	// soil bgc Calibrated parameters
	getline(fctrcomm, str);     //comments in the file
	fctrcomm >> micbnup; getline(fctrcomm, str);
	fctrcomm >> kdcrawc; getline(fctrcomm, str);
	fctrcomm >> kdcsoma; getline(fctrcomm, str);
	fctrcomm >> kdcsompr; getline(fctrcomm, str);
	fctrcomm >> kdcsomcr; getline(fctrcomm, str);

	fctrcomm.close();

};

void CohortLookup::assignVegDimension(string &dircmt){

	string parfilecomm = dircmt+"_dimvegetation.txt";
	ifstream fctrpft;
	fctrpft.open(parfilecomm.c_str(),ios::in );
	bool isOpen = fctrpft.is_open();
	if ( !isOpen ) {
  		cout << "\nCannot open " << parfilecomm << "  \n" ;
  		exit( -1 );
	}

	string str;    //dummy string for comments in the file
	getline(fctrpft,str);     //read comments
	getline(fctrpft,str);     //read comments

	for(int ip=0; ip<NUM_PFT; ip++) fctrpft >> vegcov[ip];
	getline(fctrpft,str);     // read comments

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> ifwoody[ip];
	getline(fctrpft,str);     // read comments

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> ifdeciwoody[ip];
	getline(fctrpft,str);     // read comments

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> ifperenial[ip];
	getline(fctrpft,str);     // read comments
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> nonvascular[ip];
	getline(fctrpft,str);     // read comments

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> sla[ip];
	getline(fctrpft,str);     // read comments

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> klai[ip];
	getline(fctrpft,str);     // read comments

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> minleaf[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> aleaf[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> bleaf[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> cleaf[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> kfoliage[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> cov[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> m1[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> m2[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> m3[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> m4[ip];
	getline(fctrpft,str);

    for (int il =0; il<MAX_ROT_LAY; il++){
    	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> frootfrac[il][ip];
    	getline(fctrpft,str);     //comments in the file
    }

    for(int ip=0; ip<NUM_PFT; ip++) fctrpft >> lai[ip];
	getline(fctrpft,str);     // read comments

    for (int im =0; im<MINY; im++){
    	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> envlai[im][ip];
    	getline(fctrpft,str);     //comments in the file
    }


	fctrpft.close();

};

void CohortLookup::assignGroundDimension(string &dircmt){

	string parfilecomm = dircmt+"_dimground.txt";

	ifstream fctrcomm;
	fctrcomm.open(parfilecomm.c_str(),ios::in );
	bool isOpen = fctrcomm.is_open();
	if ( !isOpen ){
  		cout << "\nCannot open " << parfilecomm << "  \n" ;
  		exit( -1 );
	}

	string str;
	getline(fctrcomm,str);     //comments in the file

	//snow
	getline(fctrcomm,str);     //comments in the file
	fctrcomm >> snwdenmax; getline(fctrcomm,str);     //comments in the file
	fctrcomm >> snwdennew; getline(fctrcomm,str);     //comments in the file
	fctrcomm >> initsnwthick;  getline(fctrcomm,str);     //comments in the file
	fctrcomm >> initsnwdense;  getline(fctrcomm,str);     //comments in the file

	//moss
	getline(fctrcomm,str);     //comments in the file
	fctrcomm >> maxmossthick; getline(fctrcomm,str);     //comments in the file
  	fctrcomm >> initmossthick; getline(fctrcomm,str);    //comments in the file
  	fctrcomm >> initmosstype; getline(fctrcomm,str);     //comments in the file
  	fctrcomm >> coefmossa; getline(fctrcomm,str);       //comments in the file
  	fctrcomm >> coefmossb; getline(fctrcomm,str);       //comments in the file

  	//soil
	getline(fctrcomm,str);     //comments in the file
  	fctrcomm >> initfibthick; getline(fctrcomm,str);        //comments in the file
  	fctrcomm >> inithumthick; getline(fctrcomm,str);        //comments in the file
  	fctrcomm >> coefshlwa; getline(fctrcomm,str);       //comments in the file
  	fctrcomm >> coefshlwb; getline(fctrcomm,str);       //comments in the file
  	fctrcomm >> coefdeepa; getline(fctrcomm,str);       //comments in the file
  	fctrcomm >> coefdeepb; getline(fctrcomm,str);       //comments in the file
  	fctrcomm >> coefminea; getline(fctrcomm,str);       //comments in the file
  	fctrcomm >> coefmineb; getline(fctrcomm,str);       //comments in the file

  	for (int ily=0; ily<MAX_MIN_LAY; ily++){
  			fctrcomm >> minetexture[ily];
  			getline(fctrcomm,str);     //comments in the file

  	}

	fctrcomm.close();

};

void CohortLookup::assignEnv4Canopy(string &dir){

	string parfilecomm = dir+"_envcanopy.txt";
	ifstream fctrpft;
	fctrpft.open(parfilecomm.c_str(),ios::in );
	bool isOpen = fctrpft.is_open();
	if ( !isOpen ) {
  		cout << "\nCannot open " << parfilecomm << "  \n" ;
  		exit( -1 );
	}

	string str;
	getline(fctrpft,str);     //comments in the file
	getline(fctrpft,str);     //comments in the file

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> albvisnir[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> er[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> ircoef[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> iscoef[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> glmax[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> gl_bl[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> gl_c[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> vpd_open[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> vpd_close[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> ppfd50[ip];
	getline(fctrpft,str);

   	// initial values
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> initvegwater[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> initvegsnow[ip];
	getline(fctrpft,str);

	fctrpft.close();

};

// vegetation C/N parameters
void CohortLookup::assignBgc4Vegetation(string & dircmt){

	string parfilecomm = dircmt+"_bgcvegetation.txt";
	ifstream fctrpft;
	fctrpft.open(parfilecomm.c_str(),ios::in );
	bool isOpen = fctrpft.is_open();
	if ( !isOpen ){
  		cout << "\nCannot open " << parfilecomm << "  \n" ;
  		exit( -1 );
	}

	string str;
	getline(fctrpft,str);     //comments in the file
	getline(fctrpft,str);     //comments in the file

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> kc[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> ki[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> tmin[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> toptmin[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> toptmax[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> tmax[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> raq10a0[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> raq10a1[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> raq10a2[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> raq10a3[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> knuptake[ip];
	getline(fctrpft,str);

	for (int i=0; i<NUM_PFT_PART; i++){
		for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> cpart[i][ip];
		getline(fctrpft,str);
	}

	for (int i=0; i<NUM_PFT_PART; i++){
		for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> npart[i][ip];
		getline(fctrpft,str);
	}

	for (int i=0; i<NUM_PFT_PART; i++){
		for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> initc2neven[i][ip];
		getline(fctrpft,str);
	}

	for (int i=0; i<NUM_PFT_PART; i++){
		for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> c2nb[i][ip];
		getline(fctrpft,str);
	}

	for (int i=0; i<NUM_PFT_PART; i++){
		for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> c2nmin[i][ip];
		getline(fctrpft,str);
	}

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> c2na[ip];
	getline(fctrpft,str);

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> labncon[ip];
	getline(fctrpft,str);

   	// initial values
   	for (int i=0; i<NUM_PFT_PART; i++){
		for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> initvegc[i][ip];
		getline(fctrpft,str);
   	}
	for (int i=0; i<NUM_PFT_PART; i++){
		for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> initvegn[i][ip];
		getline(fctrpft,str);
	}

	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> initdeadc[ip];
	getline(fctrpft,str);
	for(int ip=0; ip<NUM_PFT; ip++)	fctrpft >> initdeadn[ip];
	getline(fctrpft,str);

	fctrpft.close();

};

void CohortLookup::assignEnv4Ground(string &dircmt){

	string parfilecomm = dircmt+"_envground.txt";

	ifstream fctrcomm;
	fctrcomm.open(parfilecomm.c_str(),ios::in );
	bool isOpen = fctrcomm.is_open();
	if ( !isOpen ){
  		cout << "\nCannot open " << parfilecomm << "  \n" ;
  		exit( -1 );
	}

	string str;
	getline(fctrcomm,str);     //comments in the file

	fctrcomm >> snwalbmax; getline(fctrcomm,str);     //comments in the file
	fctrcomm >> snwalbmin; getline(fctrcomm,str);     //comments in the file

	fctrcomm >> psimax;  getline(fctrcomm,str);     //comments in the file
	fctrcomm >> evapmin;  getline(fctrcomm,str);     //comments in the file
	fctrcomm >> drainmax;  getline(fctrcomm,str);     //comments in the file

  	fctrcomm >> rtdp4growpct; getline(fctrcomm,str);     //comments in the file

	fctrcomm >> initsnwtem;  getline(fctrcomm,str);     //comments in the file

	for (int il=0; il<10; il++){
		fctrcomm >> initts[il];
		getline(fctrcomm,str);     //comments in the file
	}
	for (int il=0; il<10; il++){
		fctrcomm >> initvwc[il];
		getline(fctrcomm,str);     //comments in the file
	}

	fctrcomm.close();

};

void CohortLookup::assignBgc4Ground(string &dircmt){
	string parfilecomm = dircmt+"_bgcsoil.txt";

	ifstream fctrcomm;
	fctrcomm.open(parfilecomm.c_str(),ios::in );
	bool isOpen = fctrcomm.is_open();
	if ( !isOpen ) {
  		cout << "\nCannot open " << parfilecomm << "  \n" ;
   		exit( -1 );
	}
	
	string str;
	getline(fctrcomm,str);     //comments in the file

	fctrcomm >> rhq10; getline(fctrcomm,str);
	fctrcomm >> moistmin; getline(fctrcomm,str);
	fctrcomm >> moistopt; getline(fctrcomm,str);
	fctrcomm >> moistmax; getline(fctrcomm,str);

	fctrcomm >> lcclnc; getline(fctrcomm,str);

	fctrcomm >> fsoma; getline(fctrcomm,str);
	fctrcomm >> fsompr; getline(fctrcomm,str);
	fctrcomm >> fsomcr; getline(fctrcomm,str);
	fctrcomm >> som2co2; getline(fctrcomm,str);

	fctrcomm >> kn2;   getline(fctrcomm,str);
	fctrcomm >> nmincnsoil; getline(fctrcomm,str);
	fctrcomm >> propftos; getline(fctrcomm,str);

	fctrcomm >> fnloss; getline(fctrcomm,str);

	//
	fctrcomm >> initshlwc; getline(fctrcomm,str);
	fctrcomm >> initdeepc; getline(fctrcomm,str);
	fctrcomm >> initminec; getline(fctrcomm,str);
	fctrcomm >> initsoln; getline(fctrcomm,str);
	fctrcomm >> initavln; getline(fctrcomm,str);

	fctrcomm.close();
	
};

void CohortLookup::assignFirePar(string &dircmt){

	string parfilecomm = dircmt+"_firepar.txt";
	ifstream fctrcomm;
	fctrcomm.open(parfilecomm.c_str(),ios::in );
	bool isOpen = fctrcomm.is_open();
	if ( !isOpen ) {
  		cout << "\nCannot open " << parfilecomm << "  \n" ;
  		exit( -1 );
	}

	string str;
	getline(fctrcomm,str);     //comments in the file
	getline(fctrcomm,str);     //comments in the file

	for(int i=0; i<NUM_FSEVR; i++){
		for(int ip=0; ip<NUM_PFT; ip++) fctrcomm >> fvcombust[i][ip];
		getline(fctrcomm,str);
	}

	for(int i=0; i<NUM_FSEVR; i++){
		for(int ip=0; ip<NUM_PFT; ip++) fctrcomm >> fvslash[i][ip];
		getline(fctrcomm,str);
	}

	getline(fctrcomm,str);     //comments in the file
	for(int i=0; i<NUM_FSEVR; i++) {
		fctrcomm >> foslburn[i];
		getline(fctrcomm,str);
	}

	getline(fctrcomm,str);     //comments in the file
	fctrcomm >> vsmburn;      getline(fctrcomm,str);
  	fctrcomm >> r_retain_c;   getline(fctrcomm,str);
  	fctrcomm >> r_retain_n;   getline(fctrcomm,str);

	getline(fctrcomm,str);     //comments in the file
	for(int i=0; i<MAX_FIR_OCRNUM; i++) {
		fctrcomm >> fireyear[i];
		fctrcomm >> fireseason[i];
		fctrcomm >> firesize[i];
		fctrcomm >> fireseverity[i];
		getline(fctrcomm,str);
	}

	fctrcomm.close();

};





