"""
输入控制器 - 支持 Win32 SendInput 和 Logitech G HUB 双驱动
含贝塞尔曲线擬人化移动
"""

import ctypes
import ctypes.wintypes
import time
import random
import math
import os

from .utils import find_file

# ==================== Win32 API 定义 ====================
ULONG_PTR = ctypes.wintypes.WPARAM
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000
KEYEVENTF_KEYUP = 0x0002

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.wintypes.WORD), ("wScan", ctypes.wintypes.WORD),
                ("dwFlags", ctypes.wintypes.DWORD), ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.wintypes.LONG), ("dy", ctypes.wintypes.LONG),
                ("mouseData", ctypes.wintypes.DWORD), ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.wintypes.DWORD), ("wParamL", ctypes.wintypes.WORD),
                ("wParamH", ctypes.wintypes.WORD)]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD), ("u", _INPUT_UNION)]

user32 = ctypes.WinDLL('user32', use_last_error=True)
SendInput = user32.SendInput
SendInput.argtypes = (ctypes.wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = ctypes.wintypes.UINT
GetSystemMetrics = user32.GetSystemMetrics
GetCursorPos = user32.GetCursorPos

# Win32 虚拟键码
VK_MAP = {
    'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
    'backspace': 0x08, 'tab': 0x09, 'enter': 0x0D, 'return': 0x0D,
    'shift': 0x10, 'lshift': 0xA0, 'rshift': 0xA1,
    'ctrl': 0x11, 'lctrl': 0xA2, 'rctrl': 0xA3, 'control': 0x11,
    'alt': 0x12, 'lalt': 0xA4, 'ralt': 0xA5,
    'esc': 0x1B, 'escape': 0x1B, 'space': 0x20, 'win': 0x5B,
    'capslock': 0x14, 'delete': 0x2E, 'insert': 0x2D,
    'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
    'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
    'f11': 0x7A, 'f12': 0x7B,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    ';': 0xBA, '=': 0xBB, ',': 0xBC, '-': 0xBD, '.': 0xBE, '/': 0xBF,
    '`': 0xC0, '[': 0xDB, '\\': 0xDC, ']': 0xDD, "'": 0xDE,
}

SHIFT_SYMBOLS = {
    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
    '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.', '?': '/', '~': '`'
}

# Logitech HID 键码
LOGITECH_KEY_MAP = {
    'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08, 'f': 0x09,
    'g': 0x0A, 'h': 0x0B, 'i': 0x0C, 'j': 0x0D, 'k': 0x0E, 'l': 0x0F,
    'm': 0x10, 'n': 0x11, 'o': 0x12, 'p': 0x13, 'q': 0x14, 'r': 0x15,
    's': 0x16, 't': 0x17, 'u': 0x18, 'v': 0x19, 'w': 0x1A, 'x': 0x1B,
    'y': 0x1C, 'z': 0x1D,
    '1': 0x1E, '2': 0x1F, '3': 0x20, '4': 0x21, '5': 0x22, '6': 0x23,
    '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,
    'enter': 0x28, 'esc': 0x29, 'escape': 0x29, 'backspace': 0x2A, 'tab': 0x2B, 'space': 0x2C,
    '-': 0x2D, '=': 0x2E, '[': 0x2F, ']': 0x30, '\\': 0x31, ';': 0x33,
    "'": 0x34, '`': 0x35, ',': 0x36, '.': 0x37, '/': 0x38, 'capslock': 0x39,
    'f1': 0x3A, 'f2': 0x3B, 'f3': 0x3C, 'f4': 0x3D, 'f5': 0x3E, 'f6': 0x3F,
    'f7': 0x40, 'f8': 0x41, 'f9': 0x42, 'f10': 0x43, 'f11': 0x44, 'f12': 0x45,
    'left': 0x50, 'up': 0x52, 'right': 0x4F, 'down': 0x51,
    'ctrl': 0xE0, 'shift': 0xE1, 'alt': 0xE2, 'win': 0xE3,
    'lctrl': 0xE0, 'lshift': 0xE1, 'lalt': 0xE2,
    'rctrl': 0xE4, 'rshift': 0xE5, 'ralt': 0xE6
}


class InputController:
    """
    输入控制器，支持两种驱动模式：
    - 'win32': Windows SendInput API（默认，通用）
    - 'logitech': Logitech G HUB 驱动（需要罗技硬件，更难被检测）
    """
    
    def __init__(self, driver='win32'):
        """
        :param driver: 'win32' 或 'logitech'
        """
        self.driver_type = driver
        self.screen_width = GetSystemMetrics(0)
        self.screen_height = GetSystemMetrics(1)
        self.variance = 0
        self.global_offset_x = 0
        self.global_offset_y = 0
        self._held_keys = set()
        
        # Logitech 专用
        self._logi_dll = None
        self._logi_connected = False
        self._logi_mouse_mask = 0
        self._logi_held_keys = set()
        
        if driver == 'logitech':
            self._init_logitech()

    def _init_logitech(self):
        """初始化 Logitech 驱动"""
        dll_path = find_file('Logitech_driver.dll')
        if not dll_path:
            dll_path = find_file('ghub_device.dll')
        
        if not dll_path:
            print("[Logitech] 找不到 DLL，回退到 Win32")
            self.driver_type = 'win32'
            return
        
        try:
            self._logi_dll = ctypes.CDLL(dll_path)
            self._logi_dll.device_open.restype = ctypes.c_bool
            self._logi_dll.device_close.restype = None
            self._logi_dll.mouse_emit.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self._logi_dll.mouse_emit.restype = ctypes.c_bool
            self._logi_dll.keyboard_emit_state.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
            self._logi_dll.keyboard_emit_state.restype = ctypes.c_bool
            self._logi_dll.keyboard_release_all.restype = None
            
            if self._logi_dll.device_open():
                self._logi_connected = True
                print(f"[Logitech] 驱动加载成功: {dll_path}")
            else:
                print("[Logitech] 驱动连接失败，回退到 Win32")
                self.driver_type = 'win32'
        except Exception as e:
            print(f"[Logitech] 加载异常: {e}，回退到 Win32")
            self.driver_type = 'win32'

    def set_variance(self, v):
        self.variance = v

    def set_global_offset(self, x, y):
        self.global_offset_x = x
        self.global_offset_y = y

    def _apply_variance(self, x, y):
        if self.variance > 0:
            x += random.randint(-self.variance, self.variance)
            y += random.randint(-self.variance, self.variance)
        return x, y

    def _apply_offset(self, x, y):
        return x + self.global_offset_x, y + self.global_offset_y

    # ==================== Win32 底层 ====================
    
    def _send_input(self, inp):
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _win32_move_to(self, x, y):
        nx = int(x * 65535 / self.screen_width)
        ny = int(y * 65535 / self.screen_height)
        mi = MOUSEINPUT(dx=nx, dy=ny, mouseData=0, dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, time=0, dwExtraInfo=0)
        self._send_input(INPUT(type=INPUT_MOUSE, u=_INPUT_UNION(mi=mi)))

    def _win32_mouse_event(self, flags, data=0):
        mi = MOUSEINPUT(dx=0, dy=0, mouseData=data, dwFlags=flags, time=0, dwExtraInfo=0)
        self._send_input(INPUT(type=INPUT_MOUSE, u=_INPUT_UNION(mi=mi)))

    def _win32_key_event(self, vk_code, is_key_up=False):
        ki = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_KEYUP if is_key_up else 0, time=0, dwExtraInfo=0)
        self._send_input(INPUT(type=INPUT_KEYBOARD, u=_INPUT_UNION(ki=ki)))

    # ==================== Logitech 底层 ====================
    
    def _logi_mouse_emit(self, button_mask, x, y, wheel):
        if self._logi_connected:
            self._logi_dll.mouse_emit(button_mask, int(x), int(y), int(wheel))

    def _logi_update_keyboard(self):
        if not self._logi_connected:
            return
        keys_array = (ctypes.c_ubyte * 6)()
        current_keys = list(self._logi_held_keys)
        for i in range(min(len(current_keys), 6)):
            keys_array[i] = current_keys[i]
        self._logi_dll.keyboard_emit_state(keys_array)

    # ==================== 贝塞尔曲线 ====================
    
    def _bezier_point(self, t, p0, p1, p2, p3):
        u = 1 - t
        return (u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1])

    def get_position(self):
        pt = ctypes.wintypes.POINT()
        GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def move_human(self, x, y, duration=None):
        """贝塞尔曲线擬人化移动"""
        x, y = self._apply_variance(x, y)
        x, y = self._apply_offset(x, y)
        
        start = self.get_position()
        end = (x, y)
        dist = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        if dist < 5:
            self._do_move_to(x, y)
            return
        
        if duration is None:
            duration = max(0.1, min(0.8, dist / 1500))
        steps = max(10, int(dist / 10))
        
        dx, dy = end[0] - start[0], end[1] - start[1]
        offset_range = max(30, dist * 0.2)
        
        ctrl1 = (start[0] + dx * 0.25 + random.uniform(-offset_range, offset_range),
                 start[1] + dy * 0.25 + random.uniform(-offset_range, offset_range))
        ctrl2 = (start[0] + dx * 0.75 + random.uniform(-offset_range, offset_range),
                 start[1] + dy * 0.75 + random.uniform(-offset_range, offset_range))
        
        step_delay = duration / steps
        
        for i in range(1, steps + 1):
            t = i / steps
            ease_t = t * (2 - t)  # Ease-out
            bx, by = self._bezier_point(ease_t, start, ctrl1, ctrl2, end)
            
            if self.driver_type == 'logitech' and self._logi_connected:
                curr = self.get_position()
                dx_step, dy_step = int(bx - curr[0]), int(by - curr[1])
                if dx_step != 0 or dy_step != 0:
                    self._logi_mouse_emit(self._logi_mouse_mask, dx_step, dy_step, 0)
            else:
                self._win32_move_to(int(bx), int(by))
            
            time.sleep(step_delay * random.uniform(0.8, 1.2))
        
        # 最终修正
        if self.driver_type == 'logitech' and self._logi_connected:
            self._logi_final_adjust(x, y)

    def _logi_final_adjust(self, target_x, target_y):
        """Logitech 最终位置微调"""
        for _ in range(30):
            curr = self.get_position()
            dx, dy = target_x - curr[0], target_y - curr[1]
            if abs(dx) < 2 and abs(dy) < 2:
                break
            move_x = max(-20, min(20, int(dx / 1.5))) or (1 if dx > 0 else -1 if dx else 0)
            move_y = max(-20, min(20, int(dy / 1.5))) or (1 if dy > 0 else -1 if dy else 0)
            self._logi_mouse_emit(self._logi_mouse_mask, move_x, move_y, 0)
            time.sleep(0.01)

    def _do_move_to(self, x, y):
        """底层移动到绝对坐标"""
        if self.driver_type == 'logitech' and self._logi_connected:
            curr = self.get_position()
            dx, dy = x - curr[0], y - curr[1]
            self._logi_mouse_emit(self._logi_mouse_mask, dx, dy, 0)
            time.sleep(0.02)
            self._logi_final_adjust(x, y)
        else:
            self._win32_move_to(x, y)


    # ==================== 鼠标操作 ====================
    
    def move(self, x, y, duration=0, human=False):
        if human:
            self.move_human(x, y, duration if duration > 0 else None)
        else:
            x, y = self._apply_variance(x, y)
            x, y = self._apply_offset(x, y)
            self._do_move_to(x, y)

    def click(self, x, y, button='left', clicks=1, human=False):
        if human:
            self.move_human(x, y)
            time.sleep(random.uniform(0.02, 0.08))
        else:
            x, y = self._apply_variance(x, y)
            x, y = self._apply_offset(x, y)
            self._do_move_to(x, y)
            time.sleep(0.02)
        
        if self.driver_type == 'logitech' and self._logi_connected:
            btn_code = {'left': 1, 'right': 2, 'middle': 4}.get(button, 1)
            for _ in range(clicks):
                self._logi_mouse_mask |= btn_code
                self._logi_mouse_emit(self._logi_mouse_mask, 0, 0, 0)
                time.sleep(random.uniform(0.06, 0.12))
                self._logi_mouse_mask &= ~btn_code
                self._logi_mouse_emit(self._logi_mouse_mask, 0, 0, 0)
                if clicks > 1:
                    time.sleep(random.uniform(0.1, 0.2))
        else:
            down_flag = {'left': MOUSEEVENTF_LEFTDOWN, 'right': MOUSEEVENTF_RIGHTDOWN, 'middle': MOUSEEVENTF_MIDDLEDOWN}.get(button, MOUSEEVENTF_LEFTDOWN)
            up_flag = {'left': MOUSEEVENTF_LEFTUP, 'right': MOUSEEVENTF_RIGHTUP, 'middle': MOUSEEVENTF_MIDDLEUP}.get(button, MOUSEEVENTF_LEFTUP)
            for _ in range(clicks):
                self._win32_mouse_event(down_flag)
                time.sleep(0.03 + random.uniform(0, 0.02))
                self._win32_mouse_event(up_flag)
                if clicks > 1:
                    time.sleep(0.08 + random.uniform(0, 0.04))

    def double_click(self, x, y, human=False):
        self.click(x, y, 'left', 2, human)

    def drag(self, x1, y1, x2, y2, duration=0.5, human=False):
        if human:
            self.move_human(x1, y1)
        else:
            x1, y1 = self._apply_variance(x1, y1)
            x1, y1 = self._apply_offset(x1, y1)
            self._do_move_to(x1, y1)
        
        time.sleep(0.05)
        self.mouse_down('left')
        time.sleep(0.05)
        
        if human:
            self.move_human(x2, y2, duration)
        else:
            x2, y2 = self._apply_variance(x2, y2)
            x2, y2 = self._apply_offset(x2, y2)
            self._do_move_to(x2, y2)
        
        time.sleep(0.05)
        self.mouse_up('left')

    def scroll(self, clicks):
        if self.driver_type == 'logitech' and self._logi_connected:
            direction = 1 if clicks > 0 else -1
            for _ in range(abs(clicks)):
                self._logi_mouse_emit(self._logi_mouse_mask, 0, 0, direction)
                time.sleep(random.uniform(0.05, 0.08))
        else:
            self._win32_mouse_event(MOUSEEVENTF_WHEEL, clicks * 120)

    def mouse_down(self, button='left'):
        if self.driver_type == 'logitech' and self._logi_connected:
            btn_code = {'left': 1, 'right': 2, 'middle': 4}.get(button, 1)
            self._logi_mouse_mask |= btn_code
            self._logi_mouse_emit(self._logi_mouse_mask, 0, 0, 0)
        else:
            down_flag = {'left': MOUSEEVENTF_LEFTDOWN, 'right': MOUSEEVENTF_RIGHTDOWN, 'middle': MOUSEEVENTF_MIDDLEDOWN}.get(button, MOUSEEVENTF_LEFTDOWN)
            self._win32_mouse_event(down_flag)

    def mouse_up(self, button='left'):
        if self.driver_type == 'logitech' and self._logi_connected:
            btn_code = {'left': 1, 'right': 2, 'middle': 4}.get(button, 1)
            self._logi_mouse_mask &= ~btn_code
            self._logi_mouse_emit(self._logi_mouse_mask, 0, 0, 0)
        else:
            up_flag = {'left': MOUSEEVENTF_LEFTUP, 'right': MOUSEEVENTF_RIGHTUP, 'middle': MOUSEEVENTF_MIDDLEUP}.get(button, MOUSEEVENTF_LEFTUP)
            self._win32_mouse_event(up_flag)

    # ==================== 键盘操作 ====================
    
    def key_press(self, key):
        if self.driver_type == 'logitech' and self._logi_connected:
            vk = LOGITECH_KEY_MAP.get(key.lower())
            if vk:
                self._logi_held_keys.add(vk)
                self._logi_update_keyboard()
                time.sleep(random.uniform(0.04, 0.08))
                self._logi_held_keys.discard(vk)
                self._logi_update_keyboard()
        else:
            vk = VK_MAP.get(key.lower())
            if vk:
                self._win32_key_event(vk, False)
                time.sleep(0.03)
                self._win32_key_event(vk, True)

    def key_down(self, key):
        if self.driver_type == 'logitech' and self._logi_connected:
            vk = LOGITECH_KEY_MAP.get(key.lower())
            if vk:
                self._logi_held_keys.add(vk)
                self._logi_update_keyboard()
        else:
            vk = VK_MAP.get(key.lower())
            if vk:
                self._win32_key_event(vk, False)
                self._held_keys.add(key.lower())

    def key_up(self, key):
        if self.driver_type == 'logitech' and self._logi_connected:
            vk = LOGITECH_KEY_MAP.get(key.lower())
            if vk:
                self._logi_held_keys.discard(vk)
                self._logi_update_keyboard()
        else:
            vk = VK_MAP.get(key.lower())
            if vk:
                self._win32_key_event(vk, True)
                self._held_keys.discard(key.lower())

    def key_hold(self, key, duration):
        self.key_down(key)
        time.sleep(duration)
        self.key_up(key)

    def type_text(self, text):
        for char in text:
            target_key = char.lower()
            need_shift = False
            
            if char in SHIFT_SYMBOLS:
                target_key = SHIFT_SYMBOLS[char]
                need_shift = True
            elif char.isupper():
                need_shift = True
            
            if need_shift:
                self.key_down('shift')
                time.sleep(0.02)
            
            self.key_press(target_key)
            
            if need_shift:
                self.key_up('shift')
                time.sleep(0.02)
            
            time.sleep(random.uniform(0.03, 0.08))

    def hotkey(self, *keys):
        for key in keys:
            self.key_down(key)
            time.sleep(0.02)
        for key in reversed(keys):
            self.key_up(key)
            time.sleep(0.02)

    def release_all(self):
        if self.driver_type == 'logitech' and self._logi_connected:
            self._logi_dll.keyboard_release_all()
            self._logi_mouse_mask = 0
            self._logi_mouse_emit(0, 0, 0, 0)
            self._logi_held_keys.clear()
        else:
            modifiers = ['win', 'ctrl', 'alt', 'shift', 'lwin', 'rwin', 'lctrl', 'rctrl', 'lalt', 'ralt', 'lshift', 'rshift']
            for key in modifiers:
                vk = VK_MAP.get(key)
                if vk:
                    self._win32_key_event(vk, True)
            self._held_keys.clear()

    def close(self):
        """关闭驱动"""
        self.release_all()
        if self._logi_connected and self._logi_dll:
            self._logi_dll.device_close()
            self._logi_connected = False
