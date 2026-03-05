"""
CPM Document - Analysis Operations Mixin

Analysis, validation, and metrics operations.
"""

from typing import Dict, List, Optional, Any, Set, Union, Tuple
from prov.model import ProvDocument, ProvBundle, ProvEntity, ProvActivity, ProvAgent, ProvRecord
from prov.identifier import QualifiedName, Namespace
from prov.constants import PROV_TYPE, PROV_LABEL, PROV_VALUE
import copy

from src.graph.node import GraphNode
from src.graph.wrapper import ProvGraphWrapper
from src.cpm.constants import *
from src.cpm.template import TraversalInformationTemplate
from src.cpm.template_mapper import TemplateProvMapper
from src.cpm.ti_algorithm import TraversalInformationAlgorithm
from src.cpm.exceptions import *


class CpmDocumentAnalysisMixin:
    """
    Mixin providing analysis and validation operations for CPM documents.

    This mixin handles:
    - TI/DS separation analysis
    - Structure validation
    - Provenance chain analysis
    - Complexity metrics
    - Centrality calculations

    Note: This mixin expects the following attributes to be available:
    - self.graph_wrapper: ProvGraphWrapper instance
    - self.ti_algorithm: TI algorithm instance
    """

    def get_traversal_information_nodes(self) -> List[GraphNode]:
        """Get all nodes belonging to traversal information"""
        ti_nodes = []
        for node in self.graph_wrapper.get_nodes():
            if self.ti_algorithm.belongs_to_traversal_information(node.prov_entity):
                ti_nodes.append(node)
        return ti_nodes

    def get_domain_specific_nodes(self) -> List[GraphNode]:
        """Get all nodes belonging to domain-specific provenance"""
        ds_nodes = []
        for node in self.graph_wrapper.get_nodes():
            if not self.ti_algorithm.belongs_to_traversal_information(node.prov_entity):
                ds_nodes.append(node)
        return ds_nodes

    def get_statistics(self) -> Dict[str, int]:
        """
        Get document statistics.

        Returns:
            Dictionary with node and relation counts
        """
        all_nodes = self.graph_wrapper.get_nodes()
        ti_nodes = self.get_traversal_information_nodes()
        ds_nodes = self.get_domain_specific_nodes()

        return {
            'total_nodes': len(all_nodes),
            'total_edges': len(self.get_edges()),
            'traversal_information_nodes': len(ti_nodes),
            'domain_specific_nodes': len(ds_nodes),
            'entities': len([n for n in all_nodes if isinstance(n.prov_entity, ProvEntity)]),
            'activities': len([n for n in all_nodes if isinstance(n.prov_entity, ProvActivity)]),
            'agents': len([n for n in all_nodes if isinstance(n.prov_entity, ProvAgent)]),
            'forward_connectors': len(self.get_forward_connectors()),
            'backward_connectors': len(self.get_backward_connectors()),
            'main_activities': len([n for n in ti_nodes if self._has_cpm_type(n, CPM_MAIN_ACTIVITY)])
        }

    def get_cross_part_edges(self) -> List[Any]:
        """
        Get edges between traversal information and domain-specific nodes.

        Returns:
            List of cross-part edges
        """
        cross_edges = []
        all_edges = self.get_edges()

        for edge in all_edges:
            source, target = self._extract_edge_endpoints(edge)
            if source and target:
                source_node = self.get_node(source)
                target_node = self.get_node(target)

                if source_node and target_node:
                    source_is_ti = self.ti_algorithm.belongs_to_traversal_information(source_node.prov_entity)
                    target_is_ti = self.ti_algorithm.belongs_to_traversal_information(target_node.prov_entity)

                    # Edge is cross-part if one endpoint is TI and the other is DS
                    if source_is_ti != target_is_ti:
                        cross_edges.append(edge)

        return cross_edges

    def get_traversal_information_part(self) -> List[GraphNode]:
        """
        Get cloned traversal information nodes with only TI-to-TI relations.

        Returns:
            List of cloned TI nodes
        """
        ti_nodes = self.get_traversal_information_nodes()

        # Create copies of TI nodes (simplified - full implementation would deep clone)
        cloned_nodes = []
        for node in ti_nodes:
            cloned_nodes.append(node)

        return cloned_nodes

    def validate_structure(self) -> Dict[str, List[str]]:
        """
        Validate the CPM document structure and return any issues found.

        Returns:
            Dictionary with validation issues categorized by type
        """
        issues = {
            'errors': [],
            'warnings': [],
            'info': []
        }

        # Check for main activity
        main_activities = [n for n in self.get_traversal_information_nodes()
                           if self._has_cpm_type(n, CPM_MAIN_ACTIVITY)]

        if not main_activities:
            issues['warnings'].append("No main activity found in traversal information")
        elif len(main_activities) > 1:
            issues['warnings'].append(f"Multiple main activities found: {len(main_activities)}")

        # Check connector consistency
        forward_connectors = self.get_forward_connectors()
        backward_connectors = self.get_backward_connectors()

        for connector in forward_connectors + backward_connectors:
            # Check if connector has required attributes
            bundle_id_attrs = connector.get_prov_attribute('cpm:referencedBundleId')
            hash_attrs = connector.get_prov_attribute('cpm:referencedBundleHashValue')

            if not bundle_id_attrs:
                issues['errors'].append(f"Connector {connector.identifier} missing referencedBundleId")
            if not hash_attrs:
                issues['warnings'].append(f"Connector {connector.identifier} missing hash value")

        # Check for orphaned nodes (nodes with no edges)
        all_nodes = self.graph_wrapper.get_nodes()
        for node in all_nodes:
            incoming_edges = self.get_edges(target_id=node.identifier)
            outgoing_edges = self.get_edges(source_id=node.identifier)

            if not incoming_edges and not outgoing_edges:
                issues['info'].append(f"Orphaned node found: {node.identifier}")

        return issues

    def analyze_provenance_chains(self) -> Dict[str, Any]:
        """
        Analyze provenance chains in the document.

        Returns:
            Analysis results including chain statistics and patterns
        """
        analysis = {
            'total_chains': 0,
            'average_chain_length': 0,
            'longest_chain': 0,
            'chain_patterns': {},
            'circular_dependencies': []
        }

        # Find all entity nodes as potential chain starts
        entity_nodes = [n for n in self.graph_wrapper.get_nodes()
                        if isinstance(n.prov_entity, ProvEntity)]

        chains = []
        for entity in entity_nodes:
            # Trace derivation chains
            chain = self._trace_derivation_chain(entity)
            if len(chain) > 1:
                chains.append(chain)

        if chains:
            analysis['total_chains'] = len(chains)
            chain_lengths = [len(chain) for chain in chains]
            analysis['average_chain_length'] = sum(chain_lengths) / len(chain_lengths)
            analysis['longest_chain'] = max(chain_lengths)

        # Check for circular dependencies
        analysis['circular_dependencies'] = self._find_circular_dependencies()

        return analysis

    def get_influence_network(self) -> Dict[str, List[str]]:
        """
        Build an influence network showing how nodes influence each other.

        Returns:
            Dictionary mapping node IDs to lists of influenced node IDs
        """
        network = {}

        for node in self.graph_wrapper.get_nodes():
            node_id = str(node.identifier)
            influenced_nodes = []

            # Find all nodes this node influences through any relation
            successors = self.get_successors(node.identifier, max_depth=1)
            for successor in successors:
                influenced_nodes.append(str(successor.identifier))

            network[node_id] = influenced_nodes

        return network

    def compute_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Compute centrality metrics for nodes in the graph.

        Returns:
            Dictionary with centrality metrics for each node
        """
        metrics = {}
        all_nodes = self.graph_wrapper.get_nodes()

        for node in all_nodes:
            node_id = str(node.identifier)

            # Degree centrality (simple version)
            in_degree = len(self.get_predecessors(node.identifier, max_depth=1))
            out_degree = len(self.get_successors(node.identifier, max_depth=1))
            total_degree = in_degree + out_degree

            # Normalize by total possible connections
            max_connections = len(all_nodes) - 1
            degree_centrality = total_degree / max_connections if max_connections > 0 else 0

            metrics[node_id] = {
                'degree_centrality': degree_centrality,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'total_degree': total_degree
            }

        return metrics

    def _trace_derivation_chain(self, start_entity: GraphNode) -> List[GraphNode]:
        """Trace a derivation chain starting from an entity."""
        chain = [start_entity]
        visited = {str(start_entity.identifier)}

        current = start_entity
        while True:
            # Find entities this one was derived from
            derivation_edges = self.get_edges(target_id=current.identifier, relation_type='derivation')
            if not derivation_edges:
                break

            # Take the first derivation source
            source, _ = self._extract_edge_endpoints(derivation_edges[0])
            if source and str(source) not in visited:
                source_node = self.get_node(source)
                if source_node and isinstance(source_node.prov_entity, ProvEntity):
                    chain.append(source_node)
                    visited.add(str(source))
                    current = source_node
                else:
                    break
            else:
                break

        return chain

    def _find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the graph."""
        circular_deps = []
        all_nodes = self.graph_wrapper.get_nodes()

        def _has_path(start: GraphNode, end: GraphNode, visited: Set[str]) -> bool:
            if str(start.identifier) == str(end.identifier):
                return True
            if str(start.identifier) in visited:
                return False

            visited.add(str(start.identifier))
            successors = self.get_successors(start.identifier, max_depth=1)

            for successor in successors:
                if _has_path(successor, end, visited.copy()):
                    return True
            return False

        # Check each pair of nodes for bidirectional paths
        for i, node1 in enumerate(all_nodes):
            for node2 in all_nodes[i+1:]:
                if (_has_path(node1, node2, set()) and
                        _has_path(node2, node1, set())):
                    circular_deps.append([str(node1.identifier), str(node2.identifier)])

        return circular_deps

    def validate_cpm_constraints(self) -> Dict[str, List[str]]:
        """
        Validate CPM-specific constraints beyond basic structure validation.
        """
        issues = {
            'critical_errors': [],
            'warnings': [],
            'recommendations': []
        }

        # Check main activity constraints
        main_activities = [n for n in self.get_traversal_information_nodes()
                           if self._has_cpm_type(n, CPM_MAIN_ACTIVITY)]

        if len(main_activities) == 0:
            issues['critical_errors'].append("No main activity found - required for CPM compliance")
        elif len(main_activities) > 1:
            issues['warnings'].append(f"Multiple main activities found: {len(main_activities)}")

        # Check connector integrity
        for connector in self.get_forward_connectors() + self.get_backward_connectors():
            # Validate required CPM attributes
            bundle_id_attrs = connector.get_prov_attribute('cpm:referencedBundleId')
            if not bundle_id_attrs:
                issues['critical_errors'].append(
                    f"Connector {connector.identifier} missing required referencedBundleId")

            # Check hash value presence
            hash_attrs = connector.get_prov_attribute('cpm:referencedBundleHashValue')
            if not hash_attrs:
                issues['recommendations'].append(
                    f"Connector {connector.identifier} should have hash value for integrity")

        # Check traversal information completeness
        ti_nodes = self.get_traversal_information_nodes()
        ds_nodes = self.get_domain_specific_nodes()

        if len(ti_nodes) == 0:
            issues['critical_errors'].append("No traversal information nodes found")

        if len(ds_nodes) == 0:
            issues['recommendations'].append("No domain-specific nodes found - consider adding domain context")

        return issues

    def analyze_document_complexity(self) -> Dict[str, Any]:
        """
        Analyze document complexity metrics.
        Extended analysis beyond basic statistics
        """
        stats = self.get_statistics()
        all_nodes = self.get_all_nodes()
        all_edges = self.get_all_edges()

        # Calculate complexity metrics
        node_count = len(all_nodes)
        edge_count = len(all_edges)

        # Graph density (edges / max possible edges)
        max_edges = node_count * (node_count - 1) if node_count > 1 else 0
        density = edge_count / max_edges if max_edges > 0 else 0

        # Average degree
        total_degree = 0
        for node in all_nodes:
            in_degree = len(self.get_predecessors(node.identifier, max_depth=1))
            out_degree = len(self.get_successors(node.identifier, max_depth=1))
            total_degree += in_degree + out_degree

        avg_degree = total_degree / node_count if node_count > 0 else 0

        # Identify hub nodes (nodes with high connectivity)
        hub_nodes = []
        if node_count > 0:
            degrees = []
            for node in all_nodes:
                degree = (len(self.get_predecessors(node.identifier, max_depth=1)) +
                          len(self.get_successors(node.identifier, max_depth=1)))
                degrees.append((node.identifier, degree))

            degrees.sort(key=lambda x: x[1], reverse=True)
            # Top 10% are considered hubs
            hub_count = max(1, node_count // 10)
            hub_nodes = [node_id for node_id, degree in degrees[:hub_count]]

        return {
            'basic_stats': stats,
            'complexity_metrics': {
                'node_count': node_count,
                'edge_count': edge_count,
                'graph_density': density,
                'average_degree': avg_degree,
                'hub_nodes': hub_nodes,
                'connected_components': len(self.get_connected_components()),
                'complexity_score': density * avg_degree  # Simple complexity measure
            }
        }
