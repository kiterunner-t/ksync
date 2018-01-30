# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import hashlib
import uuid

import kconfig


_sys_encoding = kconfig.config.platform_encoding


# @Deprecated
to_local = lambda s: s.decode("utf-8").encode(_sys_encoding) \
    if _sys_encoding not in ("utf-8", "utf8") else lambda s: s


# @Deprecated
to_utf8 = lambda s: s.decode(_sys_encoding).encode("utf-8") \
    if _sys_encoding not in ("utf-8", "utf8") else lambda s: s


# @Deprecated
def list_to_utf8(ls):
    assert isinstance(ls, list)

    ls_utf8 = []
    for item in ls:
        assert not isinstance(item, tuple)

        t = item
        if isinstance(item, str):
            t = to_utf8(item)
        elif isinstance(item, list):
            t = list_to_utf8(item)
        elif isinstance(item, dict):
            t = map_to_utf8(item)

        ls_utf8.append(t)

    return ls_utf8


# @Deprecated
def map_to_utf8(h):
    assert isinstance(h, dict)

    h_utf8 = {}
    for k, v in h.iteritems():
        assert not isinstance(v, tuple)

        t = v
        if isinstance(v, str):
            t = to_utf8(v)
        elif isinstance(v, list):
            t = list_to_utf8(v)
        elif isinstance(v, dict):
            t = map_to_utf8(v)

        h_utf8[to_utf8(k)] = t

    return h_utf8


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

