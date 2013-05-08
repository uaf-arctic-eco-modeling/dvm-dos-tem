/*
 * TEMccjava.cpp
 *
 * Purpose: some data/info connection between C++ and Java, because of unmatch 'string', 2D-array
 *
 */

#include "TEMccjava.h"

TEMccjava::TEMccjava(){

};

TEMccjava::~TEMccjava(){

};

void TEMccjava::setCohort(Cohort * chtp) {
     cht = chtp;
};

/////////////////////////////////////////////////////////////////////////////////////////////////
// for Java calling to reset some initial conditions and calibrated BGC parameters
// NOTE: all inputs are assigned into 'chtlu', which is regarded as the portal
//
void TEMccjava::setInitVbState1pft(const int & ipft) {

        // FOR VEGETATION BGC
        for (int i=0; i<NUM_PFT_PART; i++){
            cht->chtlu.initvegc[i][ipft] = initvegc[i];
            cht->chtlu.initvegn[i][ipft] = initvegn[i];
        }

        cht->chtlu.initdeadc[ipft] = initdeadc;
        cht->chtlu.initdeadn[ipft] = initdeadn;

        cht->vegbgc[ipft].initializeState();

};

void TEMccjava::setInitSbState() {

         // get data from outside
        cht->chtlu.initdmossc= initdmossc;
        cht->chtlu.initshlwc = initshlwc;
        cht->chtlu.initdeepc = initdeepc;
        cht->chtlu.initminec = initminec;
        cht->chtlu.initavln  = initavln;
        cht->chtlu.initsoln  = initsoln;

         // initializing soil bgc state conditions
        cht->soilbgc.initializeState();

};

void TEMccjava::setVbCalPar1pft(const int &ipft, vegpar_cal *jvcalpar) {

        // Calibrated parameters for vegetation BGC
        cht->chtlu.cmax[ipft] = jvcalpar->cmax;
        cht->chtlu.nmax[ipft] = jvcalpar->nmax;

        for (int i=0; i<NUM_PFT_PART; i++) {
            cht->chtlu.cfall[i][ipft] = jvcalpar->cfall[i];
            cht->chtlu.nfall[i][ipft] = jvcalpar->nfall[i];
        }

        cht->chtlu.kra[ipft] = jvcalpar->kra;
        for (int i=0; i<NUM_PFT_PART; i++) {
            cht->chtlu.krb[i][ipft] = jvcalpar->krb[i];
        }

        cht->chtlu.frg[ipft] = jvcalpar->frg;

        // parameters passing
        cht->vegbgc[ipft].initializeParameter();

};

void TEMccjava::setSbCalPar(soipar_cal *jscalpar) {

        // Calibrated parameters for soil BGC
        cht->chtlu.micbnup = jscalpar->micbnup;
        cht->chtlu.kdcmoss = jscalpar->kdcmoss;
        cht->chtlu.kdcrawc = jscalpar->kdcrawc;
        cht->chtlu.kdcsoma = jscalpar->kdcsoma;
        cht->chtlu.kdcsompr= jscalpar->kdcsompr;
        cht->chtlu.kdcsomcr= jscalpar->kdcsomcr;

        // parameters passing
        cht->soilbgc.initializeParameter();
};


/////////////////
// retrieve the paramaters and some BGC states for calibration
void TEMccjava::getVbCalPar1pft(const int &ipft) {

        // Calibrated parameters for vegetation BGC
		vcalpar1pft.cmax = cht->chtlu.cmax[ipft];
		vcalpar1pft.nmax = cht->chtlu.nmax[ipft];

        for (int i=0; i<NUM_PFT_PART; i++) {
        	vcalpar1pft.cfall[i] = cht->chtlu.cfall[i][ipft];
        	vcalpar1pft.nfall[i] = cht->chtlu.nfall[i][ipft];
        }

        vcalpar1pft.kra = cht->chtlu.kra[ipft];
        for (int i=0; i<NUM_PFT_PART; i++) {
        	vcalpar1pft.krb[i] = cht->chtlu.krb[i][ipft];
        }
        vcalpar1pft.frg = cht->chtlu.frg[ipft];

};

void TEMccjava::getSbCalPar() {

        // Calibrated parameters for soil BGC
		scalpar.micbnup = cht->chtlu.micbnup;
		scalpar.kdcmoss = cht->chtlu.kdcmoss;
		scalpar.kdcrawc = cht->chtlu.kdcrawc;
		scalpar.kdcsoma = cht->chtlu.kdcsoma;
		scalpar.kdcsompr= cht->chtlu.kdcsompr;
		scalpar.kdcsomcr= cht->chtlu.kdcsomcr;

};

void TEMccjava::getInitVbState1pft(const int & ipft) {

        // FOR VEGETATION BGC
        for (int i=0; i<NUM_PFT_PART; i++){
            initvegc[i] = cht->chtlu.initvegc[i][ipft];
            initvegn[i] = cht->chtlu.initvegn[i][ipft];
        }

        initdeadc = cht->chtlu.initdeadc[ipft];
        initdeadn = cht->chtlu.initdeadn[ipft];

};

void TEMccjava::getInitSbState() {

         // get data from tem
    	 initdmossthick = cht->chtlu.initdmossthick;
         initfibthick = cht->chtlu.initfibthick;
         inithumthick = cht->chtlu.inithumthick;

         initdmossc= cht->chtlu.initdmossc;
         initshlwc = cht->chtlu.initshlwc;
         initdeepc = cht->chtlu.initdeepc;
         initminec = cht->chtlu.initminec;
         initavln  = cht->chtlu.initavln;
         initsoln  = cht->chtlu.initsoln;

};

void TEMccjava::getData1pft(const int & ipft) {
	ed1pft = cht->ed[ipft];
	bd1pft = cht->bd[ipft];
	cd     = cht->cd;

};
