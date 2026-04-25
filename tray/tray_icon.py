import pystray
from PIL import Image, ImageDraw
import threading
import os
import sys


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self.icon_thread = None
        self.is_running = False

    def _create_image(self, connected=False):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))
        
        icon_path = os.path.join(base_path, 'icon.png')
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                return img
            except Exception as e:
                print(f"加载图标失败: {e}")

        # 默认图案：V 字
        width = 64
        height = 64
        color = '#00AA00' if connected else '#888888'

        image = Image.new('RGB', (width, height), color)
        dc = ImageDraw.Draw(image)

        # 绘制 V 字
        points = [
            (14, 14),  # 左上
            (32, 50),  # V 字底部
            (50, 14),  # 右上
        ]
        dc.line(points + [points[0]], fill='white', width=8)

        return image

    def _on_show_window(self, icon, item):
        """显示主窗口"""
        if self.app and hasattr(self.app, 'show_window'):
            self.app.show_window()

    def _on_toggle_autostart(self, icon, item):
        """切换开机自启"""
        if self.app and hasattr(self.app, 'toggle_autostart'):
            self.app.toggle_autostart()
            self._update_menu()

    def _on_exit(self, icon, item):
        """退出程序"""
        self.is_running = False
        icon.stop()
        if self.app and hasattr(self.app, 'exit_app'):
            self.app.exit_app()

    def _update_menu(self):
        if self.icon:
            self.icon.menu = pystray.Menu(
                pystray.MenuItem("显示主窗口", self._on_show_window),
                pystray.MenuItem("开机自启", self._on_toggle_autostart, checked=lambda item: self.app.is_autostart_enabled()),
                pystray.MenuItem("退出", self._on_exit)
            )

    def update_status(self, connected_count):
        """更新连接状态图标"""
        if self.icon:
            self.icon.icon = self._create_image(connected_count > 0)
            self.icon.title = f"VibeMic - 已连接({connected_count}台设备)" if connected_count > 0 else "VibeMic - 等待连接"

    def run(self):
        self.is_running = True

        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", self._on_show_window),
            pystray.MenuItem("开机自启", self._on_toggle_autostart, checked=lambda item: self.app.is_autostart_enabled()),
            pystray.MenuItem("退出", self._on_exit)
        )

        self.icon = pystray.Icon(
            "vibe_dazi",
            self._create_image(False),
            "VibeMic - 等待连接",
            menu
        )

        self.icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.icon_thread.start()

    def stop(self):
        """停止托盘图标"""
        self.is_running = False
        if self.icon:
            self.icon.stop()
