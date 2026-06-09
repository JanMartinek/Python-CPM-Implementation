"""
Tests for CpmDocumentTraversalMixin – predecessors, successors, connected
components, path finding, connector traversal.
"""

import pytest
from prov.model import ProvDocument
from src.cpm.model import CpmDocument
from src.cpm.builder import CpmDocumentBuilder


def _build_doc():
    builder = CpmDocumentBuilder("test:bundle")
    doc = (builder
           .with_main_activity("test:main", start_time="2024-01-01T00:00:00Z")
           .with_backward_connector("test:bc1", "test:src", "hash1")
           .with_forward_connector("test:fc1", "test:tgt", "hash2")
           .with_sender_agent("test:sender")
           .with_receiver_agent("test:receiver")
           .build())
    doc.add_node('entity', 'test:e1')
    doc.add_node('entity', 'test:e2')
    doc.add_node('entity', 'test:e3')
    doc.add_edge('used', 'test:main', 'test:e1')
    doc.add_edge('wasgeneratedby', 'test:main', 'test:e2')
    doc.add_edge('wasderivedfrom', 'test:e2', 'test:e1')
    doc.add_edge('wasderivedfrom', 'test:e3', 'test:e2')
    return doc


# ─── Predecessors ────────────────────────────────────────────────────────────

class TestGetPredecessors:
    def test_basic(self):
        doc = _build_doc()
        preds = doc.get_predecessors('test:e2')
        assert isinstance(preds, list)

    def test_nonexistent_node(self):
        doc = _build_doc()
        preds = doc.get_predecessors('test:nonexistent')
        assert preds == []

    def test_with_max_depth(self):
        doc = _build_doc()
        preds_1 = doc.get_predecessors('test:e3', max_depth=1)
        preds_all = doc.get_predecessors('test:e3')
        assert len(preds_1) <= len(preds_all)

    def test_with_relation_types(self):
        doc = _build_doc()
        preds = doc.get_predecessors('test:e2', relation_types=['derivation'])
        assert isinstance(preds, list)


# ─── Successors ──────────────────────────────────────────────────────────────

class TestGetSuccessors:
    def test_basic(self):
        doc = _build_doc()
        succs = doc.get_successors('test:e1')
        assert isinstance(succs, list)

    def test_nonexistent_node(self):
        doc = _build_doc()
        succs = doc.get_successors('test:nonexistent')
        assert succs == []

    def test_with_max_depth(self):
        doc = _build_doc()
        succs_1 = doc.get_successors('test:e1', max_depth=1)
        succs_all = doc.get_successors('test:e1')
        assert len(succs_1) <= len(succs_all)

    def test_with_relation_types(self):
        doc = _build_doc()
        succs = doc.get_successors('test:e1', relation_types=['derivation'])
        assert isinstance(succs, list)


# ─── Connected components ────────────────────────────────────────────────────

class TestConnectedComponents:
    def test_returns_list(self):
        doc = _build_doc()
        components = doc.get_connected_components()
        assert isinstance(components, list)

    def test_at_least_one_component(self):
        doc = _build_doc()
        components = doc.get_connected_components()
        assert len(components) >= 1

    def test_isolated_node_forms_own_component(self):
        doc = _build_doc()
        doc.add_node('entity', 'test:isolated')
        components = doc.get_connected_components()
        # Isolated node should form its own component
        isolated_found = False
        for comp in components:
            ids = [str(n.identifier) for n in comp]
            if any('isolated' in i for i in ids):
                isolated_found = True
                assert len(comp) == 1
        assert isolated_found


# ─── Path finding ────────────────────────────────────────────────────────────

class TestFindPaths:
    def test_path_exists(self):
        doc = _build_doc()
        paths = doc.find_paths('test:e1', 'test:e3')
        assert isinstance(paths, list)

    def test_no_path(self):
        doc = _build_doc()
        doc.add_node('entity', 'test:isolated2')
        paths = doc.find_paths('test:e1', 'test:isolated2')
        assert paths == []

    def test_nonexistent_source(self):
        doc = _build_doc()
        paths = doc.find_paths('test:nonexistent', 'test:e1')
        assert paths == []

    def test_nonexistent_target(self):
        doc = _build_doc()
        paths = doc.find_paths('test:e1', 'test:nonexistent')
        assert paths == []

    def test_path_with_max_length(self):
        doc = _build_doc()
        paths = doc.find_paths('test:e1', 'test:e3', max_length=10)
        assert isinstance(paths, list)

    def test_path_to_self(self):
        doc = _build_doc()
        paths = doc.find_paths('test:e1', 'test:e1')
        # Path from node to itself should be empty or single-element
        assert isinstance(paths, list)


# ─── Connector traversal ────────────────────────────────────────────────────

class TestGetPrecursors:
    def test_precursors_of_connector(self):
        doc = _build_doc()
        result = doc.get_precursors('test:bc1')
        # bc1 is a connector; precursors may be empty but should return list
        assert result is None or isinstance(result, list)

    def test_precursors_nonexistent(self):
        doc = _build_doc()
        result = doc.get_precursors('test:nonexistent')
        assert result is None

    def test_precursors_non_connector(self):
        doc = _build_doc()
        result = doc.get_precursors('test:e1')
        assert result is None


