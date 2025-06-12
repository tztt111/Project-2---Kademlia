import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock
from dht_node import DHTNode
from interfaces import ISimulator
from id_util import IDUtil

class TestDHTNode(unittest.TestCase):
    def setUp(self):
        self.node_id = IDUtil.generate_random_id()
        self.address = b'127.0.0.1'
        self.simulator = MagicMock(spec=ISimulator)
        self.node = DHTNode(self.node_id, self.address, self.simulator)

    def test_get_id(self):
        self.assertEqual(self.node.get_id(), self.node_id)

    def test_get_address(self):
        self.assertEqual(self.node.get_address(), self.address)

    def test_join_network(self):
        seed_node_id = IDUtil.generate_random_id()
        self.node.join_network(seed_node_id)
        self.assertEqual(self.node.is_online, True)
        self.simulator.schedule_event.assert_called_once()

if __name__ == '__main__':
    unittest.main()