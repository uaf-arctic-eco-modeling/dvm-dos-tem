#ifndef TEMCCJAVA_H_
    #define TEMCCJAVA_H_

    #include "../../src/runmodule/Controller.h"
    #include "../../src/runmodule/ModelData.h"
    #include "../../src/runmodule/Cohort.h"

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

            double initdmossthick;
            double initfibthick;
            double inithumthick;
            double initdmossc;
            double initshlwc;
            double initdeepc;
            double initminec;
            double initsoln;    // total soil organic N
            double initavln;    // total soil available N

            // ONE pft's 'ed','bd', and calibrated par, which needed for operating individually in java
            EnvData ed1pft;
            BgcData bd1pft;
            CohortData cd;

            vegpar_cal vcalpar1pft;
            soipar_cal scalpar;

            void setCohort(Cohort * cht);

            void setInitVbState1pft(const int& ipft);\
            void setInitSbState();
            void setVbCalPar1pft(const int& ipft, vegpar_cal *jvcalpar);
            void setSbCalPar(soipar_cal *jscalpar);

            void getInitVbState1pft(const int& ipft);\
            void getInitSbState();
            void getVbCalPar1pft(const int& ipft);
            void getSbCalPar();

            void getData1pft(const int & ipft);

};
#endif /*TEMCCJAVA_H_*/
