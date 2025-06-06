# dht_node.py
from typing import Dict, List, Any, Optional, Set
from interfaces import INode, ISimulator
from routing_table import RoutingTable
from message import Message, MessageType
from event_system import Event, EventType
from id_util import IDUtil

class DHTNode(INode):
    """DHT节点实现"""
    # 节点配置常量
    PING_TIMEOUT = 2000  # PING超时时间（毫秒）
    MAX_RETRIES = 2     # 最大重试次数
    
    def __init__(self, 
                 node_id: bytes, 
                 address: bytes, 
                 simulator: ISimulator,
                 k_value: int = 8, 
                 id_bits: int = 160):
        self.node_id = node_id
        self.address = address
        self.simulator = simulator
        self.routing_table = RoutingTable(node_id, k_value, id_bits)
        self.file_providers: Dict[bytes, List[Dict[str, Any]]] = {}  # fileID -> [(address, last_seen), ...]
        self.owned_files: Set[bytes] = set()  # 节点拥有的文件集合
        self.is_online = False
        self.pending_responses: Dict[str, Dict[str, Any]] = {}  # transaction_id -> callback_info
        self.last_check_time = 0  # 上次检查超时的时间
        
        # 注册到模拟器
        self.simulator.register_node(self)
    
    def get_id(self) -> bytes:
        """获取节点ID"""
        return self.node_id
    
    def get_address(self) -> bytes:
        """获取节点地址"""
        return self.address
    
    def join_network(self, seed_node_id: Optional[bytes] = None) -> None:
        """加入网络，通过种子节点引导
        
        Args:
            seed_node_id: 种子节点ID，如果为None则表示这是种子节点自己
        """
        if self.is_online:
            return  # 已经在线
        
        self.is_online = True
        
        # 如果是普通节点（非种子节点），需要通过种子节点引导
        if seed_node_id and seed_node_id != self.node_id:
            self._send_find_node(seed_node_id, self.node_id, "join_network")
    
    def leave_network(self) -> None:
        """离开网络"""
        if not self.is_online:
            return  # 已经离线
        
        self.is_online = False
    
    def publish_file(self, file_id: bytes) -> None:
        """发布文件到网络"""
        if not self.is_online:
            return
        
        # 添加到自己的文件列表
        self.owned_files.add(file_id)
        
        # 查找最接近文件ID的节点，然后发送STORE请求
        current_time = self.simulator.get_current_time()
        self._find_closest_nodes(
            file_id, 
            callback_type="store_file", 
            callback_data={"file_id": file_id}, 
            event_time=current_time
        )
    
    def retrieve_file(self, file_id: bytes) -> None:
        """从网络中检索文件"""
        if not self.is_online:
            return
        
        # 发送FIND_VALUE请求
        current_time = self.simulator.get_current_time()
        self._find_value(file_id, event_time=current_time)
    
    def handle_event(self, event: Event) -> None:
        """处理事件"""
        if event.type == EventType.SIMULATION_TICK:
            # 定期检查超时的PING请求
            current_time = self.simulator.get_current_time()
            
            # 每100ms检查一次超时
            if current_time - self.last_check_time >= 100:
                self.last_check_time = current_time
                
                timeouts = []
                for txid, info in self.pending_responses.items():
                    if info["type"] == "ping":
                        # 检查是否超时
                        if current_time - info["time"] >= self.PING_TIMEOUT:
                            timeouts.append(txid)
                
                # 处理超时的消息
                for txid in timeouts:
                    self._handle_ping_timeout(txid)
        
        elif event.type == EventType.NODE_JOIN:
            pass  # 节点加入事件由DHT模拟器处理
        
        elif event.type == EventType.NODE_LEAVE:
            # 处理其他节点离开网络
            # 可以清理路由表中的相关条目
            if event.params.get("node_id") != self.node_id:
                self.routing_table.remove_node(event.params["node_id"])
    
    def handle_message(self, message: Message) -> Optional[Message]:
        """处理接收到的消息"""
        if not self.is_online:
            return None  # 节点离线，不处理消息
        
        # 无论消息类型如何，都更新路由表
        self.routing_table.update(
            message.source_id, 
            message.source_id, 
            message.delivery_time
        )
        
        # 根据消息类型处理
        if message.type == MessageType.PING:
            return self._handle_ping(message)
        elif message.type == MessageType.PONG:
            return self._handle_pong(message)
        elif message.type == MessageType.FIND_NODE:
            return self._handle_find_node(message)
        elif message.type == MessageType.FIND_NODE_RESPONSE:
            return self._handle_find_node_response(message)
        elif message.type == MessageType.FIND_VALUE:
            return self._handle_find_value(message)
        elif message.type == MessageType.FIND_VALUE_RESPONSE:
            return self._handle_find_value_response(message)
        elif message.type == MessageType.STORE:
            return self._handle_store(message)
        elif message.type == MessageType.STORE_RESPONSE:
            return self._handle_store_response(message)
        
        return None
    
    def _send_ping(self, target_id: bytes, event_time: Optional[int] = None) -> None:
        """发送PING请求"""
        send_time = event_time if event_time is not None else self.simulator.get_current_time()
        message = Message(
            MessageType.PING,
            self.node_id,
            target_id,
            {
                "ping": "ping",
                "retry_count": 0
            }
        )
        
        self.pending_responses[message.transaction_id] = {
            "type": "ping",
            "time": send_time,
            "retry_count": 0,
            "target_id": target_id
        }
        
        self.simulator.send_message(message, send_time)
    
    def _handle_ping(self, message: Message) -> Message:
        """处理PING请求"""
        retry_count = message.content.get("retry_count", 0)
        
        response = message.create_response({
            "pong": "pong",
            "retry_count": retry_count
        }, MessageType.PONG)
        response.send_time = message.delivery_time
        return response
    
    def _handle_pong(self, message: Message) -> None:
        """处理PONG响应"""
        if message.transaction_id not in self.pending_responses:
            return None
        
        callback_info = self.pending_responses.pop(message.transaction_id)
        if callback_info["type"] == "ping":
            self.routing_table.update_last_seen(message.source_id, message.delivery_time)
        
        return None
    
    def _handle_ping_timeout(self, transaction_id: str) -> None:
        """处理PING超时"""
        if transaction_id not in self.pending_responses:
            return
        
        info = self.pending_responses[transaction_id]
        if info["type"] != "ping":
            return
        
        if info["retry_count"] < self.MAX_RETRIES:
            # 增加重试计数并重发
            info["retry_count"] += 1
            current_time = self.simulator.get_current_time()
            
            message = Message(
                MessageType.PING,
                self.node_id,
                info["target_id"],
                {
                    "ping": "ping",
                    "retry_count": info["retry_count"]
                }
            )
            
            info["time"] = current_time
            self.simulator.send_message(message, current_time)
        else:
            # 超过最大重试次数
            self.routing_table.remove_node(info["target_id"])
            self.pending_responses.pop(transaction_id)
    
    def _send_find_node(self, target_id: bytes, node_id_to_find: bytes, 
                       callback_type: str = "find_node", callback_data: Dict[str, Any] = None,
                       event_time: Optional[int] = None) -> None:
        """发送FIND_NODE请求"""
        send_time = event_time if event_time is not None else self.simulator.get_current_time()
        message = Message(
            MessageType.FIND_NODE,
            self.node_id,
            target_id,
            {"target": node_id_to_find.hex().upper()}
        )
        
        self.pending_responses[message.transaction_id] = {
            "type": callback_type,
            "data": callback_data or {},
            "time": send_time
        }
        
        self.simulator.send_message(message, send_time)
    
    def _handle_find_node(self, message: Message) -> Message:
        """处理FIND_NODE请求"""
        target_id_hex = message.content.get("target")
        if not target_id_hex:
            return None
        
        target_id = bytes.fromhex(target_id_hex)
        closest_nodes = self.routing_table.find_closest_nodes(target_id)
        
        node_list = []
        for node in closest_nodes:
            node_list.append({
                "id": node["id"].hex(),
                "address": node["address"].hex()
            })
        
        response = message.create_response({"nodes": node_list}, MessageType.FIND_NODE_RESPONSE)
        response.send_time = message.delivery_time
        return response
    
    def _handle_find_node_response(self, message: Message) -> None:
        """处理FIND_NODE响应"""
        if message.transaction_id not in self.pending_responses:
            return None
        
        callback_info = self.pending_responses.pop(message.transaction_id)
        nodes = message.content.get("nodes", [])
        
        for node_info in nodes:
            node_id = bytes.fromhex(node_info["id"])
            address = bytes.fromhex(node_info["address"])
            self.routing_table.update(node_id, address, message.delivery_time)
        
        # 处理特定回调类型
        if callback_info["type"] == "join_network":
            # 加入网络时的响应处理
            for node_info in nodes:
                node_id = bytes.fromhex(node_info["id"])
                if node_id != self.node_id:  # 避免发送给自己
                    self._send_ping(node_id, message.delivery_time)
        
        elif callback_info["type"] == "store_file":
            # 存储文件时的响应处理
            file_id = callback_info["data"].get("file_id")
            if file_id:
                for node_info in nodes:
                    node_id = bytes.fromhex(node_info["id"])
                    if node_id != self.node_id:
                        self._send_store(node_id, file_id, self.address, message.delivery_time)
        
        return None
    
    def _find_closest_nodes(self, target_id: bytes, callback_type: str = "find_closest",
                          callback_data: Dict[str, Any] = None, event_time: Optional[int] = None) -> None:
        """查找最接近目标ID的节点"""
        closest_nodes = self.routing_table.find_closest_nodes(target_id)
        
        if not closest_nodes:
            return
        
        for node in closest_nodes:
            self._send_find_node(
                node["id"], 
                target_id, 
                callback_type, 
                callback_data or {"target_id": target_id},
                event_time
            )
    
    def _send_find_value(self, target_id: bytes, file_id: bytes, event_time: Optional[int] = None) -> None:
        """发送FIND_VALUE请求"""
        send_time = event_time if event_time is not None else self.simulator.get_current_time()
        message = Message(
            MessageType.FIND_VALUE,
            self.node_id,
            target_id,
            {"key": file_id.hex()}
        )
        
        self.pending_responses[message.transaction_id] = {
            "type": "find_value",
            "data": {"file_id": file_id},
            "time": send_time
        }
        
        self.simulator.send_message(message, send_time)
    
    def _find_value(self, file_id: bytes, event_time: Optional[int] = None) -> None:
        """查找文件值"""
        if file_id in self.owned_files:
            return
        
        closest_nodes = self.routing_table.find_closest_nodes(file_id)
        
        if not closest_nodes:
            return
        
        for node in closest_nodes:
            self._send_find_value(node["id"], file_id, event_time)
    
    def _handle_find_value(self, message: Message) -> Message:
        """处理FIND_VALUE请求"""
        file_id_hex = message.content.get("key")
        if not file_id_hex:
            return None
        
        file_id = bytes.fromhex(file_id_hex)
        
        if file_id in self.file_providers:
            providers = []
            for provider_info in self.file_providers[file_id]:
                providers.append({
                    "address": provider_info["address"].hex(),
                    "last_seen": provider_info["last_seen"]
                })
            
            response = message.create_response({
                "found": True,
                "key": file_id_hex,
                "providers": providers
            }, MessageType.FIND_VALUE_RESPONSE)
            response.send_time = message.delivery_time
            return response
        
        # 未找到文件，返回最近节点
        closest_nodes = self.routing_table.find_closest_nodes(file_id)
        node_list = []
        for node in closest_nodes:
            node_list.append({
                "id": node["id"].hex(),
                "address": node["address"].hex()
            })
        
        response = message.create_response({
            "found": False,
            "key": file_id_hex,
            "nodes": node_list
        }, MessageType.FIND_VALUE_RESPONSE)
        response.send_time = message.delivery_time
        return response
    
    def _handle_find_value_response(self, message: Message) -> None:
        """处理FIND_VALUE响应"""
        if message.transaction_id not in self.pending_responses:
            return None
        
        callback_info = self.pending_responses.pop(message.transaction_id)
        if callback_info["type"] != "find_value":
            return None
        
        file_id = callback_info["data"].get("file_id")
        if not file_id:
            return None
        
        if message.content.get("found", False):
            providers = message.content.get("providers", [])
            
            for provider_info in providers:
                address = bytes.fromhex(provider_info["address"])
                last_seen = provider_info.get("last_seen", message.delivery_time)
                
                if file_id not in self.file_providers:
                    self.file_providers[file_id] = []
                
                provider_exists = False
                for i, existing_provider in enumerate(self.file_providers[file_id]):
                    if existing_provider["address"] == address:
                        self.file_providers[file_id][i]["last_seen"] = last_seen
                        provider_exists = True
                        break
                
                if not provider_exists:
                    self.file_providers[file_id].append({
                        "address": address,
                        "last_seen": last_seen
                    })
        else:
            nodes = message.content.get("nodes", [])
            
            for node_info in nodes:
                node_id = bytes.fromhex(node_info["id"])
                address = bytes.fromhex(node_info["address"])
                self.routing_table.update(node_id, address, message.delivery_time)
                self._send_find_value(node_id, file_id, message.delivery_time)
        
        return None
    
    def _send_store(self, target_id: bytes, file_id: bytes, provider_address: bytes, 
                   event_time: Optional[int] = None) -> None:
        """发送STORE请求"""
        send_time = event_time if event_time is not None else self.simulator.get_current_time()
        message = Message(
            MessageType.STORE,
            self.node_id,
            target_id,
            {
                "key": file_id.hex(),
                "provider": provider_address.hex()
            }
        )
        
        self.pending_responses[message.transaction_id] = {
            "type": "store",
            "data": {"file_id": file_id},
            "time": send_time
        }
        
        self.simulator.send_message(message, send_time)
    
    def _handle_store(self, message: Message) -> Message:
        """处理STORE请求"""
        file_id_hex = message.content.get("key")
        provider_hex = message.content.get("provider")
        
        if not file_id_hex or not provider_hex:
            return None
        
        file_id = bytes.fromhex(file_id_hex)
        provider_address = bytes.fromhex(provider_hex)
        
        if file_id not in self.file_providers:
            self.file_providers[file_id] = []
        
        provider_exists = False
        for i, existing_provider in enumerate(self.file_providers[file_id]):
            if existing_provider["address"] == provider_address:
                self.file_providers[file_id][i]["last_seen"] = message.delivery_time
                provider_exists = True
                break
        
        if not provider_exists:
            self.file_providers[file_id].append({
                "address": provider_address,
                "last_seen": message.delivery_time
            })
        
        response = message.create_response({"status": "success"}, MessageType.STORE_RESPONSE)
        response.send_time = message.delivery_time
        return response
    
    def _handle_store_response(self, message: Message) -> None:
        """处理STORE响应"""
        if message.transaction_id in self.pending_responses:
            self.pending_responses.pop(message.transaction_id)
        return None
