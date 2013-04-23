/*! double linked list for snow and soil column */

#ifndef DOUBLELINKEDLIST_H_
#define DOUBLELINKEDLIST_H_

#include "layer/Layer.h"

#include <string>
#include <iostream>
using namespace std;

class DoubleLinkedList {
	public:
		DoubleLinkedList();

		/*! layer on the ground top, could be snow layer, moss layer , peat
		 * layer, or mineral layer, stored in front of list */
		Layer* toplayer;
		/*! layer at bottom of list */
		Layer* botlayer;
		
	protected:
		void insertFront(Layer *l);             
		void insertBack(Layer *l);
		void removeFront();
		void removeBack();
		void insertBefore(Layer *l,Layer *ll);
		void insertAfter(Layer *l,Layer *ll);
		void removeBefore(Layer *l);
		void removeAfter(Layer *l);
		void removeLayer(Layer *l);
};

#endif /*DOUBLELINKEDLIST_H_*/
