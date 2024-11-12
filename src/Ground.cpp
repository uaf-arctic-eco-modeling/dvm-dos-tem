/*
 * Ground.cpp
 *
 * Ground is used to manipulate the structure of snow and soil layers
 *   (1) 'Ground' comprises of a few HORIZONS as following, which are defined
 *         in /horizon/.. Snow, Rock, Moss, Organic, Mineral Soil
 *
 *   (2) EACH HORIZON may have a few LAYERS (max. no are pre-defined in
 *         /inc/layerconst.h), which are defined in /layer/..
 *
 *
 */

#include <iomanip>
#include <string>
#include <sstream>

#include <boost/tokenizer.hpp>

#include "../include/Ground.h"
#include "../include/TEMLogger.h"

extern src::severity_logger< severity_level > glg;

std::string soildesc2tag(const bool val, std::string tag) {
  if (val) {
    std::stringstream ss;
    ss << std::setw(9) << std::right << tag;
    return ss.str();
  } else {
    return "";
  }
}

/** Returns string '<-' if curl points to the same place as ql
*
* Helper for generating the layer report to visually show which layers are
* "first soil", "last soil", "first moss", "last moss", etc.
*/
std::string layer2pointertag(const Layer * curl, const Layer * ql) {
  std::stringstream ss;
  ss << std::setw(2) << std::left;
  if (!ql) {
    ss << " x"; // question layer not set!
  } else if (curl == ql) {
    ss << "<-"; // current layer is equal to the question layer
  } else {
    ss << "";
  }
  return ss.str();
}
Ground::Ground(MineralInfo mi):mineralinfo(mi) {
  // ??
}

Ground::Ground() {
  fstsoill = NULL;
  lstsoill = NULL;
  fstmossl = NULL;
  lstmossl = NULL;
  fstshlwl = NULL;
  lstshlwl = NULL;
  fstdeepl = NULL;
  lstdeepl = NULL;
  fstminel  = NULL;
  lstminel  = NULL;
  fstfntl  = NULL;
  lstfntl  = NULL;
  rocklayercreated=false;
  //this->mineralinfo = MineralInfo();
};

Ground::~Ground() {
  cleanAllLayers();
}

/** Overload for backwards compatibility, prints all columns in the layer report
*/
std::string Ground::layer_report_string() {
  return this->layer_report_string("all");
}

/** A multi-line report describing Ground's layers...

  The first several columns hold are indices and scalar values.

  The next set of columns is for visualizing where the "first" and 
  "last" pointers are for soil, fronts, moss, etc.
  \li \c '<-' in the left half of a column is for the "first" pointer
  \li \c '<-' in the right half of a column is for the "last" pointer
  \li \c ' x' indicated the pointer/member is not set.

  The final set of columns contains the "description" tags for each layer.

  EXAMPLE:
  \code{.unparsed}
  ==== LAYER REPORT ====
  [ix]           dz            z        tem       rawc SOIL|MOSS|SHLW|DEEP|MINE|FRNT|
  [ 0]   0.27243192   0.87462375   -23.8335      -9999     |    |    |    | x x| x x|      snow
  [ 1]    0.1865254   0.60219183   -23.7633      -9999     |    |    |    | x x| x x|      snow
  [ 2]   0.41566642   0.41566642   -22.1242      -9999     |    |    |    | x x| x x|      snow
  [ 3]        0.005            0   -17.8305          0 <-  |<-<-|    |    | x x| x x|      soil      moss
  [ 4]         0.02        0.005   -17.7989    11.1549     |    |<-  |    | x x| x x|      soil   organic    fibric
  [ 5]         0.04        0.025   -17.6679    38.4028     |    |    |    | x x| x x|      soil   organic    fibric
  [ 6]         0.04        0.065   -17.3991    49.5823     |    |  <-|    | x x| x x|      soil   organic    fibric
  [ 7]          0.1        0.105   -17.1882      90.62   <-|    |    |<-<-| x x| x x|      soil   organic     humic
  [ 8]            2        0.205    -11.086      -9999     |    |    |    | x x| x x|      rock
  [ 9]            4        2.205   -5.77912      -9999     |    |    |    | x x| x x|      rock
  [10]            8        6.205   -3.94041      -9999     |    |    |    | x x| x x|      rock
  [11]           16       14.205   -2.21761      -9999     |    |    |    | x x| x x|      rock
  [12]           20       30.205   -1.13197      -9999     |    |    |    | x x| x x|      rock
  \endcode
*/
std::string Ground::layer_report_string(const std::string& colunm_groups) {

  bool depth_group = false;
  bool thermal_group = false;
  bool hydro_group = false;
  bool CN_group = false;
  bool pointer_table = false;
  bool desc_table = false;

  // Parse string of column groups.
  boost::tokenizer<> tokens(colunm_groups);
  typedef boost::tokenizer<>::iterator BstTknIt;
  for (BstTknIt tkn_it=tokens.begin(); tkn_it!=tokens.end(); ++tkn_it) {
    std::string tkn = *tkn_it;

    if ("hydro" == tkn) { hydro_group = true; }
    if ("thermal" == tkn) { thermal_group = true; }
    if ("depth" == tkn) { depth_group = true; }
    if ("CN" == tkn) { CN_group = true; }
    if ("ptr" == tkn) { pointer_table = true; }
    if ("desc" == tkn) { desc_table = true; }
    if ("all" == tkn) {
      depth_group = true;
      thermal_group = true;
      hydro_group = true;
      CN_group = true;
      pointer_table = true;
      desc_table = true;
    }
  }

  std::stringstream report;
  report << "==== LAYER REPORT ====\n";

  Layer* current_layer = this->toplayer;

  if (current_layer == NULL) {
    report << " (No Layers - nothing to report...)" << std::endl;
  }
  
  // build the header for the table
  report << "[" << std::right << setw(2) << "ix" << "] ";

  if (depth_group) {
    report << std::right << setw(9) << std::setprecision(3) << "dz" << " "
           << std::right << setw(9) << std::setprecision(3) << "z" << " ";
  }
  if (thermal_group) {
    report << std::right << setw(9) << std::setprecision(3) << "tem" << " "
           << std::right << setw(4) << std::setprecision(2) << "fzn" << " "
           << std::right << setw(9) << std::setprecision(3) << "fznfrac" << " "
           << std::right << setw(9) << std::setprecision(3) << "tcond" << " "
           << std::right << setw(9) << std::setprecision(3) << "pce_t" << " "
           << std::right << setw(9) << std::setprecision(3) << "pce_f" << " ";
  }
  if (hydro_group) {
    report << std::right << setw(9) << std::setprecision(3) << "liq" << " "
           << std::right << setw(9) << std::setprecision(3) << "ice" << " "
           << std::right << setw(9) << std::setprecision(3) << "poro" << " ";

  }
  if (CN_group) {
    report << std::right << setw(9) << std::setprecision(3) << "rawc" << " ";
    report << std::right << setw(9) << std::setprecision(3) << "soma" << " ";
    report << std::right << setw(9) << std::setprecision(3) << "somcr" << " ";
    report << std::right << setw(9) << std::setprecision(3) << "sompr" << " ";
    report << std::right << setw(9) << std::setprecision(3) << "ms dmsc" << " ";
  }
  if (pointer_table) {
    report << "SOIL" << "|"
           << "MOSS" << "|"
           << "SHLW" << "|"
           << "DEEP" << "|"
           << "MINE" << "|"
           << "FRNT" << "|";
  }
  if (desc_table) {
    report << std::left << setw(27) << "     - layer type -     " << " ";
  }

  report << std::endl;

  // iterate the layer pointers, filling the table with data.
  int idx = 0;
  while (current_layer != NULL) {
    // do stuff with current_layer
    std::stringstream ls;

    ls << "[" << std::right << setw(2) << idx << "] " << std::fixed;
    if (depth_group) {
      ls << std::right << setw(9) << std::setprecision(3) << current_layer->dz << " "
         << std::right << setw(9) << std::setprecision(3) << current_layer->z << " ";
    }
    if (thermal_group) {
      ls << std::right << setw(9) << std::setprecision(3) << current_layer->tem << " "
         << std::right << setw(4) << std::setprecision(2) << current_layer->frozen << " "
         << std::right << setw(9) << std::setprecision(3) << current_layer->frozenfrac << " "
         << std::right << setw(9) << std::setprecision(3) << current_layer->tcond << " "
         << std::scientific
         << std::right << setw(9) << std::setprecision(1) << current_layer->pce_t << " "
         << std::right << setw(9) << std::setprecision(1) << current_layer->pce_f << " "
         << std::fixed;
    }
    if (hydro_group) {
      ls << std::right << setw(9) << std::setprecision(3) << current_layer->liq << " "
         << std::right << setw(9) << std::setprecision(3) << current_layer->ice << " "
         << std::right << setw(9) << std::setprecision(3) << current_layer->poro << " ";
    }
    if (CN_group) {
      ls << std::right << setw(9) << std::setprecision(3) << current_layer->rawc << " ";
      ls << std::right << setw(9) << std::setprecision(3) << current_layer->soma << " ";
      ls << std::right << setw(9) << std::setprecision(3) << current_layer->somcr << " ";
      ls << std::right << setw(9) << std::setprecision(3) << current_layer->sompr << " ";
    }
    if (pointer_table) {
      ls << layer2pointertag(current_layer, fstsoill) << ""
         << layer2pointertag(current_layer, lstsoill) << "|"
         << layer2pointertag(current_layer, fstmossl) << ""
         << layer2pointertag(current_layer, lstmossl) << "|"
         << layer2pointertag(current_layer, fstshlwl) << ""
         << layer2pointertag(current_layer, lstshlwl) << "|"
         << layer2pointertag(current_layer, fstdeepl) << ""
         << layer2pointertag(current_layer, lstdeepl) << "|"
         << layer2pointertag(current_layer, fstminel) << ""
         << layer2pointertag(current_layer, lstminel) << "|"
         << layer2pointertag(current_layer, fstfntl) << ""
         << layer2pointertag(current_layer, lstfntl) << "|";
         // this T/ST KEY business seems to be dupliacate info as the "soil description tag"
         //<< "T/ST KEY:" << std::right << setw(2) << current_layer->tkey << "/" << "[na]"//current_layer->stkey << " "
    }
    if (desc_table) {
      ls << soildesc2tag(current_layer->isSnow, "snow")
         << soildesc2tag(current_layer->isSoil, "soil")
         << soildesc2tag(current_layer->isRock, "rock")
         << soildesc2tag(current_layer->isMoss, "moss")
         << soildesc2tag(current_layer->isMineral, "mineral")
         << soildesc2tag(current_layer->isOrganic, "organic")
         << soildesc2tag(current_layer->isFibric, "fibric")
         << soildesc2tag(current_layer->isHumic, "humic");
    }
    ls << std::endl;

    report << ls.str();

    // increment the current layer pointer
    ++idx;
    current_layer = current_layer->nextl;
  }
  return report.str();
}


