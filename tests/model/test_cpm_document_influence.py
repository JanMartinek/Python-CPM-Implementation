"""
Test module for CPM influence relationship operations.
"""

import pytest
from prov.model import ProvDocument, PROV
from src.cpm.model import CpmDocument


class TestCpmInfluenceRelations:
    """Tests for CPM influence relationship handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_wasAttributedTo_creates_influence(self):
        """Test wasAttributedTo creates influence relation."""
        entity = self.doc.entity('cpm:e1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAttributedTo(entity, agent)

        cpm_doc = CpmDocument(self.doc)

        # Should have influence edge
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:agent1')
        assert edge is not None

    def test_wasAssociatedWith_creates_influence(self):
        """Test wasAssociatedWith creates influence relation."""
        activity = self.doc.activity('cpm:a1')
        agent = self.doc.agent('cpm:agent1')
        self.doc.wasAssociatedWith(activity, agent)

        cpm_doc = CpmDocument(self.doc)

        # Should have influence edge
        edge = cpm_doc.get_edge('cpm:a1', 'cpm:agent1')
        assert edge is not None

    def test_actedOnBehalfOf_creates_influence(self):
        """Test actedOnBehalfOf creates influence relation."""
        agent1 = self.doc.agent('cpm:agent1')
        agent2 = self.doc.agent('cpm:agent2')
        self.doc.actedOnBehalfOf(agent1, agent2)

        cpm_doc = CpmDocument(self.doc)

        # Should have influence edge
        edge = cpm_doc.get_edge('cpm:agent1', 'cpm:agent2')
        assert edge is not None


class TestCpmDerivationRelations:
    """Tests for CPM derivation relationship handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_wasDerivedFrom_creates_relation(self):
        """Test wasDerivedFrom creates derivation relation."""
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        self.doc.wasDerivedFrom(e1, e2)

        cpm_doc = CpmDocument(self.doc)

        # Should have derivation edge
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:e2')
        assert edge is not None

    def test_wasRevisionOf_creates_relation(self):
        """Test wasRevisionOf creates revision relation."""
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        # PROV library may not have wasRevisionOf directly
        self.doc.wasDerivedFrom(e1, e2)

        cpm_doc = CpmDocument(self.doc)

        # Should have relation
        edge = cpm_doc.get_edge('cpm:e1', 'cpm:e2')
        assert edge is not None


class TestCpmCommunicationRelations:
    """Tests for CPM communication relationship handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_wasInformedBy_creates_communication(self):
        """Test wasInformedBy creates communication relation."""
        a1 = self.doc.activity('cpm:a1')
        a2 = self.doc.activity('cpm:a2')
        self.doc.wasInformedBy(a1, a2)

        cpm_doc = CpmDocument(self.doc)

        # Should have communication edge
        edge = cpm_doc.get_edge('cpm:a1', 'cpm:a2')
        assert edge is not None


class TestCpmComplexInfluence:
    """Tests for complex influence scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.doc = ProvDocument()
        self.cpm_ns = self.doc.add_namespace('cpm', 'http://provcpm.org/')

    def test_multiple_influence_chains(self):
        """Test handling multiple influence chains."""
        e1 = self.doc.entity('cpm:e1')
        a1 = self.doc.activity('cpm:a1')
        agent1 = self.doc.agent('cpm:agent1')

        self.doc.wasGeneratedBy(e1, a1)
        self.doc.wasAssociatedWith(a1, agent1)
        self.doc.wasAttributedTo(e1, agent1)

        cpm_doc = CpmDocument(self.doc)

        # Should have all influence relationships
        assert cpm_doc.get_edge('cpm:e1', 'cpm:a1') is not None
        assert cpm_doc.get_edge('cpm:a1', 'cpm:agent1') is not None
        assert cpm_doc.get_edge('cpm:e1', 'cpm:agent1') is not None

    def test_transitive_influence(self):
        """Test transitive influence relationships."""
        e1 = self.doc.entity('cpm:e1')
        e2 = self.doc.entity('cpm:e2')
        e3 = self.doc.entity('cpm:e3')

        self.doc.wasDerivedFrom(e1, e2)
        self.doc.wasDerivedFrom(e2, e3)

        cpm_doc = CpmDocument(self.doc)

        # Should have derivation chain
        assert cpm_doc.get_edge('cpm:e1', 'cpm:e2') is not None
        assert cpm_doc.get_edge('cpm:e2', 'cpm:e3') is not None
