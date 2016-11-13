# coding: utf-8
#
# Copyright (C) KRT, 2016 by kiterunner_t
# TO THE HAPPY FEW

import ctypes

import win32api
import win32gui
import win32con

import disk_monitor
import klog


# https://msdn.microsoft.com/en-us/library/aa363480(VS.85).aspx


class DeviceEvent(object):
    Arrival = 0x8000
    QueryRemove = 0x8001
    QueryRemoveFailed = 0x8002
    RemoveComplete = 0x8003
    TypesSpecific = 0x8005
    ConfigChanged = 0x0018
    

class DeviceType(object):
    Oem = 0x0
    DevNode = 0x1
    Volume = 0x2
    Port = 0x3
    Net = 0x4


class DeviceVolume(object):
    Media = 0x1
    Net = 0x2
    

class VcType(object):
    Word = ctypes.c_ushort
    Dword = ctypes.c_ulong
    

class DevBroadcastHeader(ctypes.Structure):
    _fields_ = [ 
        ("dbch_size", VcType.Dword),
        ("dbch_devicetype", VcType.Dword),
        ("dbch_reserved", VcType.Dword)
    ]


class DevBroadcastVolume(ctypes.Structure):
    _fields_ = [
        ("dbcv_size", VcType.Dword),
        ("dbcv_devicetype", VcType.Dword),
        ("dbcv_reserved", VcType.Dword),
        ("dbcv_unitmask", VcType.Dword),
        ("dbcv_flags", VcType.Word)
    ]
    

class WinDiskMonitor(disk_monitor.DiskMonitor):
    def __init__(self, q):
        super(WinDiskMonitor, self).__init__(q)


    def _run(self):
        message_map = {
            win32con.WM_DEVICECHANGE: self._on_device_change
        }

        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "udisk-monitor"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map

        class_atom = win32gui.RegisterClass(wc)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU

        self.hwnd = win32gui.CreateWindow(
            class_atom,
            "udisk monitor",
            style,
            0,
            0,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            0,
            0,
            wc.hInstance,
            None
        )

        win32gui.PumpMessages()


    def _on_device_change(self, hwnd, msg, wparam, lparam):
        dev_broadcast_hdr = DevBroadcastHeader.from_address(lparam) 

        if wparam == DeviceEvent.Arrival: 
            if dev_broadcast_hdr.dbch_devicetype == DeviceType.Volume:
                klog.info("It's a volume!")

            driver_path = WinDiskMonitor._get_driver(lparam)

            dev_broadcast_volume = DevBroadcastVolume.from_address(lparam)
            if dev_broadcast_volume.dbcv_flags == DeviceVolume.Media: 
                pass

            super(WinDiskMonitor, self).on_disk_arrive(driver_path)
            
        elif wparam == DeviceEvent.RemoveComplete:
            driver_path = WinDiskMonitor._get_driver(lparam)
            super(WinDiskMonitor, self).on_disk_remove(driver_path)

        return 1 


    @staticmethod
    def _get_driver(lparam):
        dev_broadcast_volume = DevBroadcastVolume.from_address(lparam)
        mask = dev_broadcast_volume.dbcv_unitmask

        letters = "ABCDEFGHIGKLMNOPKRSTUVWXYZ"
        for i in xrange(0, 26):
            if mask >> i == 1:
                # chr(ord("A") + i)
                return letters[i] + ":\\"

        assert False

