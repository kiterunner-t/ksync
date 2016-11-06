# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW


class Type(object):
    Unknown = 0,
    DiskArrival = 1,
    DiskRemove = 2,
    FileChange = 3


class Message(object):
    def __init__(self, t):
        self.type = t

