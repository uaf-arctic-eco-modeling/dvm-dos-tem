/*
 * Soil_Bgc.cpp
 *
 * Purpose: Calculating Soil C and N changes
 *
 * History:
 *   June 28, 2011, by F.-M. Yuan:
 *     (1) Recoding based on DOS-TEM's code;
 *     (2) Multiple soil layer C&N pools added
 *
 * Important:
 *   (1) Parameters are read from 'CohortLookup.cpp', and set
 *       to 'bgcpar' (struct::soipar_bgc)
 *   (2) Calibrated Parameters are also read from 'CohortLookup.cpp'
 *       initially, and set to 'calpar' (struct::soipar_cal)
 *
 *   (3) The calculation is for ONE community with multple PFT.
 *
 *   (4) FOUR (4) data pointers must be initialized by calling
 *       corresponding 'set...' methods
 *          chtlu, ed, bd, fd
 *
 */

#include "../include/TEMLogger.h"

#include "../include/Soil_Bgc.h"

#include <iostream>

extern src::severity_logger< severity_level > glg;

/** New constructor. Build it complete! Build it right! */
Soil_Bgc::Soil_Bgc(): nfeed(false), avlnflg(false), baseline(false),
                      d2wdebrisc(UIN_D), d2wdebrisn(UIN_D),
                      mossdeathc(UIN_D), mossdeathn(UIN_D), kdshlw(UIN_D),
                      kddeep(UIN_D), decay(UIN_D), nup(UIN_D), totdzliq(UIN_D),
                      totdzavln(UIN_D), totnetnmin(UIN_D), totnextract(UIN_D) {
  
  for (int i = 0; i < MAX_SOI_LAY; ++i) {
    ltrflc[i] = UIN_D;
    ltrfln[i] = UIN_D;
    ch4_prod_rawc_monthly[i] = UIN_D;
    ch4_prod_soma_monthly[i] = UIN_D;
    ch4_prod_sompr_monthly[i] = UIN_D;
    ch4_prod_somcr_monthly[i] = UIN_D;
    ch4_oxid_monthly[i] = UIN_D;
    rtnextract[i] = UIN_D;
  }
};


Soil_Bgc::~Soil_Bgc() {
};

/** Writes Carbon values from the bd structure (BGC Data) into each soil
 *  layer held in the Ground object.
*/
void Soil_Bgc::assignCarbonBd2LayerMonthly() {
  Layer* currl = ground->fstsoill;

  while(currl!=NULL) {
    if(currl->isSoil) {
      currl->rawc  =  bd->m_sois.rawc[currl->solind-1];
      currl->soma  =  bd->m_sois.soma[currl->solind-1];
      currl->sompr =  bd->m_sois.sompr[currl->solind-1];
      currl->somcr =  bd->m_sois.somcr[currl->solind-1];
    } else {
      break;
    }

    currl = currl->nextl;
  }

  ground->organic.shlwc = bd->m_soid.shlwc;
  ground->organic.deepc = bd->m_soid.deepc;
  // What about mineral C ??
}


void Soil_Bgc::TriSolver(int matrix_size, double *A, double *D, double *C, double *B,double *X) {

  // B is known state, X is solution, A, D, C are used to construct tridiagonal matrix
  // note: commonly a, b, and c are in first matrix, here b and d are reversed
  // |  d1  c1  0   0  .  0  |   | x1 |   | b1 |
  // |  a2  d2  c2  0  .  0  |   | x2 |   | b2 |
  // |  0  a3  d3  c3  0  0  |   | x3 |   | b3 |
  // |  .  .              .  | x | .. | = | .. |
  // |  .  .             .   |   | .. |   | .. |
  // |  .  .             cn  |   | .. |   | .. |
  // |  0  0  0  0   an  dn  |   | xn |   | bn |

	int i;
	double xmult;

	for (i = 2; i <= matrix_size; i++) {
		xmult = A[i - 1] / D[i - 1];
		D[i] -= xmult * C[i - 1];
		B[i] -= xmult * B[i - 1];
	}

	X[matrix_size] = B[matrix_size] / D[matrix_size];
	for (i = matrix_size - 1; i >= 1; i--)
		X[i] = (B[i] - C[i] * X[i + 1]) / D[i];
}


