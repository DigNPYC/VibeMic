"""
虚拟麦克风管理器
自动检测、配置虚拟音频设备，实现手机作为电脑麦克风的功能
"""
import subprocess
import sys
import os
import json
import shutil
from typing import Optional, Dict, List, Tuple
import time

# 尝试导入 sounddevice
try:
    import sounddevice as sd
    SD_AVAILABLE = True
except ImportError:
    SD_AVAILABLE = False
    print("[虚拟麦克风] sounddevice 未安装")


class VirtualMicrophoneManager:
    """虚拟麦克风管理器"""
    
    # 已知的虚拟音频设备名称关键词
    VIRTUAL_DEVICE_KEYWORDS = [
        'cable', 'vb-audio', 'virtual', 'voicemeeter', 'banana', 'potato',
        'vac', 'virtual audio', 'stereo mix', 'what u hear', 'mix',
        'scream', 'sndvol', 'hi-fi', 'line in', 'wave', 'aux'
    ]
    
    # VB-Cable 下载信息
    VBCABLE_DOWNLOAD_URL = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip"
    VBCABLE_INSTALLER_NAME = "VBCABLE_Driver_Pack43.zip"
    
    def __init__(self):
        self.device_info = {
            'output_device': None,   # 用于接收手机音频的输出设备（CABLE Input）
            'input_device': None,    # 用于其他应用的输入设备（CABLE Output）
            'is_virtual': False,     # 是否是虚拟设备
            'device_type': 'unknown' # 设备类型：vbcable, voicemeeter, stereomix, unknown
        }
        self._detect_devices()
    
    def _detect_devices(self) -> bool:
        """检测可用的虚拟音频设备"""
        if not SD_AVAILABLE:
            return False
            
        try:
            devices = sd.query_devices()
            print(f"[虚拟麦克风] 检测到 {len(devices)} 个音频设备")
            print("[虚拟麦克风] 详细设备列表:")
            
            # 先打印所有设备，方便调试
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0 or device['max_input_channels'] > 0:
                    print(f"  ID {i}: {device['name']} [输出:{device['max_output_channels']} 输入:{device['max_input_channels']}]")
            
            # 寻找 VB-Cable Input（接收音频的输出设备）- 我们要把音频发送到这里
            best_device = None
            best_score = 0
            
            for i, device in enumerate(devices):
                name = device['name']
                name_lower = name.lower()
                
                # 必须是输出设备（能播放音频）
                if device['max_output_channels'] == 0:
                    continue
                
                # 评分：找最匹配的 CABLE Input
                score = 0
                if 'cable' in name_lower:
                    score += 10
                if 'input' in name_lower:
                    score += 5
                if 'virtual' in name_lower:
                    score += 3
                # 完整名称匹配加分
                if 'cable input' in name_lower or 'input (vb-audio' in name_lower:
                    score += 10
                    
                if score > best_score:
                    best_score = score
                    best_device = {
                        'id': i,
                        'name': name,
                        'channels': device['max_output_channels'],
                        'score': score
                    }
            
            if best_device:
                self.device_info['output_device'] = best_device
                self.device_info['is_virtual'] = True
                self.device_info['device_type'] = 'vbcable'
                print(f"\n[虚拟麦克风] ✓ 选择最佳输出设备: {best_device['name']} (ID: {best_device['id']}, 评分: {best_device['score']})")
            
            # 查找 VB-Cable Output（作为麦克风输入）
            for i, device in enumerate(devices):
                name_lower = device['name'].lower()
                if 'cable' in name_lower and 'output' in name_lower:
                    if device['max_input_channels'] > 0:
                        self.device_info['input_device'] = {
                            'id': i,
                            'name': device['name'],
                            'channels': device['max_input_channels']
                        }
                        print(f"[虚拟麦克风] ✓ 找到 VB-Cable 输入设备: {device['name']} (ID: {i})")
                        break
            
            # 如果没找到完整的 VB-Cable，查找任何包含 cable 的设备
            if not self.device_info['output_device']:
                for i, device in enumerate(devices):
                    name_lower = device['name'].lower()
                    if 'cable' in name_lower and device['max_output_channels'] > 0:
                        self.device_info['output_device'] = {
                            'id': i,
                            'name': device['name'],
                            'channels': device['max_output_channels']
                        }
                        self.device_info['is_virtual'] = True
                        self.device_info['device_type'] = 'virtual_cable'
                        print(f"[虚拟麦克风] ✓ 找到虚拟线缆设备: {device['name']} (ID: {i})")
                        break
            
            # 查找 Voicemeeter 设备
            if not self.device_info['output_device']:
                for i, device in enumerate(devices):
                    name_lower = device['name'].lower()
                    if 'voicemeeter' in name_lower and device['max_output_channels'] > 0:
                        self.device_info['output_device'] = {
                            'id': i,
                            'name': device['name'],
                            'channels': device['max_output_channels']
                        }
                        self.device_info['is_virtual'] = True
                        self.device_info['device_type'] = 'voicemeeter'
                        print(f"[虚拟麦克风] ✓ 找到 Voicemeeter 设备: {device['name']} (ID: {i})")
                        break
            
            # 查找立体声混音（Stereo Mix）作为备选
            if not self.device_info['output_device']:
                for i, device in enumerate(devices):
                    name_lower = device['name'].lower()
                    if ('stereo mix' in name_lower or 'what u hear' in name_lower) and device['max_output_channels'] > 0:
                        self.device_info['output_device'] = {
                            'id': i,
                            'name': device['name'],
                            'channels': device['max_output_channels']
                        }
                        self.device_info['is_virtual'] = False
                        self.device_info['device_type'] = 'stereomix'
                        print(f"[虚拟麦克风] ⚠ 找到立体声混音设备: {device['name']} (ID: {i})")
                        print("[虚拟麦克风] 注意：立体声混音会录制电脑所有声音，不是最佳方案")
                        break
            
            # 总结检测结果
            if self.device_info['output_device']:
                if self.device_info['is_virtual']:
                    print(f"[虚拟麦克风] ✓ 虚拟麦克风系统已就绪")
                    print(f"[虚拟麦克风] 设备类型: {self.device_info['device_type']}")
                    return True
                else:
                    print(f"[虚拟麦克风] ⚠ 使用立体声混音（不推荐）")
                    return True
            else:
                print(f"[虚拟麦克风] ✗ 未找到虚拟音频设备")
                return False
                
        except Exception as e:
            print(f"[虚拟麦克风] 检测设备时出错: {e}")
            return False
    
    def get_output_device_id(self) -> Optional[int]:
        """获取音频输出设备ID（用于接收手机音频）"""
        if self.device_info['output_device']:
            return self.device_info['output_device']['id']
        return None
    
    def get_input_device_name(self) -> Optional[str]:
        """获取麦克风输入设备名称（供其他应用选择）"""
        if self.device_info['input_device']:
            return self.device_info['input_device']['name']
        # 如果没有独立的输入设备，输出设备通常就是双向的
        if self.device_info['output_device']:
            return self.device_info['output_device']['name'].replace('Input', 'Output')
        return None
    
    def is_virtual_ready(self) -> bool:
        """检查虚拟麦克风是否就绪"""
        return self.device_info['is_virtual'] and self.device_info['output_device'] is not None
    
    def get_setup_guide(self) -> str:
        """获取安装指导"""
        guide = """
╔════════════════════════════════════════════════════════════════╗
║                 虚拟麦克风未检测到                              ║
╚════════════════════════════════════════════════════════════════╝

要让手机作为电脑的麦克风使用，需要安装虚拟音频驱动。

【推荐方案：VB-Cable（免费、轻量、稳定）】

安装步骤：
1. 访问官网下载：https://vb-audio.com/Cable/
2. 下载 VBCABLE_Driver_Packxx.zip
3. 解压后以管理员身份运行 VBCABLE_Setup.exe
4. 安装完成后重启电脑
5. 重新启动本程序

【备选方案：Voicemeeter（功能更强大）】

安装步骤：
1. 访问：https://vb-audio.com/Voicemeeter/
2. 下载并安装 Voicemeeter Banana
3. 安装完成后重启电脑

【安装后的使用】

1. 安装虚拟驱动后，系统会出现：
   - 播放设备：CABLE Input (VB-Audio Virtual Cable)
   - 录音设备：CABLE Output (VB-Audio Virtual Cable)

2. 在麦克风测试网站或应用中：
   - 选择麦克风时选择 "CABLE Output"
   - 这样手机输入的音频就会被识别为麦克风输入

3. 如果要用真实麦克风说话：
   - 切换回真实麦克风设备即可

╔════════════════════════════════════════════════════════════════╗
║  当前状态：音频将通过电脑音响播放                               ║
╚════════════════════════════════════════════════════════════════╝
"""
        return guide
    
    def check_installation_status(self) -> Dict:
        """检查安装状态详情"""
        return {
            'has_virtual_device': self.is_virtual_ready(),
            'device_type': self.device_info['device_type'],
            'output_device': self.device_info['output_device'],
            'input_device': self.device_info['input_device'],
            'can_work_as_mic': self.device_info['output_device'] is not None
        }
    
    def auto_select_best_device(self) -> Tuple[Optional[int], str]:
        """
        自动选择最佳设备
        返回: (device_id, description)
        """
        if self.is_virtual_ready():
            device_id = self.get_output_device_id()
            device_name = self.device_info['output_device']['name']
            return device_id, f"虚拟麦克风: {device_name}"
        elif self.device_info['output_device']:
            device_id = self.get_output_device_id()
            device_name = self.device_info['output_device']['name']
            return device_id, f"音频输出: {device_name} (音响播放)"
        else:
            return None, "未找到音频设备"


# 全局实例
_virtual_mic_manager = None

def get_virtual_mic_manager() -> VirtualMicrophoneManager:
    """获取虚拟麦克风管理器单例"""
    global _virtual_mic_manager
    if _virtual_mic_manager is None:
        _virtual_mic_manager = VirtualMicrophoneManager()
    return _virtual_mic_manager


if __name__ == "__main__":
    # 测试
    manager = VirtualMicrophoneManager()
    print("\n" + "="*60)
    print("设备检测完成")
    print("="*60)
    
    status = manager.check_installation_status()
    print(f"\n状态详情:")
    print(f"  虚拟设备就绪: {status['has_virtual_device']}")
    print(f"  设备类型: {status['device_type']}")
    print(f"  可作为麦克风: {status['can_work_as_mic']}")
    
    if not status['has_virtual_device']:
        print("\n" + manager.get_setup_guide())
