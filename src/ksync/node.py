# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import copy
import datetime
import json
import logging
import os

import file_manager
import util


class NodeType(object):
    Unknown = 0,
    Local = 1,
    Removable = 2  # 中心节点


class NodeStatus(object):
    Idle = 0,
    Syncing = 1


class Node(object):
    FileName = ".node.txt"
    FileListsName = ".filelists.txt"


    @staticmethod
    def create(path):
        n = Node()
        n.name = util.get_uuid()
        n.base_path = path
        n.id = 0

        now = datetime.datetime.now()
        n.create_time = now.strftime("%Y-%m-%d %H:%M:%S.%f")

        return n


    @staticmethod
    def from_map(m):
        n = Node()
        n.name = m["name"]
        n.id = m["id"]
        n.base_path = m["path"]
        n.type = m["type"]
        n.create_time = m["create_time"]
        return n


    def __init__(self):
        self.name = None
        self.id = None
        self.type = NodeType.Unknown
        self.base_path = None  # 该节点对应的监控目录
        self.create_time = None

        self.status = NodeStatus.Idle
        self.file_info = None  # 按目录层级结构构建该map，底层为顶级目录 local FileInfo
        self.file_map = {}  # fullpath -> FileInfo


    def to_map(self):
        h = {
            "name": self.name,
            "id": self.id,
            "create_time": self.create_time,
            "type": self.type,
            "path": self.base_path,
        }

        return h


    def load_filelists(self):
        self.file_info = file_manager.FileInfo.create(self.base_path)
        self.file_info.create_file_map(self.file_map)
        self.update_version()


    # 根据从filelists.txt读取出来的信息，更新版本信息
    # @todo 给出异常的那些文件信息
    def update_version(self):
        filelist_path = os.path.join(self.base_path, Node.FileListsName)
        finfo_record = file_manager.FileInfo.parse_filelists(filelist_path)
        if not finfo_record:
            self.file_info.store_fileinfo(filelist_path)
            return

        fmap_record = {}
        finfo_record.create_file_map(fmap_record)

        for k, f in self.file_map.iteritems():
            if k in fmap_record:
                f.version = fmap_record[k].version

                if f.md5 != fmap_record[k].md5:
                    logging.info("exception, %s, %s", f.relative_path, f.name)

            else:
                logging.info("new file %s, %s", f.relative_path, f.name)


    # 若拷贝了文件，则拷贝完成之前，设置节点的status为Syncing
    def sync_file(self, other_node):
        self.status = NodeStatus.Syncing
        other_node.status = NodeStatus.Syncing

        # 比较两个节点下面的file_info
        (to_other, from_other, conflict) = self._diff_file(other_node)

        # 根据差异同步文件
        file_manager.FileInfo.sync(self, other_node, to_other)
        file_manager.FileInfo.sync(other_node, self, from_other)

        # @todo conflict的文件处理

        self.status = NodeStatus.Idle
        other_node.status = NodeStatus.Idle


    def _diff_file(self, other_node):
        assert isinstance(other_node, Node)

        to_other = []
        from_other = []
        conflict = []

        # 给每个FileInfo增加一个is_diffed成员，仅仅用在该函数中
        for fullname, finfo in self.file_map.iteritems():
            if fullname not in other_node.file_map:
                to_other.append(finfo)
                continue

            other_file = other_node.file_map[fullname]
            assert finfo.type == other_file.type

            if finfo.type == file_manager.FileType.Dir:
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
                logging.warn("Exception for %s: %s -> %s",
                             fullname, finfo.version, other_file.version)
                conflict.append((finfo, other_file))

        for other_info in other_node.file_map.itervalues():
            if not other_info.is_diffed:
                from_other.append(other_info)
                other_info.is_diffed = False

        for finfo in self.file_map.itervalues():
            finfo.is_diffed = False

        # other_node的is_diffed应该都是False的，for debug
        for oinfo in other_node.file_map.itervalues():
            assert oinfo.is_diffed == False

        return (to_other, from_other, conflict)


    @staticmethod
    def flush_version(src_info, src_node, dst_node):
        fullname = os.path.join(src_info.relative_path, src_info.name)
        if fullname in dst_node.file_map:
            dst_info = dst_node[fullname]
            dst_info.version = src_info.version

        else:
            # 如果不存在的话，要一级一级的在dst_node中查找，并创建子node
            hierarchy_list = []
            src_info.get_hierarchy(src_node.file_info, hierarchy_list)

            assert len(hierarchy_list) > 0

            dst_parent_info = None
            for hl in hierarchy_list:
                if hl.name == src_info.name:
                    dst_parent_info = hl

            assert dst_parent_info
            dst_parent_info[src_info.name] = copy.deepcopy(src_info)

            dst_info = dst_parent_info[src_info.name]
            dst_info.update_file_map(dst_node.file_map)

        fullname = os.path.join(dst_node.base_path, Node.FileListsName)
        dst_node.file_info.store_fileinfo(fullname)



# 可移动磁盘当成中心节点
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


    # 从磁盘中读取一个节点的信息（可能包含了其他节点的信息）
    def load_node(self, path):
        # 若该path下不存在 .node.txt，说明这是一个新节点
        # node id此时为0（未通信之前）
        filename = os.path.join(path, Node.FileName)
        if not os.path.exists(filename):
            n = Node.create(path)
            self.all_nodes[n.name] = n
            self.store_node(n)
            return n

        contents = None
        print filename
        with open(filename, "rb") as f:
            contents = f.read()

        assert contents
        print contents
        nodes = json.loads(contents)

        self.add_new_node(nodes)

        for n in nodes["others"]:
            self.add_new_node(n)

        node_name = nodes["name"]
        return self.all_nodes[node_name]


    def add_new_node(self, node_map):
        node_name = node_map["name"]
        if node_name not in self.all_nodes:
            new_node = Node.from_map(node_map)
            self.all_nodes[node_name] = new_node

            if new_node.id > self._next_node_id:
                self._next_node_id = new_node.id


    # 存储.node.txt和.filelists.txt
    def store_node(self, current_node):
        node_hash = current_node.to_map()

        others = []
        for n in self.all_nodes.itervalues():
            if n.name != current_node.name:
                n_hash = n.to_map()
                others.append(n_hash)

        node_hash["others"] = others

        fname = os.path.join(current_node.base_path, Node.FileName)
        with open(fname, "wb") as f:
            f.write(json.dumps(node_hash))


    def get_node_name_from_disk(self, path):
        filename = os.path.join(path, Node.FileName)
        assert os.path.exists(filename)

        with open(filename, "rb") as f:
            contents = f.readlines()

        node_json = json.loads(contents)
        return node_json["name"]


    def remove_node_by_path(self, disk_path):
        for name, n in self.all_nodes.iteritems():
            if n.path == disk_path:
                if n.status == NodeStatus.Syncing:
                    logging.warn("Sync failed, because of you remove the disk")

                logging.info("Remove node, name=%s, path=%s", name, disk_path)
                self.all_nodes.pop(name)

