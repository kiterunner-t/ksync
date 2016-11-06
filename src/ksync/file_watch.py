# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import logging

import watchdog.events as watch_events
import watchdog.observers as watch_observer

import message


class FileHandler(watch_events.FileSystemEventHandler):
    def __init__(self, node, q):
        self.node = node
        self.queue = q


    def on_created(self, event):
        super(FileHandler, self).on_created(event)
        if not event.is_directory:
            logging.info("created name:[%s]", event.src_path)

        m = message.Message(message.Type.FileChange)
        m.node = self.node
        m.change_path = event.src_path

        self.queue.put(m)


    def on_modified(self, event):
        super(FileHandler, self).on_created(event)
        if not event.is_directory:
            logging.info("modified name:[%s]", event.src_path)
            abs_path = event.src_path

        m = message.Message(message.Type.FileChange)
        m.node = self.node
        m.change_path = event.src_path

        self.queue.put(m)


class Watcher(object):
    def __init__(self, q):
        self.queue = q
        self.node = []
        self.observer = watch_observer.Observer()


    def add_path(self, node):
        self.node.append(node)

        watch_handler = FileHandler(node, self.queue)
        self.observer.schedule(watch_handler, node.path, recursive=True)


    def remove_path(self, node):
        pass


    def start(self):
        if len(self.node) == 0:
            raise NotImplementedError

        observer = self.observer
        for n in self.node:
            watch_handler = FileHandler(n, self.queue)
            observer.schedule(watch_handler, n.path, recursive=True)

        observer.start()


    def join(self):
        self.observer.join()

