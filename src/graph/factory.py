"""
CPM Factory Implementation

Provides factory methods for creating CPM nodes and edges with proper isolation and cloning.
"""

import logging
from typing import List, Optional, Dict, Any, Union, Set
from abc import ABC, abstractmethod
from prov.model import ProvDocument, ProvBundle, ProvRecord, ProvRelation, ProvEntity, ProvActivity, ProvAgent
from prov.identifier import QualifiedName
import copy

from src.cpm.namespaces import (
    CPM_NAMESPACE_URI,
    EXAMPLE_NAMESPACE_PREFIX,
    EXAMPLE_NAMESPACE_URI,
    PROV_NAMESPACE_URI,
    ensure_namespace,
)
from .node import GraphNode, DividedGraphNode, MergedGraphNode
from .edge import GraphEdge, DividedGraphEdge, MergedGraphEdge
from .wrapper import ProvGraphWrapper


LOGGER = logging.getLogger(__name__)


class ICpmFactory(ABC):
    """
    Abstract factory interface for creating CPM nodes and edges.
    """

    @abstractmethod
    def create_node(self, elements: List[ProvRecord],
                    identifier: Optional[QualifiedName] = None) -> GraphNode:
        pass

    @abstractmethod
    def create_edge(self, relations: List[ProvRelation], cause: GraphNode,
                    effect: GraphNode, identifier: Optional[QualifiedName] = None) -> GraphEdge:
        pass

    @abstractmethod
    def clone_node(self, node: GraphNode, include_edges: bool = False) -> GraphNode:
        pass

    @abstractmethod
    def clone_edge(self, edge: GraphEdge, node_mapping: Optional[Dict[GraphNode, GraphNode]] = None) -> GraphEdge:
        pass

    @abstractmethod
    def get_factory_type(self) -> str:
        pass


class DividedCpmFactory(ICpmFactory):
    """
    Factory for creating divided nodes and edges.
    """

    def create_node(self, elements: List[ProvRecord],
                    identifier: Optional[QualifiedName] = None) -> DividedGraphNode:
        if not elements:
            raise ValueError("At least one element is required to create a node")

        # Clone elements to ensure isolation
        cloned_elements = [copy.deepcopy(element) for element in elements]
        return DividedGraphNode(cloned_elements, identifier)

    def create_edge(self, relations: List[ProvRelation], cause: GraphNode,
                    effect: GraphNode, identifier: Optional[QualifiedName] = None) -> DividedGraphEdge:
        if not relations:
            raise ValueError("At least one relation is required to create an edge")

        # Clone relations to ensure isolation
        cloned_relations = [copy.deepcopy(relation) for relation in relations]
        return DividedGraphEdge(cloned_relations, cause, effect, identifier)

    def clone_node(self, node: GraphNode, include_edges: bool = False) -> DividedGraphNode:
        cloned_elements = [copy.deepcopy(elem) for elem in node.elements]
        cloned_node = DividedGraphNode(cloned_elements, node.identifier)

        if include_edges:
            # Clone edge references (but not the edges themselves)
            for edge in node.cause_edges:
                cloned_node.add_cause_edge(edge)
            for edge in node.effect_edges:
                cloned_node.add_effect_edge(edge)

        return cloned_node

    def clone_edge(self, edge: GraphEdge, node_mapping: Optional[Dict[GraphNode, GraphNode]] = None) -> DividedGraphEdge:
        cloned_relations = [copy.deepcopy(rel) for rel in edge.relations]

        # Use node mapping if provided, otherwise use original nodes
        cause = node_mapping.get(edge.cause, edge.cause) if node_mapping else edge.cause
        effect = node_mapping.get(edge.effect, edge.effect) if node_mapping else edge.effect

        return DividedGraphEdge(cloned_relations, cause, effect, edge.identifier)

    def get_factory_type(self) -> str:
        return "DIVIDED"


