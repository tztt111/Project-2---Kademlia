# config.py
import json
from typing import Dict, Any, Optional

class Config:
    def __init__(self):
        # 默认配置
        self._config = {
            # 模拟器配置
            "simulation": {
                "time_tick_ms": 100,       # 每个时间单位代表的毫秒数
                "max_time": None,          # 最大模拟时间（None表示无限）
                "random_seed": None        # 随机数种子（None表示使用系统时间）
            },
            # DHT配置
            "dht": {
                "k_value": 8,              # K桶大小
                "id_bits": 160,            # ID位数
                "alpha": 3,                # 并发查询数
                "republish_interval": 3600  # 重新发布文件的间隔
            },
            # 网络配置
            "network": {
                "min_delay": 1,            # 最小网络延迟（时间单位）
                "max_delay": 3,            # 最大网络延迟（时间单位）
                "packet_loss_rate": 0.0    # 丢包率(0.0-1.0)
            },
            # 日志配置
            "logging": {
                "level": "INFO",
                "file": "simulation.log",
                "console": True
            }
        }
    
    def get(self, path: str, default=None) -> Any:
        """获取配置项，支持点号路径访问，如'dht.k_value'"""
        keys = path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, path: str, value: Any) -> None:
        """设置配置项"""
        keys = path.split('.')
        target = self._config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
    
    def load_from_file(self, filepath: str) -> None:
        """从JSON文件加载配置"""
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
                # 递归更新配置
                self._update_recursive(self._config, config)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def _update_recursive(self, target: Dict, source: Dict) -> None:
        """递归更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_recursive(target[key], value)
            else:
                target[key] = value
    
    def save_to_file(self, filepath: str) -> None:
        """将配置保存到JSON文件"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
