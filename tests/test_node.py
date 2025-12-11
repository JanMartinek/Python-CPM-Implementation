import pytest
from src.graph.node import GraphNode
from prov.model import ProvEntity, ProvDocument
from prov.identifier import QualifiedName


def test_node_creation():
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    entity = doc.entity('ex:entity_id')
    node = GraphNode(entity)

    assert node.prov_entity == entity
    assert node.identifier is not None
    assert node.kind == "PROV_ENTITY"


def test_node_edge_management():
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    entity = doc.entity('ex:entity_id')
    node = GraphNode(entity)

    assert len(node.cause_edges) == 0
    assert len(node.effect_edges) == 0
    assert len(node.all_edges) == 0
    assert node.is_isolated() == True


def test_node_prov_attributes():
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    entity = doc.entity('ex:entity_id', {'ex:type': 'test_entity', 'ex:value': 42})
    node = GraphNode(entity)

    type_values = node.get_prov_attribute('ex:type')
    assert 'test_entity' in type_values or len(type_values) > 0

    elements = node.elements
    assert len(elements) == 1
    assert elements[0] == entity


def test_node_degree_calculations():
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    entity = doc.entity('ex:entity_id')
    node = GraphNode(entity)

    assert node.degree == 0
    assert node.in_degree == 0
    assert node.out_degree == 0
    assert node.is_isolated() == True


def test_node_clone():
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    entity = doc.entity('ex:entity_id', {'ex:attr': 'value'})
    node = GraphNode(entity)

    cloned_node = node.clone()

    assert cloned_node is not node
    assert cloned_node.identifier == node.identifier
    assert cloned_node.kind == node.kind
    assert len(cloned_node.all_edges) == 0


def test_node_with_activity():
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    activity = doc.activity('ex:activity_id')
    node = GraphNode(activity)

    assert node.prov_entity == activity
    assert node.kind == "PROV_ACTIVITY"


def test_node_identifier_override():
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    entity = doc.entity('ex:entity_id')
    custom_id = doc.valid_qualified_name('ex:custom_id')
    node = GraphNode(entity, custom_id)

    assert node.identifier == custom_id
