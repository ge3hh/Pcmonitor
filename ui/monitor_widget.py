"""
监控小组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class MonitorWidget(QWidget):
    """监控显示组件"""
    
    def __init__(self, title: str, value_callback, height: int = 100):
        super().__init__()
        self.title = title
        self.value_callback = value_callback
        self.init_ui(height)
        
    def init_ui(self, height: int):
        """初始化 UI"""
        self.setMinimumHeight(height)
        self.setMaximumHeight(height + 50)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        layout.addWidget(self.title_label)
        
        # 数值显示
        self.value_label = QLabel('N/A')
        self.value_label.setStyleSheet('font-size: 24px; font-weight: bold; color: #2196F3;')
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # 设置样式
        self.setStyleSheet("""
            MonitorWidget {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #3D3D3D;
            }
        """)
        
    def update_display(self):
        """更新显示"""
        try:
            value = self.value_callback()
            self.value_label.setText(value)
        except Exception as e:
            self.value_label.setText('Error')
