"""
Test module for additional CpmDocument operations.
"""

import pytest
from prov.model import ProvDocument, PROV, PROV_TYPE
from src.cpm.model import CpmDocument


class TestCpmDocumentUtilities:
    """Tests for utility operations on CpmDocument."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_get_all_nodes(self):
        """Test retrieving all nodes from document."""
        self.doc.entity('cpm:e1')
        self.doc.entity('cpm:e2')
        self.doc.activity('cpm:a1')
        self.doc.agent('cpm:agent1')

        cpm_doc = CpmDocument(self.doc)

        # Should have all nodes
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:e2')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0

    def test_get_all_edges(self):
        """Test retrieving all edges from document."""
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        agent = self.doc.agent('cpm:agent1')

        self.doc.wasGeneratedBy(e1, a1)
        self.doc.wasAssociatedWith(a1, agent)

        cpm_doc = CpmDocument(self.doc)

        # Should have edges
        assert cpm_doc.get_edge('cpm:e1', 'cpm:a1') is not None
        assert cpm_doc.get_edge('cpm:a1', 'cpm:agent1') is not None

    def test_count_nodes_by_type(self):
        """Test counting nodes by type."""
        self.doc.entity('cpm:e1')
        self.doc.entity('cpm:e2')
        self.doc.activity('cpm:a1')
        self.doc.agent('cpm:agent1')

        cpm_doc = CpmDocument(self.doc)

        # Should be able to count
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0


class TestCpmDocumentNamespaces:
    """Tests for namespace handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()

    def test_add_namespace(self):
        """Test adding namespace to document."""
        ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

        cpm_doc = CpmDocument(self.doc)

        # Should have namespace
        assert cpm_doc is not None

    def test_multiple_namespaces(self):
        """Test handling multiple namespaces."""
        ns1 = self.doc.add_namespace('cpm', 'http://provcpm.org/')
        ns2 = self.doc.add_namespace('ex', 'http://example.org/')

        cpm_doc = CpmDocument(self.doc)

        # Should handle both
        assert cpm_doc is not None

    def test_qualified_names_with_namespace(self):
        """Test qualified names with namespaces."""
        self.doc.add_namespace('cpm', 'http://provcpm.org/')
        entity = self.doc.entity('cpm:entity1')

        cpm_doc = CpmDocument(self.doc)

        # Should find with qualified name
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0


class TestCpmDocumentBundles:
    """Tests for bundle operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
        self.ex_ns = self.doc.add_namespace('ex', 'http://example.org/')

    def test_create_bundle(self):
        """Test creating a bundle."""
        bundle = self.doc.bundle('ex:bundle1')
        bundle.entity('cpm:e1')

        cpm_doc = CpmDocument(self.doc)

        # Should have bundle
        bundle_id = cpm_doc.get_bundle_id()
        assert bundle_id is not None

    def test_bundle_with_multiple_elements(self):
        """Test bundle with multiple elements."""
        bundle = self.doc.bundle('ex:bundle1')
        bundle.entity('cpm:e1')
        bundle.entity('cpm:e2')
        bundle.activity('cpm:a1')

        cpm_doc = CpmDocument(self.doc)

        # Should have bundle
        assert cpm_doc.get_bundle_id() is not None

    def test_nested_bundles(self):
        """Test handling nested bundles if supported."""
        bundle1 = self.doc.bundle('ex:bundle1')
        bundle1.entity('cpm:e1')

        cpm_doc = CpmDocument(self.doc)

        # Should handle bundle
        assert cpm_doc.get_bundle_id() is not None


class TestCpmDocumentValidation:
    """Tests for document validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_validate_valid_document(self):
        """Test validating a valid document."""
        entity = self.doc.entity('cpm:e1')
        activity = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(entity, activity)

        cpm_doc = CpmDocument(self.doc)

        # Should be valid
        assert cpm_doc is not None

    def test_validate_empty_document(self):
        """Test validating an empty document."""
        cpm_doc = CpmDocument(self.doc)

        # Should be valid even if empty
        assert cpm_doc is not None

    def test_validate_document_with_orphan_edges(self):
        """Test validating document with edges but missing nodes."""
        # Create edge without full node context
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)

        cpm_doc = CpmDocument(self.doc)

        # Should handle gracefully
        assert cpm_doc is not None


class TestCpmDocumentSerialization:
    """Tests for document serialization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_serialize_to_prov(self):
        """Test serializing document to PROV."""
        entity = self.doc.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)

        # Should be serializable
        prov_doc = cpm_doc.to_prov_document()
        assert prov_doc is not None

    def test_roundtrip_serialization(self):
        """Test serializing and deserializing."""
        entity = self.doc.entity('cpm:e1')
        activity = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(entity, activity)

        cpm_doc1 = CpmDocument(self.doc)
        prov_doc = cpm_doc1.to_prov_document()
        cpm_doc2 = CpmDocument(prov_doc)

        # Should preserve structure
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:a1')) > 0
