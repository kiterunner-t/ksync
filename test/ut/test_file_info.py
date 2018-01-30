#! /usr/bin/env python
# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import t_util
import os
import unittest

import ksync.file_info as kfile


def _create_file(file_name, content_length):
    if os.path.exists(file_name):
        os.remove(file_name)

    with open(file_name, "wb") as f:
        f.write("x" * content_length)


class FileInfoTest(unittest.TestCase):
    def setUp(self):
        test_base_dir = os.path.join("data", "test-file-walk-data")
        level1_dir = os.path.join(test_base_dir, "level-1")
        level2_dir = os.path.join(level1_dir, "level-2")

        if not os.path.exists(level2_dir):
            os.makedirs(level2_dir)

        _create_file(os.path.join(test_base_dir, "base.txt"), 1)
        _create_file(os.path.join(level2_dir, "level-2.txt"), 3)

        self.cwd = os.getcwd()
        os.chdir(test_base_dir)

        self.base_info = kfile.file_walk()
        self.level1_info = self.base_info.subfiles["level-1"]
        self.level2_info = self.level1_info.subfiles["level-2"]
        self.level2_text_info = self.level2_info.subfiles["level-2.txt"]

        dst_base_dir = os.path.join("data", "dst-test-file-walk-data")
        dst_level_1 = os.path.join(dst_base_dir, "level-1")
        if not os.path.exists(dst_level_1):
            os.makedirs(dst_level_1)

        os.chdir(dst_base_dir)
        self.dst_root_info = kfile.file_walk()
        self.dst_level1_info = self.dst_root_info.subfiles["level-1"]


    def tearDown(self):
        os.chdir(self.cwd)


    def test_file_walk(self):
        self.assertIsInstance(self.level1_info, kfile.FileInfo)
        self.assertIsInstance(self.level2_info, kfile.FileInfo)
        self.assertIsInstance(self.level2_text_info, kfile.FileInfo)

        self.assertEqual(self.level2_text_info.name, "level-2.txt")

        level2_text_path = os.path.join(".", "level-1", "level-2")
        self.assertEqual(self.level2_text_info.relative_path, level2_text_path)

        h_list = []
        # base_info.get_hierarchy("level-2.txt", level2_text_info, h_list)
        self.level2_text_info.get_hierarchy(".", self.base_info, h_list)
        self.assertEqual(len(h_list), 4)

        (t, src_t) = self.dst_root_info.get_dst(h_list)
        self.assertEqual(t.name, "level-1")
        self.assertEqual(src_t.name, "level-2")


if __name__ == "__main__":
    unittest.main()

