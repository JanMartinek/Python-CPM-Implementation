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


# ═══════════════════════════════════════════════════════════════════════════════
# Additional coverage tests – DividedCpmFactory, MergedCpmFactory,
# CpmFactoryManager, and module-level functions.
# ═══════════════════════════════════════════════════════════════════════════════

from prov.identifier import Namespace
from src.graph.factory import get_factory_manager

EX = Namespace("ex", "http://example.org/")


def _make_entity(local="e1"):
    doc = ProvDocument()
    doc.add_namespace(EX)
    return doc.entity(EX[local])


def _make_activity(local="a1"):
    doc = ProvDocument()
    doc.add_namespace(EX)
    return doc.activity(EX[local])


def _make_agent(local="ag1"):
    doc = ProvDocument()
    doc.add_namespace(EX)
    return doc.agent(EX[local])


def _make_usage_relation():
    doc = ProvDocument()
    doc.add_namespace(EX)
    doc.activity(EX["a1"])
    doc.entity(EX["e1"])
    usage = doc.usage(EX["a1"], EX["e1"])
    return usage


def _make_wrapper_ext():
    """Simple wrapper with two entities + derivation."""
    doc = ProvDocument()
    doc.add_namespace(EX)
    b = doc.bundle(EX["bundle"])
    b.entity(EX["e1"])
    b.entity(EX["e2"])
    b.activity(EX["a1"])
    b.usage(EX["a1"], EX["e1"])
    b.wasGeneratedBy(EX["e2"], EX["a1"])
    b.wasDerivedFrom(EX["e2"], EX["e1"])
    return ProvGraphWrapper(doc)


# ─── DividedCpmFactory (extended) ───────────────────────────────────────────

class TestDividedCpmFactoryExtended:
    def test_create_node(self):
        f = DividedCpmFactory()
        e = _make_entity()
        node = f.create_node([e])
        assert isinstance(node, DividedGraphNode)

    def test_create_node_empty_raises(self):
        f = DividedCpmFactory()
        with pytest.raises(ValueError):
            f.create_node([])

    def test_create_edge(self):
        f = DividedCpmFactory()
        e1 = _make_entity("e1")
        e2 = _make_entity("e2")
        n1 = f.create_node([e1])
        n2 = f.create_node([e2])
        rel = _make_usage_relation()
        edge = f.create_edge([rel], n1, n2)
        assert isinstance(edge, DividedGraphEdge)

    def test_create_edge_empty_raises(self):
        f = DividedCpmFactory()
        n1 = f.create_node([_make_entity()])
        with pytest.raises(ValueError):
            f.create_edge([], n1, n1)

    def test_clone_node_without_edges(self):
        f = DividedCpmFactory()
        node = f.create_node([_make_entity()])
        cloned = f.clone_node(node)
        assert isinstance(cloned, DividedGraphNode)
        assert cloned is not node

    def test_clone_node_with_edges(self):
        f = DividedCpmFactory()
        n1 = f.create_node([_make_entity("e1")])
        n2 = f.create_node([_make_entity("e2")])
        rel = _make_usage_relation()
        edge = f.create_edge([rel], n1, n2)
        n1.add_cause_edge(edge)
        cloned = f.clone_node(n1, include_edges=True)
        assert len(cloned.cause_edges) == 1

    def test_clone_edge(self):
        f = DividedCpmFactory()
        n1 = f.create_node([_make_entity("e1")])
        n2 = f.create_node([_make_entity("e2")])
        rel = _make_usage_relation()
        edge = f.create_edge([rel], n1, n2)
        cloned = f.clone_edge(edge)
        assert isinstance(cloned, DividedGraphEdge)
        assert cloned.cause is n1

    def test_clone_edge_with_mapping(self):
        f = DividedCpmFactory()
        n1 = f.create_node([_make_entity("e1")])
        n2 = f.create_node([_make_entity("e2")])
        n3 = f.create_node([_make_entity("e3")])
        rel = _make_usage_relation()
        edge = f.create_edge([rel], n1, n2)
        cloned = f.clone_edge(edge, {n1: n3})
        assert cloned.cause is n3

    def test_get_factory_type(self):
        assert DividedCpmFactory().get_factory_type() == "DIVIDED"


# ─── MergedCpmFactory (extended) ────────────────────────────────────────────