void Soil_Bgc::CH4Flux(const int mind, const int id) {

  // Initial atmospheric CH4 concentration upper boundary condition
  // Fan et al. 2010 supplement Eq. 13. Units: umol L^-1
  const double upper_bound = 0.076; // >>> This should be input forcing 
  // Defining hourly time step
  double dt = 1.0 / HR_IN_DAY;
  // Unit conversion factors
  // Rates are in umol L^-1 hr^-1 unless stated in variable name
  // To convert from umol L^-1 hr^-1 to g C m^-3 hr^-1:
  // 1 umol C = 12e-6 g C
  // 1 L^-1   = 1000  m^-3
  // multiplying by the layer thickness dz gives m^-2
  double convert_umolL_to_gm3 = 0.012;
  // From Fan Eq. 8, components of CH4 mass balance prior to solver 
  // equal to prod - oxid - ebul - plant, units : umol L^-1 hr^-1 
  double partial_delta_ch4;
  // Diffusion-specific efflux from top soil layer to atmosphere 
  // in units umolL^-1hr^-1, umolL^-1day^-1, gm^-2day^-1 respectively
  double diff_efflux, diff_efflux_daily, diff_efflux_gm2day = 0.0;
  // Individual layer fluxes production, ebullition, oxidation
  // plant-mediation declared in loop to sum pfts, units : umol L^-1 hr^-1
  double prod, ebul, oxid = 0.0;
  // Individual layer fluxes and efflux units : g m^-2 hr^-1
  double prod_gm2hr, ebul_gm2hr, oxid_gm2hr, plant_gm2hr, efflux_gm2hr = 0.0;
  // Flux components cumulated over a day in units of umol L^-1 day^-1
  double plant_daily, ebul_daily = 0.0;
  // Flux components cumulated over a day in units of g m^-2 day^-1
  double plant_gm2day, ebul_gm2day, oxid_gm2day = 0.0;
  // Bunsen solubility coefficient (bun_sol - SB) in mL CH4/ mL H2O. Fan et al. 2010 
  // supplement Eq. 15. bun_sol is converted into a volume of ch4 (vol_ch4) for the 
  // ideal gas law. What is referred to as the mass-based Bunsen solubility coefficient
  // (SM) in Fan et al. 2010 supplement Eq. 16 we are referring to as the max concentration
  // for which methane can remain dissolved (i.e. not a bubble) this is given in
  // umol to relate to ch4 layer pool given in umol L^-1
  double bun_sol, vol_ch4, max_umol_ch4;
  // Pressure on ch4 used in Fan Eq. 16 for ebullition calculation
  // consisting of atmospheric (Pstd) and hydrostatic pressure (p_hydro)
  double p_hydro, pressure_ch4;

  updateKdyrly4all();

  //Some declarations for testing CH4 balance conservation
  double prev_pool[MAX_SOI_LAY] = {0};
  double curr_pool[MAX_SOI_LAY] = {0};
  double production[MAX_SOI_LAY] = {0};
  double ebullition[MAX_SOI_LAY] = {0};
  double oxidation[MAX_SOI_LAY] = {0};
  double plant_transport[MAX_SOI_LAY] = {0};
  double diffusion[MAX_SOI_LAY] = {0};
  double diffusion_sum = 0;
  double delta_pool[MAX_SOI_LAY] = {0};
  double delta_pool_sum = 0;

  //For storing methane movement data by layer for output  >>> may need to add more of these
  double ch4_ebul_layer[MAX_SOI_LAY] = {0};
  double ch4_oxid_layer[MAX_SOI_LAY] = {0};
  double ch4_flux_layer[MAX_SOI_LAY] = {0};


  int numsoill = cd->m_soil.numsl;
  // Tridiagonal matrix algorithm inputs
  // Main diagonal
  double main_diag[numsoill] = {0}; // BM: relating to lower boundary conditions - solver_l_bound
  // Sub-diagonals
  double sub_diag[numsoill] = {0}; 

  // Crank Nicolson discretization relations
  // Inverted sigma : Dg dt / dx^2
  double inv_sigma[numsoill] = {0};
  // Right hand side of tridiagonal matrix formulation
  // equal to the reaction-diffusion term needed for
  // solving - current pool + (prod - oxid - plant - ebul)
  double diff_react[numsoill] = {0};

  // diffusion coefficient
  double diff[numsoill] = {0};
  
  // ch4 production responses: kdc_ch4 * Tresp(q10) * SOM pool, Fan Eq. 9
  double prod_rawc_ch4[MAX_SOI_LAY] = {0};
  double prod_soma_ch4[MAX_SOI_LAY] = {0};
  double prod_sompr_ch4[MAX_SOI_LAY] = {0};
  double prod_somcr_ch4[MAX_SOI_LAY] = {0};

  // Temperature response (q10) for unsaturated and saturated layers
  double TResp_unsat, TResp_sat = 0;

  // Function of LAI to describe relative plant size ch4 transport capacity
  double fLAI[NUM_PFT];
  //Looping through pfts and assigning fgrow (0-1) Fan Eq. 20
  for(int ip=0; ip<NUM_PFT; ip++){
    if(cd->m_vegd.ffoliage[ip]<=0){
      fLAI[ip] = 0;
    }
    else{
      fLAI[ip] = cd->m_vegd.ffoliage[ip];
    }
  }

  // Setting soil oxidation to zero >>> not sure if this is needed or syntax convention to follow
  ed->d_soid.oxid = 0.0;
  
  // Setting layer pointer to track layer containing the water table
  Layer *wtlayer = ground->fstshlwl;

  Layer *currl;
  int il; //manual layer index tracker
  for (int j = 1; j <= HR_IN_DAY; j++) { //loop through time steps

    currl = ground->lstsoill; //reset currl to bottom of the soil stack
    il = numsoill-1; //reset manual layer index tracker. From 1 to allow future moss layer inclusion

    // zeroing rate-limiters before loading from parameter files
    double krawc_ch4, ksoma_ch4, ksompr_ch4, ksomcr_ch4 = 0.0;

    while(!currl->isMoss){

      // Unit conversion factors
      // Rates are in umol L^-1 hr^-1 unless stated in variable name
      // To convert from umol L^-1 hr^-1 to g C m^-3 hr^-1:
      // 1 umol C = 12e-6 g C
      // 1 L^-1   = 1000  m^-3
      // multiplying by the layer thickness dz gives m^-2
      // converting umol L^-1 to g m^-3
      double convert_umolL_to_gm2 = convert_umolL_to_gm3 * currl->dz;
      // converting g m^-3 to umol L^-1
      double convert_gm2_to_umolL = 1 / convert_umolL_to_gm2;

      krawc_ch4 = bgcpar.kdrawc_ch4[il];
      ksoma_ch4 = bgcpar.kdsoma_ch4[il];
      ksompr_ch4 = bgcpar.kdsompr_ch4[il];
      ksomcr_ch4 = bgcpar.kdsomcr_ch4[il];

      //Plant-mediation:

      double pft_transport[NUM_PFT] = {0};
      double plant = 0.0;

      for(int ip=0; ip<NUM_PFT; ip++){
        double layer_pft_froot = cd->m_soil.frootfrac[il][ip];

        // Fan 2013, Eq 19, rate constant for plant-aided CH4 transport (hr^-1) = 1.0 in (Zhuang, 2004)
        //but depths given in cm whereas we are using meters 
        // 10.1029/2004GB002239, but depths given in cm whereas we are using meters
        double rate_parameter_kp = 0.01; // >>> should be in cmt_calparbgc
        //See [Shannon and White, 1994; Shannon et al., 1996; Dise, 1993, Walter 1998] for pft transport capacity 
        if (ed->d_sois.ts[il]>0.0){
          pft_transport[ip] = rate_parameter_kp * layer_pft_froot * currl->ch4 * chtlu->transport_capacity[ip] * fLAI[ip]; // currl->poro *
        } else{
          pft_transport[ip] = 0.0;
        }
        
        // Catch for negative values - BM: add e-? to catch small numbers leading to rounding errors
        if (pft_transport[ip] < 0.0){
          pft_transport[ip] = 0.0;
        }

        plant += pft_transport[ip];

        //Storing plant transport values for output
        ed->output_ch4_transport[il][ip] = pft_transport[ip];
      }

      plant_transport[il] = plant;

      // BM : poro? below (or moved into above calculations?)
      // this did some weird stuff before - may need debugging session.
      // plant_gm2hr = plant * currl->poro * currl->dz * 1000.0;
      plant_gm2hr = plant * convert_umolL_to_gm2;

      //Diffusion:

      //If the layer contains the water table this provides a scaling fraction to define proportion above and below water table
      double saturated_fraction = ((currl->z + currl->dz) - ed->d_sois.watertab)/currl->dz;

      // If the layer is above the water table saturated_fraction is forced to 0.0
      // If the layer is below the water table saturated_fraction is forced to 1.0
      saturated_fraction = fmax(0.0, fmin(1.0, saturated_fraction));

      if (0.0<saturated_fraction && saturated_fraction<1.0){
        wtlayer = currl;
      }

      //Logarithmic interpolation between tortuosity and diffusion coefficient due to large
      //magnitude difference between liquid and air
      double tortuosity_sat = 0.66 * currl->getVolWater() * pow(currl->getVolWater()/(currl->poro), 3.0);
      double tortuosity_unsat = 0.66 * currl->getVolAir() * pow(currl->getVolAir() / currl->poro, 3.0);
      double tortuosity = pow(tortuosity_sat, saturated_fraction) * pow(tortuosity_unsat, 1 - saturated_fraction);
      double ch4_diffusion_coefficient = pow(CH4DIFFW, saturated_fraction) * pow(CH4DIFFA, 1 - saturated_fraction);
      //ch4_diffusion_coefficient in the atmosphere (physical constant) then scaled by temperature relation
      diff[il] = ch4_diffusion_coefficient * tortuosity * pow((currl->tem + 273.15) / 293.15, 1.75);

      //In order to prevent NaNs in the calculation of s[]
      if(diff[il] == 0){
        inv_sigma[il] = 0;
      }
      else{
        inv_sigma[il] = currl->dz * currl->dz / (diff[il] * dt);
      }

      //Oxidation:

      //Equations from Helene Genet to replace the ones from peat-dos-tem
      //HG: Why >= -2.0? and why 0.25?
      //BM: https://doi.org/10.1073/pnas.1420797112 ?
      // ^^ I don't think this is the one, but probably some kind of winter Q10
      if(currl->tem >= -2.0 && currl->tem < 0.000001){
        TResp_unsat = getRhq10(-2.1) * 0.25; //>>> getq10 - non-specific RH/ methanogenesis
        TResp_sat = getRhq10(-6.0) * 0.25;
      }// >>> get Rhq10 is heterotrophic respiration, need ch4 based q10?
      else if(currl->tem < -2.0){
        TResp_unsat = 0.0;
        TResp_sat = 0.0;
      }
      else{
        TResp_unsat = getRhq10(currl->tem-2.1);
        TResp_sat = getRhq10(currl->tem - 6.0);
      }

      //Fan 2013 Eq 18 - calculating oxidation
      //From paper: V max and k m are the Michaelis-Menten kinetics parameter and
      //set to 5 µmol L^-1 h^-1 and 20 µmol L^-1 (Walter & Heimann, 2000), respectively.
      //BM: does 5 and 20 need to be a parameter in param files? yes
      oxid = (1 - saturated_fraction) * (5.0 * currl->ch4 * TResp_unsat / (20.0 + currl->ch4)); // currl->getVolAir() * 
      //Code below was used for testing effect of partially saturated layer on oxidation
      // if (saturated_fraction > 0.0 && saturated_fraction < 1.0){
      //   oxid = 0.0;
      // }
      if (oxid < 0.000001){
        oxid = 0.0;
      }

      oxidation[il] = oxid;

      // HG: again do we need poro? we think it should be air content? test this
      // _gm2hr refers to unit conversion:
      // oxid is in units mu mol L^-1 hr^-1
      // 1 mu mol of C = 12e-6 g, ( * 12e-6)
      // L^-1 = 1000 m^-3 ( * 1000)
      // m^2 = m * m^-3 ( * dz)
      // 1 mu mol L^-1 hr^-1 = 12e-6 * 1000 * dz g C m^-2 hr^-1 ( * 0.012dz)
      oxid_gm2hr = oxid * convert_umolL_to_gm2;

      // accumulating to monthly to add to RH output
      ch4_oxid_monthly[il] += oxid_gm2hr;

      //Production:

      // Fan Eq. 9: rate constant * carbon pool * Q10
      // Saturated fraction is included here to
      // calculate carbon loss per pool per layer
      // prior to production calculation
      if(tmp_sois.rawc[il] > 0.0){
        prod_rawc_ch4[il] = saturated_fraction * (krawc_ch4 * tmp_sois.rawc[il] * TResp_sat);
        bd->d_soi2soi.ch4_rawc[il] += prod_rawc_ch4[il];
      }
      else{
        prod_rawc_ch4[il] = 0.0;
      }

      if(tmp_sois.soma[il] > 0.0){
        prod_soma_ch4[il] = saturated_fraction * (ksoma_ch4 * tmp_sois.soma[il] * TResp_sat);
        bd->d_soi2soi.ch4_soma[il] += prod_soma_ch4[il];
      }
      else{
        prod_soma_ch4[il] = 0.0;
      }

      if(tmp_sois.sompr[il] > 0.0){
        prod_sompr_ch4[il] = saturated_fraction * (ksompr_ch4 * tmp_sois.sompr[il] * TResp_sat);
        bd->d_soi2soi.ch4_sompr[il] += prod_sompr_ch4[il];
      }
      else{
        prod_sompr_ch4[il] = 0.0;
      }

      if(tmp_sois.somcr[il] > 0.0){
        prod_somcr_ch4[il] = saturated_fraction * (ksomcr_ch4 * tmp_sois.somcr[il] * TResp_sat);
        bd->d_soi2soi.ch4_somcr[il] += prod_somcr_ch4[il];
      }
      else{
        prod_somcr_ch4[il] = 0.0;
      }

      //Fan 2013 Eq. 9 for layers below the water table 
      //The /12 is from the conversion from grams to mol. 1 mol C = 12g
      //We want micro-mols (10^6 micro-mol)
      //Also converts m^3 to liters (10^-3 m^3)
      //U (unit conversion) = (1/12) * 10^6 * 10^-3

      //HG: This rhrawc_ch4 has different units than the corresponding CO2.
      //rhrawc doesn't make sense for this - it's not heterotrophic respiration
      //this is the rate, but modified by temperature and carbon content - rename the "rh" part to something relevant
      //it is hourly : rh = respiration heterotrophic. methanogenesis mg, methane production mp? 

      // accounting for carbon loss from SOM pools
      // I.e. som2prod = rawc - prod_rawc_ch4

      // rh_ch4's are in g m^-2
      // divide by dz to get g m^-3
      // to get umol L^-1 /12 /0.001
      prod = (convert_gm2_to_umolL) * (prod_rawc_ch4[il] + prod_soma_ch4[il] + prod_sompr_ch4[il] + prod_somcr_ch4[il]); //currl->getVolLiq() * 

      production[il] = prod;

      // testing effect of partially saturated layer
      // if (saturated_fraction > 0.0){
      //   prod = (1000.0 * (rhrawc_ch4[il] + rhsoma_ch4[il] + rhsompr_ch4[il] + rhsomcr_ch4[il]) / (currl->dz) / 12.0);
      // }
      // else{
      //   prod=0.0;
      // }

      // adding production in units of g m^2 hr^1 for output and comparison analysis
      prod_gm2hr = prod * convert_umolL_to_gm2;

      // Ebullition:

      // Fan 2013 Eq. 15. Bunsen solubility coefficient
      // Yamamoto, S. - Solubility of Methane in Distilled Water and Seawater
      // Journal of Chemical and Engineering Data, Vol. 21, No. 1, 1976
      // Weiss, R. F. - The solubility of nitrogen, oxygen and argon in water and seawater
      // Deep-Sea Research, 1970, Vol. 17, pp. 721 to 735
      // bun sol is a dimensionless quantity based on a least squares fit of empirical data
      // "the volume of saturating gas, V1, reduced to T° = 273.15 K, p° = 1 bar, which is absorbed
      // by unit volume V2* of pure solvent at the temperature of measurement and partial pressure of 1 bar."
      // Sazonov, V P; Shaw, DG (2006). "Introduction to the Solubility Data Series: 1.5.2. Physicochemical Quantities
      // and Units, A note on nomenclature, points 10 and 11"
      bun_sol = 0.05708 - 0.001545 * currl->tem + 0.00002069 * currl->tem * currl->tem; // mL CH4 / mL H2O Wania et al. 2010
      // mL / mL is equivalent to L/L or m3/m3
      // We are interested in a number or micromoles of CH4 per L of water i.e. umol/L
      // Therefore, we assume our ratio to be m3/m3 (to match ideal gas law units)
      // we assume that if saturated_fraction is 1.0 then the soil layer volume is totally
      // saturated, but that volume is not completely occupied by water... so we must consider
      // porosity (liquid and ice content as freezing is occurring)
      // m3 CH4 / m3 H2O in given layer (corrected for saturation, ice, and porosity)
      vol_ch4 = bun_sol; // * saturated_fraction * (1 - currl->frozenfrac) * currl->poro;

      // Hydrostatic pressure - P = rho * g * h
      // When considering hydrostatic pressure we want to know the height of the water above the center
      // of the layer, but this will be negative if the layer is above the water table so use fmax
      // if the layer contains the water table we assume an increase in pressure only if above the center
      // of the layer
      p_hydro = DENLIQ * G * (currl->z + (currl->dz / 2.0) - ed->d_sois.watertab);

      // Fan 2013 Eq. 16. Mass-based Bunsen solubility coefficient
      // fmax catch so pressure is never lower than atmospheric pressure
      pressure_ch4 = fmax(Pstd, Pstd + p_hydro);                                                                   // Pa = kgm^-1s^-2
      max_umol_ch4 = 1e3 * pressure_ch4 * vol_ch4 / (GASR * (currl->tem + 273.15));                  // mol m^-3 ( * 1e3 -> umol L^-1)

      double rate_parameter_kh = 1.0; // >>> cmt_calparbgc

      if (ed->d_sois.ts[il]>=0.0){// if not frozen
        ebul = saturated_fraction * (currl->ch4 - max_umol_ch4) * rate_parameter_kh; // currl->getVolLiq() *
      }
      else {
        ebul = 0.0;
      }

      if (ebul <= 0.0) {
        ebul = 0.0;
      }

      ebullition[il] = ebul;
      
      // Code below was used for testing effect of partially saturated layer on ebullition
      // if (saturated_fraction > 0.0){
      //   if(currl->tem > 1.0){
      //     ebul = (currl->ch4 - bun_sol_mass) * rate_parameter_kh;
      //   } else{
      //     ebul = 0.0;
      //   }
      //   if (ebul < 0.0000001) {
      //     ebul = 0.0;
      //   }
      // } else{
      //   ebul=0.0;
      // }

      // HG: Scaling by the LWC here could actually have relevance when scaled up to the /m2, as:
      // This assump- tion is supported by the fact that wetland soils are generally very porous, 
      // the relative pore volume being often greater than 90% [Scheffer and Schachtschabel, 1982],
      // and the finding that the velocity of bubbles ascending in pure water lies in the order of 
      // 1- 10 cm s -1 [e.g. Shafer and Zare, 1991].  
      ebul_gm2hr = ebul * convert_umolL_to_gm2;

      ebul_daily += ebul; //cumulated over 1 time step, 1 hour Y.MI
      ebul_gm2day += ebul_gm2hr; //cumulated over 1 time step, 1 hour - in units of g m^-2 day^-1

      // if (currl->tem < 0.0) {
      //   ebul_gm2day = 0.0;
      // }

      //Accumulating ebullitions per layer across timesteps for output
      ch4_ebul_layer[il] += ebul_gm2hr;
      ch4_oxid_layer[il] += oxid_gm2hr;

      plant_daily += plant; //cumulated over 1 day, 24 time steps, Y.MI
      plant_gm2day += plant_gm2hr; //cumulated over 1 day, 24 time steps, Y.MI - in units of g m^-2 day^-1

      oxid_gm2day += oxid_gm2hr; //cumulated over 1 day, 24 time steps, Y.MI
      ed->d_soid.oxid = oxid_gm2day;// - in units of g m^-2 day^-1

      //Fan Eq. 8 (mostly?)
      //change of CH4 conc./time = CH4 production rate - diffusion transport/soil depth
      // - Ebullition - Oxidation - CH4 emitted through plant process
      //This does not specifically include diff[] right now - see
      // calculation of V[] below
      partial_delta_ch4 = prod - ebul - oxid - plant;

      // Main diagnonal
      if (il == (numsoill - 1)) {
        main_diag[il] = 1 + inv_sigma[il];
      } else {
        main_diag[il] = 2 + inv_sigma[il];
      }
      // upper and lower sub diagonals
      if (il == 1) {
        sub_diag[il] = -1.0 - upper_bound;
      } else {
        sub_diag[il] = -1.0;
      }

      // Right hand side of tridiagonal matrix algorithm formula
      // This is determined from the crank nicolson discretization
      // for the reaction-diffusion equation as well as some
      // rearranging to bring across s (or 1 / sigma, where
      // typically sigma = Dg dt/dx^2, see below TriSolver() call
      // for additional details).
      // Relates to the diffusion-reaction term considering
      // the current pool ch4, and the partial delta from prod
      // oxid, plant, and ebul
      diff_react[il] = inv_sigma[il] * currl->ch4 + inv_sigma[il] * dt * partial_delta_ch4;

      if (diff_react[il] < 0.0000001) {
        diff_react[il] = 0.0;
      }

      prev_pool[il] = currl->ch4;

      currl = currl->prevl;
      il--; //Incrementing manual layer index tracker
    } //end of bottom up layer loop

    TriSolver(numsoill - 1,   sub_diag,  main_diag,  sub_diag,  diff_react,  diff_react);
    //TriSolver(matrix_size, *A, *D, *C, *B, *X)

    // Matrix equation: A X = B, X = A^-1 B

    // |  d1  c1  0   0  .  0  |   | x1 |   | b1 |
    // |  a2  d2  c2  0  .  0  |   | x2 |   | b2 |
    // |  0  a3  d3  c3  0  0  |   | x3 |   | b3 |
    // |  .  .              .  | x | .. | = | .. |
    // |  .  .              .  |   | .. |   | .. |
    // |  .  .             cn  |   | .. |   | .. |
    // |  0  0  0  0   an  dn  |   | xn |   | bn |

    // B (or V) is known state, X (or V replaced) is solution,
    // A, D, C are used to construct tridiagonal matrix
    // A and C are equal subdiagonals
    // D is the main diagonal

    // generally for crank nicolson discretization:
    //  r = dt / (dx)^2
    //  a = -r/2, c = -r/2
    //  d = (1 + r)
    //  b = (r/2) (x^n_i+1) + (1-r)(x^n_i) + (r/2)(x^n_i-1)
    //  assuming dCh4/dt = d^2Ch4/dx^2
    //  see: https://www.quantstart.com/articles/Crank-Nicholson-Implicit-Scheme/
    
    // In our case this is not simply linear diffusion as
    // we have production, oxidation, plant-transport, and
    // ebullition transport processes. This is called the 
    // Reaction-Diffusion equation, and is considered  by our 
    // partial_delta_ch4 term which adds/subtracts
    // from our layer concentrations, and a varying diffusion
    // coefficient, and these must be considered
    // when we find our solution.

    // Assuming the reaction-diffusion equation is
    // dCh4/dt = d^2Ch4/dx^2 + f(u, x)
    // >>> ... add crank nicolson discretization

    // In our matrix form this looks similarly to 
    // A X = B + f(u,x)
    // where f(u,x) = dt * (prod - oxid - plant - ebul)
    // to be converted to a pool for comparison with
    // current ch4 pool distribution. A is our 
    // tridiagonal matrix which we can remove a factor
    // r / sigma from 
    // Dg dt/dx**2 A X = B + f(u,x)
    // A X = (B + f(u,x)) * dx**2 / Dg * dt
    // where diagonals of matrix A become factors of
    // the inverse of r or sigma.

    currl = ground->fstshlwl; //reset currl to top of the soil stack
    il = 1; //Reset manual layer index tracker. From 1 to allow moss layer in future

    while(currl && currl->isSoil){

      currl->ch4 = diff_react[il];

      // For testing CH4 balance conservation
      curr_pool[il] = diff_react[il];
      delta_pool[il] = curr_pool[il]-prev_pool[il];
      delta_pool_sum += delta_pool[il];

      diffusion[il] = curr_pool[il] - prev_pool[il] + production[il] - oxidation[il] - plant_transport[il] - ebullition[il];

      diffusion_sum += diffusion[il];

      currl = currl->nextl;
      il++;

    }

    // BM - See R. Wania 2010 and Fick's Law:
    diff_efflux = -diffusion_sum;
    // diff_efflux = diff[1] * (ground->fstshlwl->ch4 - upper_bound) / ground->fstshlwl->dz; // flux of every time step, 1 hour, Y.MI

    delta_pool_sum = 0.0;

    // if (diff_efflux < 0.000001) { //This can be negative
    //   diff_efflux = 0.0;
    // }

    diff_efflux_daily += diff_efflux; //flux cumulated over 1 day, 24 time steps, Y.MI
  } // end of time steps looping

  //Storing daily CH4 movement for output
  for(int layer=0; layer<MAX_SOI_LAY; layer++){
    bd->d_soi2soi.ch4_ebul[layer] = ch4_ebul_layer[layer];
    bd->d_soi2a.ch4_oxid[layer] = ch4_oxid_layer[layer];
    bd->d_soi2soi.ch4_diff[layer] = diff[layer];
  }

  // Store ebullition and veg flux values (mostly for output)
  bd->d_soid.ch4ebulsum = ebul_gm2day;

  // Modifying ch4 pool by ebullitive flux if water table 
  // is not at soil surface
  // if (wtlayer != ground->fstshlwl){
  //   wtlayer->ch4 += ebul_daily;
  //   ebul_gm2day = 0.0;
  // }
    
  // If the moss layer is considered for CH4 in the future, the following will need
  //  to be modified to start at the moss layer and il should be set to 0.
  currl = ground->fstshlwl; // reset currl to top of the soil stack
  il = 1; //reset manual layer index tracker.
  while(currl && currl->isSoil){
    bd->daily_ch4_pool[id][il] = currl->ch4; //>>> UNITS: these should be in g m^2
    il++;
    currl = currl->nextl;
  }

  Layer* topsoil = ground->fstshlwl;

  // diffusion efflux unit conversion - g m^-2 d^-1
  diff_efflux_gm2day = diff_efflux_daily * topsoil->dz * 1000.0; // topsoil->getVolAir() * >>> should be needed as tortuosity considered

  //Fan Eq. 21
  //Fan 2013 supplement "it is assumed that 50% of CH4 transported by plant is oxidized by rhizospheric oxidation before 
  //being released into the atmosphere" hence 0.5
  //ebullitions counldn't reach the surface, eg. when water table is below the soil surface, are not included, Y.MI
  // BM: It looks like ebulllition is added to total efflux here even if the water table is below the soil surface
  efflux_gm2hr = 0.5 * plant_gm2day + diff_efflux_gm2day + ebul_gm2day;

  //Store ebullition and veg flux values (mostly for output)
  ed->daily_total_plant_ch4[id] = plant_gm2day;

  diff_efflux_daily = 0.0; //Y.Mi
  plant_gm2day =0.0; //Y.Mi
  ebul_gm2day = 0.0; //Y.Mi

  //HG: do we need to output this ratio - it would be good to output each surface flux so ratios can be calculated in post      
  if (efflux_gm2hr < 0.000001) {
    // efflux_gm2hr = 0.0;
    ed->d_soid.dfratio = 0.0;
  } else {
    ed->d_soid.dfratio = diff_efflux_gm2day / efflux_gm2hr * 100.0;
  }

  // The 0.012 is to convert umol to grams - looks like this reverses the conversion done in Prod equation
  // TODO check: should probably be 0.000012 >>> UNIT CONVERSION CHECK FOR ALL
  bd->d_soi2a.ch4efflux = 0.012 * efflux_gm2hr;

  //Store daily efflux value for output
  bd->daily_ch4_efflux[id] = bd->d_soi2a.ch4efflux;
}


