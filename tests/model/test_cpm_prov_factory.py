"""
Test CPM PROV Factory Implementation

Tests for CPM PROV factory operations including:
- CPM type creation
- CPM qualified name creation
- CPM attribute creation  
- CPM entity/activity/agent creation
- Namespace management
"""

import pytest
from prov.model import ProvDocument, ProvEntity, ProvActivity, ProvAgent, ProvBundle, PROV, PROV_TYPE, PROV_ATTR_STARTTIME, PROV_ATTR_ENDTIME
from prov.identifier import QualifiedName, Namespace
from datetime import datetime

from src.cpm.constants import *
from src.cpm.model import CpmDocument


class TestCpmProvFactory:
    """Test CPM PROV factory operations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.doc = ProvDocument()
        self.doc.add_namespace('cpm', CPM_NAMESPACE_URI)
        self.doc.add_namespace('ex', 'http://example.org/')
        self.bundle = self.doc.bundle('ex:bundle')

    def test_create_cpm_namespace(self):
        """Test CPM namespace creation"""
        namespace_prefixes = {ns.prefix for ns in self.doc.namespaces}
        assert 'cpm' in namespace_prefixes
        # ProvDocument namespaces is a set
        cpm_ns = [ns for ns in self.doc.namespaces if ns.prefix == 'cpm'][0]
        assert cpm_ns.uri == CPM_NAMESPACE_URI

    def test_create_cpm_qualified_name(self):
        """Test creating CPM qualified names"""
        qname = QualifiedName(CPM, 'BackwardConnector')
        assert qname is not None
        assert qname.namespace.uri == CPM_NAMESPACE_URI
        assert qname.localpart == 'BackwardConnector'

    def test_create_backward_connector_entity(self):
        """Test creating backward connector entity with CPM type"""
        connector = self.bundle.entity('ex:bc1')
        connector.add_attributes([(PROV['type'], CPM_BACKWARD_CONNECTOR)])

        # Verify attributes
        prov_types = connector.get_attribute(PROV_TYPE)
        assert prov_types is not None
        assert CPM_BACKWARD_CONNECTOR in prov_types

    def test_create_forward_connector_entity(self):
        """Test creating forward connector entity with CPM type"""
        connector = self.bundle.entity('ex:fc1')
        connector.add_attributes([(PROV['type'], CPM_FORWARD_CONNECTOR)])

        prov_types = connector.get_attribute(PROV_TYPE)
        assert prov_types is not None
        assert CPM_FORWARD_CONNECTOR in prov_types

    def test_create_main_activity(self):
        """Test creating main activity with CPM type"""
        activity = self.bundle.activity('ex:main')
        activity.add_attributes([
            (PROV['type'], CPM_MAIN_ACTIVITY),
            (PROV_ATTR_STARTTIME, datetime(2024, 11, 13, 10, 0, 0)),
            (PROV_ATTR_ENDTIME, datetime(2024, 11, 13, 12, 0, 0))
        ])

        prov_types = activity.get_attribute(PROV_TYPE)
        assert prov_types is not None
        assert CPM_MAIN_ACTIVITY in prov_types

    def test_create_sender_agent(self):
        """Test creating sender agent with CPM type"""
        agent = self.bundle.agent('ex:sender')
        agent.add_attributes([(PROV['type'], CPM_SENDER_AGENT)])

        prov_types = agent.get_attribute(PROV_TYPE)
        assert prov_types is not None
        assert CPM_SENDER_AGENT in prov_types

    def test_create_receiver_agent(self):
        """Test creating receiver agent with CPM type"""
        agent = self.bundle.agent('ex:receiver')
        agent.add_attributes([(PROV['type'], CPM_RECEIVER_AGENT)])

        prov_types = agent.get_attribute(PROV_TYPE)
        assert prov_types is not None
        assert CPM_RECEIVER_AGENT in prov_types

    def test_create_identifier_entity(self):
        """Test creating identifier entity with CPM type"""
        identifier = self.bundle.entity('ex:identifier')
        identifier.add_attributes([(PROV['type'], CPM_IDENTIFIER_ENTITY)])

        prov_types = identifier.get_attribute(PROV_TYPE)
        assert prov_types is not None
        assert CPM_IDENTIFIER_ENTITY in prov_types

    def test_add_cpm_attributes_to_connector(self):
        """Test adding CPM-specific attributes to connector"""
        connector = self.bundle.entity('ex:bc1')
        connector.add_attributes([
            (PROV['type'], CPM_BACKWARD_CONNECTOR),
            (CPM_REFERENCED_BUNDLE_ID, 'ex:source_bundle'),
            (CPM_REFERENCED_BUNDLE_HASH_VALUE, 'abc123'),
            (CPM_HASH_ALG, 'SHA-256')
        ])

        # Verify all attributes were added
        assert connector.get_attribute(CPM_REFERENCED_BUNDLE_ID) is not None
        assert connector.get_attribute(CPM_REFERENCED_BUNDLE_HASH_VALUE) is not None
        assert connector.get_attribute(CPM_HASH_ALG) is not None

    def test_create_entity_with_multiple_types(self):
        """Test creating entity with multiple prov:type values"""
        entity = self.bundle.entity('ex:multitype')
        entity.add_attributes([
            (PROV['type'], CPM_BACKWARD_CONNECTOR),
            (PROV['type'], 'ex:CustomType')
        ])

        prov_types = entity.get_attribute(PROV_TYPE)
        assert prov_types is not None
        assert len(prov_types) >= 2

    def test_cpm_dct_haspart_attribute(self):
        """Test using dct:hasPart attribute"""
        entity = self.bundle.entity('ex:collection')
        entity.add_attributes([
            (DCT_HAS_PART, 'ex:member1'),
            (DCT_HAS_PART, 'ex:member2')
        ])

        haspart = entity.get_attribute(DCT_HAS_PART)
        assert haspart is not None

    def test_all_cpm_subtypes_are_qualified_names(self):
        """Test that all CPM subtypes are properly formed QualifiedNames"""
        subtypes = [
            CPM_MAIN_ACTIVITY,
            CPM_BACKWARD_CONNECTOR,
            CPM_FORWARD_CONNECTOR,
            CPM_SENDER_AGENT,
            CPM_RECEIVER_AGENT,
            CPM_IDENTIFIER_ENTITY
        ]

        for subtype in subtypes:
            assert isinstance(subtype, QualifiedName)
            assert subtype.namespace.uri == CPM_NAMESPACE_URI

    def test_all_cpm_attributes_are_qualified_names(self):
        """Test that all CPM attributes are properly formed QualifiedNames"""
        attributes = [
            CPM_REFERENCED_BUNDLE_ID,
            CPM_REFERENCED_BUNDLE_HASH_VALUE,
            CPM_REFERENCED_META_BUNDLE_ID,
            CPM_HASH_ALG
        ]

        for attr in attributes:
            assert isinstance(attr, QualifiedName)
            assert attr.namespace.uri == CPM_NAMESPACE_URI


class TestCpmProvFactoryDocumentCreation:
    """Test document creation with CPM PROV factory"""

    def test_create_minimal_cpm_document(self):
        """Test creating minimal valid CPM document"""
        doc = ProvDocument()
        doc.add_namespace('cpm', CPM_NAMESPACE_URI)
        doc.add_namespace('ex', 'http://example.org/')

        bundle = doc.bundle('ex:bundle')

        # Add main activity
        main_activity = bundle.activity('ex:main')
        main_activity.add_attributes([(PROV['type'], CPM_MAIN_ACTIVITY)])

        # Verify document structure
        assert doc is not None
        assert len(list(doc.bundles)) > 0

    def test_create_full_cpm_document(self):
        """Test creating full CPM document with all components"""
        doc = ProvDocument()
        doc.add_namespace('cpm', CPM_NAMESPACE_URI)
        doc.add_namespace('dct', DCT_NAMESPACE_URI)
        doc.add_namespace('ex', 'http://example.org/')

        bundle = doc.bundle('ex:bundle')

        # Main activity
        main_activity = bundle.activity('ex:main')
        main_activity.add_attributes([(PROV['type'], CPM_MAIN_ACTIVITY)])

        # Backward connector
        bc = bundle.entity('ex:bc1')
        bc.add_attributes([
            (PROV['type'], CPM_BACKWARD_CONNECTOR),
            (CPM_REFERENCED_BUNDLE_ID, 'ex:source'),
            (CPM_REFERENCED_BUNDLE_HASH_VALUE, 'hash123')
        ])

        # Forward connector
        fc = bundle.entity('ex:fc1')
        fc.add_attributes([
            (PROV['type'], CPM_FORWARD_CONNECTOR),
            (CPM_REFERENCED_BUNDLE_ID, 'ex:target'),
            (CPM_REFERENCED_BUNDLE_HASH_VALUE, 'hash456')
        ])

        # Agents
        sender = bundle.agent('ex:sender')
        sender.add_attributes([(PROV['type'], CPM_SENDER_AGENT)])

        receiver = bundle.agent('ex:receiver')
        receiver.add_attributes([(PROV['type'], CPM_RECEIVER_AGENT)])

        # Verify all components
        assert bundle.get_record('ex:main') is not None
        assert bundle.get_record('ex:bc1') is not None
        assert bundle.get_record('ex:fc1') is not None
        assert bundle.get_record('ex:sender') is not None
        assert bundle.get_record('ex:receiver') is not None

    def test_namespace_management(self):
        """Test CPM namespace management"""
        doc = ProvDocument()
        doc.add_namespace('cpm', CPM_NAMESPACE_URI)
        doc.add_namespace('dct', DCT_NAMESPACE_URI)

        # Verify namespaces are registered
        namespace_prefixes = {ns.prefix for ns in doc.namespaces}
        assert 'cpm' in namespace_prefixes
        assert 'dct' in namespace_prefixes

        cpm_ns = [ns for ns in doc.namespaces if ns.prefix == 'cpm'][0]
        dct_ns = [ns for ns in doc.namespaces if ns.prefix == 'dct'][0]

        assert cpm_ns.uri == CPM_NAMESPACE_URI
        assert dct_ns.uri == DCT_NAMESPACE_URI
