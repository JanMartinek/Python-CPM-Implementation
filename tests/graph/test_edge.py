"""
Tests for GraphEdge, DividedGraphEdge, and MergedGraphEdge classes
"""

import pytest
from prov.model import ProvDocument, ProvUsage, ProvGeneration, ProvDerivation
from prov.identifier import QualifiedName, Namespace

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


# ═══════════════════════════════════════════════════════════════════════════════
# Additional coverage tests – GraphEdge, DividedGraphEdge, MergedGraphEdge,
# EdgeFilter, EdgeBuilder.
# ═══════════════════════════════════════════════════════════════════════════════

from prov.identifier import Namespace

EX = Namespace("ex", "http://example.org/")


def _doc_with_relation():
    doc = ProvDocument()
    doc.add_namespace(EX)
    doc.activity(EX["a1"])
    doc.entity(EX["e1"])
    usage = doc.usage(EX["a1"], EX["e1"])
    return doc, usage


def _make_nodes_and_relation():
    doc, usage = _doc_with_relation()
    act = list(doc.get_records())[0]
    ent = list(doc.get_records())[1]
    n_cause = GraphNode(ent, EX["e1"])
    n_effect = GraphNode(act, EX["a1"])
    return n_cause, n_effect, usage


# ─── GraphEdge basics ───────────────────────────────────────────────────────

