"""
检查 VB-Cable 音量设置
"""
import subprocess
import sys

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    
    # 获取所有音频设备
    devices = AudioUtilities.GetAllDevices()
    
    print("=" * 60)
    print("VB-Cable 音量检查")
    print("=" * 60)
    
    for device in devices:
        if 'cable' in device.FriendlyName.lower():
            print(f"\n设备: {device.FriendlyName}")
            try:
                # 获取音量控制
                interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                # 获取当前音量
                current_volume = volume.GetMasterVolumeLevelScalar()
                print(f"  当前音量: {current_volume * 100:.0f}%")
                
                # 是否静音
                is_muted = volume.GetMute()
                print(f"  是否静音: {'是' if is_muted else '否'}")
                
                # 音量范围
                vol_range = volume.GetVolumeRange()
                print(f"  音量范围: {vol_range[0]}dB 到 {vol_range[1]}dB")
                
            except Exception as e:
                print(f"  无法获取音量信息: {e}")
    
    print("\n" + "=" * 60)
    print("提示: 如果音量为0%或被静音，请调整音量")
    print("=" * 60)
    
except ImportError:
    print("请先安装 pycaw: pip install pycaw")
    
input("\n按回车键退出...")
