#include <iomanip>

#include <sstream>
#include <string>

#include <fstream>
#include <vector> 
#include <list>

#include "../TEMLogger.h"

#include "CohortLookup.h"

extern src::severity_logger< severity_level > glg;

/** Parses a string, looking for a community code.
 Reads the string, finds the first occurrence of the characters "CMT", and
 returns a string consisting of CMT and the following two characters.

 Returns something like "CMT01".
*/
string read_cmt_code(string s) {
  int pos = s.find("CMT");
  return s.substr(pos, 5);
}

/** Parses a string, looking for a community code, returns an integer.
*/
int cmtcode2num(std::string s) {
  int pos = s.find("CMT");
  
  return std::atoi( s.substr(pos+3, 2).c_str() );
}

/** Takes an integer number and returns a string like "CMT01".
* Inserts leading zeros if needed. Works if 0 <= cmtnumber <= 99.
*/
std::string cmtnum2str(int cmtnumber) {

  // get string representation of number
  std::stringstream cmtnumber_ss;
  cmtnumber_ss << cmtnumber;

  // take care of leading zero...
  std::string prefix = "";
  if (cmtnumber < 10) {
    prefix =  "CMT0";
  } else {
    prefix = "CMT";
  }

  return prefix + cmtnumber_ss.str();
}


/** Reads a file, returning a contiguous section of lines surrounded by "CMT".
* Each line from the file is an element in the vector. 
*/  
std::vector<std::string> get_cmt_data_block(std::string filename, int cmtnum) {

  BOOST_LOG_SEV(glg, note) << "Opening file: " << filename;
  std::ifstream par_file(filename.c_str(), std::ifstream::in);

  if ( !par_file.is_open() ) {
    BOOST_LOG_SEV(glg, fatal) << "Problem opening " << filename << "!";
    exit(-1);
  }

  std::string cmtstr = cmtnum2str(cmtnum);

  // create a place to store lines making up the community data "block"
  std::vector<std::string> cmt_block_vector; 
  BOOST_LOG_SEV(glg, note) << "Searching file for community: " << cmtstr;
  for (std::string line; std::getline(par_file, line); ) {
  	int pos = line.find(cmtstr);
  	if ( pos != std::string::npos ) {

  	  // add the 'header line' to the data block
  	  cmt_block_vector.push_back(line);			

	  for (std::string block_line; std::getline(par_file, block_line); ) {

	    int block_line_pos = block_line.find("CMT");
	    if ( block_line_pos != std::string::npos ) {
	      //std::cout << "Whoops - line contains 'CMT'. Must be first line of next community data block; breaking loop.\n";
	      break;
	    } else {
	      //std::cout << "Add line to cmt_block_vector: " << block_line << std::endl;
	      cmt_block_vector.push_back(block_line);
	    }
	  }

  	}
  }
  return cmt_block_vector;
}

/** Takes a cmt data "block" and strips any comments. */
std::list<std::string> strip_comments(std::vector<std::string> idb) {
  std::list<std::string> l;

  for (std::vector<std::string>::iterator it = idb.begin(); it != idb.end(); ++it ) {

    std::string line = *it;

    // // strip comment and everthing after
    // size_t pos = line.find("//");
    // line = line.substr(0, pos);

    // Split into data and comment (everything after '//')
    size_t pos = line.find("//");
    std::string data = line.substr(0, pos);
    std::string comment = "";
    if (pos != std::string::npos) {
      comment = line.substr(pos+2, std::string::npos);
    }
    //std::cout << "Data: " << data << " Comment: " << comment << std::endl;

    if (data.size() == 0) {
      // pass
    } else {
      l.push_back(line);
    }

  }

  return l;
}


/* NOTES:
 - not sure these need to be templates? to work with doubles, ints, or floats?
   right now I think all data is doubles.

 - seems like there should be a way to detect if it is a pft variable or not
   and thereby combine these two functions?
   read from string to tokenize into vectort, then if vector.size > 1, assume
   it is a pft - try and read data into appropriate spot?
   
 - need to some kind of check/safety to not overwrite the end of data??
 
 - Might eventually be useful to re-factor this again (so that the various
   codes for handling communities's parameter data can be compiled into a 
   stand-along command line utility..?
*/


