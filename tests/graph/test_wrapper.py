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


# ═══════════════════════════════════════════════════════════════════════════════
# Additional coverage tests – relation types, helpers, subgraph, to_prov_document.
# ═══════════════════════════════════════════════════════════════════════════════

from prov.identifier import Namespace

EX = Namespace("ex", "http://example.org/")


def _make_doc_with_relations():
    """Build a ProvDocument exercising many relation types."""
    doc = ProvDocument()
    doc.add_namespace(EX)
    b = doc.bundle(EX["bundle"])

    # Nodes
    b.entity(EX["e1"])
    b.entity(EX["e2"])
    b.activity(EX["a1"])
    b.agent(EX["ag1"])

    # Relations
    b.usage(EX["a1"], EX["e1"])                      # ProvUsage
    b.wasGeneratedBy(EX["e2"], EX["a1"])              # ProvGeneration
    b.wasDerivedFrom(EX["e2"], EX["e1"])              # ProvDerivation
    b.wasAttributedTo(EX["e1"], EX["ag1"])            # ProvAttribution
    b.wasAssociatedWith(EX["a1"], EX["ag1"])          # ProvAssociation
    b.actedOnBehalfOf(EX["ag1"], EX["ag1"])           # ProvDelegation (self)
    b.wasInformedBy(EX["a1"], EX["a1"])               # ProvCommunication (self)
    b.wasInfluencedBy(EX["e1"], EX["e2"])             # ProvInfluence
    b.specializationOf(EX["e1"], EX["e2"])            # ProvSpecialization
    b.alternateOf(EX["e1"], EX["e2"])                 # ProvAlternate
    return doc


# ─── Import / edge creation ─────────────────────────────────────────────────

