"""
Tests for CPM Factory classes (DividedCpmFactory, MergedCpmFactory, CpmFactoryManager)
"""

import pytest
from prov.model import ProvDocument
from prov.identifier import QualifiedName

from src.graph.factory import (
    DividedCpmFactory, MergedCpmFactory, CpmFactoryManager,
    create_node, create_edge, clone_graph, merge_graphs
)
from src.graph.node import GraphNode, DividedGraphNode, MergedGraphNode
from src.graph.edge import GraphEdge, DividedGraphEdge, MergedGraphEdge
from src.graph.wrapper import ProvGraphWrapper


class TestDividedCpmFactory:
    """Test DividedCpmFactory functionality"""

    def test_factory_type(self):
        """Test factory type identification"""
        factory = DividedCpmFactory()
        assert factory.get_factory_type() == "DIVIDED"

    def test_create_node_single_element(self):
        """Test creating a node with single element"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        factory = DividedCpmFactory()
        node = factory.create_node([entity])

        assert isinstance(node, DividedGraphNode)
        assert len(node.elements) == 1

    def test_create_node_multiple_elements(self):
        """Test creating a node with multiple elements"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        factory = DividedCpmFactory()
        node = factory.create_node([entity1, entity2])

        assert isinstance(node, DividedGraphNode)
        assert len(node.elements) == 2

    def test_create_node_requires_elements(self):
        """Test that create_node requires at least one element"""
        factory = DividedCpmFactory()

        with pytest.raises(ValueError, match="At least one element"):
            factory.create_node([])

    def test_create_edge(self):
        """Test creating an edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        factory = DividedCpmFactory()
        node1 = factory.create_node([entity1])
        node2 = factory.create_node([entity2])
        edge = factory.create_edge([usage], node1, node2)

        assert isinstance(edge, DividedGraphEdge)
        assert len(edge.relations) == 1

    def test_create_edge_multiple_relations(self):
        """Test creating an edge with multiple relations"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        factory = DividedCpmFactory()
        node1 = factory.create_node([entity1])
        node2 = factory.create_node([entity2])
        edge = factory.create_edge([usage1, usage2], node1, node2)

        assert isinstance(edge, DividedGraphEdge)
        assert len(edge.relations) == 2

    def test_create_edge_requires_relations(self):
        """Test that create_edge requires at least one relation"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        factory = DividedCpmFactory()
        node1 = factory.create_node([entity1])
        node2 = factory.create_node([entity2])

        with pytest.raises(ValueError, match="At least one relation"):
            factory.create_edge([], node1, node2)

    def test_clone_node(self):
        """Test cloning a node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        factory = DividedCpmFactory()
        node = factory.create_node([entity])
        cloned_node = factory.clone_node(node)

        assert cloned_node is not node
        assert isinstance(cloned_node, DividedGraphNode)
        assert cloned_node.identifier == node.identifier

    def test_clone_node_with_edges(self):
        """Test cloning a node with edge references"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        factory = DividedCpmFactory()
        node1 = factory.create_node([entity1])
        node2 = factory.create_node([entity2])
        edge = factory.create_edge([usage], node1, node2)

        node1.add_cause_edge(edge)
        cloned_node = factory.clone_node(node1, include_edges=True)

        assert len(cloned_node.cause_edges) == 1

    def test_clone_edge(self):
        """Test cloning an edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        factory = DividedCpmFactory()
        node1 = factory.create_node([entity1])
        node2 = factory.create_node([entity2])
        edge = factory.create_edge([usage], node1, node2)

        cloned_edge = factory.clone_edge(edge)

        assert cloned_edge is not edge
        assert isinstance(cloned_edge, DividedGraphEdge)
        assert cloned_edge.cause == edge.cause
        assert cloned_edge.effect == edge.effect

    def test_clone_edge_with_node_mapping(self):
        """Test cloning an edge with node mapping"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        entity3 = doc.entity('ex:entity3')
        usage = doc.usage(entity1, entity2)

        factory = DividedCpmFactory()
        node1 = factory.create_node([entity1])
        node2 = factory.create_node([entity2])
        node3 = factory.create_node([entity3])
        edge = factory.create_edge([usage], node1, node2)

        node_mapping = {node1: node3}
        cloned_edge = factory.clone_edge(edge, node_mapping)

        assert cloned_edge.cause == node3  # Mapped node
        assert cloned_edge.effect == node2  # Original node

    def test_elements_are_cloned(self):
        """Test that elements are deep copied to ensure isolation"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        factory = DividedCpmFactory()
        node = factory.create_node([entity])

        # Verify element is a different object
        assert node.elements[0] is not entity
        assert node.elements[0] == entity


