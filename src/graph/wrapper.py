from typing import Dict, List, Optional, Set, Union, Tuple
import networkx as nx
from prov.model import (
    ProvEntity, ProvActivity, ProvAgent, ProvDocument, ProvBundle,
    ProvRelation, ProvGeneration, ProvUsage, ProvCommunication,
    ProvDerivation, ProvAttribution, ProvAssociation, ProvDelegation,
    ProvInfluence, ProvSpecialization, ProvAlternate, ProvMembership,
    ProvStart, ProvEnd, ProvInvalidation
)
from prov.identifier import QualifiedName
from .node import GraphNode
from .edge import GraphEdge


class ProvGraphWrapper:
    """
    A wrapper that represents PROV data as a graph following PROV-DM specification:
    - ProvEntity, ProvActivity, ProvAgent objects become NODES (vertices)
    - All PROV relations (Generation, Usage, Derivation, etc.) become EDGES
    """

    def __init__(self, prov_document: Optional[ProvDocument] = None):
        self.graph = nx.DiGraph()
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        self._prov_document = prov_document or ProvDocument()

        if prov_document:
            self._import_from_prov_document(prov_document)

    def _import_from_prov_document(self, doc: ProvDocument) -> None:
        self._import_records_from_bundle(doc)

        for bundle in doc.bundles:
            self._import_records_from_bundle(bundle)

    def _import_records_from_bundle(self, bundle: Union[ProvDocument, ProvBundle]) -> None:
        # First pass: Create all nodes (entities, activities, agents)
        for record in bundle.get_records(ProvEntity):
            self.add_entity_as_node(record)

        for record in bundle.get_records(ProvAgent):
            self.add_agent_as_node(record)

        for record in bundle.get_records(ProvActivity):
            self.add_activity_as_node(record)

        # Second pass: Create all edges (relations)
        for record in bundle.get_records(ProvRelation):
            self.add_relation_as_edge(record)

    def add_entity_as_node(self, entity: ProvEntity) -> GraphNode:
        node_id = str(entity.identifier) if entity.identifier else f"entity_{len(self._nodes)}"

        if node_id in self._nodes:
            return self._nodes[node_id]

        node = GraphNode(entity, node_id)
        self._nodes[node_id] = node
        self.graph.add_node(node_id, prov_entity=entity, graph_node=node)

        return node

    def add_agent_as_node(self, agent: ProvAgent) -> GraphNode:
        node_id = str(agent.identifier) if agent.identifier else f"agent_{len(self._nodes)}"

        if node_id in self._nodes:
            return self._nodes[node_id]

        node = GraphNode(agent, node_id)
        self._nodes[node_id] = node
        self.graph.add_node(node_id, prov_agent=agent, graph_node=node)

        return node

    def add_activity_as_node(self, activity: ProvActivity) -> GraphNode:
        """Add an activity as a node (vertex) in the graph - per PROV-DM spec."""
        node_id = str(activity.identifier) if activity.identifier else f"activity_{len(self._nodes)}"

        if node_id in self._nodes:
            return self._nodes[node_id]

        node = GraphNode(activity, node_id)
        self._nodes[node_id] = node
        self.graph.add_node(node_id, prov_activity=activity, graph_node=node)

        return node

    def add_relation_as_edge(self, relation: ProvRelation) -> Optional[GraphEdge]:
        """
        Add a PROV relation as an edge in the graph.
        Per PROV-DM spec, all relations are edges connecting nodes.
        """
        edge_id = str(relation.identifier) if relation.identifier else f"relation_{len(self._edges)}"

        # Get the formal attributes to find source and target
        formal_attrs = list(relation.formal_attributes)
        if len(formal_attrs) < 2:
            return None

        source_node = None
        target_node = None

        # Different relation types have different attribute orders
        if isinstance(relation, ProvGeneration):
            # wasGeneratedBy(entity, activity, ...)
            # Edge: activity -> entity (per CPM model extraction logic)
            entity_id = formal_attrs[0][1] if formal_attrs[0] else None
            activity_id = formal_attrs[1][1] if formal_attrs[1] else None
            if activity_id and entity_id:
                source_node = self._get_or_create_node(activity_id)
                target_node = self._get_or_create_node(entity_id)

        elif isinstance(relation, ProvUsage):
            # used(activity, entity, ...)
            # Edge: entity -> activity (entity influences activity)
            activity_id = formal_attrs[0][1] if formal_attrs[0] else None
            entity_id = formal_attrs[1][1] if formal_attrs[1] else None
            if entity_id and activity_id:
                source_node = self._get_or_create_node(entity_id)
                target_node = self._get_or_create_node(activity_id)

        elif isinstance(relation, ProvDerivation):
            # wasDerivedFrom(generated_entity, used_entity, ...)
            # Edge: used_entity -> generated_entity
            generated_id = formal_attrs[0][1] if formal_attrs[0] else None
            used_id = formal_attrs[1][1] if formal_attrs[1] else None
            if used_id and generated_id:
                source_node = self._get_or_create_node(used_id)
                target_node = self._get_or_create_node(generated_id)

        elif isinstance(relation, ProvAttribution):
            # wasAttributedTo(entity, agent, ...)
            # Edge: agent -> entity
            entity_id = formal_attrs[0][1] if formal_attrs[0] else None
            agent_id = formal_attrs[1][1] if formal_attrs[1] else None
            if agent_id and entity_id:
                source_node = self._get_or_create_node(agent_id)
                target_node = self._get_or_create_node(entity_id)

        elif isinstance(relation, ProvAssociation):
            # wasAssociatedWith(activity, agent, ...)
            # Edge: agent -> activity (agent influences activity)
            activity_id = formal_attrs[0][1] if formal_attrs[0] else None
            agent_id = formal_attrs[1][1] if formal_attrs[1] else None
            if agent_id and activity_id:
                source_node = self._get_or_create_node(agent_id)
                target_node = self._get_or_create_node(activity_id)

        elif isinstance(relation, ProvDelegation):
            # actedOnBehalfOf(delegate, responsible, ...)
            # Edge: responsible -> delegate
            delegate_id = formal_attrs[0][1] if formal_attrs[0] else None
            responsible_id = formal_attrs[1][1] if formal_attrs[1] else None
            if responsible_id and delegate_id:
                source_node = self._get_or_create_node(responsible_id)
                target_node = self._get_or_create_node(delegate_id)

        elif isinstance(relation, ProvCommunication):
            # wasInformedBy(informed, informant, ...)
            # Edge: informant -> informed
            informed_id = formal_attrs[0][1] if formal_attrs[0] else None
            informant_id = formal_attrs[1][1] if formal_attrs[1] else None
            if informant_id and informed_id:
                source_node = self._get_or_create_node(informant_id)
                target_node = self._get_or_create_node(informed_id)

        elif isinstance(relation, (ProvInfluence, ProvSpecialization, ProvAlternate,
                                   ProvMembership, ProvStart, ProvEnd, ProvInvalidation)):
            # Generic handling for other relation types
            # Most follow pattern: relation(target, source, ...)
            target_id = formal_attrs[0][1] if formal_attrs[0] else None
            source_id = formal_attrs[1][1] if formal_attrs[1] else None
            if source_id and target_id:
                source_node = self._get_or_create_node(source_id)
                target_node = self._get_or_create_node(target_id)

        if not source_node or not target_node:
            return None

        # Create the edge
        edge = GraphEdge(relation, source_node, target_node, edge_id)
        self._edges[edge_id] = edge

        # Add to networkx graph
        self.graph.add_edge(source_node.node_id, target_node.node_id,
                            prov_relation=relation, graph_edge=edge)

        # Update node edge lists
        source_node.add_effect_edge(edge)
        target_node.add_cause_edge(edge)

        return edge

    def _get_or_create_node(self, identifier: QualifiedName) -> Optional[GraphNode]:
        """Get existing node by identifier or create a placeholder node."""
        node_id = str(identifier)

        if node_id in self._nodes:
            return self._nodes[node_id]

        # Try to find the actual record in the document
        for record in self._prov_document.get_records():
            if hasattr(record, 'identifier') and record.identifier == identifier:
                if isinstance(record, ProvEntity):
                    return self.add_entity_as_node(record)
                elif isinstance(record, ProvActivity):
                    return self.add_activity_as_node(record)
                elif isinstance(record, ProvAgent):
                    return self.add_agent_as_node(record)

        # Check bundles too
        if hasattr(self._prov_document, 'bundles'):
            for bundle in self._prov_document.bundles:
                for record in bundle.get_records():
                    if hasattr(record, 'identifier') and record.identifier == identifier:
                        if isinstance(record, ProvEntity):
                            return self.add_entity_as_node(record)
                        elif isinstance(record, ProvActivity):
                            return self.add_activity_as_node(record)
                        elif isinstance(record, ProvAgent):
                            return self.add_agent_as_node(record)

        # If not found, create a placeholder entity node
        # (relations might reference external entities)
        placeholder = type('PlaceholderEntity', (), {'identifier': identifier})()
        node = GraphNode(placeholder, node_id)
        self._nodes[node_id] = node
        self.graph.add_node(node_id, graph_node=node)
        return node

    def get_nodes(self) -> List[GraphNode]:
        return list(self._nodes.values())

    def get_edges(self) -> List[GraphEdge]:
        return list(self._edges.values())

    def get_node_by_id(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_edge_by_id(self, edge_id: str) -> Optional[GraphEdge]:
        return self._edges.get(edge_id)

    def get_networkx_graph(self) -> nx.DiGraph:
        return self.graph

    def get_neighbors(self, node_id: str) -> List[str]:
        if node_id in self.graph:
            return list(self.graph.neighbors(node_id))
        return []

    def get_predecessors(self, node_id: str) -> List[str]:
        if node_id in self.graph:
            return list(self.graph.predecessors(node_id))
        return []

    def get_successors(self, node_id: str) -> List[str]:
        if node_id in self.graph:
            return list(self.graph.successors(node_id))
        return []

    def visualize(self, filename: Optional[str] = None,
                  show_labels: bool = True,
                  node_size: int = 1000,
                  font_size: int = 10):
        try:
            import matplotlib.pyplot as plt

            pos = nx.spring_layout(self.graph)

            nx.draw_networkx_nodes(self.graph, pos, node_size=node_size,
                                   node_color='lightblue', alpha=0.7)

            nx.draw_networkx_edges(self.graph, pos, edge_color='gray',
                                   arrows=True, arrowsize=20, alpha=0.6)

            if show_labels:
                labels = {}
                for node_id in self.graph.nodes():
                    node = self._nodes.get(node_id)
                    if node and node.prov_entity.identifier:
                        labels[node_id] = str(node.prov_entity.identifier).split(':')[-1]
                    else:
                        labels[node_id] = node_id

                nx.draw_networkx_labels(self.graph, pos, labels, font_size=font_size)

            plt.title("Provenance Graph (Entities as Nodes, Activities as Edges)")
            plt.axis('off')

            if filename:
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                print(f"Graph saved to {filename}")
            else:
                plt.show()

        except ImportError:
            print("matplotlib not available for visualization")

    def to_prov_document(self) -> ProvDocument:
        if self._prov_document and hasattr(self._prov_document, 'bundles') and self._prov_document.bundles:
            doc = ProvDocument()

            if hasattr(self._prov_document, 'namespaces'):
                for ns in self._prov_document.namespaces:
                    doc.add_namespace(ns.prefix, ns.uri)

            for original_bundle in self._prov_document.bundles:
                new_bundle = doc.bundle(original_bundle.identifier)

                for node in self._nodes.values():
                    if node.prov_entity:
                        new_bundle.add_record(node.prov_entity)

                for edge in self._edges.values():
                    if edge.prov_activity:
                        new_bundle.add_record(edge.prov_activity)

            return doc
        else:
            doc = ProvDocument()

            for node in self._nodes.values():
                doc.add_record(node.prov_entity)

            for edge in self._edges.values():
                doc.add_record(edge.prov_activity)

            return doc

    def create_subgraph(self, node_filter_func) -> 'ProvGraphWrapper':
        """
        Create a subgraph containing only nodes that pass the filter function.

        The subgraph includes:
        - All nodes for which node_filter_func(node) returns True
        - All edges where both source and target nodes are in the filtered set
        - All namespaces from the original document

        Args:
            node_filter_func: Callable that takes a GraphNode and returns bool.
                             Returns True to include the node in the subgraph.

        Returns:
            New ProvGraphWrapper containing the filtered subgraph.

        Example:
            >>> def keep_datasets(node):
            ...     for attr_name, attr_value in node.prov_entity.attributes:
            ...         if str(attr_name) == 'prov:type':
            ...             return str(attr_value) == 'Dataset'
            ...     return False
            >>> subgraph = graph.create_subgraph(keep_datasets)
        """
        # Filter nodes
        filtered_nodes = [node for node in self._nodes.values()
                          if node_filter_func(node)]
        filtered_node_ids = {node.identifier for node in filtered_nodes}

        # Create new PROV document
        new_doc = ProvDocument()

        # Copy namespaces from original document
        if hasattr(self._prov_document, 'namespaces'):
            for ns in self._prov_document.namespaces:
                new_doc.add_namespace(ns.prefix, ns.uri)

        # Add filtered nodes to new document
        for node in filtered_nodes:
            if node.prov_entity:
                new_doc.add_record(node.prov_entity)

        # Add edges where both source and target are in filtered set
        for edge in self._edges.values():
            if (edge.cause.identifier in filtered_node_ids and
                    edge.effect.identifier in filtered_node_ids):
                if edge.prov_relation:
                    new_doc.add_record(edge.prov_relation)

        return ProvGraphWrapper(new_doc)

    def clear(self):
        self.graph.clear()
        self._nodes.clear()
        self._edges.clear()

    def __len__(self) -> int:
        return len(self._nodes)

    def __str__(self) -> str:
        return f"ProvGraphWrapper(nodes={len(self._nodes)}, edges={len(self._edges)})"
