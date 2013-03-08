#ifndef TEMCCJAVA_H_
    #define TEMCCJAVA_H_

    #include "runmodule/Controller.h"
    #include "runmodule/ModelData.h"
    #include "runmodule/Cohort.h"

    class TEMccjava{
	public :
            TEMccjava();
            ~TEMccjava();
	
            //
            Cohort * cht;
    
            // for java calibration - state variables and parameters pass
            double initvegc[NUM_PFT_PART];
            double initvegn[NUM_PFT_PART];
            double initdeadc;
            double initdeadn;

            double initfibthick;
            double inithumthick;
            double initshlwc;
            double initdeepc;
            double initminec;
            double initsoln;    // total soil organic N
            double initavln;    // total soil available N

            // ONE pft's 'ed','bd', and calibrated par, which needed for operating individually in java
            EnvData ed1pft;
            BgcData bd1pft;

            vegpar_cal vcalpar1pft;
            soipar_cal scalpar;

            void setCohort(Cohort * cht);

            void initVbState1pft(const int& ipft);\
            void initSbState();
            void setVbCalPar1pft(const int& ipft, vegpar_cal *jvcalpar);
            void setSbCalPar(soipar_cal *jscalpar);

            void getVbState1pft(const int& ipft);\
            void getSbState();
            void getVbCalPar1pft(const int& ipft);
            void getSbCalPar();

            void getData1pft(const int & ipft);

};
#endif /*TEMCCJAVA_H_*/
