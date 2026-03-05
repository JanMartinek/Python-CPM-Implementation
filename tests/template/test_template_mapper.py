"""
Tests for TemplateProvMapper – targets template_mapper.py uncovered lines:
map_to_document, _map_main_activity, _map_backward_connector,
_map_forward_connector, _map_sender_agent, _map_receiver_agent,
_map_identifier_entity, _create_qualified_name, _create_relations.
"""

import pytest
from prov.model import ProvDocument

from src.cpm.template_mapper import TemplateProvMapper
from src.cpm.template import (
    TraversalInformationTemplate,
    MainActivityTemplate,
    ConnectorTemplate,
    AgentTemplate,
    IdentifierEntityTemplate,
    RelationTemplate,
)


def _minimal_template():
    return TraversalInformationTemplate(
        bundle_name="test:bundle",
        prefixes={},
        main_activity=MainActivityTemplate(
            id="test:main",
            used=[],
            generated=[],
        ),
        backward_connectors=[],
        forward_connectors=[],
        sender_agents=[],
        receiver_agents=[],
        identifier_entities=[],
    )


def _full_template():
    return TraversalInformationTemplate(
        bundle_name="test:bundle",
        prefixes={"ex": "http://example.org/"},
        main_activity=MainActivityTemplate(
            id="test:main",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            referenced_meta_bundle_id="test:meta",
            has_part=["test:sub1"],
            used=[RelationTemplate(target_id="test:bc1", relation_id="test:u1")],
            generated=["test:fc1"],
            attributes={"ex:custom": "value1"},
        ),
        backward_connectors=[
            ConnectorTemplate(
                id="test:bc1",
                external_id="ext:bc1",
                referenced_bundle_id="test:ref",
                referenced_meta_bundle_id="test:refmeta",
                referenced_bundle_hash_value="abc123",
                hash_alg="SHA-256",
                provenance_service_uri="http://prov.example.org",
                derived_from=[],
                specialized_by=[],
                attributed_to=RelationTemplate(target_id="test:sender", relation_id="test:attr1"),
                attributes={"ex:note": "bc"},
            ),
        ],
        forward_connectors=[
            ConnectorTemplate(
                id="test:fc1",
                external_id="ext:fc1",
                referenced_bundle_id="test:fref",
                referenced_meta_bundle_id="test:frefmeta",
                referenced_bundle_hash_value="def456",
                hash_alg="SHA-256",
                provenance_service_uri="http://prov2.example.org",
                derived_from=["test:bc1"],
                specialized_by=["test:bc1"],
                specialization_of="test:bc1",
                attributed_to=RelationTemplate(target_id="test:receiver", relation_id="test:attr2"),
                attributes={"ex:note": "fc"},
            ),
        ],
        sender_agents=[
            AgentTemplate(id="test:sender", contact_id_pid="pid:sender",
                          attributes={"ex:role": "sender"}),
        ],
        receiver_agents=[
            AgentTemplate(id="test:receiver", contact_id_pid="pid:receiver",
                          attributes={"ex:role": "receiver"}),
        ],
        identifier_entities=[
            IdentifierEntityTemplate(
                id="test:ident",
                external_id="ext:ident",
                external_id_type="DOI",
                comment="test identifier",
                attributes={"ex:info": "extra"},
            ),
        ],
    )


class TestTemplateProvMapper:
    def test_minimal_mapping(self):
        mapper = TemplateProvMapper()
        doc = mapper.map_to_document(_minimal_template())
        assert isinstance(doc, ProvDocument)

    def test_full_mapping(self):
        mapper = TemplateProvMapper()
        doc = mapper.map_to_document(_full_template())
        assert isinstance(doc, ProvDocument)
        # Should have at least one bundle
        bundles = list(doc.bundles)
        assert len(bundles) >= 1

    def test_merge_agents_true(self):
        tmpl = _full_template()
        # Add a receiver with same id as sender
        tmpl.receiver_agents.append(
            AgentTemplate(id="test:sender", contact_id_pid="pid:sender2"))
        mapper = TemplateProvMapper(merge_agents=True)
        doc = mapper.map_to_document(tmpl)
        assert isinstance(doc, ProvDocument)

    def test_merge_agents_false(self):
        tmpl = _full_template()
        tmpl.receiver_agents.append(
            AgentTemplate(id="test:sender", contact_id_pid="pid:sender2"))
        mapper = TemplateProvMapper(merge_agents=False)
        doc = mapper.map_to_document(tmpl)
        assert isinstance(doc, ProvDocument)

    def test_unprefixed_bundle_name(self):
        tmpl = _minimal_template()
        tmpl.bundle_name = "simplebundle"
        mapper = TemplateProvMapper()
        doc = mapper.map_to_document(tmpl)
        assert isinstance(doc, ProvDocument)

    def test_create_qualified_name_empty_raises(self):
        mapper = TemplateProvMapper()
        doc = ProvDocument()
        doc.add_namespace("ex", "http://example.org/")
        bundle = doc.bundle(doc.valid_qualified_name("ex:b"))
        with pytest.raises(ValueError):
            mapper._create_qualified_name(bundle, "")

    def test_create_qualified_name_prefixed(self):
        mapper = TemplateProvMapper()
        doc = ProvDocument()
        doc.add_namespace("ex", "http://example.org/")
        bundle = doc.bundle(doc.valid_qualified_name("ex:b"))
        qname = mapper._create_qualified_name(bundle, "ex:thing")
        assert qname is not None

    def test_create_qualified_name_new_prefix(self):
        mapper = TemplateProvMapper()
        doc = ProvDocument()
        doc.add_namespace("ex", "http://example.org/")
        bundle = doc.bundle(doc.valid_qualified_name("ex:b"))
        qname = mapper._create_qualified_name(bundle, "newns:thing")
        assert qname is not None

    def test_create_qualified_name_simple(self):
        mapper = TemplateProvMapper()
        doc = ProvDocument()
        doc.add_namespace("ex", "http://example.org/")
        bundle = doc.bundle(doc.valid_qualified_name("ex:b"))
        qname = mapper._create_qualified_name(bundle, "simplename")
        assert qname is not None

    def test_relations_created(self):
        mapper = TemplateProvMapper()
        doc = mapper.map_to_document(_full_template())
        bundles = list(doc.bundles)
        bundle = bundles[0]
        records = list(bundle.get_records())
        # Should have activities, entities, agents, plus relations
        assert len(records) > 5
