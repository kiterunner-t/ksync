# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import json
import os
import re
import stat

import klog
import kutil


class FileType(object):
    File = 0
    Dir = 1


class FileManager(object):
    def __init__(self, base_path):
        self.base_path = base_path
        self.root_info = None
        self.root_file_map = {}


class FileInfo(object):
    def __init__(self):
        self.name = None
        self.relative_path = None
        self.type = None
        self.create_time = None
        self.size = 0
        self.md5 = None
        self.version = [0, 0]   # [<node_id>, [last_modify_version>]

        self.subfiles = {}      # name -> file_info

        self.is_diffed = False  # 参考Node._diff_file函数
        self.parent_dir = None


    @staticmethod
    def create_from_map(m):
        finfo = FileInfo()
        finfo.relative_path = m[u"path"]
        finfo.name = m[u"name"]
        finfo.type = m[u"type"]
        finfo.create_time = m[u"create_time"]
        finfo.md5 = m[u"md5"]
        finfo.size = m[u"size"]
        finfo.version = m[u"version"]

        if u"subfiles" not in m:
            return finfo

        for f in m[u"subfiles"].itervalues():
            fullname = os.path.join(f[u"path"], f[u"name"])
            finfo.subfiles[fullname] = FileInfo.create_from_map(f)

        return finfo


    def to_map(self):
        map = {}
        map[u"path"] = self.relative_path
        map[u"name"] = self.name
        map[u"type"] = self.type
        map[u"create_time"] = self.create_time
        map[u"md5"] = self.md5
        map[u"size"] = self.size
        map[u"version"] = self.version

        submap = {}
        for f in self.subfiles.itervalues():
            fullname = os.path.join(f.relative_path, f.name)
            submap[fullname] = f.to_map()

        map[u"subfiles"] = submap

        return map


    def create_file_map(self, file_map):
        assert isinstance(file_map, dict)

        fullname = os.path.join(self.relative_path, self.name)
        if fullname not in file_map:
            file_map[fullname] = self

        for sub in self.subfiles.itervalues():
            sub.create_file_map(file_map)


    # full_name -> file_info
    def update_file_map(self, file_map):
        for name, finfo in self.subfiles.iteritems():
            full_name = os.path.join(finfo.relative_path, finfo.name)
            file_map[full_name] = finfo

            finfo.update_file_map(file_map)


    # 从父parent_info中，获取直到当前节点的所有节点list（该list存放到hierarchy_list）
    def get_hierarchy(self, parent_dir, parent_info, hierarchy_list):
        if os.path.join(self.relative_path, self.name) == \
                os.path.join(parent_info.relative_path, parent_info.name):
            hierarchy_list.append(parent_info)
            return

        hierarchy_list.append(parent_info)

        for name, sub_parent_info in parent_info.subfiles.iteritems():
            parent_dir_t = os.path.normpath(os.path.join(parent_dir, name))
            relative_path_norm = os.path.normpath(self.relative_path)
            if parent_dir_t == relative_path_norm:
                hierarchy_list.append(sub_parent_info)
                hierarchy_list.append(self)
                break

            if re.match(r"^" + parent_dir_t, relative_path_norm):
                self.get_hierarchy(parent_dir_t, sub_parent_info, hierarchy_list)


    def get_dst(self, src_hierarchy, level=0):
        assert 0 <= level < len(src_hierarchy)

        if level + 1 == len(src_hierarchy):
            return self, src_hierarchy[-1]

        src_info = src_hierarchy[level]

        src_fullname = os.path.join(src_info.relative_path, src_info.name)
        dst_fullname = os.path.join(self.relative_path, self.name)

        if src_fullname == dst_fullname:
            src_info = src_hierarchy[level+1]
            src_fullname = os.path.join(src_info.relative_path, src_info.name)

            p = None
            for name, sub_dst in self.subfiles.iteritems():
                dst_sub_fullname = os.path.join(sub_dst.relative_path, sub_dst.name)
                if src_fullname == dst_sub_fullname:
                    p, src_info = sub_dst.get_dst(src_hierarchy, level + 1)
                    break

            if not p:
                return self, src_info
            else:
                return p, src_info

        else:
            assert False  # this should not be happened


    def store_fileinfo(self, file_name):
        h_utf8 = kutil.map_to_utf8(self.to_map())
        json_str = json.dumps(h_utf8)

        klog.info(u"store file info to %s: %s", file_name, json_str)

        with open(file_name, "wb") as f:
            f.write(json_str)


def parse_filelists(fullname):
    if not os.path.exists(fullname):
        return None

    contents = None
    with open(fullname, "rb") as f:
        contents = f.read()

    if not contents:
        return None

    contents = kutil.to_local(contents)
    map = json.loads(contents)
    return FileInfo.create_from_map(map)


def create(path):
    cwd = os.getcwd()
    os.chdir(path)

    root_info = file_walk()

    os.chdir(cwd)
    return root_info


def file_walk(current_path="."):
    (sub, total_size, md5_str) = _file_walk(current_path, ".", 0)

    file_stat = os.stat(current_path)

    root_info = FileInfo()
    root_info.parent_dir = ""
    root_info.relative_path = ""
    root_info.name = current_path
    root_info.type = FileType.Dir
    root_info.create_time = file_stat.st_ctime
    root_info.size = total_size
    root_info.md5 = kutil.str_md5(md5_str) if md5_str != "" else None
    root_info.version = [0, 0]
    root_info.subfiles = sub

    return root_info


def _file_walk(path, dir_name, level):
    total_size = 0
    md5_str = ""
    subfiles_map = {}

    subfiles = os.listdir(path)
    for file in subfiles:
        fullname = os.path.join(path, file)
        file_stat = os.stat(fullname)

        if level == 0 \
                and (file == u".node.txt" or file == u".filelists.txt"):
            klog.info(u"Skip file, %s", file)
            continue

        file_info = FileInfo()

        sub = {}
        mode = file_stat.st_mode
        if stat.S_ISDIR(mode):
            sub_type = FileType.Dir
            (sub, sub_size, sub_md5) = _file_walk(fullname, file, level + 1)
            sub_md5 = kutil.str_md5(sub_md5)

        elif stat.S_ISREG(mode):
            sub_type = FileType.File
            sub_size = file_stat.st_size
            sub_md5 = kutil.file_md5(fullname)

        else:
            continue

        file_info.name = file
        file_info.parent_dir = dir_name
        file_info.relative_path = path
        file_info.type = sub_type
        file_info.create_time = file_stat.st_ctime
        file_info.size = sub_size
        file_info.md5 = sub_md5
        file_info.subfiles = sub

        subfiles_map[file] = file_info

        md5_str += sub_md5
        total_size += sub_size

    return (subfiles_map, total_size, md5_str)

