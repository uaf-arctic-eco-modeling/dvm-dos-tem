#include <iomanip>

#include <sstream>
#include <string>

#include <fstream>
#include <vector> 
#include <list>

#include "../include/TEMLogger.h"

#include "../include/TEMUtilityFunctions.h"

#include "../include/CohortLookup.h"

extern src::severity_logger< severity_level > glg;

CohortLookup::CohortLookup() {
  cmtcode = "CMT00"; // the default community code (5 alphnumerics)
};

/** New constructor...*/
CohortLookup::CohortLookup(std::string directory, std::string code) :
    dir(directory), cmtcode(code)  {

  BOOST_LOG_SEV(glg, info) << "Building a CohortLookup: set directory, "
                           << "community type, then read " << dir << "/* files "
                           << "and set data members.";
  assignBgcCalpar(this->dir);
  assignVegDimension(this->dir);
  assignGroundDimension(this->dir);
  assignEnv4Canopy(this->dir);
  assignBgc4Vegetation(this->dir);
  assignEnv4Ground(this->dir);
  assignBgc4Ground(this->dir);
  assignFirePar(this->dir);

};

CohortLookup::~CohortLookup(){}

void CohortLookup::init() {
  BOOST_LOG_SEV(glg, info) << "Cohort Lookup init function. Assigning all values from various config/* files...";
  assignBgcCalpar(dir);
  assignVegDimension(dir);
  assignGroundDimension(dir);
  assignEnv4Canopy(dir);
  assignBgc4Vegetation(dir);
  assignEnv4Ground(dir);
  assignBgc4Ground(dir);
  assignFirePar(dir);
}

/** Prints data from this-> fields mimics format of cmt_calparbgc.txt file,
 * but only for one cmt type which ever one "this->cmtcode" refers to..
 */
std::string CohortLookup::calparbgc2str() {
  std::stringstream s("");
  s << "CMT code: " << this->cmtcode << "\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    std::stringstream p;//("PFT");
    p << "PFT" << i;
    s << std::setw(12) << std::setfill(' ') << p.str();
  }

  s << "\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->cmax[i];
  }

  s << "    cmax\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->nmax[i];
  }

  s << "    nmax\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->cfall[0][i];
  }

  s << "    cfall[0] leaf\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->cfall[1][i];
  }

  s << "    cfall[1] stem\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->cfall[2][i];
  }

  s << "    cfall[2] root\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->nfall[0][i];
  }

  s << "    nfall[0] leaf\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->nfall[1][i];
  }

  s << "    nfall[1] stem\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->nfall[2][i];
  }

  s << "    nfall[2] root\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->kra[i];
  }

  s << "    kra (coeff in maintenance resp.)\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->krb[0][i];
  }

  s << "    krb[0] (coeff in maintenance resp., leaf)\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->krb[1][i];
  }

  s << "    krb[1] (coeff in maintenance resp., stem)\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->krb[2][i];
  }

  s << "    krb[2] (coeff in maintenance resp., root)\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->frg[i];
  }

  s << "    kra[2] (fraction of available NPP (GPP after rm))\n";
  s << "// soil calibrated parameters\n";
  s << this->micbnup << " // micbnup: parameter for soil microbial immobialization of N\n";
  s << this->kdcrawc << " // kdcrawc: raw-material (litter) C decompositin rates at reference condition\n";
  s << this->kdcsoma << " // kdcsoma:\n";
  s << this->kdcsompr << " // kdcsompr:\n";
  s << this->kdcsomcr << "// kdcsomcr:\n";
  return s.str();
}


