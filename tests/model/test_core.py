"""
Tests for CpmDocumentCoreMixin – covers the uncovered helpers and CRUD paths in core.py.
"""

import pytest
from prov.model import ProvDocument, ProvEntity, ProvActivity, ProvAgent
from prov.identifier import Namespace
from prov.constants import PROV_TYPE
from src.cpm.model import CpmDocument
from src.cpm.builder import CpmDocumentBuilder
from src.cpm.exceptions import (
    InvalidOperationError, NodeNotFoundError, CpmDocumentError,
    MultipleEdgesError, MultipleNodesError,
)


EX = Namespace("ex", "http://example.org/")


def _build_doc():
    builder = CpmDocumentBuilder("test:bundle")
    doc = (builder
           .with_main_activity("test:main", start_time="2024-01-01T00:00:00Z")
           .with_backward_connector("test:bc1", "test:src", "hash1")
           .with_forward_connector("test:fc1", "test:tgt", "hash2")
           .with_sender_agent("test:sender")
           .with_receiver_agent("test:receiver")
           .build())
    doc.add_node('entity', 'test:e1', {'label': 'Entity1'})
    doc.add_node('entity', 'test:e2', {'label': 'Entity2'})
    doc.add_edge('used', 'test:main', 'test:e1')
    doc.add_edge('wasgeneratedby', 'test:main', 'test:e2')
    doc.add_edge('wasderivedfrom', 'test:e2', 'test:e1')
    return doc


def _build_doc_minimal():
    """Minimal doc without extra entities/edges (used by extra tests)."""
    builder = CpmDocumentBuilder("test:bundle")
    doc = (builder
           .with_main_activity("test:main")
           .with_backward_connector("test:bc1", "test:src", "hash1")
           .with_forward_connector("test:fc1", "test:tgt", "hash2")
           .with_sender_agent("test:sender")
           .with_receiver_agent("test:receiver")
           .build())
    return doc


# ─── Bundle helpers ──────────────────────────────────────────────────────────

class TestBundleHelpers:
    def test_get_bundle(self):
        doc = _build_doc()
        bundle = doc._get_bundle()
        assert bundle is not None

    def test_mark_modified(self):
        doc = _build_doc()
        doc._mark_modified()
        assert doc.is_modified()

    def test_reinitialize_graph_wrapper(self):
        doc = _build_doc()
        original_count = len(doc.get_all_nodes())
        doc._reinitialize_graph_wrapper()
        assert len(doc.get_all_nodes()) == original_count


# ─── Node type checks ───────────────────────────────────────────────────────

class TestNodeTypeChecks:
    def test_has_cpm_type_on_connector(self):
        doc = _build_doc()
        bc = doc.get_node('test:bc1')
        from src.cpm.constants import CPM_BACKWARD_CONNECTOR
        assert doc._has_cpm_type(bc, CPM_BACKWARD_CONNECTOR)

    def test_node_has_type_entity(self):
        doc = _build_doc()
        node = doc.get_node('test:e1')
        assert doc._node_has_type(node, 'entity')
        assert doc._node_has_type(node, 'prov:entity')
        assert not doc._node_has_type(node, 'activity')

    def test_node_has_type_activity(self):
        doc = _build_doc()
        node = doc.get_node('test:main')
        assert doc._node_has_type(node, 'activity')

    def test_node_has_type_agent(self):
        doc = _build_doc()
        node = doc.get_node('test:sender')
        assert doc._node_has_type(node, 'agent')


# ─── add_node edge cases ────────────────────────────────────────────────────

