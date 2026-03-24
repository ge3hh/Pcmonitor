"""
监控小组件 - 带实时图表
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
import pyqtgraph as pg
from collections import deque


class MonitorWidget(QWidget):
    """监控显示组件 - 带实时图表"""
    
    # 图表配色 - 负载变色（4档）
    COLOR_LOW = '#4CAF50'      # 绿色 - 0-50%
    COLOR_MID = '#FFC107'      # 黄色 - 51-70%
    COLOR_HIGH = '#FF9800'     # 橙色 - 71-90%
    COLOR_CRITICAL = '#F44336' # 红色 - 91-100%
    COLOR_BACKGROUND = '#2D2D2D'
    COLOR_GRID = '#3D3D3D'
    
    def __init__(self, title: str, value_callback, data_callback=None, height: int = 150):
        """
        初始化监控组件
        
        Args:
            title: 监控项标题
            value_callback: 获取显示值的回调函数
            data_callback: 获取图表数值的回调函数 (返回 0-100 的数值)
            height: 组件高度
        """
        super().__init__()
        self.title = title
        self.value_callback = value_callback
        self.data_callback = data_callback or value_callback
        self.max_data_points = 60  # 60秒历史数据
        self.data_history = deque(maxlen=self.max_data_points)
        
        # 填充初始数据
        for _ in range(self.max_data_points):
            self.data_history.append(0)
        
        self.init_ui(height)
        
    def init_ui(self, height: int):
        """初始化 UI"""
        self.setMinimumHeight(height)
        self.setMaximumHeight(height + 50)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # 标题
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #FFFFFF;')
        layout.addWidget(self.title_label)
        
        # 数值显示
        self.value_label = QLabel('N/A')
        self.value_label.setStyleSheet('font-size: 20px; font-weight: bold; color: #2196F3;')
        self.value_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.value_label)
        
        # 图表区域
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMaximumHeight(80)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.hideButtons()
        
        # 设置图表样式
        self.plot_widget.setBackground(self.COLOR_BACKGROUND)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getAxis('bottom').setPen(self.COLOR_GRID)
        self.plot_widget.getAxis('left').setPen(self.COLOR_GRID)
        self.plot_widget.getAxis('bottom').setTextPen(self.COLOR_GRID)
        self.plot_widget.getAxis('left').setTextPen(self.COLOR_GRID)
        
        # 隐藏坐标轴标签
        self.plot_widget.getAxis('bottom').setTicks([])
        self.plot_widget.getAxis('left').setWidth(25)
        
        # 设置 Y 轴范围 (0-100%)
        self.plot_widget.setYRange(0, 100, padding=0)
        self.plot_widget.setXRange(0, self.max_data_points - 1, padding=0)
        
        # 创建曲线
        pen = pg.mkPen(color=self.COLOR_LOW, width=2)
        self.curve = self.plot_widget.plot(pen=pen, fillLevel=0, 
                                           brush=pg.mkBrush(color=self.COLOR_LOW + '40'))
        
        layout.addWidget(self.plot_widget)
        
        # 设置样式
        self.setStyleSheet(f"""
            MonitorWidget {{
                background-color: {self.COLOR_BACKGROUND};
                border-radius: 8px;
                border: 1px solid {self.COLOR_GRID};
            }}
        """)
        
    def extract_numeric_value(self, value_str: str) -> float:
        """从字符串中提取数值"""
        try:
            # 尝试直接解析
            return float(value_str.replace('%', '').split()[0])
        except Exception:
            # 如果失败，尝试提取第一个数字
            import re
            numbers = re.findall(r'\d+\.?\d*', value_str)
            if numbers:
                return float(numbers[0])
            return 0.0
        
    def update_display(self):
        """更新显示"""
        try:
            # 更新数值显示
            value = self.value_callback()
            self.value_label.setText(value)

            # 优先使用独立的 data_callback 获取图表数值
            if self.data_callback is not self.value_callback:
                numeric_value = self.data_callback()
            else:
                # 从显示文本中提取
                numeric_value = self.extract_numeric_value(value)

            # 限制在 0-100 范围内
            numeric_value = max(0, min(100, numeric_value))

            # 更新历史数据
            self.data_history.append(numeric_value)

            # 更新图表
            self.curve.setData(list(self.data_history))

            # 根据数值更新颜色
            self.update_color(numeric_value)

        except Exception as e:
            self.value_label.setText('Error')
            
    def update_color(self, value: float):
        """根据数值更新颜色 - 负载变色（4档）"""
        if value <= 50:
            color = self.COLOR_LOW       # 绿色 0-50%
        elif value <= 70:
            color = self.COLOR_MID       # 黄色 51-70%
        elif value <= 90:
            color = self.COLOR_HIGH      # 橙色 71-90%
        else:
            color = self.COLOR_CRITICAL  # 红色 91-100%
            
        self.value_label.setStyleSheet(f'font-size: 20px; font-weight: bold; color: {color};')
        
        # 更新曲线颜色
        pen = pg.mkPen(color=color, width=2)
        self.curve.setPen(pen)
        self.curve.setBrush(pg.mkBrush(color=color + '40'))
    
    def set_theme(self, theme: str = 'dark'):
        """
        设置主题
        
        Args:
            theme: 'dark' 或 'light'
        """
        if theme == 'dark':
            bg_color = '#2D2D2D'
            text_color = '#FFFFFF'
            grid_color = '#3D3D3D'
        else:
            bg_color = '#FFFFFF'
            text_color = '#212121'
            grid_color = '#E0E0E0'
        
        # 更新标题颜色
        self.title_label.setStyleSheet(f'font-size: 14px; font-weight: bold; color: {text_color};')
        
        # 更新图表背景
        self.plot_widget.setBackground(bg_color)
        self.plot_widget.getAxis('bottom').setPen(grid_color)
        self.plot_widget.getAxis('left').setPen(grid_color)
        self.plot_widget.getAxis('bottom').setTextPen(grid_color)
        self.plot_widget.getAxis('left').setTextPen(grid_color)
        
        # 更新组件样式
        self.setStyleSheet(f"""
            MonitorWidget {{
                background-color: {bg_color};
                border-radius: 8px;
                border: 1px solid {grid_color};
            }}
        """)
