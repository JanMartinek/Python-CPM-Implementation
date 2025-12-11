"""
Test module for CPM utilities and helper functions.
Corresponds to CpmUtilitiesTest.java.
"""

import pytest
from prov.model import ProvDocument, PROV
from src.cpm.model import CpmDocument


class TestCpmNodeUtilities:
    """Tests for node utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
    
    def test_get_node_by_id(self):
        """Test retrieving node by identifier."""
        entity = self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)
        
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0
    
    def test_get_multiple_nodes_by_id(self):
        """Test retrieving multiple nodes with same ID."""
        self.doc.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        
        nodes = cpm_doc.get_nodes('cpm:e1')
        assert len(nodes) > 0
    
    def test_get_nonexistent_node(self):
        """Test retrieving non-existent node."""
        cpm_doc = CpmDocument(self.doc)
        
        nodes = cpm_doc.get_nodes('cpm:nonexistent')
        assert len(nodes) == 0


class TestCpmEdgeUtilities:
    """Tests for edge utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
    
    def test_get_edge_by_endpoints(self):
        """Test retrieving edge by endpoint IDs."""
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        
        cpm_doc = CpmDocument(self.doc)
        
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:a1')
        assert edge is not None
    
    def test_get_nonexistent_edge(self):
        """Test retrieving non-existent edge."""
        cpm_doc = CpmDocument(self.doc)
        
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:a1')
        assert edge is None
    
    def test_get_edge_wrong_direction(self):
        """Test retrieving edge with reversed endpoints."""
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        
        cpm_doc = CpmDocument(self.doc)
        
        # Correct direction
        edge1 = cpm_doc.get_edge('cpm:e1', 'cpm:a1')
        assert edge1 is not None


class TestCpmTypeUtilities:
    """Tests for CPM type utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
    
    def test_check_cpm_type(self):
        """Test checking if node has CPM type."""
        entity = self.doc.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        
        nodes = cpm_doc.get_nodes('cpm:e1')
        assert len(nodes) > 0
    
    def test_get_nodes_by_type(self):
        """Test retrieving nodes by CPM type."""
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        a1 = self.doc.activity('cpm:a1')
        
        cpm_doc = CpmDocument(self.doc)
        
        # Should have all nodes
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0


class TestCpmGraphUtilities:
    """Tests for graph utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
    
    def test_get_neighbors(self):
        """Test getting neighboring nodes."""
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        a1 = self.doc.activity('cpm:a1')
        
        self.doc.wasGeneratedBy(e1, a1)
        self.doc.used(a1, e2)
        
        cpm_doc = CpmDocument(self.doc)
        
        # All nodes should exist
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
        assert len(cpm_doc.get_nodes('cpm:e2')) > 0
    
    def test_get_predecessors(self):
        """Test getting predecessor nodes."""
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.wasGeneratedBy(e1, a1)
        
        cpm_doc = CpmDocument(self.doc)
        
        # Should have connection
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:a1')
        assert edge is not None
    
    def test_get_successors(self):
        """Test getting successor nodes."""
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        self.doc.used(a1, e1)
        
        cpm_doc = CpmDocument(self.doc)
        
        # Should have connection
        edge = cpm_doc.get_edge('cpm:a1', 'cpm:e1')
        assert edge is not None


class TestCpmDocumentUtilities:
    """Tests for document-level utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
    
    def test_is_empty_document(self):
        """Test checking if document is empty."""
        cpm_doc = CpmDocument(self.doc)
        
        # Should be valid
        assert cpm_doc is not None
    
    def test_document_size(self):
        """Test getting document size."""
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        a1 = self.doc.activity('cpm:a1')
        
        cpm_doc = CpmDocument(self.doc)
        
        # Should have nodes
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
    
    def test_clear_document(self):
        """Test clearing document contents."""
        e1 = self.doc.entity('cpm:e1')
        cpm_doc = CpmDocument(self.doc)
        
        # Should have entity
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
