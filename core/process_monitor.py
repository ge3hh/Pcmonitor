"""
进程监控模块
"""
import psutil
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ProcessInfo:
    """进程信息数据类"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    username: Optional[str]
    create_time: Optional[float]
    

class ProcessMonitor:
    """进程监控器"""
    
    def __init__(self):
        self._last_cpu_times = {}
        
    def get_process_list(self, sort_by: str = 'cpu', limit: int = 100) -> List[ProcessInfo]:
        """
        获取进程列表
        
        Args:
            sort_by: 排序字段 ('cpu', 'memory', 'pid', 'name')
            limit: 返回的最大进程数
            
        Returns:
            进程信息列表
        """
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'memory_info', 'status', 'username', 'create_time']):
            try:
                pinfo = proc.info
                
                # 计算内存使用 (MB)
                memory_mb = 0
                if pinfo.get('memory_info'):
                    memory_mb = pinfo['memory_info'].rss / (1024 * 1024)
                
                process_info = ProcessInfo(
                    pid=pinfo['pid'],
                    name=pinfo['name'] or 'Unknown',
                    cpu_percent=pinfo['cpu_percent'] or 0.0,
                    memory_percent=pinfo['memory_percent'] or 0.0,
                    memory_mb=round(memory_mb, 2),
                    status=pinfo['status'] or 'unknown',
                    username=pinfo.get('username'),
                    create_time=pinfo.get('create_time')
                )
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # 排序
        if sort_by == 'cpu':
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        elif sort_by == 'memory':
            processes.sort(key=lambda x: x.memory_percent, reverse=True)
        elif sort_by == 'pid':
            processes.sort(key=lambda x: x.pid)
        elif sort_by == 'name':
            processes.sort(key=lambda x: x.name.lower())
        
        return processes[:limit]
    
    def kill_process(self, pid: int) -> bool:
        """
        结束指定进程
        
        Args:
            pid: 进程 ID
            
        Returns:
            是否成功结束
        """
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            
            # 等待进程结束，超时则强制结束
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
                
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
    
    def get_process_details(self, pid: int) -> Optional[Dict]:
        """
        获取进程详细信息
        
        Args:
            pid: 进程 ID
            
        Returns:
            进程详细信息字典
        """
        try:
            proc = psutil.Process(pid)
            
            # 基础信息
            details = {
                'pid': pid,
                'name': proc.name(),
                'exe': proc.exe(),
                'cmdline': ' '.join(proc.cmdline()),
                'status': proc.status(),
                'create_time': proc.create_time(),
                'username': proc.username(),
            }
            
            # CPU 信息
            with proc.oneshot():
                details['cpu_percent'] = proc.cpu_percent(interval=0.1)
                details['cpu_times'] = proc.cpu_times()._asdict()
                details['num_threads'] = proc.num_threads()
                
                # 内存信息
                memory_info = proc.memory_info()._asdict()
                details['memory'] = {
                    'rss_mb': round(memory_info['rss'] / (1024 * 1024), 2),
                    'vms_mb': round(memory_info['vms'] / (1024 * 1024), 2),
                    'percent': proc.memory_percent()
                }
                
                # I/O 信息
                try:
                    io_counters = proc.io_counters()._asdict()
                    details['io'] = {
                        'read_mb': round(io_counters['read_bytes'] / (1024 * 1024), 2),
                        'write_mb': round(io_counters['write_bytes'] / (1024 * 1024), 2)
                    }
                except (psutil.AccessDenied, AttributeError):
                    details['io'] = None
                
                # 网络连接
                try:
                    connections = proc.connections()
                    details['connections'] = len(connections)
                except (psutil.AccessDenied, AttributeError):
                    details['connections'] = 0
            
            return details
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def search_processes(self, keyword: str) -> List[ProcessInfo]:
        """
        搜索进程
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的进程列表
        """
        all_processes = self.get_process_list(sort_by='cpu', limit=1000)
        keyword_lower = keyword.lower()
        
        return [
            p for p in all_processes 
            if keyword_lower in p.name.lower() 
            or keyword_lower in str(p.pid)
        ]
