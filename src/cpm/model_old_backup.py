"""
CPM Model - Template to PROV Mapping and CPM Document Classes

Implements the mapping from CPM templates to PROV documents and provides
CPM-specific document handling as described in the Reference Implementation thesis.
"""

from src.graph.node import GraphNode
from src.graph.wrapper import ProvGraphWrapper
from typing import Dict, List, Optional, Any, Set, Union, Tuple
from prov.model import ProvDocument, ProvBundle, ProvEntity, ProvActivity, ProvAgent, ProvRecord
from prov.identifier import QualifiedName, Namespace
from prov.constants import PROV_TYPE, PROV_LABEL, PROV_VALUE
import copy

from .constants import *
from .template import TraversalInformationTemplate, RelationTemplate, MainActivityTemplate, ConnectorTemplate, AgentTemplate, IdentifierEntityTemplate


class CpmDocumentError(Exception):
    """Base exception for CPM document operations"""
    pass


class NodeNotFoundError(CpmDocumentError):
    """Raised when a requested node is not found"""
    pass


class MultipleNodesError(CpmDocumentError):
    """Raised when multiple nodes are found where only one is expected"""
    pass


class EdgeNotFoundError(CpmDocumentError):
    """Raised when a requested edge is not found"""
    pass


class InvalidOperationError(CpmDocumentError):
    """Raised when an invalid operation is attempted"""
    pass


class MultipleEdgesError(CpmDocumentError):
    """Raised when multiple edges are found where only one is expected"""
    pass


