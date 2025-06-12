import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routing_table import RoutingTable, KBucket


from unittest.mock import MagicMock
from dht_node import DHTNode
from interfaces import ISimulator
from id_util import IDUtil
class TestRoutingTable(unittest.TestCase):
    def setUp(self):
        self.node_id = IDUtil.generate_random_id()
        self.routing_table = RoutingTable(self.node_id)

    def test_update(self):
        other_node_id = IDUtil.generate_random_id()
        address = b'127.0.0.1'
        last_seen = 1
        result = self.routing_table.update(other_node_id, address, last_seen)
        self.assertEqual(result, True)

    def test_find_closest_nodes(self):
        target_id = IDUtil.generate_random_id()
        nodes = self.routing_table.find_closest_nodes(target_id)
        self.assertEqual(len(nodes), 0)

if __name__ == '__main__':
    unittest.main()