# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import locale
import logging


class Platform(object):
    Nt = 0,
    Linux = 1


class Config(object):
    def __init__(self):
        _sys_encoding = locale.getdefaultlocale()[1].lower()
        to_local = lambda s: s.decode("utf-8").encode(_sys_encoding) \
            if _sys_encoding not in ("utf-8", "utf8") else lambda s: s

        self.platform = Platform.Nt
        self.platform_encoding = _sys_encoding

        self.local_path = to_local(r"F:\网盘")
        self.removable_disk_path = r"krt-data-sync"

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')


config = Config()

