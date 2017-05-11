/*! \file
 * Bug fixed
 * 1) in insertBefore, need to put the curl->prevl->nextl = l, if curl->prevl
 *      is not null
*/

#include "../TEMLogger.h"
#include "DoubleLinkedList.h"

extern src::severity_logger< severity_level > glg;

DoubleLinkedList::DoubleLinkedList() {
  toplayer = NULL;
  botlayer = NULL;
};

/*! insert a layer at the end of list */
void DoubleLinkedList::insertBack (Layer * l) {
  BOOST_LOG_SEV(glg, debug) << "DLL::insertBack()  <== Insert Layer at BOTTOM of column (will call insertFront() or insertAfter()).";
  if(this->botlayer==NULL) {
    insertFront(l);
  } else  {
    insertAfter(l,this->botlayer);
  }
};

/*! insert a layer before the front layer */
void DoubleLinkedList::insertFront (Layer * l) {
  BOOST_LOG_SEV(glg, debug) << "DLL::insertFront()  <== Insert Layer at TOP of column (may call insertBefore()).";
  if(this->toplayer==NULL) {
    this->toplayer =l;
    this->botlayer =l;
    l->prevl=NULL;
    l->nextl=NULL;
  } else {
    insertBefore(l, this->toplayer );
  }
}

/*! insert a layer before the specified layer */
void DoubleLinkedList::insertBefore(Layer *l, Layer *curl) {
  BOOST_LOG_SEV(glg, debug) << "DLL::insertBefore() <== ? Insert Layer ABOVE in column?";
  l->prevl = curl->prevl;
  l->nextl = curl;

  if(curl->prevl==NULL) {
    this->toplayer=l;
  } else {
    curl->prevl->nextl = l;
  }

  curl->prevl=l;
}

/*! insert a layer after the specified layer */
void DoubleLinkedList::insertAfter(Layer* l, Layer *curl) {
  BOOST_LOG_SEV(glg, debug) << "DLL::insertAfter()  <== ? Insert Layer BELOW in column?";
  Layer* tempnext= curl->nextl;
  l->nextl = curl->nextl;
  l->prevl = curl;

  if(curl->nextl==NULL) {
    this->botlayer =l;
  } else {
    tempnext->prevl= l;
  }

  curl->nextl=l;
}

/*! remove a layer from the front */
void DoubleLinkedList::removeFront () {
  BOOST_LOG_SEV(glg, debug) << "DLL::removeFront()  <== Delete TOP Layer in column (calls removeLayer())";
  removeLayer(this->toplayer);
}

/*! remove a layer from the back */
void DoubleLinkedList::removeBack () {
  BOOST_LOG_SEV(glg, debug) << "DLL::removeBack()  <== Delete BOTTOM Layer in column (calls removeLayer())";
  removeLayer(this->botlayer);
}

/*! remove a layer before a specified layer */
void DoubleLinkedList::removeBefore(Layer *curl) {

  BOOST_LOG_SEV(glg, debug) << "DLL::removeBefore()  <== ? Remove Layer ABOVE or BELOW?? (may call removeLayer())";

  if(curl->prevl==this->toplayer) {
    this->toplayer=curl;
    this->toplayer->prevl=NULL;
    delete curl;
  } else {
    removeLayer(curl->prevl);
  }
}

/*! remove a layer after a specified layer */
void DoubleLinkedList::removeAfter(Layer * curl ) {
  BOOST_LOG_SEV(glg, debug) << "DLL::removeAfter()  <== ? Remove Layer ABOVE or BELOW?? (may call removeLayer())";
  if(curl->nextl==this->botlayer) {
    this->botlayer=curl;
    this->botlayer->nextl=NULL;
    delete curl;
  } else {
    removeLayer(curl->nextl);
  }
}

/*! remove a layer */
void DoubleLinkedList::removeLayer(Layer * curl) {

  BOOST_LOG_SEV(glg, debug) << "DLL::removeLayer()  <== Delete Layer from the column, re-shuffles top/bottom accordingly.";

  if(curl==this->toplayer) {
    if(this->toplayer->nextl!=NULL) {
      this->toplayer=curl->nextl;
      this->toplayer->prevl =NULL;
      delete curl;
    }
  } else if (curl==this->botlayer) {
    if(this->botlayer->prevl !=NULL) {
      this->botlayer=curl->prevl;
      this->botlayer->nextl =NULL;
      delete curl;
    }
  } else  {
    curl->prevl->nextl=curl->nextl;
    curl->nextl->prevl=curl->prevl;
    curl->prevl =NULL;
    curl->nextl =NULL;
    delete curl;
  }

  curl=NULL;
}

