import unittest
from src.adapters.prov_adapter import ProvAdapter
from src.graph.wrapper import ProvGraphWrapper
from prov.model import ProvEntity, ProvActivity, ProvDocument


class TestProvAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = ProvAdapter()
        # Create a PROV document for testing
        self.doc = ProvDocument()
        self.doc.add_namespace('ex', 'http://example.org/')

    def test_from_prov_document(self):
        entity1 = self.doc.entity('ex:entity1')
        entity2 = self.doc.entity('ex:entity2')
        activity = self.doc.activity('ex:activity1')

        self.doc.used(activity, entity1)
        self.doc.wasGeneratedBy(entity2, activity)

        graph = self.adapter.from_prov_document(self.doc)

        self.assertIsInstance(graph, ProvGraphWrapper)
        self.assertTrue(len(graph.get_nodes()) >= 2)

    def test_to_prov_document(self):
        graph = ProvGraphWrapper(self.doc)
        entity = self.doc.entity('ex:test_entity')
        graph.add_entity_as_node(entity)

        converted_doc = self.adapter.to_prov_document(graph)

        self.assertIsInstance(converted_doc, ProvDocument)
        entities = list(converted_doc.get_records(ProvEntity))
        self.assertTrue(len(entities) >= 1)

    def test_create_simple_graph(self):
        entities = ['entity1', 'entity2', 'entity3']
        activities = [('activity1', 'entity1', 'entity2'), ('activity2', 'entity2', 'entity3')]

        graph = self.adapter.create_simple_graph(entities, activities)

        self.assertIsInstance(graph, ProvGraphWrapper)
        # With PROV-DM: 3 entities + 2 activities = 5 nodes
        self.assertEqual(len(graph.get_nodes()), 5)
        # 2 activities × 2 relations each (usage + generation) = 4 edges
        self.assertEqual(len(graph.get_edges()), 4)

    def test_add_entity_to_graph(self):
        graph = ProvGraphWrapper()

        node = self.adapter.add_entity_to_graph(graph, 'new_entity', {'type': 'test'})

        self.assertIsNotNone(node)
        self.assertIn(node, graph.get_nodes())
        self.assertEqual(node.kind, "PROV_ENTITY")

    def test_add_activity_to_graph(self):
        graph = ProvGraphWrapper()

        node1 = self.adapter.add_entity_to_graph(graph, 'source_entity')
        node2 = self.adapter.add_entity_to_graph(graph, 'target_entity')

        # Activity is now added as a node (PROV-DM compliant)
        activity_node = self.adapter.add_activity_to_graph(graph, 'test_activity', 'source_entity', 'target_entity')

        if activity_node:
            self.assertIn(activity_node, graph.get_nodes())
            # Relations should create edges
            self.assertGreater(len(graph.get_edges()), 0)

    def test_export_to_formats(self):
        entities = ['e1', 'e2']
        activities = [('a1', 'e1', 'e2')]
        graph = self.adapter.create_simple_graph(entities, activities)

        exports = self.adapter.export_to_formats(graph, ['json'])

        self.assertIn('json', exports)
        self.assertIsInstance(exports['json'], str)
        self.assertTrue(len(exports['json']) > 0)

    def test_import_from_formats(self):
        entities = ['test_entity']
        graph = self.adapter.create_simple_graph(entities, [])
        exports = self.adapter.export_to_formats(graph, ['json'])

        imported_graph = self.adapter.import_from_formats(exports['json'], 'json')

        self.assertIsInstance(imported_graph, ProvGraphWrapper)
        self.assertTrue(len(imported_graph.get_nodes()) >= 1)

    def test_merge_graphs(self):
        graph1 = self.adapter.create_simple_graph(['e1'], [])
        graph2 = self.adapter.create_simple_graph(['e2'], [])

        merged = self.adapter.merge_graphs(graph1, graph2)

        self.assertIsInstance(merged, ProvGraphWrapper)
        self.assertTrue(len(merged.get_nodes()) >= 2)

    def test_get_graph_statistics(self):
        entities = ['e1', 'e2', 'e3']
        activities = [('a1', 'e1', 'e2')]
        graph = self.adapter.create_simple_graph(entities, activities)

        stats = self.adapter.get_graph_statistics(graph)

        self.assertIsInstance(stats, dict)
        self.assertIn('num_nodes', stats)
        self.assertIn('num_edges', stats)
        self.assertIn('is_connected', stats)
        # With PROV-DM: 3 entities + 1 activity = 4 nodes
        self.assertEqual(stats['num_nodes'], 4)


if __name__ == '__main__':
    unittest.main()
