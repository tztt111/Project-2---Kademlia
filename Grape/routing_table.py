# routing_table.py
from typing import List, Dict, Any, Optional, Tuple
from interfaces import IRoutingTable
from id_util import IDUtil

class KBucket:
    """K桶实现，用于存储节点联系信息"""
    def __init__(self, k_value: int = 8):
        self.nodes = []  # 按最后访问时间排序，最近的在末尾
        self.k_value = k_value
        
    def contains(self, node_id: bytes) -> bool:
        """检查K桶是否包含指定节点"""
        return any(entry['id'] == node_id for entry in self.nodes)
    
    def get_node(self, node_id: bytes) -> Optional[Dict[str, Any]]:
        """获取K桶中的指定节点信息"""
        for node in self.nodes:
            if node['id'] == node_id:
                return node
        return None
    
    def add_node(self, node_id: bytes, address: bytes, last_seen: int) -> bool:
        """添加或更新节点信息"""
        # 检查节点是否已存在
        for i, node in enumerate(self.nodes):
            if node['id'] == node_id:
                # 节点存在，移到列表末尾(最近访问)
                self.nodes.pop(i)
                self.nodes.append({
                    'id': node_id,
                    'address': address,
                    'last_seen': last_seen
                })
                return True
        
        # 节点不存在，检查是否有空间
        if len(self.nodes) < self.k_value:
            # 桶未满，直接添加到末尾
            self.nodes.append({
                'id': node_id,
                'address': address,
                'last_seen': last_seen
            })
            return True
        
        # 桶已满，返回False表示需要考虑替换策略
        return False
    
    def remove_node(self, node_id: bytes) -> bool:
        """从K桶移除节点"""
        for i, node in enumerate(self.nodes):
            if node['id'] == node_id:
                self.nodes.pop(i)
                return True
        return False
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """获取K桶中的所有节点"""
        return self.nodes.copy()
    
    def get_oldest_node(self) -> Optional[Dict[str, Any]]:
        """获取K桶中最老的节点（最久未访问）"""
        if not self.nodes:
            return None
        return self.nodes[0]
    
    def size(self) -> int:
        """返回K桶中节点数量"""
        return len(self.nodes)
    
    def is_full(self) -> bool:
        """判断K桶是否已满"""
        return len(self.nodes) >= self.k_value

class RoutingTable(IRoutingTable):
    """Kademlia路由表实现"""
    def __init__(self, node_id: bytes, k_value: int = 8, id_bits: int = 160):
        self.node_id = node_id
        self.k_value = k_value
        self.id_bits = id_bits
        # 创建所有可能的K桶
        self.buckets = [KBucket(k_value) for _ in range(id_bits)]
        
    def update(self, node_id: bytes, address: bytes, last_seen: int) -> bool:
        """更新路由表，添加或刷新节点信息"""
        # 不存储自己的ID
        if node_id == self.node_id:
            return False
        
        # 计算桶索引
        bucket_index = IDUtil.get_bucket_index(self.node_id, node_id)
        if bucket_index < 0:
            return False  # 无效的桶索引
        
        # 尝试添加到对应的K桶
        bucket = self.buckets[bucket_index]
        return bucket.add_node(node_id, address, last_seen)
    
    def find_closest_nodes(self, target_id: bytes, count: int = None) -> List[Dict[str, Any]]:
        """查找最接近目标ID的节点"""
        if count is None:
            count = self.k_value
        
        # 计算所有节点到目标的距离
        nodes_with_distance = []
        for bucket in self.buckets:
            for node in bucket.get_nodes():
                distance = IDUtil.calculate_distance(target_id, node['id'])
                nodes_with_distance.append((distance, node))
        
        # 按距离排序，最近的在前
        nodes_with_distance.sort(key=lambda x: x[0])
        
        # 返回最近的count个节点
        return [node for _, node in nodes_with_distance[:count]]
    
    def remove_node(self, node_id: bytes) -> bool:
        """从路由表中移除节点"""
        bucket_index = IDUtil.get_bucket_index(self.node_id, node_id)
        if bucket_index < 0:
            return False
        
        return self.buckets[bucket_index].remove_node(node_id)
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """获取路由表中的所有节点"""
        all_nodes = []
        for bucket in self.buckets:
            all_nodes.extend(bucket.get_nodes())
        return all_nodes
    
    def get_bucket_for_node(self, node_id: bytes) -> Tuple[int, KBucket]:
        """获取节点应该在的K桶及其索引"""
        bucket_index = IDUtil.get_bucket_index(self.node_id, node_id)
        if bucket_index < 0:
            return (-1, None)
        return (bucket_index, self.buckets[bucket_index])
    
    def get_stats(self) -> Dict[str, Any]:
        """获取路由表统计信息"""
        total_nodes = sum(bucket.size() for bucket in self.buckets)
        non_empty_buckets = sum(1 for bucket in self.buckets if bucket.size() > 0)
        
        return {
            "total_nodes": total_nodes,
            "non_empty_buckets": non_empty_buckets,
            "max_bucket_nodes": max((bucket.size() for bucket in self.buckets), default=0),
            "bucket_distribution": [bucket.size() for bucket in self.buckets]
        }
