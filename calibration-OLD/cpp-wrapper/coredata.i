/*
 * coredata.i
 *
 */

	%module coredata

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
				#include "../../src/data/BgcData.h"
				#include "../../src/data/CohortData.h"
				#include "../../src/data/EnvData.h"
				#include "../../src/data/FirData.h"
				#include "../../src/data/GridData.h"
				#include "../../src/data/RegionData.h"
				#include "../../src/data/RestartData.h"
				#include "../../src/data/OutDataRegn.h"
			%}

			%include "../../src/data/BgcData.h"
			%include "../../src/data/CohortData.h"
			%include "../../src/data/EnvData.h"
			%include "../../src/data/FirData.h"
			%include "../../src/data/GridData.h"
			%include "../../src/data/RegionData.h"
			%include "../../src/data/RestartData.h"
			%include "../../src/data/OutDataRegn.h"
			