//
void Ground::initParameter() {
  //parameters for snow dimension
  snowdimpar.denmax = chtlu->snwdenmax;   //kg/m3
  snowdimpar.newden = chtlu->snwdennew;
  //parameters for soil dimension
  soildimpar.maxmossthick = chtlu->maxdmossthick;
  soildimpar.minmossthick = chtlu->maxdmossthick*0.050;
  soildimpar.minshlwthick = 0.010;   // meters
  soildimpar.coefshlwa  = chtlu->coefshlwa;
  soildimpar.coefshlwb  = chtlu->coefshlwb;
  soildimpar.mindeepthick = 0.005;   // meters
  soildimpar.coefdeepa  = chtlu->coefdeepa;
  soildimpar.coefdeepb  = chtlu->coefdeepb;
  soildimpar.coefminea  = chtlu->coefminea;
  soildimpar.coefmineb  = chtlu->coefmineb;
};

/** Initialize dimensions from inputs. */
void Ground::initDimension() {
  snow.thick = chtlu->initsnwthick;
  snow.dense = chtlu->initsnwdense;

  moss.thick = chtlu->initdmossthick;
  moss.type  = chtlu->mosstype;
  organic.shlwthick = chtlu->initfibthick;
  organic.deepthick = chtlu->inithumthick;
  
  soilparent.thick = 50.0;  // meter


  // SHOULD BE ABLE TO GET RID OF ALL OF THIS WITH PROPERLY CONSTRUCTED MineralInfo object!
  //mineralinfo.num = 0;
  //mineralinfo.thick = 0;
  //
  ////BOOST_LOG_SEV(glg, warn) << "FIX THIS!!!! ARIBTRARILY SETTING TEXTURE!";
  ////for (int il=0; il<MAX_MIN_LAY; il++) {
  ////  chtlu->minetexture[il] = 4;
  ////}
  //
  //for (int il=0; il<MAX_MIN_LAY; il++) {
  //  //mineralinfo.sand = chtlu->pctsand;
  //  //mineralinfo.silt = chtlu->pctsilt;
  //  //mineralinfo.clay = chtlu->clay;
  //  //mineralinfo.thick += MINETHICK[il];
  //  //mineralinfo.dz[il] = MINETHICK[il];
  //
  //  // Not sure if it will be a problem adding thickness for all layers, and not just
  //  // the layers that have a texture defined??
  //  // we aren't using texture, and I think every mineral layer will have percentages sand/silt/clay...
  //
  //  if (chtlu->minetexture[il] > 0 && MINETHICK[il]>0.) {
  //    mineralinfo.num+=1;
  //    mineralinfo.thick += MINETHICK[il];
  //    mineralinfo.dz[il] = MINETHICK[il];
  //    mineralinfo.texture[il] = chtlu->minetexture[il];
  //  } else {
  //    break;
  //  }
  //}

}

void Ground::initLayerStructure(snwstate_dim *snowdim, soistate_dim *soildim) {
  // Needs to clean up old 'ground', if any
  cleanAllLayers();

  rocklayercreated = false;

  // Layers are constructed from bottom
  if(rocklayercreated) {
    cleanSnowSoilLayers();
  } else {
    initRockLayers(); // Rock in the bottom first and no-need to do again
  }


  initSnowSoilLayers();
  resortGroundLayers();
  // put the layer structure to 'cd'
  retrieveSnowDimension(snowdim);
  retrieveSoilDimension(soildim);
};

void Ground::initRockLayers() {
  soilparent.updateThicknesses(soilparent.thick); //thickness in m

  for(int il =soilparent.num-1; il>=0; il--) {
    ParentLayer* rl = new ParentLayer(soilparent.dz[il]);
    insertFront(rl);
  }

  rocklayercreated=true;
};

/** Note as is, this is not setup to be called after fire! see moss initialization.*/
void Ground::initSnowSoilLayers() {
  // mineral thickness must be input before calling this
  for(int il = mineralinfo.num - 1; il >= 0; il--) {
    MineralLayer* ml = new MineralLayer(mineralinfo.dz[il],
                                        mineralinfo.sand[il],
                                        mineralinfo.silt[il],
                                        mineralinfo.clay[il]);
    insertFront(ml);
  }

  //need to do shlw organic horizon division before organic deep horizon,
  //since the layers of deep are determined by the thickness of last shlw layer
  organic.ShlwThickScheme(organic.shlwthick); //fibthick in m, which needs input
  organic.DeepThickScheme(organic.deepthick); //humthick in m, which needs input

  // but for insertion of layers into the double-linked matrix, do the
  //   deep organic first
  for(int il = organic.deepnum-1; il >=  0; il--) {
    OrganicLayer* pl = new OrganicLayer(organic.deepdz[il], 2, chtlu); //2 means deep organic
    insertFront(pl);
  }

  for(int il = organic.shlwnum-1; il >= 0; il--) {
    OrganicLayer* pl = new OrganicLayer(organic.shlwdz[il], 1, chtlu); //1 means shallow organic
    insertFront(pl);
  }

  // if dead moss thickness is specified in chtlookup from init file
  if (moss.thick > 0.0) {

    bool moss_pft_exists = false;
    //if ANY of the nonvascular PFTs have vegcov
    for(int ii=0; ii<NUM_PFT; ii++){
      if(chtlu->vegcov[ii]>0.0){
        moss_pft_exists = true;
      }
    }

    if(moss_pft_exists){

      //This is wrong - FIX. Should be related to living moss C pool
      double initmldz[1] = {0.01};

      int soiltype[] = {0};

      moss.setThicknesses(soiltype, initmldz, 1);

      for(int il = moss.num-1; il >= 0; il--) {
        // moss type (1- sphagnum, 2- feathermoss), which needs input
        MossLayer* ml = new MossLayer(moss.dz[il], moss.type, chtlu);
        insertFront(ml);
      }
    }
    else{
      BOOST_LOG_SEV(glg, debug)<<"No moss PFT exists, so do not create moss layers";
    }
  }
  else{
    BOOST_LOG_SEV(glg, debug)<<"No moss thickness specified";
  }

  // only ONE snow layer input assummed, if any
  if(snow.thick > 0) {
    SnowLayer* sl = new SnowLayer();
    sl->dz = snow.thick;
    insertFront(sl);
  }
}

void Ground::set_state_from_restartdata(snwstate_dim *snowdim,
                                   soistate_dim *soildim,
                                   const RestartData & rdata) {

  // This cleaning up will keep the bottom layer of the profile - if one try to
  // force deleting it, one would get a seg fault. So let's try to delete this
  // old bottom layer after new rock 
  cleanAllLayers();
  
  // test if any layer is remaining
  Layer* current_layer = this->toplayer;
  int extra = 0;
  if (current_layer == NULL) {
    BOOST_LOG_SEV(glg, warn) << " (No Layers left...)";
  } else {
    BOOST_LOG_SEV(glg, warn) << " (Remaining Layers...)";
    while(current_layer!=NULL) {
      ++extra;
      current_layer = current_layer->nextl;
    }
  }

  soilparent.num = 0;
  soilparent.thick = 0.;

  for (int i=0; i<MAX_ROC_LAY; i++) {
    soilparent.dz[i] = rdata.DZrock[i];
    soilparent.type[i] = MISSING_I;    // not used now
    soilparent.num += 1;
    soilparent.thick += soilparent.dz[i];
  }

  for(int il =soilparent.num-1; il>=0; il--) {
    ParentLayer* rl = new ParentLayer(soilparent.dz[il]);
    insertFront(rl);
  }

  // Clean extra bottom rock layers if any
  for(int il = soilparent.num-1+extra; il>soilparent.num-1; il--) {
    BOOST_LOG_SEV(glg, warn) << "after parent layers :" << il;
    cleanRockLayers(); 
  }

  rocklayercreated = true;
  //
  int soiltype[MAX_SOI_LAY];
  int soilage[MAX_SOI_LAY];
  double dzsoil[MAX_SOI_LAY];
  int frozen[MAX_SOI_LAY];

  for (int i=0; i<MAX_SOI_LAY; i++) {
    soiltype[i]    = rdata.TYPEsoil[i];
    soilage[i]     = rdata.AGEsoil[i];
    dzsoil[i]      = rdata.DZsoil[i];
    frozen[i]      = rdata.FROZENsoil[i];
  }

  mineralinfo.set5Soilprofile(soiltype, dzsoil, MAX_SOI_LAY);

  for(int il =mineralinfo.num-1; il>=0; il--) {

    MineralLayer* ml = new MineralLayer(mineralinfo.dz[il],
                                        mineralinfo.sand[il],
                                        mineralinfo.silt[il],
                                        mineralinfo.clay[il]);

    ml->age = soilage[il];
    ml->frozen = frozen[il];
    insertFront(ml);
  }

  organic.assignDeepThicknesses(soiltype, dzsoil, MAX_SOI_LAY);

  for(int il = organic.deepnum-1; il>=0; il--) {
    OrganicLayer* pl = new OrganicLayer(organic.deepdz[il], 2, chtlu); //2 means deep organic
    pl->age = soilage[il];
    pl->frozen = frozen[il];
    insertFront(pl);
  }

  organic.assignShlwThicknesses(soiltype, dzsoil, MAX_SOI_LAY);

  for(int il =organic.shlwnum-1; il>=0; il--) {
    OrganicLayer* pl = new OrganicLayer(organic.shlwdz[il], 1, chtlu);//1 means shallow organic
    pl->age = soilage[il];
    pl->frozen = frozen[il];
    insertFront(pl);
  }

  moss.setThicknesses(soiltype, dzsoil, MAX_SOI_LAY);

  for(int il = moss.num-1; il>=0; il--) {
    MossLayer* ml = new MossLayer(moss.dz[il], moss.type, chtlu);
    ml->age = soilage[il];
    ml->frozen = frozen[il];
    insertFront(ml);
  }

  //snow
  snow.coverage  = 0.;
  snow.extramass = 0.;
  snow.numl  = 0;
  snow.thick = 0.;

  for(int il =MAX_SNW_LAY-1; il>=0; il--) {
    if(rdata.DZsnow[il]>0) {
      SnowLayer* snwl = new SnowLayer();
      snwl->dz = rdata.DZsnow[il];
      snwl->age = rdata.AGEsnow[il];
      snwl->rho = rdata.RHOsnow[il];
      insertFront(snwl);
      snow.coverage = 1.;
      snow.dz[il] = rdata.DZsnow[il];
      snow.numl++;
      snow.thick += rdata.DZsnow[il];
    } else {
      snow.dz[il] = MISSING_D;
    }
  }

  //
  frontsz.clear();
  frontstype.clear();
  int frontFT[MAX_NUM_FNT];
  double frontZ[MAX_NUM_FNT];

  for (int i=0; i<MAX_NUM_FNT; i++) {
    frontZ[i] = rdata.frontZ[i];
    frontFT[i] = rdata.frontFT[i];
  }

  for(int ifnt = 0; ifnt<MAX_NUM_FNT; ifnt++) {
    if(frontZ[ifnt]>0.) {
      frontsz.push_back(frontZ[ifnt]);
      frontstype.push_back(frontFT[ifnt]);
    }
  }

  //
  resortGroundLayers();
  // put the layer structure to 'cd'
  retrieveSnowDimension(snowdim);
  retrieveSoilDimension(soildim);
};

