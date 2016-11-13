#! /usr/bin/env python
# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import os
import re
import sys
import unittest


# ref:
#   http://blog.csdn.net/five3/article/details/7104466
#   http://xdzw608.blog.51cto.com/4812210/1612063


def test_all():
    current_path = os.path.split(os.path.realpath(__file__))[0]

    sys.path.append(os.path.join(current_path, "..", "ksync"))
    sys.path.append(os.path.join(current_path, "ut"))

    files = os.listdir(current_path)

    test_file_re = re.compile("^test_.*\.py$", re.IGNORECASE)
    files = filter(test_file_re.search, files)
    filename_to_modulename = lambda f: os.path.splitext(f)[0]
    module_names = map(filename_to_modulename, files)
    
    test_modules = map(__import__, module_names)
    testsuite_loader = unittest.defaultTestLoader.loadTestsFromModule
    return unittest.TestSuite(map(testsuite_loader, test_modules))
    
    
def ut():
    pass
    
    
def st():
    pass
    
    
def performance():
    pass


if __name__ == "__main__":
    test_all()