/** Writes Carbon values from each of the Ground object's Layers into the bd 
    structure (BGC Data).
*/
void Soil_Bgc::assignCarbonLayer2BdMonthly() {
  Layer* currl = ground->fstsoill;
  int lstprocessedlayer = 0;

  while(currl!=NULL) {
    if(currl->isSoil) {
      lstprocessedlayer = currl->solind-1;
      bd->m_sois.rawc[currl->solind-1] = currl->rawc;
      bd->m_sois.soma[currl->solind-1] = currl->soma;
      bd->m_sois.sompr[currl->solind-1]= currl->sompr;
      bd->m_sois.somcr[currl->solind-1]= currl->somcr;
    } else {
      break;
    }

    currl = currl->nextl;
  }

  for(int il = lstprocessedlayer+1; il<MAX_SOI_LAY; il++) {
    bd->m_sois.rawc[il] = 0.0;
    bd->m_sois.soma[il] = 0.0;
    bd->m_sois.sompr[il] = 0.0;
    bd->m_sois.somcr[il] = 0.0;
  }
}

void Soil_Bgc::prepareIntegration(const bool &mdnfeedback,
                                  const bool &mdavlnflg,
                                  const bool &mdbaseline) {
  this->set_nfeed(mdnfeedback);
  this->set_avlnflg(mdavlnflg);
  this->set_baseline(mdbaseline);

  // moss death rate if any (from Vegetation_bgc.cpp)
  mossdeathc    = bd->m_v2soi.mossdeathc;
  mossdeathn    = bd->m_v2soi.mossdeathn;

  // litter-fall C/N from Vegetation_bgc.cpp
  double blwlfc = bd->m_v2soi.ltrfalc[I_root];
  double abvlfc = fmax(0., bd->m_v2soi.ltrfalcall - blwlfc);
  double blwlfn = bd->m_v2soi.ltrfaln[I_root];
  double abvlfn = fmax(0., bd->m_v2soi.ltrfalnall - blwlfn);

  // Maybe the "below" calc should be done like this?:
  // double abvlfc = bd->m_v2soi.ltrfalc[I_stem] + bd->m_v2soi.ltrfalc[I_leaf];
  // double abvlfn = bd->m_v2soi.ltrfaln[I_stem] + bd->m_v2soi.ltrfaln[I_leaf];

  for(int i=0; i<cd->m_soil.numsl; i++) {
    //FIX litterfall should be added to the shallow layer
    //There *must* be a shallow layer
    //if(fstshlwl!=NULL). if(currl->isShlw() && prevl != shlw)
    //  add abvlfc and this shallow layer's blwlfc fraction
    //else
    //  just root death?
    //else if fstshlwl==NULL and there is litterfall, ERROR
    //if (cd->m_soil.type[i]>0) { WRONG
    //soillayer sl = ground ;lksadjf; [i];

    if( (i==0 && cd->m_soil.type[i]==1) ||
        ((i>0 && cd->m_soil.type[i]==1) && (cd->m_soil.type[i-1]!=1)) ) {
      // always put the litterfall from vascular and moss in the
      // first non-moss soil layer
      ltrflc[i] = abvlfc + bd->m_v2soi.mossdeathc + bd->m_v2soi.rtlfalfrac[i] * blwlfc;
      ltrfln[i] = abvlfn + bd->m_v2soi.mossdeathn + bd->m_v2soi.rtlfalfrac[i] * blwlfn;

      abvlfc = 0.;
      abvlfn = 0.;
    } else if(cd->m_soil.type[i]>0) {
      // root death is directly put into each soil layer
      ltrflc[i] = bd->m_v2soi.rtlfalfrac[i] * blwlfc;
      ltrfln[i] = bd->m_v2soi.rtlfalfrac[i] * blwlfn;
    }

    if (ltrflc[i]>0. && ltrfln[i]> 0.) {
      bd->m_soid.ltrfcn[i] = ltrflc[i]/ltrfln[i];
    } else {
      bd->m_soid.ltrfcn[i] = 0.0;
    }
  }

  //SOM decompositin Kd will updated based on previous 12
  //  month accumulative littering C/N
  updateKdyrly4all();

  if (this->nfeed == 1) {
    // vegetation root N extraction
    for (int i=0; i<cd->m_soil.numsl; i++) {
      rtnextract[i] = bd->m_soi2v.nextract[i];
    }

    //soil liq. water controlling factor for soil N
    //  minralization/immobilization and root N extraction
    for (int i=0; i<cd->m_soil.numsl; i++) {
      bd->m_soid.knmoist[i] = getKnsoilmoist(ed->m_soid.sws[i]);
    }

    //prepare total liq water and available N in soil zones above drainage depth
    //In this version of model, N leaching loss is assumed to with
    // drainage flow from all above-drainage profile as the
    // drainage zone - needs improvement here!
    totdzliq     = 0.;
    totdzavln    = 0.;

    for(int i=0; i<cd->m_soil.numsl; i++) {
      if((cd->m_soil.z[i]+cd->m_soil.dz[i]) <= ed->m_sois.draindepth) { //note: z is at the top of a layer
        totdzliq += fmax(0., ed->m_sois.liq[i]);
        totdzavln += fmax(0., bd->m_sois.avln[i]);
      } else {
        if (cd->m_soil.z[i]<ed->m_sois.draindepth) { //note: z is at the top of a layer
          double fdz = (ed->m_sois.draindepth - cd->m_soil.z[i])
                       /cd->m_soil.dz[i];
          totdzliq += fmax(0., ed->m_sois.liq[i])*fdz;
          totdzavln += fmax(0., bd->m_sois.avln[i])*fdz;
        } else {
          break;
        }
      }
    }

    if(cd->yrsdist < cd->fri) {
      bd->m_a2soi.orgninput = fd->fire_a2soi.orgn/12.;
    }
  }

  // dead standing C due to fire will put into ground debris
  d2wdebrisc = bd->m_v2soi.d2wdebrisc;

  if (this->nfeed == 1) {
    d2wdebrisn = bd->m_v2soi.d2wdebrisn;
  }
};

