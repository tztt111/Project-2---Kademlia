# simulation_clock.py
from typing import Optional, Callable, List

class SimulationClock:
    def __init__(self, tick_ms: int = 100):
        self.current_time = 0    # 当前模拟时间
        self.tick_ms = tick_ms   # 每个时间单位代表的毫秒数
        self._callbacks = []     # 时钟滴答回调
    
    def reset(self) -> None:
        """重置时钟"""
        self.current_time = 0
    
    def advance(self, ticks: int = 1) -> None:
        """推进时钟指定的时间单位"""
        self.current_time += ticks
        self._notify_callbacks()
    
    def set_time(self, time: int) -> None:
        """直接设置时间"""
        previous_time = self.current_time
        self.current_time = time
        if time != previous_time:
            self._notify_callbacks()
    
    def get_time(self) -> int:
        """获取当前时间"""
        return self.current_time
    
    def get_time_ms(self) -> int:
        """获取当前时间（毫秒）"""
        return self.current_time * self.tick_ms
    
    def ms_to_ticks(self, ms: int) -> int:
        """将毫秒转换为时间单位"""
        return ms // self.tick_ms
    
    def add_tick_callback(self, callback: Callable[[int], None]) -> None:
        """添加时间变化回调"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def remove_tick_callback(self, callback: Callable[[int], None]) -> None:
        """移除时间变化回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self) -> None:
        """通知所有回调时间已更新"""
        for callback in self._callbacks:
            callback(self.current_time)
