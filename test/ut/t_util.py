#! /usr/bin/env python
# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import os
import sys


current_path = os.path.split(os.path.realpath(__file__))[0]
lib_path = os.path.join(current_path, "..", "..", "src")
sys.path.append(lib_path)

