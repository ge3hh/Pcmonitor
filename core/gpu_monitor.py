"""
GPU 监控模块
"""
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GPUMonitor:
    """GPU 监控器"""
    
    def __init__(self):
        self.gputil_available = False
        try:
            import GPUtil
            self.gputil_available = True
        except ImportError:
            pass
    
    def get_gpu_info(self) -> List[Dict]:
        """获取 GPU 信息"""
        gpus = []
        
        if self.gputil_available:
            try:
                import GPUtil
                gpu_list = GPUtil.getGPUs()
                for gpu in gpu_list:
                    gpus.append({
                        'id': gpu.id,
                        'name': gpu.name,
                        'load': round(gpu.load * 100, 2),
                        'memory_total': gpu.memoryTotal,
                        'memory_used': gpu.memoryUsed,
                        'memory_free': gpu.memoryFree,
                        'memory_percent': round((gpu.memoryUsed / gpu.memoryTotal) * 100, 2) if gpu.memoryTotal > 0 else 0,
                        'temperature': gpu.temperature
                    })
            except Exception as e:
                logger.debug("获取 GPU 信息失败: %s", e)
        
        return gpus
    
    def get_gpu_stats(self) -> Dict:
        """获取 GPU 统计信息"""
        gpus = self.get_gpu_info()
        return {
            'gpus': gpus,
            'count': len(gpus),
            'available': self.gputil_available
        }
