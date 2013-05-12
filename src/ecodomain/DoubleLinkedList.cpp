/*! \file
 * Bug fixed 
 * 1) in insertBefore, need to put the curl->prevl->nextl = l, if curl->prevl is not null
*/

#include "DoubleLinkedList.h"

DoubleLinkedList::DoubleLinkedList(){
 	toplayer = NULL;
 	botlayer = NULL;
};

 /*! insert a layer at the end of list */ 
void DoubleLinkedList::insertBack (Layer * l){          
	if(this->botlayer==NULL){
		//std::cout<<"insert at back";
		insertFront(l);
	} else	{
		//std::cout<<"insert at back";
		insertAfter(l,this->botlayer);
	}
};
 
 /*! insert a layer before the front layer */
void DoubleLinkedList::insertFront (Layer * l){
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

	l->prevl = curl->prevl;
	l->nextl = curl;

	if(curl->prevl==NULL){
		this->toplayer=l;
	}else{
		 curl->prevl->nextl = l;	
	}

	curl->prevl=l;

}
	
/*! insert a layer after the specified layer */
void DoubleLinkedList::insertAfter(Layer* l, Layer *curl){
    Layer* tempnext= curl->nextl;
        
	l->nextl = curl->nextl;
	l->prevl = curl;
		
	if(curl->nextl==NULL){
		this->botlayer =l;
	}else{
		tempnext->prevl= l;
	}
			
	curl->nextl=l;
}

/*! remove a layer from the front */
void DoubleLinkedList::removeFront (){
	removeLayer(this->toplayer);
}

/*! remove a layer from the back */
void DoubleLinkedList::removeBack (){
	removeLayer(this->botlayer);
}

/*! remove a layer before a specified layer */
void DoubleLinkedList::removeBefore(Layer *curl) {

	if(curl->prevl==this->toplayer){
		this->toplayer=curl;
		this->toplayer->prevl=NULL;
		delete curl;
	}else{
        removeLayer(curl->prevl);
	}
}

/*! remove a layer after a specified layer */ 
void DoubleLinkedList::removeAfter(Layer * curl ){
	if(curl->nextl==this->botlayer) {
		this->botlayer=curl;
		this->botlayer->nextl=NULL;
		delete curl;
	}else{
		removeLayer(curl->nextl);
	}
}

/*! remove a layer */
void DoubleLinkedList::removeLayer(Layer * curl) {
	if(curl==this->toplayer){
		if(this->toplayer->nextl!=NULL){
			this->toplayer=curl->nextl;
			this->toplayer->prevl =NULL;

			delete curl;
		}
		
	}else if (curl==this->botlayer){
		if(this->botlayer->prevl !=NULL){
			this->botlayer=curl->prevl;
			this->botlayer->nextl =NULL;
			delete curl;
		}
	} else	{
		curl->prevl->nextl=curl->nextl;
		curl->nextl->prevl=curl->prevl;
		curl->prevl =NULL;
		curl->nextl =NULL;
	    delete curl;
	}
	
	curl=NULL;
	
}

