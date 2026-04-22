import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
from PIL import Image, ImageTk
import io
import requests
from utils.helpers import get_local_ip


class MainWindow:
    def __init__(self, app):
        self.app = app
        self.root = None
        self.qr_label = None
        self.status_label = None
        self.ip_label = None
        self.autostart_var = None
        
        # 缩放相关
        self.base_width = 480
        self.base_height = 620
        self.scale_factor = 1.0
        
        # 存储所有需要缩放的字体
        self.fonts = {}
        self.widgets_to_scale = []

    def create_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title("vibe搭子 - 电脑端服务端")
        self.root.geometry(f"{self.base_width}x{self.base_height}")
        self.root.minsize(320, 400)
        self.root.resizable(True, True)
        
        # 设置窗口关闭行为
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 创建字体
        self._create_fonts()
        
        # 创建界面
        self._create_widgets()
        self.update_status(0)
        
        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self._on_resize)

    def _create_fonts(self):
        """创建字体字典"""
        self.fonts = {
            'title': ("Microsoft YaHei", int(24 * self.scale_factor), "bold"),
            'subtitle': ("Microsoft YaHei", int(12 * self.scale_factor)),
            'normal': ("Microsoft YaHei", int(10 * self.scale_factor)),
            'ip': ("Microsoft YaHei", int(11 * self.scale_factor)),
            'status': ("Microsoft YaHei", int(12 * self.scale_factor)),
            'settings': ("Microsoft YaHei", int(11 * self.scale_factor)),
            'button': ("Microsoft YaHei", int(10 * self.scale_factor))
        }

    def _create_widgets(self):
        """创建界面组件"""
        # 使用 Canvas 作为主容器，支持精确控制
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # 创建内容框架
        self.content_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.content_frame, 
            anchor="nw",
            tags="content"
        )
        
        # 配置 canvas 随窗口变化
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # 标题
        self.title_label = tk.Label(
            self.content_frame,
            text="vibe搭子",
            font=self.fonts['title'],
            fg="#333333"
        )
        self.title_label.pack(pady=(int(20 * self.scale_factor), int(5 * self.scale_factor)))

        self.subtitle_label = tk.Label(
            self.content_frame,
            text="手机遥控电脑工具",
            font=self.fonts['subtitle'],
            fg="#666666"
        )
        self.subtitle_label.pack(pady=(0, int(15 * self.scale_factor)))

        # 二维码区域
        qr_size = int(200 * self.scale_factor)
        qr_frame = tk.Frame(self.content_frame, bg="white", width=qr_size, height=qr_size)
        qr_frame.pack(pady=int(10 * self.scale_factor))
        qr_frame.pack_propagate(False)

        self.qr_label = tk.Label(qr_frame, bg="white")
        self.qr_label.pack(expand=True)

        # 刷新二维码按钮
        btn_width = int(15 * self.scale_factor) if self.scale_factor >= 0.8 else 12
        refresh_btn = tk.Button(
            self.content_frame,
            text="刷新二维码",
            command=self._refresh_qrcode,
            font=self.fonts['button'],
            cursor="hand2",
            width=btn_width
        )
        refresh_btn.pack(pady=int(8 * self.scale_factor))

        # 连接信息
        info_frame = tk.Frame(self.content_frame)
        info_frame.pack(pady=int(10 * self.scale_factor))

        self.ip_label = tk.Label(
            info_frame,
            text=f"IP: {get_local_ip()}:{self.app.ws_port}",
            font=self.fonts['ip'],
            fg="#333333"
        )
        self.ip_label.pack()

        # 状态显示
        self.status_label = tk.Label(
            self.content_frame,
            text="等待连接...",
            font=self.fonts['status'],
            fg="#888888"
        )
        self.status_label.pack(pady=int(10 * self.scale_factor))

        # 设置区域
        settings_frame = tk.LabelFrame(
            self.content_frame, 
            text="设置", 
            font=self.fonts['settings']
        )
        settings_frame.pack(
            pady=int(10 * self.scale_factor), 
            padx=int(30 * self.scale_factor), 
            fill="x"
        )

        # 开机自启选项
        self.autostart_var = tk.BooleanVar(value=self.app.is_autostart_enabled())
        autostart_check = tk.Checkbutton(
            settings_frame,
            text="开机自动启动",
            variable=self.autostart_var,
            command=self._on_autostart_change,
            font=self.fonts['normal'],
            cursor="hand2"
        )
        autostart_check.pack(anchor="w", padx=int(10 * self.scale_factor), pady=int(8 * self.scale_factor))

        # 按钮区域
        btn_frame = tk.Frame(self.content_frame)
        btn_frame.pack(pady=int(15 * self.scale_factor))

        minimize_btn = tk.Button(
            btn_frame,
            text="最小化到托盘",
            command=self._minimize_to_tray,
            font=self.fonts['button'],
            width=btn_width,
            cursor="hand2"
        )
        minimize_btn.pack(side="left", padx=int(5 * self.scale_factor))

        exit_btn = tk.Button(
            btn_frame,
            text="退出程序",
            command=self.app.exit_app,
            font=self.fonts['button'],
            width=btn_width,
            bg="#ff6b6b",
            fg="white",
            cursor="hand2"
        )
        exit_btn.pack(side="left", padx=int(5 * self.scale_factor))
        
        # 底部留白
        tk.Label(self.content_frame, text="").pack(pady=int(20 * self.scale_factor))

        # 加载二维码
        self._refresh_qrcode()

    def _on_canvas_configure(self, event=None):
        """Canvas 大小变化时调整内容"""
        if self.canvas:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            # 让内容框架宽度等于 canvas 宽度
            self.canvas.itemconfig(self.canvas_window, width=width)

    def _on_resize(self, event=None):
        """窗口大小变化时重新计算缩放比例"""
        if not self.root or event.widget != self.root:
            return
            
        # 获取当前窗口尺寸
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # 计算缩放比例（以高度为准，确保所有内容都能显示）
        scale_w = width / self.base_width
        scale_h = height / self.base_height
        new_scale = min(scale_w, scale_h)
        
        # 限制最小缩放比例
        new_scale = max(new_scale, 0.6)
        
        # 如果缩放比例变化足够大，重新创建界面
        if abs(new_scale - self.scale_factor) > 0.05:
            self.scale_factor = new_scale
            self._recreate_interface()

    def _recreate_interface(self):
        """重新创建界面以应用新的缩放比例"""
        # 保存当前状态
        old_connected_count = 0
        if self.status_label:
            text = self.status_label.cget("text")
            if "已连接" in text:
                try:
                    old_connected_count = int(text.split()[1])
                except:
                    pass
        
        # 清空内容框架
        if self.content_frame:
            for widget in self.content_frame.winfo_children():
                widget.destroy()
        
        # 重新创建字体
        self._create_fonts()
        
        # 重新创建所有组件
        self._create_widgets_content()
        
        # 恢复状态
        self.update_status(old_connected_count)

    def _create_widgets_content(self):
        """创建内容（供重新创建时使用）"""
        # 标题
        self.title_label = tk.Label(
            self.content_frame,
            text="vibe搭子",
            font=self.fonts['title'],
            fg="#333333"
        )
        self.title_label.pack(pady=(int(20 * self.scale_factor), int(5 * self.scale_factor)))

        self.subtitle_label = tk.Label(
            self.content_frame,
            text="手机遥控电脑工具",
            font=self.fonts['subtitle'],
            fg="#666666"
        )
        self.subtitle_label.pack(pady=(0, int(15 * self.scale_factor)))

        # 二维码区域
        qr_size = int(200 * self.scale_factor)
        qr_frame = tk.Frame(self.content_frame, bg="white", width=qr_size, height=qr_size)
        qr_frame.pack(pady=int(10 * self.scale_factor))
        qr_frame.pack_propagate(False)

        self.qr_label = tk.Label(qr_frame, bg="white")
        self.qr_label.pack(expand=True)

        # 刷新二维码按钮
        btn_width = int(15 * self.scale_factor) if self.scale_factor >= 0.8 else 12
        refresh_btn = tk.Button(
            self.content_frame,
            text="刷新二维码",
            command=self._refresh_qrcode,
            font=self.fonts['button'],
            cursor="hand2",
            width=btn_width
        )
        refresh_btn.pack(pady=int(8 * self.scale_factor))

        # 连接信息
        info_frame = tk.Frame(self.content_frame)
        info_frame.pack(pady=int(10 * self.scale_factor))

        self.ip_label = tk.Label(
            info_frame,
            text=f"IP: {get_local_ip()}:{self.app.ws_port}",
            font=self.fonts['ip'],
            fg="#333333"
        )
        self.ip_label.pack()

        # 状态显示
        self.status_label = tk.Label(
            self.content_frame,
            text="等待连接...",
            font=self.fonts['status'],
            fg="#888888"
        )
        self.status_label.pack(pady=int(10 * self.scale_factor))

        # 设置区域
        settings_frame = tk.LabelFrame(
            self.content_frame, 
            text="设置", 
            font=self.fonts['settings']
        )
        settings_frame.pack(
            pady=int(10 * self.scale_factor), 
            padx=int(30 * self.scale_factor), 
            fill="x"
        )

        # 开机自启选项
        self.autostart_var = tk.BooleanVar(value=self.app.is_autostart_enabled())
        autostart_check = tk.Checkbutton(
            settings_frame,
            text="开机自动启动",
            variable=self.autostart_var,
            command=self._on_autostart_change,
            font=self.fonts['normal'],
            cursor="hand2"
        )
        autostart_check.pack(anchor="w", padx=int(10 * self.scale_factor), pady=int(8 * self.scale_factor))

        # 按钮区域
        btn_frame = tk.Frame(self.content_frame)
        btn_frame.pack(pady=int(15 * self.scale_factor))

        minimize_btn = tk.Button(
            btn_frame,
            text="最小化到托盘",
            command=self._minimize_to_tray,
            font=self.fonts['button'],
            width=btn_width,
            cursor="hand2"
        )
        minimize_btn.pack(side="left", padx=int(5 * self.scale_factor))

        exit_btn = tk.Button(
            btn_frame,
            text="退出程序",
            command=self.app.exit_app,
            font=self.fonts['button'],
            width=btn_width,
            bg="#ff6b6b",
            fg="white",
            cursor="hand2"
        )
        exit_btn.pack(side="left", padx=int(5 * self.scale_factor))
        
        # 底部留白
        tk.Label(self.content_frame, text="").pack(pady=int(20 * self.scale_factor))

        # 加载二维码
        self._refresh_qrcode()

    def _refresh_qrcode(self):
        """刷新二维码"""
        try:
            # 从本地 HTTP 服务获取二维码
            url = f"http://127.0.0.1:{self.app.http_port}/api/qrcode"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                # 根据缩放比例调整二维码大小
                qr_size = int(180 * self.scale_factor)
                image = image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.qr_label.config(image=photo)
                self.qr_label.image = photo  # 保持引用
        except Exception as e:
            print(f"二维码加载失败: {e}")
            self.qr_label.config(text="二维码加载失败\n请刷新重试")

    def _on_autostart_change(self):
        """开机自启状态变更"""
        enabled = self.autostart_var.get()
        self.app.set_autostart(enabled)

    def _minimize_to_tray(self):
        """最小化到托盘"""
        self.root.withdraw()

    def _on_close(self):
        """窗口关闭处理"""
        self.root.withdraw()  # 隐藏窗口而不是退出

    def show_window(self):
        """显示窗口"""
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

    def update_status(self, connected_count):
        """更新连接状态"""
        if not self.root or not self.status_label:
            return

        if connected_count > 0:
            self.status_label.config(
                text=f"已连接 {connected_count} 台设备",
                fg="#00AA00"
            )
        else:
            self.status_label.config(
                text="等待连接...",
                fg="#888888"
            )

    def run(self):
        """运行主窗口"""
        self.create_window()
        self.root.mainloop()

    def stop(self):
        """停止主窗口"""
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None
