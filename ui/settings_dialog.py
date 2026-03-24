"""
设置对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QComboBox, QCheckBox, QPushButton, QGroupBox, QFormLayout,
    QMessageBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt

from utils import Config, AutoStartManager


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('设置')
        self.setGeometry(200, 200, 450, 400)
        self.setMinimumSize(450, 400)
        
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 常规设置页
        self.general_tab = QWidget()
        self.init_general_tab()
        self.tabs.addTab(self.general_tab, '常规')
        
        # 告警设置页
        self.alert_tab = QWidget()
        self.init_alert_tab()
        self.tabs.addTab(self.alert_tab, '告警')
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton('应用')
        self.apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton('确定')
        self.ok_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # 应用样式
        self.apply_style()
        
    def init_general_tab(self):
        """初始化常规设置页"""
        layout = QVBoxLayout(self.general_tab)
        
        # 更新频率设置
        update_group = QGroupBox('更新设置')
        update_layout = QFormLayout()
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 10)
        self.interval_spin.setSuffix(' 秒')
        update_layout.addRow('更新频率:', self.interval_spin)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        # 主题设置
        theme_group = QGroupBox('外观设置')
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['深色', '浅色'])
        theme_layout.addRow('主题:', self.theme_combo)
        
        self.always_on_top_check = QCheckBox('窗口置顶')
        theme_layout.addRow('', self.always_on_top_check)
        
        self.minimal_mode_check = QCheckBox('极简模式（只显示监控图表）')
        theme_layout.addRow('', self.minimal_mode_check)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # 启动设置
        startup_group = QGroupBox('启动设置')
        startup_layout = QFormLayout()
        
        self.start_minimized_check = QCheckBox('启动时最小化到托盘')
        startup_layout.addRow('', self.start_minimized_check)
        
        self.auto_start_check = QCheckBox('开机自动启动')
        startup_layout.addRow('', self.auto_start_check)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        layout.addStretch()
        
    def init_alert_tab(self):
        """初始化告警设置页"""
        layout = QVBoxLayout(self.alert_tab)
        
        # 告警总开关
        self.alert_enabled_check = QCheckBox('启用告警功能')
        layout.addWidget(self.alert_enabled_check)
        
        # 告警方式
        alert_method_group = QGroupBox('告警方式')
        alert_method_layout = QFormLayout()
        
        self.alert_sound_check = QCheckBox('声音提醒')
        alert_method_layout.addRow('', self.alert_sound_check)
        
        self.alert_popup_check = QCheckBox('弹窗提醒')
        alert_method_layout.addRow('', self.alert_popup_check)
        
        alert_method_group.setLayout(alert_method_layout)
        layout.addWidget(alert_method_group)
        
        # 监控项选择
        alert_monitors_group = QGroupBox('启用告警的监控项')
        alert_monitors_layout = QFormLayout()
        
        self.alert_cpu_check = QCheckBox('CPU')
        alert_monitors_layout.addRow('', self.alert_cpu_check)
        
        self.alert_memory_check = QCheckBox('内存')
        alert_monitors_layout.addRow('', self.alert_memory_check)
        
        self.alert_disk_check = QCheckBox('磁盘')
        alert_monitors_layout.addRow('', self.alert_disk_check)
        
        self.alert_gpu_check = QCheckBox('GPU')
        alert_monitors_layout.addRow('', self.alert_gpu_check)
        
        alert_monitors_group.setLayout(alert_monitors_layout)
        layout.addWidget(alert_monitors_group)
        
        # 阈值设置
        thresholds_group = QGroupBox('告警阈值设置 (%)')
        thresholds_layout = QFormLayout()
        
        # CPU 阈值
        cpu_threshold_layout = QHBoxLayout()
        self.cpu_warning_spin = QSpinBox()
        self.cpu_warning_spin.setRange(10, 100)
        self.cpu_warning_spin.setSuffix('%')
        cpu_threshold_layout.addWidget(QLabel('警告:'))
        cpu_threshold_layout.addWidget(self.cpu_warning_spin)
        cpu_threshold_layout.addSpacing(20)
        self.cpu_danger_spin = QSpinBox()
        self.cpu_danger_spin.setRange(10, 100)
        self.cpu_danger_spin.setSuffix('%')
        cpu_threshold_layout.addWidget(QLabel('危险:'))
        cpu_threshold_layout.addWidget(self.cpu_danger_spin)
        cpu_threshold_layout.addStretch()
        thresholds_layout.addRow('CPU:', cpu_threshold_layout)
        
        # 内存阈值
        mem_threshold_layout = QHBoxLayout()
        self.mem_warning_spin = QSpinBox()
        self.mem_warning_spin.setRange(10, 100)
        self.mem_warning_spin.setSuffix('%')
        mem_threshold_layout.addWidget(QLabel('警告:'))
        mem_threshold_layout.addWidget(self.mem_warning_spin)
        mem_threshold_layout.addSpacing(20)
        self.mem_danger_spin = QSpinBox()
        self.mem_danger_spin.setRange(10, 100)
        self.mem_danger_spin.setSuffix('%')
        mem_threshold_layout.addWidget(QLabel('危险:'))
        mem_threshold_layout.addWidget(self.mem_danger_spin)
        mem_threshold_layout.addStretch()
        thresholds_layout.addRow('内存:', mem_threshold_layout)
        
        # 磁盘阈值
        disk_threshold_layout = QHBoxLayout()
        self.disk_warning_spin = QSpinBox()
        self.disk_warning_spin.setRange(10, 100)
        self.disk_warning_spin.setSuffix('%')
        disk_threshold_layout.addWidget(QLabel('警告:'))
        disk_threshold_layout.addWidget(self.disk_warning_spin)
        disk_threshold_layout.addSpacing(20)
        self.disk_danger_spin = QSpinBox()
        self.disk_danger_spin.setRange(10, 100)
        self.disk_danger_spin.setSuffix('%')
        disk_threshold_layout.addWidget(QLabel('危险:'))
        disk_threshold_layout.addWidget(self.disk_danger_spin)
        disk_threshold_layout.addStretch()
        thresholds_layout.addRow('磁盘:', disk_threshold_layout)

        # GPU 阈值
        gpu_threshold_layout = QHBoxLayout()
        self.gpu_warning_spin = QSpinBox()
        self.gpu_warning_spin.setRange(10, 100)
        self.gpu_warning_spin.setSuffix('%')
        gpu_threshold_layout.addWidget(QLabel('警告:'))
        gpu_threshold_layout.addWidget(self.gpu_warning_spin)
        gpu_threshold_layout.addSpacing(20)
        self.gpu_danger_spin = QSpinBox()
        self.gpu_danger_spin.setRange(10, 100)
        self.gpu_danger_spin.setSuffix('%')
        gpu_threshold_layout.addWidget(QLabel('危险:'))
        gpu_threshold_layout.addWidget(self.gpu_danger_spin)
        gpu_threshold_layout.addStretch()
        thresholds_layout.addRow('GPU:', gpu_threshold_layout)

        thresholds_group.setLayout(thresholds_layout)
        layout.addWidget(thresholds_group)
        
        layout.addStretch()
        
    def apply_style(self):
        """应用样式"""
        theme = self.config.get('theme', 'dark')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QDialog {
                    background-color: #1E1E1E;
                }
                QTabWidget::pane {
                    border: 1px solid #3D3D3D;
                    background-color: #1E1E1E;
                }
                QTabBar::tab {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                    padding: 8px 20px;
                    border: 1px solid #3D3D3D;
                }
                QTabBar::tab:selected {
                    background-color: #2196F3;
                }
                QGroupBox {
                    color: #FFFFFF;
                    font-weight: bold;
                    border: 1px solid #3D3D3D;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QLabel {
                    color: #FFFFFF;
                }
                QSpinBox, QComboBox {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                    border: 1px solid #3D3D3D;
                    padding: 5px;
                    border-radius: 3px;
                }
                QCheckBox {
                    color: #FFFFFF;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QPushButton {
                    background-color: #2196F3;
                    color: #FFFFFF;
                    border: none;
                    padding: 8px 20px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #F5F5F5;
                }
                QTabWidget::pane {
                    border: 1px solid #CCCCCC;
                    background-color: #FFFFFF;
                }
                QTabBar::tab {
                    background-color: #E0E0E0;
                    padding: 8px 20px;
                    border: 1px solid #CCCCCC;
                }
                QTabBar::tab:selected {
                    background-color: #2196F3;
                    color: #FFFFFF;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #CCCCCC;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QSpinBox, QComboBox {
                    background-color: #FFFFFF;
                    border: 1px solid #CCCCCC;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton {
                    background-color: #2196F3;
                    color: #FFFFFF;
                    border: none;
                    padding: 8px 20px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
        
    def load_settings(self):
        """加载当前设置"""
        # 更新频率
        interval = self.config.get('update_interval', 1.0)
        self.interval_spin.setValue(int(interval))
        
        # 主题
        theme = self.config.get('theme', 'dark')
        self.theme_combo.setCurrentIndex(0 if theme == 'dark' else 1)
        
        # 窗口置顶
        always_on_top = self.config.get('window_always_on_top', False)
        self.always_on_top_check.setChecked(always_on_top)
        
        # 极简模式
        minimal_mode = self.config.get('minimal_mode', False)
        self.minimal_mode_check.setChecked(minimal_mode)
        
        # 启动最小化
        start_minimized = self.config.get('start_minimized', False)
        self.start_minimized_check.setChecked(start_minimized)
        
        # 开机自启
        auto_start = self.config.get('auto_start', False)
        self.auto_start_check.setChecked(auto_start)
        
        # 告警设置
        alert_config = self.config.get('alerts', {})
        self.alert_enabled_check.setChecked(alert_config.get('enabled', True))
        self.alert_sound_check.setChecked(alert_config.get('sound_enabled', True))
        self.alert_popup_check.setChecked(alert_config.get('popup_enabled', True))
        
        # 告警监控项
        enabled_monitors = alert_config.get('enabled_monitors', ['cpu', 'memory'])
        self.alert_cpu_check.setChecked('cpu' in enabled_monitors)
        self.alert_memory_check.setChecked('memory' in enabled_monitors)
        self.alert_disk_check.setChecked('disk' in enabled_monitors)
        self.alert_gpu_check.setChecked('gpu' in enabled_monitors)
        
        # 阈值设置
        thresholds = alert_config.get('thresholds', {})
        cpu_thresholds = thresholds.get('cpu', {'warning': 70, 'danger': 90})
        self.cpu_warning_spin.setValue(cpu_thresholds.get('warning', 70))
        self.cpu_danger_spin.setValue(cpu_thresholds.get('danger', 90))
        
        mem_thresholds = thresholds.get('memory', {'warning': 70, 'danger': 90})
        self.mem_warning_spin.setValue(mem_thresholds.get('warning', 70))
        self.mem_danger_spin.setValue(mem_thresholds.get('danger', 90))
        
        disk_thresholds = thresholds.get('disk', {'warning': 80, 'danger': 95})
        self.disk_warning_spin.setValue(disk_thresholds.get('warning', 80))
        self.disk_danger_spin.setValue(disk_thresholds.get('danger', 95))

        gpu_thresholds = thresholds.get('gpu', {'warning': 70, 'danger': 90})
        self.gpu_warning_spin.setValue(gpu_thresholds.get('warning', 70))
        self.gpu_danger_spin.setValue(gpu_thresholds.get('danger', 90))
        
    def get_settings(self):
        """获取当前设置值"""
        # 收集启用的告警监控项
        enabled_monitors = []
        if self.alert_cpu_check.isChecked():
            enabled_monitors.append('cpu')
        if self.alert_memory_check.isChecked():
            enabled_monitors.append('memory')
        if self.alert_disk_check.isChecked():
            enabled_monitors.append('disk')
        if self.alert_gpu_check.isChecked():
            enabled_monitors.append('gpu')
        
        return {
            'update_interval': float(self.interval_spin.value()),
            'theme': 'dark' if self.theme_combo.currentIndex() == 0 else 'light',
            'window_always_on_top': self.always_on_top_check.isChecked(),
            'start_minimized': self.start_minimized_check.isChecked(),
            'auto_start': self.auto_start_check.isChecked(),
            'minimal_mode': self.minimal_mode_check.isChecked(),
            'alerts': {
                'enabled': self.alert_enabled_check.isChecked(),
                'sound_enabled': self.alert_sound_check.isChecked(),
                'popup_enabled': self.alert_popup_check.isChecked(),
                'enabled_monitors': enabled_monitors,
                'thresholds': {
                    'cpu': {
                        'warning': self.cpu_warning_spin.value(),
                        'danger': self.cpu_danger_spin.value()
                    },
                    'memory': {
                        'warning': self.mem_warning_spin.value(),
                        'danger': self.mem_danger_spin.value()
                    },
                    'disk': {
                        'warning': self.disk_warning_spin.value(),
                        'danger': self.disk_danger_spin.value()
                    },
                    'gpu': {
                        'warning': self.gpu_warning_spin.value(),
                        'danger': self.gpu_danger_spin.value()
                    }
                }
            }
        }
        
    def validate_thresholds(self) -> bool:
        """校验告警阈值：warning 必须小于 danger"""
        checks = [
            ('CPU', self.cpu_warning_spin.value(), self.cpu_danger_spin.value()),
            ('内存', self.mem_warning_spin.value(), self.mem_danger_spin.value()),
            ('磁盘', self.disk_warning_spin.value(), self.disk_danger_spin.value()),
            ('GPU', self.gpu_warning_spin.value(), self.gpu_danger_spin.value()),
        ]
        errors = []
        for name, warning, danger in checks:
            if warning >= danger:
                errors.append(f'{name}: 警告阈值 ({warning}%) 必须小于危险阈值 ({danger}%)')
        if errors:
            QMessageBox.warning(self, '阈值设置错误', '\n'.join(errors))
            return False
        return True

    def apply_settings(self):
        """应用设置但不关闭对话框"""
        if not self.validate_thresholds():
            return

        settings = self.get_settings()
        
        # 保存配置
        for key, value in settings.items():
            if key != 'alerts':
                self.config.set(key, value)
        
        # 单独保存告警配置
        self.config.set('alerts', settings['alerts'])
        
        # 应用开机自启设置
        self.apply_auto_start(settings.get('auto_start', False), 
                             settings.get('start_minimized', False))
        
        # 通知父窗口应用设置
        if self.parent():
            self.parent().apply_settings_from_dialog(settings)
        
        # 重新应用样式
        self.apply_style()
        
        QMessageBox.information(self, '提示', '设置已应用')
    
    def apply_auto_start(self, enabled: bool, minimized: bool = False):
        """应用开机自启设置"""
        if enabled:
            success = AutoStartManager.enable_auto_start(minimized)
            if not success:
                QMessageBox.warning(self, '警告', '设置开机自启失败，可能需要管理员权限')
        else:
            AutoStartManager.disable_auto_start()
        
    def save_and_close(self):
        """保存设置并关闭"""
        self.apply_settings()
        self.accept()