class TestAddNode:
    def test_add_entity(self):
        doc = _build_doc()
        node = doc.add_node('entity', 'test:new_entity', {'description': 'new'})
        assert node is not None

    def test_add_activity(self):
        doc = _build_doc()
        node = doc.add_node('activity', 'test:act1')
        assert node is not None

    def test_add_agent(self):
        doc = _build_doc()
        node = doc.add_node('agent', 'test:ag1')
        assert node is not None

    def test_add_node_invalid_type_raises(self):
        doc = _build_doc()
        with pytest.raises((InvalidOperationError, CpmDocumentError)):
            doc.add_node('invalid_type', 'test:bad')

    def test_add_duplicate_node_raises(self):
        doc = _build_doc()
        with pytest.raises(InvalidOperationError):
            doc.add_node('entity', 'test:e1')

    def test_add_node_with_prov_type(self):
        doc = _build_doc()
        node = doc.add_node('entity', 'test:typed', prov_type='cpm:someType')
        assert node is not None

    def test_add_node_unprefixed_identifier(self):
        doc = _build_doc()
        node = doc.add_node('entity', 'simpleId')
        assert node is not None

    def test_add_node_with_attributes(self):
        doc = _build_doc()
        node = doc.add_node('entity', 'test:attr_node',
                            {'test:color': 'blue', 'size': 42})
        assert node is not None


# ─── remove_node / remove_nodes ──────────────────────────────────────────────

class TestRemoveNode:
    def test_remove_existing_node(self):
        doc = _build_doc()
        assert doc.remove_node('test:e1', 'entity')

    def test_remove_nonexistent_node(self):
        doc = _build_doc()
        assert not doc.remove_node('test:nonexistent')

    def test_remove_nodes_all(self):
        doc = _build_doc()
        doc.add_node('entity', 'test:dup')
        assert doc.remove_nodes('test:dup')

    def test_remove_nodes_nonexistent(self):
        doc = _build_doc()
        assert not doc.remove_nodes('test:nonexistent')


# ─── update_node_identifier ──────────────────────────────────────────────────

class TestUpdateNodeIdentifier:
    def test_update_identifier(self):
        doc = _build_doc()
        result = doc.update_node_identifier('test:e1', 'test:e1_renamed')
        assert result is True
        assert doc.get_node('test:e1_renamed') is not None

    def test_update_nonexistent(self):
        doc = _build_doc()
        with pytest.raises(NodeNotFoundError):
            doc.update_node_identifier('test:nonexistent', 'test:new')


# ─── Edge operations ─────────────────────────────────────────────────────────

class TestEdgeOperations:
    def test_get_edges_by_source(self):
        doc = _build_doc()
        edges = doc.get_edges(source_id='test:main')
        assert isinstance(edges, list)

    def test_get_edges_by_target(self):
        doc = _build_doc()
        edges = doc.get_edges(target_id='test:e1')
        assert isinstance(edges, list)

    def test_get_edges_by_relation_type(self):
        doc = _build_doc()
        edges = doc.get_edges(relation_type='derivation')
        assert isinstance(edges, list)

    def test_get_edge_single(self):
        doc = _build_doc()
        edge = doc.get_edge('test:main', 'test:e1')

    def test_add_edge_various_types(self):
        doc = _build_doc()
        doc.add_node('entity', 'test:e3')
        doc.add_node('activity', 'test:act2')
        doc.add_node('agent', 'test:ag2')

        doc.add_edge('wasassociatedwith', 'test:act2', 'test:ag2')
        doc.add_edge('wasattributedto', 'test:e3', 'test:ag2')
        doc.add_edge('wasinformedby', 'test:act2', 'test:main')
        doc.add_edge('wasinfluencedby', 'test:e3', 'test:e1')
        doc.add_edge('specializationof', 'test:e3', 'test:e1')
        doc.add_edge('alternateof', 'test:e3', 'test:e2')
        doc.add_edge('hadmember', 'test:e1', 'test:e3')

    def test_add_edge_invalid_type_raises(self):
        doc = _build_doc()
        with pytest.raises(InvalidOperationError):
            doc.add_edge('badtype', 'test:e1', 'test:e2')

    def test_add_edge_missing_source_raises(self):
        doc = _build_doc()
        with pytest.raises(NodeNotFoundError):
            doc.add_edge('used', 'test:nonexistent', 'test:e1')

    def test_add_edge_missing_target_raises(self):
        doc = _build_doc()
        with pytest.raises(NodeNotFoundError):
            doc.add_edge('used', 'test:main', 'test:nonexistent')

    def test_add_edge_with_id(self):
        doc = _build_doc()
        edge = doc.add_edge('used', 'test:main', 'test:e2', edge_id='test:myUsage')
        assert edge is not None
        retrieved = doc.get_edge_by_id('test:myUsage')
        assert retrieved is not None

    def test_remove_edge(self):
        doc = _build_doc()
        doc.add_node('entity', 'test:r1')
        doc.add_edge('wasderivedfrom', 'test:r1', 'test:e1')
        result = doc.remove_edge('test:r1', 'test:e1', 'derivation')

    def test_remove_edge_nonexistent(self):
        doc = _build_doc()
        result = doc.remove_edge('test:nonexistent', 'test:e1')
        assert result is False

    def test_remove_edges_batch(self):
        doc = _build_doc()
        removed = doc.remove_edges(source_id='test:main')
        assert isinstance(removed, int)

    def test_remove_edges_no_match(self):
        doc = _build_doc()
        removed = doc.remove_edges(source_id='test:nonexistent')
        assert removed == 0

    def test_get_edges_by_id(self):
        doc = _build_doc()
        doc.add_edge('used', 'test:main', 'test:e2', edge_id='test:usage2')
        edges = doc.get_edges_by_id('test:usage2')
        assert len(edges) >= 1

    def test_get_edges_by_id_nonexistent(self):
        doc = _build_doc()
        edges = doc.get_edges_by_id('test:nonexistent_edge')
        assert len(edges) == 0

    def test_remove_edge_by_id(self):
        doc = _build_doc()
        doc.add_edge('used', 'test:main', 'test:e2', edge_id='test:to_remove')
        result = doc.remove_edge_by_id('test:to_remove')
        assert result is True

    def test_remove_edge_by_id_nonexistent(self):
        doc = _build_doc()
        assert doc.remove_edge_by_id('test:nonexistent') is False


