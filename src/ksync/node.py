# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import copy
import datetime
import json
import os
import shutil
import traceback

import file_info
import klog
import kutil


class NodeType(object):
    Unknown = 0,
    Local = 1,
    Removable = 2  # 中心节点


class NodeStatus(object):
    Idle = 0,
    Syncing = 1


class Node(object):
    FileName = u".node.txt"
    FileListsName = u".filelists.txt"


    def __init__(self):
        self.name = None
        self.id = None
        self.type = NodeType.Unknown
        self.base_path = None  # monitor path
        self.create_time = None

        self.status = NodeStatus.Idle
        self.root_file_info = None  # 按目录层级结构构建该map，底层为顶级目录 local FileInfo
        self.root_file_map = {}     # fullname (path+name) -> FileInfo


    @staticmethod
    def create(path):
        n = Node()
        n.name = kutil.get_uuid()
        n.base_path = path
        n.id = 0

        now = datetime.datetime.now()
        n.create_time = now.strftime(u"%Y-%m-%d %H:%M:%S.%f")

        return n


    @staticmethod
    def from_map(m):
        n = Node()
        n.name = m[u"name"]
        n.id = m[u"id"]
        n.base_path = m[u"base_path"]
        n.type = m[u"type"]
        n.create_time = m[u"create_time"]
        return n


    def to_map(self):
        h = {
            u"name": self.name,
            u"id": self.id,
            u"create_time": self.create_time,
            u"type": self.type,
            u"base_path": self.base_path,
        }

        return h


    def load_filelists(self):
        self.root_file_info = file_info.create(self.base_path)
        self.root_file_info.create_file_map(self.root_file_map)
        self.update_version()


    # @todo 给出异常的那些文件信息
    def update_version(self):
        filelist_name = os.path.join(self.base_path, Node.FileListsName)
        root_file_info = file_info.parse_filelists(filelist_name)
        if not root_file_info:
            self.root_file_info.store_fileinfo(filelist_name)
            return

        fmap_record = {}
        root_file_info.create_file_map(fmap_record)

        for k, f in self.root_file_map.iteritems():
            if k in fmap_record:
                f.version = fmap_record[k].version

                if f.md5 != fmap_record[k].md5:
                    klog.info(u"Update version exception, md5 is not matched for file=%s, %s",
                                 f.relative_path, f.name)

            else:
                klog.info(u"Update version new file=%s, %s", f.relative_path, f.name)


    def sync_file(self, other_node):
        self.status = NodeStatus.Syncing
        other_node.status = NodeStatus.Syncing

        (to_other, from_other, conflict) = self._diff_file(other_node)

        self.sync(other_node, to_other)
        other_node.sync(self, from_other)

        # @todo conflict的文件处理

        self.status = NodeStatus.Idle
        other_node.status = NodeStatus.Idle

        klog.info(u"Sync files finished.")


    def sync(self, to_node, fileinfo_list):
        cwd = os.getcwd()

        src_base_path = self.base_path
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

                if finfo.type == file_info.FileType.Dir:
                    # shutil.copytree(local_src_file, local_dst_file)
                    # 只能一个文件一个文件的copy
                    if not os.path.exists(dst_file):
                        klog.info(u"Sync file, make dirs=%s", dst_file)
                        os.makedirs(dst_file)

                else:
                    klog.info(u"Sync file, filename=%s", src_file)
                    # @todo 考虑copy失败的情况，如磁盘满
                    shutil.copyfile(src_file, dst_file)

                Node.flush_version(finfo, self, to_node)

            klog.info(u"Sync files finished from node/%s to node/%s",
                         self.name, to_node.name)

        except:
            klog.error(u"sync file error, %s", traceback.format_exc())

        finally:
            os.chdir(cwd)


    def _diff_file(self, other_node):
        assert isinstance(other_node, Node)

        to_other = []
        from_other = []
        conflict = []

        # 给每个FileInfo增加一个is_diffed成员，仅仅用在该函数中
        for fullname, finfo in self.root_file_map.iteritems():
            if fullname not in other_node.root_file_map:
                to_other.append(finfo)
                continue

            other_file = other_node.root_file_map[fullname]
            assert finfo.type == other_file.type

            if finfo.type == file_info.FileType.Dir:
                other_file.is_diffed = True
                continue

            # 名字相同了，比较MD5和版本
            if finfo.md5 == other_file.md5:
                assert finfo.version[0]==other_file.version[0] \
                       and finfo.version[1]==other_file.version[1]
                other_file.is_diffed = True
                continue

            other_file.is_diffed = True
            if finfo.version[1] > other_file.version[1]:
                to_other.append(finfo)
            elif finfo.version[1] < other_file.version[1]:
                from_other.append(other_file)
            else:
                klog.warn(u"Exception for %s: %s -> %s",
                          fullname, finfo.version, other_file.version)
                conflict.append((finfo, other_file))

        for other_info in other_node.root_file_map.itervalues():
            if not other_info.is_diffed:
                from_other.append(other_info)
            else:
                other_info.is_diffed = False

        other_node.root_file_map["."].is_diffed = False

        for finfo in self.root_file_map.itervalues():
            finfo.is_diffed = False

        # other_node的is_diffed应该都是False的，for debug
        for oinfo in other_node.root_file_map.itervalues():
            assert oinfo.is_diffed == False

        return (to_other, from_other, conflict)


    @staticmethod
    def flush_version(src_info, src_node, dst_node):
        fullname = os.path.join(src_info.relative_path, src_info.name)
        if fullname in dst_node.root_file_map:
            dst_info = dst_node.root_file_map[fullname]
            dst_info.version = src_info.version

        else:
            # 如果不存在的话，要一级一级的在dst_node中查找，并创建子node
            hierarchy_list = []
            src_info.get_hierarchy(u".", src_node.root_file_info, hierarchy_list)
            assert len(hierarchy_list) > 0

            dst_parent_info, needed_copy = dst_node.root_file_info.get_dst(hierarchy_list)
            assert dst_parent_info

            t = copy.deepcopy(needed_copy)
            dst_parent_info.subfiles[needed_copy.name] = t

            dst_info = dst_parent_info.subfiles[needed_copy.name]
            dst_info.update_file_map(dst_node.root_file_map)

        fullname = os.path.join(dst_node.base_path, Node.FileListsName)
        dst_node.root_file_info.store_fileinfo(fullname)


