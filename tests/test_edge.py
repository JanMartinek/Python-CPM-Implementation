import unittest
from src.graph.wrapper import ProvGraphWrapper
from src.graph.node import GraphNode
from src.graph.edge import GraphEdge
from prov.model import ProvDocument



class TestEdge(unittest.TestCase):

    def setUp(self):
        self.graph = ProvGraphWrapper()

        # Create PROV document with proper namespace
        self.doc = ProvDocument()
        self.doc.add_namespace('ex', 'http://example.org/')

        # Create entities with proper identifiers
        self.entity1 = self.doc.entity('ex:entity1')
        self.entity2 = self.doc.entity('ex:entity2')

        # Create a PROV usage relation for the edge
        self.activity = self.doc.activity('ex:activity1')
        self.usage_relation = self.doc.used(self.activity, self.entity1)

        # Create nodes using the actual GraphNode class
        self.node1 = GraphNode(self.entity1)
        self.node2 = GraphNode(self.entity2)

        # Create edge using the actual GraphEdge class and ProvUsage relation
        self.edge = GraphEdge(self.usage_relation, self.node1, self.node2)

    def test_edge_creation(self):
        self.assertEqual(self.edge.prov_relation, self.usage_relation)
        self.assertEqual(self.edge.cause, self.node1)
        self.assertEqual(self.edge.effect, self.node2)

    def test_edge_kind(self):
        self.assertEqual(self.edge.kind, 'PROV_USAGE')

    def test_edge_nodes_connection(self):
        self.assertTrue(self.edge.is_between(self.node1, self.node2))
        self.assertTrue(self.edge.connects_node(self.node1))
        self.assertTrue(self.edge.connects_node(self.node2))
        self.assertEqual(self.edge.get_other_node(self.node1), self.node2)
        self.assertEqual(self.edge.get_other_node(self.node2), self.node1)

    def test_edge_relations(self):
        relations = self.edge.relations.copy()
        self.assertIn(self.usage_relation, relations)
        # For any_relation, use the first relation or prov_relation
        any_relation = self.edge.relations[0] if self.edge.relations else self.edge.prov_relation
        self.assertEqual(any_relation, self.usage_relation)

        generation_relation = self.doc.wasGeneratedBy(self.entity2, self.activity)
        usage_relation2 = self.doc.used(self.activity, self.entity2)
        self.assertTrue(self.edge.add_relation(usage_relation2))
        self.assertIn(usage_relation2, self.edge.relations)

    def test_edge_attributes(self):
        if hasattr(self.usage_relation, 'attributes'):
            attributes = self.edge.get_attributes()
            self.assertIsInstance(attributes, list)

    def test_edge_clone(self):
        cloned_edge = self.edge.clone()
        self.assertIsNot(cloned_edge, self.edge)
        self.assertEqual(cloned_edge.cause, self.edge.cause)
        self.assertEqual(cloned_edge.effect, self.edge.effect)
        self.assertEqual(cloned_edge.kind, self.edge.kind)

    def test_edge_reverse(self):
        reversed_edge = self.edge.reverse()
        self.assertEqual(reversed_edge.cause, self.node2)
        self.assertEqual(reversed_edge.effect, self.node1)

    def test_graph_wrapper_with_edges(self):
        """Test that relations create edges in the graph wrapper"""
        # Create a document with relations
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        # Create relations (these become edges)
        doc.used(activity, entity1)
        doc.wasGeneratedBy(entity2, activity)

        # Import into wrapper
        wrapper = ProvGraphWrapper(doc)

        # Check nodes exist (entities and activity)
        nodes = wrapper.get_nodes()
        self.assertEqual(len(nodes), 3)

        # Check edges exist (relations)
        edges = wrapper.get_edges()
        self.assertEqual(len(edges), 2)


if __name__ == '__main__':
    unittest.main()
