"""
CPM Factory - Factory patterns and multiple implementation strategies

Implements the factory patterns including:
- CpmFactory interfaces for different document strategies
- Ordered, Divided, and Merged implementations
- Statement ordering preservation capabilities
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Callable
from enum import Enum
import copy

from prov.model import ProvDocument, ProvBundle, ProvEntity, ProvActivity, ProvAgent
from prov.identifier import QualifiedName

from .model import CpmDocument


class ComponentStrategy(Enum):
    """Strategy for handling CPM document components"""
    MERGED = "merged"
    ORDERED = "ordered"
    DIVIDED_ORDERED = "divided_ordered"
    DIVIDED_UNORDERED = "divided_unordered"


class ICpmFactory(ABC):
    """
    Abstract factory interface for creating CPM model components.
    """

    @abstractmethod
    def create_document(self, prov_document: ProvDocument) -> CpmDocument:
        pass

    @abstractmethod
    def create_node(self, element: Any) -> Any:
        pass

    @abstractmethod
    def create_edge(self, relation: Any) -> Any:
        pass

    @abstractmethod
    def get_components_transformer(self) -> Callable[[List[Any]], List[Any]]:
        pass


class ICpmProvFactory(ABC):
    """
    Abstract factory interface for creating CPM PROV elements.
    """

    @abstractmethod
    def create_cpm_entity(self, identifier: QualifiedName, cpm_type: QualifiedName,
                          attributes: Optional[List[tuple]] = None) -> ProvEntity:
        pass

    @abstractmethod
    def create_cpm_activity(self, identifier: QualifiedName, cmp_type: QualifiedName,
                            start_time: Optional[Any] = None, end_time: Optional[Any] = None,
                            attributes: Optional[List[tuple]] = None) -> ProvActivity:
        pass

    @abstractmethod
    def create_cmp_agent(self, identifier: QualifiedName, cpm_type: QualifiedName,
                         attributes: Optional[List[tuple]] = None) -> ProvAgent:
        pass


class CpmMergedFactory(ICpmFactory):
    """
    Merged factory implementation where all components are handled uniformly.
    """

    def __init__(self):
        self.strategy = ComponentStrategy.MERGED

    def create_document(self, prov_document: ProvDocument) -> CpmDocument:
        return CpmDocument(prov_document)

    def create_node(self, element: Any) -> Any:
        return CpmMergedNode(element)

    def create_edge(self, relation: Any) -> Any:
        return CpmMergedEdge(relation)

    def get_components_transformer(self) -> Callable[[List[Any]], List[Any]]:
        def merge_transformer(components: List[Any]) -> List[Any]:
            statements = []
            for component in components:
                if hasattr(component, 'to_statements'):
                    statements.extend(component.to_statements())
                else:
                    statements.append(component)
            return statements
        return merge_transformer


class CpmOrderedFactory(ICpmFactory):
    """
    Ordered factory implementation that preserves statement order.
    """

    def __init__(self):
        self.strategy = ComponentStrategy.ORDERED
        self._statement_order = []

    def create_document(self, prov_document: ProvDocument) -> CpmDocument:
        return CpmOrderedDocument(prov_document, self)

    def create_node(self, element: Any) -> Any:
        return CpmOrderedNode(element, self)

    def create_edge(self, relation: Any) -> Any:
        return CpmOrderedEdge(relation, self)

    def get_components_transformer(self) -> Callable[[List[Any]], List[Any]]:
        def ordered_transformer(components: List[Any]) -> List[Any]:
            ordered_components = sorted(components,
                                        key=lambda c: self._get_component_order(c))

            statements = []
            for component in ordered_components:
                if hasattr(component, 'to_statements'):
                    statements.extend(component.to_statements())
                else:
                    statements.append(component)
            return statements
        return ordered_transformer

    def _get_component_order(self, component: Any) -> int:
        if hasattr(component, '_insertion_order'):
            return component._insertion_order
        return len(self._statement_order)

    def register_statement_order(self, statement: Any) -> int:
        order_index = len(self._statement_order)
        self._statement_order.append(statement)
        return order_index


class CpmDividedOrderedFactory(ICpmFactory):
    """
    Divided ordered factory that separates TI and DS components while preserving order.
    """

    def __init__(self):
        self.strategy = ComponentStrategy.DIVIDED_ORDERED
        self._ti_order = []
        self._ds_order = []

    def create_document(self, prov_document: ProvDocument) -> CpmDocument:
        return CpmDividedOrderedDocument(prov_document, self)

    def create_node(self, element: Any) -> Any:
        return CpmDividedOrderedNode(element, self)

    def create_edge(self, relation: Any) -> Any:
        return CpmDividedOrderedEdge(relation, self)

    def get_components_transformer(self) -> Callable[[List[Any]], List[Any]]:
        def divided_ordered_transformer(components: List[Any]) -> List[Any]:
            ti_components = []
            ds_components = []

            for component in components:
                if self._is_traversal_information_component(component):
                    ti_components.append(component)
                else:
                    ds_components.append(component)

            ti_components.sort(key=lambda c: self._get_ti_order(c))
            ds_components.sort(key=lambda c: self._get_ds_order(c))

            ordered_components = ti_components + ds_components

            statements = []
            for component in ordered_components:
                if hasattr(component, 'to_statements'):
                    statements.extend(component.to_statements())
                else:
                    statements.append(component)
            return statements
        return divided_ordered_transformer

    def _is_traversal_information_component(self, component: Any) -> bool:
        return getattr(component, '_is_ti', False)

    def _get_ti_order(self, component: Any) -> int:
        return getattr(component, '_ti_order', len(self._ti_order))

    def _get_ds_order(self, component: Any) -> int:
        return getattr(component, '_ds_order', len(self._ds_order))


class CpmDividedUnorderedFactory(ICpmFactory):
    """
    Divided unordered factory that separates TI and DS components without order guarantees.
    """

    def __init__(self):
        self.strategy = ComponentStrategy.DIVIDED_UNORDERED

    def create_document(self, prov_document: ProvDocument) -> CpmDocument:
        return CpmDividedUnorderedDocument(prov_document, self)

    def create_node(self, element: Any) -> Any:
        return CpmDividedUnorderedNode(element)

    def create_edge(self, relation: Any) -> Any:
        return CpmDividedUnorderedEdge(relation)

    def get_components_transformer(self) -> Callable[[List[Any]], List[Any]]:
        def divided_unordered_transformer(components: List[Any]) -> List[Any]:
            ti_components = []
            ds_components = []

            for component in components:
                if self._is_traversal_information_component(component):
                    ti_components.append(component)
                else:
                    ds_components.append(component)

            all_components = ti_components + ds_components

            statements = []
            for component in all_components:
                if hasattr(component, 'to_statements'):
                    statements.extend(component.to_statements())
                else:
                    statements.append(component)
            return statements
        return divided_unordered_transformer

    def _is_traversal_information_component(self, component: Any) -> bool:
        return getattr(component, '_is_ti', False)


class CpmProvFactory(ICpmProvFactory):
    """
    Vanilla implementation of CPM PROV factory.
    """

    def __init__(self, prov_factory: Optional[Any] = None):
        from prov.model import ProvDocument
        self.prov_factory = prov_factory or ProvDocument()

    def create_cpm_entity(self, identifier: QualifiedName, cpm_type: QualifiedName,
                          attributes: Optional[List[tuple]] = None) -> ProvEntity:
        from prov.constants import PROV_TYPE

        attr_list = [(PROV_TYPE, cpm_type)]
        if attributes:
            attr_list.extend(attributes)

        return self.prov_factory.entity(identifier, other_attributes=attr_list)

    def create_cpm_activity(self, identifier: QualifiedName, cpm_type: QualifiedName,
                            start_time: Optional[Any] = None, end_time: Optional[Any] = None,
                            attributes: Optional[List[tuple]] = None) -> ProvActivity:
        from prov.constants import PROV_TYPE

        attr_list = [(PROV_TYPE, cpm_type)]
        if attributes:
            attr_list.extend(attributes)

        return self.prov_factory.activity(identifier, startTime=start_time,
                                          endTime=end_time, other_attributes=attr_list)

    def create_cmp_agent(self, identifier: QualifiedName, cpm_type: QualifiedName,
                         attributes: Optional[List[tuple]] = None) -> ProvAgent:
        from prov.constants import PROV_TYPE

        attr_list = [(PROV_TYPE, cpm_type)]
        if attributes:
            attr_list.extend(attributes)

        return self.prov_factory.agent(identifier, other_attributes=attr_list)


# ========================
# NODE AND EDGE IMPLEMENTATIONS
# ========================

class CpmNode(ABC):
    """Base class for CPM node implementations"""

    def __init__(self, element: Any):
        self.element = element
        self._insertion_order = 0

    @abstractmethod
    def to_statements(self) -> List[Any]:
        pass


class CpmEdge(ABC):
    """Base class for CPM edge implementations"""

    def __init__(self, relation: Any):
        self.relation = relation
        self._insertion_order = 0

    @abstractmethod
    def to_statements(self) -> List[Any]:
        pass


class CpmMergedNode(CpmNode):
    """Merged implementation of CPM node"""

    def to_statements(self) -> List[Any]:
        return [self.element]


class CpmMergedEdge(CpmEdge):
    """Merged implementation of CPM edge"""

    def to_statements(self) -> List[Any]:
        return [self.relation]


class CpmOrderedNode(CpmNode):
    """Ordered implementation of CPM node"""

    def __init__(self, element: Any, factory: CpmOrderedFactory):
        super().__init__(element)
        self._insertion_order = factory.register_statement_order(element)

    def to_statements(self) -> List[Any]:
        return [self.element]


class CpmOrderedEdge(CpmEdge):
    """Ordered implementation of CPM edge"""

    def __init__(self, relation: Any, factory: CpmOrderedFactory):
        super().__init__(relation)
        self._insertion_order = factory.register_statement_order(relation)

    def to_statements(self) -> List[Any]:
        return [self.relation]


class CpmDividedOrderedNode(CpmNode):
    """Divided ordered implementation of CPM node"""

    def __init__(self, element: Any, factory: CpmDividedOrderedFactory):
        super().__init__(element)
        self._is_ti = self._determine_if_ti(element)
        if self._is_ti:
            self._ti_order = len(factory._ti_order)
            factory._ti_order.append(element)
        else:
            self._ds_order = len(factory._ds_order)
            factory._ds_order.append(element)

    def _determine_if_ti(self, element: Any) -> bool:
        from .model import TraversalInformationAlgorithm
        return TraversalInformationAlgorithm.belongs_to_traversal_information(element)

    def to_statements(self) -> List[Any]:
        return [self.element]


class CpmDividedOrderedEdge(CpmEdge):
    """Divided ordered implementation of CPM edge"""

    def __init__(self, relation: Any, factory: CpmDividedOrderedFactory):
        super().__init__(relation)
        self._is_ti = self._determine_if_ti_edge(relation)

    def _determine_if_ti_edge(self, relation: Any) -> bool:
        return True

    def to_statements(self) -> List[Any]:
        return [self.relation]


class CpmDividedUnorderedNode(CpmNode):
    """Divided unordered implementation of CPM node"""

    def __init__(self, element: Any):
        super().__init__(element)
        self._is_ti = self._determine_if_ti(element)

    def _determine_if_ti(self, element: Any) -> bool:
        from .model import TraversalInformationAlgorithm
        return TraversalInformationAlgorithm.belongs_to_traversal_information(element)

    def to_statements(self) -> List[Any]:
        return [self.element]


class CpmDividedUnorderedEdge(CpmEdge):
    """Divided unordered implementation of CPM edge"""

    def to_statements(self) -> List[Any]:
        return [self.relation]


# ========================
# SPECIALIZED DOCUMENT IMPLEMENTATIONS
# ========================

class CpmOrderedDocument(CpmDocument):
    """
    CPM document that preserves statement order.
    """

    def __init__(self, prov_document: ProvDocument, factory: CpmOrderedFactory):
        super().__init__(prov_document)
        self.factory = factory

    def to_prov_document(self) -> ProvDocument:
        doc = super().to_prov_document()

        for bundle in doc.bundles:
            if hasattr(bundle, '_records'):
                ordered_records = sorted(bundle._records,
                                         key=lambda r: self._get_statement_order(r))
                bundle._records = ordered_records

        return doc

    def _get_statement_order(self, statement: Any) -> int:
        try:
            return self.factory._statement_order.index(statement)
        except ValueError:
            return len(self.factory._statement_order)


class CpmDividedOrderedDocument(CpmDocument):
    """
    CPM document that separates TI/DS and preserves order within each part.
    """

    def __init__(self, prov_document: ProvDocument, factory: CpmDividedOrderedFactory):
        super().__init__(prov_document)
        self.factory = factory

    def get_traversal_information_part_ordered(self) -> List[Any]:
        ti_nodes = self.get_traversal_information_nodes()
        return sorted(ti_nodes, key=lambda n: self._get_ti_order(n))

    def get_domain_specific_part_ordered(self) -> List[Any]:
        ds_nodes = self.get_domain_specific_nodes()
        return sorted(ds_nodes, key=lambda n: self._get_ds_order(n))

    def _get_ti_order(self, node: Any) -> int:
        if hasattr(node, 'prov_entity'):
            try:
                return self.factory._ti_order.index(node.prov_entity)
            except ValueError:
                pass
        return len(self.factory._ti_order)

    def _get_ds_order(self, node: Any) -> int:
        if hasattr(node, 'prov_entity'):
            try:
                return self.factory._ds_order.index(node.prov_entity)
            except ValueError:
                pass
        return len(self.factory._ds_order)


class CpmDividedUnorderedDocument(CpmDocument):
    """
    CPM document that separates TI/DS without order guarantees.
    """

    def __init__(self, prov_document: ProvDocument, factory: CpmDividedUnorderedFactory):
        super().__init__(prov_document)
        self.factory = factory

    def get_separated_parts(self) -> Dict[str, List[Any]]:
        ti_nodes = self.get_traversal_information_nodes()
        ds_nodes = self.get_domain_specific_nodes()

        return {
            'traversal_information': ti_nodes,
            'domain_specific': ds_nodes,
            'cross_part_edges': self.get_cross_part_edges()
        }


# ========================
# FACTORY REGISTRY AND UTILITIES
# ========================

class CpmFactoryRegistry:
    """Registry for CPM factory instances"""

    _factories = {
        ComponentStrategy.MERGED: CpmMergedFactory,
        ComponentStrategy.ORDERED: CpmOrderedFactory,
        ComponentStrategy.DIVIDED_ORDERED: CpmDividedOrderedFactory,
        ComponentStrategy.DIVIDED_UNORDERED: CpmDividedUnorderedFactory
    }

    _prov_factories = {
        'vanilla': CpmProvFactory
    }

    # Cache for factory instances
    _factory_instances = {}
    _prov_factory_instances = {}

    @classmethod
    def get_factory(cls, strategy: ComponentStrategy) -> ICpmFactory:
        # Return cached instance if exists
        if strategy in cls._factory_instances:
            return cls._factory_instances[strategy]

        # Create new instance and cache it
        factory_class = cls._factories.get(strategy)
        if not factory_class:
            raise ValueError(f"Unknown factory strategy: {strategy}")

        instance = factory_class()
        cls._factory_instances[strategy] = instance
        return instance

    @classmethod
    def get_prov_factory(cls, factory_type: str = 'vanilla') -> ICpmProvFactory:
        # Return cached instance if exists
        if factory_type in cls._prov_factory_instances:
            return cls._prov_factory_instances[factory_type]

        # Create new instance and cache it
        factory_class = cls._prov_factories.get(factory_type)
        if not factory_class:
            raise ValueError(f"Unknown PROV factory type: {factory_type}")

        instance = factory_class()
        cls._prov_factory_instances[factory_type] = instance
        return instance

    @classmethod
    def register_factory(cls, strategy: ComponentStrategy, factory_class: type):
        cls._factories[strategy] = factory_class

    @classmethod
    def register_prov_factory(cls, factory_type: str, factory_class: type):
        cls._prov_factories[factory_type] = factory_class


class CpmDocumentFactory:
    """
    High-level factory for creating CPM documents with different strategies.
    """

    @staticmethod
    def create_merged_document(prov_document: ProvDocument) -> CpmDocument:
        factory = CpmFactoryRegistry.get_factory(ComponentStrategy.MERGED)
        return factory.create_document(prov_document)

    @staticmethod
    def create_ordered_document(prov_document: ProvDocument) -> CpmOrderedDocument:
        factory = CpmFactoryRegistry.get_factory(ComponentStrategy.ORDERED)
        return factory.create_document(prov_document)

    @staticmethod
    def create_divided_ordered_document(prov_document: ProvDocument) -> CpmDividedOrderedDocument:
        factory = CpmFactoryRegistry.get_factory(ComponentStrategy.DIVIDED_ORDERED)
        return factory.create_document(prov_document)

    @staticmethod
    def create_divided_unordered_document(prov_document: ProvDocument) -> CpmDividedUnorderedDocument:
        factory = CpmFactoryRegistry.get_factory(ComponentStrategy.DIVIDED_UNORDERED)
        return factory.create_document(prov_document)

    @staticmethod
    def create_from_template_with_strategy(template: Any, strategy: ComponentStrategy,
                                           domain_specific_doc: Optional[ProvDocument] = None) -> CpmDocument:
        from .model import TemplateProvMapper

        mapper = TemplateProvMapper()
        ti_doc = mapper.map_to_document(template)

        if domain_specific_doc:
            ti_doc.update(domain_specific_doc)

        factory = CpmFactoryRegistry.get_factory(strategy)
        return factory.create_document(ti_doc)


# ========================
# UTILITIES AND HELPER CLASSES
# ========================

class CpmUtilities:
    """
    Utility functions for CPM operations.
    """

    @staticmethod
    def has_cpm_type(element: Any, cpm_type: QualifiedName) -> bool:
        from prov.constants import PROV_TYPE

        if hasattr(element, 'get_attribute'):
            types = element.get_attribute(PROV_TYPE)
            return cmp_type in types if types else False
        return False

    @staticmethod
    def is_connector(element: Any) -> bool:
        from .constants import CPM_FORWARD_CONNECTOR, CPM_BACKWARD_CONNECTOR

        return (CpmUtilities.has_cpm_type(element, CPM_FORWARD_CONNECTOR) or
                CmpUtilities.has_cpm_type(element, CPM_BACKWARD_CONNECTOR))

    @staticmethod
    def belongs_to_cpm_namespace(qname: QualifiedName) -> bool:
        return str(qname).startswith('cpm:') if qname else False

    @staticmethod
    def extract_cpm_attributes(element: Any) -> Dict[str, Any]:
        cpm_attrs = {}
        if hasattr(element, 'attributes'):
            for attr_name, attr_value in element.attributes:
                if CpmUtilities.belongs_to_cpm_namespace(attr_name):
                    cmp_attrs[str(attr_name)] = attr_value
        return cpm_attrs


class ProvUtilities2:
    """
    Extended PROV utilities for CPM operations.
    """

    @staticmethod
    def same_edge(relation1: Any, relation2: Any) -> bool:
        if type(relation1) != type(relation2):
            return False

        if hasattr(relation1, 'identifier') and hasattr(relation2, 'identifier'):
            if relation1.identifier and relation2.identifier:
                return relation1.identifier == relation2.identifier

        endpoints1 = ProvUtilities2.get_relation_endpoints(relation1)
        endpoints2 = ProvUtilities2.get_relation_endpoints(relation2)

        return endpoints1 == endpoints2

    @staticmethod
    def get_relation_endpoints(relation: Any) -> tuple:
        try:
            if hasattr(relation, 'entity') and hasattr(relation, 'activity'):
                return (relation.activity, relation.entity)
            elif hasattr(relation, 'generatedEntity') and hasattr(relation, 'usedEntity'):
                return (relation.usedEntity, relation.generatedEntity)
            elif hasattr(relation, 'agent') and hasattr(relation, 'entity'):
                return (relation.agent, relation.entity)
        except:
            pass
        return (None, None)

    @staticmethod
    def get_effect_kind(edge_kind: str) -> str:
        kind_mappings = {
            'usage': 'activity',
            'generation': 'entity',
            'derivation': 'entity',
            'attribution': 'entity',
            'association': 'activity'
        }
        return kind_mappings.get(edge_kind.lower(), 'entity')

    @staticmethod
    def get_cause_kind(edge_kind: str) -> str:
        kind_mappings = {
            'usage': 'entity',
            'generation': 'activity',
            'derivation': 'entity',
            'attribution': 'agent',
            'association': 'agent'
        }
        return kind_mappings.get(edge_kind.lower(), 'entity')
