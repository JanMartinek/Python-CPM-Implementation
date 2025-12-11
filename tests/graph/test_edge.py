"""
Tests for GraphEdge, DividedGraphEdge, and MergedGraphEdge classes
"""

import pytest
from prov.model import ProvDocument, ProvUsage, ProvGeneration, ProvDerivation
from prov.identifier import QualifiedName

from src.graph.node import GraphNode
from src.graph.edge import GraphEdge, DividedGraphEdge, MergedGraphEdge, EdgeFilter, EdgeBuilder


class TestGraphEdge:
    """Test basic GraphEdge functionality"""

    def test_edge_creation(self):
        """Test creating an edge with a relation"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = GraphEdge(usage, node1, node2)

        assert edge.prov_relation == usage
        assert edge.cause == node1
        assert edge.effect == node2
        assert edge.kind == "PROV_USAGE"

    def test_edge_kind_detection(self):
        """Test automatic edge kind detection"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        node3 = GraphNode(activity)

        usage = doc.usage(activity, entity1)
        generation = doc.generation(entity2, activity)
        derivation = doc.derivation(entity2, entity1)

        edge1 = GraphEdge(usage, node3, node1)
        edge2 = GraphEdge(generation, node3, node2)
        edge3 = GraphEdge(derivation, node1, node2)

        assert edge1.kind == "PROV_USAGE"
        assert edge2.kind == "PROV_GENERATION"
        assert edge3.kind == "PROV_DERIVATION"

    def test_edge_set_cause(self):
        """Test setting the cause node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        entity3 = doc.entity('ex:entity3')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        node3 = GraphNode(entity3)

        edge = GraphEdge(usage, node1, node2)
        edge.set_cause(node3)

        assert edge.cause == node3

    def test_edge_set_effect(self):
        """Test setting the effect node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        entity3 = doc.entity('ex:entity3')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        node3 = GraphNode(entity3)

        edge = GraphEdge(usage, node1, node2)
        edge.set_effect(node3)

        assert edge.effect == node3

    def test_edge_is_between(self):
        """Test checking if edge is between two nodes"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = GraphEdge(usage, node1, node2)

        assert edge.is_between(node1, node2) is True
        assert edge.is_between(node2, node1) is False

    def test_edge_connects_node(self):
        """Test checking if edge connects to a node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        entity3 = doc.entity('ex:entity3')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        node3 = GraphNode(entity3)

        edge = GraphEdge(usage, node1, node2)

        assert edge.connects_node(node1) is True
        assert edge.connects_node(node2) is True
        assert edge.connects_node(node3) is False

    def test_edge_get_other_node(self):
        """Test getting the other node in an edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = GraphEdge(usage, node1, node2)

        assert edge.get_other_node(node1) == node2
        assert edge.get_other_node(node2) == node1

    def test_edge_reverse(self):
        """Test reversing an edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = GraphEdge(usage, node1, node2)
        reversed_edge = edge.reverse()

        assert reversed_edge.cause == node2
        assert reversed_edge.effect == node1

    def test_edge_add_relation(self):
        """Test adding a relation to an edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = GraphEdge(usage1, node1, node2)
        result = edge.add_relation(usage2)

        assert result is True
        assert len(edge.relations) == 2

    def test_edge_remove_relation(self):
        """Test removing a relation from an edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = GraphEdge(usage1, node1, node2)
        edge.add_relation(usage2)

        result = edge.remove_relation(usage2)
        assert result is True
        assert len(edge.relations) == 1

    def test_edge_attributes(self):
        """Test getting edge attributes"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2, other_attributes={'ex:attr': 'value'})

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = GraphEdge(usage, node1, node2)

        attrs = edge.get_attributes()
        assert len(attrs) > 0

    def test_edge_clone(self):
        """Test cloning an edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = GraphEdge(usage, node1, node2)
        cloned_edge = edge.clone()

        assert cloned_edge is not edge
        assert cloned_edge.cause == edge.cause
        assert cloned_edge.effect == edge.effect

    def test_edge_equality(self):
        """Test edge equality"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge1 = GraphEdge(usage1, node1, node2)
        edge2 = GraphEdge(usage1, node1, node2)
        edge3 = GraphEdge(usage2, node1, node2)

        assert edge1 == edge2
        assert edge1 != edge3


class TestDividedGraphEdge:
    """Test DividedGraphEdge functionality"""

    def test_divided_edge_creation(self):
        """Test creating a divided edge with multiple relations"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = DividedGraphEdge([usage1, usage2], node1, node2)

        assert len(edge.relations) == 2
        assert usage1 in edge.relations
        assert usage2 in edge.relations

    def test_divided_edge_requires_relations(self):
        """Test that DividedGraphEdge requires at least one relation"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        with pytest.raises(ValueError, match="at least one relation"):
            DividedGraphEdge([], node1, node2)

    def test_divided_edge_add_relation(self):
        """Test adding relations to divided edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = DividedGraphEdge([usage1], node1, node2)
        result = edge.add_relation(usage2)

        assert result is True
        assert len(edge.relations) == 2

    def test_divided_edge_remove_relation(self):
        """Test removing relations from divided edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = DividedGraphEdge([usage1, usage2], node1, node2)
        result = edge.remove_relation(usage2)

        assert result is True
        assert len(edge.relations) == 1

    def test_divided_edge_cannot_remove_last_relation(self):
        """Test that last relation cannot be removed"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = DividedGraphEdge([usage], node1, node2)
        result = edge.remove_relation(usage)

        assert result is False
        assert len(edge.relations) == 1

    def test_divided_edge_clone(self):
        """Test cloning a divided edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = DividedGraphEdge([usage1, usage2], node1, node2)
        cloned_edge = edge.clone()

        assert cloned_edge is not edge
        assert len(cloned_edge.relations) == 2
        assert isinstance(cloned_edge, DividedGraphEdge)


class TestMergedGraphEdge:
    """Test MergedGraphEdge functionality"""

    def test_merged_edge_creation(self):
        """Test creating a merged edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = MergedGraphEdge(usage, node1, node2)

        assert len(edge.relations) == 1
        assert edge.prov_relation == usage

    def test_merged_edge_cannot_add_relation(self):
        """Test that relations cannot be added to merged edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = MergedGraphEdge(usage1, node1, node2)
        result = edge.add_relation(usage2)

        assert result is False
        assert len(edge.relations) == 1

    def test_merged_edge_cannot_remove_relation(self):
        """Test that relation cannot be removed from merged edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = MergedGraphEdge(usage, node1, node2)
        result = edge.remove_relation(usage)

        assert result is False