// called at the time of restructuring or initializing soil layers
void Ground::resortGroundLayers() {
  setFstLstSoilLayer(); // This must be called at first
  updateLayerIndex();
  updateLayerZ();
  setFstLstMineLayers();
  setFstLstMossLayers();
  setFstLstShlwLayers();
  setFstLstDeepLayers();
  setFstLstFrontLayers();
};

void Ground::setFstLstSoilLayer() {
  fstsoill = NULL;
  lstsoill = NULL;
  Layer* currl = toplayer;

  while(currl!=NULL) {
    if(currl->isSoil) {
      fstsoill =currl;
      break;
    }

    currl = currl->nextl;
  }

  currl = botlayer;

  while(currl!=NULL) {
    if(currl->isSoil) {
      lstsoill =currl;
      break;
    }

    currl = currl->prevl;
  }
};

// only perform this at initialization of cohort
// the mineral layer will never be removed/added
void Ground::setFstLstMineLayers() {
  fstminel = NULL;
  fstminel = NULL;
  Layer* currl = toplayer;

  while(currl!=NULL) {
    if(currl->isSoil && currl->isMineral) {
      fstminel = currl;
      break;
    }

    currl = currl->nextl;
  }

  currl =botlayer;

  while(currl!=NULL) {
    if(currl->isSoil && currl->isMineral) {
      lstminel = currl;
      break;
    }

    currl=currl->prevl;
  }
};

void Ground::setFstLstMossLayers() {
  fstmossl = NULL;
  lstmossl = NULL;
  Layer* currl = fstsoill;

  while(currl!=NULL) {
    if(currl->isMoss) {
      // first moss layer
      if (currl->prevl==NULL || !currl->prevl->isMoss) {
        fstmossl = currl;
      }

      // last moss layer
      if (currl->nextl==NULL || !currl->nextl->isMoss) {
        lstmossl = currl;
        break;
      }
    } else {
      break; //So, 'moss' layer always stay on the top soil
    }

    currl = currl->nextl;
  }
};

void Ground::setFstLstShlwLayers() {
  fstshlwl =NULL;
  lstshlwl =NULL;
  Layer* currl = fstsoill;

  while(currl!=NULL) {
    if(currl->isFibric) {
      // first fibric layer
      if (currl->prevl==NULL || !currl->prevl->isFibric) {
        fstshlwl = currl;
      }

      // last fibric layer
      if (currl->nextl==NULL || !currl->nextl->isFibric) {
        lstshlwl = currl;
        organic.lstshlwdz = currl->dz;
        break;
      }
    } else {
      if (currl->isMineral) {
        break;  //So, No burried organic horizon exists in the model
      }
    }

    currl = currl->nextl;
  }
}

void Ground::setFstLstDeepLayers() {
  fstdeepl =NULL;
  lstdeepl =NULL;
  Layer* currl = fstsoill;

  while(currl!=NULL) {
    if(currl->isHumic) {
      // first humic layer
      if (currl->prevl==NULL || !currl->prevl->isHumic) {
        fstdeepl = currl;
      }

      // last humic layer
      if (currl->nextl==NULL || !currl->nextl->isHumic) {
        lstdeepl = currl;
        break;
      }
    } else {
      if (currl->isMineral) {
        break;  //So, No burried organic horizon exists in the model
      }
    }

    currl = currl->nextl;
  }
};

void Ground::setFstLstFrontLayers() {
  // determine the first and last soil layer with thawing/freezing fronts
  fstfntl=NULL;
  lstfntl=NULL;
  Layer* currl=fstsoill;

  while(currl!=NULL) {
    if(currl->frozen==0 && currl->isSoil) {
      fstfntl=currl;
      break;
    }

    currl=currl->nextl;
  }

  if(fstfntl!=NULL) {
    currl=botlayer;

    while(currl!=NULL) {
      if(currl->isSoil && currl->frozen==0) {
        lstfntl=currl;
        break;
      }

      currl=currl->prevl;
    }
  }

  //
  checkFrontsValidity();
};

void Ground::updateLayerIndex() {
  Layer* currl = toplayer;
  int ind =0;
  int sind=0;

  while (currl!=NULL) {
    ind++;
    currl->indl =ind;

    if(currl->isSoil) {
      sind++;
      currl->solind = sind;
    }

    currl =currl->nextl;
  }
};

// update the z, which is the distance between soil surface and top of a
//   soil layer. Note that the dz for each layer already known.
void Ground::updateLayerZ() {
  // soil layers are indexed downwardly
  Layer* currl = fstsoill; // 'fstsoill' must be first set up or updated

  while(currl!=NULL) {
    if (currl==fstsoill) {
      currl->z = 0.0;
    } else {
      currl->z = currl->prevl->z + currl->prevl->dz;
    }

    currl = currl->nextl;
  }

  // snow layers ar indexed upwardly
  currl = fstsoill;     // 'fstsoill' must be first set up or updated

  while(currl!=NULL) {
    if (currl->isSnow) {
      currl->z = currl->nextl->z+currl->nextl->dz;
    } else {
      break;
    }

    currl = currl->prevl;
  }
};

// update information from layer's properties, except for 'type'
void Ground::updateSoilHorizons() {
  moss.num = 0;
  moss.thick = 0.;

  for (int i=0; i<MAX_MOS_LAY; i++) {
    moss.dz[i] = MISSING_D;
  }

  organic.shlwnum = 0;
  organic.shlwthick = 0.;
  organic.shlwc = 0.;

  for (int i=0; i<MAX_SLW_LAY; i++) {
    organic.shlwdz[i] = MISSING_D;
  }

  organic.deepnum = 0;
  organic.deepthick = 0.;

  for (int i=0; i<MAX_DEP_LAY; i++) {
    organic.deepdz[i] = MISSING_D;
  }

  mineralinfo.num = 0;
  mineralinfo.thick = 0.;

  for (int i=0; i<MAX_MIN_LAY; i++) {
    mineralinfo.dz[i] = MISSING_D;
  }

  ///
  Layer* currl = toplayer;
  int ind = -1;

  while(currl!=NULL) {
    if(currl->isMoss) {
      ind += 1;
      moss.num += 1;
      moss.thick += currl->dz;
      moss.dz[ind] = currl->dz;

      if (currl->nextl==NULL || (!currl->nextl->isMoss)) {
        ind = -1;
      }
    } else if(currl->isFibric) {
      ind +=1;
      organic.shlwnum +=1;
      organic.shlwthick +=currl->dz;
      organic.shlwdz[ind] = currl->dz;
      organic.shlwc += currl->rawc;

      if (currl->nextl==NULL || (!currl->nextl->isFibric)) {
        ind = -1;
      }
    } else if(currl->isHumic) {
      ind +=1;
      organic.deepnum +=1;
      organic.deepthick +=currl->dz;
      organic.deepdz[ind] = currl->dz;

      if (currl->nextl==NULL || (!currl->nextl->isHumic)) {
        ind = -1;
      }
    } else if(currl->isMineral) {
      ind +=1;
      mineralinfo.num +=1;
      mineralinfo.thick +=currl->dz;
      mineralinfo.dz[ind] = currl->dz;
      // Check that the layer is a MineralLayer - otherwise the compiler
      // complains about currl not having pctsand member.
      if (MineralLayer* ml = dynamic_cast<MineralLayer*>(currl)) {
        mineralinfo.sand[ind] = ml->pctsand;
        mineralinfo.silt[ind] = ml->pctsilt;
        mineralinfo.clay[ind] = ml->pctclay;
      }
      if (currl->nextl==NULL || (!currl->nextl->isMineral)) {
        ind = -1;
      }
    } else if (currl->isRock) {
      break;
    }

    currl = currl->nextl;
  }
};

///////////////////////////////////////////////////////////////////////
//update the snowlayer z, which is the distance between soil surface and
//  top of a snow layer
void Ground::updateSnowHorizon() {
  snow.reset();
  Layer* curr = fstsoill;
  int snowind = 0;
  double oldz = 0.;

  while(curr!=NULL) {
    if(curr->isSnow) {
      curr->z = oldz + curr->dz;
      oldz = curr->z;
      snow.numl++;
      snow.dz[snowind] = curr->dz; //note: snow layer index 0 starting
                                   //        from 'fstsoill' upwardly
      snow.thick += curr->dz;

      if (snow.age<=curr->age) {
        snow.age = curr->age;  // the oldest layer age
      }

      snow.swe += curr->ice;
      snowind ++;
    }

    curr = curr->prevl;   //Note: 'snow', the index is ordered upwardly
  }

  if (snow.thick > 0.) {  //d_snws.swesum includes 'extramass', which is less
                          //  than that for constructing a single snow layer
    snow.dense = snow.swe/snow.thick;
    snow.coverage = 1.;
  } else if (snow.extramass>0.) {
    snow.dense = snowdimpar.newden;
    snow.coverage = snow.extramass/snowdimpar.newden/snow.mindz[1];
  } else {
    snow.dense = 0.;
    snow.coverage = 0.;
  }
};