void Soil_Bgc::afterIntegration() {
  for(int i=0; i<cd->m_soil.numsl; i++) {
    bd->m_soid.tsomc[i] = bd->m_sois.rawc[i] + bd->m_sois.soma[i]
                          + bd->m_sois.sompr[i] + bd->m_sois.somcr[i];
  }
};

void Soil_Bgc::clear_del_structs(){
  //soistate_bgc del_sois
  del_sois.wdebrisc = 0.0;
  del_sois.wdebrisn = 0.0;

  //soi2soi_bgc del_soi2soi
  del_soi2soi.netnminsum = 0.0;
  del_soi2soi.nimmobsum = 0.0;

  //soi2atm_bgc del_soi2a
  del_soi2a.rhwdeb = 0.0;
  del_soi2a.rhrawcsum = 0.0;
  del_soi2a.rhsomasum = 0.0;
  del_soi2a.rhsomprsum = 0.0;
  del_soi2a.rhsomcrsum = 0.0;
  del_soi2a.rhtot = 0.0;

  //soi2lnd_bgc del_soi2l
  del_soi2l.doclost = 0.0;
  del_soi2l.avlnlost = 0.0;
  del_soi2l.orgnlost = 0.0;

  //atm2soi_bgc del_a2soi
  del_a2soi.orgcinput = 0.0;
  del_a2soi.orgninput = 0.0;
  del_a2soi.avlninput = 0.0;

  for(int il=0; il<MAX_SOI_LAY; il++){
    del_sois.rawc[il] = 0.0;
    del_sois.soma[il] = 0.0;
    del_sois.sompr[il] = 0.0;
    del_sois.somcr[il] = 0.0;
    del_sois.orgn[il] = 0.0;
    del_sois.avln[il] = 0.0;

    del_soi2soi.netnmin[il] = 0.0;
    del_soi2soi.nimmob[il] = 0.0;
    del_soi2soi.ch4_rawc[il] = 0.0;
    del_soi2soi.ch4_soma[il] = 0.0;
    del_soi2soi.ch4_sompr[il] = 0.0;
    del_soi2soi.ch4_somcr[il] = 0.0;

    del_soi2a.rhrawc[il] = 0.0;
    del_soi2a.rhsoma[il] = 0.0;
    del_soi2a.rhsompr[il] = 0.0;
    del_soi2a.rhsomcr[il] = 0.0;

    ch4_prod_rawc_monthly[il] = 0.0;
    ch4_prod_soma_monthly[il] = 0.0;
    ch4_prod_sompr_monthly[il] = 0.0;
    ch4_prod_somcr_monthly[il] = 0.0;
    ch4_oxid_monthly[il] = 0.0;
  }
};

