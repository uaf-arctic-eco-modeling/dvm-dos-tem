#ifndef SOILPARENT_ENV_H_
#define SOILPARENT_ENV_H_

#include "EnvData.h"
#include "RestartData.h"

#include "Ground.h"

class SoilParent_Env {
public:
  SoilParent_Env();

  void initializeState();
  void set_state_from_restartdata(const RestartData & rdata);

  void retrieveDailyTM(Layer* lstsoill);

  void  setEnvData(EnvData* ed);
  void  setGround(Ground* ground);

private:
  Ground *ground;
  EnvData *ed;

};

#endif /*SOILPARENT_ENV_H_*/