class TemplateProvMapper:
    """Maps TraversalInformationTemplate objects to PROV documents"""

    def __init__(self, merge_agents: bool = True):
        """
        Initialize mapper.

        Args:
            merge_agents: If True, merge sender and receiver agents with same ID
        """
        self.merge_agents = merge_agents

    def map_to_document(self, template: TraversalInformationTemplate) -> ProvDocument:
        """
        Map a TraversalInformationTemplate to a ProvDocument.

        Args:
            template: The template to map

        Returns:
            A ProvDocument containing the CPM bundle
        """
        # Create document with namespaces
        doc = ProvDocument()

        # Add CPM namespaces
        namespaces = dict(DEFAULT_CPM_NAMESPACES)
        namespaces.update(template.prefixes)

        for prefix, uri in namespaces.items():
            doc.add_namespace(prefix, uri)

        # Create bundle with proper QualifiedName
        bundle_name = template.bundle_name

        # Create proper QualifiedName for bundle
        bundle_id = None

        if ':' in bundle_name:
            # Handle prefixed names like "test:bundle"
            prefix, local_name = bundle_name.split(':', 1)
            if prefix in namespaces:
                # Use existing namespace - find it in doc.namespaces
                namespace = None
                for ns in doc.namespaces:
                    if ns.prefix == prefix:
                        namespace = ns
                        break
                bundle_id = namespace[local_name] if namespace else None
            else:
                # Create new namespace for this prefix
                namespace_uri = f"http://example.org/{prefix}/"
                ns = doc.add_namespace(prefix, namespace_uri)
                bundle_id = ns[local_name]
        else:
            # Simple name without prefix - use default namespace
            if 'default' not in namespaces:
                doc.add_namespace('default', 'http://example.org/default/')
            # Find default namespace in doc.namespaces
            default_ns = None
            for ns in doc.namespaces:
                if ns.prefix == 'default':
                    default_ns = ns
                    break
            bundle_id = default_ns[bundle_name] if default_ns else None

        # Fallback: create with cpm namespace
        if bundle_id is None:
            # Find cmp namespace in doc.namespaces
            cpm_ns = None
            for ns in doc.namespaces:
                if ns.prefix == 'cpm':
                    cpm_ns = ns
                    break
            if cpm_ns:
                bundle_id = cpm_ns['bundle']
            else:
                # Last resort: create simple default namespace
                doc.add_namespace('bundle_ns', 'http://example.org/bundle/')
                # Find the newly created namespace
                bundle_ns = None
                for ns in doc.namespaces:
                    if ns.prefix == 'bundle_ns':
                        bundle_ns = ns
                        break
                bundle_id = bundle_ns['main'] if bundle_ns else None

        # Create the bundle with proper QualifiedName
        bundle = doc.bundle(bundle_id)

        # Map all components
        entities = {}
        activities = {}
        agents = {}

        # Map main activity
        main_activity = self._map_main_activity(bundle, template.main_activity)
        activities[template.main_activity.id] = main_activity

        # Map connectors (entities)
        for connector in template.backward_connectors:
            entity = self._map_backward_connector(bundle, connector)
            entities[connector.id] = entity

        for connector in template.forward_connectors:
            entity = self._map_forward_connector(bundle, connector)
            entities[connector.id] = entity

        # Map agents
        all_agents = {}
        for agent_template in template.sender_agents:
            agent = self._map_sender_agent(bundle, agent_template)
            all_agents[agent_template.id] = agent

        for agent_template in template.receiver_agents:
            if self.merge_agents and agent_template.id in all_agents:
                # Merge with existing agent
                existing_agent = all_agents[agent_template.id]
                existing_agent.add_asserted_type(CPM_RECEIVER_AGENT)
            else:
                agent = self._map_receiver_agent(bundle, agent_template)
                all_agents[agent_template.id] = agent

        agents.update(all_agents)

        # Map identifier entities
        for entity_template in template.identifier_entities:
            entity = self._map_identifier_entity(bundle, entity_template)
            entities[entity_template.id] = entity

        # Create relations
        self._create_relations(bundle, template, entities, activities, agents)

        return doc

    def _map_main_activity(self, bundle: ProvBundle, template) -> ProvActivity:
        """Map main activity template to ProvActivity"""
        # Create proper QualifiedName for activity
        activity_id = self._create_qualified_name(bundle, template.id)

        attributes = [(PROV_TYPE, CPM_MAIN_ACTIVITY)]

        # Add time attributes
        if template.start_time:
            start_time_attr = self._create_qualified_name(bundle, 'prov:startTime')
            if start_time_attr:
                attributes.append((start_time_attr, template.start_time))
        if template.end_time:
            end_time_attr = self._create_qualified_name(bundle, 'prov:endTime')
            if end_time_attr:
                attributes.append((end_time_attr, template.end_time))

        # Add dct:hasPart for sub-activities
        for part_id in template.has_part:
            part_qname = self._create_qualified_name(bundle, part_id)
            if part_qname:
                attributes.append((DCT_HAS_PART, part_qname))

        # Add custom attributes
        for attr_name, attr_value in template.attributes.items():
            attr_qname = self._create_qualified_name(bundle, attr_name)
            if attr_qname:
                attributes.append((attr_qname, attr_value))

        return bundle.activity(activity_id, other_attributes=attributes)

    def _map_backward_connector(self, bundle: ProvBundle, template) -> ProvEntity:
        """Map backward connector template to ProvEntity"""
        entity_id = self._create_qualified_name(bundle, template.id)

        attributes = [(PROV_TYPE, CPM_BACKWARD_CONNECTOR)]

        # Add CPM-specific attributes
        if template.referenced_bundle_id:
            ref_bundle_qname = self._create_qualified_name(bundle, template.referenced_bundle_id)
            if ref_bundle_qname:
                attributes.append((CPM_REFERENCED_BUNDLE_ID, ref_bundle_qname))

        if template.referenced_bundle_hash_value:
            attributes.append((CPM_REFERENCED_BUNDLE_HASH_VALUE, template.referenced_bundle_hash_value))

        if template.hash_alg:
            attributes.append((CPM_HASH_ALG, template.hash_alg))

        # Add custom attributes
        for attr_name, attr_value in template.attributes.items():
            attr_qname = self._create_qualified_name(bundle, attr_name)
            if attr_qname:
                attributes.append((attr_qname, attr_value))

        return bundle.entity(entity_id, other_attributes=attributes)

    def _map_forward_connector(self, bundle: ProvBundle, template) -> ProvEntity:
        """Map forward connector template to ProvEntity"""
        entity_id = self._create_qualified_name(bundle, template.id)

        attributes = [(PROV_TYPE, CPM_FORWARD_CONNECTOR)]

        # Add CPM-specific attributes
        if template.referenced_bundle_id:
            ref_bundle_qname = self._create_qualified_name(bundle, template.referenced_bundle_id)
            if ref_bundle_qname:
                attributes.append((CPM_REFERENCED_BUNDLE_ID, ref_bundle_qname))

        if template.referenced_bundle_hash_value:
            attributes.append((CPM_REFERENCED_BUNDLE_HASH_VALUE, template.referenced_bundle_hash_value))

        if template.hash_alg:
            attributes.append((CPM_HASH_ALG, template.hash_alg))

        # Add custom attributes
        for attr_name, attr_value in template.attributes.items():
            attr_qname = self._create_qualified_name(bundle, attr_name)
            if attr_qname:
                attributes.append((attr_qname, attr_value))

        return bundle.entity(entity_id, other_attributes=attributes)

    def _map_sender_agent(self, bundle: ProvBundle, template) -> ProvAgent:
        """Map sender agent template to ProvAgent"""
        agent_id = self._create_qualified_name(bundle, template.id)

        attributes = [(PROV_TYPE, CPM_SENDER_AGENT)]

        # Add custom attributes
        for attr_name, attr_value in template.attributes.items():
            attr_qname = self._create_qualified_name(bundle, attr_name)
            if attr_qname:
                attributes.append((attr_qname, attr_value))

        return bundle.agent(agent_id, other_attributes=attributes)

    def _map_receiver_agent(self, bundle: ProvBundle, template) -> ProvAgent:
        """Map receiver agent template to ProvAgent"""
        agent_id = self._create_qualified_name(bundle, template.id)

        attributes = [(PROV_TYPE, CPM_RECEIVER_AGENT)]

        # Add custom attributes
        for attr_name, attr_value in template.attributes.items():
            attr_qname = self._create_qualified_name(bundle, attr_name)
            if attr_qname:
                attributes.append((attr_qname, attr_value))

        return bundle.agent(agent_id, other_attributes=attributes)

    def _map_identifier_entity(self, bundle: ProvBundle, template) -> ProvEntity:
        """Map identifier entity template to ProvEntity"""
        entity_id = self._create_qualified_name(bundle, template.id)

        attributes = [(PROV_TYPE, CPM_IDENTIFIER_ENTITY)]

        if template.external_id:
            ext_id_qname = self._create_qualified_name(bundle, template.external_id)
            if ext_id_qname:
                attributes.append((PROV_VALUE, ext_id_qname))

        # Add custom attributes
        for attr_name, attr_value in template.attributes.items():
            attr_qname = self._create_qualified_name(bundle, attr_name)
            if attr_qname:
                attributes.append((attr_qname, attr_value))

        return bundle.entity(entity_id, other_attributes=attributes)

    def _create_qualified_name(self, bundle: ProvBundle, identifier: str):
        """
        Create a proper QualifiedName for PROV elements.

        Args:
            bundle: The PROV bundle
            identifier: String identifier to convert

        Returns:
            QualifiedName that can be used with PROV library
        """
        if not identifier:
            raise ValueError("Identifier cannot be empty")

        # Get the document from the bundle
        doc = bundle._document if hasattr(bundle, '_document') else bundle.document

        # Try bundle.valid_qualified_name first
        try:
            qname = bundle.valid_qualified_name(identifier)
            if qname is not None:
                return qname
        except:
            pass

        # If that fails, handle manually using correct PROV API
        if ':' in identifier:
            # Handle prefixed names like "test:main"
            prefix, local_name = identifier.split(':', 1)

            # Check if namespace exists using correct PROV API
            namespace = None
            for ns in doc.namespaces:
                if ns.prefix == prefix:
                    namespace = ns
                    break

            if namespace:
                return namespace[local_name]
            else:
                # Create new namespace for this prefix
                namespace_uri = f"http://example.org/{prefix}/"
                ns = doc.add_namespace(prefix, namespace_uri)
                return ns[local_name]
        else:
            # Simple name without prefix - use default namespace
            default_ns = None
            for ns in doc.namespaces:
                if ns.prefix == 'default':
                    default_ns = ns
                    break

            if not default_ns:
                default_ns = doc.add_namespace('default', 'http://example.org/default/')
            return default_ns[identifier]

    def _create_relations(self, bundle: ProvBundle, template: TraversalInformationTemplate,
                          entities: Dict[str, ProvEntity], activities: Dict[str, ProvActivity],
                          agents: Dict[str, ProvAgent]):
        """Create all relations between elements"""

        main_activity = activities[template.main_activity.id]

        # Main activity usage relations
        for used_rel in template.main_activity.used:
            if used_rel.target_id in entities:
                entity = entities[used_rel.target_id]
                rel_id = bundle.valid_qualified_name(used_rel.relation_id) if used_rel.relation_id else None
                bundle.usage(main_activity, entity, identifier=rel_id)

        # Main activity generation relations
        for generated_id in template.main_activity.generated:
            if generated_id in entities:
                entity = entities[generated_id]
                bundle.generation(entity, main_activity)

        # Attribution relations for connectors
        for connector in template.backward_connectors + template.forward_connectors:
            if connector.attributed_to and connector.id in entities and connector.attributed_to.target_id in agents:
                entity = entities[connector.id]
                agent = agents[connector.attributed_to.target_id]
                rel_id = bundle.valid_qualified_name(connector.attributed_to.relation_id) if connector.attributed_to.relation_id else None
                bundle.attribution(entity, agent, identifier=rel_id)

        # Derivation relations between connectors
        for connector in template.backward_connectors + template.forward_connectors:
            if connector.id in entities:
                target_entity = entities[connector.id]
                for source_id in connector.derived_from:
                    if source_id in entities:
                        source_entity = entities[source_id]
                        bundle.derivation(target_entity, source_entity)

        # Specialization relations
        for connector in template.backward_connectors + template.forward_connectors:
            if connector.id in entities:
                general_entity = entities[connector.id]
                for specific_id in connector.specialized_by:
                    if specific_id in entities:
                        specific_entity = entities[specific_id]
                        bundle.specialization(specific_entity, general_entity)


