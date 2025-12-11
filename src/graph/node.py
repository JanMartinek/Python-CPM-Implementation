"""
Graph Node Implementation

Represents nodes in the CPM provenance graph with advanced edge management
"""

from typing import List, Optional, Set, Any, Dict, Union, TYPE_CHECKING
from prov.model import ProvRecord, ProvEntity, ProvActivity, ProvAgent
from prov.identifier import QualifiedName
from prov.constants import PROV_TYPE

if TYPE_CHECKING:
    from .edge import GraphEdge


class GraphNode:
    """
    Represents a node in the provenance graph with enhanced edge management.
    """

    def __init__(self, prov_entity: ProvRecord, identifier: Optional[QualifiedName] = None):
        self.prov_entity = prov_entity
        self._identifier = identifier
        self.node_id = str(identifier) if identifier else str(getattr(prov_entity, 'identifier', f"node_{id(prov_entity)}"))
        self._cause_edges: List['GraphEdge'] = []
        self._effect_edges: List['GraphEdge'] = []
        self._cached_attributes = None

    @property
    def identifier(self) -> Optional[QualifiedName]:
        if self._identifier:
            return self._identifier
        return getattr(self.prov_entity, 'identifier', None)

    @property
    def cause_edges(self) -> List['GraphEdge']:
        return self._cause_edges.copy()

    @property
    def effect_edges(self) -> List['GraphEdge']:
        return self._effect_edges.copy()

    @property
    def all_edges(self) -> List['GraphEdge']:
        return self._cause_edges + self._effect_edges

    def add_cause_edge(self, edge: 'GraphEdge'):
        if edge not in self._cause_edges:
            self._cause_edges.append(edge)

    def add_effect_edge(self, edge: 'GraphEdge'):
        if edge not in self._effect_edges:
            self._effect_edges.append(edge)

    def remove_cause_edge(self, edge: 'GraphEdge') -> bool:
        if edge in self._cause_edges:
            self._cause_edges.remove(edge)
            return True
        return False

    def remove_effect_edge(self, edge: 'GraphEdge') -> bool:
        if edge in self._effect_edges:
            self._effect_edges.remove(edge)
            return True
        return False

    @property
    def kind(self) -> str:
        if isinstance(self.prov_entity, ProvEntity):
            return "PROV_ENTITY"
        elif isinstance(self.prov_entity, ProvActivity):
            return "PROV_ACTIVITY"
        elif isinstance(self.prov_entity, ProvAgent):
            return "PROV_AGENT"
        return "UNKNOWN"

    @property
    def id(self) -> Optional[QualifiedName]:
        return self.identifier

    def get_prov_attribute(self, attribute_name: str) -> List[Any]:
        if not hasattr(self.prov_entity, 'attributes'):
            return []

        values = []
        for attr_name, attr_value in self.prov_entity.attributes:
            if str(attr_name) == attribute_name:
                if isinstance(attr_value, (list, tuple, set)):
                    values.extend(attr_value)
                else:
                    values.append(attr_value)

        return values

    def has_prov_type(self, prov_type: Union[str, QualifiedName]) -> bool:
        prov_types = self.get_prov_attribute(str(PROV_TYPE))
        type_str = str(prov_type)
        return any(str(ptype) == type_str for ptype in prov_types)

    @property
    def elements(self) -> List[ProvRecord]:
        return [self.prov_entity]

    @property
    def any_element(self) -> ProvRecord:
        return self.prov_entity

    def handle_duplicate(self, duplicate_element: ProvRecord):
        if hasattr(duplicate_element, 'attributes') and hasattr(self.prov_entity, 'attributes'):
            pass

    def remove_element(self, element: ProvRecord) -> bool:
        if element == self.prov_entity:
            return False
        return False

    def clone(self) -> 'GraphNode':
        import copy
        cloned_entity = copy.deepcopy(self.prov_entity)
        cloned_node = GraphNode(cloned_entity, self._identifier)
        return cloned_node

    def get_edges_by_relation_type(self, relation_type: str) -> List['GraphEdge']:
        return [edge for edge in self.all_edges
                if edge.kind.lower() == relation_type.lower()]

    def get_connected_nodes(self, relation_types: Optional[List[str]] = None) -> List['GraphNode']:
        connected = []
        relation_types_lower = [rt.lower() for rt in relation_types] if relation_types else None

        for edge in self.all_edges:
            if relation_types_lower and edge.kind.lower() not in relation_types_lower:
                continue

            other_node = edge.effect if edge.cause == self else edge.cause
            if other_node and other_node not in connected:
                connected.append(other_node)

        return connected

    @property
    def degree(self) -> int:
        return len(self.all_edges)

    @property
    def in_degree(self) -> int:
        return len(self._effect_edges)

    @property
    def out_degree(self) -> int:
        return len(self._cause_edges)

    def is_isolated(self) -> bool:  # This needs to be a method for backward compatibility
        return len(self.all_edges) == 0

    def __str__(self):
        return f"GraphNode({self.identifier}, {self.kind}, edges: {self.degree})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, GraphNode):
            return False
        return (self.identifier == other.identifier and
                self.prov_entity == other.prov_entity)

    def __hash__(self):
        return hash((self.identifier, id(self.prov_entity)))


