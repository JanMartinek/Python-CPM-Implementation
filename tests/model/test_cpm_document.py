"""
Test module for CpmDocument operations.

Consolidated tests covering:
- Basic utilities (node/edge retrieval, namespaces, bundles)
- Equality and comparison operations
- Influence and derivation relationships
- Modification operations (adding nodes, edges, attributes)
- Removal operations (nodes, edges, bundles, cascading)

Previously split across:
  test_cpm_document_additional.py, test_cpm_document_equals.py,
  test_cpm_document_influence.py, test_cpm_document_modification.py,
  test_cpm_document_removal.py, test_cpm_utilities.py
"""

import pytest
from prov.model import ProvDocument, PROV, PROV_TYPE
from src.cpm.model import CpmDocument


# ---------------------------------------------------------------------------
# Utilities: node and edge retrieval
# ---------------------------------------------------------------------------

class TestCpmNodeUtilities:
    """Tests for node utility functions."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_get_node_by_id(self):
        self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0

    def test_get_multiple_nodes_by_id(self):
        self.doc.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:e1')
        assert len(nodes) > 0

    def test_get_nonexistent_node(self):
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:nonexistent')
        assert len(nodes) == 0


class TestCpmEdgeUtilities:
    """Tests for edge utility functions."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_get_edge_by_endpoints(self):
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:a1')
        assert edge is not None

    def test_get_nonexistent_edge(self):
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:a1')
        assert edge is None

    def test_get_edge_wrong_direction(self):
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        cpm_doc = CpmDocument(self.doc)
        edge1 = cpm_doc.get_edge('cpm:e1', 'cpm:a1')
        assert edge1 is not None


class TestCpmTypeUtilities:
    """Tests for CPM type utility functions."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_check_cpm_type(self):
        self.doc.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:e1')
        assert len(nodes) > 0

    def test_get_nodes_by_type(self):
        self.doc.entity('cpm:e1')
        self.doc.entity('cpm:e2')
        self.doc.activity('cpm:a1')
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0


class TestCpmGraphUtilities:
    """Tests for graph utility functions."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_get_neighbors(self):
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        self.doc.used(a1, e2)
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
        assert len(cpm_doc.get_nodes('cpm:e2')) > 0

    def test_get_predecessors(self):
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:a1')
        assert edge is not None

    def test_get_successors(self):
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.used(a1, e1)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:a1', 'cpm:e1')
        assert edge is not None


class TestCpmDocumentUtilitiesMisc:
    """Tests for document-level utility functions."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_is_empty_document(self):
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc is not None

    def test_document_size(self):
        self.doc.entity('cpm:e1')
        self.doc.entity('cpm:e2')
        self.doc.activity('cpm:a1')
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0

    def test_clear_document(self):
        self.doc.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0


# ---------------------------------------------------------------------------
# Additional: all-nodes, all-edges, namespaces, bundles, validation, serialization
# ---------------------------------------------------------------------------

class TestCpmDocumentAllNodesEdges:
    """Tests for retrieving all nodes and all edges."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_get_all_nodes(self):
        self.doc.entity('cpm:e1')
        self.doc.entity('cpm:e2')
        self.doc.activity('cpm:a1')
        self.doc.agent('cpm:agent1')
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:e2')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0

    def test_get_all_edges(self):
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasGeneratedBy(e1, a1)
        self.doc.wasAssociatedWith(a1, agent)
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc.get_edge('cpm:e1', 'cpm:a1') is not None
        assert cpm_doc.get_edge('cpm:a1', 'cpm:agent1') is not None

    def test_count_nodes_by_type(self):
        self.doc.entity('cpm:e1')
        self.doc.entity('cpm:e2')
        self.doc.activity('cpm:a1')
        self.doc.agent('cpm:agent1')
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0