class TestRelationEdgeCreation:
    def test_usage_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        edges = w.get_edges()
        kinds = [e.kind for e in edges]
        assert "PROV_USAGE" in kinds

    def test_generation_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in edges] if (edges := w.get_edges()) else []
        assert "PROV_GENERATION" in kinds

    def test_derivation_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in w.get_edges()]
        assert "PROV_DERIVATION" in kinds

    def test_attribution_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in w.get_edges()]
        assert "PROV_ATTRIBUTION" in kinds

    def test_association_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in w.get_edges()]
        assert "PROV_ASSOCIATION" in kinds

    def test_delegation_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in w.get_edges()]
        assert "PROV_DELEGATION" in kinds

    def test_communication_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in w.get_edges()]
        assert "PROV_COMMUNICATION" in kinds

    def test_influence_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in w.get_edges()]
        assert "PROV_INFLUENCE" in kinds

    def test_specialization_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in w.get_edges()]
        assert "PROV_SPECIALIZATION" in kinds

    def test_alternate_edge(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        kinds = [e.kind for e in w.get_edges()]
        assert "PROV_ALTERNATE" in kinds


# ─── Node / edge accessors ──────────────────────────────────────────────────

class TestAccessors:
    def test_get_node_by_id(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        node = w.get_node_by_id(str(EX["e1"]))
        assert node is not None

    def test_get_node_by_id_missing(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        assert w.get_node_by_id("nonexistent") is None

    def test_get_edge_by_id(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        edges = w.get_edges()
        if edges:
            edge = w.get_edge_by_id(edges[0].identifier if hasattr(edges[0], 'identifier') else str(edges[0].identifier))

    def test_get_networkx_graph(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        g = w.get_networkx_graph()
        assert g is not None
        assert g.number_of_nodes() > 0

    def test_get_neighbors(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        n = w.get_neighbors(str(EX["e1"]))
        assert isinstance(n, list)

    def test_get_neighbors_missing(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        assert w.get_neighbors("nonexistent") == []

    def test_get_predecessors(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        p = w.get_predecessors(str(EX["e2"]))
        assert isinstance(p, list)

    def test_get_predecessors_missing(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        assert w.get_predecessors("nonexistent") == []

    def test_get_successors(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        s = w.get_successors(str(EX["e1"]))
        assert isinstance(s, list)

    def test_get_successors_missing(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        assert w.get_successors("nonexistent") == []


# ─── Subgraph (extended) ────────────────────────────────────────────────────

class TestCreateSubgraphExtended:
    def test_subgraph_filter(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        sub = w.create_subgraph(lambda n: "e1" in str(n.identifier))
        assert isinstance(sub, ProvGraphWrapper)
        assert len(sub.get_nodes()) >= 1

    def test_subgraph_empty(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        sub = w.create_subgraph(lambda n: False)
        assert len(sub.get_nodes()) == 0


# ─── to_prov_document ───────────────────────────────────────────────────────

class TestToProvDocument:
    def test_returns_prov_document(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        doc = w.to_prov_document()
        assert isinstance(doc, ProvDocument)

    def test_empty_wrapper(self):
        w = ProvGraphWrapper(ProvDocument())
        doc = w.to_prov_document()
        assert isinstance(doc, ProvDocument)

    def test_no_bundles(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        w = ProvGraphWrapper(doc)
        out = w.to_prov_document()
        assert isinstance(out, ProvDocument)


# ─── Misc ────────────────────────────────────────────────────────────────────

class TestWrapperMisc:
    def test_clear(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        w.clear()
        assert len(w.get_nodes()) == 0
        assert len(w.get_edges()) == 0

    def test_len(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        assert len(w) > 0

    def test_str(self):
        w = ProvGraphWrapper(_make_doc_with_relations())
        s = str(w)
        assert "ProvGraphWrapper" in s

    def test_empty_wrapper(self):
        w = ProvGraphWrapper()
        assert len(w) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Extra tests – placeholder nodes, bundles, subgraph, accessors for missing IDs
# ═══════════════════════════════════════════════════════════════════════════════


class TestWrapperPlaceholderNode:
    def test_relation_referencing_external_entity_creates_placeholder(self):
        """When a relation references an identifier not declared in the doc,
        _get_or_create_node creates a placeholder."""
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        doc.wasInfluencedBy(EX["e1"], EX["e2"])
        w = ProvGraphWrapper(doc)
        node = w.get_node_by_id(str(EX["e2"]))
        assert node is not None


class TestWrapperToProvDocumentBundles:
    def test_to_prov_document_with_bundle(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        bundle = doc.bundle(EX["b1"])
        bundle.entity(EX["e1"])
        bundle.activity(EX["a1"])
        bundle.usage(EX["a1"], EX["e1"])
        w = ProvGraphWrapper(doc)
        result = w.to_prov_document()
        assert result is not None
        bundles = list(result.bundles)
        assert len(bundles) >= 1

    def test_to_prov_document_without_bundle(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        doc.entity(EX["e2"])
        doc.wasInfluencedBy(EX["e1"], EX["e2"])
        w = ProvGraphWrapper(doc)
        result = w.to_prov_document()
        assert result is not None


class TestWrapperCreateSubgraphExtra:
    def test_subgraph_filters_nodes(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        doc.entity(EX["e2"])
        doc.entity(EX["e3"])
        doc.wasInfluencedBy(EX["e1"], EX["e2"])
        doc.wasInfluencedBy(EX["e2"], EX["e3"])
        w = ProvGraphWrapper(doc)
        sub = w.create_subgraph(lambda n: str(n.identifier) in [str(EX["e1"]), str(EX["e2"])])
        assert len(sub.get_nodes()) == 2
        assert len(sub.get_edges()) <= 1

    def test_subgraph_empty_filter(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        w = ProvGraphWrapper(doc)
        sub = w.create_subgraph(lambda n: False)
        assert len(sub.get_nodes()) == 0


class TestWrapperAccessorsExtra:
    def test_get_neighbors_missing(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        w = ProvGraphWrapper(doc)
        assert w.get_neighbors("missing") == []

    def test_get_predecessors_missing(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        w = ProvGraphWrapper(doc)
        assert w.get_predecessors("missing") == []

    def test_get_successors_missing(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        w = ProvGraphWrapper(doc)
        assert w.get_successors("missing") == []
