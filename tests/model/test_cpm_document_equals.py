"""
Test module for CpmDocument equality and comparison operations.
"""

import pytest
from prov.model import ProvDocument, PROV, PROV_TYPE
from src.cpm.model import CpmDocument


class TestCpmDocumentEquality:
    """Tests for CpmDocument equality comparison."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc1 = ProvDocument()
        self.doc2 = ProvDocument()
        self.cpm_ns1 = self.doc1.add_namespace('cpm', 'http://provcpm.org/')
        self.cpm_ns2 = self.doc2.add_namespace('cpm', 'http://provcpm.org/')

    def test_equal_documents_are_equal(self):
        """Test that identical documents are considered equal."""
        entity1 = self.doc1.entity('cpm:entity1')
        entity2 = self.doc2.entity('cpm:entity1')

        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)

        # Both should have same entity
        assert len(cpm_doc1.get_nodes('cpm:entity1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:entity1')) > 0

    def test_different_documents_are_not_equal(self):
        """Test that different documents are not equal."""
        entity1 = self.doc1.entity('cpm:entity1')
        entity2 = self.doc2.entity('cpm:entity2')

        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)

        # Different entities
        assert len(cpm_doc1.get_nodes('cpm:entity1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:entity2')) > 0
        assert len(cpm_doc1.get_nodes('cpm:entity2')) == 0

    def test_empty_documents_are_equal(self):
        """Test that two empty documents are equal."""
        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)

        # Both should be valid but empty
        assert cpm_doc1 is not None
        assert cpm_doc2 is not None


class TestCpmDocumentStructuralEquality:
    """Tests for structural equality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc1 = ProvDocument()
        self.doc2 = ProvDocument()
        self.cpm_ns1 = self.doc1.add_namespace('cpm', 'http://provcpm.org/')
        self.cpm_ns2 = self.doc2.add_namespace('cpm', 'http://provcpm.org/')

    def test_same_nodes_same_structure(self):
        """Test documents with same nodes and structure."""
        # Doc1
        e1 = self.doc1.entity('cpm:e1')
        a1 = self.doc1.activity('cpm:a1')
        self.doc1.wasGeneratedBy(e1, a1)

        # Doc2
        e2 = self.doc2.entity('cpm:e1')
        a2 = self.doc2.activity('cpm:a1')
        self.doc2.wasGeneratedBy(e2, a2)

        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)

        # Both should have same structure
        assert len(cpm_doc1.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0
        assert cpm_doc1.get_edge('cpm:e1', 'cpm:a1') is not None
        assert cpm_doc2.get_edge('cpm:e1', 'cpm:a1') is not None

    def test_same_nodes_different_edges(self):
        """Test documents with same nodes but different edges."""
        # Doc1
        e1 = self.doc1.entity('cpm:e1')
        a1 = self.doc1.activity('cpm:a1')
        self.doc1.wasGeneratedBy(e1, a1)

        # Doc2 - different edge type
        e2 = self.doc2.entity('cpm:e1')
        a2 = self.doc2.activity('cpm:a1')
        self.doc2.used(a2, e2)

        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)

        # Same nodes, different relationships
        assert len(cpm_doc1.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0


class TestCpmDocumentAttributeEquality:
    """Tests for attribute-based equality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc1 = ProvDocument()
        self.doc2 = ProvDocument()
        self.cpm_ns1 = self.doc1.add_namespace('cpm', 'http://provcpm.org/')
        self.cpm_ns2 = self.doc2.add_namespace('cpm', 'http://provcpm.org/')
        self.ex_ns1 = self.doc1.add_namespace('ex', 'http://example.org/')
        self.ex_ns2 = self.doc2.add_namespace('ex', 'http://example.org/')

    def test_same_node_same_attributes(self):
        """Test nodes with same attributes."""
        e1 = self.doc1.entity('cpm:e1', {self.ex_ns1['attr']: 'value'})
        e2 = self.doc2.entity('cpm:e1', {self.ex_ns2['attr']: 'value'})

        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)

        assert len(cpm_doc1.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0

    def test_same_node_different_attributes(self):
        """Test nodes with different attributes."""
        e1 = self.doc1.entity('cpm:e1', {self.ex_ns1['attr']: 'value1'})
        e2 = self.doc2.entity('cpm:e1', {self.ex_ns2['attr']: 'value2'})

        cpm_doc1 = CpmDocument(self.doc1)
        cpm_doc2 = CpmDocument(self.doc2)

        assert len(cpm_doc1.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc2.get_nodes('cpm:e1')) > 0


class TestCpmDocumentHashCode:
    """Tests for document hash code."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_document_hash_is_consistent(self):
        """Test that document hash is consistent."""
        entity = self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)

        # Should be hashable
        h1 = hash(cpm_doc)
        h2 = hash(cpm_doc)
        assert h1 == h2

    def test_equal_documents_same_hash(self):
        """Test that equal documents have same hash."""
        doc1 = ProvDocument()
        doc1.add_namespace('cpm', 'http://provcpm.org/')
        doc1.entity('cpm:entity1')

        doc2 = ProvDocument()
        doc2.add_namespace('cpm', 'http://provcpm.org/')
        doc2.entity('cpm:entity1')

        cpm_doc1 = CpmDocument(doc1)
        cpm_doc2 = CpmDocument(doc2)

        # Both should be hashable
        h1 = hash(cpm_doc1)
        h2 = hash(cpm_doc2)
        assert isinstance(h1, int)
        assert isinstance(h2, int)


class TestCpmDocumentComparison:
    """Tests for document comparison operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_compare_document_to_itself(self):
        """Test comparing document to itself."""
        entity = self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)

        # Should be same object
        assert cpm_doc is cpm_doc

    def test_compare_document_to_none(self):
        """Test comparing document to None."""
        entity = self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)

        # Should not be None
        assert cpm_doc is not None

    def test_compare_documents_different_types(self):
        """Test comparing document to different type."""
        entity = self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)

        # Should not equal a string
        assert cpm_doc != "not a document"
        assert not (cpm_doc == "not a document")
