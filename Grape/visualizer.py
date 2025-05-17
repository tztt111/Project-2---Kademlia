# visualizer.py
import os
import json
import time
import matplotlib.pyplot as plt
import networkx as nx
from typing import Dict, List, Any, Optional
from event_system import EventType
from id_util import IDUtil

class NetworkVisualizer:
    """Kademlia网络可视化器"""
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 节点和连接的历史记录
        self.nodes = {}  # node_id -> node_info
        self.files = {}  # file_id -> [provider_nodes]
        self.events = []  # 重要事件列表
        
        # 统计信息
        self.stats = {
            "total_messages": 0,
            "node_joins": 0,
            "node_leaves": 0,
            "file_publishes": 0,
            "file_retrievals": 0,
            "messages_by_type": {}
        }
    
    def record_event(self, event_type: EventType, time: int, params: Dict):
        """记录重要网络事件"""
        # 简化的事件信息
        event_info = {
            "type": event_type.name,
            "time": time,
        }
        
        # 根据事件类型添加特定信息
        if event_type == EventType.NODE_JOIN:
            node_id = params.get("node_id")
            if node_id:
                event_info["node_id"] = node_id.hex()[:8] + "..."
                self.stats["node_joins"] += 1
                # 记录节点信息
                self.nodes[node_id.hex()] = {
                    "join_time": time,
                    "address": params.get("address", b"").hex(),
                    "is_online": True
                }
        
        elif event_type == EventType.NODE_LEAVE:
            node_id = params.get("node_id")
            if node_id:
                event_info["node_id"] = node_id.hex()[:8] + "..."
                self.stats["node_leaves"] += 1
                if node_id.hex() in self.nodes:
                    self.nodes[node_id.hex()]["is_online"] = False
                    self.nodes[node_id.hex()]["leave_time"] = time
        
        elif event_type == EventType.FILE_PUBLISH:
            node_id = params.get("node_id")
            file_id = params.get("file_id")
            if node_id and file_id:
                event_info["node_id"] = node_id.hex()[:8] + "..."
                event_info["file_id"] = file_id.hex()[:8] + "..."
                self.stats["file_publishes"] += 1
                # 记录文件信息
                file_hex = file_id.hex()
                if file_hex not in self.files:
                    self.files[file_hex] = []
                self.files[file_hex].append({
                    "provider": node_id.hex(),
                    "time": time
                })
        
        elif event_type == EventType.FILE_RETRIEVE:
            node_id = params.get("node_id")
            file_id = params.get("file_id")
            if node_id and file_id:
                event_info["node_id"] = node_id.hex()[:8] + "..."
                event_info["file_id"] = file_id.hex()[:8] + "..."
                self.stats["file_retrievals"] += 1
        
        elif event_type == EventType.MESSAGE_SENT:
            message = params.get("message", {})
            msg_type = message.get("type", "unknown")
            self.stats["total_messages"] += 1
            if msg_type not in self.stats["messages_by_type"]:
                self.stats["messages_by_type"][msg_type] = 0
            self.stats["messages_by_type"][msg_type] += 1
        
        # 添加到事件列表
        self.events.append(event_info)
    
    def record_network_state(self, network_state: Dict):
        """记录网络最终状态"""
        self.final_state = network_state
        
        # 保存为JSON文件
        with open(os.path.join(self.output_dir, "network_state.json"), 'w') as f:
            json.dump(network_state, f, indent=2)
    
    def generate_network_graph(self, routing_tables=None):
        """生成网络拓扑图"""
        G = nx.Graph()
        
        # 添加节点
        for node_id, node_info in self.nodes.items():
            if node_info.get("is_online", False):
                short_id = node_id[:8]  # 截断ID以便显示
                G.add_node(short_id, full_id=node_id)
        
        # 如果有路由表信息，添加边
        if routing_tables:
            for node_id, routes in routing_tables.items():
                short_id = node_id[:8]
                for connected_id in routes:
                    short_connected = connected_id[:8]
                    if G.has_node(short_connected):
                        G.add_edge(short_id, short_connected)
        
        # 从最终状态提取连接信息
        elif hasattr(self, 'final_state') and 'nodes' in self.final_state:
            for node_id, node_data in self.final_state['nodes'].items():
                short_id = node_id[:8]
                if 'routing_table' in node_data:
                    for connected_id in node_data['routing_table']:
                        short_connected = connected_id[:8]
                        if G.has_node(short_connected):
                            G.add_edge(short_id, short_connected)
        
        # 绘制图形
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)  # 使用弹簧布局算法
        nx.draw(G, pos, with_labels=True, node_color='skyblue', 
                node_size=800, font_size=10, font_weight='bold', 
                edge_color='gray', width=0.5, alpha=0.7)
        
        plt.title("Kademlia DHT Network")
        plt.savefig(os.path.join(self.output_dir, "network_graph.png"), dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_report(self):
        """生成HTML报告"""
        # 创建简单的HTML报告
        html = f"""
        
        ```html
        <!DOCTYPE html>
                <html>
                <head>
                    <title>Kademlia DHT Simulation Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1, h2 {{ color: #333; }}
                        .container {{ max-width: 1200px; margin: 0 auto; }}
                        .stats {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                        .events {{ max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; }}
                        .network-graph {{ text-align: center; margin: 20px 0; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Kademlia DHT Simulation Report</h1>
                        <div class="stats">
                            <h2>Statistics</h2>
                            <table>
                                <tr><th>Metric</th><th>Value</th></tr>
                                <tr><td>Total Nodes</td><td>{len(self.nodes)}</td></tr>
                                <tr><td>Online Nodes</td><td>{sum(1 for n in self.nodes.values() if n.get('is_online', False))}</td></tr>
                                <tr><td>Total Files</td><td>{len(self.files)}</td></tr>
                                <tr><td>Node Joins</td><td>{self.stats['node_joins']}</td></tr>
                                <tr><td>Node Leaves</td><td>{self.stats['node_leaves']}</td></tr>
                                <tr><td>File Publishes</td><td>{self.stats['file_publishes']}</td></tr>
                                <tr><td>File Retrievals</td><td>{self.stats['file_retrievals']}</td></tr>
                                <tr><td>Total Messages</td><td>{self.stats['total_messages']}</td></tr>
                            </table>
                            
                            <h3>Message Types</h3>
                            <table>
                                <tr><th>Message Type</th><th>Count</th></tr>
                                {''.join(f"<tr><td>{msg_type}</td><td>{count}</td></tr>" for msg_type, count in self.stats['messages_by_type'].items())}
                            </table>
                        </div>
                        
                        <div class="network-graph">
                            <h2>Network Topology</h2>
                            <img src="network_graph.png" alt="Network Graph" style="max-width: 100%;">
                        </div>
                        
                        <h2>Key Events</h2>
                        <div class="events">
                            <table>
                                <tr><th>Time</th><th>Event</th><th>Details</th></tr>
                                {''.join(self._format_event_row(e) for e in self.events if e['type'] in ['NODE_JOIN', 'NODE_LEAVE', 'FILE_PUBLISH', 'FILE_RETRIEVE'])}
                            </table>
                        </div>
                    </div>
                </body>
                </html>
        ```
        """
    
        # 写入HTML文件
        with open(os.path.join(self.output_dir, "simulation_report.html"), 'w') as f:
            f.write(html)
        
        print(f"Report generated at {os.path.join(self.output_dir, 'simulation_report.html')}")

    def _format_event_row(self, event):
        """格式化事件行HTML"""
        time = event['time']
        event_type = event['type']
        
        details = ""
        if event_type == "NODE_JOIN":
            details = f"Node {event.get('node_id', '?')} joined the network"
        elif event_type == "NODE_LEAVE":
            details = f"Node {event.get('node_id', '?')} left the network"
        elif event_type == "FILE_PUBLISH":
            details = f"Node {event.get('node_id', '?')} published file {event.get('file_id', '?')}"
        elif event_type == "FILE_RETRIEVE":
            details = f"Node {event.get('node_id', '?')} retrieved file {event.get('file_id', '?')}"
        
        return f"<tr><td>{time}</td><td>{event_type}</td><td>{details}</td></tr>"