/** Pop the front of a "line-list" and store at the location of "data".
 * For setting internal data from dvmdostem parameter files.
*/
template<typename T>
void pfll2data(std::list<std::string> &l, T &data) {

  std::stringstream s(l.front());

  if ( !(s >> data) ) {
    BOOST_LOG_SEV(glg, err) << "ERROR! Problem converting parameter in this line to numeric value: " << l.front();
    data = -999999.0;
  }

  l.pop_front();
}

/** Pop the front of line-list and store at data. For multi pft 
 *  (multi-column) parameters 
 * For setting internal data from dvmdostem parameter files.
 *
*/
template<typename T>
void pfll2data_pft(std::list<std::string> &l, T *data) {

  std::stringstream s(l.front());
 
  for(int i = 0; i < NUM_PFT; i++) {

    if ( !(s >> data[i]) ) {
      BOOST_LOG_SEV(glg, err) << "ERROR! Problem converting parameter in column "<<i<<"of this line to numeric value: " << l.front();
      data[i] = -99999.0;
    }
  }
 
  l.pop_front();

}

/** Given a file name, a community number and a number for expected lines of 
 * data, returns a list of strings with just that data, after stripping 
 * comments.
 */
std::list<std::string> parse_parameter_file(
    const std::string& fname, int cmtnumber, int linesofdata) {
  
  BOOST_LOG_SEV(glg, note) << "Parsing '"<< fname << "', "
                           << "for community number: " << cmtnumber;

  // get a vector of strings for that cmt "block". includes comments.
  std::vector<std::string> v(get_cmt_data_block(fname, cmtnumber));
  
  // strip the comments and turn it into a list
  std::list<std::string> datalist(strip_comments(v));

  // check the size
  if (datalist.size() != linesofdata) {
    BOOST_LOG_SEV(glg, err) << "Expected " << linesofdata << ". "
                            << "Only found " << datalist.size() << ". "
                            << "(" << fname << ", community " << cmtnumber << ")";
    exit(-1);
  }

  return datalist;
}


CohortLookup::CohortLookup() {
  cmtcode = "CMT00"; // the default community code (5 alphnumerics)
};

CohortLookup::~CohortLookup() {
};

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

  s << "    krb[1] (coeff in maintenance resp., leaf)\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->krb[2][i];
  }

  s << "    krb[2] (coeff in maintenance resp., leaf)\n";

  for (int i = 0 ; i < NUM_PFT; ++i) {
    s << std::setw(12) << std::setfill(' ') << this->frg[i];
  }

  s << "    kra[2] (fraction of available NPP (GPP after rm))\n";
  s << "// soil calibrated parameters\n";
  s << this->micbnup << " // micbnup: parameter for soil microbial immobialization of N\n";
  s << this->kdcmoss << " // kdcmoss: dead moss C decompositin rates at reference condition\n";
  s << this->kdcrawc << " // kdcrawc: raw-material (litter) C decompositin rates at reference condition\n";
  s << this->kdcsoma << " // kdcsoma:\n";
  s << this->kdcsompr << " // kdcsompr:\n";
  s << this->kdcsomcr << "// kdcsomcr:\n";
  return s.str();
}


