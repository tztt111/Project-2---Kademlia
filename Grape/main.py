# main.py
import sys
import json
import os
from typing import List, Dict, Any
from config import Config
from dht_simulator import DHTSimulator
from dht_node import DHTNode
from id_util import IDUtil
from visualizer import NetworkVisualizer  # 导入可视化模块
from event_system import Event, EventType  # 导入事件类型

def load_simulation_events(filename: str) -> List[Dict[str, Any]]:
    """从文件加载模拟事件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            events = json.load(f)
            if not isinstance(events, list):
                print(f"Warning: {filename} 格式不正确，期望事件列表")
                return []
            return events
    except FileNotFoundError:
        print(f"Error: 找不到事件文件 {filename}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: 事件文件 {filename} JSON格式错误: {str(e)}")
        return []

def bytes_from_hex_or_random(hex_str: str = None, length: int = 20) -> bytes:
    """从十六进制字符串创建字节或生成随机字节"""
    if hex_str:
        try:
            # 移除所有空白字符并确保是大写
            hex_str = hex_str.strip().upper()
            return bytes.fromhex(hex_str)
        except ValueError as e:
            print(f"Error converting hex string: {hex_str}")
            print(f"Error message: {str(e)}")
            raise
    return IDUtil.generate_random_id(length*8)

def setup_network_monitoring(simulator, visualizer):
    """设置网络监控"""
    def on_message_dropped(event):
        msg = event.params["message"]
        visualizer.record_event(
            EventType.MESSAGE_DROPPED,
            event.time,
            {
                "source": msg["source_id"][:8],
                "target": msg["target_id"][:8],
                "type": msg["type"],
                "retry_count": msg["content"].get("retry_count", 0)
            }
        )
        print(f"[{event.time}] 丢包: {msg['source_id'][:8]} -> {msg['target_id'][:8]}" + 
              (f" (重试 #{msg['content'].get('retry_count', 0)})" if msg['content'].get('retry_count', 0) > 0 else ""))
    
    def on_message_sent(event):
        msg = event.params["message"]
        retry_count = msg["content"].get("retry_count", 0)
        if retry_count > 0:
            visualizer.record_event(
                EventType.MESSAGE_SENT,
                event.time,
                {
                    "source": msg["source_id"][:8],
                    "target": msg["target_id"][:8],
                    "type": msg["type"],
                    "retry_count": retry_count
                }
            )
            print(f"[{event.time}] 重试 #{retry_count}: {msg['source_id'][:8]} -> {msg['target_id'][:8]}")
    
    simulator.event_emitter.on(EventType.MESSAGE_DROPPED, on_message_dropped)
    simulator.event_emitter.on(EventType.MESSAGE_SENT, on_message_sent)

def main():
    # 加载配置
    config = Config()
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        config.load_from_file(config_file)
    
    # 创建模拟器
    simulator = DHTSimulator(config)
    
    # 创建可视化器
    output_dir = config.get("logging.output_dir", "output")
    visualizer = NetworkVisualizer(output_dir)
    
    # 注册事件监听器
    simulator.event_emitter.on(EventType.NODE_JOIN, lambda e: visualizer.record_event(e.type, e.time, e.params))
    simulator.event_emitter.on(EventType.NODE_LEAVE, lambda e: visualizer.record_event(e.type, e.time, e.params))
    simulator.event_emitter.on(EventType.FILE_PUBLISH, lambda e: visualizer.record_event(e.type, e.time, e.params))
    simulator.event_emitter.on(EventType.FILE_RETRIEVE, lambda e: visualizer.record_event(e.type, e.time, e.params))
    simulator.event_emitter.on(EventType.MESSAGE_SENT, lambda e: visualizer.record_event(e.type, e.time, e.params))
    
    # 设置网络监控
    setup_network_monitoring(simulator, visualizer)
    
    # 加载事件文件
    events_file = config.get("simulation.events_file", "simulation_events.json")
    events = load_simulation_events(events_file)
    
    # 创建种子节点
    seed_config = config.get("seed_node", {})
    seed_id = bytes_from_hex_or_random(seed_config.get("id"))
    seed_address = bytes_from_hex_or_random(seed_config.get("address"), 6)
    
    seed_node = simulator.create_seed_node(seed_id, seed_address)
    
    # 注册事件
    for event_data in events:
        time = event_data.get("time", 0)
        event_type_str = event_data.get("event")
        params = event_data.get("params", {})
        
        # 转换节点ID和文件ID为字节
        if "nodeID" in params:
            params["node_id"] = bytes_from_hex_or_random(params["nodeID"])
            del params["nodeID"]
        
        if "address" in params and isinstance(params["address"], str):
            params["address"] = bytes_from_hex_or_random(params["address"], 6)
        
        if "fileID" in params:
            params["file_id"] = bytes_from_hex_or_random(params["fileID"])
            del params["fileID"]
        
        # 确定事件类型
        event_type = None
        
        if event_type_str == "NODE_JOIN":
            event_type = EventType.NODE_JOIN
            # 创建新节点但暂不上线
            node = DHTNode(
                params["node_id"],
                params["address"],
                simulator,
                config.get("dht.k_value", 8),
                config.get("dht.id_bits", 160)
            )
            # 添加种子节点ID到参数中，用于节点加入时的引导
            params["seed_node_id"] = seed_id
        
        elif event_type_str == "NODE_LEAVE":
            event_type = EventType.NODE_LEAVE
            # 节点离开网络在处理事件时进行
        
        elif event_type_str == "FILE_PUBLISH":
            event_type = EventType.FILE_PUBLISH
            # 发布文件在处理事件时进行
        
        elif event_type_str == "FILE_RETRIEVE":
            event_type = EventType.FILE_RETRIEVE
            # 检索文件在处理事件时进行
        
        if event_type:
            simulator.schedule_event(Event(event_type, time, params))
    
    # 运行模拟
    simulator.run()
    
    # 获取最终网络状态
    final_state = simulator.get_network_state()
    
    # 记录网络状态并生成可视化
    visualizer.record_network_state(final_state)
    visualizer.generate_network_graph()
    visualizer.generate_report()
    
    # 保存到文件
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "network_state.json"), 'w', encoding='utf-8') as f:
        json.dump(final_state, f, indent=2, ensure_ascii=False)
    
    print(f"Simulation completed at time {simulator.get_current_time()}")
    print(f"Processed {len(events)} events")
    print(f"Final network has {len(simulator.get_all_nodes())} nodes")
    print(f"Results saved to {output_dir}/network_state.json")
    print(f"Visualization available at {output_dir}/simulation_report.html")

if __name__ == "__main__":
    main()
