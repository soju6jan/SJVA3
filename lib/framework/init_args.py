# -*- coding: utf-8 -*-
#########################################################
import sys
args = None

def process_args():
    from sjva3 import process_args
    args = process_args()
    return args


if sys.argv[0] == 'sjva3.py':
    args = process_args()
else:
    args = None