// Snow Layers construction (+ 'extramass') or ablation (-'extramass')
bool Ground::constructSnowLayers(const double & dsmass, const double & tdrv) {
  bool layerchanged=false;
  snow.extramass += dsmass; //Note: 'dsmass' + for snow-adding, - for
                            //      snow-melting/sublimating when calling
                            //      this function

  if(snow.extramass>0) { // accumulate
    double density = snowdimpar.newden;
    double thick = snow.extramass/density;

    if(toplayer->isSnow) {
      SnowLayer * snwl = new SnowLayer();
      snwl->age = 0.;
      snwl->rho = snowdimpar.newden;
      snwl->dz = thick;
      snwl->ice = snow.extramass;
      snow.extramass = 0.;
      snwl->frozen =1;
      snwl->tem = tdrv;
      insertFront(snwl);
      return  true;
    } else { // snow layer does not exist
      double tsno =toplayer->tem;

      if(tsno<=0) {
        SnowLayer * snwl = new SnowLayer();
        snwl->rho    = snowdimpar.newden;
        snwl->dz  = thick;
        snwl->ice = snow.extramass;
        snow.extramass = 0.;
        snwl->frozen =1;
        snwl->tem = tdrv;
        insertFront(snwl);
        return true;
      }
    }
  } else if (snow.extramass<0.) { // ablate
    double ablat = -snow.extramass;
    snow.extramass = 0.;

    //remove whole snow layer, if ablation meets
    if(toplayer->isSnow) {
      while(ablat>= toplayer->ice) {
        ablat -= toplayer->ice;
        removeFront(); //NOTE: here after calling removeFront(),
                       //        the 'toplayer' will be updated!
        layerchanged =true;

        if(toplayer->isSoil) {
          break;
        }
      }
    }

    // partially remove snow layer, if any, after above whole layer
    //   removal process
    if(toplayer->isSnow) {
      toplayer->dz *= ((toplayer->ice -ablat)/(toplayer->ice));
      toplayer->ice -= ablat;
    }
  }

  return layerchanged;
};

bool Ground::divideSnowLayers() {
  bool layerchanged =false;
  Layer* currl;
STARTOFDIVIDE:
  currl= toplayer;

  while(currl!=NULL) {
    if(currl->isSoil) {
      break;
    }

    if(currl->dz>snow.maxdz[currl->indl]) {
      if(currl->nextl->isSnow) {//assume that the nextl meets the dz requirement
        currl->dz /=2;
        currl->liq /=2;
        currl->ice /=2;
        currl->nextl->liq += currl->liq;
        currl->nextl->ice += currl->ice;
        currl->nextl->dz  += currl->dz;
        currl->nextl->rho  = currl->nextl->ice/currl->nextl->dz;
      } else { //create new layer
        if(currl->indl+1 <MAX_SNW_LAY-1) {
          if(currl->dz/2>snow.mindz[currl->indl+1]) {
            currl->dz  /=2;
            currl->liq /=2;
            currl->ice /=2;
            SnowLayer* sl = new SnowLayer();
            sl->clone(dynamic_cast<SnowLayer*>(currl));
            sl->tem = currl->tem;
            insertAfter(sl, currl);
            updateLayerIndex();
            layerchanged =true;
            goto STARTOFDIVIDE;
          } else if(currl->dz- snow.maxdz[currl->indl]
                    >= snow.mindz[currl->indl+1]) {
            double tempdz = currl->dz;
            double tempice = currl->ice;
            double templiq = currl->liq;
            currl->dz = snow.maxdz[currl->indl];
            currl->liq *= currl->dz/tempdz ;
            currl->ice *= currl->dz/tempdz ;
            SnowLayer* sl = new SnowLayer();
            sl->tem = currl->tem;
            sl->clone(dynamic_cast<SnowLayer*>(currl));
            sl->dz  = tempdz - currl->dz;
            sl->liq = templiq -currl->liq;
            sl->ice = tempice -currl->ice;
            insertAfter(sl, currl);
            updateLayerIndex();
            layerchanged =true;
            goto STARTOFDIVIDE;
          }
        } else {
          break;
        }
      }
    }

    currl= currl->nextl;
  }

  return layerchanged;
};

bool Ground::combineSnowLayers() {
  bool layerchanged =false;
  Layer* currl;
  Layer* tempnext;
STARTCOMBINE:
  currl= toplayer;

  while(currl!=NULL && currl->nextl!=NULL) {
    // for case of first layer
    tempnext = currl->nextl;

    if(currl==toplayer) {
      if(currl->isSnow) {
        if(currl->dz < snow.mindz[currl->indl]) {
          if(currl->nextl->isSnow) {
            currl->nextl->liq += currl->liq;
            currl->nextl->ice += currl->ice;
            currl->nextl->dz  += currl->dz;
            currl->nextl->rho = currl->nextl->ice/currl->nextl->dz;
            currl->nextl->age = currl->nextl->age/2. + currl->age/2.;
          } else { // set extramass
            snow.extramass += currl->ice;
          }

          //remove current layer
          removeLayer(currl);
          updateLayerIndex();
          layerchanged =true;
          goto STARTCOMBINE;
        }
      }
    } else { // for other layers
      if(currl->isSnow) {
        if(currl->dz < snow.mindz[currl->indl]) {
          if(currl->nextl->isSnow) {
            //find the thinest layer
            if(currl->nextl->dz<currl->prevl->dz) {
              currl->nextl->liq += currl->liq;
              currl->nextl->ice += currl->ice;
              currl->nextl->dz +=currl->dz;
              currl->nextl->rho = currl->nextl->ice/currl->nextl->dz;
            } else {
              currl->prevl->liq += currl->liq;
              currl->prevl->ice += currl->ice;
              currl->prevl->dz  +=currl->dz;
              currl->prevl->rho = currl->prevl->ice/currl->prevl->dz;
            }
          } else { // combine to upper snow layer
            currl->prevl->liq += currl->liq;
            currl->prevl->ice += currl->ice;
            currl->prevl->dz  +=currl->dz;
            currl->prevl->rho = currl->prevl->ice/currl->prevl->dz;
          }

          //remove current layer
          removeLayer(currl);
          updateLayerIndex();
          layerchanged = true;
          goto STARTCOMBINE;
        }
      }
    }

    currl= tempnext;

    if(currl->isSoil) {
      break;
    }
  }

  return layerchanged;
};

void Ground::updateSnowLayerPropertiesDaily() {
  Layer* currl=toplayer;

  while(currl!= NULL) {
    if(currl->isSnow) {
      currl->advanceOneDay();
      dynamic_cast<SnowLayer*>(currl)->updateDensity(&snowdimpar);   // this will compact snow layer based on snowlayer age
      dynamic_cast<SnowLayer*>(currl)->updateThick();
    } else {
      break;
    }

    currl=currl->nextl;
  }
};

// save double-linked snow structure to 'cd' snow states
void Ground::retrieveSnowDimension(snwstate_dim * snowdim) {
  Layer * curr=toplayer;
  int snwind = 0;

  while(curr!=NULL) {
    if(curr->isSnow) {
      //dimension output here as well
      snowdim->dz[snwind] = curr->dz;
      snowdim->age[snwind]= curr->age;
      snowdim->rho[snwind]= curr->rho;
      snowdim->por[snwind]= curr->poro;
      curr = curr->nextl;
    } else {
      if (snwind>=MAX_SNW_LAY) {
        break;
      }

      snowdim->dz[snwind] = MISSING_D;
      snowdim->age[snwind]= MISSING_D;
      snowdim->rho[snwind]= MISSING_D;
      snowdim->por[snwind]= MISSING_D;
    }

    snwind++;
  }

  snowdim->olds   = snow.age;
  snowdim->thick  = snow.thick;
  snowdim->numsnwl= snow.numl;
  snowdim->dense  = snow.dense;
  snowdim->extramass = snow.extramass;
}

////////////////////////////////////////////////////////////////////////////////
// Basically, here will not do thickness change, which will carry out in
// 'updateOslThickness5Carbon', therefore, any new layer creation, will have
// to originate from neighbouring layer, otherwise mathematic error will occur
// except for create new moss/fibrous organic layer from none.
void  Ground::redivideSoilLayers() {
  redivideMossLayers(moss.type);
  redivideShlwLayers();
  redivideDeepLayers();
  checkWaterValidity();
};

/** ??? */
void  Ground::redivideMossLayers(const int &mosstype) {
  // Before adjusting moss layer, needs checking if Moss layer exists
  setFstLstMossLayers();

  BOOST_LOG_SEV(glg, debug)<<"redividemosslayers() moss.thick: "<<moss.thick;

  // If no moss layer exists, force creation
  if( fstmossl==NULL ) {
    moss.type = mosstype;

    //Create live moss
    moss.thick = 0.01;
    BOOST_LOG_SEV(glg, debug)<<"Creating new moss layer, type: "<<moss.type<<", thickness: "<<moss.thick;
    MossLayer* ml = new MossLayer(moss.thick, moss.type, chtlu);
    moss.num = 1;
    ml->tem = fstsoill->tem;
    ml->z = 0.0;
    insertBefore(ml, fstsoill);
    setFstLstSoilLayer();//Called before moss to ensure soil ptrs are set
    setFstLstMossLayers();
    adjustFrontsAfterThickchange(ml->z, ml->dz); 

    for(int ii=0; ii<moss.num; ii++){
      if(ii==0){ml = (MossLayer*)fstmossl;}
      else if(ii==moss.num-1){ml = (MossLayer*)lstmossl;}

      ml->derivePhysicalProperty();
      if(ml->tem>0.) {
        //assuming same volume content as the following layer
        ml->liq = ml->nextl->getVolLiq()*DENLIQ*ml->dz;
        ml->ice = 0.;
        ml->frozen = -1;
        ml->frozenfrac = 0.;
      } else {
        ml->liq = 0.;
        //assumming same volume content as the following layer;
        ml->ice = ml->nextl->getVolIce()*DENICE*ml->dz;
        ml->frozen = 1;
        ml->frozenfrac = 1.;
      }

      ml->rawc = 0.0;
      ml->soma = 0.0;
      ml->sompr= 0.0;
      ml->somcr= 0.0;
      ml->orgn = 0.0;
      ml->avln = 0.0;
      resortGroundLayers();
      updateSoilHorizons();
    }
  }
    // one-layer moss currently assumed, so no need to do redivision

  // moss.thick is too small
};

