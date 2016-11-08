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


class DiskMessage(Message):
    def __init__(self, t, path):
        super(DiskMessage, self).__init__(t)
        self.path = path


class FileMessage(Message):
    def __init__(self, t, path, node):
        super(FileMessage, self).__init__(t)
        self.path = path
        self.node = node