class MergedCpmFactory(ICpmFactory):
    """
    Factory for creating merged nodes and edges.
    """

    def create_node(self, elements: List[ProvRecord],
                    identifier: Optional[QualifiedName] = None) -> MergedGraphNode:
        if not elements:
            raise ValueError("At least one element is required to create a node")

        # Use only the first element and clone for isolation
        cloned_element = copy.deepcopy(elements[0])
        return MergedGraphNode(cloned_element, identifier)

    def create_edge(self, relations: List[ProvRelation], cause: GraphNode,
                    effect: GraphNode, identifier: Optional[QualifiedName] = None) -> MergedGraphEdge:
        if not relations:
            raise ValueError("At least one relation is required to create an edge")

        # Use only the first relation and clone for isolation
        cloned_relation = copy.deepcopy(relations[0])
        return MergedGraphEdge(cloned_relation, cause, effect, identifier)

    def clone_node(self, node: GraphNode, include_edges: bool = False) -> MergedGraphNode:
        cloned_element = copy.deepcopy(node.any_element)
        cloned_node = MergedGraphNode(cloned_element, node.identifier)

        if include_edges:
            # Clone edge references (but not the edges themselves)
            for edge in node.cause_edges:
                cloned_node.add_cause_edge(edge)
            for edge in node.effect_edges:
                cloned_node.add_effect_edge(edge)

        return cloned_node

    def clone_edge(self, edge: GraphEdge, node_mapping: Optional[Dict[GraphNode, GraphNode]] = None) -> MergedGraphEdge:
        # Get any relation - use first relation or prov_relation
        any_relation = edge.relations[0] if edge.relations else edge.prov_relation

        # MergedGraphEdge requires ProvRelation, so check the type
        if isinstance(any_relation, ProvRelation):
            cloned_relation = copy.deepcopy(any_relation)
        else:
            # For ProvActivity, we need to handle this case - skip or convert
            raise ValueError(f"Cannot create MergedGraphEdge with {type(any_relation).__name__}")

        # Use node mapping if provided, otherwise use original nodes
        cause = node_mapping.get(edge.cause, edge.cause) if node_mapping else edge.cause
        effect = node_mapping.get(edge.effect, edge.effect) if node_mapping else edge.effect

        return MergedGraphEdge(cloned_relation, cause, effect, edge.identifier)

    def get_factory_type(self) -> str:
        return "MERGED"