# ─── Attribute-based queries ─────────────────────────────────────────────────

class TestNodesByAttribute:
    def test_get_nodes_by_attribute_exists(self):
        doc = _build_doc()
        nodes = doc.get_nodes_by_attribute('prov:label')
        assert isinstance(nodes, list)

    def test_get_nodes_by_attribute_with_value(self):
        doc = _build_doc()
        nodes = doc.get_nodes_by_attribute('prov:label', 'Entity1')
        assert isinstance(nodes, list)

    def test_get_nodes_by_attribute_nonexistent(self):
        doc = _build_doc()
        nodes = doc.get_nodes_by_attribute('nonexistent:attr')
        assert nodes == []


# ─── Miscellaneous core methods ──────────────────────────────────────────────

class TestMiscCoreMethods:
    def test_are_all_relations_mapped(self):
        doc = _build_doc()
        result = doc.are_all_relations_mapped()
        assert isinstance(result, bool)

    def test_get_nodes_map(self):
        doc = _build_doc()
        nmap = doc.get_nodes_map()
        assert isinstance(nmap, dict)
        assert len(nmap) > 0

    def test_get_bundle_id(self):
        doc = _build_doc()
        bid = doc.get_bundle_id()
        assert bid is None or isinstance(bid, str)

    def test_set_bundle_id(self):
        doc = _build_doc()
        assert doc.set_bundle_id('test:newBundleId')
        assert doc.get_bundle_id() == 'test:newBundleId'

    def test_get_namespaces(self):
        doc = _build_doc()
        ns = doc.get_namespaces()
        assert isinstance(ns, dict)

    def test_to_document(self):
        doc = _build_doc()
        prov_doc = doc.to_document()
        assert isinstance(prov_doc, ProvDocument)

    def test_get_all_edges(self):
        doc = _build_doc()
        edges = doc.get_all_edges()
        assert isinstance(edges, list)
        assert len(edges) > 0

    def test_get_all_nodes(self):
        doc = _build_doc()
        nodes = doc.get_all_nodes()
        assert isinstance(nodes, list)
        assert len(nodes) > 0

    def test_get_node_by_element(self):
        doc = _build_doc()
        node = doc.get_node('test:e1')
        if node:
            found = doc.get_node_by_element(node.prov_entity)
            assert found is not None

    def test_get_node_by_element_not_found(self):
        doc = _build_doc()
        assert doc.get_node_by_element("not_a_real_element") is None

    def test_remove_node_by_kind(self):
        doc = _build_doc()
        doc.add_node('entity', 'test:killme')
        result = doc.remove_node_by_kind('test:killme', 'entity')
        assert result is True

    def test_remove_node_by_kind_wrong_kind(self):
        doc = _build_doc()
        result = doc.remove_node_by_kind('test:e1', 'activity')
        assert result is False

    def test_remove_edges_by_kind(self):
        doc = _build_doc()
        doc.add_node('entity', 'test:ek1')
        doc.add_edge('wasderivedfrom', 'test:ek1', 'test:e1')
        result = doc.remove_edges_by_kind('test:ek1', 'test:e1', 'derivation')
        assert isinstance(result, bool)

    def test_remove_edges_by_kind_nonexistent(self):
        doc = _build_doc()
        result = doc.remove_edges_by_kind('test:nope', 'test:nope2', 'derivation')
        assert result is False

    def test_set_ti_strategy(self):
        doc = _build_doc()
        doc.set_ti_strategy("custom_strategy")
        assert doc._ti_strategy == "custom_strategy"

    def test_get_edge_with_kind(self):
        doc = _build_doc()
        doc.add_edge('used', 'test:main', 'test:e2', edge_id='test:kinded')
        edge = doc.get_edge_with_kind('test:kinded', 'usage')

    def test_remove_element(self):
        doc = _build_doc()
        node = doc.get_node('test:e1')
        if node:
            result = doc.remove_element(node.prov_entity)
            assert isinstance(result, bool)

    def test_remove_element_none(self):
        doc = _build_doc()
        assert doc.remove_element(None) is False

    def test_set_new_cause_and_effect(self):
        doc = _build_doc()
        edges = doc.get_edges(relation_type='derivation')
        if edges:
            result = doc.set_new_cause_and_effect(edges[0], 'test:e1', 'test:e2')
            assert isinstance(result, bool)

    def test_set_new_cause_and_effect_no_relation(self):
        doc = _build_doc()
        assert doc.set_new_cause_and_effect(None, 'test:e1', 'test:e2') is False

    def test_update_element_identifier(self):
        doc = _build_doc()
        node = doc.get_node('test:e1')
        if node:
            result = doc.update_element_identifier(node.prov_entity, 'test:e1_upd')
            assert isinstance(result, bool)

    def test_update_element_identifier_none(self):
        doc = _build_doc()
        assert doc.update_element_identifier(None, 'test:e1_upd') is False

    def test_set_collection_members(self):
        doc = _build_doc()
        doc.add_node('entity', 'test:coll')
        doc.add_node('entity', 'test:m1')
        doc.add_node('entity', 'test:m2')
        doc.add_edge('hadmember', 'test:coll', 'test:m1')
        result = doc.set_collection_members(
            'test:coll', ['test:m1'],
            'test:coll', ['test:m1', 'test:m2']
        )
        assert result is True

    def test_set_collection_members_same(self):
        doc = _build_doc()
        result = doc.set_collection_members(
            'test:e1', ['test:e2'],
            'test:e1', ['test:e2']
        )
        assert result is True

    def test_extract_edge_endpoints(self):
        doc = _build_doc()
        edges = doc.get_edges()
        for edge in edges:
            source, target = doc._extract_edge_endpoints(edge)

    def test_remove_edges_for_node(self):
        doc = _build_doc()
        node = doc.get_node('test:e1')
        if node:
            doc._remove_edges_for_node(node)

    def test_get_edges_by_relation(self):
        doc = _build_doc()
        result = doc.get_edges_by_relation("random_relation")
        assert isinstance(result, list)

    def test_normalize_qname(self):
        doc = _build_doc()
        assert doc._normalize_qname("test:entity") == "test:entity"