class TestMergedCpmFactory:
    """Test MergedCpmFactory functionality"""

    def test_factory_type(self):
        """Test factory type identification"""
        factory = MergedCpmFactory()
        assert factory.get_factory_type() == "MERGED"

    def test_create_node_single_element(self):
        """Test creating a merged node (uses only first element)"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        factory = MergedCpmFactory()
        node = factory.create_node([entity1, entity2])

        assert isinstance(node, MergedGraphNode)
        assert len(node.elements) == 1  # Only first element used

    def test_create_node_requires_elements(self):
        """Test that create_node requires at least one element"""
        factory = MergedCpmFactory()

        with pytest.raises(ValueError, match="At least one element"):
            factory.create_node([])

    def test_create_edge(self):
        """Test creating a merged edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        factory = MergedCpmFactory()
        node1 = factory.create_node([entity1])
        node2 = factory.create_node([entity2])
        edge = factory.create_edge([usage], node1, node2)

        assert isinstance(edge, MergedGraphEdge)
        assert len(edge.relations) == 1

    def test_create_edge_uses_first_relation(self):
        """Test that merged edge uses only first relation"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        factory = MergedCpmFactory()
        node1 = factory.create_node([entity1])
        node2 = factory.create_node([entity2])
        edge = factory.create_edge([usage1, usage2], node1, node2)

        assert isinstance(edge, MergedGraphEdge)
        assert len(edge.relations) == 1  # Only first relation

    def test_clone_node(self):
        """Test cloning a merged node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        factory = MergedCpmFactory()
        node = factory.create_node([entity])
        cloned_node = factory.clone_node(node)

        assert cloned_node is not node
        assert isinstance(cloned_node, MergedGraphNode)


