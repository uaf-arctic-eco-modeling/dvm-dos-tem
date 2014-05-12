#!/bin/bash

#echo $@

src="sample-master-slave.cpp"
prog="sms"


mpic++ $src -o $prog
