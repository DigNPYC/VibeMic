from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import qrcode
import io
import json
from utils.helpers import get_local_ip, generate_qr_data
from server.websocket_server import WebSocketServer


class HTTPServer:
    def __init__(self, ws_server: WebSocketServer, host="0.0.0.0", port=8080):
        self.app = FastAPI(title="VibeMic服务端")
        self.host = host
        self.port = port
        self.ws_server = ws_server
        self.local_ip = get_local_ip()

        # 配置 CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/")
        async def root():
            return {
                "name": "VibeMic",
                "version": "1.0.0",
                "status": "running"
            }

        @self.app.get("/api/info")
        async def get_info():
            """获取服务端信息"""
            return {
                "name": "VibeMic",
                "version": "1.0.0",
                "ip": self.local_ip,
                "http_port": self.port,
                "ws_port": self.ws_server.port
            }

        @self.app.get("/api/status")
        async def get_status():
            """获取连接状态"""
            return {
                "connected_count": self.ws_server.get_connected_count(),
                "ip": self.local_ip,
                "ws_port": self.ws_server.port
            }

        @self.app.get("/api/qrcode")
        async def get_qrcode():
            """获取连接二维码"""
            qr_data = generate_qr_data(self.local_ip, self.ws_server.port)

            # 生成二维码图片
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # 转换为字节流
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            return Response(
                content=img_byte_arr.getvalue(),
                media_type="image/png"
            )

        @self.app.get("/api/qrcode/data")
        async def get_qrcode_data():
            """获取二维码原始数据（JSON）"""
            qr_data = generate_qr_data(self.local_ip, self.ws_server.port)
            return json.loads(qr_data)

    def run(self):
        """启动 HTTP 服务"""
        import uvicorn
        print(f"HTTP 服务启动: http://{self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="warning")
