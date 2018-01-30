# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import os
import Queue as queue

import file_watch
import kconfig
import klog
import message
import node


class Main(object):
    def __init__(self, config):
        self.config = config

        self._node_manager = node.NodeManager()
        self.local_node = None

        self._threads = []
        self.watcher = None
        self.dispatcher = {
            message.Type.DiskArrival: self._disk_arrival,
            message.Type.DiskRemove:  self._disk_remove,
            message.Type.FileChange:  self._file_change,
        }


    def run(self):
        q = queue.Queue()

        # 启动U盘监控模块
        monitor = self._get_monitor(q)
        monitor.run()
        self._threads.append(monitor)

        # 启动node_manager，获取本地节点信息；刷新本地文件相关信息
        # 初始节点信息大多无效，当有节点通信以后，需要再次保存节点信息
        node_manager = self._node_manager
        local_node = node_manager.load_node(self.config.local_path)
        local_node.load_filelists()
        self.local_node = local_node

        # 启动文件监控模块
        self.watcher = file_watch.Watcher(q)
        self.watcher.add_node(local_node)
        self.watcher.start()
        self._threads.append(self.watcher)

        klog.info("Start monitor job.")

        # 主线程监控queue，然后处理任务
        while True:
            msg = q.get()
            self._do_work(msg)
            q.task_done()

        for t in self._threads:
            t.join()


    def _do_work(self, msg):
        msg_type = msg.type
        handler = self.dispatcher[msg_type]
        assert handler

        handler(msg)


    def _get_monitor(self, q):
        platform = self.config.platform

        if platform == kconfig.Platform.Nt:
            import disk_monitor_win as disk_monitor
            return disk_monitor.WinDiskMonitor(q)

        elif platform == kconfig.Platform.Linux:
            raise NotImplementedError

        else:
            raise NotImplementedError


    def _disk_arrival(self, msg):
        driver_path = msg.disk_path
        udisk_path = os.path.join(driver_path, self.config.removable_disk_path)
        if not os.path.exists(udisk_path):
            klog.info(u"path is not exist: %s", udisk_path)
            return

        new_node = self._node_manager.load_node(udisk_path)
        new_node.load_filelists()

        self.local_node.sync_file(new_node)

        self.watcher.add_node(new_node)


    def _disk_remove(self, msg):
        driver_path = msg.disk_path
        udisk_path = os.path.join(driver_path, self.config.removable_disk_path)
        if not os.path.exists(udisk_path):
            klog.info(u"path is not exist: %s", udisk_path)
            return

        self.watcher.remove_path(udisk_path)

        self._node_manager.remove_node_by_path(udisk_path)


    # 需要过滤那些正在同步的文件的事件通知
    def _file_change(self, msg):
        pass

