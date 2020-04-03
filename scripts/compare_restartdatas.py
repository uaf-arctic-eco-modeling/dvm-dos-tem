#!/usr/bin/env python


eq_f = open('sp_end_rd.txt')
sp_f = open('beg_tr_rd.txt')

#eq_line = eq_f.readline()

for eq_line in eq_f:
  sp_line = sp_f.readline()
  eq_loc = eq_line.find(': ')
  sp_loc = sp_line.find(': ')

  if eq_loc:
    eq_value = eq_line[eq_loc+2:]
    sp_value = sp_line[sp_loc+2:]

    if eq_value != sp_value:
      print("Unequal: " + eq_value + " " + sp_value)
    #print eq_value
    #print sp_value

