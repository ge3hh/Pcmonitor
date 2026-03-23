"""
内存监控模块
"""
import psutil
from typing import Dict


class MemoryMonitor:
    """内存监控器"""
    
    def get_memory_info(self) -> Dict:
        """获取物理内存信息"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'free': mem.free,
            'percent': mem.percent,
            'total_gb': round(mem.total / (1024**3), 2),
            'used_gb': round(mem.used / (1024**3), 2),
            'available_gb': round(mem.available / (1024**3), 2)
        }
    
    def get_swap_info(self) -> Dict:
        """获取交换内存信息"""
        swap = psutil.swap_memory()
        return {
            'total': swap.total,
            'used': swap.used,
            'free': swap.free,
            'percent': swap.percent,
            'total_gb': round(swap.total / (1024**3), 2),
            'used_gb': round(swap.used / (1024**3), 2)
        }
    
    def get_memory_stats(self) -> Dict:
        """获取完整内存统计"""
        return {
            'memory': self.get_memory_info(),
            'swap': self.get_swap_info()
        }