/** Set calibrated BCG parameters based on values in file. */
void CohortLookup::assignBgcCalpar(std::string & dircmt) {

  // get a list of data for the cmt number
  std::list<std::string> l = temutil::parse_parameter_file(
      dircmt + "cmt_calparbgc.txt", temutil::cmtcode2num(this->cmtcode), 18
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  temutil::pfll2data_pft(l, cmax);
  temutil::pfll2data_pft(l, nmax);
  temutil::pfll2data_pft(l, cfall[I_leaf]);
  temutil::pfll2data_pft(l, cfall[I_stem]);
  temutil::pfll2data_pft(l, cfall[I_root]);
  temutil::pfll2data_pft(l, nfall[I_leaf]);
  temutil::pfll2data_pft(l, nfall[I_stem]);
  temutil::pfll2data_pft(l, nfall[I_root]);
  temutil::pfll2data_pft(l, kra);
  temutil::pfll2data_pft(l, krb[I_leaf]);
  temutil::pfll2data_pft(l, krb[I_stem]);
  temutil::pfll2data_pft(l, krb[I_root]);
  temutil::pfll2data_pft(l, frg);

  temutil::pfll2data(l, micbnup);
  temutil::pfll2data(l, kdcrawc);
  temutil::pfll2data(l, kdcsoma);
  temutil::pfll2data(l, kdcsompr);
  temutil::pfll2data(l, kdcsomcr);

}

/** Assign "veg dimension?" from parameter file. */
void CohortLookup::assignVegDimension(string &dircmt) {

  // get a list of data for the cmt number
  std::list<std::string> l = temutil::parse_parameter_file(
      dircmt + "cmt_dimvegetation.txt", temutil::cmtcode2num(this->cmtcode), 40
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  temutil::pfll2data_pft(l, vegcov);
  temutil::pfll2data_pft(l, ifwoody);
  temutil::pfll2data_pft(l, ifdeciwoody);
  temutil::pfll2data_pft(l, ifperenial);
  temutil::pfll2data_pft(l, nonvascular);
  temutil::pfll2data_pft(l, sla);
  temutil::pfll2data_pft(l, klai);
  temutil::pfll2data_pft(l, minleaf);
  temutil::pfll2data_pft(l, aleaf);
  temutil::pfll2data_pft(l, bleaf);
  temutil::pfll2data_pft(l, cleaf);
  temutil::pfll2data_pft(l, kfoliage);
  temutil::pfll2data_pft(l, cov);
  temutil::pfll2data_pft(l, m1);
  temutil::pfll2data_pft(l, m2);
  temutil::pfll2data_pft(l, m3);
  temutil::pfll2data_pft(l, m4);

  for (int i = 0; i < MAX_ROT_LAY; i++) {
    temutil::pfll2data_pft(l, frootfrac[i]);
  }

  temutil::pfll2data_pft(l, initial_lai);

  for (int im = 0; im < MINY; im++) {
    temutil::pfll2data_pft( l, static_lai[im]);
  }

}

/** Assigns "ground dimension?" parameters from file */
void CohortLookup::assignGroundDimension(string &dircmt) {

  // get a list of data for the cmt number
  std::list<std::string> l = temutil::parse_parameter_file(
      dircmt + "cmt_dimground.txt", temutil::cmtcode2num(this->cmtcode), 15
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  temutil::pfll2data(l, snwdenmax);
  temutil::pfll2data(l, snwdennew);
  temutil::pfll2data(l, initsnwthick);
  temutil::pfll2data(l, initsnwdense);

  temutil::pfll2data(l, maxdmossthick);
  temutil::pfll2data(l, initdmossthick);
  temutil::pfll2data(l, mosstype);

  temutil::pfll2data(l, initfibthick);
  temutil::pfll2data(l, inithumthick);
  temutil::pfll2data(l, coefshlwa);
  temutil::pfll2data(l, coefshlwb);
  temutil::pfll2data(l, coefdeepa);
  temutil::pfll2data(l, coefdeepb);
  temutil::pfll2data(l, coefminea);
  temutil::pfll2data(l, coefmineb);

  // ?????????? NOT sure what this was doing before.
  //
  // Currently there are not parameters for mineral texture in the
  // config/cmt_dimground.txt file. I think with the previous method of parsing/
  // reading the file, it would silently fail.
  //
  // But with the new mechanism of parsing, if there is no more data in the line
  // list, then you get an error trying to create a string in pfll2data()
  // fucntion. So I have commented it out for now...
  //
  //for (int ily=0; ily<MAX_MIN_LAY; ily++) {
  //  pfll2data(l, minetexture[ily]);
  //}

}

/** Assigns "environmental canony?" data from config file */
void CohortLookup::assignEnv4Canopy(string &dir) {

  // get a list of data for the cmt number
  std::list<std::string> l = temutil::parse_parameter_file(
      dir + "cmt_envcanopy.txt", temutil::cmtcode2num(this->cmtcode), 12
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  temutil::pfll2data_pft(l, albvisnir);
  temutil::pfll2data_pft(l, er);
  temutil::pfll2data_pft(l, ircoef);
  temutil::pfll2data_pft(l, iscoef);
  temutil::pfll2data_pft(l, glmax);
  temutil::pfll2data_pft(l, gl_bl);
  temutil::pfll2data_pft(l, gl_c);
  temutil::pfll2data_pft(l, vpd_open);
  temutil::pfll2data_pft(l, vpd_close);
  temutil::pfll2data_pft(l, ppfd50);
  temutil::pfll2data_pft(l, initvegwater);
  temutil::pfll2data_pft(l, initvegsnow);
  
}

/** Assigns vegetation C/N parameters from config file
*/
void CohortLookup::assignBgc4Vegetation(string & dircmt) {
  
  // get a list of data for the cmt number
  std::list<std::string> l = temutil::parse_parameter_file(
      dircmt + "cmt_bgcvegetation.txt", temutil::cmtcode2num(this->cmtcode), 33
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  temutil::pfll2data_pft(l, kc);
  temutil::pfll2data_pft(l, ki);
  temutil::pfll2data_pft(l, tmin);
  temutil::pfll2data_pft(l, toptmin);
  temutil::pfll2data_pft(l, toptmax);
  temutil::pfll2data_pft(l, tmax);
  temutil::pfll2data_pft(l, raq10a0);
  temutil::pfll2data_pft(l, raq10a1);
  temutil::pfll2data_pft(l, raq10a2);
  temutil::pfll2data_pft(l, raq10a3);
  temutil::pfll2data_pft(l, knuptake);
  temutil::pfll2data_pft(l, cpart[I_leaf]);
  temutil::pfll2data_pft(l, cpart[I_stem]);
  temutil::pfll2data_pft(l, cpart[I_root]);
  temutil::pfll2data_pft(l, initc2neven[I_leaf]);
  temutil::pfll2data_pft(l, initc2neven[I_stem]);
  temutil::pfll2data_pft(l, initc2neven[I_root]);
  temutil::pfll2data_pft(l, c2nb[I_leaf]);
  temutil::pfll2data_pft(l, c2nb[I_stem]);
  temutil::pfll2data_pft(l, c2nb[I_root]);
  temutil::pfll2data_pft(l, c2nmin[I_leaf]);
  temutil::pfll2data_pft(l, c2nmin[I_stem]);
  temutil::pfll2data_pft(l, c2nmin[I_root]);
  temutil::pfll2data_pft(l, c2na);
  temutil::pfll2data_pft(l, labncon);
  temutil::pfll2data_pft(l, initvegc[I_leaf]);
  temutil::pfll2data_pft(l, initvegc[I_stem]);
  temutil::pfll2data_pft(l, initvegc[I_root]);
  temutil::pfll2data_pft(l, initvegn[I_leaf]);
  temutil::pfll2data_pft(l, initvegn[I_stem]);
  temutil::pfll2data_pft(l, initvegn[I_root]);
  temutil::pfll2data_pft(l, initdeadc);
  temutil::pfll2data_pft(l, initdeadn);


  // Makes sure that the 'cpart' compartment variables match the proportions
  // set in initvegc variables in a cmt_bgcvegetation.txt file.

  // The initvegc(leaf, wood, root) variables in cmt_bgcvegetation.txt are the
  // measured values from literature. The cpart(leaf, wood, root) variables,
  // which are in the same file, should be set to the fractional make up of
  // the components. So if the initvegc values for l, w, r are 100, 200, 300,
  // then the cpart values should be 0.166, 0.33, and 0.5. It is very easy for
  // these values to get out of sync when users manually update the parameter
  // file.

  std::stringstream ss;
  ss << fixed;

  // Build the header
  ss << "Table of cpart and initvegc values and discrepancies." << endl
     << right << setw(5) << setprecision(1) << setfill(' ') << "PFT"
     << right << setw(12) << setprecision(1) << setfill(' ') << "COMPARTMENT"
     << right << setw(12) << setprecision(6) << setfill(' ') << "cpart"
     << right << setw(12) << setprecision(6) << setfill(' ') << "initvegC"
     << right << setw(12) << setprecision(6) << setfill(' ') << "cpart*sumC"
     << right << setw(12) << setprecision(6) << setfill(' ') << "diff"
     << right << setw(12) << setprecision(6) << setfill(' ') << "%error"
     << endl;


  bool OK = true; // Sentinel value enabling us to quit if any checks fail

  for (int ipft=0; ipft < NUM_PFT; ipft++) {

    // First, check that cpart for all the compartments adds to 1 (or zero)
    double cpart_sum = cpart[I_leaf][ipft] + cpart[I_stem][ipft] + cpart[I_root][ipft];
    if (! (temutil::AlmostEqualRelative(cpart_sum, 1.0) ||
           temutil::AlmostEqualRelative(cpart_sum, 0.0)) ) {
      BOOST_LOG_SEV(glg, fatal) << "cpart for PFT " << ipft << " does not add up to 1 (or zero)!";
      OK = false;
    }

    // Next check that the cpart values are comensurate with the values that
    // are set for initvegc.
    double sumC = initvegc[I_leaf][ipft] + initvegc[I_stem][ipft] + initvegc[I_root][ipft];
    for (int jpart=I_leaf; jpart < NUM_PFT_PART; jpart++) {

      double diff = abs((cpart[jpart][ipft] * sumC) - initvegc[jpart][ipft]);
      double percent_error = 100.0 * abs((cpart[jpart][ipft] * sumC) - initvegc[jpart][ipft]) / sumC;
      if (percent_error > 0.1) {
        OK = false;
        BOOST_LOG_SEV(glg, fatal) << "Problem with initvegc and cpart parameters for PFT: " << ipft << "!";
      }

      // Put together the data for the table
      ss << right << setw(5) << setprecision(1) << setfill(' ') << ipft
         << right << setw(12) << setprecision(1) << setfill(' ') << jpart
         << right << setw(12) << setprecision(6) << setfill(' ') << cpart[jpart][ipft]
         << right << setw(12) << setprecision(6) << setfill(' ') << initvegc[jpart][ipft]
         << right << setw(12) << setprecision(6) << setfill(' ') << cpart[jpart][ipft] * sumC
         << right << setw(12) << setprecision(6) << setfill(' ') << diff
         << right << setw(12) << setprecision(6) << setfill(' ') << percent_error
         << endl;
    }
  }
  BOOST_LOG_SEV(glg, debug) << ss.str();

  if (!OK) {
    BOOST_LOG_SEV(glg, fatal) << "Problem with cmt_bgcvegetation.txt!!";
    throw std::runtime_error("Problem with initial parameter files!");

  }

}

/** Assign environemntal parameters for the ground based on config file */
void CohortLookup::assignEnv4Ground(string &dircmt) {

  // get a list of data for the cmt number
  std::list<std::string> datalist = temutil::parse_parameter_file(
      dircmt + "cmt_envground.txt", temutil::cmtcode2num(this->cmtcode), 41
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  temutil::pfll2data(datalist, snwalbmax);
  temutil::pfll2data(datalist, snwalbmin);
  temutil::pfll2data(datalist, psimax);
  temutil::pfll2data(datalist, evapmin);
  temutil::pfll2data(datalist, drainmax);
  temutil::pfll2data(datalist, rtdp4gdd);
  temutil::pfll2data(datalist, tcsolid_moss);
  temutil::pfll2data(datalist, tcsolid_f);
  temutil::pfll2data(datalist, tcsolid_h);
  temutil::pfll2data(datalist, poro_moss);
  temutil::pfll2data(datalist, poro_f);
  temutil::pfll2data(datalist, poro_h);
  temutil::pfll2data(datalist, bulkden_moss);
  temutil::pfll2data(datalist, bulkden_f);
  temutil::pfll2data(datalist, bulkden_h);
  temutil::pfll2data(datalist, hksat_moss);
  temutil::pfll2data(datalist, hksat_f);
  temutil::pfll2data(datalist, hksat_h);
  temutil::pfll2data(datalist, nfactor_s);
  temutil::pfll2data(datalist, nfactor_w);
  temutil::pfll2data(datalist, initsnwtem);

  for (int i = 0; i < 10; i++) {
    temutil::pfll2data(datalist, initts[i]);
  }

  for (int i = 0; i < 10; i++) {
    temutil::pfll2data(datalist, initvwc[i]);
  }

}

/** Assign ground related bgc parameters from file...*/
void CohortLookup::assignBgc4Ground(string &dircmt) {
  
  // get a list of data for the cmt number
  std::list<std::string> datalist = temutil::parse_parameter_file(
      dircmt + "cmt_bgcsoil.txt", temutil::cmtcode2num(this->cmtcode), 19
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  temutil::pfll2data(datalist, rhq10);
  temutil::pfll2data(datalist, rhmoistfrozen);
  temutil::pfll2data(datalist, moistmin);
  temutil::pfll2data(datalist, moistopt);
  temutil::pfll2data(datalist, moistmax);
  temutil::pfll2data(datalist, lcclnc);
  temutil::pfll2data(datalist, fsoma);
  temutil::pfll2data(datalist, fsompr);
  temutil::pfll2data(datalist, fsomcr);
  temutil::pfll2data(datalist, som2co2);
  temutil::pfll2data(datalist, kn2);
  temutil::pfll2data(datalist, nmincnsoil);
  temutil::pfll2data(datalist, propftos);
  temutil::pfll2data(datalist, fnloss);
  temutil::pfll2data(datalist, initshlwc);
  temutil::pfll2data(datalist, initdeepc);
  temutil::pfll2data(datalist, initminec);
  temutil::pfll2data(datalist, initsoln);
  temutil::pfll2data(datalist, initavln);

}

/** Assign the fire parameters from a file */
void CohortLookup::assignFirePar(string &dircmt) {

  // get a list of data for the cmt number
  std::list<std::string> datalist = temutil::parse_parameter_file(
      dircmt + "cmt_firepar.txt", temutil::cmtcode2num(this->cmtcode), 18
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  for(int i = 0; i < NUM_FSEVR; i++) {
    temutil::pfll2data_pft( datalist, fvcombust[i]);
  }

  for(int i=0; i<NUM_FSEVR; i++) {
    temutil::pfll2data_pft( datalist, fvslash[i]);
  }

  for(int i = 0; i < NUM_FSEVR; i++) {
    temutil::pfll2data( datalist, foslburn[i]);
  }

  temutil::pfll2data(datalist, vsmburn);
  temutil::pfll2data(datalist, r_retain_c);
  temutil::pfll2data(datalist, r_retain_n);
};
