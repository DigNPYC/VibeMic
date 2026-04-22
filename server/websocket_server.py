import asyncio
import websockets
import json
import base64
from typing import Set, Dict, Callable
from keyboard.simulator import KeyboardSimulator, SHORTCUTS
from utils.helpers import parse_message, create_message

# 音频功能可选
try:
    from audio.player import AudioPlayer
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("[警告] PyAudio 未安装，语音功能不可用")


class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.keyboard = KeyboardSimulator()
        self.audio_player = AudioPlayer() if AUDIO_AVAILABLE else None
        self.status_callbacks: list[Callable] = []
        self.voice_recording = False  # 标记是否正在录音
        self.voice_packet_count = 0  # 接收的语音包计数
        self.is_virtual_mic = False  # 是否使用虚拟麦克风

    def configure_audio_device(self, device_id: int, device_desc: str, is_virtual: bool = False):
        """配置音频输出设备"""
        if self.audio_player:
            self.audio_player.set_device(device_id, device_desc, is_virtual)
            self.is_virtual_mic = is_virtual
            if is_virtual:
                print("[系统] 已配置虚拟麦克风模式")
            else:
                print(f"[系统] 已配置音频设备: {device_desc}")
        else:
            print("[系统] 音频播放器不可用")

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """注册新客户端"""
        self.clients.add(websocket)
        print(f"新设备连接: {websocket.remote_address}")
        self._notify_status_change()

        # 发送连接成功消息
        await websocket.send(create_message("status", {
            "connected": True,
            "device_name": "Windows-PC",
            "message": "连接成功"
        }))

    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """注销客户端"""
        self.clients.discard(websocket)
        print(f"设备断开: {websocket.remote_address}")
        self._notify_status_change()

    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """处理客户端消息"""
        data = parse_message(message)
        if not data:
            return

        msg_type = data.get("type")
        msg_data = data.get("data", {})

        if msg_type == "key_press":
            await self._handle_key_press(websocket, msg_data)
        elif msg_type == "key_combo":
            await self._handle_key_combo(websocket, msg_data)
        elif msg_type == "shortcut":
            await self._handle_shortcut(websocket, msg_data)
        elif msg_type == "voice_start":
            await self._handle_voice_start(websocket)
        elif msg_type == "voice_data":
            await self._handle_voice_data(websocket, msg_data)
        elif msg_type == "voice_stop":
            await self._handle_voice_stop(websocket)
        elif msg_type == "ping":
            await websocket.send(create_message("pong"))
        else:
            await websocket.send(create_message("error", {
                "code": 1001,
                "message": f"未知消息类型: {msg_type}"
            }))

    async def _handle_key_press(self, websocket, data):
        """处理单键按下"""
        key = data.get("key", "")
        success = self.keyboard.press_key(key)
        await websocket.send(create_message("key_result", {
            "success": success,
            "key": key
        }))

    async def _handle_key_combo(self, websocket, data):
        """处理组合键"""
        keys = data.get("keys", [])
        success = self.keyboard.press_combo(keys)
        await websocket.send(create_message("key_result", {
            "success": success,
            "keys": keys
        }))

    async def _handle_shortcut(self, websocket, data):
        """处理快捷键"""
        shortcut_name = data.get("name", "")
        if shortcut_name in SHORTCUTS:
            keys = SHORTCUTS[shortcut_name]
            success = self.keyboard.press_combo(keys)
            await websocket.send(create_message("key_result", {
                "success": success,
                "shortcut": shortcut_name,
                "keys": keys
            }))
        else:
            await websocket.send(create_message("error", {
                "code": 1002,
                "message": f"未知快捷键: {shortcut_name}"
            }))

    async def _handle_voice_start(self, websocket):
        """开始语音传输"""
        print("[语音] 开始接收语音数据")
        self.voice_recording = True
        self.voice_packet_count = 0  # 重置计数器
        if self.audio_player:
            self.audio_player.start()
        await websocket.send(create_message("voice_status", {
            "status": "started"
        }))

    async def _handle_voice_data(self, websocket, data):
        """接收语音数据（实时传输）"""
        if not self.audio_player:
            print("[语音] 音频播放器未初始化，无法播放")
            return
        
        audio_base64 = data.get("audio", "")
        is_last = data.get("isLast", False)
        
        if not audio_base64:
            return
            
        try:
            # 解码 Base64
            audio_bytes = base64.b64decode(audio_base64)
            
            if len(audio_bytes) == 0:
                return
            
            # 如果播放器未启动，重新启动它
            if not self.audio_player.is_playing:
                print("[语音] 实时播放开始")
                self.audio_player.start()
            
            # 添加到播放队列
            self.audio_player.add_audio_data(audio_bytes)
            
            # 计数并打印日志（每20个包打印一次）
            self.voice_packet_count += 1
            if self.voice_packet_count % 20 == 0:
                print(f"[语音] 已接收 {self.voice_packet_count} 个音频包")
            
            # 如果是最后一个数据块，延迟停止播放器
            if is_last:
                await asyncio.sleep(0.5)  # 等待0.5秒让数据播放完
                await self._stop_voice_playback(websocket)
            
        except Exception as e:
            print(f"[语音] 音频数据解码失败: {e}")

    async def _handle_voice_stop(self, websocket):
        """停止语音传输 - 由voice_data在收到isLast时调用"""
        print("[语音] 客户端请求停止录音")
        # 不立即停止，等待voice_data中的isLast标志
        self.voice_recording = False
        await websocket.send(create_message("voice_status", {
            "status": "stopped"
        }))
    
    async def _stop_voice_playback(self, websocket):
        """停止语音播放"""
        print("[语音] 停止语音播放")
        self.voice_recording = False
        if self.audio_player:
            self.audio_player.stop()

    async def ws_handler(self, websocket: websockets.WebSocketServerProtocol):
        """WebSocket 连接处理"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    def get_connected_count(self):
        """获取已连接设备数量"""
        return len(self.clients)

    def on_status_change(self, callback: Callable):
        """注册状态变更回调"""
        self.status_callbacks.append(callback)

    def _notify_status_change(self):
        """通知状态变更"""
        count = self.get_connected_count()
        for callback in self.status_callbacks:
            try:
                callback(count)
            except Exception:
                pass

    async def start(self):
        """启动 WebSocket 服务"""
        print(f"WebSocket 服务启动: ws://{self.host}:{self.port}")
        async with websockets.serve(self.ws_handler, self.host, self.port):
            await asyncio.Future()  # 永久运行

    def run(self):
        """运行服务（阻塞）"""
        asyncio.run(self.start())
