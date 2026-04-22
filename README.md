# vibe搭子

一款微信小程序与 Windows 电脑端联动的工具，通过局域网连接，实现手机作为语音输入设备和自定义遥控按键的功能。

## 功能特性

- **语音输入**：将手机作为麦克风，语音实时传输到电脑播放
- **快捷按键**：支持回车、复制、粘贴等常用快捷键
- **按键自定义**：支持添加、编辑、删除自定义按键
- **组合键支持**：支持 Ctrl+C、Ctrl+V 等组合键
- **扫码连接**：通过微信扫码快速连接电脑
- **系统托盘**：最小化到系统托盘，后台运行
- **开机自启**：支持设置开机自动启动

## 项目结构

```
vibe搭子/
├── desktop/              # 电脑端服务端 (Python)
│   ├── main.py           # 程序入口
│   ├── requirements.txt  # Python 依赖
│   ├── server/           # 网络服务
│   ├── keyboard/         # 键盘模拟
│   ├── audio/            # 音频处理
│   ├── tray/             # 系统托盘
│   ├── ui/               # 界面
│   └── utils/            # 工具函数
├── miniprogram/          # 微信小程序
│   ├── pages/            # 页面
│   ├── utils/            # 工具函数
│   ├── app.js            # 小程序入口
│   ├── app.json          # 全局配置
│   └── app.wxss          # 全局样式
└── README.md
```

## 电脑端部署

### 环境要求

- Windows 10/11
- Python 3.8+

### 安装步骤

1. 进入 desktop 目录：
```bash
cd desktop
```

2. 创建虚拟环境（可选但推荐）：
```bash
python -m venv venv
venv\Scripts\activate.bat
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 启动服务端：
```bash
python main.py
```

或者双击运行 `start.bat` 脚本。

### 使用说明

1. 启动程序后，主窗口会显示二维码
2. 使用手机微信扫描小程序码进入小程序
3. 点击「扫码连接」扫描电脑端显示的二维码
4. 连接成功后即可使用手机控制电脑

## 微信小程序部署

1. 微信搜索 VibeMic 小程序

### 注意

- 小程序需要在「详情」→「本地设置」中勾选「不校验合法域名」以进行局域网调试
- 正式使用时需要配置服务器域名

## 通信协议

### WebSocket 消息格式

```json
// 按键指令
{
  "type": "key_press",
  "data": { "key": "enter" }
}

// 组合键指令
{
  "type": "key_combo",
  "data": { "keys": ["ctrl", "c"] }
}

// 快捷键指令
{
  "type": "shortcut",
  "data": { "name": "copy" }
}

// 语音数据
{
  "type": "voice_data",
  "data": { "audio": "base64_encoded_pcm" }
}
```

## 常见问题

1. **无法连接**：请确保手机和电脑在同一局域网内
2. **防火墙拦截**：需要在 Windows 防火墙中允许 Python 程序通过
3. **录音失败**：请确保小程序已获得录音权限
4. **按键无效**：部分程序需要以管理员身份运行

## 技术栈

- **电脑端**：Python + FastAPI + WebSocket + pynput + PyAudio
- **小程序**：微信原生小程序
- **通信**：WebSocket + HTTP REST

## 许可证

MIT License
