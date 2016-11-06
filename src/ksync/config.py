# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import logging


class Platform(object):
    Nt = 0,
    Linux = 1


class Config(object):
    def __init__(self):
        self.platform = Platform.Nt
        self.local_path = r"F:\krt-data-sync"
        self.removable_disk_path = r"krt-data-sync"

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

