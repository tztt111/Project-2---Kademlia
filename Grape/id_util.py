# id_util.py
import os
import hashlib
from typing import Union, Tuple

class IDUtil:
    @staticmethod
    def generate_random_id(bits: int = 160) -> bytes:
        """生成指定位数的随机ID"""
        return os.urandom(bits // 8)
    
    @staticmethod
    def generate_id_from_string(input_string: str, bits: int = 160) -> bytes:
        """从字符串生成ID（如SHA-1哈希）"""
        if bits == 160:
            return hashlib.sha1(input_string.encode()).digest()
        else:
            # 对于非160位的情况，使用SHA-256并截断
            hash_bytes = hashlib.sha256(input_string.encode()).digest()
            return hash_bytes[:bits // 8]
    
    @staticmethod
    def calculate_distance(id1: bytes, id2: bytes) -> int:
        """计算两个ID之间的XOR距离"""
        # 确保两个ID长度相同
        if len(id1) != len(id2):
            raise ValueError(f"ID lengths must be equal (got {len(id1)} and {len(id2)})")
        
        # 按字节计算XOR然后转换为整数
        return int.from_bytes(bytes(a ^ b for a, b in zip(id1, id2)), byteorder='big')
    
    @staticmethod
    def get_bucket_index(self_id: bytes, other_id: bytes) -> int:
        """计算other_id在self_id的路由表中应该属于哪个桶"""
        distance = IDUtil.calculate_distance(self_id, other_id)
        if distance == 0:
            return -1  # 相同的ID
        return (distance.bit_length() - 1)
    
    @staticmethod
    def id_to_hex(id_bytes: bytes) -> str:
        """将ID字节转换为十六进制字符串"""
        return id_bytes.hex()
    
    @staticmethod
    def hex_to_id(hex_string: str) -> bytes:
        """将十六进制字符串转换为ID字节"""
        return bytes.fromhex(hex_string)
