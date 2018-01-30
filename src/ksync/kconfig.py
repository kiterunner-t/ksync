# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import locale
import logging


class Platform(object):
    Nt = 0,
    Linux = 1,
    Mac = 2


class Config(object):
    def __init__(self):
        self.platform = Platform.Nt
        self.platform_encoding = locale.getdefaultlocale()[1].lower()

        self.local_path = ur"F:\网盘"
        self.removable_disk_path = ur"krt-data-sync"

        logging.basicConfig(level=logging.INFO,
                            format=u'%(asctime)s - %(message)s',
                            datefmt=u'%Y-%m-%d %H:%M:%S')


config = Config()

