"""
Pcmonitor - Windows 系统资源监控工具
程序入口
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """程序入口"""
    # 启用高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 设置应用信息
    app.setApplicationName("Pcmonitor")
    app.setApplicationDisplayName("Pcmonitor - 系统资源监控")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
