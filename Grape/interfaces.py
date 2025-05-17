# interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from event_system import Event
from message import Message

class IEventHandler(ABC):
    """事件处理器接口"""
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """处理事件"""
        pass

class IMessageHandler(ABC):
    """消息处理器接口"""
    @abstractmethod
    def handle_message(self, message: Message) -> Optional[Message]:
        """处理消息并可选地返回响应"""
        pass

class INode(IEventHandler, IMessageHandler):
    """DHT节点接口"""
    @abstractmethod
    def get_id(self) -> bytes:
        """获取节点ID"""
        pass
    
    @abstractmethod
    def get_address(self) -> bytes:
        """获取节点地址"""
        pass
    
    @abstractmethod
    def join_network(self, seed_node_id: bytes) -> None:
        """加入网络"""
        pass
    
    @abstractmethod
    def leave_network(self) -> None:
        """离开网络"""
        pass
    
    @abstractmethod
    def publish_file(self, file_id: bytes) -> None:
        """发布文件"""
        pass
    
    @abstractmethod
    def retrieve_file(self, file_id: bytes) -> None:
        """检索文件"""
        pass

class IRoutingTable(ABC):
    """路由表接口"""
    @abstractmethod
    def update(self, node_id: bytes, address: bytes, last_seen: int) -> bool:
        """更新路由表"""
        pass
    
    @abstractmethod
    def find_closest_nodes(self, target_id: bytes, count: int) -> List[Dict[str, Any]]:
        """查找最接近目标ID的节点"""
        pass
    
    @abstractmethod
    def remove_node(self, node_id: bytes) -> bool:
        """从路由表中移除节点"""
        pass
    
    @abstractmethod
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """获取路由表中的所有节点"""
        pass

class ISimulator(ABC):
    """模拟器接口"""
    @abstractmethod
    def send_message(self, message: Message) -> None:
        """发送消息"""
        pass
    
    @abstractmethod
    def schedule_event(self, event: Event) -> None:
        """调度事件"""
        pass
    
    @abstractmethod
    def get_current_time(self) -> int:
        """获取当前模拟时间"""
        pass
    
    @abstractmethod
    def register_node(self, node: INode) -> None:
        """注册节点"""
        pass
    
    @abstractmethod
    def unregister_node(self, node_id: bytes) -> None:
        """注销节点"""
        pass
