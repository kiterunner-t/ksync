# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import hashlib
import uuid


def file_md5(file):
    assert isinstance(file, (str, unicode))

    m = hashlib.md5()

    with open(file, "rb") as f:
        buf = f.read(4096)
        m.update(buf)

    return m.hexdigest()


def str_md5(s):
    assert isinstance(s, str)
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()


# http://www.cnblogs.com/dkblog/archive/2011/10/10/2205200.html
def get_uuid():
    return str_md5(str(uuid.uuid1()))