void Ground::redivideShlwLayers() {
  organic.shlwchanged = false;

  ////////// IF there exists 'shlw' layer(s) ////////////////
  if(fstshlwl != NULL) {
    Layer* currl;
    SoilLayer* upsl ;
    SoilLayer* lwsl;
    organic.shlwchanged =true;
    // first, combine all layers into one
COMBINEBEGIN:
    currl =fstshlwl;

    while(currl!=NULL) {
      if(currl->indl<lstshlwl->indl && currl->nextl->isFibric) {
        upsl = dynamic_cast<SoilLayer*>(currl);
        lwsl = dynamic_cast<SoilLayer*>(currl->nextl);
        combineTwoSoilLayersL2U(lwsl,upsl);  //combine this layer and next layer
        upsl->indl = lwsl->indl;
        removeLayer(currl->nextl);
        goto COMBINEBEGIN;
      } else {
        break;
      }

      currl =currl->nextl;
    }

    lstshlwl = fstshlwl;
    updateSoilHorizons(); //all 'shlwl' are merged at this point,
                          //  and 'horizon' info updated
    // then, re-do the thickness division
    organic.ShlwThickScheme(organic.shlwthick);

    // restructure the double-linked 'shlw layer'
    if(organic.shlwnum==0) { // just in case
      fstshlwl=NULL;
      lstshlwl=NULL;
    } else if (organic.shlwnum ==1) { //only change the 'dz' dependent
                                      //  properties of layer
      fstshlwl->dz = organic.shlwdz[0];
      SoilLayer* shlwsl = dynamic_cast<SoilLayer*>(fstshlwl);
      shlwsl->derivePhysicalProperty();
    } else {
      OrganicLayer* plnew;

      for (int i=organic.shlwnum-1; i>0; i--) {
        plnew = new OrganicLayer(organic.shlwdz[i], 1, chtlu);
        SoilLayer* shlwsl = dynamic_cast<SoilLayer*>(fstshlwl);
        //split 'plnew' from bottom of 'shlwsl'
        splitOneSoilLayer(shlwsl, plnew, 0., organic.shlwdz[i]);
        insertAfter(plnew, shlwsl);
      }
    }

    // end of adjusting existing layer structure
    ////no existing fibric layer, MUST create a new one from the following layer
  } else {
    SoilLayer *nextsl;

    if (fstdeepl != NULL) {
      nextsl = dynamic_cast<SoilLayer*>(fstdeepl);
    } else {
      nextsl = dynamic_cast<SoilLayer*>(fstminel);
    }
    
    double cfall_ls_tot = 0;//total carbon litterfall from leaf and stem
    for(int pp=0; pp<2; pp++){//leaf and stem
      for(int ip=0; ip<NUM_PFT; ip++){
        if(chtlu->nonvascular[ip]==0){//vascular only
          cfall_ls_tot += chtlu->cfall[pp][ip];
        }
      }  
    }

    double rawcmin = carbonFromThickness(MINSLWTHICK, soildimpar.coefshlwa, soildimpar.coefshlwb);

    // FIX: Problem if nextsl is still NULL
    //if (nextsl->rawc >= rawcmin) {
    //bd->m_soid.shlwc? As seen Soil_Bgc.cpp:73
    //if(organic.shlwc > 0.0){
    double abvgfallC = bd->m_v2soi.ltrfalcall - bd->m_v2soi.ltrfalc[I_root];
    if(abvgfallC > 0.0){
    //if(cfall_ls_tot > 0.0){
    //if(bd->m_v2soi.ltrfalcall > 0.0){
      organic.shlwchanged =true;
      double thick = thicknessFromCarbon(abvgfallC, soildimpar.coefshlwa, soildimpar.coefshlwb);
      //organic.ShlwThickScheme(MINSLWTHICK);
      organic.ShlwThickScheme(thick);
      OrganicLayer* plnew = new OrganicLayer(organic.shlwdz[0], 1, chtlu);
      //plnew->dz= MINSLWTHICK;
      plnew->dz= thick;
      //double frac = MINSLWTHICK/nextsl->dz;
      double frac = thick/nextsl->dz;
      // assign properties for the new-created 'shlw' layer
      plnew->ice = fmax(0., nextsl->ice*frac);
      plnew->liq = fmax(0., nextsl->liq*frac);

      if (plnew->ice>plnew->maxice) {
        plnew->ice = plnew->maxice;
      }

      if (plnew->liq>plnew->maxliq) {
        plnew->liq = plnew->maxliq;
      }

      plnew->tem = nextsl->tem;
      getLayerFrozenstatusByFronts(plnew);
      plnew->rawc  = abvgfallC;
      plnew->soma  = 0.;
      plnew->sompr = 0.;
      plnew->somcr = 0.;
      plnew->orgn  = 0.;
      plnew->avln  = 0.;
      plnew->derivePhysicalProperty();
      insertBefore(plnew, nextsl);
      // adjust properties for the following layer
      //nextsl->ice -= plnew->ice;
      //nextsl->liq -= plnew->liq;
      //nextsl->rawc-=rawcmin;

      if (nextsl->isHumic) {//additional changes needed for if the
                            //  following layer is 'humic'
        nextsl->dz *=(1.-frac);
      }

      nextsl->derivePhysicalProperty();
      updateSoilHorizons();
    }
  }

  resortGroundLayers();
}

void Ground::redivideDeepLayers() {
  ////////// IF there exists 'deep' layer(s) ////////////////
  if(fstdeepl != NULL) {
    Layer * currl = fstdeepl;
    // Adjusting the OS horizon's layer division/combination
    SoilLayer* upsl ;
    SoilLayer* lwsl;

    // combine all deep layers into ONE for re-structuring

    COMBINEBEGIN:
    currl = fstdeepl;

    while(currl!=NULL) {
      if(currl->indl < lstdeepl->indl) {
        upsl = dynamic_cast<SoilLayer*>(currl);
        lwsl = dynamic_cast<SoilLayer*>(currl->nextl);
        combineTwoSoilLayersL2U(lwsl,upsl); //combine this layer and next layer
        upsl->indl = lwsl->indl;
        removeLayer(currl->nextl);
        goto COMBINEBEGIN;
      } else {
        break;
      }

      currl =currl->nextl;
    }

    lstdeepl = fstdeepl; //above always merge the lower layer into the
                         //'fstdeepl', so need to update 'lstdeepl'
    updateSoilHorizons(); //all 'deepl' are merged at this point, and
                          //info updated
    //Divide this one layer into up to pre-defined numbers of layers
    organic.DeepThickScheme(organic.deepthick); //here, 'Soil Horizons'
                                                // info has updated

    if(organic.deepnum==0) { //remove all deep layer(s) from the
                             //  double-linked structure
      currl = fstdeepl;

      while (currl!=NULL && currl->isHumic) {
        Layer * next = currl->nextl;
        removeLayer(currl); //Note: here acutally the double-linked
                            //        structure has changed
        currl = next;
      }

      fstdeepl = NULL;
      lstdeepl = NULL;
    } else if(organic.deepnum ==1) {
      //only change the properties of layer
      fstdeepl->dz = organic.deepdz[0];
      SoilLayer* deepsl = dynamic_cast<SoilLayer*>(fstdeepl);
      deepsl->derivePhysicalProperty();
    } else {
      //split ONE combined deep layer according to the new division scheme
      //  in 'organic.initDeepThickness(thick)'
      OrganicLayer* plnew;

      for (int i=organic.deepnum-1; i>0; i--) {
        plnew = new OrganicLayer(organic.deepdz[i], 2, chtlu);
        SoilLayer* deepsl = dynamic_cast<SoilLayer*>(fstdeepl);
        // split 'plnew' from bottom of 'deepsl'
        splitOneSoilLayer(deepsl, plnew, 0., organic.deepdz[i]);
        insertAfter(plnew, deepsl);
      }
    }

    /////////// THERE NO Existing deep amorphous OS layer //////////////////////
  } else {
    SoilLayer *lfibl;

    if (lstshlwl !=NULL) {
      lfibl = dynamic_cast<SoilLayer*>(lstshlwl);
    } else {
      return;
    }

    double deepcmin = carbonFromThickness(MINDEPTHICK, soildimpar.coefdeepa, soildimpar.coefdeepb);

    //assuming those SOMC available for forming a deep humific OS layer
    double somc = 0.5*lfibl->soma+lfibl->sompr+lfibl->somcr;

    if (somc>=deepcmin) {
      organic.DeepThickScheme(MINDEPTHICK);
      OrganicLayer* plnew = new OrganicLayer(organic.deepdz[0], 2, chtlu);
      double frac = plnew->dz/lfibl->dz;
      // assign properties for the new-created 'deep' layer
      plnew->ice = lfibl->ice*frac;
      plnew->liq = lfibl->liq*frac;
      plnew->tem = lfibl->tem;
      plnew->frozen = lfibl->frozen;
      plnew->rawc  = 0.;
      plnew->soma  = 0.5*lfibl->soma;
      plnew->sompr = lfibl->sompr;
      plnew->somcr = lfibl->somcr;
      plnew->orgn  = lfibl->orgn;
      plnew->avln  = lfibl->avln;
      plnew->derivePhysicalProperty();
      insertAfter(plnew, lfibl);
      // adjust properties for the above fibrous layer
      organic.shlwchanged =true;
      lfibl->ice *= (1.-frac);
      lfibl->liq *= (1.-frac);
      lfibl->soma *=0.5;
      lfibl->sompr = 0.;
      lfibl->somcr = 0.;
      lfibl->orgn  = 0.;
      lfibl->avln  = 0.;
      lfibl->derivePhysicalProperty();
      updateSoilHorizons();
    }
  }

  resortGroundLayers();
};

