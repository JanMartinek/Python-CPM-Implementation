"""
Template to PROV Mapping

Maps CPM TraversalInformationTemplate objects to PROV documents.
"""

from typing import Dict
from prov.model import ProvDocument, ProvBundle, ProvEntity, ProvActivity, ProvAgent
from prov.constants import PROV_TYPE, PROV_VALUE

from .constants import *
from .template import TraversalInformationTemplate


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

        # Add referenced meta bundle ID
        if template.referenced_meta_bundle_id:
            ref_meta_bundle_qname = self._create_qualified_name(bundle, template.referenced_meta_bundle_id)
            if ref_meta_bundle_qname:
                attributes.append((CPM_REFERENCED_META_BUNDLE_ID, ref_meta_bundle_qname))

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

        # Add external ID
        if template.external_id:
            attributes.append((CPM_EXTERNAL_ID, template.external_id))

        # Add CPM-specific attributes
        if template.referenced_bundle_id:
            ref_bundle_qname = self._create_qualified_name(bundle, template.referenced_bundle_id)
            if ref_bundle_qname:
                attributes.append((CPM_REFERENCED_BUNDLE_ID, ref_bundle_qname))

        if template.referenced_meta_bundle_id:
            ref_meta_bundle_qname = self._create_qualified_name(bundle, template.referenced_meta_bundle_id)
            if ref_meta_bundle_qname:
                attributes.append((CPM_REFERENCED_META_BUNDLE_ID, ref_meta_bundle_qname))

        if template.referenced_bundle_hash_value:
            attributes.append((CPM_REFERENCED_BUNDLE_HASH_VALUE, template.referenced_bundle_hash_value))

        if template.hash_alg:
            attributes.append((CPM_HASH_ALG, template.hash_alg))

        if template.provenance_service_uri:
            attributes.append((CPM_PROVENANCE_SERVICE_URI, template.provenance_service_uri))

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

        # Add external ID
        if template.external_id:
            attributes.append((CPM_EXTERNAL_ID, template.external_id))

        # Add CPM-specific attributes
        if template.referenced_bundle_id:
            ref_bundle_qname = self._create_qualified_name(bundle, template.referenced_bundle_id)
            if ref_bundle_qname:
                attributes.append((CPM_REFERENCED_BUNDLE_ID, ref_bundle_qname))

        if template.referenced_meta_bundle_id:
            ref_meta_bundle_qname = self._create_qualified_name(bundle, template.referenced_meta_bundle_id)
            if ref_meta_bundle_qname:
                attributes.append((CPM_REFERENCED_META_BUNDLE_ID, ref_meta_bundle_qname))

        if template.referenced_bundle_hash_value:
            attributes.append((CPM_REFERENCED_BUNDLE_HASH_VALUE, template.referenced_bundle_hash_value))

        if template.hash_alg:
            attributes.append((CPM_HASH_ALG, template.hash_alg))

        if template.provenance_service_uri:
            attributes.append((CPM_PROVENANCE_SERVICE_URI, template.provenance_service_uri))

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

        # Add contact ID PID
        if template.contact_id_pid:
            attributes.append((CPM_CONTACT_ID_PID, template.contact_id_pid))

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

        # Add contact ID PID
        if template.contact_id_pid:
            attributes.append((CPM_CONTACT_ID_PID, template.contact_id_pid))

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
            attributes.append((CPM_EXTERNAL_ID, template.external_id))

        if template.external_id_type:
            attributes.append((CPM_EXTERNAL_ID_TYPE, template.external_id_type))

        if template.comment:
            attributes.append((CPM_COMMENT, template.comment))

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
        except Exception:
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

        # Specialization relations (specialized_by - who specializes this connector)
        for connector in template.backward_connectors + template.forward_connectors:
            if connector.id in entities:
                general_entity = entities[connector.id]
                for specific_id in connector.specialized_by:
                    if specific_id in entities:
                        specific_entity = entities[specific_id]
                        bundle.specialization(specific_entity, general_entity)

        # Specialization relations (specialization_of - this connector specializes another)
        # Only forward connectors have this (matches Java ForwardConnector.specializationOf)
        for connector in template.forward_connectors:
            if connector.specialization_of and connector.id in entities:
                specific_entity = entities[connector.id]
                general_id = connector.specialization_of
                if general_id in entities:
                    general_entity = entities[general_id]
                    bundle.specialization(specific_entity, general_entity)