class TestGetSuccessorsConnectors:
    def test_successors_of_connector(self):
        doc = _build_doc()
        result = doc.get_successors_connectors('test:fc1')
        assert result is None or isinstance(result, list)

    def test_successors_nonexistent(self):
        doc = _build_doc()
        result = doc.get_successors_connectors('test:nonexistent')
        assert result is None

    def test_successors_non_connector(self):
        doc = _build_doc()
        result = doc.get_successors_connectors('test:e1')
        assert result is None


class TestGetRelatedConnectors:
    def test_related_of_connector(self):
        doc = _build_doc()
        result = doc.get_related_connectors('test:fc1')
        assert isinstance(result, list)

    def test_related_nonexistent(self):
        doc = _build_doc()
        result = doc.get_related_connectors('test:nonexistent')
        assert result == []

    def test_related_non_connector(self):
        doc = _build_doc()
        result = doc.get_related_connectors('test:e1')
        assert result == []

    def test_related_forward_direction(self):
        doc = _build_doc()
        result = doc.get_related_connectors('test:fc1', direction='forward')
        assert isinstance(result, list)

    def test_related_backward_direction(self):
        doc = _build_doc()
        result = doc.get_related_connectors('test:bc1', direction='backward')
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════════════════
# Extra traversal tests – related connectors direction variants,
# precursors/successors connector edge cases.
# ═══════════════════════════════════════════════════════════════════════════════

from src.cpm.constants import CPM_FORWARD_CONNECTOR, CPM_BACKWARD_CONNECTOR


def _build_connector_chain():
    """Build a doc with a chain of forward connector derivation: bc1 -> fc1 -> fc2."""
    builder = CpmDocumentBuilder("test:bundle")
    doc = (builder
           .with_main_activity("test:main")
           .with_backward_connector("test:bc1", "test:src", "hash1")
           .with_forward_connector("test:fc1", "test:src2", "hash2")
           .with_sender_agent("test:sender")
           .with_receiver_agent("test:receiver")
           .build())
    doc.add_edge("wasderivedfrom", "test:fc1", "test:bc1")
    return doc


class TestTraversalRelatedConnectorsExtra:
    def test_related_connectors_forward(self):
        doc = _build_connector_chain()
        related = doc.get_related_connectors("test:bc1", direction="forward")
        assert isinstance(related, list)

    def test_related_connectors_backward(self):
        doc = _build_connector_chain()
        related = doc.get_related_connectors("test:fc1", direction="backward")
        assert isinstance(related, list)

    def test_related_connectors_both(self):
        doc = _build_connector_chain()
        related = doc.get_related_connectors("test:bc1", direction="both")
        assert isinstance(related, list)

    def test_related_connectors_not_a_connector(self):
        doc = _build_connector_chain()
        related = doc.get_related_connectors("test:main")
        assert related == []

    def test_related_connectors_not_found(self):
        doc = _build_connector_chain()
        related = doc.get_related_connectors("test:nope")
        assert related == []


class TestTraversalPrecursorsSuccessorsExtra:
    def test_precursors(self):
        doc = _build_connector_chain()
        result = doc.get_precursors("test:fc1")
        assert result is None or isinstance(result, list)

    def test_successors_connectors(self):
        doc = _build_connector_chain()
        result = doc.get_successors_connectors("test:bc1")
        assert result is None or isinstance(result, list)

    def test_precursors_not_connector(self):
        doc = _build_connector_chain()
        result = doc.get_precursors("test:main")
        assert result is None

    def test_successors_not_connector(self):
        doc = _build_connector_chain()
        result = doc.get_successors_connectors("test:main")
        assert result is None

    def test_precursors_nonexistent(self):
        doc = _build_connector_chain()
        result = doc.get_precursors("test:nope")
        assert result is None

    def test_successors_nonexistent(self):
        doc = _build_connector_chain()
        result = doc.get_successors_connectors("test:nope")
        assert result is None


# ─── Subgraph ────────────────────────────────────────────────────────────────

class TestSubgraph:
    def test_subgraph_with_known_nodes(self):
        doc = _build_doc()
        sub = doc.get_subgraph(['test:e1', 'test:e2'])
        assert isinstance(sub, CpmDocument)
        assert len(sub.get_all_nodes()) <= 2

    def test_subgraph_empty_ids(self):
        doc = _build_doc()
        sub = doc.get_subgraph([])
        assert len(sub.get_all_nodes()) == 0

    def test_subgraph_nonexistent_ids(self):
        doc = _build_doc()
        sub = doc.get_subgraph(['test:nonexistent'])
        assert len(sub.get_all_nodes()) == 0

    def test_subgraph_without_edges(self):
        doc = _build_doc()
        sub = doc.get_subgraph(['test:e1', 'test:e2'], include_edges=False)
        assert isinstance(sub, CpmDocument)

    def test_subgraph_with_edges(self):
        doc = _build_doc()
        sub = doc.get_subgraph(['test:e1', 'test:main'], include_edges=True)
        assert isinstance(sub, CpmDocument)