void Soil_Bgc::initializeState() {

  // Set initiate state variable
  double shlwc = chtlu->initshlwc;
  double deepc = chtlu->initdeepc;
  double minec = chtlu->initminec;

  initSoilCarbon(shlwc, deepc, minec);
  assignCarbonLayer2BdMonthly();

  bd->m_sois.wdebrisc = 0;

  // Initial N based on input total and SOM C profile
  double sum_total_C = shlwc + deepc + minec;

  for (int il=0; il<MAX_SOI_LAY; il++ ) {
    double total_monthly_C = bd->m_sois.rawc[il] +
                             bd->m_sois.soma[il] +
                             bd->m_sois.sompr[il] +
                             bd->m_sois.somcr[il];

    // Available N should only be calculated where roots are actively
    // turning over (ie, root zone)
    bool root_presence = false;
    double sum_root_frac = 0.0;

    for (int ipft=0; ipft<NUM_PFT; ++ipft) {
      sum_root_frac += cd->m_soil.frootfrac[il][ipft];
    }

    if (sum_root_frac > 0.0) {
      root_presence = true;
    }

    if (total_monthly_C > 0.0 && sum_total_C > 0.0) {

      if (root_presence) {
        bd->m_sois.avln[il] = chtlu->initavln * total_monthly_C/sum_total_C;
      } else {
        bd->m_sois.avln[il] = 0.0;
      }

      bd->m_sois.orgn [il] = chtlu->initsoln * total_monthly_C/sum_total_C;

    } else {
      bd->m_sois.avln [il] = 0.0;
      bd->m_sois.orgn [il] = 0.0;
    }
  } // end soil layer loop
}

void Soil_Bgc::set_state_from_restartdata(const RestartData & rdata) {

  for (int il =0; il<MAX_SOI_LAY; il++) {

    if(rdata.rawc[il]>=0) {
      bd->m_sois.rawc[il] = rdata.rawc[il];
    } else {
      bd->m_sois.rawc[il] = 0;
    }

    if(rdata.soma[il]>=0) {
      bd->m_sois.soma[il] = rdata.soma[il];
    } else {
      bd->m_sois.soma[il] = 0;
    }

    if(rdata.sompr[il]>=0) {
      bd->m_sois.sompr[il]= rdata.sompr[il];
    } else {
      bd->m_sois.sompr[il] = 0;
    }

    if(rdata.somcr[il]>=0) {
      bd->m_sois.somcr[il]= rdata.somcr[il];
    } else {
      bd->m_sois.somcr[il] = 0;
    }

    if(rdata.orgn[il]>=0) {
      bd->m_sois.orgn[il] = rdata.orgn[il];
    } else {
      bd->m_sois.orgn[il] = 0;
    }

    if(rdata.avln[il]>=0) {
      bd->m_sois.avln[il] = rdata.avln[il];
    } else {
      bd->m_sois.avln[il] = 0;
    }

    for(int i=0; i<10; i++) {
      bd->prvltrfcnque[il].clear();
      double tmpcn = rdata.prvltrfcnA[i][il];

      if(tmpcn!=MISSING_D) {
        bd->prvltrfcnque[il].push_back(tmpcn);
      }
    }
  }

  bd->m_sois.wdebrisc = rdata.wdebrisc;
  bd->m_sois.wdebrisn = rdata.wdebrisn;
  assignCarbonBd2LayerMonthly();
};

void Soil_Bgc::initializeParameter() {
  BOOST_LOG_SEV(glg, note) << "Initializing parameters in Soil_Bgc from chtlu (CohortLookup) values.";
  calpar.micbnup    = chtlu->micbnup;
  calpar.kdcrawc    = chtlu->kdcrawc;
  calpar.kdcsoma    = chtlu->kdcsoma;
  calpar.kdcsompr   = chtlu->kdcsompr;
  calpar.kdcsomcr   = chtlu->kdcsomcr;
  calpar.kdcrawc_ch4 = chtlu->kdcrawc_ch4;
  calpar.kdcsoma_ch4 = chtlu->kdcsoma_ch4;
  calpar.kdcsompr_ch4 = chtlu->kdcsompr_ch4;
  calpar.kdcsomcr_ch4 = chtlu->kdcsomcr_ch4;
  bgcpar.rhq10      = chtlu->rhq10;
  bgcpar.moistmin   = chtlu->moistmin;
  bgcpar.moistmax   = chtlu->moistmax;
  bgcpar.moistopt   = chtlu->moistopt;
  bgcpar.fsoma      = chtlu->fsoma;
  bgcpar.fsompr     = chtlu->fsompr;
  bgcpar.fsomcr     = chtlu->fsomcr;
  bgcpar.som2co2    = chtlu->som2co2;
  bgcpar.lcclnc     = chtlu->lcclnc;
  bgcpar.kn2        = chtlu->kn2;
  bgcpar.propftos   = chtlu->propftos;
  bgcpar.fnloss     = chtlu->fnloss;
  bgcpar.nmincnsoil = chtlu->nmincnsoil;

  BOOST_LOG_SEV(glg, note) << "Calculating parameter in Soil_Bgc from Jenkinson and Rayner (1977).";
  // Alternatively these can be estimated from Ks calibrated.
  // Jenkinson and Rayner (1977):
  //   1t plant C / ha / yr for 10,000yrs, will produce:
  //   0.48t RAWC + 0.28t SOMA + 11.3t SOMPR + 12.2t SOMCR = 24.26 tC
  bgcpar.eqrawc = 0.48 / (0.48 + 0.28 + 11.3 + 12.2);
  bgcpar.eqsoma = 0.28 / (0.48 + 0.28 + 11.3 + 12.2);
  bgcpar.eqsompr = 11.3 / (0.48 + 0.28 + 11.3 + 12.2);
  bgcpar.eqsomcr = 12.2 / (0.48 + 0.28 + 11.3 + 12.2);

  BOOST_LOG_SEV(glg, note) << "Calculating decay in Soil_Bgc.";
  decay = 0.26299 +
          (1.14757 * bgcpar.propftos) -
          (0.42956 * pow((double)bgcpar.propftos, 2.0));
}

void Soil_Bgc::initSoilCarbon(double & initshlwc, double & initdeepc,
                              double & initminec) {
  for(int il =0; il <MAX_SOI_LAY ; il++) {
    bd->m_sois.rawc[il]  = 0.;
    bd->m_sois.soma[il]  = 0.;
    bd->m_sois.sompr[il] = 0.;
    bd->m_sois.somcr[il] = 0.;
  }

  initOslayerCarbon(initshlwc, initdeepc);

  if (initminec<0.10) {
    initminec = 0.10;
  }

  initMslayerCarbon(initminec);
};

// initialize Organic Soil layers' carbon based on input layer thickness
void Soil_Bgc::initOslayerCarbon(double & shlwc, double & deepc) {
  Layer* currl = ground->fstsoill;
  double dbmtop = 0.0;
  double dbmbot = 0.0;
  double cumcarbontop = 0.0;
  double cumcarbonbot = 0.0;
  double cumcarbonshlw = 0.0;
  double cumcarbondeep = 0.0;

  while(currl!=NULL) {
    if(currl->isSoil) {
      if (currl->isMineral || currl->isRock) {
        break;
      }

      if (currl==ground->fstmossl
          || currl==ground->fstshlwl
          || currl==ground->fstdeepl) {
        dbmtop = 0.0;
        cumcarbontop = 0.0;
      }

      dbmbot = dbmtop+currl->dz;

      if(currl->isFibric) {
        cumcarbonbot = ground->soildimpar.coefshlwa
                       * pow(dbmbot*100., ground->soildimpar.coefshlwb*1.)
                       * 10000; //from gC/cm2 to gC/m2
        cumcarbonshlw += cumcarbonbot - cumcarbontop;
      } else if(currl->isHumic) {
        cumcarbonbot = ground->soildimpar.coefdeepa
                       * pow(dbmbot*100., ground->soildimpar.coefdeepb*1.)
                       * 10000; //from gC/cm2 to gC/m2
        cumcarbondeep += cumcarbonbot - cumcarbontop;
      }

      if( cumcarbonbot - cumcarbontop > 0.0 ) {
        if (currl->isOrganic) {
          currl->rawc  = bgcpar.eqrawc * (cumcarbonbot - cumcarbontop); //note: those eq-fractions of SOM pools must be estimated before
          currl->soma  = bgcpar.eqsoma * (cumcarbonbot - cumcarbontop);
          currl->sompr = bgcpar.eqsompr * (cumcarbonbot - cumcarbontop);
          currl->somcr = bgcpar.eqsomcr * (cumcarbonbot - cumcarbontop);
        } else if (currl->isMoss) {

          // moss layers are not 'normal' soil organic layers, so contain
          // no C in the normal soil C pools
          currl->rawc  = 0.0;
          currl->soma  = 0.0;
          currl->sompr = 0.0;
          currl->somcr = 0.0;

        } else {
          currl->rawc  = 0.0;
          currl->soma  = 0.0;
          currl->sompr = 0.0;
          currl->somcr = 0.0;
        }
      } else {
        currl->rawc  = 0.0;
        currl->soma  = 0.0;
        currl->sompr = 0.0;
        currl->somcr = 0.0;
      }

      cumcarbontop = cumcarbonbot;
      dbmtop = dbmbot;
    } else {
      break;
    }

    currl = currl->nextl;
  }

  //Above calculation will give all soil organic layer C content UPON two
  //  parameters and thickness, the following will adjust that by
  //  actual initial SOMC amount as an input
  double adjfactor = 1.0;
  currl = ground->fstshlwl;

  while(currl!=NULL) {
    if(currl->isSoil) {
      if(currl->isOrganic) {
        if (currl->isFibric) {
          adjfactor = shlwc/cumcarbonshlw;
        } else if (currl->isHumic) {
          adjfactor = deepc/cumcarbondeep;
        }

        currl->rawc  *= adjfactor;
        currl->soma  *= adjfactor;
        currl->sompr *= adjfactor;
        currl->somcr *= adjfactor;
      } else {
        break;
      }
    }

    currl = currl->nextl;
  }
};

