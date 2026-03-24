"""
仪表盘组件 - 汽车仪表盘样式
圆形进度条 + 中心数值显示
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QConicalGradient, QBrush


class GaugeWidget(QWidget):
    """仪表盘组件"""
    
    # 颜色配置 - 负载变色（4档）
    COLOR_LOW = QColor('#4CAF50')      # 绿色 - 0-50%
    COLOR_MID = QColor('#FFC107')      # 黄色 - 51-70%
    COLOR_HIGH = QColor('#FF9800')     # 橙色 - 71-90%
    COLOR_CRITICAL = QColor('#F44336') # 红色 - 91-100%
    COLOR_BG = QColor('#2D2D2D')       # 背景色
    COLOR_BG_LIGHT = QColor('#E0E0E0') # 浅色背景
    
    def __init__(self, title: str, value_callback, size: int = 140):
        """
        初始化仪表盘
        
        Args:
            title: 监控项名称 (CPU/内存/磁盘等)
            value_callback: 获取数值的回调函数
            size: 仪表盘尺寸
        """
        super().__init__()
        self.title = title
        self.value_callback = value_callback
        self.size = size
        self.current_value = 0
        self.theme = 'dark'
        
        # 高度 = 仪表盘 + 标题区域（确保标题完整显示）
        self.setFixedSize(size, size + 45)
        self.setMinimumSize(size, size + 45)
        
    def update_value(self):
        """更新数值"""
        try:
            value_str = self.value_callback()
            # 提取数值
            import re
            numbers = re.findall(r'\d+\.?\d*', value_str)
            if numbers:
                self.current_value = float(numbers[0])
            else:
                self.current_value = 0
        except:
            self.current_value = 0
        
        # 限制在 0-100
        self.current_value = max(0, min(100, self.current_value))
        self.update()
    
    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self.update()
    
    def paintEvent(self, event):
        """绘制仪表盘"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 确定颜色
        if self.theme == 'dark':
            text_color = QColor('#FFFFFF')
            bg_ring_color = QColor('#404040')
        else:
            text_color = QColor('#212121')
            bg_ring_color = QColor('#BDBDBD')
        
        # 背景透明 - 不绘制背景，使用父窗口背景色
        
        # 绘制圆形区域
        center_x = self.width() // 2
        center_y = self.size // 2
        radius = (self.size - 20) // 2
        
        # 绘制背景圆环
        pen_bg = QPen()
        pen_bg.setWidth(10)
        pen_bg.setColor(bg_ring_color)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            225 * 16, -270 * 16  # 从225度开始，画270度
        )
        
        # 计算进度颜色 - 负载变色（4档）
        if self.current_value <= 50:
            progress_color = self.COLOR_LOW       # 绿色 0-50%
        elif self.current_value <= 70:
            progress_color = self.COLOR_MID       # 黄色 51-70%
        elif self.current_value <= 90:
            progress_color = self.COLOR_HIGH      # 橙色 71-90%
        else:
            progress_color = self.COLOR_CRITICAL  # 红色 91-100%
        
        # 绘制进度圆环
        if self.current_value > 0:
            pen_progress = QPen()
            pen_progress.setWidth(10)
            pen_progress.setColor(progress_color)
            pen_progress.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_progress)
            
            # 计算角度 (270度对应100%)
            span_angle = int(-270 * 16 * self.current_value / 100)
            painter.drawArc(
                center_x - radius, center_y - radius,
                radius * 2, radius * 2,
                225 * 16, span_angle
            )
        
        # 绘制中心数值
        painter.setPen(text_color)
        font = QFont('Microsoft YaHei', 16, QFont.Bold)
        painter.setFont(font)
        
        value_text = f'{self.current_value:.0f}%'
        text_rect = painter.boundingRect(
            QRectF(center_x - 40, center_y - 20, 80, 40),
            Qt.AlignCenter, value_text
        )
        painter.drawText(text_rect, Qt.AlignCenter, value_text)
        
        # 绘制标题
        font_title = QFont('Microsoft YaHei', 10)
        painter.setFont(font_title)
        # 标题使用与进度条相同的颜色
        painter.setPen(progress_color)
        # 标题位置：紧贴在圆形下方，间隔3px
        title_rect = QRectF(0, self.size - 5, self.width(), 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.title)
        
        painter.end()


class MinimalModeWidget(QWidget):
    """极简模式容器 - 水平排列所有仪表盘"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gauges = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        from PyQt5.QtWidgets import QHBoxLayout, QPushButton
        
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(8, 4, 8, 0)  # 上边距4px，下边距0
        self.layout.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        
        self.setStyleSheet('background-color: transparent;')
        
        # 添加极简模式切换按钮（完全透明，无边框）
        self.toggle_btn = QPushButton('≡')
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setToolTip('切换极简模式')
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.layout.addWidget(self.toggle_btn)
    
    def add_gauge(self, key: str, title: str, value_callback):
        """添加仪表盘"""
        gauge = GaugeWidget(title, value_callback)
        self.gauges[key] = gauge
        self.layout.addWidget(gauge)
    
    def remove_gauge(self, key: str):
        """移除仪表盘"""
        if key in self.gauges:
            gauge = self.gauges.pop(key)
            self.layout.removeWidget(gauge)
            gauge.deleteLater()
    
    def update_gauges(self):
        """更新所有仪表盘"""
        for gauge in self.gauges.values():
            gauge.update_value()
    
    def set_theme(self, theme: str):
        """设置主题"""
        for gauge in self.gauges.values():
            gauge.set_theme(theme)
        
        # 更新切换按钮样式（完全透明，无边框，文字与背景反色）
        if hasattr(self, 'toggle_btn'):
            if theme == 'dark':
                # 深色背景，浅色文字
                self.toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #CCCCCC;
                        border: none;
                        border-radius: 4px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 30);
                        color: #FFFFFF;
                    }
                """)
            else:
                # 浅色背景，深色文字
                self.toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #666666;
                        border: none;
                        border-radius: 4px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 0, 0, 30);
                        color: #000000;
                    }
                """)
    
    def clear(self):
        """清空所有仪表盘（保留切换按钮）"""
        for gauge in list(self.gauges.values()):
            self.layout.removeWidget(gauge)
            gauge.deleteLater()
        self.gauges.clear()
