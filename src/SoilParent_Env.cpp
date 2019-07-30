#include "../include/SoilParent_Env.h"

SoilParent_Env::SoilParent_Env() {
}

void SoilParent_Env::initializeState() {
  Layer* currl = ground->botlayer;
  int permf =1;

  while(currl!=NULL) {
    if(currl->isRock) {
      currl->liq =0.;
      currl->ice=0.;

      if(permf==0) {
        currl->tem=1;
        currl->ch4 = 0.076;
      } else if(permf==1) {
        currl->tem=-1;
        currl->ch4 = 0.076;
      }
    } else {
      break;
    }

    currl = currl->prevl;
  }
};

void SoilParent_Env::set_state_from_restartdata(const RestartData & rdata) {
  double TSrock[MAX_ROC_LAY];

  for (int i=0; i<MAX_ROC_LAY; i++) {
    TSrock[i] = rdata.TSrock[i];
  }

  Layer* currl = ground->lstminel;
  int rcind =-1;

  while(currl!=NULL) {
    if(currl->isRock) {
      rcind ++;
      currl->tem = TSrock[rcind];
      currl->liq =0;
      currl->ice =0;
      currl->age =0;
      currl->poro=0;
    }

    currl = currl->nextl;
  }
};

void SoilParent_Env::retrieveDailyTM(Layer* lstsoill) {
  Layer *currl = lstsoill->nextl;
  double trock = lstsoill->tem;
  int rcind = -1;

  while (currl!=NULL) {
    if (currl->isRock) {
      rcind++;
      ed->d_sois.trock[rcind] = trock;
    }

    currl = currl->nextl;
  }
}

void SoilParent_Env::setEnvData(EnvData *edp) {
  ed = edp;
}

void SoilParent_Env::setGround(Ground *groundp) {
  ground = groundp;
}

