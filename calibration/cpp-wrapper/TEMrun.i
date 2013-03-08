/*
 * TEMrun.i
 *
 */

	%module TEMrun

//Translate operators
%rename(add) operator+;
%rename(elementAt) operator[];
%rename(getValue) operator();
%rename(subtract) operator-;
%rename(multiply) operator*;
%rename(divide) operator/;
%rename(equals) operator==;
%rename(unEquals) operator!=;
%rename(shiftLeft) operator<<;
%rename(shiftRight) operator>>;
%rename(lessThan) operator<;
%rename(lessThanOrEquals) operator<=;
%rename(greaterThan) operator>=;
%rename(greaterThanOrEquals) operator>=;
%rename(addOne) operator++;
%rename(subtractOne) operator--;
%rename(addAndAssign) operator+=;
%rename(subtractAndAssign) operator-=;
%rename(multiplyAndAssign) operator*=;
%rename(divideAndAssign) operator/=;
%rename(clone) operator=;

%include "typemaps.i"
%include "std_string.i"
%include "arrays_java.i"
%include "coredata.i"
%include "coreinc.i"
%include "corelookup.i"

			%{
				#include "../../src/runmodule/Cohort.h"
				#include "../../src/runmodule/Controller.h"
				#include "../../src/runmodule/Grid.h"
				#include "../../src/runmodule/ModelData.h"
				#include "../../src/runmodule/OutRetrive.h"
				#include "../../src/runmodule/Region.h"
				#include "../../src/runmodule/Timer.h"

				#include "../cpp-wrapper/TEMccjava.h"
								
			%}

			%include "../../src/runmodule/Cohort.h"
			%include "../../src/runmodule/Controller.h"
			%include "../../src/runmodule/Grid.h"
			%include "../../src/runmodule/ModelData.h"
			%include "../../src/runmodule/OutRetrive.h"
			%include "../../src/runmodule/Region.h"
			%include "../../src/runmodule/Timer.h"
			%include "../cpp-wrapper/TEMccjava.h"
			
