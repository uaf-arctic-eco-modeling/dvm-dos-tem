/*! \file
 *
 */
#ifndef SOILLAYER_H_
#define SOILLAYER_H_
#include "Layer.h"

#include <math.h>
#include <cmath>
#include <memory>
using namespace std;

class SoilLayer:public Layer {
public:

  SoilLayer();
  virtual ~SoilLayer();

  virtual double getFrzThermCond();//get frozen layer thermal conductivity
  virtual double getUnfThermCond();//get unfrozen layer thermal conductivity
  virtual double getMixThermCond(); // get mixed layer thermal conductivity
  virtual double getFrzVolHeatCapa();//get frozen layer specific heat capcity
  virtual double getUnfVolHeatCapa();//get unfrozen layer specific heat capacity
  virtual double getMixVolHeatCapa(); //Yuan: all soil components

  virtual double getLatentHeatContent(); // LHC following Hinzman et al. 1998
  virtual double getDeltaLatentHeatContentDeltaT(); // dLHC/dT Hinzman et al. 1998

  double getAlbedoVis(); // get albedo of visible radiation
  double getAlbedoNir();// get albedo of Nir radiation

  void derivePhysicalProperty();

  double getMatricPotential();
  double getHydraulicCond();

};
#endif /*SOILLAYER_H_*/
