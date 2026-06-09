"""
Tests for GraphNode, DividedGraphNode, and MergedGraphNode classes
"""

import pytest
from prov.model import ProvDocument, ProvEntity, ProvActivity, ProvAgent
from prov.identifier import QualifiedName
from prov.constants import PROV_TYPE

from src.graph.node import GraphNode, DividedGraphNode, MergedGraphNode
from src.graph.edge import GraphEdge


class TestGraphNode:
    """Test basic GraphNode functionality"""

    def test_node_creation_with_entity(self):
        """Test creating a node with a ProvEntity"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node = GraphNode(entity)

        assert node.prov_entity == entity
        assert node.identifier == entity.identifier
        assert node.kind == "PROV_ENTITY"
        assert len(node.all_edges) == 0

    def test_node_creation_with_activity(self):
        """Test creating a node with a ProvActivity"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        activity = doc.activity('ex:activity1')

        node = GraphNode(activity)

        assert node.kind == "PROV_ACTIVITY"
        assert node.identifier == activity.identifier

    def test_node_creation_with_agent(self):
        """Test creating a node with a ProvAgent"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        agent = doc.agent('ex:agent1')

        node = GraphNode(agent)

        assert node.kind == "PROV_AGENT"
        assert node.identifier == agent.identifier

    def test_node_edge_management(self):
        """Test adding and removing edges from a node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        edge = GraphEdge(usage, node1, node2)

        node1.add_cause_edge(edge)
        node2.add_effect_edge(edge)

        assert len(node1.cause_edges) == 1
        assert len(node2.effect_edges) == 1
        assert edge in node1.all_edges
        assert edge in node2.all_edges

    def test_node_remove_edges(self):
        """Test removing edges from a node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        edge = GraphEdge(usage, node1, node2)

        node1.add_cause_edge(edge)
        assert node1.remove_cause_edge(edge) is True
        assert len(node1.cause_edges) == 0

        node2.add_effect_edge(edge)
        assert node2.remove_effect_edge(edge) is True
        assert len(node2.effect_edges) == 0

    def test_node_degree_calculations(self):
        """Test node degree calculations"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        entity3 = doc.entity('ex:entity3')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        node3 = GraphNode(entity3)

        usage1 = doc.usage(entity1, entity2)
        usage2 = doc.usage(entity1, entity3)

        edge1 = GraphEdge(usage1, node1, node2)
        edge2 = GraphEdge(usage2, node1, node3)

        node1.add_cause_edge(edge1)
        node1.add_cause_edge(edge2)
        node2.add_effect_edge(edge1)
        node3.add_effect_edge(edge2)

        assert node1.degree == 2
        assert node1.out_degree == 2
        assert node1.in_degree == 0
        assert node2.degree == 1
        assert node2.in_degree == 1
        assert node2.out_degree == 0

    def test_node_is_isolated(self):
        """Test checking if node is isolated"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node = GraphNode(entity)

        assert node.is_isolated() is True

        # Add an edge
        entity2 = doc.entity('ex:entity2')
        node2 = GraphNode(entity2)
        usage = doc.usage(entity, entity2)
        edge = GraphEdge(usage, node, node2)
        node.add_cause_edge(edge)

        assert node.is_isolated() is False

    def test_node_get_prov_attribute(self):
        """Test getting PROV attributes from node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1', {'ex:attr1': 'value1', 'ex:attr2': 'value2'})

        node = GraphNode(entity)

        attr1_values = node.get_prov_attribute('ex:attr1')
        assert 'value1' in attr1_values

    def test_node_has_prov_type(self):
        """Test checking PROV type"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1', {PROV_TYPE: 'ex:CustomType'})

        node = GraphNode(entity)

        assert node.has_prov_type('ex:CustomType') is True
        assert node.has_prov_type('ex:OtherType') is False

    def test_node_clone(self):
        """Test cloning a node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node = GraphNode(entity)
        cloned_node = node.clone()

        assert cloned_node is not node
        assert cloned_node.identifier == node.identifier
        assert cloned_node.kind == node.kind

    def test_handle_duplicate_merges_attributes(self):
        """Test duplicate node handling merges previously missing PROV attributes."""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1', {'ex:attr1': 'value1'})

        duplicate_doc = ProvDocument()
        duplicate_doc.add_namespace('ex', 'http://example.org/')
        duplicate = duplicate_doc.entity('ex:entity1', {'ex:attr2': 'value2'})

        node = GraphNode(entity)
        node.handle_duplicate(duplicate)

        assert 'value2' in node.get_prov_attribute('ex:attr2')

    def test_node_get_edges_by_relation_type(self):
        """Test getting edges by relation type"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        entity3 = doc.entity('ex:entity3')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        node3 = GraphNode(entity3)

        usage = doc.usage(entity1, entity2)
        generation = doc.generation(entity3, entity1)

        edge1 = GraphEdge(usage, node1, node2)
        edge2 = GraphEdge(generation, node1, node3)

        node1.add_cause_edge(edge1)
        node1.add_cause_edge(edge2)

        usage_edges = node1.get_edges_by_relation_type('PROV_USAGE')
        assert len(usage_edges) == 1
        assert edge1 in usage_edges

    def test_node_get_connected_nodes(self):
        """Test getting connected nodes"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        entity3 = doc.entity('ex:entity3')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        node3 = GraphNode(entity3)

        usage = doc.usage(entity1, entity2)
        generation = doc.generation(entity3, entity1)

        edge1 = GraphEdge(usage, node1, node2)
        edge2 = GraphEdge(generation, node1, node3)

        node1.add_cause_edge(edge1)
        node1.add_cause_edge(edge2)

        connected = node1.get_connected_nodes()
        assert len(connected) == 2
        assert node2 in connected
        assert node3 in connected

    def test_node_equality(self):
        """Test node equality"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity1)
        node3 = GraphNode(entity2)

        assert node1 == node2
        assert node1 != node3

    def test_node_hash(self):
        """Test node hashing"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node1 = GraphNode(entity)
        node2 = GraphNode(entity)

        # Nodes should be hashable and usable in sets
        node_set = {node1, node2}
        # Both nodes have same identifier and same prov_entity, so they're equal and hash to same value
        assert len(node_set) == 1  # Same entity results in equal nodes


