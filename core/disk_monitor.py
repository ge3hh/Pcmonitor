"""
磁盘监控模块
"""
import psutil
import time
from typing import Dict, List


class DiskMonitor:
    """磁盘监控器"""
    
    def get_disk_partitions(self) -> List[Dict]:
        """获取磁盘分区信息"""
        partitions = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2)
                })
            except:
                pass
        return partitions
    
    def get_disk_io(self) -> Dict:
        """获取磁盘 I/O 统计"""
        io = psutil.disk_io_counters()
        if io:
            return {
                'read_bytes': io.read_bytes,
                'write_bytes': io.write_bytes,
                'read_count': io.read_count,
                'write_count': io.write_count,
                'read_time': io.read_time,
                'write_time': io.write_time
            }
        return {}
    
    def get_disk_stats(self) -> Dict:
        """获取完整磁盘统计"""
        return {
            'partitions': self.get_disk_partitions(),
            'io': self.get_disk_io()
        }
