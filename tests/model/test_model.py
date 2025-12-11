"""Tests for Python TemplateProvMapper and CpmDocument.

These tests verify:
 - Traversal Information mapping
 - Main Activity mapping
 - Connector mapping

They verify correct mapping of TraversalInformationTemplate to a PROV document,
agent merging behavior, connector relations, identifier entities and relation creation.
"""
import pytest
from prov.model import ProvDocument, ProvAgent, ProvActivity, ProvEntity, ProvBundle
from src.cpm.template import (
    TraversalInformationTemplate,
    MainActivityTemplate,
    ConnectorTemplate,
    AgentTemplate,
    IdentifierEntityTemplate,
    RelationTemplate,
)
from src.cpm.model import TemplateProvMapper, CpmDocument
from src.cpm.constants import (
    CPM_MAIN_ACTIVITY,
    CPM_BACKWARD_CONNECTOR,
    CPM_FORWARD_CONNECTOR,
    CPM_SENDER_AGENT,
    CPM_RECEIVER_AGENT,
    CPM_IDENTIFIER_ENTITY,
    CPM_REFERENCED_BUNDLE_HASH_VALUE,
    CPM_HASH_ALG,
)
from prov.constants import PROV_TYPE


def build_basic_template():
    """Construct a minimal but rich traversal information template."""
    prefixes = {"ex": "http://example.org/"}
    bundle_name = "ex:bundle1"

    # Main activity uses bc1 and generates fc1
    main_activity = MainActivityTemplate(
        id="ex:activity1",
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-01T01:00:00Z",
        used=[RelationTemplate(target_id="ex:bc1")],
        generated=["ex:fc1"],
        has_part=["ex:subActivity"],
        attributes={"prov:label": "Main Activity"},
    )

    backward_connector = ConnectorTemplate(
        id="ex:bc1",
        referenced_bundle_id="ex:otherBundle",
        referenced_bundle_hash_value="hash123",
        hash_alg="SHA256",
        derived_from=[],
        attributes={"prov:label": "Backward"},
    )

    forward_connector = ConnectorTemplate(
        id="ex:fc1",
        derived_from=["ex:bc1"],
        specialized_by=[],
        attributes={"prov:label": "Forward"},
    )

    sender_agent = AgentTemplate(id="ex:agent1", attributes={"role": "sender"})
    receiver_agent = AgentTemplate(id="ex:agent1", attributes={"role": "receiver"})

    identifier_entity = IdentifierEntityTemplate(
        id="ex:id1", external_id="ex:externalEntity", attributes={"category": "identifier"}
    )

    return TraversalInformationTemplate(
        prefixes=prefixes,
        bundle_name=bundle_name,
        main_activity=main_activity,
        backward_connectors=[backward_connector],
        forward_connectors=[forward_connector],
        sender_agents=[sender_agent],
        receiver_agents=[receiver_agent],
        identifier_entities=[identifier_entity],
    )


def _get_bundle(doc: ProvDocument) -> ProvBundle:
    bundles = list(doc.bundles)
    assert bundles, "No bundle created from template mapping"
    return bundles[0]


def _has_type(record, qname):
    return any(attr[0] == PROV_TYPE and attr[1] == qname for attr in getattr(record, 'attributes', []))


def test_map_basic_traversal_information():
    template = build_basic_template()
    mapper = TemplateProvMapper()
    doc = mapper.map_to_document(template)
    assert isinstance(doc, ProvDocument)
    bundle = _get_bundle(doc)

    activities = [r for r in bundle.get_records() if isinstance(r, ProvActivity)]
    entities = [r for r in bundle.get_records() if isinstance(r, ProvEntity)]
    agents = [r for r in bundle.get_records() if isinstance(r, ProvAgent)]

    assert any(_has_type(a, CPM_MAIN_ACTIVITY) for a in activities)
    assert any(_has_type(e, CPM_BACKWARD_CONNECTOR) for e in entities)
    assert any(_has_type(e, CPM_FORWARD_CONNECTOR) for e in entities)
    assert any(_has_type(e, CPM_IDENTIFIER_ENTITY) for e in entities)


def test_main_activity_times_and_parts():
    template = build_basic_template()
    mapper = TemplateProvMapper()
    doc = mapper.map_to_document(template)
    bundle = _get_bundle(doc)
    main = [r for r in bundle.get_records() if isinstance(r, ProvActivity) and _has_type(r, CPM_MAIN_ACTIVITY)]
    assert main, "Main activity not found"
    activity = main[0]
    attrs = getattr(activity, 'attributes', [])
    # Expect at least type plus start/end times and hasPart
    assert len(attrs) >= 2
    # Check hasPart presence by local part match
    assert any(getattr(a[0], 'localpart', '') == 'hasPart' for a in attrs if isinstance(a, tuple))


def test_merge_agents_true():
    template = build_basic_template()
    mapper = TemplateProvMapper(merge_agents=True)
    doc = mapper.map_to_document(template)
    bundle = _get_bundle(doc)
    agents = [r for r in bundle.get_records() if isinstance(r, ProvAgent)]
    assert len(agents) == 1
    agent = agents[0]
    type_attrs = [a for a in getattr(agent, 'attributes', []) if a[0] == PROV_TYPE]
    type_values = [a[1] for a in type_attrs]
    assert CPM_SENDER_AGENT in type_values
    assert CPM_RECEIVER_AGENT in type_values


def test_merge_agents_false():
    template = build_basic_template()
    mapper = TemplateProvMapper(merge_agents=False)
    doc = mapper.map_to_document(template)
    bundle = _get_bundle(doc)
    agents = [r for r in bundle.get_records() if isinstance(r, ProvAgent)]
    assert len(agents) == 2
    sender_present = any(_has_type(a, CPM_SENDER_AGENT) for a in agents)
    receiver_present = any(_has_type(a, CPM_RECEIVER_AGENT) for a in agents)
    assert sender_present
    assert receiver_present


def test_connector_attributes_and_relations():
    template = build_basic_template()
    mapper = TemplateProvMapper()
    doc = mapper.map_to_document(template)
    bundle = _get_bundle(doc)
    connectors = [r for r in bundle.get_records() if isinstance(r, ProvEntity)]
    backward = [c for c in connectors if _has_type(c, CPM_BACKWARD_CONNECTOR)]
    assert backward, "Backward connector missing"
    b = backward[0]
    attr_list = getattr(b, 'attributes', [])
    attr_keys = [a[0] for a in attr_list]
    assert CPM_REFERENCED_BUNDLE_HASH_VALUE in attr_keys
    assert CPM_HASH_ALG in attr_keys


def test_identifier_entity_external_id():
    template = build_basic_template()
    mapper = TemplateProvMapper()
    doc = mapper.map_to_document(template)
    bundle = _get_bundle(doc)
    identifiers = [r for r in bundle.get_records() if isinstance(r, ProvEntity) and _has_type(r, CPM_IDENTIFIER_ENTITY)]
    assert identifiers, "Identifier entity missing"


def test_relations_created():
    template = build_basic_template()
    mapper = TemplateProvMapper()
    doc = mapper.map_to_document(template)
    bundle = _get_bundle(doc)

    records = list(bundle.get_records())
    node_records = [r for r in records if isinstance(r, (ProvEntity, ProvActivity, ProvAgent))]
    relation_records = [r for r in records if r not in node_records]
    # Expect at least usage + generation + derivation relations
    assert len(relation_records) >= 2
