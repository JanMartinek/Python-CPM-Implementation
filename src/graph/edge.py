"""
Graph Edge Implementation

Represents edges in the CPM provenance graph with advanced relation management
"""

from typing import List, Optional, Any, Union, TYPE_CHECKING
from prov.model import ProvRecord, ProvRelation, ProvActivity
from prov.identifier import QualifiedName

if TYPE_CHECKING:
    from .node import GraphNode


class GraphEdge:
    """
    Represents an edge in the provenance graph with enhanced relation management.
    """

    def __init__(self, prov_relation: Union[ProvRelation, 'ProvActivity'], cause: 'GraphNode', effect: 'GraphNode',
                 identifier: Optional[QualifiedName] = None):
        """

        Args:
            prov_relation: The underlying PROV relation or activity
            cause: The cause node (source)
            effect: The effect node (target)
            identifier: Optional identifier override
        """
        from prov.model import ProvActivity

        self.prov_relation = prov_relation
        # For compatibility with ProvGraphWrapper, also store as prov_activity
        if isinstance(prov_relation, ProvActivity):
            self.prov_activity = prov_relation
        else:
            self.prov_activity = prov_relation

        self.cause = cause
        self.effect = effect
        self._identifier = identifier
        # Only store ProvRelations in relations list
        if isinstance(prov_relation, ProvRelation):
            self.relations: List[ProvRelation] = [prov_relation]
        else:
            self.relations: List[ProvRelation] = []

    @property
    def identifier(self) -> Optional[QualifiedName]:
        """Get the edge identifier"""
        if self._identifier:
            return self._identifier
        return getattr(self.prov_relation, 'identifier', None)

    def set_cause(self, cause: 'GraphNode'):
        if self.cause:
            self.cause.remove_cause_edge(self)
        self.cause = cause
        if cause:
            cause.add_cause_edge(self)

    def set_effect(self, effect: 'GraphNode'):
        """Set the effect node"""
        if self.effect:
            self.effect.remove_effect_edge(self)
        self.effect = effect
        if effect:
            effect.add_effect_edge(self)

    @property
    def kind(self) -> str:
        relation_type = type(self.prov_relation).__name__
        # Convert to standard PROV relation names
        type_mapping = {
            'ProvUsage': 'PROV_USAGE',
            'ProvGeneration': 'PROV_GENERATION',
            'ProvAssociation': 'PROV_ASSOCIATION',
            'ProvAttribution': 'PROV_ATTRIBUTION',
            'ProvDerivation': 'PROV_DERIVATION',
            'ProvCommunication': 'PROV_COMMUNICATION',
            'ProvDelegation': 'PROV_DELEGATION',
            'ProvInfluence': 'PROV_INFLUENCE',
            'ProvSpecialization': 'PROV_SPECIALIZATION',
            'ProvAlternate': 'PROV_ALTERNATE',
            'ProvMembership': 'PROV_MEMBERSHIP'
        }
        return type_mapping.get(relation_type, relation_type.upper())

    def add_relation(self, relation: ProvRelation) -> bool:
        """Add a relation to this edge"""
        if relation not in self.relations:
            self.relations.append(relation)
            return True
        return False

    def remove_relation(self, relation: ProvRelation) -> bool:
        """Remove a relation from this edge"""
        if relation in self.relations and len(self.relations) > 1:
            self.relations.remove(relation)
            return True
        return False

    def handle_duplicate(self, duplicate_relation: ProvRelation):
        """Handle duplicate relation"""
        # Check if we already have a similar relation
        for existing_relation in self.relations:
            if (hasattr(existing_relation, 'identifier') and
                hasattr(duplicate_relation, 'identifier') and
                    existing_relation.identifier == duplicate_relation.identifier):
                # Merge attributes - simplified implementation
                return

        # Add as new relation
        self.add_relation(duplicate_relation)

    def clone(self) -> 'GraphEdge':
        """Create a clone of this edge"""
        import copy
        cloned_relation = copy.deepcopy(self.prov_relation)
        # Note: cause and effect nodes should be updated after cloning
        cloned_edge = GraphEdge(cloned_relation, self.cause, self.effect, self._identifier)
        cloned_edge.relations = [copy.deepcopy(rel) for rel in self.relations]
        return cloned_edge

    def is_between(self, cause: 'GraphNode', effect: 'GraphNode') -> bool:
        """Check if this edge connects the specified cause and effect nodes"""
        return self.cause == cause and self.effect == effect

    def connects_node(self, node: 'GraphNode') -> bool:
        """Check if this edge connects to the specified node"""
        return self.cause == node or self.effect == node

    def get_other_node(self, node: 'GraphNode') -> Optional['GraphNode']:
        """Get the node on the other end of this edge"""
        if self.cause == node:
            return self.effect
        elif self.effect == node:
            return self.cause
        return None

    def reverse(self) -> 'GraphEdge':
        """Create a reversed version of this edge"""
        return GraphEdge(self.prov_relation, self.effect, self.cause, self._identifier)

    def get_attributes(self) -> List[tuple]:
        """Get all attributes from the primary relation"""
        if hasattr(self.prov_relation, 'attributes'):
            return list(self.prov_relation.attributes)
        return []

    def has_attribute(self, attribute_name: str) -> bool:
        """Check if edge has a specific attribute"""
        for attr_name, _ in self.get_attributes():
            if str(attr_name) == attribute_name:
                return True
        return False

    def get_attribute_values(self, attribute_name: str) -> List[Any]:
        """Get values for a specific attribute"""
        values = []
        for attr_name, attr_value in self.get_attributes():
            if str(attr_name) == attribute_name:
                if isinstance(attr_value, (list, tuple, set)):
                    values.extend(attr_value)
                else:
                    values.append(attr_value)
        return values

    def __str__(self):
        cause_id = self.cause.identifier if self.cause else "None"
        effect_id = self.effect.identifier if self.effect else "None"
        return f"GraphEdge({cause_id} -> {effect_id}, {self.kind})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, GraphEdge):
            return False
        return (self.identifier == other.identifier and
                self.prov_relation == other.prov_relation and
                self.cause == other.cause and
                self.effect == other.effect)

    def __hash__(self):
        return hash((self.identifier, id(self.prov_relation),
                    id(self.cause), id(self.effect)))


