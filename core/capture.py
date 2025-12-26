"""
截图模块 - WGC (Windows Graphics Capture)
"""

import os
import time
import ctypes
from ctypes import wintypes
import numpy as np
from PIL import Image
from cv2 import cvtColor, COLOR_BGRA2RGBA
from .utils import get_resource_path, find_file

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ('length', wintypes.UINT),
        ('flags', wintypes.UINT),
        ('showCmd', wintypes.UINT),
        ('ptMinPosition', wintypes.POINT),
        ('ptMaxPosition', wintypes.POINT),
        ('rcNormalPosition', wintypes.RECT),
    ]


class ScreenCapture:
    """WGC 截图驱动"""

    def __init__(self):
        self.lib = None
        self.hwnd = 0
        self.width = 0
        self.height = 0
        self._initialized = False

        # 设置 DPI 感知
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass

    def _load_dll(self):
        """加载 WGC.dll"""
        # 使用工具函数查找 DLL
        dll_path = find_file('WGC.dll')
        
        if not dll_path:
            # 备用路径
            dll_path = get_resource_path('libs/WGC.dll')
            if not os.path.exists(dll_path):
                raise FileNotFoundError(f"找不到 WGC.dll")

        self.lib = ctypes.CDLL(dll_path)
        
        self.lib.CaptureWindow.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int,
            ctypes.c_int
        ]
        self.lib.CaptureWindow.restype = ctypes.c_bool
        
        print(f"[Capture] WGC.dll 已加载: {dll_path}")

    def init(self, hwnd=None, process_name=None):
        """
        初始化截图
        :param hwnd: 窗口句柄
        :param process_name: 进程名称 (如 "notepad.exe")
        """
        try:
            self._load_dll()
        except FileNotFoundError as e:
            print(f"[Capture] {e}")
            return False

        if hwnd:
            self.hwnd = hwnd
        elif process_name:
            self.hwnd = self._find_window_by_process(process_name)
            if not self.hwnd:
                print(f"[Capture] 找不到进程 {process_name} 的窗口")
                return False
        else:
            print("[Capture] 必须指定 hwnd 或 process_name")
            return False

        self.width, self.height = self._get_window_rect(self.hwnd)
        if self.width <= 0 or self.height <= 0:
            print(f"[Capture] 无效的窗口尺寸: {self.width}x{self.height}")
            return False

        self._initialized = True
        print(f"[Capture] 目标窗口: {self.hwnd}, 尺寸: {self.width}x{self.height}")
        return True

    def _find_window_by_process(self, process_name):
        """根据进程名称查找窗口"""
        if not HAS_PSUTIL:
            print("[Capture] psutil 未安装")
            return None

        candidates = []

        def enum_windows_proc(hwnd, lParam):
            pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                proc = psutil.Process(pid.value)
                if proc.name().lower() == process_name.lower():
                    w, h = self._get_window_rect(hwnd)
                    area = w * h
                    if area > 100:
                        candidates.append((area, hwnd))
            except:
                pass
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        return None

    def _get_window_rect(self, hwnd):
        """获取窗口尺寸"""
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect.right - rect.left, rect.bottom - rect.top

    def capture(self):
        """执行截图，返回 PIL Image"""
        if not self._initialized or not self.hwnd:
            return None

        # 更新窗口尺寸
        try:
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            
            if w <= 0 or h <= 0:
                return None
                
            self.width = w
            self.height = h
        except:
            return None

        # 检查最小化
        placement = WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(WINDOWPLACEMENT)
        ctypes.windll.user32.GetWindowPlacement(self.hwnd, ctypes.byref(placement))
        
        if placement.showCmd == 2:  # SW_SHOWMINIMIZED
            ctypes.windll.user32.ShowWindow(self.hwnd, 9)  # SW_RESTORE
            time.sleep(0.3)

        try:
            size = self.width * self.height * 4
            buffer = (ctypes.c_uint8 * size)()

            success = self.lib.CaptureWindow(self.hwnd, buffer, self.width, self.height)

            if success:
                image_data = np.ctypeslib.as_array(buffer)
                if image_data.size != (self.height * self.width * 4):
                    return None
                image_data = image_data.reshape(self.height, self.width, 4)
                image_data_rgb = cvtColor(image_data, COLOR_BGRA2RGBA)
                return Image.fromarray(image_data_rgb)
            return None
        except Exception as e:
            print(f"[Capture] 错误: {e}")
            return None

    def release(self):
        self.lib = None
        self.hwnd = 0
        self._initialized = False
