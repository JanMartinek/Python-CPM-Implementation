"""
Test module for CpmDocument removal operations.
"""

import pytest
from prov.model import ProvDocument, PROV
from src.cpm.model import CpmDocument


class TestCpmDocumentNodeRemoval:
    """Tests for removing nodes from document."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_remove_entity_removes_node(self):
        """Test removing an entity node."""
        entity = self.doc.entity('cpm:entity1')
        cpm_doc = CpmDocument(self.doc)

        # Should have entity
        nodes = cpm_doc.get_nodes('cpm:entity1')
        assert len(nodes) > 0

    def test_remove_agent_removes_node(self):
        """Test removing an agent node."""
        agent = self.doc.agent('cpm:agent1')
        cpm_doc = CpmDocument(self.doc)

        nodes = cpm_doc.get_nodes('cpm:agent1')
        assert len(nodes) > 0

    def test_remove_activity_removes_node(self):
        """Test removing an activity node."""
        activity = self.doc.activity('cpm:activity1')
        cpm_doc = CpmDocument(self.doc)

        nodes = cpm_doc.get_nodes('cpm:activity1')
        assert len(nodes) > 0


class TestCpmDocumentEdgeRemoval:
    """Tests for removing edges from document."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_remove_edge_between_nodes(self):
        """Test removing an edge."""
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)

        cpm_doc = CpmDocument(self.doc)

        # Should have edge
        edge = cpm_doc.get_edge('cpm:entity1', 'cpm:agent1')
        assert edge is not None

    def test_remove_edge_preserves_nodes(self):
        """Test that removing edge keeps nodes."""
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)

        cpm_doc = CpmDocument(self.doc)

        # Should still have both nodes
        assert len(cpm_doc.get_nodes('cpm:entity1')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0


class TestCpmDocumentCascadingRemoval:
    """Tests for cascading removals."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_remove_node_with_edges_removes_all(self):
        """Test removing node also handles connected edges."""
        entity = self.doc.entity('cpm:entity1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)

        cpm_doc = CpmDocument(self.doc)

        # Both should exist
        assert len(cpm_doc.get_nodes('cpm:entity1')) > 0
        assert cpm_doc.get_edge('cpm:entity1', 'cpm:agent1') is not None

    def test_remove_node_with_multiple_edges(self):
        """Test removing node with multiple connections."""
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        agent = self.doc.agent('cpm:agent1')

        self.doc.wasAttributedTo(e1, agent)
        self.doc.wasAttributedTo(e2, agent)

        cpm_doc = CpmDocument(self.doc)

        # All should exist
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:e2')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0


class TestCpmDocumentBundleRemoval:
    """Tests for bundle removal operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')
        self.ex_ns = self.doc.add_namespace('ex', 'http://example.org/')

    def test_remove_bundle_from_document(self):
        """Test removing a bundle."""
        bundle = self.doc.bundle('ex:bundle')
        bundle.entity('cpm:entity1')

        cpm_doc = CpmDocument(self.doc)

        # Should have bundle
        bundle_id = cpm_doc.get_bundle_id()
        assert bundle_id is not None


class TestCpmDocumentComplexRemoval:
    """Tests for complex removal scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_remove_from_complex_structure(self):
        """Test removing from complex document structure."""
        # Create complex structure
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        a1 = self.doc.activity('cpm:a1')
        agent = self.doc.agent('cpm:agent1')

        self.doc.wasGeneratedBy(e1, a1)
        self.doc.used(a1, e2)
        self.doc.wasAssociatedWith(a1, agent)

        cpm_doc = CpmDocument(self.doc)

        # All should exist
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
        assert len(cpm_doc.get_nodes('cpm:agent1')) > 0

    def test_partial_removal_preserves_rest(self):
        """Test that partial removal preserves remaining structure."""
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        e3 = self.doc.entity('cpm:e3')
        a1 = self.doc.activity('cpm:a1')

        self.doc.wasGeneratedBy(e1, a1)
        self.doc.wasGeneratedBy(e2, a1)
        self.doc.used(a1, e3)

        cpm_doc = CpmDocument(self.doc)

        # All should be present
        assert len(cpm_doc.get_nodes('cpm:e1')) > 0
        assert len(cpm_doc.get_nodes('cpm:e2')) > 0
        assert len(cpm_doc.get_nodes('cpm:e3')) > 0
        assert len(cpm_doc.get_nodes('cpm:a1')) > 0
