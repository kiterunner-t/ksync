#! /usr/bin/env python
# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import sys
reload(sys)

import locale
sys.setdefaultencoding(locale.getdefaultlocale()[1])

import os
parent_dir, bin_dir = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))
module_dir = os.path.join(parent_dir, "src")
if os.path.exists(module_dir):
    sys.path.insert(0, module_dir)

import ksync.kconfig as kconfig
import ksync.klog as klog
import ksync.main as ksync_main


if __name__ == "__main__":
    klog.info("Start ksync.")
    config = kconfig.Config()
    main = ksync_main.Main(config)
    main.run()