class DividedGraphNode(GraphNode):
    """
    Implementation of a divided node that can contain multiple elements.
    """

    def __init__(self, elements: List[ProvRecord], identifier: Optional[QualifiedName] = None):
        if not elements:
            raise ValueError("DividedNode must have at least one element")

        super().__init__(elements[0], identifier)
        self._elements = elements.copy()

    @property
    def elements(self) -> List[ProvRecord]:
        return self._elements.copy()

    @property
    def any_element(self) -> ProvRecord:
        return self._elements[0]

    def add_element(self, element: ProvRecord):
        if element not in self._elements:
            self._elements.append(element)

    def remove_element(self, element: ProvRecord) -> bool:
        if element in self._elements and len(self._elements) > 1:
            self._elements.remove(element)
            return True
        return False

    def handle_duplicate(self, duplicate_element: ProvRecord):
        for element in self._elements:
            if (hasattr(element, 'identifier') and hasattr(duplicate_element, 'identifier') and
                    element.identifier == duplicate_element.identifier):
                if hasattr(duplicate_element, 'attributes') and hasattr(element, 'attributes'):
                    pass
                return

        self.add_element(duplicate_element)

    @property
    def kind(self) -> str:
        return super().kind

    def clone(self) -> 'DividedGraphNode':
        import copy
        cloned_elements = [copy.deepcopy(elem) for elem in self._elements]
        cloned_node = DividedGraphNode(cloned_elements, self._identifier)
        return cloned_node

    def __eq__(self, other):
        if not isinstance(other, DividedGraphNode):
            return False
        return (self.identifier == other.identifier and
                self._elements == other._elements)

    def __hash__(self):
        return hash((self.identifier, tuple(id(elem) for elem in self._elements)))


class MergedGraphNode(GraphNode):
    """
    Implementation of a merged node containing a single element.
    """

    def __init__(self, element: ProvRecord, identifier: Optional[QualifiedName] = None):
        super().__init__(element, identifier)

    def handle_duplicate(self, duplicate_element: ProvRecord):
        if (hasattr(self.prov_entity, 'identifier') and
            hasattr(duplicate_element, 'identifier') and
                self.prov_entity.identifier == duplicate_element.identifier):
            if hasattr(duplicate_element, 'attributes') and hasattr(self.prov_entity, 'attributes'):
                pass

    def remove_element(self, element: ProvRecord) -> bool:
        return False

    def clone(self) -> 'MergedGraphNode':
        import copy
        cloned_element = copy.deepcopy(self.prov_entity)
        cloned_node = MergedGraphNode(cloned_element, self._identifier)
        return cloned_node