class TestEdgeFilter:
    """Test EdgeFilter utility class"""

    def test_filter_by_cause(self):
        """Test filtering edges by cause node"""
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
        usage3 = doc.usage(entity2, entity3)

        edge1 = GraphEdge(usage1, node1, node2)
        edge2 = GraphEdge(usage2, node1, node3)
        edge3 = GraphEdge(usage3, node2, node3)

        edges = [edge1, edge2, edge3]
        filtered = EdgeFilter.by_cause(edges, node1)

        assert len(filtered) == 2
        assert edge1 in filtered
        assert edge2 in filtered

    def test_filter_by_effect(self):
        """Test filtering edges by effect node"""
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
        usage3 = doc.usage(entity2, entity3)

        edge1 = GraphEdge(usage1, node1, node2)
        edge2 = GraphEdge(usage2, node1, node3)
        edge3 = GraphEdge(usage3, node2, node3)

        edges = [edge1, edge2, edge3]
        filtered = EdgeFilter.by_effect(edges, node3)

        assert len(filtered) == 2
        assert edge2 in filtered
        assert edge3 in filtered

    def test_filter_by_kind(self):
        """Test filtering edges by relation kind"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)
        node3 = GraphNode(activity)

        usage = doc.usage(activity, entity1)
        generation = doc.generation(entity2, activity)

        edge1 = GraphEdge(usage, node3, node1)
        edge2 = GraphEdge(generation, node3, node2)

        edges = [edge1, edge2]
        filtered = EdgeFilter.by_kind(edges, 'PROV_USAGE')

        assert len(filtered) == 1
        assert edge1 in filtered


class TestEdgeBuilder:
    """Test EdgeBuilder utility class"""

    def test_builder_creates_merged_edge(self):
        """Test building a merged edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = (EdgeBuilder()
                .with_relation(usage)
                .with_cause(node1)
                .with_effect(node2)
                .as_merged()
                .build())

        assert isinstance(edge, MergedGraphEdge)
        assert edge.cause == node1
        assert edge.effect == node2

    def test_builder_creates_divided_edge(self):
        """Test building a divided edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage1 = doc.usage(entity1, entity2, identifier='ex:usage1')
        usage2 = doc.usage(entity1, entity2, identifier='ex:usage2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        edge = (EdgeBuilder()
                .with_relations([usage1, usage2])
                .with_cause(node1)
                .with_effect(node2)
                .as_divided()
                .build())

        assert isinstance(edge, DividedGraphEdge)
        assert len(edge.relations) == 2

    def test_builder_requires_relation(self):
        """Test that builder requires a relation"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        node1 = GraphNode(entity1)
        node2 = GraphNode(entity2)

        with pytest.raises(ValueError, match="Relation is required"):
            (EdgeBuilder()
             .with_cause(node1)
             .with_effect(node2)
             .build())

    def test_builder_requires_cause(self):
        """Test that builder requires a cause node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node2 = GraphNode(entity2)

        with pytest.raises(ValueError, match="Cause node is required"):
            (EdgeBuilder()
             .with_relation(usage)
             .with_effect(node2)
             .build())

    def test_builder_requires_effect(self):
        """Test that builder requires an effect node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        usage = doc.usage(entity1, entity2)

        node1 = GraphNode(entity1)

        with pytest.raises(ValueError, match="Effect node is required"):
            (EdgeBuilder()
             .with_relation(usage)
             .with_cause(node1)
             .build())
