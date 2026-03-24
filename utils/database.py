"""
历史数据数据库模块
使用 SQLite 存储监控历史数据
"""
import sqlite3
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from threading import Lock


class HistoryDatabase:
    """历史数据数据库管理器"""
    
    DB_FILE = 'history.db'
    MAX_RETENTION_DAYS = 7  # 保留7天数据
    
    def __init__(self):
        self.lock = Lock()
        self.init_database()
        
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
        
    def init_database(self):
        """初始化数据库"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 创建历史数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_gb REAL,
                    disk_percent REAL,
                    disk_read_mb REAL,
                    disk_write_mb REAL,
                    network_up_mb REAL,
                    network_down_mb REAL,
                    gpu_percent REAL,
                    gpu_memory_percent REAL
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON history(timestamp)
            ''')
            
            conn.commit()
            conn.close()
    
    def insert_record(self, data: Dict):
        """
        插入一条历史记录
        
        Args:
            data: 监控数据字典
        """
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            timestamp = int(time.time())
            
            cursor.execute('''
                INSERT INTO history 
                (timestamp, cpu_percent, memory_percent, memory_used_gb,
                 disk_percent, disk_read_mb, disk_write_mb,
                 network_up_mb, network_down_mb, gpu_percent, gpu_memory_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                data.get('cpu_percent', 0),
                data.get('memory_percent', 0),
                data.get('memory_used_gb', 0),
                data.get('disk_percent', 0),
                data.get('disk_read_mb', 0),
                data.get('disk_write_mb', 0),
                data.get('network_up_mb', 0),
                data.get('network_down_mb', 0),
                data.get('gpu_percent', 0),
                data.get('gpu_memory_percent', 0)
            ))
            
            conn.commit()
            conn.close()
            
            # 清理旧数据
            self._cleanup_old_data()
    
    def _cleanup_old_data(self):
        """清理过期数据"""
        cutoff_time = int(time.time()) - (self.MAX_RETENTION_DAYS * 24 * 3600)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM history WHERE timestamp < ?', (cutoff_time,))
        conn.commit()
        conn.close()
    
    def get_recent_data(self, minutes: int = 60) -> List[Dict]:
        """
        获取最近的数据
        
        Args:
            minutes: 最近多少分钟的数据
            
        Returns:
            历史数据列表
        """
        cutoff_time = int(time.time()) - (minutes * 60)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM history 
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        ''', (cutoff_time,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_data_range(self, start_time: int, end_time: int) -> List[Dict]:
        """
        获取指定时间范围的数据
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            
        Returns:
            历史数据列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM history 
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        ''', (start_time, end_time))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_statistics(self, hours: int = 24) -> Dict:
        """
        获取统计信息
        
        Args:
            hours: 最近多少小时
            
        Returns:
            统计数据字典
        """
        cutoff_time = int(time.time()) - (hours * 3600)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                AVG(network_up_mb) as avg_upload,
                AVG(network_down_mb) as avg_download
            FROM history 
            WHERE timestamp >= ?
        ''', (cutoff_time,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'avg_cpu': round(row['avg_cpu'] or 0, 2),
                'max_cpu': round(row['max_cpu'] or 0, 2),
                'avg_memory': round(row['avg_memory'] or 0, 2),
                'max_memory': round(row['max_memory'] or 0, 2),
                'avg_upload': round(row['avg_upload'] or 0, 2),
                'avg_download': round(row['avg_download'] or 0, 2)
            }
        
        return {
            'avg_cpu': 0, 'max_cpu': 0,
            'avg_memory': 0, 'max_memory': 0,
            'avg_upload': 0, 'avg_download': 0
        }
    
    def export_to_csv(self, filepath: str, start_time: Optional[int] = None, 
                      end_time: Optional[int] = None):
        """
        导出数据到 CSV
        
        Args:
            filepath: CSV 文件路径
            start_time: 开始时间戳 (可选)
            end_time: 结束时间戳 (可选)
        """
        import csv
        
        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = int(time.time())
        
        data = self.get_data_range(start_time, end_time)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
    
    def get_record_count(self) -> int:
        """获取记录总数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM history')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def clear_all_data(self):
        """清空所有数据"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM history')
            conn.commit()
            conn.close()