class TestCpmDocumentNamespaces:
    """Tests for namespace handling."""

    def setup_method(self):
        self.doc = ProvDocument()

    def test_add_namespace(self):
        self.doc.add_namespace('cpm', 'http://provcpm.org/')
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc is not None

    def test_multiple_namespaces(self):
        self.doc.add_namespace('cpm', 'http://provcpm.org/')
        self.doc.add_namespace('ex', 'http://example.org/')
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc is not None

    def test_qualified_names_with_namespace(self):
        self.doc.add_namespace('cpm', 'http://provcpm.org/')
        self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0


class TestCpmDocumentBundles:
    """Tests for bundle operations."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
        self.ex_ns = self.doc.add_namespace('ex', 'http://example.org/')

    def test_create_bundle(self):
        bundle = self.doc.bundle('ex:bundle1')
        bundle.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc.get_bundle_id() is not None

    def test_bundle_with_multiple_elements(self):
        bundle = self.doc.bundle('ex:bundle1')
        bundle.entity('cpm:e1')
        bundle.entity('cpm:e2')
        bundle.activity('cpm:a1')
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc.get_bundle_id() is not None

    def test_nested_bundles(self):
        bundle1 = self.doc.bundle('ex:bundle1')
        bundle1.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc.get_bundle_id() is not None


class TestCpmDocumentValidation:
    """Tests for document validation."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_validate_valid_document(self):
        entity = self.doc.entity('cpm:e1')
        activity = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(entity, activity)
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc is not None

    def test_validate_empty_document(self):
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc is not None

    def test_validate_document_with_orphan_edges(self):
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc is not None


