"""
告警管理模块
支持阈值告警、弹窗通知、声音提醒
"""
import time
import threading
import winsound
from typing import Dict, Callable, Optional
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject, Signal


class AlertManager(QObject):
    """告警管理器"""
    
    # 告警信号
    alert_triggered = Signal(str, str)  # 告警类型, 告警消息
    popup_requested = Signal(str, str, str)  # 级别, 消息, 标题 (用于在主线程安全显示弹窗)
    
    # 告警级别
    LEVEL_WARNING = 'warning'  # 警告 (>70%)
    LEVEL_DANGER = 'danger'    # 危险 (>90%)
    
    # 默认阈值
    DEFAULT_THRESHOLDS = {
        'cpu': {'warning': 70, 'danger': 90},
        'memory': {'warning': 70, 'danger': 90},
        'disk': {'warning': 80, 'danger': 95},
        'gpu': {'warning': 70, 'danger': 90},
    }
    
    # 冷却时间 (秒) - 防止重复告警
    COOLDOWN_SECONDS = 60
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.last_alert_time = {}  # 记录上次告警时间
        self.alert_enabled = True
        self.sound_enabled = True
        self.popup_enabled = True
        
    def get_threshold(self, monitor_type: str, level: str) -> int:
        """获取阈值
        
        Args:
            monitor_type: 监控类型 (cpu/memory/disk/gpu)
            level: 级别 (warning/danger)
            
        Returns:
            阈值百分比
        """
        alert_config = self.config.get('alerts', {})
        thresholds = alert_config.get('thresholds', self.DEFAULT_THRESHOLDS)
        monitor_thresholds = thresholds.get(monitor_type, self.DEFAULT_THRESHOLDS.get(monitor_type, {}))
        return monitor_thresholds.get(level, 70)
    
    def is_alert_enabled(self, monitor_type: str) -> bool:
        """检查某监控项是否启用了告警"""
        if not self.alert_enabled:
            return False
        alert_config = self.config.get('alerts', {})
        enabled_monitors = alert_config.get('enabled_monitors', ['cpu', 'memory'])
        return monitor_type in enabled_monitors
    
    def check_alert(self, monitor_type: str, value: float) -> Optional[Dict]:
        """检查是否需要告警
        
        Args:
            monitor_type: 监控类型
            value: 当前值 (0-100)
            
        Returns:
            告警信息字典，或 None
        """
        if not self.is_alert_enabled(monitor_type):
            return None
            
        # 检查危险级别
        danger_threshold = self.get_threshold(monitor_type, 'danger')
        if value >= danger_threshold:
            return {
                'type': monitor_type,
                'level': self.LEVEL_DANGER,
                'value': value,
                'threshold': danger_threshold,
                'message': f'{monitor_type.upper()} 使用率过高: {value:.1f}% (危险阈值: {danger_threshold}%)'
            }
        
        # 检查警告级别
        warning_threshold = self.get_threshold(monitor_type, 'warning')
        if value >= warning_threshold:
            return {
                'type': monitor_type,
                'level': self.LEVEL_WARNING,
                'value': value,
                'threshold': warning_threshold,
                'message': f'{monitor_type.upper()} 使用率较高: {value:.1f}% (警告阈值: {warning_threshold}%)'
            }
        
        return None
    
    def should_alert(self, alert_key: str) -> bool:
        """检查是否应该触发告警（考虑冷却时间）"""
        current_time = time.time()
        last_time = self.last_alert_time.get(alert_key, 0)
        
        if current_time - last_time >= self.COOLDOWN_SECONDS:
            self.last_alert_time[alert_key] = current_time
            return True
        return False
    
    def trigger_alert(self, alert_info: Dict, parent_widget=None):
        """触发告警

        Args:
            alert_info: 告警信息字典
            parent_widget: 父窗口，用于显示弹窗
        """
        # 使用资源类型作为冷却 key，避免 warning→danger 切换时重置冷却
        alert_key = alert_info['type']

        # 检查冷却时间
        if not self.should_alert(alert_key):
            return

        level = alert_info['level']
        message = alert_info['message']

        # 发射信号
        self.alert_triggered.emit(alert_info['type'], message)

        # 播放声音
        if self.sound_enabled:
            self.play_alert_sound(level)

        # 通过信号请求弹窗，确保在主线程中安全显示
        if self.popup_enabled:
            title = '⚠️ 资源告警 - 危险' if level == self.LEVEL_DANGER else '⚠️ 资源告警 - 警告'
            self.popup_requested.emit(level, message, title)
    
    def play_alert_sound(self, level: str):
        """播放告警声音"""
        try:
            if level == self.LEVEL_DANGER:
                # 危险级别 - 急促声音
                winsound.MessageBeep(winsound.MB_ICONHAND)
            else:
                # 警告级别 - 普通提示音
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception as e:
            print(f"播放告警声音失败: {e}")
    
    def show_alert_popup(self, level: str, message: str, parent_widget=None):
        """显示告警弹窗 (应通过信号在主线程中调用)"""
        try:
            if level == self.LEVEL_DANGER:
                QMessageBox.critical(parent_widget, '⚠️ 资源告警 - 危险', message)
            else:
                QMessageBox.warning(parent_widget, '⚠️ 资源告警 - 警告', message)
        except Exception as e:
            print(f"显示告警弹窗失败: {e}")
    
    def check_all_monitors(self, data: Dict, parent_widget=None):
        """检查所有监控项
        
        Args:
            data: 监控数据字典，如 {'cpu': 85.5, 'memory': 60.0, ...}
            parent_widget: 父窗口
        """
        for monitor_type, value in data.items():
            if isinstance(value, (int, float)):
                alert_info = self.check_alert(monitor_type, value)
                if alert_info:
                    self.trigger_alert(alert_info, parent_widget)
    
    def set_alert_enabled(self, enabled: bool):
        """设置告警总开关"""
        self.alert_enabled = enabled
    
    def set_sound_enabled(self, enabled: bool):
        """设置声音开关"""
        self.sound_enabled = enabled
    
    def set_popup_enabled(self, enabled: bool):
        """设置弹窗开关"""
        self.popup_enabled = enabled
