#include "Moss.h"

Moss::Moss() {}

Moss::~Moss() {}

void Moss::setThicknesses(int soiltype[], double soildz[],
                          const int &soilmaxnum) {
  this->num = 0;
  this->thick = 0.0;

  for(int i=0; i < soilmaxnum; i++) {
    if (soiltype[i]==0) {
      this->dz[num] = soildz[i];
      this->num++;
      this->thick += this->dz[i];
    } else {
      break;
    }
  }
}

