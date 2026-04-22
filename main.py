import sys
import os
import threading
import asyncio
import winreg as reg
import argparse
from server.websocket_server import WebSocketServer
from server.http_server import HTTPServer
from tray.tray_icon import TrayIcon
from ui.main_window import MainWindow
from audio.virtual_mic import get_virtual_mic_manager


class CyberRuyiApp:
    def __init__(self, silent_mode=False):
        self.silent_mode = silent_mode
        
        # 首先检测虚拟麦克风设备
        self.vmic_manager = get_virtual_mic_manager()
        device_id, device_desc = self.vmic_manager.auto_select_best_device()
        
        self.ws_server = WebSocketServer(host="0.0.0.0", port=8765)
        self.http_server = HTTPServer(self.ws_server, host="0.0.0.0", port=8080)
        self.tray_icon = TrayIcon(self)
        self.main_window = MainWindow(self)

        self.ws_port = 8765
        self.http_port = 8080
        self.running = False

        # 注册状态变更回调
        self.ws_server.on_status_change(self._on_ws_status_change)
        
        # 配置音频设备
        if device_id is not None:
            is_virtual = self.vmic_manager.is_virtual_ready()
            self.ws_server.configure_audio_device(device_id, device_desc, is_virtual)

    def _on_ws_status_change(self, connected_count):
        """WebSocket 连接状态变更回调"""
        self.tray_icon.update_status(connected_count)
        self.main_window.update_status(connected_count)

    def is_autostart_enabled(self):
        """检查是否开启开机自启"""
        try:
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                reg.KEY_READ
            )
            try:
                reg.QueryValueEx(key, "CyberRuyi")
                reg.CloseKey(key)
                return True
            except FileNotFoundError:
                reg.CloseKey(key)
                return False
        except Exception:
            return False

    def set_autostart(self, enabled, silent_startup=None):
        """设置开机自启
        
        Args:
            enabled: 是否启用开机自启
            silent_startup: 是否静默启动，None表示使用当前设置
        """
        try:
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                reg.KEY_WRITE
            )

            if enabled:
                # 获取当前程序路径
                exe_path = sys.executable
                script_path = os.path.abspath(__file__)
                
                # 确定是否静默启动
                if silent_startup is None:
                    silent_startup = self.is_silent_startup_enabled()

                # 如果是打包后的 exe，直接注册 exe 路径
                if exe_path.endswith("python.exe") or exe_path.endswith("pythonw.exe"):
                    # 开发环境，强制使用 pythonw.exe 运行，避免 CMD 窗口弹窗
                    # pythonw.exe 是无窗口版本的 Python 解释器
                    exe_dir = os.path.dirname(exe_path)
                    pythonw_path = os.path.join(exe_dir, "pythonw.exe")
                    
                    # 如果 pythonw.exe 不存在，尝试替换路径中的 python.exe
                    if not os.path.exists(pythonw_path):
                        pythonw_path = exe_path.replace("python.exe", "pythonw.exe")
                    
                    # 如果还是不存在，使用原路径（但这种情况不应该发生）
                    if not os.path.exists(pythonw_path):
                        pythonw_path = exe_path
                    
                    # 根据静默设置决定是否添加 --autostart 参数
                    if silent_startup:
                        value = f'"{pythonw_path}" "{script_path}" --autostart'
                    else:
                        value = f'"{pythonw_path}" "{script_path}"'
                else:
                    # 打包后的 exe
                    if silent_startup:
                        value = f'"{exe_path}" --autostart'
                    else:
                        value = f'"{exe_path}"'

                reg.SetValueEx(key, "CyberRuyi", 0, reg.REG_SZ, value)
            else:
                try:
                    reg.DeleteValue(key, "CyberRuyi")
                except FileNotFoundError:
                    pass

            reg.CloseKey(key)
            return True
        except Exception as e:
            print(f"设置开机自启失败: {e}")
            return False
    
    def is_silent_startup_enabled(self):
        """检查是否开启静默启动"""
        try:
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER,
                r"Software\CyberRuyi",
                0,
                reg.KEY_READ
            )
            try:
                value, _ = reg.QueryValueEx(key, "SilentStartup")
                reg.CloseKey(key)
                return bool(value)
            except FileNotFoundError:
                reg.CloseKey(key)
                return True  # 默认开启静默启动
        except Exception:
            return True  # 默认开启静默启动
    
    def set_silent_startup(self, enabled):
        """设置静默启动"""
        try:
            # 创建或打开应用配置项
            key = reg.CreateKey(reg.HKEY_CURRENT_USER, r"Software\CyberRuyi")
            reg.SetValueEx(key, "SilentStartup", 0, reg.REG_DWORD, 1 if enabled else 0)
            reg.CloseKey(key)
            
            # 如果开机自启已启用，更新注册表
            if self.is_autostart_enabled():
                self.set_autostart(True, enabled)
            
            return True
        except Exception as e:
            print(f"设置静默启动失败: {e}")
            return False

    def toggle_autostart(self):
        """切换开机自启状态"""
        current = self.is_autostart_enabled()
        return self.set_autostart(not current)

    def show_window(self):
        """显示主窗口"""
        self.main_window.show_window()

    def exit_app(self):
        """退出程序"""
        self.running = False
        print("正在退出程序...")

        # 停止各个组件
        self.tray_icon.stop()
        self.main_window.stop()

        # 退出程序
        os._exit(0)

    def run(self):
        """启动应用"""
        self.running = True
        
        # 静默模式下不打印启动信息到控制台
        if not self.silent_mode:
            print("=" * 50)
            print("VibeMic - 电脑端服务端")
            print("=" * 50)
            
            # 显示虚拟麦克风状态
            status = self.vmic_manager.check_installation_status()
            print("\n[虚拟麦克风状态]")
            if status['has_virtual_device']:
                print(f"  ✓ 虚拟设备就绪: {status['device_type']}")
                print(f"  ✓ 可作为真实麦克风使用")
            else:
                print(f"  ✗ 未检测到虚拟音频设备")
                print(f"  ⚠ 语音将通过音响播放")
                print(f"  ℹ 如需作为麦克风使用，请安装 VB-Cable")
                print(f"    下载: https://vb-audio.com/Cable/")
            print()

        # 启动 WebSocket 服务（在独立线程中）
        ws_thread = threading.Thread(target=self.ws_server.run, daemon=True)
        ws_thread.start()

        # 启动 HTTP 服务（在独立线程中）
        http_thread = threading.Thread(target=self.http_server.run, daemon=True)
        http_thread.start()
        
        # 等待服务启动完成
        import time
        if not self.silent_mode:
            print("[系统] 正在启动服务...")
        time.sleep(2)  # 给服务启动留出时间
        if not self.silent_mode:
            print("[系统] 服务已就绪\n")

        # 启动系统托盘
        self.tray_icon.run()

        # 根据启动模式决定是否显示主窗口
        if self.silent_mode:
            # 静默模式：只运行托盘，不显示主窗口
            # 使用一个后台线程来保持程序运行
            while self.running:
                import time
                time.sleep(1)
        else:
            # 正常模式：启动主窗口（阻塞）
            self.main_window.run()


def main():
    """程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='VibeMic - 电脑端服务端')
    parser.add_argument('--autostart', action='store_true', help='开机自启动模式（静默启动，不显示窗口）')
    parser.add_argument('--silent', action='store_true', help='静默模式，不显示主窗口')
    args = parser.parse_args()
    
    # 如果指定了 --autostart 或 --silent，则使用静默模式
    silent_mode = args.autostart or args.silent
    
    app = CyberRuyiApp(silent_mode=silent_mode)

    try:
        app.run()
    except KeyboardInterrupt:
        if not silent_mode:
            print("\n收到中断信号，正在退出...")
        app.exit_app()


if __name__ == "__main__":
    main()
