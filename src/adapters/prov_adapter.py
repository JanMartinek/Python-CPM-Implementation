import logging
from typing import Optional, List, Dict, Any
import networkx as nx
from prov.model import ProvDocument
from ..graph.wrapper import ProvGraphWrapper
from ..graph.node import GraphNode
from ..cpm.namespaces import (
    EXAMPLE_NAMESPACE_PREFIX,
    EXAMPLE_NAMESPACE_URI,
    ensure_namespace,
    get_namespace_by_prefix,
)


LOGGER = logging.getLogger(__name__)


class ProvAdapter:
    """
    Adapter class to convert between PROV documents and graph representations.
    """

    def __init__(self):
        pass

    def from_prov_document(self, doc: ProvDocument) -> ProvGraphWrapper:
        return ProvGraphWrapper(doc)

    def to_prov_document(self, graph: ProvGraphWrapper) -> ProvDocument:
        return graph.to_prov_document()

    def create_simple_graph(self, entities: List[str], activities: List[tuple]) -> ProvGraphWrapper:
        doc = ProvDocument()

        ensure_namespace(doc, EXAMPLE_NAMESPACE_PREFIX, EXAMPLE_NAMESPACE_URI)

        entity_objects = {}
        for entity_id in entities:
            qualified_id = f'ex:{entity_id}' if ':' not in entity_id else entity_id
            entity = doc.entity(qualified_id)
            entity_objects[entity_id] = entity

        for activity_id, source_id, target_id in activities:
            if source_id in entity_objects and target_id in entity_objects:
                qualified_activity_id = f'ex:{activity_id}' if ':' not in activity_id else activity_id
                activity = doc.activity(qualified_activity_id)

                doc.usage(activity, entity_objects[source_id])
                doc.generation(entity_objects[target_id], activity)

        return ProvGraphWrapper(doc)

    def add_entity_to_graph(self, graph: ProvGraphWrapper, entity_id: str,
                            attributes: Optional[Dict[str, Any]] = None) -> GraphNode:
        ensure_namespace(graph._prov_document, EXAMPLE_NAMESPACE_PREFIX, EXAMPLE_NAMESPACE_URI)
        example_ns = get_namespace_by_prefix(graph._prov_document, EXAMPLE_NAMESPACE_PREFIX)

        if ':' not in entity_id:
            qualified_id = example_ns[entity_id] if example_ns else f'{EXAMPLE_NAMESPACE_PREFIX}:{entity_id}'
        else:
            qualified_id = entity_id

        attr_list = []
        if attributes:
            for attr_name, attr_value in attributes.items():
                if ':' not in attr_name:
                    for ns in graph._prov_document.namespaces:
                        if ns.prefix == 'ex':
                            attr_qname = ns[attr_name]
                            attr_list.append((attr_qname, attr_value))
                            break
                else:
                    try:
                        attr_qname = graph._prov_document.valid_qualified_name(attr_name)
                        if attr_qname:
                            attr_list.append((attr_qname, attr_value))
                    except (AttributeError, TypeError, ValueError) as exc:
                        LOGGER.debug("Skipping invalid attribute %s: %s", attr_name, exc)
                        continue

        entity = graph._prov_document.entity(qualified_id, other_attributes=attr_list)

        return graph.add_entity_as_node(entity)

    def add_activity_to_graph(self, graph: ProvGraphWrapper, activity_id: str,
                              source_entity_id: str, target_entity_id: str,
                              attributes: Optional[Dict[str, Any]] = None) -> Optional[GraphNode]:
        """Add an activity as a node (PROV-DM compliant) with usage and generation relations"""
        qualified_source_id = f'ex:{source_entity_id}' if ':' not in source_entity_id else source_entity_id
        qualified_target_id = f'ex:{target_entity_id}' if ':' not in target_entity_id else target_entity_id
        qualified_activity_id = f'ex:{activity_id}' if ':' not in activity_id else activity_id

        # Find existing entities in the graph
        source_entity = None
        target_entity = None
        for node in graph.get_nodes():
            if hasattr(node.prov_entity, 'identifier'):
                node_id = str(node.prov_entity.identifier)
                if node_id == qualified_source_id:
                    source_entity = node.prov_entity
                elif node_id == qualified_target_id:
                    target_entity = node.prov_entity

        if not source_entity or not target_entity:
            return None

        # Create activity with relations
        activity = graph._prov_document.activity(qualified_activity_id, other_attributes=attributes)
        usage_relation = graph._prov_document.usage(activity, source_entity)
        generation_relation = graph._prov_document.generation(target_entity, activity)

        # Add activity as a node (PROV-DM compliant)
        activity_node = graph.add_activity_as_node(activity)

        # Add relations as edges
        graph.add_relation_as_edge(usage_relation)
        graph.add_relation_as_edge(generation_relation)

        return activity_node

    def export_to_formats(self, graph: ProvGraphWrapper,
                          formats: List[str] = None) -> Dict[str, str]:
        if formats is None:
            formats = ['json', 'xml', 'rdf']

        doc = graph.to_prov_document()
        results = {}

        for format_name in formats:
            try:
                results[format_name] = doc.serialize(format=format_name)
            except (AttributeError, TypeError, ValueError, NotImplementedError) as e:
                results[format_name] = f"Error serializing to {format_name}: {str(e)}"

        return results

    def import_from_formats(self, content: str, format_name: str = 'json') -> ProvGraphWrapper:
        doc = ProvDocument.deserialize(content=content, format=format_name)
        return ProvGraphWrapper(doc)

    def merge_graphs(self, *graphs: ProvGraphWrapper) -> ProvGraphWrapper:
        merged_doc = ProvDocument()

        for graph in graphs:
            graph_doc = graph.to_prov_document()
            merged_doc.update(graph_doc)

        return ProvGraphWrapper(merged_doc)

    def get_graph_statistics(self, graph: ProvGraphWrapper) -> Dict[str, Any]:
        nx_graph = graph.get_networkx_graph()

        stats = {
            'num_nodes': len(graph.get_nodes()),
            'num_edges': len(graph.get_edges()),
            'is_connected': len(nx_graph) > 0 and nx.is_weakly_connected(nx_graph),
            'num_connected_components': nx.number_weakly_connected_components(nx_graph),
            'is_dag': nx.is_directed_acyclic_graph(nx_graph),
            'density': nx.density(nx_graph) if len(nx_graph) > 1 else 0.0
        }

        if len(nx_graph) > 0:
            degrees = [d for n, d in nx_graph.degree()]
            stats['avg_degree'] = sum(degrees) / len(degrees) if degrees else 0
            stats['max_degree'] = max(degrees) if degrees else 0
            stats['min_degree'] = min(degrees) if degrees else 0

        return stats