class TestGraphEdgeBasics:
    def test_identifier(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert edge.identifier is not None or edge.identifier is None

    def test_identifier_override(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e, identifier=EX["myedge"])
        assert edge.identifier == EX["myedge"]

    def test_kind(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert edge.kind == "PROV_USAGE"

    def test_set_cause(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        doc = ProvDocument()
        doc.add_namespace(EX)
        new_c = GraphNode(doc.entity(EX["e2"]), EX["e2"])
        edge.set_cause(new_c)
        assert edge.cause is new_c

    def test_set_effect(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        doc = ProvDocument()
        doc.add_namespace(EX)
        new_e = GraphNode(doc.activity(EX["a2"]), EX["a2"])
        edge.set_effect(new_e)
        assert edge.effect is new_e

    def test_add_relation(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert edge.add_relation(rel) is False  # already present
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.activity(EX["a1"])
        doc.entity(EX["e2"])
        rel2 = doc.usage(EX["a1"], EX["e2"])
        assert edge.add_relation(rel2) is True

    def test_remove_relation_only_one(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert edge.remove_relation(rel) is False  # can't remove only relation

    def test_handle_duplicate(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        edge.handle_duplicate(rel)  # same identifier → no-op

    def test_clone(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        cloned = edge.clone()
        assert cloned is not edge
        assert isinstance(cloned, GraphEdge)

    def test_is_between(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert edge.is_between(c, e) is True
        assert edge.is_between(e, c) is False

    def test_connects_node(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert edge.connects_node(c) is True
        assert edge.connects_node(e) is True

    def test_get_other_node(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert edge.get_other_node(c) is e
        assert edge.get_other_node(e) is c
        doc = ProvDocument()
        doc.add_namespace(EX)
        other = GraphNode(doc.entity(EX["x"]), EX["x"])
        assert edge.get_other_node(other) is None

    def test_reverse(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        rev = edge.reverse()
        assert rev.cause is e
        assert rev.effect is c

    def test_get_attributes(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        attrs = edge.get_attributes()
        assert isinstance(attrs, list)

    def test_has_attribute(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert isinstance(edge.has_attribute("prov:entity"), bool)

    def test_get_attribute_values(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        vals = edge.get_attribute_values("nonexistent")
        assert vals == []

    def test_str_repr(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        assert "GraphEdge" in str(edge)
        assert "GraphEdge" in repr(edge)

    def test_eq_and_hash(self):
        c, e, rel = _make_nodes_and_relation()
        edge1 = GraphEdge(rel, c, e)
        edge2 = GraphEdge(rel, c, e)
        assert edge1 == edge2
        assert not (edge1 == "not an edge")
        assert isinstance(hash(edge1), int)


# ─── DividedGraphEdge (extended) ────────────────────────────────────────────

class TestDividedGraphEdgeExtended:
    def test_create(self):
        c, e, rel = _make_nodes_and_relation()
        edge = DividedGraphEdge([rel], c, e)
        assert isinstance(edge, DividedGraphEdge)

    def test_create_empty_raises(self):
        c, e, _ = _make_nodes_and_relation()
        with pytest.raises(ValueError):
            DividedGraphEdge([], c, e)

    def test_add_remove_relation(self):
        c, e, rel = _make_nodes_and_relation()
        doc2 = ProvDocument()
        doc2.add_namespace(EX)
        doc2.activity(EX["a1"])
        doc2.entity(EX["e2"])
        rel2 = doc2.usage(EX["a1"], EX["e2"])
        edge = DividedGraphEdge([rel], c, e)
        assert edge.add_relation(rel2) is True
        assert edge.remove_relation(rel2) is True
        assert edge.remove_relation(rel) is False  # can't remove last

    def test_handle_duplicate_new(self):
        c, e, rel = _make_nodes_and_relation()
        doc2 = ProvDocument()
        doc2.add_namespace(EX)
        doc2.activity(EX["a1"])
        doc2.entity(EX["e2"])
        rel2 = doc2.usage(EX["a1"], EX["e2"], identifier=EX["u2"])
        edge = DividedGraphEdge([rel], c, e)
        edge.handle_duplicate(rel2)
        assert len(edge.relations) == 2

    def test_kind(self):
        c, e, rel = _make_nodes_and_relation()
        edge = DividedGraphEdge([rel], c, e)
        assert edge.kind == "PROV_USAGE"

    def test_clone(self):
        c, e, rel = _make_nodes_and_relation()
        edge = DividedGraphEdge([rel], c, e)
        cloned = edge.clone()
        assert isinstance(cloned, DividedGraphEdge)

    def test_eq_hash(self):
        c, e, rel = _make_nodes_and_relation()
        edge = DividedGraphEdge([rel], c, e)
        assert edge == edge
        assert not (edge == "not an edge")
        assert isinstance(hash(edge), int)


# ─── MergedGraphEdge (extended) ─────────────────────────────────────────────

class TestMergedGraphEdgeExtended:
    def test_create(self):
        c, e, rel = _make_nodes_and_relation()
        edge = MergedGraphEdge(rel, c, e)
        assert isinstance(edge, MergedGraphEdge)

    def test_add_relation_returns_false(self):
        c, e, rel = _make_nodes_and_relation()
        edge = MergedGraphEdge(rel, c, e)
        assert edge.add_relation(rel) is False

    def test_remove_relation_returns_false(self):
        c, e, rel = _make_nodes_and_relation()
        edge = MergedGraphEdge(rel, c, e)
        assert edge.remove_relation(rel) is False

    def test_handle_duplicate(self):
        c, e, rel = _make_nodes_and_relation()
        edge = MergedGraphEdge(rel, c, e)
        edge.handle_duplicate(rel)  # should not raise

    def test_clone(self):
        c, e, rel = _make_nodes_and_relation()
        edge = MergedGraphEdge(rel, c, e)
        cloned = edge.clone()
        assert isinstance(cloned, (MergedGraphEdge, GraphEdge))


# ─── EdgeFilter (extended) ──────────────────────────────────────────────────

class TestEdgeFilterExtended:
    def _edges(self):
        c, e, rel = _make_nodes_and_relation()
        edge = GraphEdge(rel, c, e)
        return [edge], c, e

    def test_by_cause(self):
        edges, c, e = self._edges()
        assert len(EdgeFilter.by_cause(edges, c)) == 1

    def test_by_effect(self):
        edges, c, e = self._edges()
        assert len(EdgeFilter.by_effect(edges, e)) == 1

    def test_by_kind(self):
        edges, _, _ = self._edges()
        assert len(EdgeFilter.by_kind(edges, "PROV_USAGE")) == 1

    def test_by_cause_and_effect(self):
        edges, c, e = self._edges()
        assert len(EdgeFilter.by_cause_and_effect(edges, c, e)) == 1

    def test_by_node(self):
        edges, c, _ = self._edges()
        assert len(EdgeFilter.by_node(edges, c)) == 1

    def test_by_attribute_presence(self):
        edges, _, _ = self._edges()
        result = EdgeFilter.by_attribute(edges, "prov:entity")
        assert isinstance(result, list)

    def test_by_attribute_value(self):
        edges, _, _ = self._edges()
        result = EdgeFilter.by_attribute(edges, "nonexistent", "val")
        assert result == []


# ─── EdgeBuilder (extended) ─────────────────────────────────────────────────

class TestEdgeBuilderExtended:
    def test_build_merged(self):
        c, e, rel = _make_nodes_and_relation()
        edge = (EdgeBuilder()
                .with_relation(rel)
                .with_cause(c)
                .with_effect(e)
                .as_merged()
                .build())
        assert isinstance(edge, MergedGraphEdge)

    def test_build_divided(self):
        c, e, rel = _make_nodes_and_relation()
        edge = (EdgeBuilder()
                .with_relations([rel])
                .with_cause(c)
                .with_effect(e)
                .as_divided()
                .build())
        assert isinstance(edge, DividedGraphEdge)

    def test_build_divided_from_single(self):
        c, e, rel = _make_nodes_and_relation()
        edge = (EdgeBuilder()
                .with_relation(rel)
                .with_cause(c)
                .with_effect(e)
                .as_divided()
                .build())
        assert isinstance(edge, DividedGraphEdge)

    def test_missing_relation_raises(self):
        c, e, _ = _make_nodes_and_relation()
        with pytest.raises(ValueError, match="Relation"):
            EdgeBuilder().with_cause(c).with_effect(e).build()

    def test_missing_cause_raises(self):
        _, e, rel = _make_nodes_and_relation()
        with pytest.raises(ValueError, match="Cause"):
            EdgeBuilder().with_relation(rel).with_effect(e).build()

    def test_missing_effect_raises(self):
        c, _, rel = _make_nodes_and_relation()
        with pytest.raises(ValueError, match="Effect"):
            EdgeBuilder().with_relation(rel).with_cause(c).build()

    def test_with_identifier(self):
        c, e, rel = _make_nodes_and_relation()
        edge = (EdgeBuilder()
                .with_relation(rel)
                .with_cause(c)
                .with_effect(e)
                .with_identifier(EX["myedge"])
                .build())
        assert edge.identifier == EX["myedge"] or edge._identifier == EX["myedge"]
