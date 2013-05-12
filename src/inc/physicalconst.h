/*! \file
 * provides physical constants*/
#ifndef PHYSICALCONST_H_
#define PHYSICALCONST_H_

	const float DENLIQ = 1000.; // liquid water density kg/m3
	const float DENICE = 917. ; // ice density kg/m3
	const float TCLIQ  = 0.6  ; //  thermal conductivity of liq W/mK
	const float TCICE  = 2.29 ; //  thermal conductivity of ice W/mK
	const float TCAIR  = 0.023 ; // thermal conductivity of air W/mK
	
	const float SHCLIQ = 4.188e3  ; //  specific heat capacity of liq J/kgK
	const float SHCICE = 2.11727e3 ; //  specific heat capacity of ice J/kgK
	const float SHCAIR = 1.00464e3 ; // specific heat capacity of air J/kgK
	
	const float LHFUS  = 3.337e5 ; // latent heat of fusion  J/kg
	const float LHVAP  = 2.501e6 ; // latent heat of vaporization  J/kg
	const float LHSUB  = 2.8338e6 ; // latent heat of sublimation  J/kg
	
	const float G        = 9.80616 ;  //  acceleration of gravity m/s2
#ifndef PI
	const float PI       = 3.14159265358979; // pi -
#endif
	const float Pstd     = 101325 ; // standard pressure Pa
	const float STFBOLTZ = 5.67e-8 ;// Stefan-Boltzmann constant W/m2K4
	const float BOLTZ    = 1.38e-23 ; // Boltzmann constant J/Kmolecule
	const float NA       = 6.02214e26 ; // mole/kmol
	const float KPA      = 0.4; // von karman constant -

#endif /*PHYSICALCONST_H_*/
