# dht_simulator.py
import random
from typing import Dict, List, Any, Optional
from interfaces import ISimulator, INode
from event_system import Event, EventType, EventEmitter
from event_queue import EventQueue
from simulation_clock import SimulationClock
from message import Message
from logger import Logger
from config import Config
from id_util import IDUtil

class DHTSimulator(ISimulator):
    """DHT网络模拟器"""
    def __init__(self, config: Config):
        self.config = config
        self.clock = SimulationClock(config.get("simulation.time_tick_ms", 100))
        self.event_queue = EventQueue()
        self.event_emitter = EventEmitter()
        self.logger = Logger(config)
        self.nodes: Dict[bytes, INode] = {}  # 节点字典，ID -> 节点
        
        # 随机数生成器，使用固定种子以确保可重现性
        self.random = random.Random(config.get("simulation.random_seed"))
        
        # 注册时钟回调
        self.clock.add_tick_callback(self._on_clock_tick)
    
    def run(self, max_time: Optional[int] = None) -> None:
        """运行模拟器直到结束或达到最大时间"""
        # 发送模拟开始事件
        self.schedule_event(Event(
            EventType.SIMULATION_START,
            self.clock.get_time(),
            {}
        ))
        
        # 如果没有指定最大时间，使用配置
        if max_time is None:
            max_time = self.config.get("simulation.max_time")
        
        # 主循环
        while self.event_queue.has_events():
            # 获取下一个事件时间
            next_event_time = self.event_queue.peek_time()
            
            # 检查是否达到最大时间
            if max_time is not None and next_event_time > max_time:
                break
            
            # 设置时钟
            self.clock.set_time(next_event_time)
            
            # 处理当前时间的所有事件
            while self.event_queue.has_events() and self.event_queue.peek_time() == next_event_time:
                event = self.event_queue.pop_event()
                self._process_event(event)
        
        # 发送模拟结束事件
        self.schedule_event(Event(
            EventType.SIMULATION_END,
            self.clock.get_time(),
            {}
        ))
        
        # 处理最终事件
        while self.event_queue.has_events():
            event = self.event_queue.pop_event()
            if event.type == EventType.SIMULATION_END:
                self._process_event(event)
    
    def _on_clock_tick(self, time: int) -> None:
        """时钟滴答回调"""
        # 发出时钟滴答事件
        self.event_emitter.emit(Event(
            EventType.SIMULATION_TICK,
            time,
            {"time": time}
        ))
    
    def _process_event(self, event: Event) -> None:
        """处理单个事件"""
        # 记录事件
        self.logger.debug(
            self.clock.get_time(),
            "Event",
            f"Processing event: {event.type.name}",
            {"event_type": event.type.name, "params": event.params}
        )
        
        # 发送事件到订阅者
        self.event_emitter.emit(event)
        
        # 根据事件类型处理
        if event.type == EventType.NODE_JOIN:
            node_id = event.params.get("node_id")
            if node_id in self.nodes:
                node = self.nodes[node_id]
                # 处理节点加入
                self.logger.info(
                    self.clock.get_time(),
                    "Node",
                    f"Node {node_id.hex()[:8]} joined the network"
                )
        
        elif event.type == EventType.NODE_LEAVE:
            node_id = event.params.get("node_id")
            if node_id in self.nodes:
                # 处理节点离开
                self.logger.info(
                    self.clock.get_time(),
                    "Node",
                    f"Node {node_id.hex()[:8]} left the network"
                )
                # 可以选择从nodes字典中移除
                # self.nodes.pop(node_id)
        
        elif event.type == EventType.FILE_PUBLISH:
            node_id = event.params.get("node_id")
            file_id = event.params.get("file_id")
            if node_id and file_id:
                self.logger.info(
                    self.clock.get_time(),
                    "File",
                    f"Node {node_id.hex()[:8]} is publishing file {file_id.hex()[:8]}"
                )
        
        elif event.type == EventType.FILE_RETRIEVE:
            node_id = event.params.get("node_id")
            file_id = event.params.get("file_id")
            if node_id and file_id:
                self.logger.info(
                    self.clock.get_time(),
                    "File",
                    f"Node {node_id.hex()[:8]} is retrieving file {file_id.hex()[:8]}"
                )
    
    def send_message(self, message: Message) -> None:
        """发送消息（由节点调用）"""
        # 设置消息发送时间
        message.send_time = self.clock.get_time()
        
        # 检查目标节点是否存在
        if message.target_id not in self.nodes:
            self.logger.warning(
                self.clock.get_time(),
                "Message",
                f"Message target node {message.target_id.hex()[:8]} not found"
            )
            return
        
        # 模拟网络延迟
        min_delay = self.config.get("network.min_delay", 1)
        max_delay = self.config.get("network.max_delay", 3)
        delay = self.random.randint(min_delay, max_delay)
        
        # 模拟丢包
        packet_loss_rate = self.config.get("network.packet_loss_rate", 0.0)
        if self.random.random() < packet_loss_rate:
            self.logger.debug(
                self.clock.get_time(),
                "Message",
                f"Message from {message.source_id.hex()[:8]} to {message.target_id.hex()[:8]} dropped"
            )
            
            # 发送消息丢失事件
            self.event_emitter.emit(Event(
                EventType.MESSAGE_DROPPED,
                self.clock.get_time(),
                {"message": message.to_dict()}
            ))
            return
        
        # 设置消息投递时间
        delivery_time = message.send_time + delay
        message.delivery_time = delivery_time
        
        # 记录消息发送
        self.logger.debug(
            self.clock.get_time(),
            "Message",
            f"Message from {message.source_id.hex()[:8]} to {message.target_id.hex()[:8]} sent, "
            f"type: {message.type.name}, delivery in {delay} ticks"
        )
        
        # 安排消息投递事件
        self.schedule_event(Event(
            EventType.MESSAGE_RECEIVED,
            delivery_time,
            {"message": message.to_dict()}
        ))
        
        # 发送消息发送事件
        self.event_emitter.emit(Event(
            EventType.MESSAGE_SENT,
            self.clock.get_time(),
            {"message": message.to_dict()}
        ))
    
    def schedule_event(self, event: Event) -> None:
        """调度一个新事件"""
        self.event_queue.schedule(event)
    
    def get_current_time(self) -> int:
        """获取当前模拟时间"""
        return self.clock.get_time()
    
    def register_node(self, node: INode) -> None:
        """注册节点到模拟器"""
        node_id = node.get_id()
        if node_id in self.nodes:
            self.logger.warning(
                self.clock.get_time(),
                "Node",
                f"Node {node_id.hex()[:8]} already registered"
            )
            return
        
        self.nodes[node_id] = node
        self.logger.debug(
            self.clock.get_time(),
            "Node",
            f"Node {node_id.hex()[:8]} registered"
        )
        
        # 监听消息接收事件
        self.event_emitter.on(EventType.MESSAGE_RECEIVED, self._on_message_received)
    
    def unregister_node(self, node_id: bytes) -> None:
        """从模拟器中移除节点"""
        if node_id in self.nodes:
            self.nodes.pop(node_id)
            self.logger.debug(
                self.clock.get_time(),
                "Node",
                f"Node {node_id.hex()[:8]} unregistered"
            )
    
    def _on_message_received(self, event: Event) -> None:
        """处理消息接收事件"""
        message_dict = event.params.get("message")
        if not message_dict:
            return
        
        # 重建消息对象
        message = Message.from_dict(message_dict)
        
        # 检查目标节点是否存在
        if message.target_id not in self.nodes:
            self.logger.warning(
                self.clock.get_time(),
                "Message",
                f"Message target node {message.target_id.hex()[:8]} not found"
            )
            return
        
        # 获取目标节点
        target_node = self.nodes[message.target_id]
        
        # 让目标节点处理消息
        self.logger.debug(
            self.clock.get_time(),
            "Message",
            f"Delivering message from {message.source_id.hex()[:8]} to {message.target_id.hex()[:8]}, "
            f"type: {message.type.name}"
        )
        
        response = target_node.handle_message(message)
        
        # 如果有响应，发送回去
        if response:
            self.send_message(response)
    
    def create_seed_node(self, node_id: bytes, address: bytes) -> INode:
        """创建并注册种子节点"""
        from dht_node import DHTNode  # 避免循环导入
        
        # 创建种子节点
        seed_node = DHTNode(
            node_id,
            address,
            self,
            self.config.get("dht.k_value", 8),
            self.config.get("dht.id_bits", 160)
        )
        
        # 设置为在线
        seed_node.is_online = True
        
        # 发送节点加入事件
        self.schedule_event(Event(
            EventType.NODE_JOIN,
            self.clock.get_time(),
            {"node_id": node_id, "address": address}
        ))
        
        return seed_node
    
    def get_all_nodes(self) -> Dict[bytes, INode]:
        """获取所有节点"""
        return self.nodes.copy()
    
    def get_network_state(self) -> Dict[str, Any]:
        """获取当前网络状态"""
        node_states = {}
        for node_id, node in self.nodes.items():
            # 假设节点有一个get_state方法，将其状态转换为可序列化的格式
            if hasattr(node, 'get_state'):
                node_states[node_id.hex()] = node.get_state()
            else:
                # 基本信息
                node_states[node_id.hex()] = {
                    "id": node_id.hex(),
                    "address": node.get_address().hex(),
                    "is_online": getattr(node, 'is_online', False)
                }
        
        return {
            "time": self.clock.get_time(),
            "node_count": len(self.nodes),
            "nodes": node_states,
            "events_pending": self.event_queue.count()
        }