/** Set calibrated BCG parameters based on values in file. */
void CohortLookup::assignBgcCalpar(string & dircmt) {

  // get a list of data for the cmt number
  std::list<std::string> l = parse_parameter_file(
      dircmt + "cmt_calparbgc.txt", cmtcode2num(this->cmtcode), 19
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  pfll2data_pft(l, cmax);
  pfll2data_pft(l, nmax);
  pfll2data_pft(l, cfall[I_leaf]);
  pfll2data_pft(l, cfall[I_stem]);
  pfll2data_pft(l, cfall[I_root]);
  pfll2data_pft(l, nfall[I_leaf]);
  pfll2data_pft(l, nfall[I_stem]);
  pfll2data_pft(l, nfall[I_root]);
  pfll2data_pft(l, kra);
  pfll2data_pft(l, krb[I_leaf]);
  pfll2data_pft(l, krb[I_stem]);
  pfll2data_pft(l, krb[I_root]);
  pfll2data_pft(l, frg);

  pfll2data(l, micbnup);
  pfll2data(l, kdcmoss);
  pfll2data(l, kdcrawc);
  pfll2data(l, kdcsoma);
  pfll2data(l, kdcsompr);
  pfll2data(l, kdcsomcr);

}

/** Assign "veg dimension?" from parameter file. */
void CohortLookup::assignVegDimension(string &dircmt) {

  // get a list of data for the cmt number
  std::list<std::string> l = parse_parameter_file(
      dircmt + "cmt_dimvegetation.txt", cmtcode2num(this->cmtcode), 40
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  pfll2data_pft(l, vegcov);
  pfll2data_pft(l, ifwoody);
  pfll2data_pft(l, ifdeciwoody);
  pfll2data_pft(l, ifperenial);
  pfll2data_pft(l, nonvascular);
  pfll2data_pft(l, sla);
  pfll2data_pft(l, klai);
  pfll2data_pft(l, minleaf);
  pfll2data_pft(l, aleaf);
  pfll2data_pft(l, bleaf);
  pfll2data_pft(l, cleaf);
  pfll2data_pft(l, kfoliage);
  pfll2data_pft(l, cov);
  pfll2data_pft(l, m1);
  pfll2data_pft(l, m2);
  pfll2data_pft(l, m3);
  pfll2data_pft(l, m4);

  for (int i = 0; i < MAX_ROT_LAY; i++) {
    pfll2data_pft(l, frootfrac[i]);
  }

  pfll2data_pft(l, lai);

  for (int im = 0; im < MINY; im++) {
    pfll2data_pft( l, envlai[im]);
  }

}

/** Assigns "ground dimension?" parameters from file */
void CohortLookup::assignGroundDimension(string &dircmt) {

  // get a list of data for the cmt number
  std::list<std::string> l = parse_parameter_file(
      dircmt + "cmt_dimground.txt", cmtcode2num(this->cmtcode), 17
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  pfll2data(l, snwdenmax );
  pfll2data(l, snwdennew);
  pfll2data(l, initsnwthick);
  pfll2data(l, initsnwdense);

  pfll2data(l, maxdmossthick);
  pfll2data(l, initdmossthick);
  pfll2data(l, mosstype);
  pfll2data(l, coefmossa);
  pfll2data(l, coefmossb);

  pfll2data(l, initfibthick );
  pfll2data(l, inithumthick);
  pfll2data(l, coefshlwa);
  pfll2data(l, coefshlwb);
  pfll2data(l, coefdeepa);
  pfll2data(l, coefdeepb);
  pfll2data(l, coefminea);
  pfll2data(l, coefmineb);

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
  std::list<std::string> l = parse_parameter_file(
      dir + "cmt_envcanopy.txt", cmtcode2num(this->cmtcode), 12
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  pfll2data_pft(l, albvisnir);
  pfll2data_pft(l, er);
  pfll2data_pft(l, ircoef);
  pfll2data_pft(l, iscoef);
  pfll2data_pft(l, glmax);
  pfll2data_pft(l, gl_bl);
  pfll2data_pft(l, gl_c);
  pfll2data_pft(l, vpd_open);
  pfll2data_pft(l, vpd_close);
  pfll2data_pft(l, ppfd50);
  pfll2data_pft(l, initvegwater);
  pfll2data_pft(l, initvegsnow);
  
}

/** Assigns vegetation C/N parameters from config file
*/
void CohortLookup::assignBgc4Vegetation(string & dircmt) {
  
  // get a list of data for the cmt number
  std::list<std::string> l = parse_parameter_file(
      dircmt + "cmt_bgcvegetation.txt", cmtcode2num(this->cmtcode), 33
  );

  // pop each line off the front of the list
  // and assign to the right data member.
  pfll2data_pft(l, kc);
  pfll2data_pft(l, ki);
  pfll2data_pft(l, tmin);
  pfll2data_pft(l, toptmin);
  pfll2data_pft(l, toptmax);
  pfll2data_pft(l, tmax);
  pfll2data_pft(l, raq10a0);
  pfll2data_pft(l, raq10a1);
  pfll2data_pft(l, raq10a2);
  pfll2data_pft(l, raq10a3);
  pfll2data_pft(l, knuptake);
  pfll2data_pft(l, cpart[I_leaf]);
  pfll2data_pft(l, cpart[I_stem]);
  pfll2data_pft(l, cpart[I_root]);
  pfll2data_pft(l, initc2neven[I_leaf]);
  pfll2data_pft(l, initc2neven[I_stem]);
  pfll2data_pft(l, initc2neven[I_root]);
  pfll2data_pft(l, c2nb[I_leaf]);
  pfll2data_pft(l, c2nb[I_stem]);
  pfll2data_pft(l, c2nb[I_root]);
  pfll2data_pft(l, c2nmin[I_leaf]);
  pfll2data_pft(l, c2nmin[I_stem]);
  pfll2data_pft(l, c2nmin[I_root]);
  pfll2data_pft(l, c2na);
  pfll2data_pft(l, labncon);
  pfll2data_pft(l, initvegc[I_leaf]);
  pfll2data_pft(l, initvegc[I_stem]);
  pfll2data_pft(l, initvegc[I_root]);
  pfll2data_pft(l, initvegn[I_leaf]);
  pfll2data_pft(l, initvegn[I_stem]);
  pfll2data_pft(l, initvegn[I_root]);
  pfll2data_pft(l, initdeadc);
  pfll2data_pft(l, initdeadn);

}

void CohortLookup::assignEnv4Ground(string &dircmt) {
  string parfilecomm = dircmt+"cmt_envground.txt";
  BOOST_LOG_SEV(glg, note) << "Assigning parameters from " << parfilecomm;
  ifstream fctrcomm;
  fctrcomm.open(parfilecomm.c_str(),ios::in );
  bool isOpen = fctrcomm.is_open();

  if ( !isOpen ) {
    cout << "\nCannot open " << parfilecomm << "  \n" ;
    exit( -1 );
  }

  string str;
  string code;
  int lines = 27; //total lines of one block of community data/info,
                  //  except for 2 header lines
  getline(fctrcomm, str); //community separation line ("//====" or
                          //  something or empty line)
  getline(fctrcomm, str); // community code - 'CMTxx' (xx: two digits)
  code = read_cmt_code(str);

  while (code.compare(cmtcode)!=0) {
    for (int il=0; il<lines; il++) {
      getline(fctrcomm, str);  //skip lines
    }

    if (fctrcomm.eof()) {
      cout << "Cannot find community type: " << cmtcode
           << " in file: " <<parfilecomm << "  \n" ;
      exit( -1 );
    }

    getline(fctrcomm, str); //community separation line ("//====" or
                            //  something or empty line)
    getline(fctrcomm, str); //community code - 'CMTxx' (xx: two digits)

    if (str.empty()) {  // blank line in end of file
      cout << "Cannot find community type: " << cmtcode
           << " in file: " <<parfilecomm << "  \n" ;
      exit( -1 );
    }

    code = read_cmt_code(str);
  }

  fctrcomm >> snwalbmax;
  getline(fctrcomm,str);     //comments in the file
  fctrcomm >> snwalbmin;
  getline(fctrcomm,str);     //comments in the file
  fctrcomm >> psimax;
  getline(fctrcomm,str);     //comments in the file
  fctrcomm >> evapmin;
  getline(fctrcomm,str);     //comments in the file
  fctrcomm >> drainmax;
  getline(fctrcomm,str);     //comments in the file
  fctrcomm >> rtdp4gdd;
  getline(fctrcomm,str);     //comments in the file
  fctrcomm >> initsnwtem;
  getline(fctrcomm,str);     //comments in the file

  for (int il=0; il<10; il++) {
    fctrcomm >> initts[il];
    getline(fctrcomm,str);     //comments in the file
  }

  for (int il=0; il<10; il++) {
    fctrcomm >> initvwc[il];
    getline(fctrcomm,str);     //comments in the file
  }

  fctrcomm.close();
};

void CohortLookup::assignBgc4Ground(string &dircmt) {
  string parfilecomm = dircmt+"cmt_bgcsoil.txt";
  BOOST_LOG_SEV(glg, note) << "Assigning parameters from " << parfilecomm;
  ifstream fctrcomm;
  fctrcomm.open(parfilecomm.c_str(),ios::in );
  bool isOpen = fctrcomm.is_open();

  if ( !isOpen ) {
    cout << "\nCannot open " << parfilecomm << "  \n" ;
    exit( -1 );
  }

  string str;
  string code;
  int lines = 19; //total lines of one block of community data/info,
                  //  except for 2 header lines
  getline(fctrcomm, str); //community separation line ("//====" or
                          //  something or empty line)
  getline(fctrcomm, str); //community code - 'CMTxx' (xx: two digits)
  code = read_cmt_code(str);

  while (code.compare(cmtcode)!=0) {
    for (int il=0; il<lines; il++) {
      getline(fctrcomm, str);  //skip lines
    }

    if (fctrcomm.eof()) {
      cout << "Cannot find community type: " << cmtcode
           << " in file: " <<parfilecomm << "  \n" ;
      exit( -1 );
    }

    getline(fctrcomm, str); //community separation line ("//====" or
                            //  something or empty line)
    getline(fctrcomm, str); //community code - 'CMTxx' (xx: two digits)

    if (str.empty()) {  // blank line in end of file
      cout << "Cannot find community type: " << cmtcode
           << " in file: " <<parfilecomm << "  \n" ;
      exit( -1 );
    }

    code = read_cmt_code(str);
  }

  fctrcomm >> rhq10;
  getline(fctrcomm,str);
  fctrcomm >> moistmin;
  getline(fctrcomm,str);
  fctrcomm >> moistopt;
  getline(fctrcomm,str);
  fctrcomm >> moistmax;
  getline(fctrcomm,str);
  fctrcomm >> lcclnc;
  getline(fctrcomm,str);
  fctrcomm >> fsoma;
  getline(fctrcomm,str);
  fctrcomm >> fsompr;
  getline(fctrcomm,str);
  fctrcomm >> fsomcr;
  getline(fctrcomm,str);
  fctrcomm >> som2co2;
  getline(fctrcomm,str);
  fctrcomm >> kn2;
  getline(fctrcomm,str);
  fctrcomm >> nmincnsoil;
  getline(fctrcomm,str);
  fctrcomm >> propftos;
  getline(fctrcomm,str);
  fctrcomm >> fnloss;
  getline(fctrcomm,str);
  //
  fctrcomm >> initdmossc;
  getline(fctrcomm,str);
  fctrcomm >> initshlwc;
  getline(fctrcomm,str);
  fctrcomm >> initdeepc;
  getline(fctrcomm,str);
  fctrcomm >> initminec;
  getline(fctrcomm,str);
  fctrcomm >> initsoln;
  getline(fctrcomm,str);
  fctrcomm >> initavln;
  getline(fctrcomm,str);
  fctrcomm.close();
};

void CohortLookup::assignFirePar(string &dircmt) {
  string parfilecomm = dircmt+"cmt_firepar.txt";
  BOOST_LOG_SEV(glg, note) << "Assigning parameters from " << parfilecomm;
  ifstream fctrcomm;
  fctrcomm.open(parfilecomm.c_str(),ios::in );
  bool isOpen = fctrcomm.is_open();

  if ( !isOpen ) {
    cout << "\nCannot open " << parfilecomm << "  \n" ;
    exit( -1 );
  }

  string str;
  string code;
  int lines = 21; //total lines of one block of community data/info,
                  //  except for 2 header lines
  getline(fctrcomm, str); //community separation line ("//====" or
                          //  something or empty line)
  getline(fctrcomm, str); // community code - 'CMTxx' (xx: two digits)
  code = read_cmt_code(str);

  while (code.compare(cmtcode)!=0) {
    for (int il=0; il<lines; il++) {
      getline(fctrcomm, str);  //skip lines
    }

    if (fctrcomm.eof()) {
      cout << "Cannot find community type: " << cmtcode
           << " in file: " <<parfilecomm << "  \n" ;
      exit( -1 );
    }

    getline(fctrcomm, str); //community separation line ("//====" or
                            //  something or empty line)
    getline(fctrcomm, str); // community code - 'CMTxx' (xx: two digits)

    if (str.empty()) {  // blank line in end of file
      cout << "Cannot find community type: " << cmtcode
           << " in file: " <<parfilecomm << "  \n" ;
      exit( -1 );
    }

    code = read_cmt_code(str);
  }

  getline(fctrcomm,str);     // PFT code/name comments in the file

  for(int i=0; i<NUM_FSEVR; i++) {
    for(int ip=0; ip<NUM_PFT; ip++) {
      fctrcomm >> fvcombust[i][ip];
    }

    getline(fctrcomm,str);
  }

  for(int i=0; i<NUM_FSEVR; i++) {
    for(int ip=0; ip<NUM_PFT; ip++) {
      fctrcomm >> fvslash[i][ip];
    }

    getline(fctrcomm,str);
  }

  getline(fctrcomm,str);     //comments in the file

  for(int i=0; i<NUM_FSEVR; i++) {
    fctrcomm >> foslburn[i];
    getline(fctrcomm,str);
  }

  getline(fctrcomm,str);     //comments in the file
  fctrcomm >> vsmburn;
  getline(fctrcomm,str);
  fctrcomm >> r_retain_c;
  getline(fctrcomm,str);
  fctrcomm >> r_retain_n;
  getline(fctrcomm,str);
  fctrcomm.close();
};