class CpmFactoryManager:
    """
    Manager for CPM factories with automatic factory selection and graph operations.
    Provides advanced factory functionality.
    """

    def __init__(self, default_factory_type: str = "DIVIDED"):
        self._factories = {
            "DIVIDED": DividedCpmFactory(),
            "MERGED": MergedCpmFactory()
        }
        self._default_factory_type = default_factory_type

    def get_factory(self, factory_type: Optional[str] = None) -> ICpmFactory:
        factory_type = factory_type or self._default_factory_type
        if factory_type not in self._factories:
            raise ValueError(f"Unknown factory type: {factory_type}")
        return self._factories[factory_type]

    def create_node_from_elements(self, elements: List[ProvRecord],
                                  factory_type: Optional[str] = None,
                                  identifier: Optional[QualifiedName] = None) -> GraphNode:
        factory = self.get_factory(factory_type)
        return factory.create_node(elements, identifier)

    def create_edge_from_relations(self, relations: List[ProvRelation],
                                   cause: GraphNode, effect: GraphNode,
                                   factory_type: Optional[str] = None,
                                   identifier: Optional[QualifiedName] = None) -> GraphEdge:
        factory = self.get_factory(factory_type)
        return factory.create_edge(relations, cause, effect, identifier)

    def clone_graph(self, wrapper: ProvGraphWrapper,
                    factory_type: Optional[str] = None) -> ProvGraphWrapper:
        factory = self.get_factory(factory_type)

        # Clone all nodes first
        node_mapping = {}
        cloned_nodes = []

        for original_node in wrapper.get_nodes():
            cloned_node = factory.clone_node(original_node, include_edges=False)
            node_mapping[original_node] = cloned_node
            cloned_nodes.append(cloned_node)

        # Clone all edges with node mapping
        cloned_edges = []
        for original_edge in wrapper.get_edges():
            cloned_edge = factory.clone_edge(original_edge, node_mapping)
            cloned_edges.append(cloned_edge)

        # Create new PROV document from cloned elements
        cloned_doc = self._create_document_from_elements(cloned_nodes, cloned_edges)
        return ProvGraphWrapper(cloned_doc)

    def merge_graphs(self, wrappers: List[ProvGraphWrapper],
                     factory_type: Optional[str] = None) -> ProvGraphWrapper:
        if not wrappers:
            return ProvGraphWrapper(ProvDocument())

        factory = self.get_factory(factory_type)

        # Collect all nodes and edges
        all_nodes = []
        all_edges = []
        node_id_mapping = {}

        for wrapper in wrappers:
            for node in wrapper.get_nodes():
                # Check for duplicate identifiers
                if node.identifier in node_id_mapping:
                    # Handle duplicate by merging or creating new identifier
                    existing_node = node_id_mapping[node.identifier]
                    if hasattr(existing_node, 'handle_duplicate'):
                        for element in node.elements:
                            existing_node.handle_duplicate(element)
                else:
                    cloned_node = factory.clone_node(node, include_edges=False)
                    all_nodes.append(cloned_node)
                    node_id_mapping[node.identifier] = cloned_node

            for edge in wrapper.get_edges():
                # Map edge endpoints to merged nodes
                cause = node_id_mapping.get(edge.cause.identifier)
                effect = node_id_mapping.get(edge.effect.identifier)

                if cause and effect:
                    cloned_edge = factory.clone_edge(edge, {
                        edge.cause: cause,
                        edge.effect: effect
                    })
                    all_edges.append(cloned_edge)

        # Create new PROV document from merged elements
        merged_doc = self._create_document_from_elements(all_nodes, all_edges)
        return ProvGraphWrapper(merged_doc)

    def create_subgraph(self, wrapper: ProvGraphWrapper,
                        node_filter: callable,
                        factory_type: Optional[str] = None) -> ProvGraphWrapper:
        factory = self.get_factory(factory_type)

        # Filter nodes
        filtered_nodes = [node for node in wrapper.get_nodes() if node_filter(node)]
        filtered_node_set = set(filtered_nodes)

        # Clone filtered nodes
        node_mapping = {}
        cloned_nodes = []

        for node in filtered_nodes:
            cloned_node = factory.clone_node(node, include_edges=False)
            node_mapping[node] = cloned_node
            cloned_nodes.append(cloned_node)

        # Filter and clone edges that connect filtered nodes
        cloned_edges = []
        for edge in wrapper.get_edges():
            if (edge.cause in filtered_node_set and
                    edge.effect in filtered_node_set):
                cloned_edge = factory.clone_edge(edge, node_mapping)
                cloned_edges.append(cloned_edge)

        # Create new PROV document from subgraph elements
        subgraph_doc = self._create_document_from_elements(cloned_nodes, cloned_edges)
        return ProvGraphWrapper(subgraph_doc)

    def _create_document_from_elements(self, nodes: List[GraphNode],
                                       edges: List[GraphEdge]) -> ProvDocument:
        """
        Create a ProvDocument from a collection of nodes and edges.
        Properly reconstructs PROV elements and relations with namespaces.
        """
        doc = ProvDocument()

        self._add_element_namespaces(doc, nodes)
        self._ensure_default_namespaces(doc)

        bundle = self._create_bundle(doc)
        self._add_nodes_to_bundle(bundle, nodes)
        self._add_edges_to_bundle(bundle, edges)

        return doc

    def _add_element_namespaces(self, doc: ProvDocument, nodes: List[GraphNode]) -> None:
        """Copy namespaces referenced by node identifiers into a new document."""
        namespaces = set()
        for node in nodes:
            for element in node.elements:
                identifier = getattr(element, 'identifier', None)
                namespace = getattr(identifier, 'namespace', None)
                if not namespace:
                    continue

                namespace_key = (namespace.prefix, str(namespace.uri))
                if namespace_key in namespaces:
                    continue

                namespaces.add(namespace_key)
                doc.add_namespace(namespace.prefix, str(namespace.uri))

    def _ensure_default_namespaces(self, doc: ProvDocument) -> None:
        """Ensure the reconstructed document includes the core CPM namespaces."""
        ensure_namespace(doc, 'prov', PROV_NAMESPACE_URI)
        ensure_namespace(doc, 'cpm', CPM_NAMESPACE_URI)
        ensure_namespace(doc, EXAMPLE_NAMESPACE_PREFIX, EXAMPLE_NAMESPACE_URI)

    def _create_bundle(self, doc: ProvDocument):
        """Create a stable bundle identifier for reconstructed documents."""
        bundle_ns = ensure_namespace(doc, EXAMPLE_NAMESPACE_PREFIX, EXAMPLE_NAMESPACE_URI)
        return doc.bundle(bundle_ns['bundle'])

    def _add_nodes_to_bundle(self, bundle, nodes: List[GraphNode]) -> None:
        """Add reconstructed node records to the output bundle."""
        added_elements = set()
        for node in nodes:
            for element in node.elements:
                elem_id = element.identifier if hasattr(element, 'identifier') else None
                if elem_id and elem_id in added_elements:
                    continue

                attrs = list(element.attributes) if hasattr(element, 'attributes') else []

                if isinstance(element, ProvEntity):
                    bundle.entity(elem_id, other_attributes=attrs)
                elif isinstance(element, ProvActivity):
                    bundle.activity(elem_id, other_attributes=attrs)
                elif isinstance(element, ProvAgent):
                    bundle.agent(elem_id, other_attributes=attrs)

                if elem_id:
                    added_elements.add(elem_id)

    def _add_edges_to_bundle(self, bundle, edges: List[GraphEdge]) -> None:
        """Add reconstructed relation records to the output bundle."""
        added_relations = set()
        for edge in edges:
            for relation in edge.relations:
                rel_id = relation.identifier if hasattr(relation, 'identifier') else None
                if rel_id and rel_id in added_relations:
                    continue

                self._add_relation_to_bundle(bundle, relation, rel_id)

                if rel_id:
                    added_relations.add(rel_id)

    def _add_relation_to_bundle(self, bundle, relation: ProvRelation, rel_id: Optional[QualifiedName]) -> None:
        """Add a single relation record to the reconstructed bundle."""
        formal_attrs = list(relation.formal_attributes) if hasattr(relation, 'formal_attributes') else []
        other_attrs = list(relation.extra_attributes) if hasattr(relation, 'extra_attributes') else []
        relation_type = type(relation).__name__

        try:
            if 'Usage' in relation_type and len(formal_attrs) >= 2:
                activity_id = formal_attrs[0][1]
                entity_id = formal_attrs[1][1]
                bundle.usage(activity_id, entity_id, identifier=rel_id, other_attributes=other_attrs)

            elif 'Generation' in relation_type and len(formal_attrs) >= 2:
                entity_id = formal_attrs[0][1]
                activity_id = formal_attrs[1][1]
                bundle.generation(entity_id, activity_id, identifier=rel_id, other_attributes=other_attrs)

            elif 'Derivation' in relation_type and len(formal_attrs) >= 2:
                generated_id = formal_attrs[0][1]
                used_id = formal_attrs[1][1]
                bundle.derivation(generated_id, used_id, identifier=rel_id, other_attributes=other_attrs)

            elif 'Attribution' in relation_type and len(formal_attrs) >= 2:
                entity_id = formal_attrs[0][1]
                agent_id = formal_attrs[1][1]
                bundle.attribution(entity_id, agent_id, identifier=rel_id, other_attributes=other_attrs)

            elif 'Association' in relation_type and len(formal_attrs) >= 2:
                activity_id = formal_attrs[0][1]
                agent_id = formal_attrs[1][1]
                bundle.association(activity_id, agent_id, identifier=rel_id, other_attributes=other_attrs)

            elif 'Communication' in relation_type and len(formal_attrs) >= 2:
                informed_id = formal_attrs[0][1]
                informant_id = formal_attrs[1][1]
                bundle.communication(informed_id, informant_id, identifier=rel_id, other_attributes=other_attrs)

            elif 'Delegation' in relation_type and len(formal_attrs) >= 2:
                delegate_id = formal_attrs[0][1]
                responsible_id = formal_attrs[1][1]
                bundle.delegation(delegate_id, responsible_id, identifier=rel_id, other_attributes=other_attrs)

            elif 'Influence' in relation_type and len(formal_attrs) >= 2:
                influencee_id = formal_attrs[0][1]
                influencer_id = formal_attrs[1][1]
                bundle.influence(influencee_id, influencer_id, identifier=rel_id, other_attributes=other_attrs)

            elif 'Specialization' in relation_type and len(formal_attrs) >= 2:
                specific_id = formal_attrs[0][1]
                general_id = formal_attrs[1][1]
                bundle.specialization(specific_id, general_id)

            elif 'Alternate' in relation_type and len(formal_attrs) >= 2:
                alt1_id = formal_attrs[0][1]
                alt2_id = formal_attrs[1][1]
                bundle.alternate(alt1_id, alt2_id)

            elif 'Membership' in relation_type and len(formal_attrs) >= 2:
                collection_id = formal_attrs[0][1]
                entity_id = formal_attrs[1][1]
                bundle.membership(collection_id, entity_id)

        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            LOGGER.warning("Skipping relation %s during document reconstruction: %s", relation_type, exc)

    def get_available_factory_types(self) -> List[str]:
        return list(self._factories.keys())

    def register_factory(self, factory_type: str, factory: ICpmFactory):
        self._factories[factory_type] = factory

    def set_default_factory_type(self, factory_type: str):
        if factory_type not in self._factories:
            raise ValueError(f"Unknown factory type: {factory_type}")
        self._default_factory_type = factory_type


# Global factory manager instance
_factory_manager = CpmFactoryManager()


def get_factory_manager() -> CpmFactoryManager:
    return _factory_manager


def create_node(elements: List[ProvRecord], factory_type: str = "DIVIDED",
                identifier: Optional[QualifiedName] = None) -> GraphNode:
    return _factory_manager.create_node_from_elements(elements, factory_type, identifier)


def create_edge(relations: List[ProvRelation], cause: GraphNode, effect: GraphNode,
                factory_type: str = "DIVIDED",
                identifier: Optional[QualifiedName] = None) -> GraphEdge:
    return _factory_manager.create_edge_from_relations(relations, cause, effect, factory_type, identifier)


def clone_graph(wrapper: ProvGraphWrapper, factory_type: str = "DIVIDED") -> ProvGraphWrapper:
    return _factory_manager.clone_graph(wrapper, factory_type)


def merge_graphs(wrappers: List[ProvGraphWrapper], factory_type: str = "DIVIDED") -> ProvGraphWrapper:
    return _factory_manager.merge_graphs(wrappers, factory_type)
