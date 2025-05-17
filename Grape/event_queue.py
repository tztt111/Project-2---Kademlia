# event_queue.py
import heapq
from typing import List, Optional
from event_system import Event

class EventQueue:
    def __init__(self):
        self._queue = []  # 优先队列，按事件时间排序
        self._counter = 0  # 用于同时间事件的稳定排序
    
    def schedule(self, event: Event) -> None:
        """将事件加入队列"""
        # 为同一时间的事件提供稳定排序
        entry = (event.time, self._counter, event)
        self._counter += 1
        heapq.heappush(self._queue, entry)
    
    def next_event(self) -> Optional[Event]:
        """获取下一个事件，但不从队列中移除"""
        if not self._queue:
            return None
        return self._queue[0][2]  # 返回事件对象
    
    def pop_event(self) -> Optional[Event]:
        """获取并移除下一个事件"""
        if not self._queue:
            return None
        return heapq.heappop(self._queue)[2]  # 返回事件对象
    
    def peek_time(self) -> Optional[int]:
        """查看下一个事件的时间，不移除事件"""
        if not self._queue:
            return None
        return self._queue[0][0]
    
    def has_events(self) -> bool:
        """检查队列是否有事件"""
        return len(self._queue) > 0
    
    def clear(self) -> None:
        """清空事件队列"""
        self._queue = []
        self._counter = 0
    
    def get_events_until(self, time: int) -> List[Event]:
        """获取直到指定时间的所有事件"""
        result = []
        while self.has_events() and self.peek_time() <= time:
            result.append(self.pop_event())
        return result
    
    def count(self) -> int:
        """返回队列中事件数量"""
        return len(self._queue)