class TestDividedGraphNode:
    """Test DividedGraphNode functionality"""

    def test_divided_node_creation(self):
        """Test creating a divided node with multiple elements"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        node = DividedGraphNode([entity1, entity2])

        assert len(node.elements) == 2
        assert entity1 in node.elements
        assert entity2 in node.elements

    def test_divided_node_requires_elements(self):
        """Test that DividedGraphNode requires at least one element"""
        with pytest.raises(ValueError, match="at least one element"):
            DividedGraphNode([])

    def test_divided_node_add_element(self):
        """Test adding elements to divided node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        node = DividedGraphNode([entity1])
        node.add_element(entity2)

        assert len(node.elements) == 2
        assert entity2 in node.elements

    def test_divided_node_remove_element(self):
        """Test removing elements from divided node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        node = DividedGraphNode([entity1, entity2])

        result = node.remove_element(entity2)
        assert result is True
        assert len(node.elements) == 1
        assert entity2 not in node.elements

    def test_divided_node_cannot_remove_last_element(self):
        """Test that last element cannot be removed"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node = DividedGraphNode([entity])

        result = node.remove_element(entity)
        assert result is False
        assert len(node.elements) == 1

    def test_divided_node_clone(self):
        """Test cloning a divided node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        node = DividedGraphNode([entity1, entity2])
        cloned_node = node.clone()

        assert cloned_node is not node
        assert len(cloned_node.elements) == 2
        assert isinstance(cloned_node, DividedGraphNode)


class TestMergedGraphNode:
    """Test MergedGraphNode functionality"""

    def test_merged_node_creation(self):
        """Test creating a merged node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node = MergedGraphNode(entity)

        assert node.prov_entity == entity
        assert len(node.elements) == 1

    def test_merged_node_cannot_remove_element(self):
        """Test that element cannot be removed from merged node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node = MergedGraphNode(entity)

        result = node.remove_element(entity)
        assert result is False

    def test_merged_node_clone(self):
        """Test cloning a merged node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        node = MergedGraphNode(entity)
        cloned_node = node.clone()

        assert cloned_node is not node
        assert isinstance(cloned_node, MergedGraphNode)
        assert cloned_node.identifier == node.identifier
