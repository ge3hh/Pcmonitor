"""
配置管理模块
"""
import json
import os
from typing import Dict, List


class Config:
    """配置管理器"""
    
    CONFIG_FILE = 'config.json'
    
    DEFAULT_CONFIG = {
        'monitors': {
            'cpu': True,
            'memory': True,
            'disk': True,
            'network': True,
            'gpu': False
        },
        'update_interval': 1.0,
        'theme': 'dark',
        'window_always_on_top': False,
        'start_minimized': False
    }
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in self.DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                pass
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置项"""
        self.config[key] = value
        self.save_config()
    
    def get_monitor_enabled(self, monitor_name: str) -> bool:
        """获取监控项是否启用"""
        monitors = self.config.get('monitors', {})
        return monitors.get(monitor_name, False)
    
    def set_monitor_enabled(self, monitor_name: str, enabled: bool):
        """设置监控项启用状态"""
        if 'monitors' not in self.config:
            self.config['monitors'] = {}
        self.config['monitors'][monitor_name] = enabled
        self.save_config()
    
    def get_enabled_monitors(self) -> List[str]:
        """获取所有启用的监控项"""
        monitors = self.config.get('monitors', {})
        return [name for name, enabled in monitors.items() if enabled]