void Soil_Bgc::initMslayerCarbon(double & minec) {
  double dbm = 0.;
  double prevcumcarbon = 0.;
  double cumcarbon = 0.;
  double ca =  ground->soildimpar.coefminea;
  double cb = ground->soildimpar.coefmineb;
  Layer* currl = ground->fstminel;
  double totsomc = 0.0;

  while(currl!=NULL) {
    if(currl->isSoil) {
      dbm += currl->dz;
      cumcarbon = ca*(pow(dbm*100,cb))*10000;

      if(cumcarbon-prevcumcarbon>0.01 && dbm<=2.0) {  // somc will not exist more than 2 m intially
        currl->rawc  = bgcpar.eqrawc * (cumcarbon -prevcumcarbon);
        currl->soma  = bgcpar.eqsoma * (cumcarbon -prevcumcarbon);
        currl->sompr = bgcpar.eqsompr * (cumcarbon -prevcumcarbon);
        currl->somcr = bgcpar.eqsomcr * (cumcarbon -prevcumcarbon);
      } else {
        currl->rawc  = 0.0;    //
        currl->soma  = 0.0;
        currl->sompr = 0.0;
        currl->somcr = 0.0;
      }

      prevcumcarbon = cumcarbon;
      totsomc += currl->rawc+currl->soma+currl->sompr+currl->somcr;
    } else {
      break;
    }

    currl =currl->nextl;
  }

  //Above calculation will give all soil mineral layer C content UPON
  //  two parameters, the following will adjust that by actual
  //  initial MINEC amount as an input
  double adjfactor = 1.0;

  if (totsomc>0.) {
    adjfactor=minec/totsomc;
  }

  currl = ground->fstminel;

  while(currl!=NULL) {
    if(currl->isSoil) {
      currl->rawc *= adjfactor;
      currl->soma *= adjfactor;
      currl->sompr *= adjfactor;
      currl->somcr *= adjfactor;
    }

    currl =currl->nextl;
  }
};

// before delta and afterdelta are considered in Integrator
void Soil_Bgc::deltac() {
  double krawc = 0.0;     // for littering materials (in model, rawc)
  double ksoma = 0.0;     // for active SOM (in model, soma)
  double ksompr = 0.0;    // for PR SOM (in model, sompr)
  double ksomcr = 0.0;    // for CR SOM (in model, somcr)

  for (int il =0; il<cd->m_soil.numsl; il++) {
    //HG: 01122023 - this condition allows for winter respiration
    //(Natali et al. 2019, Nature Climate Change)
    if (ed->m_sois.ts[il] <0.) {
      bd->m_soid.rhmoist[il] = 1;
    } else {
      // Yuan: vwc normalized by total pore - this will allow
      // respiration (methane/oxidation) implicitly
      // BM: Not sure what this comment means? HG?
      bd->m_soid.rhmoist[il] = getRhmoist( ed->m_soid.sws[il],
                                           bgcpar.moistmin,
                                           bgcpar.moistmax,
                                           bgcpar.moistopt );
    }

    bd->m_soid.rhq10[il] = getRhq10(ed->m_sois.ts[il]);
    krawc  = bgcpar.kdrawc[il];
    ksoma  = bgcpar.kdsoma[il];
    ksompr = bgcpar.kdsompr[il];
    ksomcr = bgcpar.kdsomcr[il];

    if(tmp_sois.rawc[il]>0.) {
      del_soi2a.rhrawc[il] = (krawc * tmp_sois.rawc[il]
                              * bd->m_soid.rhmoist[il] * bd->m_soid.rhq10[il]);
    } else {
      del_soi2a.rhrawc[il] = 0.;
    }

    if(tmp_sois.soma[il]>0) {
      del_soi2a.rhsoma[il] = ksoma*tmp_sois.soma[il]
                             * bd->m_soid.rhmoist[il] * bd->m_soid.rhq10[il];
    } else {
      del_soi2a.rhsoma[il] = 0.;
    }

    if(tmp_sois.sompr[il]>0) {
      del_soi2a.rhsompr[il] = ksompr*tmp_sois.sompr[il]
                              * bd->m_soid.rhmoist[il] * bd->m_soid.rhq10[il];
    } else {
      del_soi2a.rhsompr[il] = 0.;
    }

    if(tmp_sois.somcr[il]>0) {
      del_soi2a.rhsomcr[il] = ksomcr*tmp_sois.somcr[il]
                              * bd->m_soid.rhmoist[il] * bd->m_soid.rhq10[il];
    } else {
      del_soi2a.rhsomcr[il] = 0.;
    }

    del_soi2soi.ch4_rawc[il] = bd->m_soi2soi.ch4_rawc[il];
    del_soi2soi.ch4_soma[il] = bd->m_soi2soi.ch4_soma[il];
    del_soi2soi.ch4_sompr[il] = bd->m_soi2soi.ch4_sompr[il];
    del_soi2soi.ch4_somcr[il] = bd->m_soi2soi.ch4_somcr[il];

  } // loop for each soil layer

  // for wood debris at ground surface
  del_soi2a.rhwdeb = 0.;

  if(tmp_sois.wdebrisc > 0) {
    double rhmoist_wd = 0.0;
    double rhq10_wd = 0.0;
    double wdkd = 0.0;

    for (int il =0; il<cd->m_soil.numsl; il++) {
      if(cd->m_soil.type[il] > 0) { // 0 moss 1 shlw, and 2 deep
        rhmoist_wd = bd->m_soid.rhmoist[il];
        rhq10_wd = bd->m_soid.rhq10[il];
        wdkd = bgcpar.kdrawc[il];
        break; // Taking the first non-moss layer's only for wood debris
      }
    }

    del_soi2a.rhwdeb = wdkd * tmp_sois.wdebrisc * rhmoist_wd * rhq10_wd;
  }
};

/** soil N budget */
void Soil_Bgc::deltan() {
  if (this->nfeed == 1) { // soil-plant N cycle switched on
    // Total N immobilization and net mineralization
    totnetnmin = 0.0;

    for(int i=0; i<cd->m_soil.numsl; i++) {
      double totc = tmp_sois.rawc[i] +
                    tmp_sois.soma[i] +
                    tmp_sois.sompr[i] +
                    tmp_sois.somcr[i];

      double rhsum = del_soi2a.rhrawc[i] +
                     del_soi2a.rhsoma[i] +
                     del_soi2a.rhsompr[i]+
                     del_soi2a.rhsomcr[i];

      double nimmob = getNimmob(ed->m_sois.liq[i], totc,
                                tmp_sois.orgn[i], tmp_sois.avln[i],
                                bd->m_soid.knmoist[i], bgcpar.kn2);

      del_soi2soi.nimmob[i] = nimmob;
      del_soi2soi.netnmin[i] = getNetmin(nimmob, totc, tmp_sois.orgn[i],
                                         rhsum ,bgcpar.nmincnsoil,
                                         decay, calpar.micbnup);

      totnetnmin += del_soi2soi.netnmin[i];
    }

    //m_soi2v.nuptake IS calculated in Vegetation_Bgc.cpp and
    //  integrated in 'Cohort.cpp'
    totnextract = 0.;

    for (int il=0; il<MAX_SOI_LAY; il++) {
      totnextract += bd->m_soi2v.nextract[il];
    }

    if (this->avlnflg == 1) { // open-N (inorganic) swithed on - note here ONLY 'lost' considered, while 'input' shall be from outside if any
      del_soi2l.avlnlost = 0.;  // N leaching out with drainage water

      if(totdzliq>0) {
        del_soi2l.avlnlost = totdzavln / totdzliq * bgcpar.fnloss
                             * ed->m_soi2l.qdrain;
      }

      if(ed->m_sois.liq[0]>0) { // N loss with surface runoff water
        del_soi2l.avlnlost += tmp_sois.avln[0] / ed->m_sois.liq[0]
                              * bgcpar.fnloss * ed->m_soi2l.qover;
      }

      if( del_soi2l.avlnlost > totdzavln - totnextract
          + totnetnmin + bd->m_a2soi.avlninput) {
        del_soi2l.avlnlost = totdzavln - totnextract
                             + totnetnmin + bd->m_a2soi.avlninput;
      }

      if (del_soi2l.avlnlost < 0) {
        del_soi2l.avlnlost = 0.0;
        double nminadj = del_soi2l.avlnlost +
                         totnextract - bd->m_a2soi.avlninput - totdzavln;

        for(int i=0; i<cd->m_soil.numsl; i++) {
          del_soi2soi.netnmin[i] *=nminadj/totnetnmin;
        }
      }
    } else { // End (this->avlnflg == 1)
      // N budget estimation of inorganic N loss
      del_soi2l.avlnlost = bd->m_a2soi.avlninput -
                           totnextract + totnetnmin;
    }

    if ( !this->baseline ) {
      del_soi2l.orgnlost = 0.0; // Dynamic Organic N lost - not yet done.
                                // this is the portal for future development.
    } else {
      // note: this will re-estimate the fire-emission re-deposition
      del_a2soi.orgninput = 0.;
      del_soi2l.orgnlost = 0.;
      double tsomcsum=bd->m_soid.rawcsum+bd->m_soid.somasum
                      +bd->m_soid.somprsum+bd->m_soid.somcrsum;
      double orgneven = tsomcsum/bgcpar.nmincnsoil;

      if ( orgneven >= bd->m_soid.orgnsum) {
        //This forces the C:N ratio in all the soil layers to be
        //equal to the C:N ratio in the parameter file.
        del_a2soi.orgninput += orgneven - bd->m_soid.orgnsum;
      } else {
        del_soi2l.orgnlost  += bd->m_soid.orgnsum - orgneven;
      }
    } // End baseline
  } // end if (nfeed)
};

