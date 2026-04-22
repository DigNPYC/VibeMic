import threading
import queue
import numpy as np
import time

# 尝试导入 sounddevice，如果失败则尝试 PyAudio
try:
    import sounddevice as sd
    AUDIO_BACKEND = 'sounddevice'
    print("[音频] 使用 sounddevice 后端")
except ImportError:
    try:
        import pyaudio
        AUDIO_BACKEND = 'pyaudio'
        print("[音频] 使用 PyAudio 后端")
    except ImportError:
        AUDIO_BACKEND = None
        print("[警告] 未找到音频库，语音功能不可用")


class AudioPlayer:
    def __init__(self, sample_rate=16000, channels=1, chunk_size=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        
        # 虚拟设备ID（None表示使用默认设备）
        self.device_id = None
        self.device_name = None
        self.is_virtual_device = False
        
        self.audio_queue = queue.Queue(maxsize=200)
        self.is_playing = False
        self.is_stopping = False
        self.play_thread = None
        self._lock = threading.Lock()
        self._stream = None
        self.total_played = 0

    def set_device(self, device_id: int, device_name: str, is_virtual: bool = False):
        """设置音频输出设备"""
        self.device_id = device_id
        self.device_name = device_name
        self.is_virtual_device = is_virtual
        if is_virtual:
            print(f"[音频] 已配置虚拟麦克风设备: {device_name}")
        else:
            print(f"[音频] 已配置音频设备: {device_name}")

    def start(self):
        """开始音频播放"""
        with self._lock:
            if self.is_playing:
                return
            
            if AUDIO_BACKEND is None:
                print("[音频] 无音频后端，无法播放")
                return
                
            try:
                self.is_playing = True
                self.is_stopping = False
                self.total_played = 0
                self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
                self.play_thread.start()
                
                if self.is_virtual_device:
                    print("[音频] 虚拟麦克风已启动")
                else:
                    print("[音频] 播放已启动")
                    
            except Exception as e:
                print(f"[音频] 播放启动失败: {e}")
                self.is_playing = False

    def stop(self):
        """停止音频播放"""
        with self._lock:
            self.is_stopping = True

        # 等待队列中的数据播放完毕（最多等2秒）
        wait_count = 0
        max_wait = 20
        while wait_count < max_wait:
            if self.audio_queue.empty():
                break
            time.sleep(0.1)
            wait_count += 1

        with self._lock:
            self.is_playing = False
            self.is_stopping = False

        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1)

        # 清空队列
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        # 关闭流
        if self._stream:
            try:
                if AUDIO_BACKEND == 'sounddevice':
                    self._stream.stop()
                    self._stream.close()
                elif AUDIO_BACKEND == 'pyaudio':
                    self._stream.stop_stream()
                    self._stream.close()
            except Exception:
                pass
            self._stream = None

        status = "虚拟麦克风" if self.is_virtual_device else "播放"
        print(f"[音频] {status}已停止")

    def add_audio_data(self, audio_data):
        """添加音频数据到播放队列"""
        if not self.is_playing:
            return

        try:
            self.audio_queue.put_nowait(audio_data)
        except queue.Full:
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put_nowait(audio_data)
            except queue.Empty:
                pass

    def _play_loop(self):
        """音频播放循环"""
        if AUDIO_BACKEND == 'sounddevice':
            self._play_loop_sounddevice()
        elif AUDIO_BACKEND == 'pyaudio':
            self._play_loop_pyaudio()

    def _play_loop_sounddevice(self):
        """使用 sounddevice 播放"""
        import sounddevice as sd
        
        try:
            # 检查设备信息
            if self.device_id is not None:
                try:
                    device_info = sd.query_devices(self.device_id)
                    print(f"[音频] 使用设备: {device_info['name']} (ID: {self.device_id})")
                    print(f"[音频] 设备采样率: {device_info.get('default_samplerate', 'unknown')}")
                except Exception as e:
                    print(f"[音频] 无法获取设备信息: {e}")
            
            # 创建设备配置
            if self.device_id is not None:
                self._stream = sd.RawOutputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=np.int16,
                    blocksize=self.chunk_size,
                    device=self.device_id
                )
            else:
                self._stream = sd.RawOutputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=np.int16,
                    blocksize=self.chunk_size
                )
            
            self._stream.start()
            print(f"[音频] 音频流已启动，采样率: {self.sample_rate}Hz")
            
            empty_count = 0
            
            while self.is_playing:
                try:
                    audio_data = self.audio_queue.get(timeout=0.5)
                    empty_count = 0
                    
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    self._stream.write(audio_array)
                    self.total_played += len(audio_data)
                    
                except queue.Empty:
                    empty_count += 1
                    if self.is_stopping and empty_count > 2:
                        break
                    continue
                except Exception as e:
                    print(f"[音频] 播放错误: {e}")
                    break
                    
        except Exception as e:
            print(f"[音频] 启动失败: {e}")
        finally:
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except:
                    pass
                self._stream = None

    def _play_loop_pyaudio(self):
        """使用 PyAudio 播放"""
        import pyaudio
        
        try:
            audio = pyaudio.PyAudio()
            
            self._stream = audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                output_device_index=self.device_id,
                frames_per_buffer=self.chunk_size
            )
            
            empty_count = 0
            
            while self.is_playing:
                try:
                    audio_data = self.audio_queue.get(timeout=0.5)
                    empty_count = 0
                    self._stream.write(audio_data)
                    self.total_played += len(audio_data)
                except queue.Empty:
                    empty_count += 1
                    if self.is_stopping and empty_count > 2:
                        break
                    continue
                except Exception as e:
                    print(f"[音频] 播放错误: {e}")
                    break
                    
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
            audio.terminate()
        except Exception as e:
            print(f"[音频] 错误: {e}")

    def cleanup(self):
        """清理资源"""
        self.stop()
