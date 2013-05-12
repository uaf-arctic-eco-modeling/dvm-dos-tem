/*! \file 
 * This is a class for looking up soil properties based on texture and environment
 * The purpose of this class is to reduce computing time.
 */
#ifndef SOILLOOKUP_H_
	#define SOILLOOKUP_H_

	#include <cmath>
	#include <iostream>
	#include "../inc/physicalconst.h"
	
	using namespace std;

/*! maximum number of soil texture*/
	const int MAX_SOIL_TXTR = 12; //add gravel
	const int MAX_SM =1000;       // the soil moisture is divided into 100
	const int MAX_ST1 =1000;      // from 0 to -1, 0.001 interval
	const int MAX_ST2 =500;       // from -1 to -50, 0.1 interval

	class SoilLookup{
		public:
			SoilLookup();
			~SoilLookup();
	
			/* the following parameters are from lookup table*/
			int sand[MAX_SOIL_TXTR];
			int silt[MAX_SOIL_TXTR];
			int clay[MAX_SOIL_TXTR];
	
			// the thermal conductivity of soil solids W m-1 K-1
			float Ksolids[MAX_SOIL_TXTR];
			// the heat capacity of soil solids  J m-3 K-1
			float Csolids[MAX_SOIL_TXTR];
			// saturated hydralic conductivity  mm s-1
			float Ksat[MAX_SOIL_TXTR];
			// saturated matric potential mm
			float Psisat[MAX_SOIL_TXTR];
			// Porosity
			float poro[MAX_SOIL_TXTR];
			// poro size distribution factor 
			float b[MAX_SOIL_TXTR];
	
			float color[MAX_SOIL_TXTR];
	
			float bulkden[MAX_SOIL_TXTR];

			/* derive parameter values based on soil texture*/
			float wiltp[MAX_SOIL_TXTR]; //wilting point
	
			float fieldcap[MAX_SOIL_TXTR];// field capacity
	
			float tcunfsat[MAX_SOIL_TXTR];
			float tcfrzsat[MAX_SOIL_TXTR];
			float tcdry[MAX_SOIL_TXTR];
	 
			float albsatvis[MAX_SOIL_TXTR];
			float albsatnir[MAX_SOIL_TXTR];
			float albdryvis[MAX_SOIL_TXTR];
			float albdrynir[MAX_SOIL_TXTR];
	
			/* the following parameters are based on soil texture and other env variables */
	
			float hk[MAX_SOIL_TXTR][MAX_SM];
			float psi[MAX_SOIL_TXTR][MAX_SM];

		private:
			void setLookupParam();
			void deriveParam5Texture();
			void deriveParam5TextureEnv();
		         
	    	float getDryThermCond(const float & bulkden);
			float getSolidThermalCond(const float & clay ,const float & sand ); 	
	    	float getSolidVolHeatCapa(const float & clay ,const float & sand );
	    	float getSatuHydraulCond(const float & sand);
	    	float getSatuMatrPotential(const float & sand);
	   	 	float getPorosity(const float & sand);
			float getBSW(const float & clay);
			float getBulkden(const float & poro);
};
#endif /*SOILLOOKUP_H_*/
