#! /usr/bin/env python
# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

try:
    import ksync.kconfig as kconfig
except:
    import os
    import sys
    parent_dir, bin_dir = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))
    module_dir = os.path.join(parent_dir, u"src")
    if os.path.exists(module_dir):
        sys.path.insert(0, module_dir)

import ksync.kconfig as kconfig
import ksync.klog as klog
import ksync.main as ksync_main


if __name__ == u"__main__":
    klog.info(u"Start ksync.")
    config = kconfig.Config()
    main = ksync_main.Main(config)
    main.run()

