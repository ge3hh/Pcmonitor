"""
数据收集器 - 在后台线程中采集系统数据
使用 QThread 避免阻塞主线程
"""
from PySide6.QtCore import QThread, Signal
from typing import Dict, List
import time
import logging

logger = logging.getLogger(__name__)

from .cpu_monitor import CPUMonitor
from .memory_monitor import MemoryMonitor
from .disk_monitor import DiskMonitor
from .network_monitor import NetworkMonitor
from .gpu_monitor import GPUMonitor


class DataCollector(QThread):
    """数据收集线程"""
    
    # 数据收集完成信号
    data_collected = Signal(dict)
    
    def __init__(self, enabled_monitors: List[str], interval: float = 1.0):
        """
        初始化数据收集器
        
        Args:
            enabled_monitors: 启用的监控项列表 ['cpu', 'memory', ...]
            interval: 收集间隔（秒）
        """
        super().__init__()
        self.enabled_monitors = enabled_monitors
        self.interval = interval
        self.running = False
        
        # 初始化监控器
        self.monitors = {}
        if 'cpu' in enabled_monitors:
            self.monitors['cpu'] = CPUMonitor()
        if 'memory' in enabled_monitors:
            self.monitors['memory'] = MemoryMonitor()
        if 'disk' in enabled_monitors:
            self.monitors['disk'] = DiskMonitor()
        if 'network' in enabled_monitors:
            self.monitors['network'] = NetworkMonitor()
        if 'gpu' in enabled_monitors:
            self.monitors['gpu'] = GPUMonitor()
        
        # 缓存数据，用于计算差值
        self.last_network_stats = None
        self.last_disk_io = None
        self.last_disk_io_time = None
        
    def run(self):
        """线程运行循环"""
        self.running = True
        
        while self.running:
            data = self.collect_data()
            self.data_collected.emit(data)
            time.sleep(self.interval)
    
    def collect_data(self) -> Dict:
        """
        采集所有启用的监控数据
        
        Returns:
            包含所有监控数据的字典
        """
        result = {
            'timestamp': time.time(),
            'values': {},
            'stats': {}
        }
        
        # 采集 CPU 数据
        if 'cpu' in self.monitors:
            try:
                stats = self.monitors['cpu'].get_cpu_stats()
                result['stats']['cpu'] = stats
                result['values']['cpu'] = stats['cpu_percent']
            except Exception as e:
                logger.warning("采集 CPU 数据失败: %s", e)
                result['values']['cpu'] = 0
        
        # 采集内存数据
        if 'memory' in self.monitors:
            try:
                stats = self.monitors['memory'].get_memory_stats()
                result['stats']['memory'] = stats
                result['values']['memory'] = stats['memory']['percent']
            except Exception as e:
                logger.warning("采集内存数据失败: %s", e)
                result['values']['memory'] = 0
        
        # 采集磁盘数据
        if 'disk' in self.monitors:
            try:
                stats = self.monitors['disk'].get_disk_stats()
                result['stats']['disk'] = stats
                partitions = stats.get('partitions', [])
                if partitions:
                    total_used = sum(p['used_gb'] for p in partitions)
                    total_size = sum(p['total_gb'] for p in partitions)
                    result['values']['disk'] = (total_used / total_size * 100) if total_size > 0 else 0
                else:
                    result['values']['disk'] = 0
                # 计算磁盘 IO 速率 (MB/s)
                io = stats.get('io', {})
                if io and self.last_disk_io is not None and self.last_disk_io_time is not None:
                    dt = time.time() - self.last_disk_io_time
                    if dt > 0:
                        result['values']['disk_read_mb'] = round(
                            (io['read_bytes'] - self.last_disk_io['read_bytes']) / dt / (1024**2), 2)
                        result['values']['disk_write_mb'] = round(
                            (io['write_bytes'] - self.last_disk_io['write_bytes']) / dt / (1024**2), 2)
                else:
                    result['values']['disk_read_mb'] = 0
                    result['values']['disk_write_mb'] = 0
                if io:
                    self.last_disk_io = io
                    self.last_disk_io_time = time.time()
            except Exception as e:
                logger.warning("采集磁盘数据失败: %s", e)
                result['values']['disk'] = 0
                result['values']['disk_read_mb'] = 0
                result['values']['disk_write_mb'] = 0
        
        # 采集网络数据
        if 'network' in self.monitors:
            try:
                stats = self.monitors['network'].get_network_stats()
                result['stats']['network'] = stats
                result['values']['network_up'] = stats['upload_speed']
                result['values']['network_down'] = stats['download_speed']
            except Exception as e:
                logger.warning("采集网络数据失败: %s", e)
                result['values']['network_up'] = 0
                result['values']['network_down'] = 0
        
        # 采集 GPU 数据
        if 'gpu' in self.monitors:
            try:
                stats = self.monitors['gpu'].get_gpu_stats()
                result['stats']['gpu'] = stats
                gpus = stats.get('gpus', [])
                if gpus:
                    result['values']['gpu'] = gpus[0].get('load', 0)
                    result['values']['gpu_memory'] = gpus[0].get('memory_percent', 0)
                else:
                    result['values']['gpu'] = 0
                    result['values']['gpu_memory'] = 0
            except Exception as e:
                logger.warning("采集 GPU 数据失败: %s", e)
                result['values']['gpu'] = 0
                result['values']['gpu_memory'] = 0
        
        return result
    
    def stop(self):
        """停止数据收集"""
        self.running = False
        self.wait(1000)  # 等待1秒让线程结束
    
    def update_enabled_monitors(self, enabled_monitors: List[str]):
        """更新启用的监控项"""
        self.enabled_monitors = enabled_monitors
        # 重新初始化监控器
        self.monitors = {}
        if 'cpu' in enabled_monitors:
            self.monitors['cpu'] = CPUMonitor()
        if 'memory' in enabled_monitors:
            self.monitors['memory'] = MemoryMonitor()
        if 'disk' in enabled_monitors:
            self.monitors['disk'] = DiskMonitor()
        if 'network' in enabled_monitors:
            self.monitors['network'] = NetworkMonitor()
        if 'gpu' in enabled_monitors:
            self.monitors['gpu'] = GPUMonitor()
    
    def update_interval(self, interval: float):
        """更新收集间隔"""
        self.interval = interval