void Soil_Bgc::deltastate() {
  /////////////// Carbon pools in soil ///////////////////////////////////
  // (I) soil respiration and C pool internal transformation
  //Yuan: the following is modified, assuming that -
  // 1) Jenkinson et al, 1977, soil science 123: 298 - 305
  //    when C is respired, 1 C will produce:
  //      0.076 microbial biomass C,
  //      0.125 physically-resistant C,
  //      0.0035 chemically-resistant C
  //    and the rest are released as CO2
  //In this code, those fractions can be as inputs
  // the ratio of SOM products per unit of CO2 respired
  double somtoco2 = (double)bgcpar.som2co2;
  // the fraction of SOMA in total SOM product
  double fsoma    = (double)bgcpar.fsoma;
  // the fraction of SOMPR in total SOM product
  double fsompr   = (double)bgcpar.fsompr;
  // the fraction of SOMCR in total SOM product
  double fsomcr   = (double)bgcpar.fsomcr;

  // 2) If soil respiration known, then internal C pool transformation
  //      can be estimated as following
  for(int il=0; il<cd->m_soil.numsl; il++) {
    double rhsum = del_soi2a.rhrawc[il] +
                   del_soi2a.rhsoma[il] +
                   del_soi2a.rhsompr[il] +
                   del_soi2a.rhsomcr[il];

                   // Only calculate these pools for non-moss layers...
                   if (cd->m_soil.type[il] > 0)
    {
      // So note that: root death is the reason for deep SOM increment
      // BM: Also note that, ch4_prod is only calculated if ch4 is enabled 
      del_sois.rawc[il] = ltrflc[il] - del_soi2a.rhrawc[il] * (1.0+somtoco2) - del_soi2soi.ch4_rawc[il];

      del_sois.soma[il] = (rhsum * somtoco2 * fsoma) -
                          del_soi2a.rhsoma[il] * (1.0+somtoco2) - del_soi2soi.ch4_soma[il];

      del_sois.sompr[il] = (rhsum * somtoco2 * fsompr) -
                           del_soi2a.rhsompr[il] * (1.0+somtoco2) - del_soi2soi.ch4_sompr[il];

      del_sois.somcr[il] = rhsum * somtoco2 * fsomcr -
                           del_soi2a.rhsomcr[il] * (1.0+somtoco2) - del_soi2soi.ch4_somcr[il];
    }
  }

  //ground surface wood debris decrement, if any
  del_sois.wdebrisc = d2wdebrisc- del_soi2a.rhwdeb;
  //(II) moving/mixing portion of C among layers
  //fibric-C (rawc) will NOT to move between layers
  double s2dfraction = 1.0;
  double mobiletoco2 = (double)bgcpar.fsoma*(double)bgcpar.som2co2;
  double xtopdlthick  = fmin(0.10, cd->m_soil.deepthick);  //Yuan: the max. thickness of deep-C layers, which shallow-C can move into
  double xtopmlthick  = 0.20;                              //Yuan: the max. thickness of mineral-C layers, which deep-C can move into
  double s2dcarbon1 = 0.0;  // read "soil to deep"?
  double s2dcarbon2 = 0.0;
  double s2dorgn    = 0.0;
  double d2mcarbon = 0.0;   // read "deep to mineral"?
  double d2morgn   = 0.0;
  double dlleft    = xtopdlthick;
  double mlleft    = xtopmlthick;
  double dcaddfrac = 0.0;
  double thickadded= 0.0;
  double del_orgn[MAX_SOI_LAY]= {0.0}; // soil org. N change with SOMC transformation and/or allocation

  for(int il=0; il<cd->m_soil.numsl; il++) {
    // 1) most of resistant-C increment into the fibric-horizon (generated
    //      above) will move down so that fibric horizon will be
    //      coarse-material dominated (active SOM will remain)
    if (cd->m_soil.type[il]<=1) {
      if (del_sois.sompr[il] > 0.) {
        s2dcarbon1 += del_sois.sompr[il]*s2dfraction;   //
        del_sois.sompr[il] *= (1.0-s2dfraction); // <<-- NOTE: may set delta sompr to zero?
      }

      if (del_sois.somcr[il] > 0.) {
        s2dcarbon2 += del_sois.somcr[il]*s2dfraction;   //
        del_sois.somcr[il] *= (1.0-s2dfraction);
      }

      if (this->nfeed == 1) {  // move orgn with SOMC as well
        double totsomc = tmp_sois.rawc[il] + tmp_sois.soma[il]
                         + tmp_sois.sompr[il] + tmp_sois.somcr[il];

        if (totsomc > (s2dcarbon1 + s2dcarbon2)) {
          del_orgn[il] = - (s2dcarbon1+s2dcarbon2) / totsomc
                          * tmp_sois.orgn[il]; //assuming C/N same for all
                                               //  SOM components
        } else {
          del_orgn[il] = 0.0;
        }

        s2dorgn += (-del_orgn[il]); //note: del_orgn[il] above is not positive
      }

      // In case there is no existing deep humific layer
      if (il<(cd->m_soil.numsl-1) && cd->m_soil.type[il+1]>2) {
        // NOTE:
        // Should this been 'cd->m_soil.type[il+1] > 1'??
        // Also, not sure how this is supposed to work, since we are w/in the
        // fibric layer check - not sure how this code will ever execute...

        del_sois.sompr[il] += s2dcarbon1; // Let the humified SOM C staying
                                          // in the last fibrous layer,
        del_sois.somcr[il] += s2dcarbon2; // Which later on, if greater than a
                                          // min. value, will form a new
                                          // humic layer

        if (this->nfeed == 1) {
          del_orgn[il] += s2dorgn;
        }
      }

    // end soil type 0 or 1
    } else if (cd->m_soil.type[il]==2 && dlleft>0) {
      // Humic layers...
      // 2) s2dcarbon from above will move into the 'xtopdlthick';
      thickadded = fmin(cd->m_soil.dz[il], dlleft);
      dcaddfrac = thickadded / xtopdlthick;
      dlleft -= thickadded;
      del_sois.sompr[il] += dcaddfrac * s2dcarbon1;
      del_sois.somcr[il] += dcaddfrac * s2dcarbon2;

      if (this->nfeed == 1) {
        del_orgn[il]+=s2dorgn;
      }

      // 3) meanwhile, the most mobilable portion of increment in
      //    deep-C layers will move down
      //    Here,
      //    (1) the mobilable portion is assumed to equal the SOMA
      //        production ONLY in value
      //    if any suggestion on this fraction (i.e., mobiletoco2) from
      //    field work, it should be modified;
      //
      //    (2) the mobilable portion is assumed to be related to
      //        decomposition activity, rather than directly to the
      //        substrate itself, because theorectically this mobile SOM C
      //        should be related to microbial activity
      double rhsum = del_soi2a.rhrawc[il] + del_soi2a.rhsoma[il]
                     + del_soi2a.rhsompr[il] + del_soi2a.rhsomcr[il];

      if (rhsum > 0.0) {
        double totmobile = rhsum*mobiletoco2;
        d2mcarbon += totmobile;
        del_sois.rawc[il]  -= del_soi2a.rhrawc[il]*mobiletoco2;
        del_sois.soma[il]  -= del_soi2a.rhsoma[il]*mobiletoco2;
        del_sois.sompr[il] -= del_soi2a.rhsompr[il]*mobiletoco2;
        del_sois.somcr[il] -= del_soi2a.rhsomcr[il]*mobiletoco2;

        if (this->nfeed == 1) {
          double totsomc = tmp_sois.rawc[il] + tmp_sois.soma[il]
                           + tmp_sois.sompr[il] + tmp_sois.somcr[il];

          if (totsomc > totmobile) {
            del_orgn [il] = - totmobile/totsomc*tmp_sois.orgn[il]; //assuming C/N same for all SOM components
          } else {
            del_orgn[il] = 0.0;
          }

          d2morgn += (-del_orgn[il]); //note: del_orgn[il] above is not positive
        }
      }

    // end soil type 2 and 'dlleft>0'
    } else if (cd->m_soil.type[il]==3) { // mineral layers...
      // 4) d2mcarbon from above will move into the 'xtopmlthick';
      thickadded = fmin(cd->m_soil.dz[il], mlleft);
      dcaddfrac = thickadded/xtopmlthick;
      mlleft -= thickadded;
      double tsom = tmp_sois.soma[il] + tmp_sois.sompr[il] + tmp_sois.somcr[il];

      if (tsom > 0.0) {
        del_sois.soma[il]+= dcaddfrac*d2mcarbon*(tmp_sois.soma[il]/tsom);
        del_sois.sompr[il]+= dcaddfrac*d2mcarbon*(tmp_sois.sompr[il]/tsom);
        del_sois.somcr[il]+= dcaddfrac*d2mcarbon*(tmp_sois.somcr[il]/tsom);
      } else {
        del_sois.soma[il]+= dcaddfrac*d2mcarbon*fsoma;
        del_sois.sompr[il]+= dcaddfrac*d2mcarbon*fsompr;
        del_sois.somcr[il]+= dcaddfrac*d2mcarbon*fsomcr;
      }

      if (this->nfeed == 1) {
        del_orgn[il] = d2morgn * dcaddfrac;
      }

      if (mlleft<=0.0) {
        break;
      }
    } // end soil type 3
  }

  /////////////// Nitrogen pools in soil ///////////////////////////////////
  if (this->nfeed == 1) {
    for(int il = 0; il<cd->m_soil.numsl; il++) {
      // organic N pools
      //del_orgn[il] is from above SOM C mixing and moving
      del_sois.orgn[il] = ltrfln[il] - del_soi2soi.netnmin[il] + del_orgn[il];

      if (il==0) { //put the deposited orgn (here, mainly fire emitted
                   //  or budget estimation) into the first soil layer
        del_sois.orgn[il] += bd->m_a2soi.orgninput;
      }

//      double dondrain = 0.0; // dissolved organic N drainage??
//
//      if (totdzliq > 0.01) {
//        if((cd->m_soil.z[il]+cd->m_soil.dz[il]) <= ed->m_sois.draindepth) { //note: z is at the top of a layer
//          dondrain = del_soi2l.orgnlost
//                     * (ed->m_sois.liq[il]/totdzliq);
//        } else {
//          if (cd->m_soil.z[il]<ed->m_sois.draindepth) { // note: z is at the top of a layer
//            double fdz = (ed->m_sois.draindepth - cd->m_soil.z[il]) / cd->m_soil.dz[il];
//            dondrain = del_soi2l.orgnlost * (ed->m_sois.liq[il]/totdzliq) * fdz;
//          }
//        }
//      }
//
//      del_sois.orgn[il] -= dondrain; // <==== When orgn ends up negative, the
//                                     // Integrator has a hard time converging!
//
//      // If del_sosi.orgn is a "pool" variable and not a "change in pool"
//      // variable, then it might be appropriate to force the values to zero:
//      // with something like this:
//      //if (del_sois.orgn[il] < 0) { del_sois.orgn[il] = 0.0; }

      // Inorganic N pools
      double ninput = 0.;

      if (il == 0) {
        ninput = bd->m_a2soi.avlninput;
      }

      //Note: the internal N transport not estimated, but assuming that all
      //        N leaching loss are from all above-drainage zone upon liq
      //         water fraction
      //  This is not good for daily N process, but shall be reasonble
      //    for longer intervals, e.g. monthly
      double ndrain = 0.;

      if (totdzliq>0.01) {
        if((cd->m_soil.z[il]+cd->m_soil.dz[il]) <= ed->m_sois.draindepth) { //note: z is at the top of a layer
          ndrain = del_soi2l.avlnlost
                   *(ed->m_sois.liq[il]/totdzliq*ed->m_soi2l.qdrain);
        } else {
          if (cd->m_soil.z[il]<ed->m_sois.draindepth) { // note: z is at the top of a layer
            double fdz = (ed->m_sois.draindepth - cd->m_soil.z[il])
                         /cd->m_soil.dz[il];
            ndrain = del_soi2l.avlnlost
                     *(ed->m_sois.liq[il]/totdzliq*ed->m_soi2l.qdrain)*fdz;
          }
        }
      }

      if(bd->m_v2soi.rtlfalfrac[il] > 0.) {
        del_sois.avln[il] = ninput + del_soi2soi.netnmin[il]
                            - ndrain - rtnextract[il];
      } else {
        del_sois.avln[il] = 0;
        del_soi2soi.netnmin[il] = 0.0;
      }
    } // end of soil layer loop

    // wood debris
    if (tmp_sois.wdebrisc > 0.) {
      del_sois.wdebrisn = d2wdebrisn;
      del_sois.wdebrisn -=del_soi2a.rhwdeb*tmp_sois.wdebrisn/tmp_sois.wdebrisc;
    }
  } // end of 'if (this->nfeed == 1)'
};

