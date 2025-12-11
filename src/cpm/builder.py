"""
CPM Document Builder and Validator

This module provides utilities for building and validating CPM documents:
- CpmDocumentBuilder: Fluent API for constructing CPM documents programmatically
"""

from typing import Dict, List, Optional, Any
from .model import CpmDocument, InvalidOperationError


class CpmDocumentBuilder:
    """
    Builder class for constructing CPM documents programmatically.
    Provides a fluent API for building CPM documents step by step.
    """

    def __init__(self, bundle_name: str = "cpm:bundle"):
        """
        Initialize the builder.

        Args:
            bundle_name: Name for the CPM bundle
        """
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
        """
        Add main activity to the document.

        Args:
            activity_id: Identifier for the main activity
            start_time: Optional start time
            end_time: Optional end time
            **attributes: Additional attributes for the activity

        Returns:
            Self for method chaining
        """
        from .template import MainActivityTemplate

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
        """
        Add forward connector to the document.

        Args:
            connector_id: Identifier for the connector
            referenced_bundle_id: Referenced bundle identifier
            hash_value: Optional hash value for verification
            **attributes: Additional attributes for the connector

        Returns:
            Self for method chaining
        """
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
        """
        Add backward connector to the document.

        Args:
            connector_id: Identifier for the connector
            referenced_bundle_id: Referenced bundle identifier
            hash_value: Optional hash value for verification
            **attributes: Additional attributes for the connector

        Returns:
            Self for method chaining
        """
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
        """
        Add sender agent to the document.

        Args:
            agent_id: Identifier for the agent
            **attributes: Additional attributes for the agent

        Returns:
            Self for method chaining
        """
        from .template import AgentTemplate

        agent = AgentTemplate(id=agent_id, attributes=attributes)
        self.sender_agents.append(agent)
        return self

    def with_receiver_agent(self, agent_id: str, **attributes) -> 'CpmDocumentBuilder':
        """
        Add receiver agent to the document.

        Args:
            agent_id: Identifier for the agent
            **attributes: Additional attributes for the agent

        Returns:
            Self for method chaining
        """
        from .template import AgentTemplate

        agent = AgentTemplate(id=agent_id, attributes=attributes)
        self.receiver_agents.append(agent)
        return self

    def with_prefix(self, prefix: str, uri: str) -> 'CpmDocumentBuilder':
        """
        Add namespace prefix.

        Args:
            prefix: Namespace prefix
            uri: Namespace URI

        Returns:
            Self for method chaining
        """
        self.prefixes[prefix] = uri
        return self

    def with_used_relation(self, target_id: str, relation_id: Optional[str] = None) -> 'CpmDocumentBuilder':
        """
        Add a 'used' relation to the main activity.

        Args:
            target_id: Target entity identifier
            relation_id: Optional relation identifier

        Returns:
            Self for method chaining
        """
        if not self.main_activity:
            raise InvalidOperationError("Main activity must be set before adding relations")

        from .template import RelationTemplate
        relation = RelationTemplate(target_id=target_id, relation_id=relation_id)
        self.main_activity.used.append(relation)
        return self

    def with_generated_entity(self, entity_id: str) -> 'CpmDocumentBuilder':
        """
        Add a generated entity to the main activity.

        Args:
            entity_id: Generated entity identifier

        Returns:
            Self for method chaining
        """
        if not self.main_activity:
            raise InvalidOperationError("Main activity must be set before adding generated entities")

        self.main_activity.generated.append(entity_id)
        return self

    def with_sub_activity(self, sub_activity_id: str) -> 'CpmDocumentBuilder':
        """
        Add a sub-activity (hasPart relation) to the main activity.

        Args:
            sub_activity_id: Sub-activity identifier

        Returns:
            Self for method chaining
        """
        if not self.main_activity:
            raise InvalidOperationError("Main activity must be set before adding sub-activities")

        self.main_activity.has_part.append(sub_activity_id)
        return self

    def build(self) -> CpmDocument:
        """
        Build the CPM document from the configured components.

        Returns:
            A new CpmDocument instance

        Raises:
            InvalidOperationError: If main activity is not set
        """
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


