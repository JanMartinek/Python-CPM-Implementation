"""
CPM Document - Traversal Operations Mixin

Graph traversal and path finding operations.
"""

from typing import Dict, List, Optional, Any, Set, Union, Tuple
from prov.model import ProvDocument, ProvBundle, ProvEntity, ProvActivity, ProvAgent, ProvRecord
from prov.identifier import QualifiedName, Namespace
from prov.constants import PROV_TYPE, PROV_LABEL, PROV_VALUE
import copy

from src.graph.node import GraphNode
from src.graph.wrapper import ProvGraphWrapper
from src.cpm.constants import *
from src.cpm.template import CpmBundleTemplate
from src.cpm.template_mapper import TemplateProvMapper
from src.cpm.ti_algorithm import TraversalInformationAlgorithm
from src.cpm.exceptions import *


class CpmDocumentTraversalMixin:
    """
    Mixin providing graph traversal operations for CPM documents.

    This mixin handles:
    - Predecessor/successor traversal
    - Path finding
    - Connected components
    - Connector chains

    Note: This mixin expects the following attributes to be available:
    - self.graph_wrapper: ProvGraphWrapper instance
    - self.ti_algorithm: TI algorithm instance
    - self._bundle: Current bundle
    """

    def get_predecessors(self, node_id: Union[str, QualifiedName],
                         relation_types: Optional[List[str]] = None,
                         max_depth: Optional[int] = None) -> List[GraphNode]:
        """
        Get all predecessor nodes (nodes that have edges pointing to this node).

        Args:
            node_id: Target node identifier
            relation_types: Optional list of relation types to follow
            max_depth: Optional maximum traversal depth

        Returns:
            List of predecessor nodes
        """
        visited = set()
        predecessors = []

        def _traverse_predecessors(current_id: Union[str, QualifiedName], depth: int):
            if max_depth is not None and depth >= max_depth:
                return

            str_current_id = str(current_id)
            if str_current_id in visited:
                return
            visited.add(str_current_id)

            # Find edges where current node is target
            edges = self.get_edges(target_id=current_id)
            for edge in edges:
                if relation_types:
                    edge_type = type(edge).__name__.lower()
                    if not any(rel_type.lower() in edge_type for rel_type in relation_types):
                        continue

                source, _ = self._extract_edge_endpoints(edge)
                if source and str(source) != str_current_id:
                    pred_node = self.get_node(source)
                    if pred_node and pred_node not in predecessors:
                        predecessors.append(pred_node)
                        _traverse_predecessors(source, depth + 1)

        _traverse_predecessors(node_id, 0)
        return predecessors

    def get_successors(self, node_id: Union[str, QualifiedName],
                       relation_types: Optional[List[str]] = None,
                       max_depth: Optional[int] = None) -> List[GraphNode]:
        """
        Get all successor nodes (nodes that this node has edges pointing to).

        Args:
            node_id: Source node identifier
            relation_types: Optional list of relation types to follow
            max_depth: Optional maximum traversal depth

        Returns:
            List of successor nodes
        """
        visited = set()
        successors = []

        def _traverse_successors(current_id: Union[str, QualifiedName], depth: int):
            if max_depth is not None and depth >= max_depth:
                return

            str_current_id = str(current_id)
            if str_current_id in visited:
                return
            visited.add(str_current_id)

            # Find edges where current node is source
            edges = self.get_edges(source_id=current_id)
            for edge in edges:
                if relation_types:
                    edge_type = type(edge).__name__.lower()
                    if not any(rel_type.lower() in edge_type for rel_type in relation_types):
                        continue

                _, target = self._extract_edge_endpoints(edge)
                if target and str(target) != str_current_id:
                    succ_node = self.get_node(target)
                    if succ_node and succ_node not in successors:
                        successors.append(succ_node)
                        _traverse_successors(target, depth + 1)

        _traverse_successors(node_id, 0)
        return successors

    def get_connected_components(self) -> List[List[GraphNode]]:
        """
        Get all connected components in the graph.

        Returns:
            List of connected components, each as a list of nodes
        """
        all_nodes = self.graph_wrapper.get_nodes()
        visited = set()
        components = []

        def _dfs_component(start_node: GraphNode, component: List[GraphNode]):
            if str(start_node.identifier) in visited:
                return

            visited.add(str(start_node.identifier))
            component.append(start_node)

            # Find all connected nodes
            all_connected = (self.get_predecessors(start_node.identifier, max_depth=1) +
                             self.get_successors(start_node.identifier, max_depth=1))

            for connected_node in all_connected:
                if str(connected_node.identifier) not in visited:
                    _dfs_component(connected_node, component)

        for node in all_nodes:
            if str(node.identifier) not in visited:
                component = []
                _dfs_component(node, component)
                if component:
                    components.append(component)

        return components

    def find_paths(self, source_id: Union[str, QualifiedName],
                   target_id: Union[str, QualifiedName],
                   max_length: Optional[int] = None) -> List[List[GraphNode]]:
        """
        Find all paths between two nodes.

        Args:
            source_id: Source node identifier
            target_id: Target node identifier
            max_length: Optional maximum path length

        Returns:
            List of paths, each as a list of nodes
        """
        source_node = self.get_node(source_id)
        target_node = self.get_node(target_id)

        if not source_node or not target_node:
            return []

        paths = []

        def _find_paths_recursive(current: GraphNode, target: GraphNode,
                                  path: List[GraphNode], visited: Set[str]):
            if max_length and len(path) >= max_length:
                return

            if current.identifier == target.identifier:
                paths.append(path + [current])
                return

            if str(current.identifier) in visited:
                return

            visited.add(str(current.identifier))
            successors = self.get_successors(current.identifier, max_depth=1)

            for successor in successors:
                _find_paths_recursive(successor, target, path + [current], visited.copy())

        _find_paths_recursive(source_node, target_node, [], set())
        return paths

    def get_precursors(self, connector_id: Union[str, QualifiedName]) -> Optional[List[GraphNode]]:
        """
        Get precursor connectors for a given connector through derivation relations.

        Args:
            connector_id: Connector identifier

        Returns:
            List of precursor connector nodes, or None if not a connector
        """
        connector_node = self.get_node(connector_id)
        if not connector_node:
            return None

        # Check if it's a connector and belongs to TI
        if not (self._has_cpm_type(connector_node, CPM_FORWARD_CONNECTOR) or
                self._has_cpm_type(connector_node, CPM_BACKWARD_CONNECTOR)):
            return None

        if not self.ti_algorithm.belongs_to_traversal_information(connector_node.prov_entity):
            return None

        precursors = []
        visited = set()

        def _find_precursors(current_id: Union[str, QualifiedName]):
            if str(current_id) in visited:
                return
            visited.add(str(current_id))

            # Find derivation edges where current node is the derived entity
            derivation_edges = self.get_edges(target_id=current_id, relation_type='derivation')
            for edge in derivation_edges:
                source, _ = self._extract_edge_endpoints(edge)
                if source:
                    source_node = self.get_node(source)
                    if (source_node and
                        (self._has_cpm_type(source_node, CPM_FORWARD_CONNECTOR) or
                         self._has_cpm_type(source_node, CPM_BACKWARD_CONNECTOR)) and
                            self.ti_algorithm.belongs_to_traversal_information(source_node.prov_entity)):
                        if source_node not in precursors:
                            precursors.append(source_node)
                        _find_precursors(source)

        _find_precursors(connector_id)
        return precursors

    def get_successors_connectors(self, connector_id: Union[str, QualifiedName]) -> Optional[List[GraphNode]]:
        """
        Get successor connectors for a given connector through derivation relations.

        Args:
            connector_id: Connector identifier

        Returns:
            List of successor connector nodes, or None if not a connector
        """
        connector_node = self.get_node(connector_id)
        if not connector_node:
            return None

        # Check if it's a connector and belongs to TI
        if not (self._has_cpm_type(connector_node, CPM_FORWARD_CONNECTOR) or
                self._has_cpm_type(connector_node, CPM_BACKWARD_CONNECTOR)):
            return None

        if not self.ti_algorithm.belongs_to_traversal_information(connector_node.prov_entity):
            return None

        successors = []
        visited = set()

        def _find_successors(current_id: Union[str, QualifiedName]):
            if str(current_id) in visited:
                return
            visited.add(str(current_id))

            # Find derivation edges where current node is the source entity
            derivation_edges = self.get_edges(source_id=current_id, relation_type='derivation')
            for edge in derivation_edges:
                _, target = self._extract_edge_endpoints(edge)
                if target:
                    target_node = self.get_node(target)
                    if (target_node and
                        (self._has_cpm_type(target_node, CPM_FORWARD_CONNECTOR) or
                         self._has_cpm_type(target_node, CPM_BACKWARD_CONNECTOR)) and
                            self.ti_algorithm.belongs_to_traversal_information(target_node.prov_entity)):
                        if target_node not in successors:
                            successors.append(target_node)
                        _find_successors(target)

        _find_successors(connector_id)
        return successors

    def get_related_connectors(self, connector_id: Union[str, QualifiedName],
                               direction: str = 'both') -> List[GraphNode]:
        """
        Get connectors related to a given connector through derivation chains.

        Args:
            connector_id: Connector identifier
            direction: 'forward', 'backward', or 'both'

        Returns:
            List of related connector nodes
        """
        connector_node = self.get_node(connector_id)
        if not connector_node:
            return []

        # Check if it's actually a connector
        if not (self._has_cpm_type(connector_node, CPM_FORWARD_CONNECTOR) or
                self._has_cpm_type(connector_node, CPM_BACKWARD_CONNECTOR)):
            return []

        related = []
        visited = set()

        def _traverse_connectors(current_id: Union[str, QualifiedName],
                                 search_direction: str):
            if str(current_id) in visited:
                return
            visited.add(str(current_id))

            if search_direction in ['forward', 'both']:
                # Follow derivation edges forward
                derivation_edges = self.get_edges(source_id=current_id, relation_type='derivation')
                for edge in derivation_edges:
                    _, target = self._extract_edge_endpoints(edge)
                    if target:
                        target_node = self.get_node(target)
                        if (target_node and
                            (self._has_cpm_type(target_node, CPM_FORWARD_CONNECTOR) or
                             self._has_cpm_type(target_node, CPM_BACKWARD_CONNECTOR)) and
                                self.ti_algorithm.belongs_to_traversal_information(target_node.prov_entity)):
                            if target_node not in related:
                                related.append(target_node)
                            _traverse_connectors(target, search_direction)

            if search_direction in ['backward', 'both']:
                # Follow derivation edges backward
                derivation_edges = self.get_edges(target_id=current_id, relation_type='derivation')
                for edge in derivation_edges:
                    source, _ = self._extract_edge_endpoints(edge)
                    if source:
                        source_node = self.get_node(source)
                        if (source_node and
                            (self._has_cpm_type(source_node, CPM_FORWARD_CONNECTOR) or
                             self._has_cpm_type(source_node, CPM_BACKWARD_CONNECTOR)) and
                                self.ti_algorithm.belongs_to_traversal_information(source_node.prov_entity)):
                            if source_node not in related:
                                related.append(source_node)
                            _traverse_connectors(source, search_direction)

        _traverse_connectors(connector_id, direction)
        return related

    def get_subgraph(self, node_ids: List[Union[str, QualifiedName]],
                     include_edges: bool = True) -> 'CpmDocument':
        """
        Extract a subgraph containing only specified nodes and optionally their edges.

        Args:
            node_ids: List of node identifiers to include
            include_edges: Whether to include edges between the nodes

        Returns:
            A new CpmDocument containing the subgraph
        """
        subgraph_doc = self.__class__(ProvDocument())
        added_nodes = {}

        # Add specified nodes
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node:
                node_type = node.node_type_name

                # Extract attributes
                attributes = {}
                for attr_name, attr_value in node.prov_entity.attributes:
                    if attr_name != PROV_TYPE:
                        attributes[str(attr_name)] = attr_value

                prov_types = node.get_prov_attribute(str(PROV_TYPE))
                prov_type = prov_types[0] if prov_types else None

                try:
                    added_node = subgraph_doc.add_node(node_type, node.identifier, attributes, prov_type)
                    added_nodes[str(node.identifier)] = added_node
                except (AttributeError, TypeError, ValueError, InvalidOperationError, CpmDocumentError):
                    pass

        # Add edges between included nodes
        if include_edges:
            for source_id in node_ids:
                for target_id in node_ids:
                    if source_id != target_id:
                        edges = self.get_edges(source_id, target_id)
                        for edge in edges:
                            try:
                                # Determine edge type and add to subgraph
                                edge_type = type(edge).__name__.lower()
                                if 'usage' in edge_type:
                                    subgraph_doc.add_edge('used', source_id, target_id)
                                elif 'generation' in edge_type:
                                    subgraph_doc.add_edge('wasgeneratedby', source_id, target_id)
                                # Add other edge types as needed
                            except (AttributeError, TypeError, ValueError, InvalidOperationError, CpmDocumentError, NodeNotFoundError):
                                pass

        return subgraph_doc
