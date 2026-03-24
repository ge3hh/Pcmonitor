"""
主窗口 UI
"""
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QPushButton, QGridLayout,
    QSystemTrayIcon, QMenu, QAction, QApplication, QStyle
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon

from core import CPUMonitor, MemoryMonitor, DiskMonitor, NetworkMonitor, GPUMonitor, DataCollector
from utils import Config, AlertManager
from utils.database import HistoryDatabase
from .monitor_widget import MonitorWidget
from .gauge_widget import GaugeWidget, MinimalModeWidget
from .process_dialog import ProcessDialog
from .settings_dialog import SettingsDialog
from .history_dialog import HistoryDialog


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.init_monitors()
        self.init_ui()
        self.init_timer()
        self.init_tray()
        
        # 检查是否是最小化启动
        if self.config.get('start_minimized', False):
            self.hide()
        
    def init_monitors(self):
        """初始化监控器"""
        self.db = HistoryDatabase()
        self.alert_manager = AlertManager(self.config)
        # 连接告警信号
        self.alert_manager.alert_triggered.connect(self.on_alert_triggered)
        self.alert_manager.popup_requested.connect(self.on_alert_popup_requested)
        
        # 初始化异步数据收集器
        enabled_monitors = self.config.get_enabled_monitors()
        interval = self.config.get('update_interval', 1.0)
        self.data_collector = DataCollector(enabled_monitors, interval)
        self.data_collector.data_collected.connect(self.on_data_collected)
        
        # 为兼容性保留监控器实例（用于进程管理等功能）
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
        

        
        # 监控选择区域（极简模式下可隐藏）
        self.selection_widget = self.create_monitor_selection(main_layout)
        
        # 监控面板区域（正常模式）
        self.monitor_panels_widget = QWidget()
        self.monitor_panels_layout = QVBoxLayout(self.monitor_panels_widget)
        self.monitor_panels_layout.setContentsMargins(0, 0, 0, 0)
        self.create_monitor_panels(self.monitor_panels_layout)
        main_layout.addWidget(self.monitor_panels_widget)
        
        # 极简模式容器（初始隐藏）
        self.minimal_widget = MinimalModeWidget()
        self.minimal_widget.setVisible(False)
        main_layout.addWidget(self.minimal_widget, alignment=Qt.AlignCenter)
        
        # 状态栏（极简模式下可隐藏）
        self.status_label = QLabel('就绪')
        main_layout.addWidget(self.status_label)
        
        # 应用主题
        self.apply_theme()
        
        # 应用极简模式
        self.apply_minimal_mode(self.config.get('minimal_mode', False))
        
    def create_monitor_selection(self, parent_layout):
        """创建监控选择区域"""
        selection_widget = QWidget()
        selection_layout = QHBoxLayout(selection_widget)
        selection_layout.setContentsMargins(0, 0, 0, 0)
        
        # 极简模式切换按钮（普通模式下显示，完全透明）
        self.normal_mode_btn = QPushButton('≡')
        self.normal_mode_btn.setFixedSize(28, 28)
        self.normal_mode_btn.setToolTip('切换极简模式')
        self.normal_mode_btn.setCursor(Qt.PointingHandCursor)
        self.normal_mode_btn.clicked.connect(self.toggle_minimal_mode)
        selection_layout.addWidget(self.normal_mode_btn)
        
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
        
        # 进程管理按钮
        process_btn = QPushButton('进程管理')
        process_btn.clicked.connect(self.show_process_manager)
        selection_layout.addWidget(process_btn)
        
        # 历史数据按钮
        history_btn = QPushButton('历史数据')
        history_btn.clicked.connect(self.show_history)
        selection_layout.addWidget(history_btn)
        
        # 设置按钮
        settings_btn = QPushButton('设置')
        settings_btn.clicked.connect(self.show_settings)
        selection_layout.addWidget(settings_btn)
        
        parent_layout.addWidget(selection_widget)
        return selection_widget
        
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
        
        # 第二行：网络（使用 data_callback 提供图表数据，将速率映射到 0-100）
        self.monitor_widgets['network'] = MonitorWidget(
            '网络', self.get_network_value,
            data_callback=self.get_network_chart_value, height=150
        )
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
        
        # 极简模式下需要重新创建仪表盘
        if getattr(self, 'is_minimal_mode', False):
            self._create_gauges()
            # 重新调整窗口大小
            enabled_count = len(self.config.get_enabled_monitors())
            gauge_width = 150
            window_width = max(400, enabled_count * gauge_width + 50)
            self.resize(window_width, 220)
        
    def init_timer(self):
        """初始化定时器"""
        # 启动数据收集线程
        self.data_collector.start()
        
        # UI 刷新定时器（降低频率到 500ms 一次，实际数据由线程提供）
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(500)  # 500ms 刷新一次 UI
        
        # 保存历史数据的定时器（每 5 秒一次）
        self.history_timer = QTimer()
        self.history_timer.timeout.connect(self.save_history_data)
        self.history_timer.start(5000)  # 5 秒保存一次
        
    def on_data_collected(self, data: dict):
        """数据收集线程返回数据的槽函数"""
        self.latest_data = data
        
        # 检查告警
        if 'values' in data:
            self.alert_manager.check_all_monitors(data['values'], self)
    
    def update_ui(self):
        """更新 UI 显示"""
        if not hasattr(self, 'latest_data'):
            return
        
        # 极简模式：更新仪表盘
        if getattr(self, 'is_minimal_mode', False):
            self.minimal_widget.update_gauges()
            return
        
        # 正常模式：更新监控面板
        data = self.latest_data
        stats = data.get('stats', {})
        values = data.get('values', {})
        
        # 更新 CPU 显示
        if 'cpu' in values and self.config.get_monitor_enabled('cpu'):
            self.monitor_widgets['cpu'].update_display()
        
        # 更新内存显示
        if 'memory' in values and self.config.get_monitor_enabled('memory'):
            self.monitor_widgets['memory'].update_display()
        
        # 更新磁盘显示
        if 'disk' in values and self.config.get_monitor_enabled('disk'):
            self.monitor_widgets['disk'].update_display()
        
        # 更新网络显示
        if self.config.get_monitor_enabled('network'):
            self.monitor_widgets['network'].update_display()
        
        # 更新 GPU 显示
        if self.config.get_monitor_enabled('gpu'):
            self.monitor_widgets['gpu'].update_display()
        
    def save_history_data(self):
        """保存历史数据到数据库"""
        try:
            if not hasattr(self, 'latest_data'):
                return
            
            data = self.latest_data
            stats = data.get('stats', {})
            values = data.get('values', {})
            
            # 从缓存的数据中提取
            cpu_stats = stats.get('cpu', {})
            memory_stats = stats.get('memory', {})
            mem_info = memory_stats.get('memory', {})
            network_stats = stats.get('network', {})
            gpu_stats = stats.get('gpu', {})
            gpus = gpu_stats.get('gpus', [])
            
            if gpus:
                gpu_percent = gpus[0].get('load', 0)
                gpu_memory_percent = gpus[0].get('memory_percent', 0)
            else:
                gpu_percent = 0
                gpu_memory_percent = 0
            
            # 构造数据字典
            db_data = {
                'cpu_percent': cpu_stats.get('cpu_percent', 0),
                'memory_percent': mem_info.get('percent', 0),
                'memory_used_gb': mem_info.get('used_gb', 0),
                'disk_percent': values.get('disk', 0),
                'disk_read_mb': values.get('disk_read_mb', 0),
                'disk_write_mb': values.get('disk_write_mb', 0),
                'network_up_mb': values.get('network_up', 0),
                'network_down_mb': values.get('network_down', 0),
                'gpu_percent': gpu_percent,
                'gpu_memory_percent': gpu_memory_percent
            }
            
            self.db.insert_record(db_data)
            
        except Exception as e:
            # 记录失败不中断程序
            pass
                
    def get_cpu_value(self) -> str:
        """获取 CPU 显示值"""
        try:
            if hasattr(self, 'latest_data'):
                values = self.latest_data.get('values', {})
                return f"{values.get('cpu', 0):.1f}%"
            # 备用方案：直接采集
            stats = self.monitors['cpu'].get_cpu_stats()
            return f"{stats['cpu_percent']:.1f}%"
        except Exception:
            return "N/A"
            
    def get_memory_value(self) -> str:
        """获取内存显示值"""
        try:
            if hasattr(self, 'latest_data'):
                stats = self.latest_data.get('stats', {})
                mem_stats = stats.get('memory', {})
                mem = mem_stats.get('memory', {})
                return f"{mem.get('percent', 0):.1f}% ({mem.get('used_gb', 0):.1f}/{mem.get('total_gb', 0):.1f} GB)"
            # 备用方案：直接采集
            stats = self.monitors['memory'].get_memory_stats()
            mem = stats['memory']
            return f"{mem['percent']:.1f}% ({mem['used_gb']:.1f}/{mem['total_gb']:.1f} GB)"
        except Exception:
            return "N/A"
            
    def get_disk_value(self) -> str:
        """获取磁盘显示值"""
        try:
            if hasattr(self, 'latest_data'):
                stats = self.latest_data.get('stats', {})
                disk_stats = stats.get('disk', {})
                partitions = disk_stats.get('partitions', [])
                values = self.latest_data.get('values', {})
                percent = values.get('disk', 0)
                if partitions:
                    total_used = sum(p['used_gb'] for p in partitions)
                    total_size = sum(p['total_gb'] for p in partitions)
                    return f"{percent:.1f}% ({total_used:.1f}/{total_size:.1f} GB)"
            # 备用方案：直接采集
            stats = self.monitors['disk'].get_disk_stats()
            partitions = stats['partitions']
            if partitions:
                total_used = sum(p['used_gb'] for p in partitions)
                total_size = sum(p['total_gb'] for p in partitions)
                percent = (total_used / total_size * 100) if total_size > 0 else 0
                return f"{percent:.1f}% ({total_used:.1f}/{total_size:.1f} GB)"
        except Exception:
            pass
        return "N/A"
        
    def get_network_value(self) -> str:
        """获取网络显示值"""
        try:
            if hasattr(self, 'latest_data'):
                values = self.latest_data.get('values', {})
                up = values.get('network_up', 0)
                down = values.get('network_down', 0)
                return f"↑ {up:.2f} MB/s | ↓ {down:.2f} MB/s"
            # 备用方案：直接采集
            stats = self.monitors['network'].get_network_stats()
            return f"↑ {stats['upload_speed']:.2f} MB/s | ↓ {stats['download_speed']:.2f} MB/s"
        except Exception:
            return "N/A"

    def get_network_chart_value(self) -> float:
        """获取网络图表数值 (总带宽 MB/s 映射到 0-100)

        使用总带宽 (上传+下载) 并以 100 MB/s 为满量程，
        映射到 0-100 的范围用于图表显示。
        """
        try:
            if hasattr(self, 'latest_data'):
                values = self.latest_data.get('values', {})
                up = values.get('network_up', 0)
                down = values.get('network_down', 0)
                total_mbps = up + down
                # 以 100 MB/s 为满量程映射到 0-100
                return min(100.0, total_mbps / 100.0 * 100.0)
        except Exception:
            pass
        return 0.0
            
    def get_gpu_value(self) -> str:
        """获取 GPU 显示值"""
        try:
            if hasattr(self, 'latest_data'):
                values = self.latest_data.get('values', {})
                load = values.get('gpu', 0)
                mem_percent = values.get('gpu_memory', 0)
                return f"{load:.1f}% | 显存: {mem_percent:.1f}%"
            # 备用方案：直接采集
            stats = self.monitors['gpu'].get_gpu_stats()
            gpus = stats['gpus']
            if gpus:
                gpu = gpus[0]
                return f"{gpu['load']:.1f}% | 显存: {gpu['memory_percent']:.1f}%"
        except Exception:
            pass
        return "N/A"
    
    def apply_minimal_mode(self, enabled: bool):
        """
        应用极简模式
        
        Args:
            enabled: 是否启用极简模式
        """
        self.is_minimal_mode = enabled
        
        if enabled:
            # 极简模式：显示仪表盘，隐藏其他元素
            self.selection_widget.setVisible(False)
            self.status_label.setVisible(False)
            self.monitor_panels_widget.setVisible(False)
            self.minimal_widget.setVisible(True)
            
            # 创建仪表盘
            self._create_gauges()
            
            # 调整窗口大小 - 根据启用的监控项数量计算宽度
            enabled_count = len(self.config.get_enabled_monitors())
            gauge_width = 150  # 每个仪表盘的宽度
            window_width = max(400, enabled_count * gauge_width + 50)
            window_height = 220  # 仪表盘195 + 容器边距4 + 余量21
            
            self.setMinimumSize(400, 210)
            self.setFixedHeight(window_height)
            self.resize(window_width, window_height)
            
        else:
            # 正常模式：显示所有元素
            self.selection_widget.setVisible(True)
            self.status_label.setVisible(True)
            self.monitor_panels_widget.setVisible(True)
            self.minimal_widget.setVisible(False)
            
            # 恢复默认大小
            self.setMinimumSize(600, 400)
            self.setMaximumSize(16777215, 16777215)  # 解除高度限制
            self.resize(900, 600)
    
    def _create_gauges(self):
        """创建仪表盘（极简模式）"""
        # 断开之前的按钮信号（避免重复）
        if hasattr(self.minimal_widget, 'toggle_btn'):
            try:
                self.minimal_widget.toggle_btn.clicked.disconnect()
            except Exception:
                pass
        
        # 清空现有仪表盘
        self.minimal_widget.clear()
        
        # 根据启用的监控项创建仪表盘
        monitor_titles = {
            'cpu': 'CPU',
            'memory': '内存',
            'disk': '磁盘',
            'network': '网络',
            'gpu': 'GPU'
        }
        
        value_callbacks = {
            'cpu': self.get_cpu_value,
            'memory': self.get_memory_value,
            'disk': self.get_disk_value,
            'network': self.get_network_value,
            'gpu': self.get_gpu_value
        }
        
        # 只创建启用的监控项仪表盘
        enabled_monitors = self.config.get_enabled_monitors()
        for key in enabled_monitors:
            if key in monitor_titles:
                self.minimal_widget.add_gauge(
                    key,
                    monitor_titles[key],
                    value_callbacks[key]
                )
        
        # 应用主题
        self.minimal_widget.set_theme(self.config.get('theme', 'dark'))
        
        # 连接切换按钮信号
        if hasattr(self.minimal_widget, 'toggle_btn'):
            self.minimal_widget.toggle_btn.clicked.connect(self.toggle_minimal_mode)
    
    def toggle_minimal_mode(self):
        """切换极简模式"""
        new_state = not self.config.get('minimal_mode', False)
        self.config.set('minimal_mode', new_state)
        self.apply_minimal_mode(new_state)
        
        # 更新按钮状态
        if hasattr(self, 'minimal_mode_btn'):
            self.minimal_mode_btn.setChecked(new_state)
            self.minimal_mode_btn.setStyleSheet(
                'background-color: #4CAF50; border: none;' if new_state else ''
            )
        
        # 同步托盘菜单状态
        if hasattr(self, 'minimal_mode_action'):
            self.minimal_mode_action.setChecked(new_state)
        
    def init_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip('Pcmonitor')
        
        # 使用应用程序图标或系统默认图标
        app_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(app_icon)
        self.setWindowIcon(app_icon)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction('显示', self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction('隐藏', self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # 极简模式切换
        self.minimal_mode_action = QAction('极简模式', self)
        self.minimal_mode_action.setCheckable(True)
        self.minimal_mode_action.setChecked(self.config.get('minimal_mode', False))
        self.minimal_mode_action.triggered.connect(self.toggle_minimal_mode_from_tray)
        tray_menu.addAction(self.minimal_mode_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
        
    def on_tray_activated(self, reason):
        """托盘图标点击事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
    
    def toggle_minimal_mode_from_tray(self, checked: bool):
        """从托盘菜单切换极简模式"""
        self.config.set('minimal_mode', checked)
        self.apply_minimal_mode(checked)
        # 更新托盘菜单状态
        self.minimal_mode_action.setChecked(checked)
                
    def show_process_manager(self):
        """显示进程管理器"""
        dialog = ProcessDialog(self)
        dialog.exec()
        
    def show_history(self):
        """显示历史数据"""
        dialog = HistoryDialog(self)
        dialog.exec()
        
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def apply_settings_from_dialog(self, settings: dict):
        """从设置对话框应用设置"""
        # 应用更新频率
        if 'update_interval' in settings:
            self.data_collector.update_interval(settings['update_interval'])
        
        # 应用主题
        if 'theme' in settings:
            self.apply_theme()
        
        # 应用窗口置顶
        if 'window_always_on_top' in settings:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, settings['window_always_on_top'])
            self.show()  # 重新显示以应用窗口标志
        
        # 应用告警设置
        if 'alerts' in settings:
            alert_config = settings['alerts']
            self.alert_manager.set_alert_enabled(alert_config.get('enabled', True))
            self.alert_manager.set_sound_enabled(alert_config.get('sound_enabled', True))
            self.alert_manager.set_popup_enabled(alert_config.get('popup_enabled', True))
        
        # 应用极简模式
        if 'minimal_mode' in settings:
            self.apply_minimal_mode(settings['minimal_mode'])
        
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
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
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
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """)
        else:
            # 浅色主题
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #F5F5F5;
                }
                QWidget {
                    background-color: #F5F5F5;
                    color: #212121;
                }
                QLabel {
                    color: #212121;
                }
                QCheckBox {
                    color: #212121;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
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
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """)
        
        # 更新所有监控组件的主题
        for widget in self.monitor_widgets.values():
            widget.set_theme(theme)
        
        # 更新仪表盘主题（极简模式）
        if hasattr(self, 'minimal_widget'):
            self.minimal_widget.set_theme(theme)
        
        # 更新普通模式切换按钮样式（完全透明，无边框，文字与背景反色）
        if hasattr(self, 'normal_mode_btn'):
            if theme == 'dark':
                # 深色背景，浅色文字
                self.normal_mode_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #AAAAAA;
                        border: none;
                        border-radius: 4px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 30);
                        color: #FFFFFF;
                    }
                """)
            else:
                # 浅色背景，深色文字
                self.normal_mode_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #666666;
                        border: none;
                        border-radius: 4px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 0, 0, 30);
                        color: #000000;
                    }
                """)
        
    def quit_app(self):
        """退出应用"""
        # 停止数据收集线程
        if hasattr(self, 'data_collector') and self.data_collector.isRunning():
            self.data_collector.stop()
        
        self.tray_icon.hide()
        QApplication.quit()
        
    def on_alert_triggered(self, alert_type: str, message: str):
        """告警触发回调"""
        # 更新状态栏显示告警信息
        self.status_label.setText(f'⚠️ {message}')
        self.status_label.setStyleSheet('color: #FF9800;')

    def on_alert_popup_requested(self, level: str, message: str, title: str):
        """在主线程中安全显示告警弹窗"""
        self.alert_manager.show_alert_popup(level, message, self)
        
    def closeEvent(self, event):
        """关闭事件"""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            # 停止数据收集线程
            if hasattr(self, 'data_collector') and self.data_collector.isRunning():
                self.data_collector.stop()
            event.accept()
