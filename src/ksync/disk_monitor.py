# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import logging
import os
import threading

import message


class DiskMonitor(object):
    def __init__(self, q):
        self.platform = "Windows"
        self.queue = q

        self.thread = threading.Thread(target=self._run)


    def _run(self):
        raise NotImplementedError


    def run(self):
        self.thread.start()


    def join(self):
        self.thread.join()


    def on_disk_arrive(self, driver_path):
        logging.info("Removable disk arrive: %s", driver_path)

        m = message.Message(message.Type.DiskArrival)
        m.disk_path = driver_path
        self.queue.put(m)

    
    def on_disk_remove(self, driver_path):
        logging.info("Removable disk leave: %s", driver_path)

        m = message.Message(message.Type.DiskRemove)
        m.disk_path = driver_path
        self.queue.put(m)

