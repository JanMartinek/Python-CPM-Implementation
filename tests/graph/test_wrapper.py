"""
Tests for ProvGraphWrapper class
"""

import pytest
from prov.model import ProvDocument

from src.graph.wrapper import ProvGraphWrapper
from src.graph.node import GraphNode
from src.graph.edge import GraphEdge


class TestProvGraphWrapper:
    """Test ProvGraphWrapper functionality"""

    def test_wrapper_creation_empty(self):
        """Test creating an empty wrapper"""
        wrapper = ProvGraphWrapper()

        assert wrapper.graph is not None
        assert len(wrapper.get_nodes()) == 0
        assert len(wrapper.get_edges()) == 0

    def test_wrapper_creation_with_document(self):
        """Test creating wrapper from PROV document"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        doc.usage(activity, entity1)
        doc.generation(entity2, activity)

        wrapper = ProvGraphWrapper(doc)

        nodes = wrapper.get_nodes()
        edges = wrapper.get_edges()

        assert len(nodes) >= 2  # At least the entities
        assert len(edges) >= 2  # Usage and generation

    def test_add_entity_as_node(self):
        """Test adding an entity as a node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        wrapper = ProvGraphWrapper()
        node = wrapper.add_entity_as_node(entity)

        assert isinstance(node, GraphNode)
        assert node.kind == "PROV_ENTITY"
        assert len(wrapper.get_nodes()) == 1

    def test_add_activity_as_node(self):
        """Test adding an activity as a node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        activity = doc.activity('ex:activity1')

        wrapper = ProvGraphWrapper()
        node = wrapper.add_activity_as_node(activity)

        assert isinstance(node, GraphNode)
        assert node.kind == "PROV_ACTIVITY"
        assert len(wrapper.get_nodes()) == 1

    def test_add_agent_as_node(self):
        """Test adding an agent as a node"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        agent = doc.agent('ex:agent1')

        wrapper = ProvGraphWrapper()
        node = wrapper.add_agent_as_node(agent)

        assert isinstance(node, GraphNode)
        assert node.kind == "PROV_AGENT"
        assert len(wrapper.get_nodes()) == 1

    def test_add_relation_as_edge(self):
        """Test adding a relation as an edge"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        wrapper = ProvGraphWrapper()

        node1 = wrapper.add_entity_as_node(entity1)
        node2 = wrapper.add_entity_as_node(entity2)
        node3 = wrapper.add_activity_as_node(activity)

        usage = doc.usage(activity, entity1)
        edge = wrapper.add_relation_as_edge(usage)

        assert edge is not None
        assert isinstance(edge, GraphEdge)
        assert len(wrapper.get_edges()) == 1

    def test_get_nodes(self):
        """Test getting all nodes"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        wrapper = ProvGraphWrapper()
        wrapper.add_entity_as_node(entity1)
        wrapper.add_entity_as_node(entity2)
        wrapper.add_activity_as_node(activity)

        nodes = wrapper.get_nodes()
        assert len(nodes) == 3

    def test_get_edges(self):
        """Test getting all edges"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        wrapper = ProvGraphWrapper()
        wrapper.add_entity_as_node(entity1)
        wrapper.add_entity_as_node(entity2)
        wrapper.add_activity_as_node(activity)

        usage = doc.usage(activity, entity1)
        generation = doc.generation(entity2, activity)

        wrapper.add_relation_as_edge(usage)
        wrapper.add_relation_as_edge(generation)

        edges = wrapper.get_edges()
        assert len(edges) == 2

    def test_networkx_integration(self):
        """Test NetworkX graph integration"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        wrapper = ProvGraphWrapper()
        wrapper.add_entity_as_node(entity1)
        wrapper.add_entity_as_node(entity2)

        # Verify NetworkX graph exists
        assert wrapper.graph is not None
        assert len(wrapper.graph.nodes()) >= 2

    def test_duplicate_entity_handling(self):
        """Test that duplicate entities are not added twice"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        wrapper = ProvGraphWrapper()
        node1 = wrapper.add_entity_as_node(entity)
        node2 = wrapper.add_entity_as_node(entity)

        assert node1 == node2
        assert len(wrapper.get_nodes()) == 1

    def test_clear_graph(self):
        """Test clearing the graph"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        wrapper = ProvGraphWrapper()
        wrapper.add_entity_as_node(entity1)
        wrapper.add_entity_as_node(entity2)

        assert len(wrapper.get_nodes()) == 2

        # Clear by creating new wrapper
        wrapper._nodes.clear()
        wrapper._edges.clear()
        wrapper.graph.clear()

        assert len(wrapper.get_nodes()) == 0

    def test_import_from_bundle(self):
        """Test importing from PROV bundle"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        bundle = doc.bundle('ex:bundle1')
        entity1 = bundle.entity('ex:entity1')
        entity2 = bundle.entity('ex:entity2')
        bundle.derivation(entity2, entity1)

        wrapper = ProvGraphWrapper(doc)

        nodes = wrapper.get_nodes()
        edges = wrapper.get_edges()

        # Should have imported entities from bundle
        assert len(nodes) >= 2
        assert len(edges) >= 1

    def test_complex_provenance_graph(self):
        """Test creating a complex provenance graph"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        # Create entities
        input1 = doc.entity('ex:input1')
        input2 = doc.entity('ex:input2')
        output = doc.entity('ex:output')

        # Create activity
        activity = doc.activity('ex:process')

        # Create agent
        agent = doc.agent('ex:agent')

        # Create relations
        doc.usage(activity, input1)
        doc.usage(activity, input2)
        doc.generation(output, activity)
        doc.association(activity, agent)
        doc.attribution(output, agent)

        wrapper = ProvGraphWrapper(doc)

        nodes = wrapper.get_nodes()
        edges = wrapper.get_edges()

        # Should have 4 nodes (2 inputs, 1 output, 1 activity, 1 agent)
        assert len(nodes) >= 4
        # Should have 5 edges (2 usage, 1 generation, 1 association, 1 attribution)
        assert len(edges) >= 5

    def test_get_node_by_identifier(self):
        """Test retrieving a node by its identifier"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        entity = doc.entity('ex:entity1')

        wrapper = ProvGraphWrapper()
        node = wrapper.add_entity_as_node(entity)

        # Get node from internal storage
        node_id = str(entity.identifier)
        retrieved_node = wrapper._nodes.get(node_id)

        assert retrieved_node is not None
        assert retrieved_node == node

    def test_edge_connectivity(self):
        """Test that edges properly connect nodes"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        wrapper = ProvGraphWrapper()
        node1 = wrapper.add_entity_as_node(entity1)
        node2 = wrapper.add_entity_as_node(entity2)

        derivation = doc.derivation(entity2, entity1)
        edge = wrapper.add_relation_as_edge(derivation)

        assert edge is not None
        assert edge.connects_node(node1) or edge.connects_node(node2)

    def test_multiple_relations_same_nodes(self):
        """Test multiple relations between same nodes"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        wrapper = ProvGraphWrapper()
        node1 = wrapper.add_entity_as_node(entity1)
        node2 = wrapper.add_entity_as_node(entity2)
        node3 = wrapper.add_activity_as_node(activity)

        usage1 = doc.usage(activity, entity1, identifier='ex:usage1')
        usage2 = doc.usage(activity, entity1, identifier='ex:usage2')

        edge1 = wrapper.add_relation_as_edge(usage1)
        edge2 = wrapper.add_relation_as_edge(usage2)

        # Should create two separate edges
        assert edge1 is not None
        assert edge2 is not None
        assert edge1 != edge2


class TestProvGraphWrapperSubgraph:
    """Test ProvGraphWrapper subgraph creation functionality"""

    def test_create_subgraph_with_filter(self):
        """Test creating a subgraph with node filter"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        # Create entities with different types
        dataset1 = doc.entity('ex:dataset1', {'prov:type': 'Dataset'})
        dataset2 = doc.entity('ex:dataset2', {'prov:type': 'Dataset'})
        report = doc.entity('ex:report1', {'prov:type': 'Report'})
        model = doc.entity('ex:model1', {'prov:type': 'Model'})

        activity = doc.activity('ex:activity1')

        # Create relationships
        doc.usage(activity, dataset1)
        doc.generation(dataset2, activity)
        doc.generation(report, activity)
        doc.generation(model, activity)

        wrapper = ProvGraphWrapper(doc)

        # Filter to keep only Dataset and Report types
        def node_filter(node):
            for attr_name, attr_value in node.prov_entity.attributes:
                if str(attr_name) == 'prov:type':
                    return str(attr_value) in ['Dataset', 'Report']
            return False

        subgraph = wrapper.create_subgraph(node_filter)

        # Verify filtered nodes (3 datasets/reports + activity)
        assert len(subgraph) >= 3
        assert len(subgraph) < len(wrapper)

    def test_create_subgraph_preserves_namespaces(self):
        """Test that subgraph preserves namespaces from original"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')
        doc.add_namespace('data', 'http://data.example.org/')

        entity1 = doc.entity('ex:entity1', {'prov:type': 'Dataset'})
        entity2 = doc.entity('data:entity2', {'prov:type': 'Dataset'})

        wrapper = ProvGraphWrapper(doc)

        def keep_all(node):
            return True

        subgraph = wrapper.create_subgraph(keep_all)

        # Check namespaces are preserved
        sub_doc = subgraph._prov_document
        namespace_prefixes = {ns.prefix for ns in sub_doc.namespaces}

        assert 'ex' in namespace_prefixes
        assert 'data' in namespace_prefixes

    def test_create_subgraph_with_edges(self):
        """Test that subgraph includes edges between filtered nodes"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1', {'prov:type': 'Dataset'})
        entity2 = doc.entity('ex:entity2', {'prov:type': 'Dataset'})
        entity3 = doc.entity('ex:entity3', {'prov:type': 'Model'})

        activity = doc.activity('ex:activity1')

        doc.usage(activity, entity1)
        doc.generation(entity2, activity)
        doc.generation(entity3, activity)
        doc.derivation(entity2, entity1)

        wrapper = ProvGraphWrapper(doc)
        original_edges = len(wrapper.get_edges())

        # Filter to keep only Datasets
        def keep_datasets(node):
            for attr_name, attr_value in node.prov_entity.attributes:
                if str(attr_name) == 'prov:type':
                    return str(attr_value) == 'Dataset'
            return True  # Keep nodes without type (like activity)

        subgraph = wrapper.create_subgraph(keep_datasets)

        # Subgraph should have fewer edges than original
        # (edges to Model entity should be excluded)
        assert len(subgraph.get_edges()) < original_edges
        assert len(subgraph.get_edges()) > 0

    def test_create_subgraph_empty_filter(self):
        """Test creating subgraph that filters out everything"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        wrapper = ProvGraphWrapper(doc)

        # Filter that excludes everything
        def exclude_all(node):
            return False

        subgraph = wrapper.create_subgraph(exclude_all)

        assert len(subgraph) == 0
        assert len(subgraph.get_edges()) == 0

    def test_create_subgraph_keeps_all(self):
        """Test creating subgraph that keeps everything"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')
        activity = doc.activity('ex:activity1')

        doc.usage(activity, entity1)
        doc.generation(entity2, activity)

        wrapper = ProvGraphWrapper(doc)

        # Filter that includes everything
        def keep_all(node):
            return True

        subgraph = wrapper.create_subgraph(keep_all)

        assert len(subgraph) == len(wrapper)
        assert len(subgraph.get_edges()) == len(wrapper.get_edges())