// Note: here properties updated when do re-structuring double-linked layer
//        matrix the 'usl' is the original layer, which will be divided into a
//        new 'usl' (upper) and a new 'lsl' (lower)
// 'updeptop' - the 'usl' top depth of same soil horizon type (needed for
//   estimating C content from depth)
// 'lsldz' - the new 'lsl' thickness
void Ground::splitOneSoilLayer(SoilLayer*usl, SoilLayer* lsl,
                               const double & updeptop, const double &lsldz) {
  double lslfrac = lsldz/usl->dz;
  // dividing depth/thickness
  usl->dz -= lsldz; // the upper one will not change its depth from the surface
  lsl->z   = usl->z + usl->dz;
  lsl->dz  = lsldz;
  // update layer physical properties ('dz' and 'poro' dependent only)
  lsl->derivePhysicalProperty();
  usl->derivePhysicalProperty();

  //update layer temperature first, because it's needed for determine
  //  frozen status below
  if(usl->nextl==NULL) {
    lsl->tem = usl->tem;
  } else {
    double ultem = usl->tem;
    double ulz = usl->z+0.5*(usl->dz+lsl->dz);//the original 'usl' mid-node
                                              //  depth (here, usl->dz
                                              //  update above)
    double nxltem = usl->nextl->tem;
    double nxlz = usl->nextl->z+0.5*usl->nextl->dz;
    double gradient = (ultem - nxltem)/(ulz -nxlz); //linearly interpolated
    double slz = lsl->z+0.5*lsl->dz;
    lsl->tem = (slz-nxlz) * gradient + nxltem;
    ulz = usl->z+0.5*usl->dz;
    if(usl->prevl == NULL){ //if no prevl, use same gradient
      usl->tem = (ulz-nxlz) * gradient + nxltem;
    } else { //otherwise incorporate prevl temp
      double pltem = usl->prevl->tem;
      double plz = usl->prevl->z + 0.5 * usl->prevl->dz;
      gradient = (pltem - lsl->tem) / (plz - slz);
      usl->tem = (ulz-slz) * gradient + lsl->tem;
    }
  }

  // after division, needs to update 'usl' and 'lsl'- 'frozen/frozenfrac'
  //   status based on 'fronts' if given
  getLayerFrozenstatusByFronts(lsl);
  getLayerFrozenstatusByFronts(usl);

  // update layer water contents, based on 'frozenfrac' update above
  // essentially in a layer if front exists, 'ice' and 'liq' are located
  //   separately by front
  double totwat = usl->ice+usl->liq;
  double totice = usl->ice;
  double totliq = usl->liq;
  double f1 = usl->frozenfrac;
  double f2 = lsl->frozenfrac;
  double ice1, ice2;

  //Values for calculating redistribution of ice
  double upper_frozen_dz = f1*usl->dz;
  double lower_frozen_dz = f2*lsl->dz;
  double total_frozen_dz = upper_frozen_dz + lower_frozen_dz;

  //If either are partially or completely frozen based on frozen
  // fraction, not state
  if(f1>0.0 or f2>0.0){
    double lower_frozen_ratio = lower_frozen_dz/total_frozen_dz;
    ice2 = lower_frozen_ratio * totice;
    ice1 = totice - ice2;
  }
  else{ //Both layers are completely thawed
    if(totice > 0.0){
      BOOST_LOG_SEV(glg, warn) << "Positive ice content when both layers are unfrozen";
    }
    ice2 = 0;
    ice1 = 0;
  }

  usl->ice = fmin(ice1, usl->maxice);
  lsl->ice = fmin(ice2, lsl->maxice);

  //Redistributing liquid water
  double liq1, liq2;
  double unf1 = 1.0 - usl->frozenfrac;
  double unf2 = 1.0 - lsl->frozenfrac;

  double upper_unfrozen_dz = unf1 * usl->dz;
  double lower_unfrozen_dz = unf2 * lsl->dz;
  double total_unfrozen_dz = upper_unfrozen_dz + lower_unfrozen_dz;

  //if either are partially or completely unfrozen
  if(unf1>0.0 or unf2>0.0){
    double lower_unfrozen_ratio = lower_unfrozen_dz/total_unfrozen_dz;
    liq2 = lower_unfrozen_ratio * totliq;
    liq1 = totliq - liq2;
  }
  else{ //if both are completely frozen
    liq2 = 0;
    liq1 = totliq; //Should be 0, but setting to totliq in case
  }

  usl->liq = fmin(liq1, usl->maxliq);
  lsl->liq = fmin(liq2, lsl->maxliq);

  //update C in new 'lsl' and 'usl' - note: at this point, 'usl' C must be
  //  not updated
  //first, assign 'lsl' C with original 'usl', then update it using actual
  //  thickness and depth
  lsl->rawc = usl->rawc;
  lsl->soma = usl->soma;
  lsl->sompr = usl->sompr;
  lsl->somcr = usl->somcr;
  lsl->orgn = usl->orgn;
  lsl->avln = usl->avln;

  if (usl->isOrganic) {
    double pldtop = updeptop + usl->dz;   //usl->dz has been updated above
    double pldbot = pldtop + lsl->dz;
    getOslCarbon5Thickness(lsl, pldtop, pldbot);
  } else {
    lsl->rawc *= lslfrac;
    lsl->soma *= lslfrac;
    lsl->sompr *= lslfrac;
    lsl->somcr *= lslfrac;
    lsl->orgn *= lslfrac;
    lsl->avln *= lslfrac;
  }

  // then update C for new 'usl'
  usl->rawc -= lsl->rawc;
  usl->soma -= lsl->soma;
  usl->sompr -= lsl->sompr;
  usl->somcr -= lsl->somcr;
  usl->orgn -= lsl->orgn;
  usl->avln -= lsl->avln;
};

// Note: here properties updated when do combining two double-linked layers
// from upper 'usl' to lower layer 'lsl'
// after calling this, 'usl' must be removed

void Ground::combineTwoSoilLayersU2L(SoilLayer* usl, SoilLayer* lsl) {
  // update water content
  lsl->z    = usl->z;   //note - z is the top of a layer from ground surface
  lsl->dz  += usl->dz;
  lsl->liq += usl->liq;
  lsl->ice += usl->ice;
  // update temperature
  double upfrac = usl->dz/lsl->dz;
  lsl->tem *= (1.-upfrac);
  lsl->tem += usl->tem*upfrac;
  // update C content:
  lsl->rawc +=usl->rawc;
  lsl->soma +=usl->soma;
  lsl->sompr+=usl->sompr;
  lsl->somcr+=usl->somcr;
  lsl->orgn +=usl->orgn;
  lsl->avln +=usl->avln;
  // after combination, needs to update 'lsl'- 'frozen' status based on
  //   'fronts' if given
  getLayerFrozenstatusByFronts(lsl);
  checkFrontsValidity();
  lsl->derivePhysicalProperty();
};

void Ground::combineTwoSoilLayersL2U(SoilLayer* lsl, SoilLayer* usl) {
  // update water content
  usl->dz  +=lsl->dz;
  usl->liq +=lsl->liq;
  usl->ice +=lsl->ice;
  // update temperature
  double lsfrac = lsl->dz/usl->dz;
  usl->tem *= (1.-lsfrac);
  usl->tem += lsl->tem*lsfrac;
  // update C content:
  usl->rawc +=lsl->rawc;
  usl->soma +=lsl->soma;
  usl->sompr+=lsl->sompr;
  usl->somcr+=lsl->somcr;
  usl->orgn +=lsl->orgn;
  usl->avln =+lsl->avln;
  // after combination, needs to update 'usl'- 'frozen' status based on
  //   'fronts' if given
  getLayerFrozenstatusByFronts(usl);
  usl->derivePhysicalProperty();
};

// The following module will re-constructure double-linked layer matrix based
//   on C content change after fire
// So, it must be called after 'bd' layerd C content was assigned to the
//   orginal double-linked layer matrix
double Ground::adjustSoilAfterburn() {
  BOOST_LOG_SEV(glg, debug) << "Beginning of adjustSoilAfterburn(..)" << this->layer_report_string();

  double bdepthadj = 0.; // this is used to check if thickness change here
                         // would be modifying burn thickness in 'WildFire.cpp'

  // and 'frontz'
  Layer *currl  = toplayer;

  // if there is snow, remove it
  while(currl!=NULL) {
    if(currl->isSnow) {
      removeLayer(currl);
    } else {
      break;
    }
    //Tucker Feb 2015: moved this statement from if(currl->isSnow){}
    //for consistency with DOSTEM ground.cpp line 1641.
    currl = toplayer; //then the new toplayer is currl->next
                      //  (otherwise, bug here)
  }

  // remove all moss/organic layers, if C is zero, after fire
  currl = fstsoill;

  while (currl!=NULL) {
    if(currl->isMoss || currl->isOrganic) {
      double tsomc = currl->rawc + currl->soma + currl->sompr + currl->somcr;

      if(tsomc <= 0.0) {
        bdepthadj += currl->dz; //adding the removed layer thickness to
                                //  that 'err' counting
        //need to adjust 'freezing/thawing front depth' due to top
        //  layer removal below
        adjustFrontsAfterThickchange(0, -currl->dz);
        removeLayer(currl);
        currl = toplayer; //then the new toplayer is currl->nextl
                          //  (otherwise, bug here)
      } else {
        break;
      }
    } else {
      break;
    }
  }

  //Note: at this point, the toplayer(s) may have been moved up due to snow/moss
  //        horizons removal above, so need resort the double-linked structure
  resortGroundLayers();
  updateSoilHorizons();

  //The left fibrous organic layer(s) after fire should all be turned
  //  into humified organic layer
  currl = toplayer;

  while (currl!=NULL) {
    if(currl->isFibric) {
      OrganicLayer * pl = dynamic_cast<OrganicLayer*>(currl);
      pl->humify(chtlu); //here only update 'physical' properties, but not states
                    //  (will do below when adjusting 'dz'
      pl->somcr += pl->rawc; //assuming all 'raw material' converted into
                             //  'chemically-resistant' SOM
      pl->rawc = 0.;
    } else if (currl->isHumic || currl->isMineral || currl->isRock) {
      break;
    }

    currl = currl->nextl;
  }

  //re-do thickness of deep organic layers, because of changing of its
  //  original type from fibrous or partially burned
  currl = toplayer;
  double deepctop = 0.; //cumulative C for deep OSL horizon at the top of a
                        //  layer, initialzed as 0
  double deepcbot;

  while(currl!=NULL) {
    if(currl->isHumic) {
      double olddz = currl->dz;
      OrganicLayer *pl=dynamic_cast<OrganicLayer*>(currl);
      double plcarbon = pl->rawc+pl->soma+pl->sompr+pl->somcr;

      if (plcarbon > 0.) { //this may not be needed, if we do things carefully
                           //  above. But just in case
        // update 'dz' for 'pl' from its C content
        deepcbot = deepctop+pl->rawc+pl->soma+pl->sompr+pl->somcr;
        getOslThickness5Carbon(pl, deepctop, deepcbot);
        deepctop = deepcbot;
        bdepthadj += (olddz - pl->dz); //adjuting the difference to that
                                       //  'err' counting
      }
    } else if (currl->isMineral || currl->isRock) {
      break;
    }

    currl =currl->nextl;
  }

  resortGroundLayers();
  updateSoilHorizons();
  //finally, checking if further needed to divide/combine double-linked layer
  //  matrix, in case that some layers may be getting too thick or too thin due
  //  to layer adjustion above. Then, re-do layer division or combination is
  //  necessary for better thermal/hydrological simulation
  redivideSoilLayers();
  // for checking the adjusted burned thickness
  return bdepthadj;
};

