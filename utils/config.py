"""
配置管理模块
"""
import json
import os
import logging
import copy
from threading import Lock
from typing import Dict, List

logger = logging.getLogger(__name__)


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
        'start_minimized': False,
        'minimal_mode': False,  # 极简模式
        'alerts': {
            'enabled': True,
            'sound_enabled': True,
            'popup_enabled': True,
            'enabled_monitors': ['cpu', 'memory'],  # 启用了告警的监控项
            'thresholds': {
                'cpu': {'warning': 70, 'danger': 90},
                'memory': {'warning': 70, 'danger': 90},
                'disk': {'warning': 80, 'danger': 95},
                'gpu': {'warning': 70, 'danger': 90}
            }
        }
    }
    
    def __init__(self):
        self._lock = Lock()
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
                    return self._validate_config(config)
            except json.JSONDecodeError as e:
                logger.warning("配置文件 JSON 解析失败: %s，使用默认配置", e)
            except Exception as e:
                logger.warning("加载配置失败: %s，使用默认配置", e)
        return copy.deepcopy(self.DEFAULT_CONFIG)

    def _validate_config(self, config: Dict) -> Dict:
        """校验配置值的类型和范围，非法值回退到默认值"""
        defaults = self.DEFAULT_CONFIG

        # update_interval: float, 0.5-60
        if not isinstance(config.get('update_interval'), (int, float)):
            config['update_interval'] = defaults['update_interval']
        else:
            config['update_interval'] = max(0.5, min(60, float(config['update_interval'])))

        # theme: 'dark' or 'light'
        if config.get('theme') not in ('dark', 'light'):
            config['theme'] = defaults['theme']

        # boolean fields
        for key in ('window_always_on_top', 'start_minimized', 'minimal_mode'):
            if not isinstance(config.get(key), bool):
                config[key] = defaults.get(key, False)

        # monitors: dict of str -> bool
        monitors = config.get('monitors')
        if not isinstance(monitors, dict):
            config['monitors'] = defaults['monitors'].copy()

        # alerts.thresholds: warning < danger, 0-100
        alerts = config.get('alerts', {})
        if isinstance(alerts, dict):
            thresholds = alerts.get('thresholds', {})
            if isinstance(thresholds, dict):
                for resource in ('cpu', 'memory', 'disk', 'gpu'):
                    rt = thresholds.get(resource, {})
                    dt = defaults['alerts']['thresholds'].get(resource, {'warning': 70, 'danger': 90})
                    if not isinstance(rt, dict):
                        thresholds[resource] = dt
                        continue
                    w = rt.get('warning', dt['warning'])
                    d = rt.get('danger', dt['danger'])
                    if not isinstance(w, (int, float)) or not isinstance(d, (int, float)):
                        thresholds[resource] = dt
                    elif not (0 <= w < d <= 100):
                        thresholds[resource] = dt

        return config
    
    def save_config(self):
        """保存配置"""
        with self._lock:
            try:
                with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error("保存配置失败: %s", e)

    def get(self, key: str, default=None):
        """获取配置项"""
        with self._lock:
            return self.config.get(key, default)

    def set(self, key: str, value):
        """设置配置项"""
        with self._lock:
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