class DividedGraphEdge(GraphEdge):
    """
    Implementation of a divided edge that can contain multiple relations.
    """

    def __init__(self, relations: List[ProvRelation], cause: 'GraphNode', effect: 'GraphNode',
                 identifier: Optional[QualifiedName] = None):
        """
        Initialize a divided edge with multiple relations.

        Args:
            relations: List of PROV relations in this edge
            cause: The cause node
            effect: The effect node
            identifier: Optional identifier override
        """
        if not relations:
            raise ValueError("DividedEdge must have at least one relation")

        # Use first relation as primary
        super().__init__(relations[0], cause, effect, identifier)
        self.relations = relations.copy()

    def add_relation(self, relation: ProvRelation) -> bool:
        """Add a relation to this divided edge"""
        if relation not in self.relations:
            self.relations.append(relation)
            return True
        return False

    def remove_relation(self, relation: ProvRelation) -> bool:
        """Remove a relation from this divided edge"""
        if relation in self.relations and len(self.relations) > 1:
            self.relations.remove(relation)
            return True
        return False

    def handle_duplicate(self, duplicate_relation: ProvRelation):
        """Handle duplicate relation by merging or adding"""
        # Find matching relation and merge
        for relation in self.relations:
            if (hasattr(relation, 'identifier') and hasattr(duplicate_relation, 'identifier') and
                    relation.identifier == duplicate_relation.identifier):
                # Merge attributes - simplified implementation
                if hasattr(duplicate_relation, 'attributes') and hasattr(relation, 'attributes'):
                    # In full implementation, would properly merge PROV attributes
                    pass
                return

        # No matching relation found, add as new
        self.add_relation(duplicate_relation)

    @property
    def kind(self) -> str:
        """Get the kind based on the first relation"""
        return super().kind

    def clone(self) -> 'DividedGraphEdge':
        """Create a clone of this divided edge"""
        import copy
        cloned_relations = [copy.deepcopy(rel) for rel in self.relations]
        cloned_edge = DividedGraphEdge(cloned_relations, self.cause, self.effect, self._identifier)
        return cloned_edge

    def __eq__(self, other):
        if not isinstance(other, DividedGraphEdge):
            return False
        return (self.identifier == other.identifier and
                self.relations == other.relations and
                self.cause == other.cause and
                self.effect == other.effect)

    def __hash__(self):
        return hash((self.identifier, tuple(id(rel) for rel in self.relations),
                    id(self.cause), id(self.effect)))


