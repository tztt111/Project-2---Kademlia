# message.py
from enum import Enum
import uuid
from typing import Dict, Any, Optional

class MessageType(Enum):
    # 基本DHT操作
    PING = "ping"
    PONG = "pong"
    FIND_NODE = "find_node"
    FIND_NODE_RESPONSE = "find_node_response"
    FIND_VALUE = "find_value"
    FIND_VALUE_RESPONSE = "find_value_response"
    STORE = "store"
    STORE_RESPONSE = "store_response"
    
    # 扩展操作（可选）
    BOOTSTRAP = "bootstrap"
    ANNOUNCE = "announce"

class Message:
    def __init__(self, 
                 msg_type: MessageType,
                 source_id: bytes,
                 target_id: bytes,
                 content: Dict[str, Any],
                 transaction_id: Optional[str] = None):
        self.type = msg_type
        self.source_id = source_id
        self.target_id = target_id
        self.content = content
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.send_time = None       # 发送时间（由模拟器填充）
        self.delivery_time = None   # 投递时间（由模拟器填充）
    
    def to_dict(self) -> Dict[str, Any]:
        """将消息转换为字典格式"""
        return {
            "type": self.type.value,
            "source_id": self.source_id.hex(),
            "target_id": self.target_id.hex(),
            "content": self.content,
            "transaction_id": self.transaction_id,
            "send_time": self.send_time,
            "delivery_time": self.delivery_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息对象"""
        msg = cls(
            msg_type=MessageType(data["type"]),
            source_id=bytes.fromhex(data["source_id"]),
            target_id=bytes.fromhex(data["target_id"]),
            content=data["content"],
            transaction_id=data["transaction_id"]
        )
        msg.send_time = data.get("send_time")
        msg.delivery_time = data.get("delivery_time")
        return msg
    
    def create_response(self, content: Dict[str, Any], msg_type=None) -> 'Message':
        """创建对此消息的响应"""
        response_type = msg_type
        if response_type is None:
            # 自动确定响应类型
            if self.type == MessageType.PING:
                response_type = MessageType.PONG
            elif self.type == MessageType.FIND_NODE:
                response_type = MessageType.FIND_NODE_RESPONSE
            elif self.type == MessageType.FIND_VALUE:
                response_type = MessageType.FIND_VALUE_RESPONSE
            elif self.type == MessageType.STORE:
                response_type = MessageType.STORE_RESPONSE
            else:
                raise ValueError(f"Cannot automatically determine response type for {self.type}")
        
        return Message(
            msg_type=response_type,
            source_id=self.target_id,  # 响应的源是原消息的目标
            target_id=self.source_id,  # 响应的目标是原消息的源
            content=content,
            transaction_id=self.transaction_id  # 保持相同的事务ID
        )
