# dht_node.py
from typing import Dict, List, Any, Optional, Set
from interfaces import INode, ISimulator
from routing_table import RoutingTable
from message import Message, MessageType
from event_system import Event, EventType
from id_util import IDUtil

class DHTNode(INode):
    """DHT节点实现"""
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
        
        # 注册到模拟器
        self.simulator.register_node(self)
    
    def get_id(self) -> bytes:
        """获取节点ID"""
        return self.node_id
    
    def get_address(self) -> bytes:
        """获取节点地址"""
        return self.address
    
    def join_network(self, seed_node_id: bytes) -> None:
        """加入网络，通过种子节点引导"""
        if self.is_online:
            return  # 已经在线

        self.is_online = True
        
        # 向模拟器发送上线事件
        self.simulator.schedule_event(Event(
            EventType.NODE_JOIN, 
            self.simulator.get_current_time(),
            {"node_id": self.node_id, "address": self.address}
        ))
        
        if seed_node_id and seed_node_id != self.node_id:
            # 向种子节点发送FIND_NODE请求（查找自己）
            self._send_find_node(seed_node_id, self.node_id)
    
    def leave_network(self) -> None:
        """离开网络"""
        if not self.is_online:
            return  # 已经离线
        
        self.is_online = False
        
        # 向模拟器发送离线事件
        self.simulator.schedule_event(Event(
            EventType.NODE_LEAVE,
            self.simulator.get_current_time(),
            {"node_id": self.node_id}
        ))
    
    def publish_file(self, file_id: bytes) -> None:
        """发布文件到网络"""
        if not self.is_online:
            return
        
        # 添加到自己的文件列表
        self.owned_files.add(file_id)
        
        # 发送事件
        self.simulator.schedule_event(Event(
            EventType.FILE_PUBLISH,
            self.simulator.get_current_time(),
            {"node_id": self.node_id, "file_id": file_id}
        ))
        
        # 查找最接近文件ID的节点，然后发送STORE请求
        self._find_closest_nodes(file_id, callback_type="store_file", callback_data={"file_id": file_id})
    
    def retrieve_file(self, file_id: bytes) -> None:
        """从网络中检索文件"""
        if not self.is_online:
            return
        
        # 发送事件
        self.simulator.schedule_event(Event(
            EventType.FILE_RETRIEVE,
            self.simulator.get_current_time(),
            {"node_id": self.node_id, "file_id": file_id}
        ))
        
        # 发送FIND_VALUE请求
        self._find_value(file_id)
    
    def handle_event(self, event: Event) -> None:
        """处理事件"""
        if event.type == EventType.SIMULATION_TICK:
            # 模拟滴答事件，可以用于定期维护任务
            pass
        elif event.type == EventType.NODE_JOIN:
            # 处理其他节点加入网络
            # 在实际实现中，该事件可能由模拟器广播，但在这里不需要处理
            pass
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
        self.routing_table.update(message.source_id, message.source_id, self.simulator.get_current_time())
        
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
    
    # 以下是处理各种消息类型的私有方法
    
    def _send_ping(self, target_id: bytes) -> None:
        """发送PING请求"""
        message = Message(
            MessageType.PING,
            self.node_id,
            target_id,
            {"ping": "ping"}  # 简单的PING内容
        )
        self.simulator.send_message(message)
    
    def _handle_ping(self, message: Message) -> Message:
        """处理PING请求"""
        # 简单地返回PONG响应
        return message.create_response({"pong": "pong"}, MessageType.PONG)
    
    def _handle_pong(self, message: Message) -> None:
        """处理PONG响应"""
        # 检查是否有待处理的回调
        if message.transaction_id in self.pending_responses:
            callback_info = self.pending_responses.pop(message.transaction_id)
            if callback_info["type"] == "ping":
                # 处理ping回调，通常只是确认节点在线
                pass
        return None
    
    def _send_find_node(self, target_id: bytes, node_id_to_find: bytes, callback_type: str = "find_node", callback_data: Dict[str, Any] = None) -> None:
        """发送FIND_NODE请求"""
        message = Message(
            MessageType.FIND_NODE,
            self.node_id,
            target_id,
            {"target": node_id_to_find.hex()}
        )
        
        # 保存回调信息
        self.pending_responses[message.transaction_id] = {
            "type": callback_type,
            "data": callback_data or {},
            "time": self.simulator.get_current_time()
        }
        
        self.simulator.send_message(message)
    
    def _handle_find_node(self, message: Message) -> Message:
        """处理FIND_NODE请求"""
        # 从消息内容中获取目标ID
        target_id_hex = message.content.get("target")
        if not target_id_hex:
            return None
        
        target_id = bytes.fromhex(target_id_hex)
        
        # 查找路由表中最接近的K个节点
        closest_nodes = self.routing_table.find_closest_nodes(target_id)
        
        # 转换为可序列化的格式
        node_list = []
        for node in closest_nodes:
            node_list.append({
                "id": node["id"].hex(),
                "address": node["address"].hex()
            })
        
        # 返回响应
        return message.create_response({"nodes": node_list}, MessageType.FIND_NODE_RESPONSE)
    
    def _handle_find_node_response(self, message: Message) -> None:
        """处理FIND_NODE响应"""
        # 检查是否有待处理的回调
        if message.transaction_id in self.pending_responses:
            callback_info = self.pending_responses.pop(message.transaction_id)
            
            # 处理返回的节点列表
            nodes = message.content.get("nodes", [])
            current_time = self.simulator.get_current_time()
            
            for node_info in nodes:
                node_id = bytes.fromhex(node_info["id"])
                address = bytes.fromhex(node_info["address"])
                
                # 更新路由表
                self.routing_table.update(node_id, address, current_time)
            
            # 如果是查找最近节点的回调
            if callback_info["type"] == "find_closest":
                target_id = callback_info["data"].get("target_id")
                
                # 继续查找过程或者执行后续操作
                if target_id and nodes:
                    # 查找过程可能继续...
                    pass
            
            # 如果是为了存储文件
            elif callback_info["type"] == "store_file":
                file_id = callback_info["data"].get("file_id")
                
                if file_id:
                    # 向找到的节点发送STORE请求
                    for node_info in nodes:
                        node_id = bytes.fromhex(node_info["id"])
                        if node_id != self.node_id:
                            self._send_store(node_id, file_id, self.address)
        
        return None
    
    def _find_closest_nodes(self, target_id: bytes, callback_type: str = "find_closest", callback_data: Dict[str, Any] = None) -> None:
        """查找最接近目标ID的节点"""
        # 先从自己的路由表中找
        closest_nodes = self.routing_table.find_closest_nodes(target_id)
        
        if not closest_nodes:
            # 路由表为空，无法继续
            return
        
        # 向最接近的节点发送FIND_NODE请求
        for node in closest_nodes:
            self._send_find_node(node["id"], target_id, callback_type, callback_data or {"target_id": target_id})
    
    def _send_find_value(self, target_id: bytes, file_id: bytes) -> None:
        """发送FIND_VALUE请求"""
        message = Message(
            MessageType.FIND_VALUE,
            self.node_id,
            target_id,
            {"key": file_id.hex()}
        )
        
        # 保存回调信息
        self.pending_responses[message.transaction_id] = {
            "type": "find_value",
            "data": {"file_id": file_id},
            "time": self.simulator.get_current_time()
        }
        
        self.simulator.send_message(message)
    
    def _find_value(self, file_id: bytes) -> None:
        """查找文件值"""
        # 先检查本地是否有
        if file_id in self.owned_files:
            # 本地已有文件
            return
        
        # 从路由表查找最近的K个节点
        closest_nodes = self.routing_table.find_closest_nodes(file_id)
        
        if not closest_nodes:
            # 路由表为空，无法查找
            return
        
        # 发送FIND_VALUE请求
        for node in closest_nodes:
            self._send_find_value(node["id"], file_id)
    
    def _handle_find_value(self, message: Message) -> Message:
        """处理FIND_VALUE请求"""
        # 从消息内容中获取文件ID
        file_id_hex = message.content.get("key")
        if not file_id_hex:
            return None
        
        file_id = bytes.fromhex(file_id_hex)
        
        # 检查是否有该文件的提供者信息
        if file_id in self.file_providers:
            # 返回提供者列表
            providers = []
            for provider_info in self.file_providers[file_id]:
                providers.append({
                    "address": provider_info["address"].hex(),
                    "last_seen": provider_info["last_seen"]
                })
            
            return message.create_response({
                "found": True,
                "key": file_id_hex,
                "providers": providers
            }, MessageType.FIND_VALUE_RESPONSE)
        
        # 没有找到文件，返回最近的节点，类似FIND_NODE
        closest_nodes = self.routing_table.find_closest_nodes(file_id)
        
        node_list = []
        for node in closest_nodes:
            node_list.append({
                "id": node["id"].hex(),
                "address": node["address"].hex()
            })
        
        return message.create_response({
            "found": False,
            "key": file_id_hex,
            "nodes": node_list
        }, MessageType.FIND_VALUE_RESPONSE)
    
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
        
        # 检查是否找到文件
        if message.content.get("found", False):
            # 找到了文件提供者
            providers = message.content.get("providers", [])
            
            for provider_info in providers:
                address = bytes.fromhex(provider_info["address"])
                last_seen = provider_info.get("last_seen", self.simulator.get_current_time())
                
                # 更新文件提供者信息
                if file_id not in self.file_providers:
                    self.file_providers[file_id] = []
                
                # 检查是否已经有这个提供者
                provider_exists = False
                for i, existing_provider in enumerate(self.file_providers[file_id]):
                    if existing_provider["address"] == address:
                        # 更新最后见到时间
                        self.file_providers[file_id][i]["last_seen"] = last_seen
                        provider_exists = True
                        break
                
                if not provider_exists:
                    # 添加新提供者
                    self.file_providers[file_id].append({
                        "address": address,
                        "last_seen": last_seen
                    })
        else:
            # 没找到文件，继续向返回的节点查询
            nodes = message.content.get("nodes", [])
            
            for node_info in nodes:
                node_id = bytes.fromhex(node_info["id"])
                address = bytes.fromhex(node_info["address"])
                
                # 更新路由表
                self.routing_table.update(node_id, address, self.simulator.get_current_time())
                
                # 继续查询
                self._send_find_value(node_id, file_id)
        
        return None
    
    def _send_store(self, target_id: bytes, file_id: bytes, provider_address: bytes) -> None:
        """发送STORE请求"""
        message = Message(
            MessageType.STORE,
            self.node_id,
            target_id,
            {
                "key": file_id.hex(),
                "provider": provider_address.hex()
            }
        )
        
        # 保存回调信息
        self.pending_responses[message.transaction_id] = {
            "type": "store",
            "data": {"file_id": file_id},
            "time": self.simulator.get_current_time()
        }
        
        self.simulator.send_message(message)
    
    def _handle_store(self, message: Message) -> Message:
        """处理STORE请求"""
        file_id_hex = message.content.get("key")
        provider_hex = message.content.get("provider")
        
        if not file_id_hex or not provider_hex:
            return None
        
        file_id = bytes.fromhex(file_id_hex)
        provider_address = bytes.fromhex(provider_hex)
        current_time = self.simulator.get_current_time()
        
        # 存储提供者信息
        if file_id not in self.file_providers:
            self.file_providers[file_id] = []
        
        # 检查是否已存在
        provider_exists = False
        for i, existing_provider in enumerate(self.file_providers[file_id]):
            if existing_provider["address"] == provider_address:
                # 更新最后见到时间
                self.file_providers[file_id][i]["last_seen"] = current_time
                provider_exists = True
                break
        
        if not provider_exists:
            # 添加新提供者
            self.file_providers[file_id].append({
                "address": provider_address,
                "last_seen": current_time
            })
        
        # 返回确认
        return message.create_response({"status": "success"}, MessageType.STORE_RESPONSE)
    
    def _handle_store_response(self, message: Message) -> None:
        """处理STORE响应"""
        if message.transaction_id in self.pending_responses:
            callback_info = self.pending_responses.pop(message.transaction_id)
            # STORE响应通常不需要额外处理
        return None