class MergedGraphEdge(GraphEdge):
    """
    Implementation of a merged edge containing a single relation.
    """

    def __init__(self, relation: ProvRelation, cause: 'GraphNode', effect: 'GraphNode',
                 identifier: Optional[QualifiedName] = None):
        """
        Initialize a merged edge with a single relation.

        Args:
            relation: Single PROV relation in this edge
            cause: The cause node
            effect: The effect node
            identifier: Optional identifier override
        """
        super().__init__(relation, cause, effect, identifier)
        self.relations = [relation]

    def add_relation(self, relation: ProvRelation) -> bool:
        """Cannot add additional relations to a merged edge"""
        return False

    def remove_relation(self, relation: ProvRelation) -> bool:
        """Cannot remove the single relation from a merged edge"""
        return False

    def handle_duplicate(self, duplicate_relation: ProvRelation):
        """Handle duplicate by merging attributes into the single relation"""
        if (hasattr(self.prov_relation, 'identifier') and
            hasattr(duplicate_relation, 'identifier') and
                self.prov_relation.identifier == duplicate_relation.identifier):
            # Merge attributes - simplified implementation
            if hasattr(duplicate_relation, 'attributes') and hasattr(self.prov_relation, 'attributes'):
                # In full implementation, would properly merge PROV attributes
                pass

    def clone(self) -> 'GraphEdge':
        """Create a clone of this merged edge"""
        import copy
        cloned_relation = copy.deepcopy(self.prov_relation)
        # MergedGraphEdge requires ProvRelation, not ProvActivity
        if isinstance(cloned_relation, ProvRelation):
            cloned_edge = MergedGraphEdge(cloned_relation, self.cause, self.effect, self._identifier)
            return cloned_edge
        else:
            # For ProvActivity, create regular GraphEdge
            return GraphEdge(cloned_relation, self.cause, self.effect, self._identifier)


class EdgeFilter:
    """
    Utility class for filtering edges based on various criteria.
    """

    @staticmethod
    def by_cause(edges: List[GraphEdge], cause: 'GraphNode') -> List[GraphEdge]:
        """Filter edges by cause node"""
        return [edge for edge in edges if edge.cause == cause]

    @staticmethod
    def by_effect(edges: List[GraphEdge], effect: 'GraphNode') -> List[GraphEdge]:
        """Filter edges by effect node"""
        return [edge for edge in edges if edge.effect == effect]

    @staticmethod
    def by_kind(edges: List[GraphEdge], kind: str) -> List[GraphEdge]:
        """Filter edges by relation kind"""
        return [edge for edge in edges if edge.kind.lower() == kind.lower()]

    @staticmethod
    def by_cause_and_effect(edges: List[GraphEdge], cause: 'GraphNode',
                            effect: 'GraphNode') -> List[GraphEdge]:
        """Filter edges by both cause and effect nodes"""
        return [edge for edge in edges if edge.is_between(cause, effect)]

    @staticmethod
    def by_node(edges: List[GraphEdge], node: 'GraphNode') -> List[GraphEdge]:
        """Filter edges that connect to a specific node"""
        return [edge for edge in edges if edge.connects_node(node)]

    @staticmethod
    def by_attribute(edges: List[GraphEdge], attribute_name: str,
                     attribute_value: Optional[Any] = None) -> List[GraphEdge]:
        """Filter edges by attribute presence or value"""
        if attribute_value is None:
            return [edge for edge in edges if edge.has_attribute(attribute_name)]
        else:
            return [edge for edge in edges
                    if attribute_value in edge.get_attribute_values(attribute_name)]


class EdgeBuilder:
    """
    Builder class for creating edges with various configurations.
    """

    def __init__(self):
        self._relation = None
        self._cause = None
        self._effect = None
        self._identifier = None
        self._edge_type = 'merged'  # 'merged' or 'divided'
        self._relations = []

    def with_relation(self, relation: ProvRelation) -> 'EdgeBuilder':
        """Set the primary relation"""
        self._relation = relation
        return self

    def with_relations(self, relations: List[ProvRelation]) -> 'EdgeBuilder':
        """Set multiple relations (creates divided edge)"""
        self._relations = relations.copy()
        self._edge_type = 'divided'
        if relations:
            self._relation = relations[0]
        return self

    def with_cause(self, cause: 'GraphNode') -> 'EdgeBuilder':
        """Set the cause node"""
        self._cause = cause
        return self

    def with_effect(self, effect: 'GraphNode') -> 'EdgeBuilder':
        """Set the effect node"""
        self._effect = effect
        return self

    def with_identifier(self, identifier: QualifiedName) -> 'EdgeBuilder':
        """Set the edge identifier"""
        self._identifier = identifier
        return self

    def as_divided(self) -> 'EdgeBuilder':
        """Create as divided edge"""
        self._edge_type = 'divided'
        return self

    def as_merged(self) -> 'EdgeBuilder':
        """Create as merged edge"""
        self._edge_type = 'merged'
        return self

    def build(self) -> GraphEdge:
        """Build the edge"""
        if not self._relation:
            raise ValueError("Relation is required")
        if not self._cause:
            raise ValueError("Cause node is required")
        if not self._effect:
            raise ValueError("Effect node is required")

        if self._edge_type == 'divided':
            relations = self._relations if self._relations else [self._relation]
            edge = DividedGraphEdge(relations, self._cause, self._effect, self._identifier)
        else:
            edge = MergedGraphEdge(self._relation, self._cause, self._effect, self._identifier)

        # Update node references
        self._cause.add_cause_edge(edge)
        self._effect.add_effect_edge(edge)

        return edge
