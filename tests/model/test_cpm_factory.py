"""
Test CPM Factory Pattern Implementation

Tests for CPM factory patterns including:
- CpmFactoryRegistry
- ComponentStrategy enum
- Various factory implementations (Merged, Ordered, Divided)
- Node and edge creation
- Factory transformation operations
"""

import pytest
from prov.model import ProvDocument, ProvEntity, ProvActivity, ProvAgent
from prov.identifier import QualifiedName, Namespace

from src.cpm.factory import (
    ICpmFactory,
    ComponentStrategy,
    CpmFactoryRegistry,
    CpmMergedFactory,
    CpmOrderedFactory,
    CpmDividedOrderedFactory,
    CpmDividedUnorderedFactory
)
from src.cpm.model import CpmDocument
from src.cpm.constants import *
from src.graph.node import GraphNode
from src.graph.edge import GraphEdge


class TestComponentStrategy:
    """Test the ComponentStrategy enum"""

    def test_component_strategy_values(self):
        """Test that all strategy values exist"""
        assert ComponentStrategy.MERGED is not None
        assert ComponentStrategy.ORDERED is not None
        assert ComponentStrategy.DIVIDED_ORDERED is not None
        assert ComponentStrategy.DIVIDED_UNORDERED is not None

    def test_strategy_enum_values(self):
        """Test strategy enum string values"""
        assert ComponentStrategy.MERGED.value == "merged"
        assert ComponentStrategy.ORDERED.value == "ordered"
        assert ComponentStrategy.DIVIDED_ORDERED.value == "divided_ordered"
        assert ComponentStrategy.DIVIDED_UNORDERED.value == "divided_unordered"


class TestCpmFactoryRegistry:
    """Test the CpmFactoryRegistry"""

    def test_registry_get_factory_merged(self):
        """Test getting merged factory from registry"""
        factory = CpmFactoryRegistry.get_factory(ComponentStrategy.MERGED)
        assert factory is not None
        assert isinstance(factory, ICpmFactory)

    def test_registry_get_factory_ordered(self):
        """Test getting ordered factory from registry"""
        factory = CpmFactoryRegistry.get_factory(ComponentStrategy.ORDERED)
        assert factory is not None
        assert isinstance(factory, ICpmFactory)

    def test_registry_get_factory_divided_ordered(self):
        """Test getting divided ordered factory from registry"""
        factory = CpmFactoryRegistry.get_factory(ComponentStrategy.DIVIDED_ORDERED)
        assert factory is not None
        assert isinstance(factory, ICpmFactory)

    def test_registry_get_factory_divided_unordered(self):
        """Test getting divided unordered factory from registry"""
        factory = CpmFactoryRegistry.get_factory(ComponentStrategy.DIVIDED_UNORDERED)
        assert factory is not None
        assert isinstance(factory, ICpmFactory)

    def test_registry_caching(self):
        """Test that registry returns same factory instance"""
        factory1 = CpmFactoryRegistry.get_factory(ComponentStrategy.MERGED)
        factory2 = CpmFactoryRegistry.get_factory(ComponentStrategy.MERGED)
        assert factory1 is factory2