class NodeManager(object):
    def __init__(self):
        # self.online_nodes = []
        self.all_nodes = {}
        self._next_node_id = 0


    # node_id一开始只能为0，与可移动磁盘通信以后再决定其真实id
    # 若next_node_id为0，说明没有通信过，默认值
    def _get_next_ndoe_id(self):
        if self._next_node_id == 0:
            return 0

        new_id = self._next_node_id
        self._next_node_id += 1
        return new_id


    def load_node(self, path):
        filename = os.path.join(path, Node.FileName)
        if not os.path.exists(filename):
            n = Node.create(path)
            self.all_nodes[n.name] = n
            self.store_node(n)
            return n

        contents = None
        with open(filename, "rb") as f:
            contents = f.read()

        assert contents
        contents = kutil.to_local(contents)
        nodes = json.loads(contents)

        self.add_new_node(nodes)

        for n in nodes[u"others"]:
            self.add_new_node(n)

        node_name = nodes[u"name"]
        return self.all_nodes[node_name]


    def add_new_node(self, node_map):
        node_name = node_map[u"name"]
        if node_name not in self.all_nodes:
            new_node = Node.from_map(node_map)
            self.all_nodes[node_name] = new_node

            if new_node.id > self._next_node_id:
                self._next_node_id = new_node.id


    def store_node(self, current_node):
        node_hash = current_node.to_map()

        others = []
        for n in self.all_nodes.itervalues():
            if n.name != current_node.name:
                n_hash = n.to_map()
                others.append(n_hash)

        node_hash[u"others"] = others

        fname = os.path.join(current_node.base_path, Node.FileName)
        with open(fname, "wb") as f:
            h_utf8 = kutil.map_to_utf8(node_hash)
            node_hash = json.dumps(h_utf8)
            f.write(node_hash)


    def get_node_name_from_disk(self, path):
        filename = os.path.join(path, Node.FileName)
        assert os.path.exists(filename)

        with open(filename, "rb") as f:
            contents = kutil.to_local(f.readlines())

        node_json = json.loads(contents)
        return node_json[u"name"]


    def remove_node_by_path(self, disk_path):
        for name, n in self.all_nodes.iteritems():
            if n.path == disk_path:
                if n.status == NodeStatus.Syncing:
                    klog.warn(u"Sync failed, because of you remove the disk")

                klog.info(u"Remove node, name=%s, path=%s", name, disk_path)
                self.all_nodes.pop(name)