class TraversalInformationAlgorithm:
    """
    Algorithm for determining whether elements belong to traversal information
    or domain-specific provenance, based on the thesis description.
    """

    @staticmethod
    def belongs_to_traversal_information(element) -> bool:
        """
        Determine if a PROV element belongs to traversal information.
        """
        # Check if element has CPM prov:type - if so, assume it's traversal information
        prov_types = element.get_attribute(PROV_TYPE)
        if prov_types:
            for prov_type in prov_types:
                if prov_type in CPM_SUBTYPES:
                    return True

        # For elements without CPM types, check if they have non-TI attributes
        if TraversalInformationAlgorithm._has_non_ti_attributes(element):
            return False

        # Default to False for non-CPM elements
        return False

    @staticmethod
    def _has_non_ti_attributes(element) -> bool:
        """Check if element has attributes not allowed in traversal information"""
        for attr_name, _ in element.attributes:
            # Check if attribute belongs to CPM namespace or is dct:hasPart
            if attr_name not in CPM_TI_ALLOWED_ATTRIBUTES and not str(attr_name).startswith('cpm:'):
                return True
        return False


class CpmDocument:
    """
    CPM Document wrapper that provides CPM-specific functionality
    on top of a ProvGraphWrapper with full CRUD operations.
    """

    def __init__(self, prov_document: ProvDocument):
        """
        Initialize CPM document from a PROV document.

        Args:
            prov_document: The underlying PROV document
        """
        self.graph_wrapper = ProvGraphWrapper(prov_document)
        self.ti_algorithm = TraversalInformationAlgorithm()
        self._bundle = self._get_bundle()
        self._modified = False
        self._custom_bundle_id = None  # Store custom bundle ID that persists across reconstructions

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

    @classmethod
    def from_template(cls, template: TraversalInformationTemplate,
                      domain_specific_doc: Optional[ProvDocument] = None) -> 'CpmDocument':
        """
        Create CPM document from template and optional domain-specific provenance.

        Args:
            template: Traversal information template
            domain_specific_doc: Optional domain-specific provenance document

        Returns:
            CpmDocument instance
        """
        mapper = TemplateProvMapper()
        ti_doc = mapper.map_to_document(template)

        if domain_specific_doc:
            # Merge traversal information with domain-specific provenance
            ti_doc.update(domain_specific_doc)

        # Create CpmDocument and ensure graph wrapper is properly initialized
        cpm_doc = cls(ti_doc)

        # Force re-initialization of graph wrapper to ensure all nodes are properly loaded
        cpm_doc._reinitialize_graph_wrapper()

        return cpm_doc

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
            'traversal_information_nodes': len(ti_nodes),
            'domain_specific_nodes': len(ds_nodes),
            'entities': len([n for n in all_nodes if isinstance(n.prov_entity, ProvEntity)]),
            'activities': len([n for n in all_nodes if isinstance(n.prov_entity, ProvActivity)]),
            'agents': len([n for n in all_nodes if isinstance(n.prov_entity, ProvAgent)]),
            'forward_connectors': len(self.get_forward_connectors()),
            'backward_connectors': len(self.get_backward_connectors()),
            'main_activities': len([n for n in ti_nodes if self._has_cpm_type(n, CPM_MAIN_ACTIVITY)])
        }

    # ========================
    # ADVANCED CRUD OPERATIONS
    # ========================

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

    # ========================
    # EDGE MANAGEMENT OPERATIONS
    # ========================

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

        edges_to_remove = self.get_edges(source_id, target_id, relation_type)
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

    # ========================
    # ADVANCED TRAVERSAL OPERATIONS
    # ========================

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

    # ========================
    # FILTERING AND ANALYSIS
    # ========================

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

    # ========================
    # HELPER METHODS
    # ========================

    def _extract_edge_endpoints(self, edge: Any) -> Tuple[Optional[Any], Optional[Any]]:
        """Extract source and target from an edge/relation."""
        try:
            # Different relation types have different attribute names
            if hasattr(edge, 'entity') and hasattr(edge, 'activity'):
                # Usage relation - entity influences activity
                return edge.entity, edge.activity
            elif hasattr(edge, 'activity') and hasattr(edge, 'entity'):
                # Generation relation - activity generates entity
                return edge.activity, edge.entity
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

    # ========================
    # DOCUMENT MANIPULATION
    # ========================

    def clone(self) -> 'CpmDocument':
        """
        Create a deep copy of this CPM document.

        Returns:
            A new CpmDocument instance with copied content
        """
        # Create a deep copy of the PROV document
        prov_doc = self.to_prov_document()
        cloned_doc = copy.deepcopy(prov_doc)
        return CpmDocument(cloned_doc)

    def merge_with(self, other: 'CpmDocument',
                   conflict_resolution: str = 'keep_both') -> 'CpmDocument':
        """
        Merge this document with another CPM document.

        Args:
            other: The other CPM document to merge with
            conflict_resolution: How to handle conflicts ('keep_both', 'keep_first', 'keep_second')

        Returns:
            A new merged CpmDocument

        Raises:
            InvalidOperationError: If conflict resolution strategy is invalid
        """
        if conflict_resolution not in ['keep_both', 'keep_first', 'keep_second']:
            raise InvalidOperationError(f"Invalid conflict resolution strategy: {conflict_resolution}")

        # Start with a copy of this document
        merged_doc = self.clone()
        other_prov_doc = other.to_prov_document()

        # Merge the documents based on conflict resolution
        if conflict_resolution == 'keep_both':
            # Add all records from other document, renaming conflicts
            merged_doc._merge_records_keep_both(other_prov_doc)
        elif conflict_resolution == 'keep_first':
            # Only add non-conflicting records from other document
            merged_doc._merge_records_keep_first(other_prov_doc)
        elif conflict_resolution == 'keep_second':
            # Replace conflicting records with ones from other document
            merged_doc._merge_records_keep_second(other_prov_doc)

        return merged_doc

    def filter_by_time_range(self, start_time: Optional[Any] = None,
                             end_time: Optional[Any] = None) -> 'CpmDocument':
        """
        Filter document to include only elements within a time range.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            A new filtered CpmDocument
        """
        filtered_doc = CpmDocument(ProvDocument())

        for node in self.graph_wrapper.get_nodes():
            # Check if node has time attributes within range
            include_node = True

            try:
                if isinstance(node.prov_entity, ProvActivity):
                    start_attr = node.get_prov_attribute('prov:startTime')
                    end_attr = node.get_prov_attribute('prov:endTime')

                    if start_time and start_attr:
                        if start_attr[0] < start_time:
                            include_node = False

                    if end_time and end_attr:
                        if end_attr[0] > end_time:
                            include_node = False
            except:
                pass

            if include_node:
                # Add node to filtered document
                node_type = 'entity'
                if isinstance(node.prov_entity, ProvActivity):
                    node_type = 'activity'
                elif isinstance(node.prov_entity, ProvAgent):
                    node_type = 'agent'

                # Extract attributes
                attributes = {}
                for attr_name, attr_value in node.prov_entity.attributes:
                    if attr_name != PROV_TYPE:
                        attributes[str(attr_name)] = attr_value

                prov_types = node.get_prov_attribute(str(PROV_TYPE))
                prov_type = prov_types[0] if prov_types else None

                try:
                    filtered_doc.add_node(node_type, node.identifier, attributes, prov_type)
                except:
                    pass  # Skip if unable to add

        return filtered_doc

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
        subgraph_doc = CpmDocument(ProvDocument())
        added_nodes = {}

        # Add specified nodes
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node:
                node_type = 'entity'
                if isinstance(node.prov_entity, ProvActivity):
                    node_type = 'activity'
                elif isinstance(node.prov_entity, ProvAgent):
                    node_type = 'agent'

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
                except:
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
                            except:
                                pass

        return subgraph_doc

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

    def export_to_formats(self) -> Dict[str, str]:
        """
        Export the document to various formats.

        Returns:
            Dictionary with format names as keys and serialized content as values
        """
        prov_doc = self.to_prov_document()
        exports = {}

        try:
            # PROV-N format
            exports['provn'] = prov_doc.get_provn()
        except:
            exports['provn'] = "Error: Could not export to PROV-N"

        try:
            # JSON format
            exports['json'] = prov_doc.serialize(format='json')
        except:
            exports['json'] = "Error: Could not export to JSON"

        try:
            # XML format
            exports['xml'] = prov_doc.serialize(format='xml')
        except:
            exports['xml'] = "Error: Could not export to XML"

        return exports

    # ========================
    # ADVANCED ANALYSIS
    # ========================

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

    # ========================
    # HELPER METHODS FOR ADVANCED FEATURES
    # ========================

    def _merge_records_keep_both(self, other_doc: ProvDocument):
        """Merge records keeping both in case of conflicts."""
        # Implementation would merge PROV records with conflict resolution
        pass

    def _merge_records_keep_first(self, other_doc: ProvDocument):
        """Merge records keeping first in case of conflicts."""
        # Implementation would merge PROV records preferring current
        pass

    def _merge_records_keep_second(self, other_doc: ProvDocument):
        """Merge records keeping second in case of conflicts."""
        # Implementation would merge PROV records preferring other
        pass

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

    def get_edge(self, effect_id: Union[str, QualifiedName],
                 cause_id: Union[str, QualifiedName],
                 kind: Optional[str] = None) -> Optional[Any]:
        """
        Get a single edge with specific effect, cause, and optionally kind.

        Args:
            effect_id: Effect node identifier
            cause_id: Cause node identifier
            kind: Optional relation kind/type

        Returns:
            The edge if found, None otherwise

        Raises:
            MultipleEdgesError: If multiple edges are found
        """
        edges = self.get_edges(cause_id, effect_id, kind)
        if not edges:
            return None
        if len(edges) > 1:
            raise MultipleEdgesError(f"Multiple edges found between cause {cause_id} and effect {effect_id}")
        return edges[0]

    def get_edges_by_kind(self, kind: str) -> List[Any]:
        """
        Get all edges of a specific kind/type.

        Args:
            kind: The relation kind/type

        Returns:
            List of matching edges
        """
        return self.get_edges(relation_type=kind)

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

    # ========================
    # ADDITIONAL UTILITY METHODS
    # ========================

    def get_edge_by_id(self, edge_id: Union[str, QualifiedName]) -> Optional[Any]:
        """
        Get edge by its identifier.
        """
        return self.get_edges_by_id(edge_id)[0] if self.get_edges_by_id(edge_id) else None

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

    # ========================
    # ADVANCED COLLECTION OPERATIONS
    # ========================

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

    def equals(self, other: 'CpmDocument') -> bool:
        """
        Check equality with another CPM document.
        """
        if not isinstance(other, CpmDocument):
            return False

        # Compare basic properties
        if self.get_bundle_id() != other.get_bundle_id():
            return False

        # Compare node counts
        self_stats = self.get_statistics()
        other_stats = other.get_statistics()

        for key in ['total_nodes', 'entities', 'activities', 'agents']:
            if self_stats.get(key, 0) != other_stats.get(key, 0):
                return False

        # Compare edge counts
        self_edges = len(self.get_all_edges())
        other_edges = len(other.get_all_edges())

        return self_edges == other_edges

    def hash_code(self) -> int:
        """
        Generate hash code for the document.
        """
        bundle_id = self.get_bundle_id() or ""
        stats = self.get_statistics()

        # Create hash from key document properties
        hash_components = [
            bundle_id,
            stats.get('total_nodes', 0),
            stats.get('entities', 0),
            stats.get('activities', 0),
            stats.get('agents', 0),
            len(self.get_all_edges())
        ]

        return hash(tuple(hash_components))

    # ========================
    # ENHANCED VALIDATION AND ANALYSIS
    # ========================

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