class TestCpmFactoryManager:
    """Test CpmFactoryManager functionality"""

    def test_manager_creation_with_default_factory(self):
        """Test creating manager with default factory type"""
        manager = CpmFactoryManager()
        factory = manager.get_factory()

        assert factory.get_factory_type() == "DIVIDED"

    def test_manager_creation_with_custom_default(self):
        """Test creating manager with custom default factory"""
        manager = CpmFactoryManager(default_factory_type="MERGED")
        factory = manager.get_factory()

        assert factory.get_factory_type() == "MERGED"

    def test_get_factory_by_type(self):
        """Test getting factory by type"""
        manager = CpmFactoryManager()

        divided_factory = manager.get_factory("DIVIDED")
        merged_factory = manager.get_factory("MERGED")

        assert divided_factory.get_factory_type() == "DIVIDED"
        assert merged_factory.get_factory_type() == "MERGED"

    def test_get_factory_invalid_type(self):
        """Test getting factory with invalid type"""
        manager = CpmFactoryManager()

        with pytest.raises(ValueError, match="Unknown factory type"):
            manager.get_factory("INVALID")

    def test_create_node_from_elements(self):
        """Test creating node via manager"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        manager = CpmFactoryManager()
        node = manager.create_node_from_elements([entity], factory_type="DIVIDED")

        assert isinstance(node, DividedGraphNode)

    def test_create_edge_from_relations(self):
        """Test creating edge via manager"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        manager = CpmFactoryManager()
        node1 = manager.create_node_from_elements([entity1])
        node2 = manager.create_node_from_elements([entity2])
        edge = manager.create_edge_from_relations([usage], node1, node2, factory_type="DIVIDED")

        assert isinstance(edge, DividedGraphEdge)

    def test_clone_graph(self):
        """Test cloning an entire graph"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        doc.derivation(entity2, entity1)

        wrapper = ProvGraphWrapper(doc)

        manager = CpmFactoryManager()
        cloned_wrapper = manager.clone_graph(wrapper, factory_type="DIVIDED")

        assert cloned_wrapper is not wrapper
        assert len(cloned_wrapper.get_nodes()) == len(wrapper.get_nodes())
        assert len(cloned_wrapper.get_edges()) == len(wrapper.get_edges())

    def test_merge_graphs(self):
        """Test merging multiple graphs"""
        doc1 = ProvDocument()
        doc1.add_namespace('ex', 'http://example.org/')
        entity1 = doc1.entity('ex:entity1')

        doc2 = ProvDocument()
        doc2.add_namespace('ex', 'http://example.org/')
        entity2 = doc2.entity('ex:entity2')

        wrapper1 = ProvGraphWrapper(doc1)
        wrapper2 = ProvGraphWrapper(doc2)

        manager = CpmFactoryManager()
        merged_wrapper = manager.merge_graphs([wrapper1, wrapper2], factory_type="DIVIDED")

        # Merged graph should contain nodes from both
        assert len(merged_wrapper.get_nodes()) >= 2

    def test_merge_empty_graphs(self):
        """Test merging empty graph list"""
        manager = CpmFactoryManager()
        merged_wrapper = manager.merge_graphs([])

        assert len(merged_wrapper.get_nodes()) == 0

    def test_create_subgraph(self):
        """Test creating a subgraph with node filter"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        entity3 = doc.entity('ex:entity3')
        doc.derivation(entity2, entity1)
        doc.derivation(entity3, entity2)

        wrapper = ProvGraphWrapper(doc)

        manager = CpmFactoryManager()

        # Create subgraph with only first two entities
        def node_filter(node):
            return 'entity1' in str(node.identifier) or 'entity2' in str(node.identifier)

        subgraph = manager.create_subgraph(wrapper, node_filter, factory_type="DIVIDED")

        # Subgraph should have fewer nodes
        assert len(subgraph.get_nodes()) <= len(wrapper.get_nodes())

    def test_get_available_factory_types(self):
        """Test getting list of available factory types"""
        manager = CpmFactoryManager()
        types = manager.get_available_factory_types()

        assert "DIVIDED" in types
        assert "MERGED" in types

    def test_set_default_factory_type(self):
        """Test setting default factory type"""
        manager = CpmFactoryManager()
        manager.set_default_factory_type("MERGED")

        factory = manager.get_factory()
        assert factory.get_factory_type() == "MERGED"

    def test_set_invalid_default_factory_type(self):
        """Test setting invalid default factory type"""
        manager = CpmFactoryManager()

        with pytest.raises(ValueError, match="Unknown factory type"):
            manager.set_default_factory_type("INVALID")


class TestFactoryGlobalFunctions:
    """Test global factory convenience functions"""

    def test_global_create_node(self):
        """Test global create_node function"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node = create_node([entity], factory_type="DIVIDED")

        assert isinstance(node, DividedGraphNode)

    def test_global_create_edge(self):
        """Test global create_edge function"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = create_node([entity1])
        node2 = create_node([entity2])
        edge = create_edge([usage], node1, node2, factory_type="DIVIDED")

        assert isinstance(edge, DividedGraphEdge)

    def test_global_clone_graph(self):
        """Test global clone_graph function"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        wrapper = ProvGraphWrapper(doc)
        cloned_wrapper = clone_graph(wrapper, factory_type="DIVIDED")

        assert cloned_wrapper is not wrapper

    def test_global_merge_graphs(self):
        """Test global merge_graphs function"""
        doc1 = ProvDocument()
        doc1.add_namespace('ex', 'http://example.org/')
        entity1 = doc1.entity('ex:entity1')

        doc2 = ProvDocument()
        doc2.add_namespace('ex', 'http://example.org/')
        entity2 = doc2.entity('ex:entity2')

        wrapper1 = ProvGraphWrapper(doc1)
        wrapper2 = ProvGraphWrapper(doc2)

        merged_wrapper = merge_graphs([wrapper1, wrapper2], factory_type="DIVIDED")

        assert len(merged_wrapper.get_nodes()) >= 2