//if OS thickness changes, the following needs to be called
void Ground::adjustFrontsAfterThickchange(const double &depth,
                                          const double &thickadding) {
  int frntnum = frontsz.size();

  for(int i=0; i<frntnum; i++) {
    if (frontsz[i]>=depth) { // only need to adjust 'fronts' below 'depth'
      frontsz[i] += thickadding; //thickadding CAN be negative
    }
  }

  // checking if the 'front' may be removed, e.g., due to fire removal of
  //   top layers
  while (frontsz.size()>0 && frontsz[0]<=0.) {
    frontsz.pop_front();
    frontstype.pop_front(); // this will update the 'deque'
  }
};

//update the fraction of frozen portion (thickness), and frozen status for
//  ONE layer, if known 'fronts' dequeue given
//this is useful if re-do soil layer construction/division, but not change
//  the total thickness
void Ground::getLayerFrozenstatusByFronts(Layer * soill) {
  if (soill==NULL) {
    return;
  }
  int fntnum = frontsz.size();
  if (fntnum<=0) { // no fronts exist, use temp to assign frozen status
    if (soill->tem > 0.) {
      soill->frozen = -1;
      soill->frozenfrac = 0.;
    } else {
      soill->frozen = 1;
      soill->frozenfrac = 1.;
    }
    return;
  }
  else { // fronts exist somewhere in the soil column
    bool hasfront = false;
    for (int ii=0; ii<fntnum; ii++){ // check for fronts in this layer
      if(frontsz[ii] >= soill->z && frontsz[ii] <= soill->z + soill->dz){
        hasfront = true;
        break;
      }
    }
    if (!hasfront){ // no fronts in this layer
      for (int fntind=0; fntind<fntnum; fntind++){
        if (frontsz[fntind]<=soill->z) { // cycle through any fronts above layer; the lowest one will give the correct status
          soill->frozen = -frontstype[fntind];
          if (soill->frozen==1) {
            soill->frozenfrac = 1.0;
          } else {
            soill->frozenfrac = 0.0;
          }
        }
        if (frontsz[fntind]>soill->z+soill->dz) { // for any fronts below layer
          soill->frozen = frontstype[fntind];
          if (soill->frozen==1){
            soill->frozenfrac = 1.0;
          } else {
            soill->frozenfrac = 0.0;
          }
          break; // only check the highest front below the layer since others will give incorrect status
        }
      }
    }
    else { // one or more fronts are in this soil layer
      double fracfrozen = 0.;
      double dzabvfnt = 0.;
      for (int fntind=0; fntind<fntnum; fntind++){
        double fntz = frontsz[fntind];
        int fnttype = frontstype[fntind];
        if(fntz > soill->z && fntz <= (soill->z + soill->dz)){ // if this front in this layer
          soill->frozen = 0;
          double dzfnt = fntz-soill->z; //the distance of the 'fntind'th front from the soill->z
          if (fnttype==1) { // freezing front: from this front up to the neighboring
                            //  previous front IS frozen portion
            fracfrozen += (dzfnt - dzabvfnt);
          } else if (fnttype==-1  //thawing front and
                     && ( (fntind==fntnum-1) // it's the last front in the deque
                       || (fntind<fntnum-1 // or it's not the last front in the deque but
                         && frontsz[fntind+1]>(soill->z+soill->dz)))) { // the following front isn't in this layer
              fracfrozen += soill->dz - dzfnt;
          }
          dzabvfnt = dzfnt; //update the upper front 'dz' for following front
          soill->frozenfrac = fracfrozen/soill->dz; // update soill frozenfrac
        }
      } // end loop through fronts
    } // end else fronts exist in this layer
  } // end else fronts exist in column
}


void Ground::setDrainL() {

  draindepth = 0.;
  drainl = NULL;

  if(ststate == 0 && fstsoill->frozen < 1){
    //check for existence of fronts
    if(fstfntl != NULL && !fstfntl->isMoss){
      drainl = fstfntl;
      if(frnttype[0] == 1){//top front is a freezing front
        draindepth = fstfntl->z; //draindepth is top of layer
      }
      else {//top front is a thawing front
        draindepth = frntz[0]; //draindepth is at front interface
        drainl = fstfntl;
      }
    }
  }
  else if(ststate == -1){
    //soil stack is completely thawed, so
    //set drain depth to the bottom of the soil stack
    draindepth = lstsoill->z + lstsoill->dz;
    drainl = lstsoill;
  }

};

///save 'soil' information in double-linked layer into struct in 'cd'
void Ground::retrieveSoilDimension(soistate_dim * soildim) {
  Layer * curr;
  curr= toplayer;
  //initializing
  soildim->mossthick =0;
  soildim->shlwthick =0;
  soildim->deepthick =0;
  soildim->mineathick =0;
  soildim->minebthick =0;
  soildim->minecthick =0;
  soildim->totthick  =0;
  soildim->mossnum =0;
  soildim->shlwnum =0;
  soildim->deepnum =0;
  soildim->minenum =0;
  soildim->numsl   =0;

  for(int il=0; il<MAX_SOI_LAY; il++) {
    soildim->age[il]  = MISSING_I;
    soildim->z[il]    = MISSING_D;
    soildim->dz[il]   = MISSING_D;
    soildim->type[il] = MISSING_I;
    soildim->por[il]  = MISSING_D;
  }

  int slind=0;
  int mlind=0;

  while(curr != NULL) {
    if(curr->isSoil) {
      soildim->age[slind] = (int)curr->age;
      soildim->dz[slind]  = curr->dz;
      soildim->z[slind]   = curr->z;
      soildim->por[slind] = curr->poro;

      if(curr->isMoss) {
        soildim->type[slind] = 0;
        soildim->mossthick += curr->dz;
        soildim->mossnum += 1;
      } else if(curr->isOrganic) {
        if(curr->isFibric) {
          soildim->type[slind] = 1;
          soildim->shlwthick += curr->dz;
          soildim->shlwnum += 1;
        } else if(curr->isHumic) {
          soildim->type[slind] = 2;
          soildim->deepthick += curr->dz;
          soildim->deepnum += 1;
        }
      } else if(curr->isMineral) {
        soildim->type[slind] = 3;
        soildim->minenum += 1;

        if (mlind>=0 && mlind<=MINEZONE[0]) {
          soildim->mineathick += curr->dz;
        }

        if (mlind>MINEZONE[0] && mlind<=MINEZONE[1]) {
          soildim->minebthick += curr->dz;
        }

        if (mlind>MINEZONE[1] && mlind<=MINEZONE[2]) {
          soildim->minecthick += curr->dz;
        }

        mlind++;
      }

      slind++;
    }

    curr= curr->nextl;
  }

  soildim->numsl = soildim->mossnum +
                   soildim->shlwnum +
                   soildim->deepnum +
                   soildim->minenum;

  soildim->totthick = soildim->mossthick +
                      soildim->shlwthick +
                      soildim->deepthick +
                      soildim->mineathick +
                      soildim->minebthick +
                      soildim->minecthick;
}

void Ground::updateWholeFrozenStatus() {
  if(fstfntl==NULL && lstfntl==NULL) {
    ststate = fstsoill->frozen;
  } else {
    ststate = 0; // partially frozen
  }

  checkFrontsValidity();
};


///////////////////////////////////////////////////////////////////////

// update OSL thickness for all organic horizons if C content known

void Ground::updateOslThickness5Carbon(Layer* fstsoil) {
  if(fstsoil->isMineral || fstsoil->isRock) {
    return;
  }

  double shlwcbot = 0.0;
  double shlwctop = 0.0;
  double deepcbot = 0.0;
  double deepctop = 0.0;
  double olddz = 0.0;
  Layer* currl=fstsoil;

  while(currl!=NULL) {
    if(currl->isSoil && (currl->isOrganic || currl->isMoss)) {
      SoilLayer* sl = dynamic_cast<SoilLayer*>(currl) ;
      olddz = sl->dz;

      if(sl->isHumic) {
        deepcbot = deepctop + sl->rawc + sl->soma + sl->sompr + sl->somcr;
        getOslThickness5Carbon(sl, deepctop, deepcbot);
        deepctop = deepcbot;
      } else if(sl->isFibric) {
        shlwcbot = shlwctop + sl->rawc + sl->soma + sl->sompr + sl->somcr;
        getOslThickness5Carbon(sl, shlwctop, shlwcbot);
        shlwctop = shlwcbot;
      } else if(sl->isMoss) {
        if ( sl->nextl->isMoss ) {
          // Do nothing.
          // The upper (living) moss layer has no SOC and so can't
          // have its thickness adjusted by SOC content...
          //
          // Maybe thickness of the upper moss layer should be determined by
          // the veg properties of the moss PFTs?
        }
        
      }

      // Later thickness ('dz') may have changed, so update the 'z'
      // (top of layer) for all layers.
      updateLayerZ();

    } else { // is soil layer, but not organic or moss (so mineral)
      break;
    }

    currl = currl->nextl;
  }

  //
  updateSoilHorizons();
  //
  checkFrontsValidity();
}


/** Convert from gC/m^2 to layer thickness (meters) based on Yi et al, 2009. 
 *
 * Throws std::runtime_error if thickness goes negative.
*/
double Ground::thicknessFromCarbon(const double carbon, const double coefA, const double coefB) {
  //assert ((coefB >= 1) && "Yi et al. 2009 says the b coefficient should be a fitted parameter constrained to >= 1!");
  //if (!(coefB >= 1)) BOOST_LOG_SEV(glg, warn) << "Yi et al. 2009 says the b coefficient should be a fitted parameter constrained to >= 1!";

  // T = (C/a)^(1/b)
  double T;
  T = pow( carbon/10000.0/coefA, 1/coefB); // convert gC/m^2 to gC/cm^2
  T = T / 100.0;                           // convert thickness from cm to m

  if( !(T >= 0) ) {
    BOOST_LOG_SEV(glg,fatal)<<"Negative layer thickness when calculating from carbon. T = "<<T;
    BOOST_LOG_SEV(glg,fatal)<<"Carbon: "<<carbon<<" CoefA: "<<coefA<<" CoefB: "<<coefB;
    BOOST_LOG_SEV(glg,fatal)<<"Forcing layer thickness to 0.0001";
    T = 0.0001;
  }

  return T;
}

