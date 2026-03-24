"""
开机自启管理模块
Windows 注册表操作
"""
import os
import sys
import winreg
from typing import Optional


class AutoStartManager:
    """开机自启管理器"""
    
    REG_KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
    APP_NAME = 'Pcmonitor'
    
    @classmethod
    def get_executable_path(cls) -> str:
        """获取可执行文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的 exe
            return sys.executable
        else:
            # 开发环境 - 使用 main.py 的绝对路径
            return os.path.abspath(sys.argv[0])
    
    @classmethod
    def enable_auto_start(cls, minimized: bool = False) -> bool:
        """
        启用开机自启
        
        Args:
            minimized: 是否以最小化方式启动
            
        Returns:
            是否成功
        """
        try:
            exe_path = cls.get_executable_path()
            
            # 如果是 py 文件，使用 python 运行
            if exe_path.endswith('.py'):
                # 找到 python 解释器
                python_exe = sys.executable
                command = f'"{python_exe}" "{exe_path}"'
            else:
                command = f'"{exe_path}"'
            
            # 添加最小化参数
            if minimized:
                command += ' --minimized'
            
            # 写入注册表
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, cls.APP_NAME, 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)
            
            return True
        except Exception as e:
            print(f"启用开机自启失败: {e}")
            return False
    
    @classmethod
    def disable_auto_start(cls) -> bool:
        """
        禁用开机自启
        
        Returns:
            是否成功
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, cls.APP_NAME)
            except FileNotFoundError:
                # 值不存在，忽略
                pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"禁用开机自启失败: {e}")
            return False
    
    @classmethod
    def is_auto_start_enabled(cls) -> bool:
        """
        检查是否已启用开机自启
        
        Returns:
            是否已启用
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_KEY_PATH,
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, cls.APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            print(f"检查开机自启状态失败: {e}")
            return False
    
    @classmethod
    def get_auto_start_command(cls) -> Optional[str]:
        """
        获取当前的自启命令
        
        Returns:
            命令字符串，或 None
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_KEY_PATH,
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, cls.APP_NAME)
                winreg.CloseKey(key)
                return value
            except FileNotFoundError:
                winreg.CloseKey(key)
                return None
        except Exception as e:
            print(f"获取自启命令失败: {e}")
            return None
