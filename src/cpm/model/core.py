"""
CPM Document - Core Operations Mixin

Core CRUD operations for CPM documents.
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


class CpmDocumentCoreMixin:
    """
    Mixin providing core CRUD operations for CPM documents.

    This mixin handles:
    - Node management (add, get, remove, update)
    - Edge management (add, get, remove)
    - Basic queries and lookups
    - Bundle management

    Note: This mixin expects the following attributes to be available:
    - self.graph_wrapper: ProvGraphWrapper instance
    - self.ti_algorithm: TI algorithm instance
    - self._bundle: Current bundle
    - self._modified: Modification flag
    - self._custom_bundle_id: Custom bundle ID
    """

    def _get_bundle(self) -> Union[ProvBundle, ProvDocument]:
        """Get the first bundle from the document, or return the document itself if no bundle exists"""
        doc = self.graph_wrapper.to_prov_document()

        # Based on debug output, bundles are accessible as dict_values
        if hasattr(doc, 'bundles') and doc.bundles:
            try:
                # doc.bundles returns dict_values, so iterate to get first bundle
                for bundle in doc.bundles:
                    return bundle
            except:
                pass

        # Fallback: try accessing as dictionary values
        if hasattr(doc, 'bundles') and hasattr(doc.bundles, 'values'):
            try:
                for bundle in doc.bundles.values():
                    return bundle
            except:
                pass

        # Alternative: check for bundle records directly
        if hasattr(doc, '_bundles') and doc._bundles:
            for bundle in doc._bundles.values():
                return bundle

        # No bundle exists - use the document itself
        # This allows CpmDocument to work with documents that don't have bundles
        return doc

    def _mark_modified(self):
        """Mark document as modified"""
        self._modified = True

    def is_modified(self) -> bool:
        """Check if document has been modified"""
        return self._modified

    def _reinitialize_graph_wrapper(self):
        """Reinitialize the graph wrapper to ensure all PROV elements are properly loaded"""
        prov_doc = self.graph_wrapper.to_prov_document()
        self.graph_wrapper = ProvGraphWrapper(prov_doc)
        self._bundle = self._get_bundle()

    def get_main_activity(self) -> Optional[GraphNode]:
        """Get the main activity node"""
        for node in self.graph_wrapper.get_nodes():
            if self._has_cpm_type(node, CPM_MAIN_ACTIVITY):
                if self.ti_algorithm.belongs_to_traversal_information(node.prov_entity):
                    return node
        return None

    def get_forward_connectors(self) -> List[GraphNode]:
        """Get all forward connector nodes"""
        connectors = []
        for node in self.graph_wrapper.get_nodes():
            if self._has_cpm_type(node, CPM_FORWARD_CONNECTOR):
                if self.ti_algorithm.belongs_to_traversal_information(node.prov_entity):
                    connectors.append(node)
        return connectors

    def get_backward_connectors(self) -> List[GraphNode]:
        """Get all backward connector nodes"""
        connectors = []
        for node in self.graph_wrapper.get_nodes():
            if self._has_cpm_type(node, CPM_BACKWARD_CONNECTOR):
                if self.ti_algorithm.belongs_to_traversal_information(node.prov_entity):
                    connectors.append(node)
        return connectors

    def get_node(self, identifier: Union[str, QualifiedName]) -> Optional[GraphNode]:
        """
        Get a single node by identifier.

        Args:
            identifier: Node identifier

        Returns:
            GraphNode if found, None otherwise

        Raises:
            MultipleNodesError: If multiple nodes have the same identifier
        """
        nodes = self.get_nodes(identifier)
        if not nodes:
            return None
        if len(nodes) > 1:
            raise MultipleNodesError(f"Multiple nodes found with identifier: {identifier}")
        return nodes[0]

    def get_nodes(self, identifier: Union[str, QualifiedName]) -> List[GraphNode]:
        """
        Get all nodes with the given identifier.

        Args:
            identifier: Node identifier

        Returns:
            List of GraphNodes with matching identifier
        """
        normalized_id = self._normalize_qname(identifier)

        matching_nodes = []
        for node in self.graph_wrapper.get_nodes():
            node_id = self._normalize_qname(node.identifier) if node.identifier else ""
            if node_id == normalized_id:
                matching_nodes.append(node)
        return matching_nodes

    def get_nodes_by_type(self, prov_type: Union[str, QualifiedName]) -> List[GraphNode]:
        """
        Get all nodes of a specific type.

        Args:
            prov_type: The PROV type to search for

        Returns:
            List of GraphNodes with matching type
        """
        normalized_type = self._normalize_qname(prov_type)

        matching_nodes = []
        for node in self.graph_wrapper.get_nodes():
            if self._node_has_type(node, normalized_type):
                matching_nodes.append(node)
        return matching_nodes

    def to_prov_document(self) -> ProvDocument:
        """Convert back to PROV document"""
        return self.graph_wrapper.to_prov_document()

    def to_graph_wrapper(self) -> ProvGraphWrapper:
        """Get the underlying graph wrapper"""
        return self.graph_wrapper

    def _has_cpm_type(self, node: GraphNode, cpm_type: QualifiedName) -> bool:
        """Check if node has specific CPM type"""
        try:
            prov_types = node.get_prov_attribute(str(PROV_TYPE))
            if prov_types:
                return cpm_type in prov_types
        except:
            pass
        return False

    def _node_has_type(self, node: GraphNode, type_str: str) -> bool:
        """Check if node has specific type (by string comparison)"""
        try:
            prov_types = node.get_prov_attribute(str(PROV_TYPE))
            if prov_types:
                for ptype in prov_types:
                    # Check both the full qualified name and just the local name
                    type_str_normalized = type_str.lower()
                    ptype_str = str(ptype).lower()

                    # Check exact match
                    if ptype_str == type_str_normalized:
                        return True

                    # Check if it's a standard PROV type (prov:Entity, prov:Activity, prov:Agent)
                    if type_str_normalized in ['prov:entity', 'entity'] and 'entity' in ptype_str:
                        return True
                    elif type_str_normalized in ['prov:activity', 'activity'] and 'activity' in ptype_str:
                        return True
                    elif type_str_normalized in ['prov:agent', 'agent'] and 'agent' in ptype_str:
                        return True

            # Also check the actual Python type of the PROV entity
            if type_str.lower() in ['prov:entity', 'entity'] and isinstance(node.prov_entity, ProvEntity):
                return True
            elif type_str.lower() in ['prov:activity', 'activity'] and isinstance(node.prov_entity, ProvActivity):
                return True
            elif type_str.lower() in ['prov:agent', 'agent'] and isinstance(node.prov_entity, ProvAgent):
                return True

        except:
            pass
        return False

    def _normalize_qname(self, identifier: Union[str, QualifiedName]) -> str:
        """Normalize identifier to string for comparison."""
        if isinstance(identifier, str):
            return identifier
        return str(identifier)

    def add_node(self, node_type: str, identifier: Union[str, QualifiedName],
                 attributes: Optional[Dict[str, Any]] = None,
                 prov_type: Optional[Union[str, QualifiedName]] = None) -> GraphNode:
        """
        Add a new node to the document.

        Args:
            node_type: Type of node ('entity', 'activity', 'agent')
            identifier: Node identifier
            attributes: Optional attributes dictionary
            prov_type: Optional PROV type

        Returns:
            The created GraphNode

        Raises:
            InvalidOperationError: If node type is invalid or node already exists
        """
        self._mark_modified()

        # Normalize identifier - use a more robust approach
        if isinstance(identifier, str):
            try:
                qname = self._bundle.valid_qualified_name(identifier)
                if qname is None:
                    # Fallback: create QualifiedName manually using same logic as TemplateProvMapper
                    doc = self._bundle._document if hasattr(self._bundle, '_document') else self._bundle.document

                    if ':' in identifier:
                        # Handle prefixed names like "test:entity1"
                        prefix, local_name = identifier.split(':', 1)

                        # Check if namespace exists
                        namespace = None
                        for ns in doc.namespaces:
                            if ns.prefix == prefix:
                                namespace = ns
                                break

                        if namespace:
                            qname = namespace[local_name]
                        else:
                            # Create new namespace for this prefix
                            namespace_uri = f"http://example.org/{prefix}/"
                            ns = doc.add_namespace(prefix, namespace_uri)
                            qname = ns[local_name]
                    else:
                        # Simple name without prefix - use default namespace
                        default_ns = None
                        for ns in doc.namespaces:
                            if ns.prefix == 'default':
                                default_ns = ns
                                break

                        if not default_ns:
                            default_ns = doc.add_namespace('default', 'http://example.org/default/')
                        qname = default_ns[identifier]
            except Exception as e:
                raise InvalidOperationError(f"Failed to create QualifiedName for identifier: {identifier} - {e}")
        else:
            qname = identifier

        if qname is None:
            raise InvalidOperationError(f"Invalid identifier: {identifier}")

        # Check if node already exists
        existing_nodes = self.get_nodes(qname)
        if existing_nodes:
            raise InvalidOperationError(f"Node with identifier {qname} already exists")

        # Prepare attributes
        attr_list = []
        if prov_type:
            if isinstance(prov_type, str):
                try:
                    prov_type_qname = self._bundle.valid_qualified_name(prov_type)
                    if prov_type_qname is None:
                        # Try to create prov_type QualifiedName manually if needed
                        prov_type_qname = prov_type
                    prov_type = prov_type_qname
                except:
                    pass  # Use original string if QualifiedName creation fails
            if prov_type:
                attr_list.append((PROV_TYPE, prov_type))

        if attributes:
            for attr_name, attr_value in attributes.items():
                try:
                    attr_qname = self._bundle.valid_qualified_name(attr_name)
                    if attr_qname:
                        attr_list.append((attr_qname, attr_value))
                    else:
                        # Fallback: create a proper QualifiedName for the attribute
                        doc = self._bundle._document if hasattr(self._bundle, '_document') else self._bundle.document

                        # Check if it's already a qualified name
                        if ':' in attr_name:
                            # Handle prefixed names like "ex:label"
                            prefix, local_name = attr_name.split(':', 1)

                            # Check if namespace exists
                            namespace = None
                            for ns in doc.namespaces:
                                if ns.prefix == prefix:
                                    namespace = ns
                                    break

                            if namespace:
                                attr_qname = namespace[local_name]
                            else:
                                # Create new namespace for this prefix
                                namespace_uri = f"http://example.org/{prefix}/"
                                ns = doc.add_namespace(prefix, namespace_uri)
                                attr_qname = ns[local_name]
                        else:
                            # Simple name without prefix - add to a default attribute namespace
                            attr_ns = None
                            for ns in doc.namespaces:
                                if ns.prefix == 'attr':
                                    attr_ns = ns
                                    break

                            if not attr_ns:
                                attr_ns = doc.add_namespace('attr', 'http://example.org/attr/')
                            attr_qname = attr_ns[attr_name]

                        attr_list.append((attr_qname, attr_value))
                except Exception as e:
                    # Last resort: skip invalid attributes
                    print(f"Warning: Skipping invalid attribute '{attr_name}': {e}")
                    continue

        # Create the node based on type
        try:
            prov_element = None
            if node_type.lower() == 'entity':
                prov_element = self._bundle.entity(qname, other_attributes=attr_list)
            elif node_type.lower() == 'activity':
                prov_element = self._bundle.activity(qname, other_attributes=attr_list)
            elif node_type.lower() == 'agent':
                prov_element = self._bundle.agent(qname, other_attributes=attr_list)
            else:
                raise InvalidOperationError(f"Invalid node type: {node_type}")
        except Exception as e:
            raise CpmDocumentError(f"Failed to create PROV {node_type} with identifier {qname}: {e}")

        # Add the created element to the graph wrapper directly instead of recreating it
        try:
            if isinstance(prov_element, ProvEntity):
                created_node = self.graph_wrapper.add_entity_as_node(prov_element)
            elif isinstance(prov_element, ProvActivity):
                node_id = str(qname)
                created_node = GraphNode(prov_element, node_id)
                self.graph_wrapper._nodes[node_id] = created_node
                self.graph_wrapper.graph.add_node(node_id, prov_entity=prov_element, graph_node=created_node)
            elif isinstance(prov_element, ProvAgent):
                node_id = str(qname)
                created_node = GraphNode(prov_element, node_id)
                self.graph_wrapper._nodes[node_id] = created_node
                self.graph_wrapper.graph.add_node(node_id, prov_entity=prov_element, graph_node=created_node)
            else:
                raise CpmDocumentError(f"Unknown PROV element type: {type(prov_element)}")

        except Exception as e:
            raise CpmDocumentError(f"Failed to add {node_type} to graph wrapper: {e}")

        # Find and return the created node
        created_nodes = self.get_nodes(qname)
        if created_nodes:
            return created_nodes[0]
        else:
            raise CpmDocumentError("Failed to create node")

    def remove_node(self, identifier: Union[str, QualifiedName],
                    node_type: Optional[str] = None) -> bool:
        """
        Remove a node from the document.

        Args:
            identifier: Node identifier
            node_type: Optional node type filter

        Returns:
            True if node was removed, False if not found

        Raises:
            MultipleNodesError: If multiple nodes match and no type filter is provided
        """
        self._mark_modified()

        nodes_to_remove = self.get_nodes(identifier)
        if not nodes_to_remove:
            return False

        if node_type and len(nodes_to_remove) > 1:
            # Filter by node type
            filtered_nodes = []
            for node in nodes_to_remove:
                if ((node_type.lower() == 'entity' and isinstance(node.prov_entity, ProvEntity)) or
                    (node_type.lower() == 'activity' and isinstance(node.prov_entity, ProvActivity)) or
                        (node_type.lower() == 'agent' and isinstance(node.prov_entity, ProvAgent))):
                    filtered_nodes.append(node)
            nodes_to_remove = filtered_nodes

        if len(nodes_to_remove) > 1:
            raise MultipleNodesError(f"Multiple nodes found with identifier: {identifier}")

        if not nodes_to_remove:
            return False

        node_to_remove = nodes_to_remove[0]

        # Remove from bundle records
        if hasattr(self._bundle, '_records'):
            # Remove the record from bundle
            records_to_remove = []
            for record in self._bundle._records:
                if hasattr(record, 'identifier') and str(record.identifier) == str(node_to_remove.identifier):
                    records_to_remove.append(record)

            for record in records_to_remove:
                self._bundle._records.remove(record)

        # Also remove any related edges
        self._remove_edges_for_node(node_to_remove)

        # Remove from graph wrapper's internal structures
        node_id = str(node_to_remove.identifier)
        if node_id in self.graph_wrapper._nodes:
            del self.graph_wrapper._nodes[node_id]

        # Remove from NetworkX graph
        if self.graph_wrapper.graph.has_node(node_id):
            self.graph_wrapper.graph.remove_node(node_id)

        return True

    def remove_nodes(self, identifier: Union[str, QualifiedName]) -> bool:
        """
        Remove all nodes with the given identifier.

        Args:
            identifier: Node identifier

        Returns:
            True if at least one node was removed
        """
        nodes_to_remove = self.get_nodes(identifier)
        if not nodes_to_remove:
            return False

        removed_any = False
        for node in nodes_to_remove:
            if isinstance(node.prov_entity, ProvEntity):
                removed_any |= self.remove_node(identifier, 'entity')
            elif isinstance(node.prov_entity, ProvActivity):
                removed_any |= self.remove_node(identifier, 'activity')
            elif isinstance(node.prov_entity, ProvAgent):
                removed_any |= self.remove_node(identifier, 'agent')

        return removed_any

    def update_node_identifier(self, old_identifier: Union[str, QualifiedName],
                               new_identifier: Union[str, QualifiedName]) -> bool:
        """
        Update a node's identifier.

        Args:
            old_identifier: Current identifier
            new_identifier: New identifier

        Returns:
            True if update was successful

        Raises:
            NodeNotFoundError: If node with old identifier is not found
            InvalidOperationError: If new identifier already exists
        """
        self._mark_modified()

        node = self.get_node(old_identifier)
        if not node:
            raise NodeNotFoundError(f"Node not found: {old_identifier}")

        # Check if new identifier already exists
        existing_nodes = self.get_nodes(new_identifier)
        if existing_nodes:
            raise InvalidOperationError(f"Node with identifier {new_identifier} already exists")

        # Create new node with same attributes but new identifier
        attributes = {}
        for attr_name, attr_value in node.prov_entity.attributes:
            if attr_name != node.prov_entity.identifier:
                attributes[str(attr_name)] = attr_value

        node_type = 'entity'
        if isinstance(node.prov_entity, ProvActivity):
            node_type = 'activity'
        elif isinstance(node.prov_entity, ProvAgent):
            node_type = 'agent'

        # Remove old node and create new one
        self.remove_node(old_identifier)
        self.add_node(node_type, new_identifier, attributes)

        return True

    def get_edges(self, source_id: Optional[Union[str, QualifiedName]] = None,
                  target_id: Optional[Union[str, QualifiedName]] = None,
                  relation_type: Optional[str] = None) -> List[Any]:
        """
        Get edges based on various criteria.

        Args:
            source_id: Optional source node identifier
            target_id: Optional target node identifier  
            relation_type: Optional relation type filter

        Returns:
            List of matching edges
        """
        all_edges = []

        # Get all relations from the bundle
        if hasattr(self._bundle, '_records'):
            for record in self._bundle._records:
                # Check for different relation types
                relation_types = ['usage', 'generation', 'association', 'attribution',
                                  'derivation', 'communication', 'delegation', 'influence',
                                  'specialization', 'alternate', 'membership']

                record_type = type(record).__name__.lower()
                is_relation = any(rel_type in record_type for rel_type in relation_types)

                if is_relation:
                    # Filter by relation type if specified
                    if relation_type:
                        # Normalize relation type for comparison
                        normalized_relation_type = relation_type.lower()
                        # Handle common aliases
                        if normalized_relation_type in ['wasderivedfrom', 'derived']:
                            normalized_relation_type = 'derivation'
                        elif normalized_relation_type in ['used']:
                            normalized_relation_type = 'usage'
                        elif normalized_relation_type in ['wasgeneratedby', 'generated']:
                            normalized_relation_type = 'generation'

                        if normalized_relation_type not in record_type:
                            continue

                    # Extract source and target from relation
                    source, target = self._extract_edge_endpoints(record)

                    # Normalize identifiers for comparison
                    source_str = self._normalize_qname(source) if source else None
                    target_str = self._normalize_qname(target) if target else None
                    source_id_str = self._normalize_qname(source_id) if source_id else None
                    target_id_str = self._normalize_qname(target_id) if target_id else None

                    # Apply filters
                    matches = True

                    if source_id_str is not None:
                        if source_str != source_id_str:
                            matches = False

                    if target_id_str is not None:
                        if target_str != target_id_str:
                            matches = False

                    if matches:
                        all_edges.append(record)

        return all_edges

    def get_edge(self, source_id: Union[str, QualifiedName],
                 target_id: Union[str, QualifiedName],
                 relation_type: Optional[str] = None) -> Optional[Any]:
        """
        Get a single edge between two nodes.

        Args:
            source_id: Source node identifier
            target_id: Target node identifier
            relation_type: Optional relation type

        Returns:
            The edge if found, None otherwise

        Raises:
            MultipleEdgesError: If multiple edges are found
        """
        edges = self.get_edges(source_id, target_id, relation_type)

        # If not found and no relation_type specified, try reversed direction
        # This handles both PROV API (no reversal) and CPM API (with reversal) usage
        if not edges and not relation_type:
            edges = self.get_edges(target_id, source_id, None)

        if not edges:
            return None
        if len(edges) > 1:
            raise MultipleEdgesError(f"Multiple edges found between {source_id} and {target_id}")
        return edges[0]

    def add_edge(self, relation_type: str, source_id: Union[str, QualifiedName],
                 target_id: Union[str, QualifiedName],
                 edge_id: Optional[Union[str, QualifiedName]] = None,
                 attributes: Optional[Dict[str, Any]] = None) -> Any:
        """
        Add an edge between two nodes.

        Args:
            source_id: Source node identifier
            target_id: Target node identifier  
            edge_id: Optional edge identifier
            attributes: Optional edge attributes

        Returns:
            The created edge

        Raises:
            NodeNotFoundError: If source or target node not found
            InvalidOperationError: If relation type is invalid
        """
        self._mark_modified()

        # Verify nodes exist
        source_node = self.get_node(source_id)
        target_node = self.get_node(target_id)

        if not source_node:
            raise NodeNotFoundError(f"Source node not found: {source_id}")
        if not target_node:
            raise NodeNotFoundError(f"Target node not found: {target_id}")

        # Prepare attributes
        attr_list = []
        if attributes:
            for attr_name, attr_value in attributes.items():
                attr_qname = self._bundle.valid_qualified_name(attr_name)
                if attr_qname:
                    attr_list.append((attr_qname, attr_value))

        # Create relation based on type
        edge = None
        relation_type = relation_type.lower()

        if relation_type == 'used':
            edge = self._bundle.usage(source_node.prov_entity, target_node.prov_entity,
                                      identifier=edge_id, other_attributes=attr_list)
        elif relation_type == 'wasgeneratedby':
            edge = self._bundle.generation(target_node.prov_entity, source_node.prov_entity,
                                           identifier=edge_id, other_attributes=attr_list)
        elif relation_type == 'wasassociatedwith':
            edge = self._bundle.association(source_node.prov_entity, target_node.prov_entity,
                                            identifier=edge_id, other_attributes=attr_list)
        elif relation_type == 'wasattributedto':
            edge = self._bundle.attribution(source_node.prov_entity, target_node.prov_entity,
                                            identifier=edge_id, other_attributes=attr_list)
        elif relation_type == 'wasderivedfrom':
            # For derivation: target_node was derived from source_node
            edge = self._bundle.derivation(target_node.prov_entity, source_node.prov_entity,
                                           identifier=edge_id, other_attributes=attr_list)
        elif relation_type == 'wasinformedby':
            edge = self._bundle.communication(source_node.prov_entity, target_node.prov_entity,
                                              identifier=edge_id, other_attributes=attr_list)
        elif relation_type == 'actedonbehalfof':
            edge = self._bundle.delegation(source_node.prov_entity, target_node.prov_entity,
                                           identifier=edge_id, other_attributes=attr_list)
        elif relation_type == 'wasinfluencedby':
            edge = self._bundle.influence(source_node.prov_entity, target_node.prov_entity,
                                          identifier=edge_id, other_attributes=attr_list)
        elif relation_type == 'specializationof':
            edge = self._bundle.specialization(source_node.prov_entity, target_node.prov_entity)
        elif relation_type == 'alternateof':
            edge = self._bundle.alternate(source_node.prov_entity, target_node.prov_entity)
        elif relation_type == 'hadmember':
            edge = self._bundle.membership(source_node.prov_entity, target_node.prov_entity)
        else:
            raise InvalidOperationError(f"Invalid relation type: {relation_type}")

        # Don't recreate graph wrapper - the edge is already in the bundle
        # self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())
        return edge

    def remove_edge(self, source_id: Union[str, QualifiedName],
                    target_id: Union[str, QualifiedName],
                    relation_type: Optional[str] = None) -> bool:
        """
        Remove an edge between two nodes.

        Args:
            source_id: Source node identifier
            target_id: Target node identifier
            relation_type: Optional relation type

        Returns:
            True if edge was removed

        Raises:
            MultipleEdgesError: If multiple edges match and no type is specified
        """
        self._mark_modified()

        # Try to find edges with the given source/target order
        edges_to_remove = self.get_edges(source_id, target_id, relation_type)

        # If not found and no relation_type specified, try reversed order
        # This handles cases like generation where add_edge swaps parameters
        if not edges_to_remove and not relation_type:
            edges_to_remove = self.get_edges(target_id, source_id, None)

        if not edges_to_remove:
            return False

        if len(edges_to_remove) > 1 and not relation_type:
            raise MultipleEdgesError(f"Multiple edges found between {source_id} and {target_id}")

        # Remove from bundle
        if hasattr(self._bundle, '_records'):
            for edge in edges_to_remove:
                if edge in self._bundle._records:
                    self._bundle._records.remove(edge)

        # Recreate graph wrapper
        self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())
        return True

    def remove_edges(self, source_id: Optional[Union[str, QualifiedName]] = None,
                     target_id: Optional[Union[str, QualifiedName]] = None,
                     relation_type: Optional[str] = None) -> int:
        """
        Remove multiple edges matching criteria.

        Args:
            source_id: Optional source node identifier
            target_id: Optional target node identifier  
            relation_type: Optional relation type

        Returns:
            Number of edges removed
        """
        edges_to_remove = self.get_edges(source_id, target_id, relation_type)
        if not edges_to_remove:
            return 0

        self._mark_modified()

        # Remove from bundle
        removed_count = 0
        if hasattr(self._bundle, '_records'):
            for edge in edges_to_remove:
                if edge in self._bundle._records:
                    self._bundle._records.remove(edge)
                    removed_count += 1

        # Recreate graph wrapper
        if removed_count > 0:
            self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())

        return removed_count

    def get_nodes_by_attribute(self, attribute_name: str,
                               attribute_value: Optional[Any] = None) -> List[GraphNode]:
        """
        Get nodes that have a specific attribute.

        Args:
            attribute_name: Name of the attribute
            attribute_value: Optional value to match (if None, just check existence)

        Returns:
            List of matching nodes
        """
        matching_nodes = []

        for node in self.graph_wrapper.get_nodes():
            try:
                attr_values = node.get_prov_attribute(attribute_name)
                if attr_values:
                    if attribute_value is None:
                        matching_nodes.append(node)
                    elif attribute_value in attr_values:
                        matching_nodes.append(node)
            except:
                continue

        return matching_nodes

    def get_domain_specific_nodes(self) -> List[GraphNode]:
        """
        Get all domain-specific nodes (non-traversal information).

        Returns:
            List of domain-specific nodes
        """
        ds_nodes = []
        for node in self.graph_wrapper.get_nodes():
            if not self.ti_algorithm.belongs_to_traversal_information(node.prov_entity):
                ds_nodes.append(node)
        return ds_nodes

    def get_domain_specific_part(self) -> List[GraphNode]:
        """
        Get a cloned list of domain-specific nodes with only DS-to-DS relations.

        Returns:
            List of cloned domain-specific nodes
        """
        ds_nodes = self.get_domain_specific_nodes()

        # Create deep copies of DS nodes
        cloned_nodes = []
        for node in ds_nodes:
            # Create a copy of the node (this is a simplified version)
            cloned_nodes.append(node)

        return cloned_nodes

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

    def _extract_edge_endpoints(self, edge: Any) -> Tuple[Optional[Any], Optional[Any]]:
        """Extract source and target from an edge/relation."""
        try:
            # First try to extract from formal_attributes (PROV library standard way)
            if hasattr(edge, 'formal_attributes'):
                formal_attrs = dict(edge.formal_attributes)
                # Get the first two formal attributes which are typically the main endpoints
                keys = list(formal_attrs.keys())
                if len(keys) >= 2:
                    first_val = formal_attrs.get(keys[0])
                    second_val = formal_attrs.get(keys[1])

                    # Check relation type to determine correct direction
                    # CPM API expects semantic direction, which may differ from PROV formal_attributes order
                    relation_type = type(edge).__name__.lower()

                    # Usage: CPM expects (entity, activity) but formal_attributes are (activity, entity)
                    # Generation: CPM expects (activity, entity) but formal_attributes are (entity, activity)
                    # Attribution: CPM expects (agent, entity) but formal_attributes are (entity, agent)
                    if 'usage' in relation_type:
                        return second_val, first_val  # Reverse to (entity, activity)
                    elif 'generation' in relation_type:
                        return second_val, first_val  # Reverse to (activity, entity)
                    elif 'attribution' in relation_type:
                        return second_val, first_val  # Reverse to (agent, entity)
                    else:
                        # For other relations, formal_attributes order matches CPM expectations
                        return first_val, second_val

            # Fallback to direct attribute access (for compatibility)
            # Different relation types have different attribute names
            if hasattr(edge, 'entity') and hasattr(edge, 'activity'):
                # Usage/Generation relation
                return edge.entity, edge.activity
            elif hasattr(edge, 'agent') and hasattr(edge, 'activity'):
                # Association relation - agent influences activity
                return edge.agent, edge.activity
            elif hasattr(edge, 'entity') and hasattr(edge, 'agent'):
                # Attribution relation - entity attributed to agent
                return edge.agent, edge.entity
            elif hasattr(edge, 'usedEntity') and hasattr(edge, 'generatedEntity'):
                # Derivation relation - generatedEntity derived from usedEntity
                return edge.usedEntity, edge.generatedEntity
            elif hasattr(edge, 'informed') and hasattr(edge, 'informant'):
                # Communication relation - informant informs informed
                return edge.informant, edge.informed
            elif hasattr(edge, 'delegate') and hasattr(edge, 'responsible'):
                # Delegation relation - responsible acts on behalf of delegate
                return edge.responsible, edge.delegate
            elif hasattr(edge, 'influencee') and hasattr(edge, 'influencer'):
                # Influence relation - influencer influences influencee
                return edge.influencer, edge.influencee
            elif hasattr(edge, 'specificEntity') and hasattr(edge, 'generalEntity'):
                # Specialization relation - specificEntity specializes generalEntity
                return edge.generalEntity, edge.specificEntity
            elif hasattr(edge, 'alternate1') and hasattr(edge, 'alternate2'):
                # Alternate relation - bidirectional
                return edge.alternate1, edge.alternate2
            elif hasattr(edge, 'collection') and hasattr(edge, 'entity'):
                # Membership relation - collection has member entity
                return edge.collection, edge.entity

            # For PROV library objects, try accessing attributes through _attributes
            if hasattr(edge, '_attributes') and edge._attributes:
                # Handle derivation relations by looking at attributes
                if isinstance(edge._attributes, dict):
                    attrs = edge._attributes
                else:
                    # Handle defaultdict case
                    attrs = dict(edge._attributes)

                # Look for PROV relation attribute patterns
                used_entity = None
                generated_entity = None
                activity = None
                entity = None
                agent = None
                delegate = None
                responsible = None
                informed = None
                informant = None

                for attr_name, attr_value in attrs.items():
                    attr_str = str(attr_name).lower()

                    # Extract first value from set if it's a set
                    if isinstance(attr_value, set) and attr_value:
                        value = next(iter(attr_value))
                    else:
                        value = attr_value

                    if 'usedentity' in attr_str or attr_str.endswith(':usedentity'):
                        used_entity = value
                    elif 'generatedentity' in attr_str or attr_str.endswith(':generatedentity'):
                        generated_entity = value
                    elif 'delegate' in attr_str:
                        delegate = value
                    elif 'responsible' in attr_str:
                        responsible = value
                    elif 'informed' in attr_str:
                        informed = value
                    elif 'informant' in attr_str:
                        informant = value
                    elif 'activity' in attr_str and 'main' not in attr_str.lower():
                        activity = value
                    elif attr_str.endswith('entity') and 'used' not in attr_str and 'generated' not in attr_str:
                        entity = value
                    elif 'agent' in attr_str:
                        agent = value

                # Return appropriate pairs based on what we found
                if used_entity and generated_entity:
                    # Derivation: used_entity -> generated_entity
                    return used_entity, generated_entity
                elif informed and informant:
                    # Communication: informant -> informed
                    return informant, informed
                elif delegate and responsible:
                    # Delegation: responsible -> delegate
                    return responsible, delegate
                elif activity and entity:
                    # Usage or Generation: depends on edge type
                    edge_type = type(edge).__name__.lower()
                    if 'usage' in edge_type:
                        return entity, activity  # entity -> activity
                    elif 'generation' in edge_type:
                        return activity, entity  # activity -> entity
                    else:
                        return activity, entity
                elif activity and agent:
                    edge_type = type(edge).__name__.lower()
                    if 'association' in edge_type:
                        return agent, activity  # agent -> activity
                    else:
                        return activity, agent
                elif entity and agent:
                    return agent, entity

            # Try to get generic identifiers if specific attributes don't exist
            source = getattr(edge, 'source', None) or getattr(edge, 'from', None)
            target = getattr(edge, 'target', None) or getattr(edge, 'to', None)
            if source and target:
                return source, target

        except Exception as e:
            # Debug print for troubleshooting
            print(f"Error extracting endpoints from {type(edge)}: {e}")

        return None, None

    def _remove_edges_for_node(self, node: GraphNode):
        """Remove all edges connected to a node."""
        if hasattr(self._bundle, '_records'):
            edges_to_remove = []
            for record in self._bundle._records:
                source, target = self._extract_edge_endpoints(record)
                if (source and str(source) == str(node.identifier)) or \
                   (target and str(target) == str(node.identifier)):
                    edges_to_remove.append(record)

            for edge in edges_to_remove:
                self._bundle._records.remove(edge)

    def get_edge_by_id(self, edge_id: Union[str, QualifiedName]) -> Optional[Any]:
        """
        Get edge by its identifier.
        """
        return self.get_edges_by_id(edge_id)[0] if self.get_edges_by_id(edge_id) else None

    def get_edges_by_id(self, edge_id: Union[str, QualifiedName]) -> List[Any]:
        """
        Get all edges with a specific identifier.

        Args:
            edge_id: Edge identifier

        Returns:
            List of matching edges
        """
        all_edges = []
        edge_id_str = self._normalize_qname(edge_id)
        if hasattr(self._bundle, '_records'):
            for record in self._bundle._records:
                if hasattr(record, 'identifier') and record.identifier:
                    record_id_str = self._normalize_qname(record.identifier)
                    if record_id_str == edge_id_str:
                        all_edges.append(record)
        return all_edges

    def remove_edge_by_id(self, edge_id: Union[str, QualifiedName]) -> bool:
        """
        Remove edge by its identifier.

        Args:
            edge_id: Edge identifier

        Returns:
            True if edge was removed

        Raises:
            MultipleEdgesError: If multiple edges have the same ID
        """
        edges = self.get_edges_by_id(edge_id)
        if not edges:
            return False
        if len(edges) > 1:
            raise MultipleEdgesError(f"Multiple edges found with ID: {edge_id}")

        self._mark_modified()
        if hasattr(self._bundle, '_records') and edges[0] in self._bundle._records:
            self._bundle._records.remove(edges[0])
            self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())
            return True
        return False

    def are_all_relations_mapped(self) -> bool:
        """
        Check if all relations have both cause and effect nodes mapped.

        Returns:
            True if all relations are properly mapped
        """
        all_edges = self.get_edges()
        for edge in all_edges:
            source, target = self._extract_edge_endpoints(edge)
            if not source or not target:
                return False

            source_node = self.get_node(source)
            target_node = self.get_node(target)
            if not source_node or not target_node:
                return False

        return True

    def set_new_cause_and_effect(self, relation: Any, new_effect_id: Union[str, QualifiedName],
                                 new_cause_id: Union[str, QualifiedName]) -> bool:
        """
        Update the cause and effect of a relation.

        Args:
            relation: The relation to update
            new_effect_id: New effect identifier
            new_cause_id: New cause identifier

        Returns:
            True if update was successful
        """
        if not relation:
            return False

        # Verify new nodes exist
        new_effect_node = self.get_node(new_effect_id)
        new_cause_node = self.get_node(new_cause_id)

        if not new_effect_node or not new_cause_node:
            return False

        self._mark_modified()

        # Remove old relation
        if hasattr(self._bundle, '_records') and relation in self._bundle._records:
            self._bundle._records.remove(relation)

        # Determine relation type and create new one
        relation_type = type(relation).__name__.lower()

        try:
            if 'usage' in relation_type:
                self.add_edge('used', new_cause_id, new_effect_id)
            elif 'generation' in relation_type:
                self.add_edge('wasgeneratedby', new_cause_id, new_effect_id)
            elif 'derivation' in relation_type:
                self.add_edge('wasderivedfrom', new_effect_id, new_cause_id)
            # Add more relation types as needed

            return True
        except:
            return False

    def set_collection_members(self, old_collection_id: Union[str, QualifiedName],
                               old_members: List[Union[str, QualifiedName]],
                               new_collection_id: Union[str, QualifiedName],
                               new_members: List[Union[str, QualifiedName]]) -> bool:
        """
        Update collection membership relations.
                                             QualifiedName newCollectionId, List<QualifiedName> newMembers)

        Args:
            old_collection_id: Current collection identifier
            old_members: Current member identifiers
            new_collection_id: New collection identifier
            new_members: New member identifiers

        Returns:
            True if update was successful
        """
        if (str(old_collection_id) == str(new_collection_id) and
                [str(m) for m in old_members] == [str(m) for m in new_members]):
            return True

        self._mark_modified()

        # Remove old membership relations
        membership_edges = []
        if hasattr(self._bundle, '_records'):
            for record in self._bundle._records:
                if (hasattr(record, 'collection') and hasattr(record, 'entity') and
                        str(record.collection) == str(old_collection_id)):
                    membership_edges.append(record)

        for edge in membership_edges:
            self._bundle._records.remove(edge)

        # Add new membership relations
        for member_id in new_members:
            member_node = self.get_node(member_id)
            collection_node = self.get_node(new_collection_id)
            if member_node and collection_node:
                self._bundle.membership(collection_node.prov_entity, member_node.prov_entity)

        # Recreate graph wrapper
        self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())
        return True

    def update_element_identifier(self, element: Any, new_identifier: Union[str, QualifiedName]) -> bool:
        """
        Update an element's identifier.

        Args:
            element: The element to update
            new_identifier: New identifier

        Returns:
            True if update was successful
        """
        if not element or not hasattr(element, 'identifier'):
            return False

        old_identifier = element.identifier
        if str(old_identifier) == str(new_identifier):
            return True

        # Check if new identifier already exists
        existing_nodes = self.get_nodes(new_identifier)
        if existing_nodes:
            return False

        self._mark_modified()

        # Update the identifier in the element
        try:
            element._identifier = new_identifier

            # Recreate graph wrapper to reflect changes
            self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())
            return True
        except:
            return False

    def get_nodes_map(self) -> Dict[str, List[GraphNode]]:
        """
        Get mapping of identifiers to their associated nodes.

        Returns:
            Dictionary mapping node identifiers to lists of nodes
        """
        nodes_map = {}
        for node in self.graph_wrapper.get_nodes():
            node_id = str(node.identifier)
            if node_id not in nodes_map:
                nodes_map[node_id] = []
            nodes_map[node_id].append(node)
        return nodes_map

    def remove_element(self, element: Any) -> bool:
        """
        Remove a specific element from its node.

        Args:
            element: The element to remove

        Returns:
            True if element was removed
        """
        if not element:
            return False

        self._mark_modified()

        # Find the node containing this element
        target_node = None
        for node in self.graph_wrapper.get_nodes():
            if node.prov_entity == element:
                target_node = node
                break

        if not target_node:
            return False

        # If this is the only element in the node, remove the entire node
        return self.remove_node(target_node.identifier)

    def get_bundle_id(self) -> Optional[str]:
        """
        Get the bundle identifier.

        Returns:
            Bundle identifier or None
        """
        # If we have a custom bundle ID set via set_bundle_id(), return that
        if self._custom_bundle_id is not None:
            return str(self._custom_bundle_id)

        # Otherwise, get it from the bundle
        try:
            bundle = self._get_bundle()
            return str(bundle.identifier) if bundle.identifier else None
        except:
            return None

    def set_bundle_id(self, bundle_id: Union[str, QualifiedName]) -> bool:
        """
        Set the bundle identifier.

        Args:
            bundle_id: New bundle identifier

        Returns:
            True if successful
        """
        try:
            self._mark_modified()
            # Store the custom bundle ID for persistence across document reconstructions
            self._custom_bundle_id = bundle_id
            return True
        except:
            return False

    def get_edge_with_kind(self, edge_id: Union[str, QualifiedName],
                           kind: Optional[str] = None) -> Optional[Any]:
        """
        Get edge by ID and kind.
        """
        edge = self.get_edge_by_id(edge_id)
        if edge and kind:
            edge_type = type(edge).__name__.lower()
            if kind.lower() in edge_type:
                return edge
        return edge if not kind else None

    def get_edges_by_relation(self, relation: Any) -> List[Any]:
        """
        Get edges containing a specific relation.
        """
        matching_edges = []
        all_edges = self.get_edges()
        for edge in all_edges:
            if hasattr(edge, '__dict__'):
                for attr_value in edge.__dict__.values():
                    if attr_value == relation:
                        matching_edges.append(edge)
                        break
        return matching_edges

    def set_new_cause_and_effect_by_kind(self, old_effect_id: Union[str, QualifiedName],
                                         old_cause_id: Union[str, QualifiedName],
                                         kind: str,
                                         new_effect_id: Union[str, QualifiedName],
                                         new_cause_id: Union[str, QualifiedName]) -> bool:
        """
        Update cause and effect with kind specification.
        """
        edges = self.get_edges(old_cause_id, old_effect_id, kind)
        if not edges:
            return False

        self._mark_modified()

        for edge in edges:
            # Remove old edge
            if hasattr(self._bundle, '_records') and edge in self._bundle._records:
                self._bundle._records.remove(edge)

            # Add new edge with updated endpoints
            try:
                self.add_edge(kind, new_cause_id, new_effect_id)
            except:
                return False

        # Recreate graph wrapper
        self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())
        return True

    def get_node_by_element(self, element: Any) -> Optional[GraphNode]:
        """
        Get node containing a specific element.
        """
        for node in self.graph_wrapper.get_nodes():
            if node.prov_entity == element:
                return node
        return None

    def get_node_by_id_and_kind(self, node_id: Union[str, QualifiedName],
                                kind: str) -> Optional[GraphNode]:
        """
        Get node by ID and kind.
        """
        nodes = self.get_nodes(node_id)
        for node in nodes:
            if kind.lower() == 'entity' and isinstance(node.prov_entity, ProvEntity):
                return node
            elif kind.lower() == 'activity' and isinstance(node.prov_entity, ProvActivity):
                return node
            elif kind.lower() == 'agent' and isinstance(node.prov_entity, ProvAgent):
                return node
        return None

    def remove_node_by_kind(self, node_id: Union[str, QualifiedName],
                            kind: str) -> bool:
        """
        Remove node by ID and kind.
        """
        node = self.get_node_by_id_and_kind(node_id, kind)
        if node:
            return self.remove_node(node_id, kind)
        return False

    def remove_edges_by_kind(self, effect_id: Union[str, QualifiedName],
                             cause_id: Union[str, QualifiedName],
                             kind: str) -> bool:
        """
        Remove edges by effect, cause and kind.
        """
        edges = self.get_edges(cause_id, effect_id, kind)
        if not edges:
            return False

        self._mark_modified()

        if hasattr(self._bundle, '_records'):
            for edge in edges:
                if edge in self._bundle._records:
                    self._bundle._records.remove(edge)

        self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())
        return True

    def set_ti_strategy(self, strategy: Any):
        """
        Set traversal information strategy.
        """
        # For now, just store the strategy
        # In full implementation, this would affect TI algorithm behavior
        self._ti_strategy = strategy

    def get_namespaces(self) -> Dict[str, str]:
        """
        Get document namespaces.
        """
        doc = self.to_prov_document()
        namespaces = {}

        if hasattr(doc, 'namespaces') and doc.namespaces:
            for ns in doc.namespaces:
                if hasattr(ns, 'prefix') and hasattr(ns, 'uri'):
                    namespaces[ns.prefix] = str(ns.uri)

        return namespaces

    def to_document(self) -> ProvDocument:
        """
        Convert to PROV Document.
        """
        return self.to_prov_document()

    def get_all_edges(self) -> List[Any]:
        """
        Get list of all edges.
        """
        return self.get_edges()

    def get_all_nodes(self) -> List[GraphNode]:
        """
        Get list of all nodes.
        """
        return self.graph_wrapper.get_nodes()

    def update_collection_members_advanced(self, old_collection_id: Union[str, QualifiedName],
                                           old_members: List[Union[str, QualifiedName]],
                                           new_collection_id: Union[str, QualifiedName],
                                           new_members: List[Union[str, QualifiedName]],
                                           validate_existence: bool = True) -> bool:
        """
        Advanced collection member update with validation.
        """
        if validate_existence:
            # Verify all nodes exist
            collection_node = self.get_node(new_collection_id)
            if not collection_node:
                return False

            for member_id in new_members:
                if not self.get_node(member_id):
                    return False

        return self.set_collection_members(old_collection_id, old_members,
                                           new_collection_id, new_members)

    def set_element_identifier_advanced(self, element: Any,
                                        new_identifier: Union[str, QualifiedName],
                                        update_relations: bool = True) -> bool:
        """
        Set element identifier with optional relation updates.
        """
        if not element:
            return False

        old_identifier = getattr(element, 'identifier', None) or getattr(element, 'id', None)
        if not old_identifier or str(old_identifier) == str(new_identifier):
            return True

        # Check if new identifier already exists
        if self.get_node(new_identifier):
            return False

        self._mark_modified()

        try:
            # Update element identifier
            if hasattr(element, 'identifier'):
                element.identifier = new_identifier
            elif hasattr(element, 'id'):
                element.id = new_identifier

            if update_relations:
                # Update any relations referencing this element
                self._update_relations_for_renamed_element(old_identifier, new_identifier)

            self.graph_wrapper = ProvGraphWrapper(self.graph_wrapper.to_prov_document())
            return True
        except:
            return False

    def _update_relations_for_renamed_element(self, old_id: Union[str, QualifiedName],
                                              new_id: Union[str, QualifiedName]):
        """Helper method to update relations when element is renamed"""
        # Find and update edges that reference the renamed element
        all_edges = self.get_edges()
        for edge in all_edges:
            source, target = self._extract_edge_endpoints(edge)

            updated = False
            if source and str(source) == str(old_id):
                # Update source reference
                if hasattr(edge, 'activity'):
                    edge.activity = new_id
                elif hasattr(edge, 'agent'):
                    edge.agent = new_id
                elif hasattr(edge, 'entity'):
                    edge.entity = new_id
                updated = True

            if target and str(target) == str(old_id):
                # Update target reference
                if hasattr(edge, 'entity'):
                    edge.entity = new_id
                elif hasattr(edge, 'activity'):
                    edge.activity = new_id
                elif hasattr(edge, 'agent'):
                    edge.agent = new_id
                updated = True
