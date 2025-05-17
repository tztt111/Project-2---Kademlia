# event_system.py
from enum import Enum, auto
from typing import Dict, Any, Callable, List
import uuid

class EventType(Enum):
    # 系统事件
    SIMULATION_START = auto()
    SIMULATION_TICK = auto()
    SIMULATION_END = auto()
    
    # 节点事件
    NODE_JOIN = auto()
    NODE_LEAVE = auto()
    
    # 文件事件
    FILE_PUBLISH = auto()
    FILE_RETRIEVE = auto()
    
    # 网络事件
    MESSAGE_SENT = auto()
    MESSAGE_RECEIVED = auto()
    MESSAGE_DROPPED = auto()

class Event:
    def __init__(self, event_type: EventType, time: int, params: Dict[str, Any] = None):
        self.id = uuid.uuid4()
        self.type = event_type
        self.time = time  # 事件发生的模拟时间
        self.params = params or {}
    
    def __lt__(self, other):
        # 用于排序的比较
        return self.time < other.time

class EventEmitter:
    def __init__(self):
        self._listeners: Dict[EventType, List[Callable]] = {}
    
    def on(self, event_type: EventType, callback: Callable) -> None:
        """注册事件监听器"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
    
    def off(self, event_type: EventType, callback: Callable) -> None:
        """移除事件监听器"""
        if event_type in self._listeners and callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)
    
    def emit(self, event: Event) -> None:
        """触发事件"""
        if event.type in self._listeners:
            for callback in self._listeners[event.type]:
                callback(event)
