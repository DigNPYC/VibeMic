"""
音频设备测试工具
用于检查音频输出设备是否正常工作
"""

import numpy as np
import time

print("=" * 50)
print("音频设备测试工具")
print("=" * 50)

# 尝试导入 sounddevice
try:
    import sounddevice as sd
    print("\n[✓] sounddevice 已安装")
    
    # 列出所有音频设备
    print("\n可用的音频输出设备:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            print(f"  {i}: {device['name']} (输出通道: {device['max_output_channels']})")
    
    # 获取默认输出设备
    try:
        default_device = sd.query_devices(kind='output')
        print(f"\n默认输出设备: {default_device['name']}")
    except Exception as e:
        print(f"\n[!] 无法获取默认输出设备: {e}")
    
    # 测试播放正弦波
    print("\n正在测试音频播放...")
    print("你应该能听到 1 秒钟的蜂鸣声")
    
    # 生成 1 秒 1000Hz 正弦波
    sample_rate = 16000
    duration = 1  # 秒
    frequency = 1000  # Hz
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(frequency * 2 * np.pi * t)
    
    # 转换为 16 位整数
    audio = (tone * 32767).astype(np.int16)
    
    try:
        sd.play(audio, sample_rate)
        sd.wait()
        print("[✓] 音频播放测试成功！")
    except Exception as e:
        print(f"[✗] 音频播放失败: {e}")
        
except ImportError:
    print("\n[✗] sounddevice 未安装")
    print("请运行: pip install sounddevice")

print("\n" + "=" * 50)
print("测试完成")
print("=" * 50)

input("\n按回车键退出...")