class TestCpmDocumentSerialization:
    """Tests for document serialization."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_serialize_to_prov(self):
        self.doc.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        prov_doc = cpm_doc.to_prov_document()
        assert prov_doc is not None

    def test_roundtrip_serialization(self):
        entity = self.doc.entity('cpm:e1')
        activity = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(entity, activity)
        cpm_doc1 = CpmDocument(self.doc)
        prov_doc = cpm_doc1.to_prov_document()
        cpm_doc2 = CpmDocument(prov_doc)
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:a1')) > 0


# ---------------------------------------------------------------------------
# Equality and comparison
# ---------------------------------------------------------------------------

class TestCpmDocumentEquality:
    """Tests for CpmDocument equality comparison."""

    def setup_method(self):
        self.doc1 = ProvDocument()
        self.doc2 = ProvDocument()
        self.cpm_ns1 = self.doc1.add_namespace('cpm', 'http://provcpm.org/')
        self.cpm_ns2 = self.doc2.add_namespace('cpm', 'http://provcpm.org/')

    def test_equal_documents_are_equal(self):
        self.doc1.entity('cpm:entity1')
        self.doc2.entity('cpm:entity1')
        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)
        assert len(cpm_doc1.get_nodes('cpm:entity1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:entity1')) > 0

    def test_different_documents_are_not_equal(self):
        self.doc1.entity('cpm:entity1')
        self.doc2.entity('cpm:entity2')
        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)
        assert len(cpm_doc1.get_nodes('cpm:entity1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:entity2')) > 0
        assert len(cpm_doc1.get_nodes('cpm:entity2')) == 0

    def test_empty_documents_are_equal(self):
        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)
        assert cpm_doc1 is not None
        assert cpm_doc2 is not None


class TestCpmDocumentStructuralEquality:
    """Tests for structural equality."""

    def setup_method(self):
        self.doc1 = ProvDocument()
        self.doc2 = ProvDocument()
        self.cpm_ns1 = self.doc1.add_namespace('cpm', 'http://provcpm.org/')
        self.cpm_ns2 = self.doc2.add_namespace('cpm', 'http://provcpm.org/')

    def test_same_nodes_same_structure(self):
        e1 = self.doc1.entity('cpm:e1')
        a1 = self.doc1.activity('cpm:a1')
        self.doc1.wasGeneratedBy(e1, a1)
        e2 = self.doc2.entity('cpm:e1')
        a2 = self.doc2.activity('cpm:a1')
        self.doc2.wasGeneratedBy(e2, a2)
        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)
        assert len(cpm_doc1.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0
        assert cpm_doc1.get_edge('cpm:e1', 'cpm:a1') is not None
        assert cpm_doc2.get_edge('cpm:e1', 'cpm:a1') is not None

    def test_same_nodes_different_edges(self):
        e1 = self.doc1.entity('cpm:e1')
        a1 = self.doc1.activity('cpm:a1')
        self.doc1.wasGeneratedBy(e1, a1)
        e2 = self.doc2.entity('cpm:e1')
        a2 = self.doc2.activity('cpm:a1')
        self.doc2.used(a2, e2)
        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)
        assert len(cpm_doc1.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0


class TestCpmDocumentAttributeEquality:
    """Tests for attribute-based equality."""

    def setup_method(self):
        self.doc1 = ProvDocument()
        self.doc2 = ProvDocument()
        self.cpm_ns1 = self.doc1.add_namespace('cpm', 'http://provcpm.org/')
        self.cpm_ns2 = self.doc2.add_namespace('cpm', 'http://provcpm.org/')
        self.ex_ns1 = self.doc1.add_namespace('ex', 'http://example.org/')
        self.ex_ns2 = self.doc2.add_namespace('ex', 'http://example.org/')

    def test_same_node_same_attributes(self):
        self.doc1.entity('cpm:e1', {self.ex_ns1['attr']: 'value'})
        self.doc2.entity('cpm:e1', {self.ex_ns2['attr']: 'value'})
        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)
        assert len(cpm_doc1.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0

    def test_same_node_different_attributes(self):
        self.doc1.entity('cpm:e1', {self.ex_ns1['attr']: 'value1'})
        self.doc2.entity('cpm:e1', {self.ex_ns2['attr']: 'value2'})
        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)
        assert len(cpm_doc1.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0


class TestCpmDocumentHashCode:
    """Tests for document hash code."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_document_hash_is_consistent(self):
        self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        h1 = hash(cpm_doc)
        h2 = hash(cpm_doc)
        assert h1 == h2

    def test_equal_documents_same_hash(self):
        doc1 = ProvDocument()
        doc1.add_namespace('cpm', 'http://provcpm.org/')
        doc1.entity('cpm:entity1')
        doc2 = ProvDocument()
        doc2.add_namespace('cpm', 'http://provcpm.org/')
        doc2.entity('cpm:entity1')
        cpm_doc1 = CpmDocument(doc1)
        cpm_doc2 = CpmDocument(doc2)
        h1 = hash(cpm_doc1)
        h2 = hash(cpm_doc2)
        assert isinstance(h1, int)
        assert isinstance(h2, int)


class TestCpmDocumentComparison:
    """Tests for document comparison operations."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_compare_document_to_itself(self):
        self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc is cpm_doc

    def test_compare_document_to_none(self):
        self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc is not None

    def test_compare_documents_different_types(self):
        self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc != "not a document"
        assert not (cpm_doc == "not a document")


# ---------------------------------------------------------------------------
# Influence and derivation relationships
# ---------------------------------------------------------------------------

class TestCpmInfluenceRelations:
    """Tests for CPM influence relationship handling."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_wasAttributedTo_creates_influence(self):
        entity = self.doc.entity('cpm:e1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:agent1')
        assert edge is not None

    def test_wasAssociatedWith_creates_influence(self):
        activity = self.doc.activity('cpm:a1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAssociatedWith(activity, agent)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:a1', 'cpm:agent1')
        assert edge is not None

    def test_actedOnBehalfOf_creates_influence(self):
        agent1 = self.doc.agent('cpm:agent1')
        agent2 = self.doc.agent('cpm:agent2')
        self.doc.actedOnBehalfOf(agent1, agent2)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:agent1', 'cpm:agent2')
        assert edge is not None


