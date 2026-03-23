"""
主窗口 UI
"""
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QPushButton, QGridLayout,
    QSystemTrayIcon, QMenu, QAction, QApplication
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

from core import CPUMonitor, MemoryMonitor, DiskMonitor, NetworkMonitor, GPUMonitor
from utils import Config
from .monitor_widget import MonitorWidget


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.init_monitors()
        self.init_ui()
        self.init_timer()
        self.init_tray()
        
    def init_monitors(self):
        """初始化监控器"""
        self.monitors = {
            'cpu': CPUMonitor(),
            'memory': MemoryMonitor(),
            'disk': DiskMonitor(),
            'network': NetworkMonitor(),
            'gpu': GPUMonitor()
        }
        
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('Pcmonitor - 系统资源监控')
        self.setGeometry(100, 100, 900, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 监控选择区域
        self.create_monitor_selection(main_layout)
        
        # 监控面板区域
        self.create_monitor_panels(main_layout)
        
        # 状态栏
        self.status_label = QLabel('就绪')
        main_layout.addWidget(self.status_label)
        
        # 应用主题
        self.apply_theme()
        
    def create_monitor_selection(self, parent_layout):
        """创建监控选择区域"""
        selection_widget = QWidget()
        selection_layout = QHBoxLayout(selection_widget)
        selection_layout.setContentsMargins(0, 0, 0, 0)
        
        selection_layout.addWidget(QLabel('监控对象:'))
        
        self.monitor_checkboxes = {}
        monitor_names = {
            'cpu': 'CPU',
            'memory': '内存',
            'disk': '磁盘',
            'network': '网络',
            'gpu': 'GPU'
        }
        
        for key, name in monitor_names.items():
            checkbox = QCheckBox(name)
            checkbox.setChecked(self.config.get_monitor_enabled(key))
            checkbox.stateChanged.connect(lambda state, k=key: self.on_monitor_toggled(k, state))
            self.monitor_checkboxes[key] = checkbox
            selection_layout.addWidget(checkbox)
        
        selection_layout.addStretch()
        
        # 设置按钮
        settings_btn = QPushButton('设置')
        settings_btn.clicked.connect(self.show_settings)
        selection_layout.addWidget(settings_btn)
        
        parent_layout.addWidget(selection_widget)
        
    def create_monitor_panels(self, parent_layout):
        """创建监控面板"""
        self.monitor_widgets = {}
        
        # 第一行：CPU、内存、磁盘
        row1_layout = QHBoxLayout()
        
        self.monitor_widgets['cpu'] = MonitorWidget('CPU', self.get_cpu_value)
        row1_layout.addWidget(self.monitor_widgets['cpu'])
        
        self.monitor_widgets['memory'] = MonitorWidget('内存', self.get_memory_value)
        row1_layout.addWidget(self.monitor_widgets['memory'])
        
        self.monitor_widgets['disk'] = MonitorWidget('磁盘', self.get_disk_value)
        row1_layout.addWidget(self.monitor_widgets['disk'])
        
        parent_layout.addLayout(row1_layout)
        
        # 第二行：网络
        self.monitor_widgets['network'] = MonitorWidget('网络', self.get_network_value, height=150)
        parent_layout.addWidget(self.monitor_widgets['network'])
        
        # 第三行：GPU
        self.monitor_widgets['gpu'] = MonitorWidget('GPU', self.get_gpu_value)
        parent_layout.addWidget(self.monitor_widgets['gpu'])
        
        # 更新显示状态
        self.update_monitor_visibility()
        
    def update_monitor_visibility(self):
        """更新监控面板可见性"""
        for key, widget in self.monitor_widgets.items():
            enabled = self.config.get_monitor_enabled(key)
            widget.setVisible(enabled)
            
    def on_monitor_toggled(self, monitor_name: str, state):
        """监控项切换回调"""
        enabled = state == Qt.Checked
        self.config.set_monitor_enabled(monitor_name, enabled)
        self.update_monitor_visibility()
        
    def init_timer(self):
        """初始化定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        interval = int(self.config.get('update_interval', 1.0) * 1000)
        self.timer.start(interval)
        
    def update_data(self):
        """更新数据"""
        for key, widget in self.monitor_widgets.items():
            if self.config.get_monitor_enabled(key):
                widget.update_display()
                
    def get_cpu_value(self) -> str:
        """获取 CPU 显示值"""
        try:
            stats = self.monitors['cpu'].get_cpu_stats()
            return f"{stats['cpu_percent']:.1f}%"
        except:
            return "N/A"
            
    def get_memory_value(self) -> str:
        """获取内存显示值"""
        try:
            stats = self.monitors['memory'].get_memory_stats()
            mem = stats['memory']
            return f"{mem['percent']:.1f}% ({mem['used_gb']:.1f}/{mem['total_gb']:.1f} GB)"
        except:
            return "N/A"
            
    def get_disk_value(self) -> str:
        """获取磁盘显示值"""
        try:
            stats = self.monitors['disk'].get_disk_stats()
            partitions = stats['partitions']
            if partitions:
                total_used = sum(p['used_gb'] for p in partitions)
                total_size = sum(p['total_gb'] for p in partitions)
                percent = (total_used / total_size * 100) if total_size > 0 else 0
                return f"{percent:.1f}% ({total_used:.1f}/{total_size:.1f} GB)"
        except:
            pass
        return "N/A"
        
    def get_network_value(self) -> str:
        """获取网络显示值"""
        try:
            stats = self.monitors['network'].get_network_stats()
            return f"↑ {stats['upload_speed']:.2f} MB/s | ↓ {stats['download_speed']:.2f} MB/s"
        except:
            return "N/A"
            
    def get_gpu_value(self) -> str:
        """获取 GPU 显示值"""
        try:
            stats = self.monitors['gpu'].get_gpu_stats()
            gpus = stats['gpus']
            if gpus:
                gpu = gpus[0]
                return f"{gpu['load']:.1f}% | 显存: {gpu['memory_percent']:.1f}%"
        except:
            pass
        return "N/A"
        
    def init_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip('Pcmonitor')
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction('显示', self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction('隐藏', self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
        
    def on_tray_activated(self, reason):
        """托盘图标点击事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                
    def show_settings(self):
        """显示设置对话框"""
        # TODO: 实现设置对话框
        pass
        
    def apply_theme(self):
        """应用主题"""
        theme = self.config.get('theme', 'dark')
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1E1E1E;
                }
                QWidget {
                    background-color: #1E1E1E;
                    color: #FFFFFF;
                }
                QLabel {
                    color: #FFFFFF;
                }
                QCheckBox {
                    color: #FFFFFF;
                }
                QPushButton {
                    background-color: #2196F3;
                    color: #FFFFFF;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
        
    def quit_app(self):
        """退出应用"""
        self.tray_icon.hide()
        QApplication.quit()
        
    def closeEvent(self, event):
        """关闭事件"""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()
