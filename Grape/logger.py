# logger.py
import logging
import sys
from enum import Enum
from typing import Optional, Dict, Any, List

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

class LogEntry:
    def __init__(self, level: LogLevel, time: int, category: str, message: str, data: Optional[Dict[str, Any]] = None):
        self.level = level
        self.time = time  # 模拟时间
        self.category = category
        self.message = message
        self.data = data or {}

class Logger:
    def __init__(self, config):
        self.config = config
        self.logs: List[LogEntry] = []
        
        # 设置Python的logging模块
        level_str = self.config.get("logging.level", "INFO")
        level = getattr(logging, level_str.upper())
        
        self.logger = logging.getLogger("dht_simulator")
        self.logger.setLevel(level)
        
        # 清除已有的handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 添加控制台handler
        if self.config.get("logging.console", True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
            self.logger.addHandler(console_handler)
        
        # 添加文件handler
        log_file = self.config.get("logging.file")
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
            self.logger.addHandler(file_handler)
    
    def log(self, level: LogLevel, time: int, category: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """记录日志"""
        entry = LogEntry(level, time, category, message, data)
        self.logs.append(entry)
        
        # 格式化消息，包含模拟时间和类别
        formatted_msg = f"[Time: {time}] [{category}] {message}"
        
        # 使用Python的logging模块
        self.logger.log(level.value, formatted_msg)
    
    def debug(self, time: int, category: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.DEBUG, time, category, message, data)
    
    def info(self, time: int, category: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.INFO, time, category, message, data)
    
    def warning(self, time: int, category: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.WARNING, time, category, message, data)
    
    def error(self, time: int, category: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.ERROR, time, category, message, data)
    
    def query_logs(self, level: Optional[LogLevel] = None, time_range=None, category=None) -> List[LogEntry]:
        """查询日志"""
        result = []
        for entry in self.logs:
            if level and entry.level != level:
                continue
            if time_range and (entry.time < time_range[0] or entry.time > time_range[1]):
                continue
            if category and entry.category != category:
                continue
            result.append(entry)
        return result