/** Convert from layer thickness (meters) to gC/m^2 based on Yi et al, 2009. 
 * 
 * Throws std::runtime_error if C goes negative
*/
double Ground::carbonFromThickness(const double thickness, const double coefA, const double coefB) {
  //assert ((coefB >= 1) && "Yi et al. 2009 says the b coefficient should be a fitted parameter constrained to >= 1!");
  //if (!(coefB >= 1)) BOOST_LOG_SEV(glg, warn) << "Yi et al. 2009 says the b coefficient should be a fitted parameter constrained to >= 1!";

  // C = aT^b
  double C;
  C = coefA * pow(thickness*100.0, coefB); // convert from m to cm
  C = C * 10000.0;                         // convert from gC/cm^2 to gC/m^2

  if( !(C >= 0) ) {
    throw std::runtime_error("It doesn't make sense to have a negative amount of Carbon!");
  }

  return C;
}

// conversion from OSL C to thickness
// after a fire we have lost a bunch of C and need to re-compute
// the layer thickness based on the updated soil C (remaining after fire)
// this is not necessarirtly a linear relationship, hence the coefdeepa, coefdeepc, see shua yi 2009 paper...
void Ground::getOslThickness5Carbon(SoilLayer* sl, const double &plctop,
                                    const double &plcbot) {
  //NOTE: the OSL C - thickness relationship is for the whole same-type
  //        OSL horizon
  // the estimation here is for ONE layer only in the whole horizon
  // it means that C cannot be calculated using the layer thickness
  // but using the bottom depth of a layer from the top of the whole horizon
  double pltop = 0.;
  double plbot = 0.;
  double cumcarbon    = plcbot; //Cumulative C from the top of the whole horizon
  double prevcumcarbon= plctop; //Cumulative C until the layer top
  double orgsoil_dz_old = sl->dz;

  if(sl->isFibric) {

    pltop = thicknessFromCarbon(prevcumcarbon, soildimpar.coefshlwa, soildimpar.coefshlwb);
    plbot = thicknessFromCarbon(cumcarbon, soildimpar.coefshlwa, soildimpar.coefshlwb);

  } else if (sl->isHumic) {

    pltop = thicknessFromCarbon(prevcumcarbon, soildimpar.coefdeepa, soildimpar.coefdeepb);
    plbot = thicknessFromCarbon(cumcarbon, soildimpar.coefdeepa, soildimpar.coefdeepb);

  } else {
    return;
  }

  sl->dz=plbot-pltop;
  double orgsoil_dz_new = sl->dz;
  //need to adjust 'freezing/thawing front depth', if 'fronts'
  //  depth below 'sl->z'
  adjustFrontsAfterThickchange(sl->z, orgsoil_dz_new - orgsoil_dz_old);
  //'dz' dependent physical properties
  double oldporo = sl->poro;
  sl->derivePhysicalProperty(); //update soil physical property after
                                //  thickness change from C is done
  double f=fmin(1., sl->dz/orgsoil_dz_old); //so if layer shrinks, it will adjust
                                     //  water; otherwise, no change.
  double f2=fmin(1., sl->poro/oldporo);  //for whatever reason, if
                                         //  porosity changes
  f = fmin(f, f2);
  sl->liq *=fmax(0., f);
  sl->ice *=fmax(0., f);
  // above soil temperature and frozen status not modified
};

//conversion from OSL thickness to C content
//note - only for thickness changing, i.e. previous fraction of SOM C
//         pools must be known
void Ground::getOslCarbon5Thickness(SoilLayer* sl, const double &plztop,
                                    const double &plzbot) {
  // NOTE: the OSL C - thickness relationship is for the whole OSL horizon
  // the estimation here is for ONE layer only in the whole horizon
  // it means that C cannot be calculated using the layer thickness
  // but using the bottom depth of a layer from the top of the whole horizon
  double dbot = plzbot; //the bottom depth of a layer from the top
                        //  of the whole horizon
  double dtop = plztop;  // the top depth of the layer
  double cumcarbon    =0.;
  double prevcumcarbon=0.;

  if(sl->isFibric) {

    prevcumcarbon = carbonFromThickness(dtop, soildimpar.coefshlwa, soildimpar.coefshlwb);
    cumcarbon = carbonFromThickness(dbot, soildimpar.coefshlwa, soildimpar.coefshlwb);

  } else if (sl->isHumic) {

    prevcumcarbon = carbonFromThickness(dtop, soildimpar.coefdeepa, soildimpar.coefdeepb);
    cumcarbon = carbonFromThickness(dbot, soildimpar.coefdeepa, soildimpar.coefdeepb);

  } else {
    return;
  }

  // this is the 'old' total SOMC
  double oldtsomc = sl->rawc+sl->soma+sl->sompr+sl->somcr;

  double newtsomc = cumcarbon-prevcumcarbon;

  if(oldtsomc>0.) {
    //because thickness change, C pools need update
    sl->rawc  *= newtsomc/oldtsomc;

    sl->soma  *= newtsomc/oldtsomc;
    sl->sompr *= newtsomc/oldtsomc;
    sl->somcr *= newtsomc/oldtsomc;
  }
};

//////////////////////////////////////////////////////////////////////

//check the validity of fronts in soil column
void Ground::checkFrontsValidity() {
  
  // checking if the 'front' may be out of the top soil layer
  while (frontsz.size()>0 && frontsz[0]<=fstsoill->z) {
    frontsz.pop_front();
    frontstype.pop_front();    // this will update the 'deque'
  }

  // checking if the 'front' may be out of soil bottom
  while (frontsz.size()>0 && frontsz[frontsz.size()-1]>=(lstsoill->z+lstsoill->dz*0.9999)) {
    frontsz.pop_back();
    frontstype.pop_back();    // this will update the 'deque'
  }

  int frntnum = frontsz.size();

  for(int i=0; i<MAX_NUM_FNT; i++) {
    if (i<frntnum) {
      frntz[i] = frontsz[i];
      frnttype[i] = frontstype[i];

      if (i>0) {
        if (frnttype[i]==frnttype[i-1]) {
          BOOST_LOG_SEV(glg, warn) << "Adjacent fronts should be different! "
                                   << "Ground::checkFrontsValidity(..)";
        }
      }
    } else {
      frntz[i] = MISSING_D;
      frnttype[i] = MISSING_I;
    }
  }

  int fntind = 0;
  Layer*currl=fstsoill;

  while (currl!=NULL && fntind<frntnum) {
    if(currl->isSoil) {
      while (frontsz[fntind] > currl->z &&
             frontsz[fntind] <= (currl->z + currl->dz)) {

        if (currl->frozen != 0) {
          BOOST_LOG_SEV(glg, warn) << "Soil layer " << currl->indl
                                   << " with front shall have 0 for its frozen "
                                   << "state! Ground::checkFronts(..)";
        }

        fntind++;

        if (fntind>=frntnum) {
          break;
        }
      }
    }

    currl=currl->nextl;
  }
}

/** Check the validity of water contents in soil column. */
void Ground::checkWaterValidity() {
  BOOST_LOG_SEV(glg, debug) << "Checking water validity...";

  Layer* currl = this->toplayer;

  while (currl != NULL) {
    if (fabs(currl->ice) < 1.e-9) {
      currl->ice = 0.0;
    }

    if (fabs(currl->liq) < 1.e-9) {
      currl->liq = 0.0;
    }

    if (currl->ice < 0.0 || currl->liq < 0.0) {
      BOOST_LOG_SEV(glg, warn) << "Layer " << currl->indl
                              << " has negative ice or negative liquid water";
    }

    if (currl->frozen == 1) {
      if (currl->liq > 0.0) {
        BOOST_LOG_SEV(glg, warn) << "Layer " << currl->indl
                                << " is fully frozen but has liquid water";
      }

      // maybe from some mathematical round up or small disagreements btw density dz and melt/sublimation dz
      if ((currl->ice-currl->maxice) > 0.01) {
        if(currl->isSnow){
          BOOST_LOG_SEV(glg, warn) << "Snow layer " << currl->indl << " has "
                                   << currl->ice-currl->maxice << " kg/m2 too much ice";

        }
        else{
          BOOST_LOG_SEV(glg, warn) << "Layer " << currl->indl
                                   << " has too much ice";
        }
      }
    }

    if (currl->frozen == -1) {
      if (currl->ice > 0.0) {
        BOOST_LOG_SEV(glg, warn) << "Layer " << currl->indl
                                << " is fully thawed but has ice";
      }

      if ((currl->liq-currl->maxliq)>1.e-6 && currl->isSoil) {
        BOOST_LOG_SEV(glg, warn) << "Layer " << currl->indl << " (soil) "
                                << " has "<< currl->liq-currl->maxliq <<" mm too much liquid water";
      }
    }

    if (currl->frozen == 0 && currl->isSoil) {
      // adjust max. liq by ice occupied space
      double maxwat = fmax(0.0, currl->maxliq-currl->getVolIce()*currl->dz*DENLIQ);

      if ((currl->liq-maxwat) > 1.e-6) {
        BOOST_LOG_SEV(glg, warn) << "Layer " << currl->indl << " (soil) "
                                << " has "<< currl->liq-maxwat <<" mm too much liquid water";
      }

      // adjust max. ice by liq occupied space
      maxwat = currl->maxice-currl->getVolLiq()*currl->dz*DENICE;
      if ((currl->ice-maxwat) > 1.e-6) {
        BOOST_LOG_SEV(glg, warn) << "Layer " << currl->indl << " (soil) "
                                << "has too much ice";
      }
    }

    if(currl->isRock) {
      break;
    }

    currl = currl->nextl;

  }
}

void Ground::cleanSnowSoilLayers() {
  Layer* currl = toplayer;
  Layer* templ;

  while(currl!=NULL) {
    templ = currl->nextl;

    if (!currl->isRock) {
      removeLayer(currl);
    } else {
      break;
    }

    currl = templ ;
  }
}

void Ground::cleanAllLayers() {
  Layer* currl = toplayer;
  Layer* templ;

  while(currl!=NULL) {
    templ = currl->nextl;
    removeLayer(currl);
    currl = templ ;
  }
}

void Ground::cleanRockLayers() {
  Layer* currl = botlayer;
  Layer* templ;

  while(currl!=NULL) {
    templ = currl->nextl;
    removeLayer(currl);
    currl = templ ;
  }

}


//////////////////////////////////////////////////////////////////////

void Ground::setBgcData(BgcData *bdp){
  bd = bdp;
}

void Ground::setCohortLookup(CohortLookup* chtlup) {
  chtlu = chtlup;
};

