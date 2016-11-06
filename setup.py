#! /usr/bin/env python
# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import setuptools


setuptools.setup(
    name="ksync",
    version="0.1.0",
    description="",
    author="kiterunner_t",
    author_email="kiterunner_t@hotmail.com",

    scripts=["bin/ksync.py"],
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    package_data={}
)