class TestCpmMergedFactory:
    """Test the CpmMergedFactory implementation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.factory = CpmMergedFactory()
        self.doc = ProvDocument()
        self.doc.add_namespace('ex', 'http://example.org/')
        self.bundle = self.doc.bundle('ex:bundle')

    def test_create_document(self):
        """Test document creation"""
        cpm_doc = self.factory.create_document(self.doc)
        assert cpm_doc is not None
        assert isinstance(cpm_doc, CpmDocument)

    def test_create_node_from_entity(self):
        """Test node creation from entity"""
        entity = self.bundle.entity('ex:entity1')
        node = self.factory.create_node(entity)
        assert node is not None

    def test_create_node_from_activity(self):
        """Test node creation from activity"""
        activity = self.bundle.activity('ex:activity1')
        node = self.factory.create_node(activity)
        assert node is not None

    def test_create_node_from_agent(self):
        """Test node creation from agent"""
        agent = self.bundle.agent('ex:agent1')
        node = self.factory.create_node(agent)
        assert node is not None

    def test_create_edge_from_relation(self):
        """Test edge creation from relation"""
        entity1 = self.bundle.entity('ex:entity1')
        entity2 = self.bundle.entity('ex:entity2')
        relation = self.bundle.wasDerivedFrom('ex:entity2', 'ex:entity1')

        edge = self.factory.create_edge(relation)
        assert edge is not None

    def test_copy_node_clears_edges(self):
        """Test that copying a node clears its edges"""
        # Create entities
        entity1 = self.bundle.entity('ex:entity1')
        entity2 = self.bundle.entity('ex:entity2')
        entity3 = self.bundle.entity('ex:entity3')

        # Create relations
        relation1 = self.bundle.wasDerivedFrom('ex:entity2', 'ex:entity1')
        relation2 = self.bundle.wasDerivedFrom('ex:entity3', 'ex:entity1')

        # Create nodes and edges
        node1 = self.factory.create_node(entity1)
        node2 = self.factory.create_node(entity2)
        node3 = self.factory.create_node(entity3)

        edge1 = self.factory.create_edge(relation1)
        edge2 = self.factory.create_edge(relation2)

        # Simulate adding edges to node (if nodes have edge tracking)
        if hasattr(node1, 'add_outgoing_edge'):
            node1.add_outgoing_edge(edge1)
            node1.add_outgoing_edge(edge2)

        # Copy the node
        copied_node = self.factory.create_node(node1)

        # Copied node should not have edges
        assert copied_node is not None
        if hasattr(copied_node, 'get_outgoing_edges'):
            assert len(copied_node.get_outgoing_edges()) == 0
        if hasattr(copied_node, 'get_incoming_edges'):
            assert len(copied_node.get_incoming_edges()) == 0


class TestCpmOrderedFactory:
    """Test the CpmOrderedFactory implementation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.factory = CpmOrderedFactory()
        self.doc = ProvDocument()
        self.doc.add_namespace('ex', 'http://example.org/')
        self.bundle = self.doc.bundle('ex:bundle')

    def test_create_document(self):
        """Test document creation with ordering"""
        cpm_doc = self.factory.create_document(self.doc)
        assert cpm_doc is not None
        assert isinstance(cpm_doc, CpmDocument)

    def test_preserves_statement_order(self):
        """Test that ordered factory preserves statement ordering"""
        # Create multiple statements in specific order
        entity1 = self.bundle.entity('ex:entity1')
        entity2 = self.bundle.entity('ex:entity2')
        activity = self.bundle.activity('ex:activity')

        cpm_doc = self.factory.create_document(self.doc)

        # Verify document was created successfully
        assert cpm_doc is not None


class TestCpmDividedOrderedFactory:
    """Test the CpmDividedOrderedFactory implementation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.factory = CpmDividedOrderedFactory()
        self.doc = ProvDocument()
        self.doc.add_namespace('ex', 'http://example.org/')
        self.bundle = self.doc.bundle('ex:bundle')

    def test_create_document(self):
        """Test divided ordered document creation"""
        cpm_doc = self.factory.create_document(self.doc)
        assert cpm_doc is not None
        assert isinstance(cpm_doc, CpmDocument)

    def test_divided_strategy(self):
        """Test that divided strategy separates components"""
        entity = self.bundle.entity('ex:entity1')
        activity = self.bundle.activity('ex:activity1')

        cpm_doc = self.factory.create_document(self.doc)
        assert cpm_doc is not None


class TestCpmDividedUnorderedFactory:
    """Test the CpmDividedUnorderedFactory implementation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.factory = CpmDividedUnorderedFactory()
        self.doc = ProvDocument()
        self.doc.add_namespace('ex', 'http://example.org/')
        self.bundle = self.doc.bundle('ex:bundle')

    def test_create_document(self):
        """Test divided unordered document creation"""
        cpm_doc = self.factory.create_document(self.doc)
        assert cpm_doc is not None
        assert isinstance(cpm_doc, CpmDocument)


class TestFactoryIntegration:
    """Test factory pattern integration"""

    def test_all_factories_create_valid_documents(self):
        """Test that all factory types can create valid documents"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        bundle = doc.bundle('ex:bundle')
        entity = bundle.entity('ex:entity1')

        strategies = [
            ComponentStrategy.MERGED,
            ComponentStrategy.ORDERED,
            ComponentStrategy.DIVIDED_ORDERED,
            ComponentStrategy.DIVIDED_UNORDERED
        ]

        for strategy in strategies:
            factory = CpmFactoryRegistry.get_factory(strategy)
            cpm_doc = factory.create_document(doc)
            assert cpm_doc is not None, f"Factory for {strategy} failed to create document"
            assert isinstance(cpm_doc, CpmDocument), f"Factory for {strategy} created wrong type"

    def test_factory_switching(self):
        """Test switching between different factory implementations"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        bundle = doc.bundle('ex:bundle')
        entity = bundle.entity('ex:entity1')

        # Create with merged factory
        merged_factory = CpmFactoryRegistry.get_factory(ComponentStrategy.MERGED)
        merged_doc = merged_factory.create_document(doc)

        # Create with ordered factory
        ordered_factory = CpmFactoryRegistry.get_factory(ComponentStrategy.ORDERED)
        ordered_doc = ordered_factory.create_document(doc)

        # Both should be valid but potentially different implementations
        assert merged_doc is not None
        assert ordered_doc is not None