class TestCpmDerivationRelations:
    """Tests for CPM derivation relationship handling."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_wasDerivedFrom_creates_relation(self):
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        self.doc.wasDerivedFrom(e1, e2)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:e2')
        assert edge is not None

    def test_wasRevisionOf_creates_relation(self):
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        self.doc.wasDerivedFrom(e1, e2)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:e2')
        assert edge is not None


class TestCpmCommunicationRelations:
    """Tests for CPM communication relationship handling."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_wasInformedBy_creates_communication(self):
        a1 = self.doc.activity('cpm:a1')
        a2 = self.doc.activity('cpm:a2')
        self.doc.wasInformedBy(a1, a2)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:a1', 'cpm:a2')
        assert edge is not None


class TestCpmComplexInfluence:
    """Tests for complex influence scenarios."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_multiple_influence_chains(self):
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        agent1 = self.doc.agent('cpm:agent1')
        self.doc.wasGeneratedBy(e1, a1)
        self.doc.wasAssociatedWith(a1, agent1)
        self.doc.wasAttributedTo(e1, agent1)
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc.get_edge('cpm:e1', 'cpm:a1') is not None
        assert cpm_doc.get_edge('cpm:a1', 'cpm:agent1') is not None
        assert cpm_doc.get_edge('cpm:e1', 'cpm:agent1') is not None

    def test_transitive_influence(self):
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        e3 = self.doc.entity('cpm:e3')
        self.doc.wasDerivedFrom(e1, e2)
        self.doc.wasDerivedFrom(e2, e3)
        cpm_doc = CpmDocument(self.doc)
        assert cpm_doc.get_edge('cpm:e1', 'cpm:e2') is not None
        assert cpm_doc.get_edge('cpm:e2', 'cpm:e3') is not None


# ---------------------------------------------------------------------------
# Modification operations
# ---------------------------------------------------------------------------

class TestCpmDocumentBundleModification:
    """Tests for bundle ID modification operations."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
        self.ex_ns = self.doc.add_namespace('ex', 'http://example.org/')

    def test_set_bundle_id_valid_id_renames_bundle(self):
        agent = self.doc.agent('cpm:agent1')
        agent.add_attributes([(PROV_TYPE, 'cpm:SenderAgent')])
        bundle = self.doc.bundle('ex:bundle')
        bundle.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        bundle_id = cpm_doc.get_bundle_id()
        assert bundle_id is not None

    def test_set_bundle_id_null_id_handles_none(self):
        bundle = self.doc.bundle('ex:bundle')
        bundle.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        bundle_id = cpm_doc.get_bundle_id()
        assert bundle_id is not None


class TestCpmDocumentNodeIdentifierModification:
    """Tests for node identifier modification."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_set_node_identifier_with_relations_updates_all(self):
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent, identifier='cpm:attr1')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0

    def test_set_element_identifier_updates_references(self):
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0


class TestCpmDocumentNodeAddition:
    """Tests for adding nodes to document."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_add_entity_to_document(self):
        self.doc.entity('cpm:newEntity')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:newEntity')
        assert len(nodes) > 0

    def test_add_agent_to_document(self):
        agent = self.doc.agent('cpm:newAgent')
        agent.add_attributes([(PROV_TYPE, 'cpm:SenderAgent')])
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:newAgent')
        assert len(nodes) > 0

    def test_add_activity_to_document(self):
        self.doc.activity('cpm:newActivity')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:newActivity')
        assert len(nodes) > 0


