"""
CPU 监控模块
"""
import psutil
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CPUMonitor:
    """CPU 监控器"""
    
    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        self.cpu_count_logical = psutil.cpu_count(logical=True)
        
    def get_cpu_percent(self, interval: float = 1.0) -> float:
        """获取总体 CPU 使用率"""
        return psutil.cpu_percent(interval=interval)
    
    def get_cpu_percent_per_core(self, interval: float = 1.0) -> List[float]:
        """获取每个核心的使用率"""
        return psutil.cpu_percent(interval=interval, percpu=True)
    
    def get_cpu_freq(self) -> Optional[Dict]:
        """获取 CPU 频率"""
        try:
            freq = psutil.cpu_freq()
            if freq:
                return {
                    'current': freq.current,
                    'min': freq.min,
                    'max': freq.max
                }
        except Exception as e:
            logger.debug("获取 CPU 频率失败: %s", e)
        return None
    
    def get_cpu_stats(self) -> Dict:
        """获取 CPU 统计信息"""
        return {
            'cpu_count': self.cpu_count,
            'cpu_count_logical': self.cpu_count_logical,
            'cpu_percent': self.get_cpu_percent(interval=0.1),
            'cpu_percent_per_core': self.get_cpu_percent_per_core(interval=0.1),
            'cpu_freq': self.get_cpu_freq()
        }
