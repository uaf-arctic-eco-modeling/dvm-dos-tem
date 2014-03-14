/*
 * coreinc.i
 *
 */

	%module coreinc

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

			%{
				#include "../../src/inc/cohortconst.h"
				#include "../../src/inc/layerconst.h"
				#include "../../src/inc/parameters.h"
				#include "../../src/inc/temconst.h"
				#include "../../src/inc/timeconst.h"

				#include "../../src/inc/errorcode.h"

				#include "../../src/inc/states.h"
				#include "../../src/inc/diagnostics.h"
				#include "../../src/inc/fluxes.h"

			%}

			%include "../../src/inc/cohortconst.h"
			%include "../../src/inc/layerconst.h"
			%include "../../src/inc/parameters.h"
			%include "../../src/inc/temconst.h"
			%include "../../src/inc/timeconst.h"

			%include "../../src/inc/errorcode.h"

			%include "../../src/inc/states.h"
			%include "../../src/inc/diagnostics.h"
			%include "../../src/inc/fluxes.h"
			