double Soil_Bgc::getRhmoist(const double &vsm, const double &moistmin,
                            const double &moistmax, const double &moistopt) {
  double rhmoist;
  //set moistlim always 1
  rhmoist = (vsm - moistmin) * (vsm - moistmax);
  rhmoist /= rhmoist - (vsm-moistopt)*(vsm-moistopt);

  if ( rhmoist < 0.0 ) {
    rhmoist = 0.0;
  }

  return rhmoist;
};

double Soil_Bgc::getRhq10(const  double & tsoil) {
  double rhq10;
  rhq10 =  pow( (double)bgcpar.rhq10, tsoil/10.0);
  return rhq10;
};

double Soil_Bgc::getNimmob(const double & soilh2o, const double & soilorgc,
                           const double & soilorgn, const double & availn,
                           const double & ksoil, const double kn2) {
  double nimmob     = 0.0;
  double tempnimmob = 0.0;
  double tempkn2    = kn2;

  //what if put && availn>0 here
  if(soilorgc>0.0 && soilorgn>0.0 && soilh2o>0 && availn>0) {
    nimmob = (availn * ksoil) / soilh2o;
    tempnimmob = nimmob;
    nimmob /= (tempkn2 + nimmob);
  }

  return nimmob;
};

double Soil_Bgc::getNetmin(const double & nimmob, const double & soilorgc,
                           const double & soilorgn, const double & rh,
                           const double & tcnsoil,
                           const double & decay, const double & nup ) {
  double nmin = 0.0;

  if ( soilorgc > 0.0 && soilorgn > 0.0 ) {
    nmin   = ((soilorgn / soilorgc) - (nup * nimmob * decay)) * rh;

    if ( nmin >= 0.0 ) {
      nmin *= (soilorgn/soilorgc) * tcnsoil;
    } else {
      nmin *= (soilorgc/soilorgn) / tcnsoil;
    }
  }

  return nmin;
};

void Soil_Bgc::updateKdyrly4all() {
  double kdrawc  = calpar.kdcrawc;
  double kdsoma  = calpar.kdcsoma;
  double kdsompr = calpar.kdcsompr;
  double kdsomcr = calpar.kdcsomcr;

  for(int il=0; il<cd->m_soil.numsl; il++) {
    //adjust SOM component respiration rate (kdc) due to 
    //  litterfall C/N ratio changing
    if (this->nfeed == 1) {
      double ltrfalcn = 0.;
      deque <double> ltrfcnque = bd->prvltrfcnque[il];
      int numrec = ltrfcnque.size();

      for (int i=0; i<numrec; i++) {
        ltrfalcn += ltrfcnque[i]/numrec;
      }

      if (ltrfalcn > 0.0) {
        kdrawc  = getKdyrly(ltrfalcn, bgcpar.lcclnc, calpar.kdcrawc);
        kdsoma  = getKdyrly(ltrfalcn, bgcpar.lcclnc, calpar.kdcsoma);
        kdsompr = getKdyrly(ltrfalcn, bgcpar.lcclnc, calpar.kdcsompr);
        kdsomcr = getKdyrly(ltrfalcn, bgcpar.lcclnc, calpar.kdcsomcr);
      } else {
        kdrawc  = calpar.kdcrawc;
        kdsoma  = calpar.kdcsoma;
        kdsompr = calpar.kdcsompr;
        kdsomcr = calpar.kdcsomcr;
      }
    }

    bgcpar.kdrawc[il]  = kdrawc;
    bgcpar.kdsoma[il]  = kdsoma;
    bgcpar.kdsompr[il] = kdsompr;
    bgcpar.kdsomcr[il] = kdsomcr;

    if (cd->m_soil.type[il] == 0) { //moss
      bgcpar.kdrawc_ch4[il] = 0.0;
      bgcpar.kdsoma_ch4[il] = 0.0;
      bgcpar.kdsompr_ch4[il] = 0.0;
      bgcpar.kdsomcr_ch4[il] = 0.0;
    }
    else{
      bgcpar.kdrawc_ch4[il] = calpar.kdcrawc_ch4;
      bgcpar.kdsoma_ch4[il] = calpar.kdcsoma_ch4;
      bgcpar.kdsompr_ch4[il] = calpar.kdcsompr_ch4;
      bgcpar.kdsomcr_ch4[il] = calpar.kdcsomcr_ch4;
    }

  }
};

double Soil_Bgc::getKdyrly(double & yrltrcn, const double lcclnc,
                           const double & kdc) {
  double kd = kdc;
  kd = kdc * pow( (yrltrcn),-0.784 ) / pow( lcclnc,-0.784 );
  return kd;
};

double Soil_Bgc::getKnsoilmoist(const double & vsm) {
  double ksoil = 0.;

  if (vsm > 0.) {
    ksoil = pow(vsm, 3.0);
  }

  return ksoil;
};

void Soil_Bgc::setGround(Ground* groundp) {
  ground = groundp;
};

void Soil_Bgc::setCohortLookup(CohortLookup* chtlup) {
  chtlu = chtlup;
};

void Soil_Bgc::setCohortData(CohortData* cdp) {
  cd = cdp;
};

void Soil_Bgc::setEnvData(EnvData* edp) {
  ed = edp;
};

void Soil_Bgc::setBgcData(BgcData* bdp) {
  bd = bdp;
};

void Soil_Bgc::setFirData(FirData* fdp) {
  fd = fdp;
};

void Soil_Bgc::set_nfeed(int value) {
  BOOST_LOG_SEV(glg, info) << "Setting Soil_Bgc.nfeed to " << value;
  this->nfeed = value;
}

int Soil_Bgc::get_nfeed() {
  return this->nfeed;
}

void Soil_Bgc::set_avlnflg(int value) {
  BOOST_LOG_SEV(glg, info) << "Setting Soil_Bgc.avlnflg to " << value;
  this->avlnflg = value;
}

int Soil_Bgc::get_avlnflg() {
  return this->avlnflg;
}

void Soil_Bgc::set_baseline(int value) {
  BOOST_LOG_SEV(glg, info) << "Setting Soil_Bgc.baseline to " << value;
  this->baseline = value;
}

int Soil_Bgc::get_baseline() {
  return this->baseline;
}