# ═══════════════════════════════════════════════════════════════════════════════
# Extra tests – targets remaining uncovered lines
# ═══════════════════════════════════════════════════════════════════════════════


# ─── add_edge: all relation type branches ────────────────────────────────────

class TestAddEdgeRelationTypes:
    def _doc_with_two_entities(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("entity", "test:e2")
        return doc

    def _doc_with_entity_and_activity(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("activity", "test:a2")
        return doc

    def _doc_with_two_agents(self):
        doc = _build_doc_minimal()
        doc.add_node("agent", "test:ag1")
        doc.add_node("agent", "test:ag2")
        return doc

    def _doc_with_two_activities(self):
        doc = _build_doc_minimal()
        doc.add_node("activity", "test:a1")
        doc.add_node("activity", "test:a2")
        return doc

    def test_used(self):
        doc = self._doc_with_entity_and_activity()
        edge = doc.add_edge("used", "test:a2", "test:e1")
        assert edge is not None

    def test_wasgeneratedby(self):
        doc = self._doc_with_entity_and_activity()
        edge = doc.add_edge("wasgeneratedby", "test:a2", "test:e1")
        assert edge is not None

    def test_wasassociatedwith(self):
        doc = _build_doc_minimal()
        doc.add_node("activity", "test:a1")
        doc.add_node("agent", "test:ag1")
        edge = doc.add_edge("wasassociatedwith", "test:a1", "test:ag1")
        assert edge is not None

    def test_wasattributedto(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("agent", "test:ag1")
        edge = doc.add_edge("wasattributedto", "test:e1", "test:ag1")
        assert edge is not None

    def test_wasderivedfrom(self):
        doc = self._doc_with_two_entities()
        edge = doc.add_edge("wasderivedfrom", "test:e2", "test:e1")
        assert edge is not None

    def test_wasinformedby(self):
        doc = self._doc_with_two_activities()
        edge = doc.add_edge("wasinformedby", "test:a1", "test:a2")
        assert edge is not None

    def test_actedonbehalfof(self):
        doc = self._doc_with_two_agents()
        edge = doc.add_edge("actedonbehalfof", "test:ag1", "test:ag2")
        assert edge is not None

    def test_wasinfluencedby(self):
        doc = self._doc_with_two_entities()
        edge = doc.add_edge("wasinfluencedby", "test:e1", "test:e2")
        assert edge is not None

    def test_specializationof(self):
        doc = self._doc_with_two_entities()
        edge = doc.add_edge("specializationof", "test:e1", "test:e2")
        assert edge is not None

    def test_alternateof(self):
        doc = self._doc_with_two_entities()
        edge = doc.add_edge("alternateof", "test:e1", "test:e2")
        assert edge is not None

    def test_hadmember(self):
        doc = self._doc_with_two_entities()
        edge = doc.add_edge("hadmember", "test:e1", "test:e2")
        assert edge is not None

    def test_invalid_relation_type(self):
        doc = self._doc_with_two_entities()
        with pytest.raises(InvalidOperationError):
            doc.add_edge("nonsense", "test:e1", "test:e2")

    def test_source_not_found(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        with pytest.raises(NodeNotFoundError):
            doc.add_edge("used", "test:missing", "test:e1")

    def test_target_not_found(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        with pytest.raises(NodeNotFoundError):
            doc.add_edge("used", "test:e1", "test:missing")


# ─── _extract_edge_endpoints branches ────────────────────────────────────────

class TestExtractEdgeEndpoints:
    def test_usage_endpoint_extraction(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1")
        edges = doc.get_edges(relation_type="usage")
        assert len(edges) >= 1

    def test_generation_endpoint_extraction(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("wasgeneratedby", "test:main", "test:e1")
        edges = doc.get_edges(source_id="test:main")
        assert len(edges) >= 1

    def test_attribution_endpoint_extraction(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("agent", "test:ag1")
        doc.add_edge("wasattributedto", "test:e1", "test:ag1")
        edges = doc.get_edges()
        assert len(edges) >= 1

    def test_derivation_endpoint_extraction(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("entity", "test:e2")
        doc.add_edge("wasderivedfrom", "test:e2", "test:e1")
        edges = doc.get_edges(relation_type="derivation")
        assert len(edges) >= 1

    def test_delegation_endpoint_extraction(self):
        doc = _build_doc_minimal()
        doc.add_node("agent", "test:ag1")
        doc.add_node("agent", "test:ag2")
        doc.add_edge("actedonbehalfof", "test:ag1", "test:ag2")
        edges = doc.get_edges()
        assert len(edges) >= 1

    def test_communication_endpoint_extraction(self):
        doc = _build_doc_minimal()
        doc.add_node("activity", "test:a1")
        doc.add_node("activity", "test:a2")
        doc.add_edge("wasinformedby", "test:a1", "test:a2")
        edges = doc.get_edges()
        assert len(edges) >= 1


# ─── remove_node / _remove_edges_for_node ────────────────────────────────────

class TestRemoveNodePaths:
    def test_remove_node_also_removes_edges(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1")
        assert doc.remove_node("test:e1") is True
        assert doc.get_node("test:e1") is None

    def test_remove_nonexistent_node(self):
        doc = _build_doc_minimal()
        assert doc.remove_node("test:nope") is False

    def test_remove_node_with_type_filter(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:x")
        assert doc.remove_node("test:x", node_type="entity") is True

    def test_remove_node_type_filter_no_match(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:x")
        result = doc.remove_node("test:x", node_type="activity")
        assert result is True


# ─── remove_edge / remove_edges ──────────────────────────────────────────────

class TestRemoveEdge:
    def test_remove_edge_basic(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1")
        result = doc.remove_edge("test:main", "test:e1")
        assert result is True

    def test_remove_edge_not_found(self):
        doc = _build_doc_minimal()
        assert doc.remove_edge("test:main", "test:nope") is False

    def test_remove_edges_count(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("entity", "test:e2")
        doc.add_edge("used", "test:main", "test:e1")
        doc.add_edge("used", "test:main", "test:e2")
        count = doc.remove_edges(relation_type="usage")
        assert count >= 1


# ─── get_edge / get_edge_by_id / remove_edge_by_id ──────────────────────────

class TestEdgeById:
    def test_get_edge_by_id(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1", edge_id="test:u1")
        edge = doc.get_edge_by_id("test:u1")
        assert edge is not None

    def test_get_edge_by_id_not_found(self):
        doc = _build_doc_minimal()
        assert doc.get_edge_by_id("test:nope") is None

    def test_remove_edge_by_id(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1", edge_id="test:u1")
        assert doc.remove_edge_by_id("test:u1") is True

    def test_remove_edge_by_id_not_found(self):
        doc = _build_doc_minimal()
        assert doc.remove_edge_by_id("test:nope") is False


# ─── are_all_relations_mapped ────────────────────────────────────────────────

class TestRelationsMapped:
    def test_all_mapped(self):
        doc = _build_doc_minimal()
        result = doc.are_all_relations_mapped()
        assert isinstance(result, bool)


# ─── set_new_cause_and_effect ────────────────────────────────────────────────

class TestSetNewCauseAndEffect:
    def test_null_relation(self):
        doc = _build_doc_minimal()
        assert doc.set_new_cause_and_effect(None, "x", "y") is False

    def test_valid_update(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("entity", "test:e2")
        doc.add_node("entity", "test:e3")
        doc.add_edge("used", "test:main", "test:e1")
        edges = doc.get_edges(source_id="test:main", target_id="test:e1")
        if edges:
            result = doc.set_new_cause_and_effect(edges[0], "test:e2", "test:main")
            assert isinstance(result, bool)


# ─── collection members ──────────────────────────────────────────────────────

class TestCollectionMembers:
    def test_set_collection_members_same(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:coll")
        doc.add_node("entity", "test:m1")
        result = doc.set_collection_members("test:coll", ["test:m1"], "test:coll", ["test:m1"])
        assert result is True

    def test_set_collection_members_update(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:coll")
        doc.add_node("entity", "test:m1")
        doc.add_node("entity", "test:m2")
        result = doc.set_collection_members("test:coll", ["test:m1"], "test:coll", ["test:m2"])
        assert result is True

    def test_update_collection_members_advanced_valid(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:coll")
        doc.add_node("entity", "test:m1")
        result = doc.update_collection_members_advanced(
            "test:coll", ["test:m1"], "test:coll", ["test:m1"])
        assert result is True

    def test_update_collection_members_advanced_missing_collection(self):
        doc = _build_doc_minimal()
        result = doc.update_collection_members_advanced(
            "test:old", [], "test:new", ["test:m"])
        assert result is False

    def test_update_collection_members_advanced_missing_member(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:coll")
        result = doc.update_collection_members_advanced(
            "test:coll", [], "test:coll", ["test:missing"])
        assert result is False


# ─── update_element_identifier ───────────────────────────────────────────────

class TestUpdateElementIdentifier:
    def test_no_element(self):
        doc = _build_doc_minimal()
        assert doc.update_element_identifier(None, "new") is False

    def test_no_identifier_attr(self):
        doc = _build_doc_minimal()
        obj = object()
        assert doc.update_element_identifier(obj, "new") is False

    def test_same_identifier(self):
        doc = _build_doc_minimal()
        node = doc.get_node("test:main")
        if node:
            result = doc.update_element_identifier(node.prov_entity, str(node.identifier))
            assert result is True

    def test_new_identifier_already_exists(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("entity", "test:e2")
        node = doc.get_node("test:e1")
        if node:
            result = doc.update_element_identifier(node.prov_entity, "test:e2")
            assert result is False


# ─── set_element_identifier_advanced ─────────────────────────────────────────

class TestSetElementIdentifierAdvanced:
    def test_none_element(self):
        doc = _build_doc_minimal()
        assert doc.set_element_identifier_advanced(None, "new") is False

    def test_already_exists(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_node("entity", "test:e2")
        node = doc.get_node("test:e1")
        if node:
            result = doc.set_element_identifier_advanced(node.prov_entity, "test:e2")
            assert result is False


# ─── set_new_cause_and_effect_by_kind ────────────────────────────────────────

class TestSetNewCauseAndEffectByKind:
    def test_no_edges_found(self):
        doc = _build_doc_minimal()
        result = doc.set_new_cause_and_effect_by_kind(
            "test:x", "test:y", "usage", "test:a", "test:b")
        assert result is False


# ─── convenience getters ─────────────────────────────────────────────────────

class TestConvenienceGetters:
    def test_get_node_by_id_and_kind(self):
        doc = _build_doc_minimal()
        node = doc.get_node_by_id_and_kind("test:main", "activity")
        assert node is not None

    def test_get_node_by_id_and_kind_wrong_kind(self):
        doc = _build_doc_minimal()
        node = doc.get_node_by_id_and_kind("test:main", "entity")
        assert node is None

    def test_remove_node_by_kind_extra(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        assert doc.remove_node_by_kind("test:e1", "entity") is True

    def test_remove_node_by_kind_not_found(self):
        doc = _build_doc_minimal()
        assert doc.remove_node_by_kind("test:nope", "entity") is False

    def test_remove_edges_by_kind_extra(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1")
        result = doc.remove_edges_by_kind("test:e1", "test:main", "usage")
        assert isinstance(result, bool)

    def test_get_node_by_element_extra(self):
        doc = _build_doc_minimal()
        node = doc.get_node("test:main")
        if node:
            found = doc.get_node_by_element(node.prov_entity)
            assert found is not None

    def test_get_node_by_element_not_found_extra(self):
        doc = _build_doc_minimal()
        assert doc.get_node_by_element("nonexistent") is None

    def test_set_ti_strategy_extra(self):
        doc = _build_doc_minimal()
        doc.set_ti_strategy("test_strategy")
        assert doc._ti_strategy == "test_strategy"

    def test_get_namespaces_extra(self):
        doc = _build_doc_minimal()
        ns = doc.get_namespaces()
        assert isinstance(ns, dict)

    def test_to_document_extra(self):
        doc = _build_doc_minimal()
        prov_doc = doc.to_document()
        assert prov_doc is not None

    def test_get_all_edges_extra(self):
        doc = _build_doc_minimal()
        edges = doc.get_all_edges()
        assert isinstance(edges, list)

    def test_get_all_nodes_extra(self):
        doc = _build_doc_minimal()
        nodes = doc.get_all_nodes()
        assert isinstance(nodes, list)
        assert len(nodes) > 0

    def test_get_nodes_map_extra(self):
        doc = _build_doc_minimal()
        m = doc.get_nodes_map()
        assert isinstance(m, dict)

    def test_get_edge_with_kind_no_kind(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1", edge_id="test:u1")
        result = doc.get_edge_with_kind("test:u1")
        assert result is not None

    def test_get_edge_with_kind_match(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1", edge_id="test:u1")
        result = doc.get_edge_with_kind("test:u1", "usage")
        assert result is not None

    def test_get_edge_with_kind_mismatch(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        doc.add_edge("used", "test:main", "test:e1", edge_id="test:u1")
        result = doc.get_edge_with_kind("test:u1", "derivation")
        assert result is None

    def test_get_edges_by_relation_extra(self):
        doc = _build_doc_minimal()
        edges = doc.get_edges_by_relation("something")
        assert isinstance(edges, list)


# ─── remove_element ──────────────────────────────────────────────────────────

class TestRemoveElement:
    def test_none(self):
        doc = _build_doc_minimal()
        assert doc.remove_element(None) is False

    def test_not_found(self):
        doc = _build_doc_minimal()
        assert doc.remove_element("nonexistent") is False

    def test_valid(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        node = doc.get_node("test:e1")
        if node:
            assert doc.remove_element(node.prov_entity) is True


# ─── bundle ID ───────────────────────────────────────────────────────────────

class TestBundleId:
    def test_get_bundle_id(self):
        doc = _build_doc_minimal()
        bid = doc.get_bundle_id()
        assert bid is not None

    def test_set_bundle_id(self):
        doc = _build_doc_minimal()
        assert doc.set_bundle_id("test:newbundle") is True
        assert doc.get_bundle_id() == "test:newbundle"


# ─── add_node with various identifier forms ──────────────────────────────────

class TestAddNodePaths:
    def test_add_activity(self):
        doc = _build_doc_minimal()
        node = doc.add_node("activity", "test:a2")
        assert node is not None

    def test_add_agent(self):
        doc = _build_doc_minimal()
        node = doc.add_node("agent", "test:ag_new")
        assert node is not None

    def test_add_node_duplicate(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:e1")
        with pytest.raises(InvalidOperationError):
            doc.add_node("entity", "test:e1")

    def test_add_node_invalid_type(self):
        doc = _build_doc_minimal()
        with pytest.raises((InvalidOperationError, CpmDocumentError)):
            doc.add_node("invalid_type", "test:xxx")

    def test_add_node_with_prov_type(self):
        doc = _build_doc_minimal()
        node = doc.add_node("entity", "test:typed", prov_type="cpm:SomeType")
        assert node is not None

    def test_add_node_with_attributes(self):
        doc = _build_doc_minimal()
        node = doc.add_node("entity", "test:attrs", attributes={"ex:label": "hello"})
        assert node is not None


# ─── update_node_identifier (advanced) ───────────────────────────────────────

class TestUpdateNodeIdentifierAdvanced:
    def test_basic_rename(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:old")
        result = doc.update_node_identifier("test:old", "test:new")
        assert result is True
        assert doc.get_node("test:new") is not None
        assert doc.get_node("test:old") is None

    def test_rename_nonexistent(self):
        doc = _build_doc_minimal()
        with pytest.raises(NodeNotFoundError):
            doc.update_node_identifier("test:nope", "test:new")

    def test_rename_to_existing(self):
        doc = _build_doc_minimal()
        doc.add_node("entity", "test:a")
        doc.add_node("entity", "test:b")
        with pytest.raises(InvalidOperationError):
            doc.update_node_identifier("test:a", "test:b")