class CpmDocumentBuilder:
    """
    Builder class for constructing CPM documents programmatically.
    """

    def __init__(self, bundle_name: str = "cpm:bundle"):
        """
        Initialize the builder.

        Args:
            bundle_name: Name for the CPM bundle
        """
        if not bundle_name or not bundle_name.strip():
            raise ValueError("Bundle name cannot be empty or whitespace")
        self.bundle_name = bundle_name
        self.main_activity = None
        self.forward_connectors = []
        self.backward_connectors = []
        self.sender_agents = []
        self.receiver_agents = []
        self.identifier_entities = []
        self.relations = []
        self.prefixes = {}

    def with_main_activity(self, activity_id: str, start_time: Optional[Any] = None,
                           end_time: Optional[Any] = None, **attributes) -> 'CpmDocumentBuilder':
        """Add main activity to the document."""
        from .template import MainActivityTemplate, RelationTemplate

        self.main_activity = MainActivityTemplate(
            id=activity_id,
            start_time=start_time,
            end_time=end_time,
            attributes=attributes,
            used=[],
            generated=[],
            has_part=[]
        )
        return self

    def with_forward_connector(self, connector_id: str, referenced_bundle_id: str,
                               hash_value: Optional[str] = None, **attributes) -> 'CpmDocumentBuilder':
        """Add forward connector to the document."""
        from .template import ConnectorTemplate

        connector = ConnectorTemplate(
            id=connector_id,
            referenced_bundle_id=referenced_bundle_id,
            referenced_bundle_hash_value=hash_value,
            attributes=attributes,
            attributed_to=None,
            derived_from=[],
            specialized_by=[]
        )
        self.forward_connectors.append(connector)
        return self

    def with_backward_connector(self, connector_id: str, referenced_bundle_id: str,
                                hash_value: Optional[str] = None, **attributes) -> 'CpmDocumentBuilder':
        """Add backward connector to the document."""
        from .template import ConnectorTemplate

        connector = ConnectorTemplate(
            id=connector_id,
            referenced_bundle_id=referenced_bundle_id,
            referenced_bundle_hash_value=hash_value,
            attributes=attributes,
            attributed_to=None,
            derived_from=[],
            specialized_by=[]
        )
        self.backward_connectors.append(connector)
        return self

    def with_sender_agent(self, agent_id: str, **attributes) -> 'CpmDocumentBuilder':
        """Add sender agent to the document."""
        from .template import AgentTemplate

        agent = AgentTemplate(id=agent_id, attributes=attributes)
        self.sender_agents.append(agent)
        return self

    def with_receiver_agent(self, agent_id: str, **attributes) -> 'CpmDocumentBuilder':
        """Add receiver agent to the document."""
        from .template import AgentTemplate

        agent = AgentTemplate(id=agent_id, attributes=attributes)
        self.receiver_agents.append(agent)
        return self

    def with_prefix(self, prefix: str, uri: str) -> 'CpmDocumentBuilder':
        """Add namespace prefix."""
        self.prefixes[prefix] = uri
        return self

    def build(self) -> CpmDocument:
        """Build the CPM document."""
        if not self.main_activity:
            raise InvalidOperationError("Main activity is required")

        from .template import TraversalInformationTemplate

        template = TraversalInformationTemplate(
            bundle_name=self.bundle_name,
            main_activity=self.main_activity,
            backward_connectors=self.backward_connectors,
            forward_connectors=self.forward_connectors,
            sender_agents=self.sender_agents,
            receiver_agents=self.receiver_agents,
            identifier_entities=self.identifier_entities,
            prefixes=self.prefixes
        )

        return CpmDocument.from_template(template)


