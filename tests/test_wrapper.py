import unittest
from src.graph.wrapper import ProvGraphWrapper
from prov.model import ProvEntity, ProvActivity, ProvDocument


class TestProvGraphWrapper(unittest.TestCase):

    def setUp(self):
        self.graph_wrapper = ProvGraphWrapper()
        # Create a PROV document for proper entity/activity creation
        self.doc = ProvDocument()
        self.doc.add_namespace('ex', 'http://example.org/')

    def test_add_entity_as_node(self):
        entity = self.doc.entity('ex:entity1')
        node = self.graph_wrapper.add_entity_as_node(entity)

        self.assertIsNotNone(node)
        self.assertIn(node, self.graph_wrapper.get_nodes())
        self.assertEqual(node.prov_entity, entity)

    def test_add_activity_as_edge(self):
        """Test that activities are now nodes, not edges (PROV-DM compliant)"""
        entity1 = self.doc.entity('ex:entity1')
        entity2 = self.doc.entity('ex:entity2')
        activity = self.doc.activity('ex:activity1')

        # Add relations to create edges
        self.doc.used(activity, entity1)
        self.doc.wasGeneratedBy(entity2, activity)

        # Import the document into the wrapper
        wrapper = ProvGraphWrapper(self.doc)

        # Activity should be a node now
        nodes = wrapper.get_nodes()
        activity_nodes = [n for n in nodes if hasattr(n.prov_entity, 'identifier')
                          and str(n.prov_entity.identifier) == 'ex:activity1']
        self.assertEqual(len(activity_nodes), 1)

        # Relations should be edges
        edges = wrapper.get_edges()
        self.assertGreater(len(edges), 0)

    def test_add_activity_as_node(self):
        activity = self.doc.activity('ex:activity1')
        node = self.graph_wrapper.add_activity_as_node(activity)

        self.assertIsNotNone(node)
        self.assertIn(node, self.graph_wrapper.get_nodes())
        self.assertEqual(node.prov_entity, activity)

    def test_get_nodes(self):
        entity1 = self.doc.entity('ex:entity1')
        entity2 = self.doc.entity('ex:entity2')

        node1 = self.graph_wrapper.add_entity_as_node(entity1)
        node2 = self.graph_wrapper.add_entity_as_node(entity2)

        nodes = self.graph_wrapper.get_nodes()
        self.assertEqual(len(nodes), 2)
        self.assertIn(node1, nodes)
        self.assertIn(node2, nodes)

    def test_get_edges(self):
        """Test getting edges from relations"""
        entity1 = self.doc.entity('ex:entity1')
        entity2 = self.doc.entity('ex:entity2')
        activity = self.doc.activity('ex:activity1')

        # Create relations (these become edges)
        self.doc.used(activity, entity1)
        self.doc.wasGeneratedBy(entity2, activity)

        # Import into wrapper
        wrapper = ProvGraphWrapper(self.doc)

        edges = wrapper.get_edges()
        self.assertEqual(len(edges), 2)  # Two relations = two edges

    def test_networkx_integration(self):
        entity1 = self.doc.entity('ex:entity1')
        entity2 = self.doc.entity('ex:entity2')

        node1 = self.graph_wrapper.add_entity_as_node(entity1)
        node2 = self.graph_wrapper.add_entity_as_node(entity2)

        nx_graph = self.graph_wrapper.get_networkx_graph()
        self.assertIsNotNone(nx_graph)

        self.assertTrue(len(nx_graph.nodes()) >= 2)

    def test_prov_document_import(self):
        doc_with_data = ProvDocument()
        doc_with_data.add_namespace('test', 'http://test.org/')

        entity1 = doc_with_data.entity('test:e1')
        entity2 = doc_with_data.entity('test:e2')
        activity = doc_with_data.activity('test:a1')

        wrapper = ProvGraphWrapper(doc_with_data)

        nodes = wrapper.get_nodes()
        self.assertTrue(len(nodes) >= 2)

    def test_clear_graph(self):
        entity = self.doc.entity('ex:entity1')
        self.graph_wrapper.add_entity_as_node(entity)

        self.assertTrue(len(self.graph_wrapper.get_nodes()) > 0)

        self.graph_wrapper.clear()
        self.assertEqual(len(self.graph_wrapper.get_nodes()), 0)
        self.assertEqual(len(self.graph_wrapper.get_edges()), 0)


if __name__ == '__main__':
    unittest.main()
