# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import json
import os
import shutil
import stat

import util


# 文件比较
# 文件同步
# 文件变化后同步
# .filelist.txt读写
#
# 若不同文件夹下有同样内容的文件，WARN
# 文件夹以何种方式进行同步？怎样判断文件夹重命名？


class FileType(object):
    File = 0
    Dir = 1


class FileInfo(object):
    def __init__(self):
        self.name = None
        self.path = None
        self.type = None
        self.create_time = None
        self.size = 0
        self.md5 = None
        self.version = (0, 0)  # (<node_id>, [last_modify_version>)

        self.subfiles = {}


    @staticmethod
    def create(path):
        (file_info, total_size, md5) = FileInfo._file_walk(path)
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
        finfo.path = m["path"]
        finfo.name = m["name"]
        finfo.type = m["type"]
        finfo.create_time = m["create_time"]
        finfo.md5 = m["md5"]
        finfo.size = m["size"]
        finfo.version = tuple(m["version"])

        if "subfiles" not in m:
            return finfo

        for f in m["subfiles"].itervalues():
            fullname = os.path.join(f.path, f.name)
            finfo.subfiles[fullname] = FileInfo.from_map(f)

        return finfo


    def to_map(self):
        map = {}
        map["path"] = self.path
        map["name"] = self.name
        map["type"] = self.type
        map["create_time"] = self.create_time
        map["md5"] = self.md5
        map["size"] = self.size
        map["version"] = list(self.version)

        submap = {}
        for f in self.subfiles.itervalues():
            fullname = os.path.join(f.path, f.name)
            submap[fullname] = f.to_map()

        map["subfiles"] = submap

        return map


    @staticmethod
    def _file_walk(path):
        file_info = FileInfo()

        total_size = 0
        md5_str = ""

        subfiles = os.listdir(path)
        for file in subfiles:
            fullname = os.path.join(path, file)
            file_stat = os.stat(fullname)

            mode = file_stat.st_mode
            if stat.S_ISDIR(mode):
                sub_type = FileType.Dir
                (sub, sub_size, sub_md5) = FileInfo._file_walk(fullname)

            elif stat.S_ISREG(mode):
                sub_type = FileType.File
                sub_size = file_stat.st_size
                sub_md5 = util.file_md5(fullname)
                sub = FileInfo()

            else:
                continue

            sub.name = file
            sub.path = fullname
            sub.type = sub_type
            sub.create_time = file_stat.st_ctime
            sub.size = sub_size
            sub.md5 = sub_md5

            file_info.subfiles[fullname] = sub

            md5_str += sub_md5
            total_size += sub_size

        file_stat = os.stat(path)
        file_info.path = path
        file_info.name = ""
        file_info.type = FileType.Dir
        file_info.create_time = file_stat.st_ctime
        file_info.size = total_size
        file_info.md5 = util.str_md5(md5_str)
        file_info.version = [0, 0]
        return (file_info, total_size, file_info.md5)


    def create_file_map(self, file_map):
        assert isinstance(file_map, dict)

        fullname = os.path.join(self.path, self.name)
        if fullname not in file_map:
            file_map[fullname] = self

        for sub in self.subfiles.itervalues():
            sub.create_file_map(file_map)


    def is_same_file(self, other):
        assert isinstance(other, FileInfo)
        assert self.type == other.type

        if self.md5 == other.md5:
            return True
        else:
            return False


    # 返回不同文件对象的list，也就是需要同步的
    def compare(self, other):
        assert isinstance(other, FileInfo)
        assert self.type == other.type

        if self.is_same_file(other):
            return []

        if self.type == FileType.File:
            return []


class FileManager(object):
    def __init__(self):
        self._removable_disk_path = r"D:\krt-data-sync"
        self._local_disk_path = r"F:\网盘"

        self._file_map = {}
        self._files = None

        self._removable_file_map = {}
        self._removable_files = None


    '''
    {
        "copy-to-removable": [("src/a", "dst/a"), ("b", "b")],
        "copy-to-local": ["c", "d"],
        "conflicts": ["e", "f"]  # 都是全路径
    }
    '''
    def compare(self):
        assert self._files
        assert self._removable_files

        to_removable = []
        to_local = []
        conflicts = []
        result = (to_removable, to_local, conflicts)

        if self._files.is_same_file(self._removable_files):
            return result


    def sync(self):
        to_local = self.to_local
        to_removable = self.to_removable

        self._do_sync(to_local, self._removable_disk_path, self._local_disk_path)
        self._do_sync(to_removable, self._local_disk_path, self._removable_disk_path)


    def _do_sync(self, sync_list, src_base_dir, dst_base_dir):
        cwd = os.getcwd()

        try:
            os.chdir(src_base_dir)
            for (src, dst) in sync_list:
                if dst is None:
                    dst_dir = os.path.join(dst_base_dir, src.path)
                    os.makedirs(dst_dir)
                else:
                    dst_dir = os.path.join(dst_base_dir, dst.path)

                src_file = os.path.join(src.path, src.name)
                dst_file = os.path.join(dst_dir, src.name)
                if src.type == FileType.Dir:
                    shutil.copytree(src_file, dst_file)
                else:
                    shutil.copyfile(src_file, dst_file)

        except:
            print "sync files exception"

        finally:
            os.chdir(cwd)

