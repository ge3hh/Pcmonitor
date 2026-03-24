"""
网络监控模块
"""
import psutil
import time
from typing import Dict, Tuple


class NetworkMonitor:
    """网络监控器"""
    
    def __init__(self):
        self.last_io = None
        self.last_time = None
        
    def get_network_io(self) -> Dict:
        """获取网络 I/O 统计"""
        io = psutil.net_io_counters()
        return {
            'bytes_sent': io.bytes_sent,
            'bytes_recv': io.bytes_recv,
            'packets_sent': io.packets_sent,
            'packets_recv': io.packets_recv,
            'errin': io.errin,
            'errout': io.errout,
            'dropin': io.dropin,
            'dropout': io.dropout
        }
    
    def get_network_speed(self) -> Tuple[float, float]:
        """获取网络速度 (上传, 下载) 单位: MB/s"""
        current_io = self.get_network_io()
        current_time = time.time()
        
        if self.last_io is None or self.last_time is None:
            self.last_io = current_io
            self.last_time = current_time
            time.sleep(1)
            current_io = self.get_network_io()
            current_time = time.time()
        
        time_delta = current_time - self.last_time
        if time_delta <= 0:
            time_delta = 1
            
        upload_speed = (current_io['bytes_sent'] - self.last_io['bytes_sent']) / time_delta / (1024**2)
        download_speed = (current_io['bytes_recv'] - self.last_io['bytes_recv']) / time_delta / (1024**2)
        
        self.last_io = current_io
        self.last_time = current_time
        
        return round(upload_speed, 2), round(download_speed, 2)
    
    def get_network_stats(self) -> Dict:
        """获取完整网络统计"""
        upload_speed, download_speed = self.get_network_speed()
        io_stats = self.get_network_io()
        
        return {
            'upload_speed': upload_speed,
            'download_speed': download_speed,
            'total_sent_mb': round(io_stats['bytes_sent'] / (1024**2), 2),
            'total_recv_mb': round(io_stats['bytes_recv'] / (1024**2), 2),
            'io': io_stats
        }
