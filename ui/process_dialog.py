"""
进程管理对话框
"""
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QMessageBox, QHeaderView,
    QMenu, QAction, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from core.process_monitor import ProcessMonitor


class ProcessDialog(QDialog):
    """进程管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = ProcessMonitor()
        self.sort_by = 'cpu'
        self.search_keyword = ''
        self.init_ui()
        self.init_timer()
        self.refresh_process_list()
        
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('进程管理')
        self.setGeometry(150, 150, 800, 500)
        
        layout = QVBoxLayout(self)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        # 搜索框
        toolbar_layout.addWidget(QLabel('搜索:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('输入进程名或PID')
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_input)
        
        # 排序选择
        toolbar_layout.addWidget(QLabel('排序:'))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['CPU', '内存', 'PID', '名称'])
        self.sort_combo.setCurrentIndex(0)
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        toolbar_layout.addWidget(self.sort_combo)
        
        toolbar_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self.refresh_process_list)
        toolbar_layout.addWidget(refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 进程表格
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            'PID', '名称', 'CPU %', '内存 %', '内存 (MB)', '状态'
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.process_table.setColumnWidth(0, 80)
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.process_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.process_table)
        
        # 底部状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel('进程数: 0')
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # 结束进程按钮
        kill_btn = QPushButton('结束选中进程')
        kill_btn.setStyleSheet('background-color: #F44336; color: white;')
        kill_btn.clicked.connect(self.kill_selected_process)
        status_layout.addWidget(kill_btn)
        
        layout.addLayout(status_layout)
        
        # 应用样式
        self.apply_style()
        
    def apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3D3D3D;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3D3D3D;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #FFFFFF;
                selection-background-color: #2196F3;
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
        
    def init_timer(self):
        """初始化定时刷新"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_process_list)
        self.refresh_timer.start(2000)  # 每2秒刷新
        
    def on_search_changed(self, text):
        """搜索框内容改变"""
        self.search_keyword = text.strip()
        self.refresh_process_list()
        
    def on_sort_changed(self, text):
        """排序方式改变"""
        sort_map = {
            'CPU': 'cpu',
            '内存': 'memory',
            'PID': 'pid',
            '名称': 'name'
        }
        self.sort_by = sort_map.get(text, 'cpu')
        self.refresh_process_list()
        
    def refresh_process_list(self):
        """刷新进程列表"""
        # 获取进程列表
        if self.search_keyword:
            processes = self.monitor.search_processes(self.search_keyword)
            # 重新排序搜索结果
            if self.sort_by == 'cpu':
                processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            elif self.sort_by == 'memory':
                processes.sort(key=lambda x: x.memory_percent, reverse=True)
            elif self.sort_by == 'pid':
                processes.sort(key=lambda x: x.pid)
            elif self.sort_by == 'name':
                processes.sort(key=lambda x: x.name.lower())
        else:
            processes = self.monitor.get_process_list(sort_by=self.sort_by, limit=100)
        
        # 更新表格
        self.process_table.setRowCount(len(processes))
        
        for i, proc in enumerate(processes):
            # PID
            item = QTableWidgetItem(str(proc.pid))
            item.setData(Qt.UserRole, proc.pid)
            self.process_table.setItem(i, 0, item)
            
            # 名称
            self.process_table.setItem(i, 1, QTableWidgetItem(proc.name))
            
            # CPU %
            cpu_item = QTableWidgetItem(f"{proc.cpu_percent:.1f}")
            cpu_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # CPU 高亮
            if proc.cpu_percent > 50:
                cpu_item.setForeground(QColor('#F44336'))
            elif proc.cpu_percent > 20:
                cpu_item.setForeground(QColor('#FF9800'))
            self.process_table.setItem(i, 2, cpu_item)
            
            # 内存 %
            mem_item = QTableWidgetItem(f"{proc.memory_percent:.1f}")
            mem_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if proc.memory_percent > 10:
                mem_item.setForeground(QColor('#F44336'))
            elif proc.memory_percent > 5:
                mem_item.setForeground(QColor('#FF9800'))
            self.process_table.setItem(i, 3, mem_item)
            
            # 内存 MB
            mem_mb_item = QTableWidgetItem(f"{proc.memory_mb:.1f}")
            mem_mb_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.process_table.setItem(i, 4, mem_mb_item)
            
            # 状态
            self.process_table.setItem(i, 5, QTableWidgetItem(proc.status))
        
        # 更新状态栏 - 显示总进程数
        try:
            import psutil
            total_count = len(psutil.pids())
        except Exception:
            total_count = len(processes)
        if len(processes) < total_count:
            self.status_label.setText(f'显示进程: {len(processes)} / 共 {total_count} 个')
        else:
            self.status_label.setText(f'进程数: {len(processes)}')
        
    def show_context_menu(self, position):
        """显示右键菜单"""
        row = self.process_table.rowAt(position.y())
        if row < 0:
            return
            
        self.process_table.selectRow(row)
        
        menu = QMenu()
        
        # 查看详情
        detail_action = QAction('查看详情', self)
        detail_action.triggered.connect(self.show_process_detail)
        menu.addAction(detail_action)
        
        menu.addSeparator()
        
        # 结束进程
        kill_action = QAction('结束进程', self)
        kill_action.setStyleSheet('color: #F44336;')
        kill_action.triggered.connect(self.kill_selected_process)
        menu.addAction(kill_action)
        
        menu.exec(self.process_table.viewport().mapToGlobal(position))
        
    def show_process_detail(self):
        """显示进程详情"""
        row = self.process_table.currentRow()
        if row < 0:
            return
            
        pid = self.process_table.item(row, 0).data(Qt.UserRole)
        details = self.monitor.get_process_details(pid)
        
        if details:
            info_text = f"""
<b>进程信息</b><br>
名称: {details['name']}<br>
PID: {details['pid']}<br>
路径: {details.get('exe', 'N/A')}<br>
命令行: {details.get('cmdline', 'N/A')}<br>
状态: {details['status']}<br>
用户: {details.get('username', 'N/A')}<br><br>

<b>CPU</b><br>
使用率: {details['cpu_percent']:.1f}%<br>
线程数: {details['num_threads']}<br><br>

<b>内存</b><br>
物理内存: {details['memory']['rss_mb']} MB<br>
虚拟内存: {details['memory']['vms_mb']} MB<br>
使用率: {details['memory']['percent']:.1f}%<br><br>

<b>I/O</b><br>
读取: {details['io']['read_mb'] if details['io'] else 'N/A'} MB<br>
写入: {details['io']['write_mb'] if details['io'] else 'N/A'} MB<br><br>

网络连接: {details['connections']}
"""
            QMessageBox.information(self, f'进程详情 - {details["name"]}', info_text)
        else:
            QMessageBox.warning(self, '错误', '无法获取进程信息')
        
    def kill_selected_process(self):
        """结束选中的进程"""
        row = self.process_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, '提示', '请先选择要结束的进程')
            return
            
        pid = self.process_table.item(row, 0).data(Qt.UserRole)
        name = self.process_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, '确认',
            f'确定要结束进程 "{name}" (PID: {pid}) 吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.monitor.kill_process(pid):
                QMessageBox.information(self, '成功', f'进程 "{name}" 已结束')
                self.refresh_process_list()
            else:
                QMessageBox.critical(self, '失败', f'无法结束进程 "{name}"\n可能需要管理员权限')
                
    def closeEvent(self, event):
        """关闭事件"""
        self.refresh_timer.stop()
        event.accept()
