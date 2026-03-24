"""
历史数据查看对话框
"""
import time
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
import pyqtgraph as pg

from utils.database import HistoryDatabase


class HistoryDialog(QDialog):
    """历史数据查看对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = HistoryDatabase()
        self.init_ui()
        self.load_statistics()
        self.load_history_data()
        
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('历史数据')
        self.setGeometry(150, 100, 900, 600)
        
        layout = QVBoxLayout(self)
        
        # 统计信息区域
        stats_group = QGroupBox('统计信息 (最近24小时)')
        stats_layout = QFormLayout()
        
        self.avg_cpu_label = QLabel('N/A')
        self.max_cpu_label = QLabel('N/A')
        self.avg_mem_label = QLabel('N/A')
        self.max_mem_label = QLabel('N/A')
        self.avg_upload_label = QLabel('N/A')
        self.avg_download_label = QLabel('N/A')
        
        stats_layout.addRow('平均 CPU:', self.avg_cpu_label)
        stats_layout.addRow('最高 CPU:', self.max_cpu_label)
        stats_layout.addRow('平均内存:', self.avg_mem_label)
        stats_layout.addRow('最高内存:', self.max_mem_label)
        stats_layout.addRow('平均上传:', self.avg_upload_label)
        stats_layout.addRow('平均下载:', self.avg_download_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 图表区域
        chart_layout = QHBoxLayout()

        # CPU 历史图表 (使用时间轴)
        cpu_time_axis = pg.DateAxisItem(orientation='bottom')
        self.cpu_plot = pg.PlotWidget(title='CPU 历史 (%)', axisItems={'bottom': cpu_time_axis})
        self.cpu_plot.setMaximumHeight(150)
        self.cpu_plot.setMenuEnabled(False)
        self.cpu_plot.setMouseEnabled(x=False, y=False)
        self.cpu_plot.hideButtons()
        self.cpu_plot.setBackground('#2D2D2D')
        self.cpu_plot.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_plot.setYRange(0, 100, padding=0)
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen(color='#2196F3', width=2))
        chart_layout.addWidget(self.cpu_plot)

        # 内存历史图表 (使用时间轴)
        mem_time_axis = pg.DateAxisItem(orientation='bottom')
        self.mem_plot = pg.PlotWidget(title='内存历史 (%)', axisItems={'bottom': mem_time_axis})
        self.mem_plot.setMaximumHeight(150)
        self.mem_plot.setMenuEnabled(False)
        self.mem_plot.setMouseEnabled(x=False, y=False)
        self.mem_plot.hideButtons()
        self.mem_plot.setBackground('#2D2D2D')
        self.mem_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mem_plot.setYRange(0, 100, padding=0)
        self.mem_curve = self.mem_plot.plot(pen=pg.mkPen(color='#4CAF50', width=2))
        chart_layout.addWidget(self.mem_plot)
        
        layout.addLayout(chart_layout)
        
        # 数据表格
        table_layout = QHBoxLayout()
        
        # 时间范围选择
        table_layout.addWidget(QLabel('时间范围:'))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(['最近1小时', '最近3小时', '最近6小时', '最近12小时', '最近24小时'])
        self.time_range_combo.currentIndexChanged.connect(self.load_history_data)
        table_layout.addWidget(self.time_range_combo)
        
        table_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self.refresh_data)
        table_layout.addWidget(refresh_btn)
        
        # 导出按钮
        export_btn = QPushButton('导出 CSV')
        export_btn.clicked.connect(self.export_data)
        table_layout.addWidget(export_btn)
        
        layout.addLayout(table_layout)
        
        # 数据表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            '时间', 'CPU %', '内存 %', '内存使用', '磁盘 %', '上传', '下载'
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)
        
        # 关闭按钮
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.apply_style()
        
    def apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
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
            QComboBox {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3D3D3D;
                padding: 5px;
                border-radius: 3px;
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
            QTableWidget {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3D3D3D;
                gridline-color: #3D3D3D;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
            }
            QHeaderView::section {
                background-color: #3D3D3D;
                color: #FFFFFF;
                padding: 5px;
                border: 1px solid #4D4D4D;
            }
        """)
        
    def load_statistics(self):
        """加载统计信息"""
        stats = self.db.get_statistics(hours=24)
        
        self.avg_cpu_label.setText(f"{stats['avg_cpu']}%")
        self.max_cpu_label.setText(f"{stats['max_cpu']}%")
        self.avg_mem_label.setText(f"{stats['avg_memory']}%")
        self.max_mem_label.setText(f"{stats['max_memory']}%")
        self.avg_upload_label.setText(f"{stats['avg_upload']} MB/s")
        self.avg_download_label.setText(f"{stats['avg_download']} MB/s")
        
        # 高亮显示
        if stats['max_cpu'] > 90:
            self.max_cpu_label.setStyleSheet('color: #F44336; font-weight: bold;')
        elif stats['max_cpu'] > 70:
            self.max_cpu_label.setStyleSheet('color: #FF9800; font-weight: bold;')
            
        if stats['max_memory'] > 90:
            self.max_mem_label.setStyleSheet('color: #F44336; font-weight: bold;')
        elif stats['max_memory'] > 70:
            self.max_mem_label.setStyleSheet('color: #FF9800; font-weight: bold;')
        
    def load_history_data(self):
        """加载历史数据到表格和图表"""
        # 获取时间范围
        time_ranges = {
            0: 60,    # 1小时
            1: 180,   # 3小时
            2: 360,   # 6小时
            3: 720,   # 12小时
            4: 1440   # 24小时
        }
        minutes = time_ranges.get(self.time_range_combo.currentIndex(), 60)
        
        # 获取数据
        data = self.db.get_recent_data(minutes=minutes)
        
        # 更新表格
        self.history_table.setRowCount(len(data))
        
        for i, row in enumerate(data):
            # 时间
            dt = datetime.fromtimestamp(row['timestamp'])
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            self.history_table.setItem(i, 0, QTableWidgetItem(time_str))
            
            # CPU
            cpu_item = QTableWidgetItem(f"{row['cpu_percent']:.1f}")
            cpu_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 1, cpu_item)
            
            # 内存
            mem_item = QTableWidgetItem(f"{row['memory_percent']:.1f}")
            mem_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 2, mem_item)
            
            # 内存使用
            mem_used_item = QTableWidgetItem(f"{row['memory_used_gb']:.2f} GB")
            mem_used_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 3, mem_used_item)
            
            # 磁盘
            disk_item = QTableWidgetItem(f"{row['disk_percent']:.1f}")
            disk_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 4, disk_item)
            
            # 上传
            up_item = QTableWidgetItem(f"{row['network_up_mb']:.2f}")
            up_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 5, up_item)
            
            # 下载
            down_item = QTableWidgetItem(f"{row['network_down_mb']:.2f}")
            down_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 6, down_item)
        
        # 更新图表
        if data:
            timestamps = [row['timestamp'] for row in data]
            cpu_data = [row['cpu_percent'] for row in data]
            mem_data = [row['memory_percent'] for row in data]

            self.cpu_curve.setData(timestamps, cpu_data)
            self.mem_curve.setData(timestamps, mem_data)

            # 设置 X 轴范围
            self.cpu_plot.setXRange(timestamps[0], timestamps[-1], padding=0.02)
            self.mem_plot.setXRange(timestamps[0], timestamps[-1], padding=0.02)
        
    def refresh_data(self):
        """刷新数据"""
        self.load_statistics()
        self.load_history_data()
        
    def export_data(self):
        """导出数据到 CSV"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, '导出历史数据', 'history_data.csv', 'CSV 文件 (*.csv)'
        )
        
        if filepath:
            try:
                self.db.export_to_csv(filepath)
                QMessageBox.information(self, '成功', f'数据已导出到:\n{filepath}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'导出失败:\n{str(e)}')
