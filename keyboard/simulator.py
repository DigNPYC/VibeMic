from pynput.keyboard import Controller, Key
import time


class KeyboardSimulator:
    def __init__(self):
        self.controller = Controller()
        self.key_map = {
            'enter': Key.enter,
            'tab': Key.tab,
            'esc': Key.esc,
            'escape': Key.esc,
            'space': Key.space,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'home': Key.home,
            'end': Key.end,
            'pageup': Key.page_up,
            'pagedown': Key.page_down,
            'f1': Key.f1,
            'f2': Key.f2,
            'f3': Key.f3,
            'f4': Key.f4,
            'f5': Key.f5,
            'f6': Key.f6,
            'f7': Key.f7,
            'f8': Key.f8,
            'f9': Key.f9,
            'f10': Key.f10,
            'f11': Key.f11,
            'f12': Key.f12,
            'ctrl': Key.ctrl,
            'ctrl_l': Key.ctrl_l,
            'ctrl_r': Key.ctrl_r,
            'leftctrl': Key.ctrl_l,
            'rightctrl': Key.ctrl_r,
            'alt': Key.alt,
            'alt_l': Key.alt_l,
            'alt_r': Key.alt_r,
            'leftalt': Key.alt_l,
            'rightalt': Key.alt_r,
            'shift': Key.shift,
            'shift_l': Key.shift_l,
            'shift_r': Key.shift_r,
            'leftshift': Key.shift_l,
            'rightshift': Key.shift_r,
            'cmd': Key.cmd,
            'win': Key.cmd,
        }

    def press_key(self, key_name):
        """按下并释放单个按键"""
        try:
            key = self._get_key(key_name)
            if key:
                self.controller.press(key)
                self.controller.release(key)
                return True
            return False
        except Exception as e:
            print(f"按键模拟失败: {e}")
            return False

    def press_combo(self, keys):
        """按下组合键"""
        try:
            key_objects = []
            for key_name in keys:
                key = self._get_key(key_name)
                if key:
                    key_objects.append(key)

            # 按下所有键
            for key in key_objects:
                self.controller.press(key)

            time.sleep(0.05)

            # 释放所有键（逆序）
            for key in reversed(key_objects):
                self.controller.release(key)

            return True
        except Exception as e:
            print(f"组合键模拟失败: {e}")
            return False

    def type_text(self, text):
        """输入文本"""
        try:
            self.controller.type(text)
            return True
        except Exception as e:
            print(f"文本输入失败: {e}")
            return False

    def _get_key(self, key_name):
        """获取按键对象"""
        key_name = key_name.lower().strip()

        # 先从映射表中查找
        if key_name in self.key_map:
            return self.key_map[key_name]

        # 单字符直接返回
        if len(key_name) == 1:
            return key_name

        return None


# 预定义常用快捷键
SHORTCUTS = {
    'copy': ['ctrl', 'c'],
    'paste': ['ctrl', 'v'],
    'cut': ['ctrl', 'x'],
    'undo': ['ctrl', 'z'],
    'redo': ['ctrl', 'y'],
    'save': ['ctrl', 's'],
    'select_all': ['ctrl', 'a'],
    'find': ['ctrl', 'f'],
    'print': ['ctrl', 'p'],
    'close': ['alt', 'f4'],
    'minimize': ['win', 'm'],
    'lock': ['win', 'l'],
}
