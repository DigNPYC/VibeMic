import socket
import base64
import json


def get_local_ip():
    """获取本机局域网 IP 地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def generate_qr_data(ip, port):
    """生成二维码数据（JSON 格式）"""
    data = {
        "ip": ip,
        "port": port,
        "type": "cyber_ruyi"
    }
    return json.dumps(data)


def create_message(msg_type, data=None):
    """创建标准消息格式"""
    return json.dumps({
        "type": msg_type,
        "data": data or {}
    })


def parse_message(message):
    """解析消息"""
    try:
        return json.loads(message)
    except json.JSONDecodeError:
        return None