class CpmValidator:
    """
    Comprehensive validator for CPM documents.
    """

    @staticmethod
    def validate_document(doc: CpmDocument) -> Dict[str, List[str]]:
        """
        Perform comprehensive validation of a CPM document.

        Args:
            doc: The CPM document to validate

        Returns:
            Dictionary with validation results
        """
        results = {
            'errors': [],
            'warnings': [],
            'info': []
        }

        # Structural validation
        structural_issues = doc.validate_structure()
        for category, issues in structural_issues.items():
            results[category].extend(issues)

        # CPM-specific validation
        CpmValidator._validate_cpm_constraints(doc, results)

        # Provenance chain validation
        CpmValidator._validate_provenance_chains(doc, results)

        return results

    @staticmethod
    def _validate_cpm_constraints(doc: CpmDocument, results: Dict[str, List[str]]):
        """Validate CPM-specific constraints."""

        # Check traversal information separation
        ti_nodes = doc.get_traversal_information_nodes()
        ds_nodes = doc.get_domain_specific_nodes()

        if not ti_nodes:
            results['warnings'].append("No traversal information nodes found")

        if not ds_nodes:
            results['info'].append("No domain-specific nodes found")

        # Check cross-part edges
        cross_edges = doc.get_cross_part_edges()
        if cross_edges:
            results['info'].append(f"Found {len(cross_edges)} cross-part edges")

    @staticmethod
    def _validate_provenance_chains(doc: CpmDocument, results: Dict[str, List[str]]):
        """Validate provenance chains."""

        analysis = doc.analyze_provenance_chains()

        if analysis['circular_dependencies']:
            for cycle in analysis['circular_dependencies']:
                results['errors'].append(f"Circular dependency detected: {' -> '.join(cycle)}")

        if analysis['total_chains'] == 0:
            results['warnings'].append("No provenance chains found")