class TestMergedCpmFactoryExtended:
    def test_create_node(self):
        f = MergedCpmFactory()
        node = f.create_node([_make_entity()])
        assert isinstance(node, MergedGraphNode)

    def test_create_node_empty_raises(self):
        f = MergedCpmFactory()
        with pytest.raises(ValueError):
            f.create_node([])

    def test_create_edge(self):
        f = MergedCpmFactory()
        n1 = f.create_node([_make_entity("e1")])
        n2 = f.create_node([_make_entity("e2")])
        rel = _make_usage_relation()
        edge = f.create_edge([rel], n1, n2)
        assert isinstance(edge, MergedGraphEdge)

    def test_create_edge_empty_raises(self):
        f = MergedCpmFactory()
        n = f.create_node([_make_entity()])
        with pytest.raises(ValueError):
            f.create_edge([], n, n)

    def test_clone_node(self):
        f = MergedCpmFactory()
        node = f.create_node([_make_entity()])
        cloned = f.clone_node(node)
        assert isinstance(cloned, MergedGraphNode)

    def test_clone_node_with_edges(self):
        f = MergedCpmFactory()
        n1 = f.create_node([_make_entity("e1")])
        n2 = f.create_node([_make_entity("e2")])
        rel = _make_usage_relation()
        edge = f.create_edge([rel], n1, n2)
        n1.add_effect_edge(edge)
        cloned = f.clone_node(n1, include_edges=True)
        assert len(cloned.effect_edges) == 1

    def test_clone_edge(self):
        f = MergedCpmFactory()
        n1 = f.create_node([_make_entity("e1")])
        n2 = f.create_node([_make_entity("e2")])
        rel = _make_usage_relation()
        edge = f.create_edge([rel], n1, n2)
        cloned = f.clone_edge(edge)
        assert isinstance(cloned, MergedGraphEdge)

    def test_get_factory_type(self):
        assert MergedCpmFactory().get_factory_type() == "MERGED"


# ─── CpmFactoryManager (extended) ──────────────────────────────────────────

class TestCpmFactoryManagerExtended:
    def test_get_factory_default(self):
        m = CpmFactoryManager()
        f = m.get_factory()
        assert isinstance(f, DividedCpmFactory)

    def test_get_factory_merged(self):
        m = CpmFactoryManager()
        f = m.get_factory("MERGED")
        assert isinstance(f, MergedCpmFactory)

    def test_get_factory_unknown_raises(self):
        m = CpmFactoryManager()
        with pytest.raises(ValueError):
            m.get_factory("UNKNOWN")

    def test_create_node_from_elements(self):
        m = CpmFactoryManager()
        node = m.create_node_from_elements([_make_entity()])
        assert isinstance(node, DividedGraphNode)

    def test_create_edge_from_relations(self):
        m = CpmFactoryManager()
        n1 = m.create_node_from_elements([_make_entity("e1")])
        n2 = m.create_node_from_elements([_make_entity("e2")])
        rel = _make_usage_relation()
        edge = m.create_edge_from_relations([rel], n1, n2)
        assert isinstance(edge, DividedGraphEdge)

    def test_clone_graph(self):
        m = CpmFactoryManager()
        w = _make_wrapper_ext()
        cloned = m.clone_graph(w)
        assert isinstance(cloned, ProvGraphWrapper)
        assert len(cloned.get_nodes()) > 0

    def test_merge_graphs_empty(self):
        m = CpmFactoryManager()
        merged = m.merge_graphs([])
        assert len(merged.get_nodes()) == 0

    def test_merge_graphs_single(self):
        m = CpmFactoryManager()
        w = _make_wrapper_ext()
        merged = m.merge_graphs([w])
        assert len(merged.get_nodes()) > 0

    def test_merge_graphs_two(self):
        m = CpmFactoryManager()
        w1 = _make_wrapper_ext()
        w2 = _make_wrapper_ext()
        merged = m.merge_graphs([w1, w2])
        assert isinstance(merged, ProvGraphWrapper)

    def test_create_subgraph(self):
        m = CpmFactoryManager()
        w = _make_wrapper_ext()
        sub = m.create_subgraph(w, lambda node: "e1" in str(node.identifier))
        assert isinstance(sub, ProvGraphWrapper)

    def test_get_available_factory_types(self):
        m = CpmFactoryManager()
        types = m.get_available_factory_types()
        assert "DIVIDED" in types
        assert "MERGED" in types

    def test_register_factory(self):
        m = CpmFactoryManager()
        m.register_factory("CUSTOM", DividedCpmFactory())
        assert "CUSTOM" in m.get_available_factory_types()

    def test_set_default_factory_type(self):
        m = CpmFactoryManager()
        m.set_default_factory_type("MERGED")
        f = m.get_factory()
        assert isinstance(f, MergedCpmFactory)

    def test_set_default_unknown_raises(self):
        m = CpmFactoryManager()
        with pytest.raises(ValueError):
            m.set_default_factory_type("NOPE")


# ─── Module-level functions ─────────────────────────────────────────────────

class TestModuleFunctions:
    def test_get_factory_manager(self):
        m = get_factory_manager()
        assert isinstance(m, CpmFactoryManager)

    def test_create_node_func(self):
        node = create_node([_make_entity()])
        assert isinstance(node, GraphNode)

    def test_create_edge_func(self):
        n1 = create_node([_make_entity("e1")])
        n2 = create_node([_make_entity("e2")])
        rel = _make_usage_relation()
        edge = create_edge([rel], n1, n2)
        assert isinstance(edge, GraphEdge)

    def test_clone_graph_func(self):
        w = _make_wrapper_ext()
        cloned = clone_graph(w)
        assert isinstance(cloned, ProvGraphWrapper)

    def test_merge_graphs_func(self):
        w = _make_wrapper_ext()
        merged = merge_graphs([w])
        assert isinstance(merged, ProvGraphWrapper)
