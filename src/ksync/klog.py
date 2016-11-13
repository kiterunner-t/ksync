# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import logging

import kutil


def _convert(args):
    args_utf8 = []
    for arg in args:
        if isinstance(arg, str):
            args_utf8.append(kutil.to_utf8(arg))
        else:
            args_utf8.append(arg)

    return args_utf8


def debug(msg, *args):
    l = _convert(list(args))
    logging.debug(msg, *l)


def info(msg, *args):
    l = _convert(list(args))
    logging.info(msg, *l)


def warn(msg, *args):
    l = _convert(list(args))
    logging.warn(msg, *l)


def error(msg, *args):
    l = _convert(list(args))
    logging.error(msg, *l)

