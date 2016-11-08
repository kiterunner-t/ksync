# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import json
import logging
import os
import shutil
import stat
import traceback

import util


class FileType(object):
    File = 0
    Dir = 1


class FileInfo(object):
    def __init__(self):
        self.name = None
        self.relative_path = None
        self.type = None
        self.create_time = None
        self.size = 0
        self.md5 = None
        self.version = [0, 0]  # [<node_id>, [last_modify_version>]

        self.subfiles = {}  # name -> file_info, 但现在存的是 full_name -> file_info

        self.is_diffed = False  # 参考Node._diff_file函数


    @staticmethod
    def create(path):
        cwd = os.getcwd()
        os.chdir(path)

        (file_info, total_size, md5) = FileInfo._file_walk(".")

        os.chdir(cwd)
        return file_info


    @staticmethod
    def parse_filelists(fullname):
        # 文件不存在或打开失败等，就当全部初始化
        if not os.path.exists(fullname):
            return None

        contents = None
        with open(fullname, "rb") as f:
            contents = f.read()

        if not contents:
            return None

        map = json.loads(contents)
        return FileInfo.create_from_map(map)


    @staticmethod
    def create_from_map(m):
        finfo = FileInfo()
        finfo.relative_path = m["path"]
        finfo.name = m["name"]
        finfo.type = m["type"]
        finfo.create_time = m["create_time"]
        finfo.md5 = m["md5"]
        finfo.size = m["size"]
        finfo.version = tuple(m["version"])

        if "subfiles" not in m:
            return finfo

        for f in m["subfiles"].itervalues():
            fullname = os.path.join(f["path"], f["name"])
            finfo.subfiles[fullname] = FileInfo.create_from_map(f)

        return finfo


    def to_map(self):
        map = {}
        map["path"] = self.relative_path
        map["name"] = self.name
        map["type"] = self.type
        map["create_time"] = self.create_time
        map["md5"] = self.md5
        map["size"] = self.size
        map["version"] = list(self.version)

        submap = {}
        for f in self.subfiles.itervalues():
            fullname = os.path.join(f.relative_path, f.name)
            submap[fullname] = f.to_map()

        map["subfiles"] = submap

        return map


    @staticmethod
    def _file_walk(path, level=0):
        file_info = FileInfo()

        total_size = 0
        md5_str = ""

        subfiles = os.listdir(path)
        for file in subfiles:
            fullname = os.path.join(path, file)
            file_stat = os.stat(fullname)

            if level == 0 \
                    and (file == ".node.txt" or file == ".filelists.txt"):
                logging.info("Skip file, %s", file)
                continue

            mode = file_stat.st_mode
            if stat.S_ISDIR(mode):
                sub_type = FileType.Dir
                (sub, sub_size, sub_md5) = FileInfo._file_walk(fullname, level+1)

            elif stat.S_ISREG(mode):
                sub_type = FileType.File
                sub_size = file_stat.st_size
                sub_md5 = util.file_md5(fullname)
                sub = FileInfo()

            else:
                continue

            sub.name = file
            sub.relative_path = path
            sub.type = sub_type
            sub.create_time = file_stat.st_ctime
            sub.size = sub_size
            sub.md5 = sub_md5

            file_info.subfiles[fullname] = sub

            md5_str += sub_md5
            total_size += sub_size

        parent_path = "."
        if path != ".":
            parent_path = os.path.normpath(os.path.join(path, ".."))

        name = "."
        names = path.split(os.sep)
        assert len(names) > 0
        if len(names) == 1:
            name = "."
        elif names[-1] == "":
            name = names[-2]
        else:
            name = names[-1]

        file_stat = os.stat(path)
        file_info.relative_path = parent_path
        file_info.name = name
        file_info.type = FileType.Dir
        file_info.create_time = file_stat.st_ctime
        file_info.size = total_size
        file_info.md5 = util.str_md5(md5_str)
        file_info.version = [0, 0]
        return (file_info, total_size, file_info.md5)


    def create_file_map(self, file_map):
        assert isinstance(file_map, dict)

        fullname = os.path.join(self.relative_path, self.name)
        if fullname not in file_map:
            file_map[fullname] = self

        for sub in self.subfiles.itervalues():
            sub.create_file_map(file_map)


    # 将file_info的信息存放到file_map hash表中
    # full_name -> file_info
    def update_file_map(self, file_map):
        for name, finfo in self.subfiles.iteritems():
            full_name = os.path.join(finfo.relative_path, finfo.name)
            file_map[full_name] = finfo

            finfo.update_file_map(file_map)


    # 从父parent_info中，获取直到当前节点的所有父节点list（该list存放到hierarchy_list）
    def get_hierarchy(self, parent_info, hierarchy_list):
        if self.name == parent_info.name:
            return

        if self.name in parent_info.subfiles:
            return

        hierarchy_list.append(parent_info)

        found = False
        for name, sub_parent_info in parent_info.subfiles.iteritems():
            if name == self.relative_path:
                found = True
                self.get_hierarchy(sub_parent_info, self, hierarchy_list)

        assert found


    def store_fileinfo(self, file_name):
        json_str = json.dumps(self.to_map())

        logging.debug(".filelists.txt: %s", json_str)

        with open(file_name, "wb") as f:
            f.write(json_str)


    @staticmethod
    def sync(from_node, to_node, fileinfo_list):
        cwd = os.getcwd()

        src_base_path = from_node.base_path
        dst_base_path = to_node.base_path
        try:
            os.chdir(src_base_path)

            for finfo in fileinfo_list:
                src_relative_path = finfo.relative_path

                dst_path = os.path.join(dst_base_path, src_relative_path)
                if not os.path.exists(dst_path):
                    os.makedirs(dst_path)

                src_file = os.path.join(src_relative_path, finfo.name)
                dst_file = os.path.join(dst_path, finfo.name)
                if finfo.type == FileType.Dir:
                    # shutil.copytree(src_file, dst_file)
                    # 只能一个文件一个文件的copy
                    assert not os.path.exists(dst_file)
                    os.makedirs(dst_file)
                    pass
                else:
                    shutil.copyfile(src_file, dst_file)

                    # @todo 每copy一次，刷新一次.filelists.txt
                    import node
                    node.Node.flush_version(src_file, from_node, to_node)

        except:
            logging.error("sync file error, %s", traceback.format_exc())

        finally:
            os.chdir(cwd)