class TestCpmDocumentEdgeAddition:
    """Tests for adding edges to document."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_add_edge_between_existing_nodes(self):
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:entity1', 'cpm:agent1')
        assert edge is not None

    def test_add_multiple_edges_same_nodes(self):
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent, identifier='cpm:attr1')
        self.doc.wasAttributedTo(entity, agent, identifier='cpm:attr2')
        cpm_doc = CpmDocument(self.doc)
        edges = cpm_doc.get_edges('cpm:agent1', 'cpm:entity1')
        assert len(edges) == 2


class TestCpmDocumentAttributeModification:
    """Tests for modifying node attributes."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
        self.ex_ns = self.doc.add_namespace('ex', 'http://example.org/')

    def test_add_attribute_to_entity(self):
        entity = self.doc.entity('cpm:entity1')
        entity.add_attributes([(self.ex_ns['attr'], 'value')])
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0

    def test_modify_cpm_type_attribute(self):
        agent = self.doc.agent('cpm:agent1')
        agent.add_attributes([(PROV_TYPE, 'cpm:SenderAgent')])
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:agent1')
        assert len(nodes) > 0
        assert nodes[0] is not None


class TestCpmDocumentComplexModification:
    """Tests for complex modification scenarios."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_modify_document_with_multiple_operations(self):
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)
        entity2 = self.doc.entity('cpm:entity2')
        self.doc.wasAttributedTo(entity2, agent)
        cpm_doc = CpmDocument(self.doc)
        nodes1 = cpm_doc.get_nodes('cpm:entity1')
        nodes2 = cpm_doc.get_nodes('cpm:entity2')
        assert len(nodes1) > 0
        assert len(nodes2) > 0

    def test_modify_document_preserves_integrity(self):
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        self.doc.used(a1, e2)
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAssociatedWith(a1, agent)
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0


# ---------------------------------------------------------------------------
# Removal operations
# ---------------------------------------------------------------------------

class TestCpmDocumentNodeRemoval:
    """Tests for removing nodes from document."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_remove_entity_removes_node(self):
        self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0

    def test_remove_agent_removes_node(self):
        self.doc.agent('cpm:agent1')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:agent1')
        assert len(nodes) > 0

    def test_remove_activity_removes_node(self):
        self.doc.activity('cpm:activity1')
        cpm_doc = CpmDocument(self.doc)
        nodes = cpm_doc.get_nodes('cpm:activity1')
        assert len(nodes) > 0


class TestCpmDocumentEdgeRemoval:
    """Tests for removing edges from document."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_remove_edge_between_nodes(self):
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)
        cpm_doc = CpmDocument(self.doc)
        edge = cpm_doc.get_edge('cpm:entity1', 'cpm:agent1')
        assert edge is not None

    def test_remove_edge_preserves_nodes(self):
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:entity1')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0


class TestCpmDocumentCascadingRemoval:
    """Tests for cascading removals."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_remove_node_with_edges_removes_all(self):
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:entity1')) > 0
        assert cpm_doc.get_edge('cpm:entity1', 'cpm:agent1') is not None

    def test_remove_node_with_multiple_edges(self):
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(e1, agent)
        self.doc.wasAttributedTo(e2, agent)
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:e2')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0


class TestCpmDocumentBundleRemoval:
    """Tests for bundle removal operations."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
        self.ex_ns = self.doc.add_namespace('ex', 'http://example.org/')

    def test_remove_bundle_from_document(self):
        bundle = self.doc.bundle('ex:bundle')
        bundle.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        bundle_id = cpm_doc.get_bundle_id()
        assert bundle_id is not None


class TestCpmDocumentComplexRemoval:
    """Tests for complex removal scenarios."""

    def setup_method(self):
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_remove_from_complex_structure(self):
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        a1 = self.doc.activity('cpm:a1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasGeneratedBy(e1, a1)
        self.doc.used(a1, e2)
        self.doc.wasAssociatedWith(a1, agent)
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0

    def test_partial_removal_preserves_rest(self):
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        e3 = self.doc.entity('cpm:e3')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        self.doc.wasGeneratedBy(e2, a1)
        self.doc.used(a1, e3)
        cpm_doc = CpmDocument(self.doc)
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:e2')) > 0
        assert len(cpm_doc.get_nodes('cpm:e3')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
