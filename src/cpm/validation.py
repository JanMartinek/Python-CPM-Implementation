"""
Enhanced CPM Validation

Advanced validation system including cross-part edge detection, 
traversal information strategy, and comprehensive graph validation.
"""

from .template import TraversalInformationTemplate
from src.graph.edge import GraphEdge
from src.graph.node import GraphNode
from src.graph.wrapper import ProvGraphWrapper
from typing import List, Dict, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from prov.model import ProvDocument, ProvBundle, ProvRecord, ProvRelation
from prov.identifier import QualifiedName


class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationType(Enum):
    """Types of validation checks"""
    STRUCTURAL = "STRUCTURAL"
    SEMANTIC = "SEMANTIC"
    TEMPLATE_COMPLIANCE = "TEMPLATE_COMPLIANCE"
    CROSS_PART = "CROSS_PART"
    TRAVERSAL = "TRAVERSAL"


@dataclass
class ValidationResult:
    """Individual validation result"""
    level: ValidationLevel
    validation_type: ValidationType
    message: str
    node_id: Optional[QualifiedName] = None
    edge_id: Optional[QualifiedName] = None
    bundle_id: Optional[QualifiedName] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationReport:
    """Complete validation report"""
    results: List[ValidationResult]
    is_valid: bool
    error_count: int
    warning_count: int
    info_count: int

    def get_errors(self) -> List[ValidationResult]:
        return [r for r in self.results if r.level == ValidationLevel.ERROR]

    def get_warnings(self) -> List[ValidationResult]:
        return [r for r in self.results if r.level == ValidationLevel.WARNING]

    def get_by_type(self, validation_type: ValidationType) -> List[ValidationResult]:
        return [r for r in self.results if r.validation_type == validation_type]


class TraversalInformationStrategy:
    """
    Strategy for handling cross-part edge detection and traversal information.
    """

    def __init__(self):
        self._cross_part_edges: Set[Tuple[QualifiedName, QualifiedName]] = set()
        self._part_boundaries: Dict[QualifiedName, Set[QualifiedName]] = {}
        self._traversal_cache: Dict[str, Any] = {}

    def detect_cross_part_edges(self, wrapper: ProvGraphWrapper) -> List[GraphEdge]:
        """
        Detect edges that cross part boundaries.

        Args:
            wrapper: Graph wrapper to analyze

        Returns:
            List of edges that cross part boundaries
        """
        cross_part_edges = []

        # Build part mapping from bundles
        part_mapping = self._build_part_mapping(wrapper)

        for edge in wrapper.get_edges():
            cause_part = part_mapping.get(edge.cause.identifier)
            effect_part = part_mapping.get(edge.effect.identifier)

            if cause_part and effect_part and cause_part != effect_part:
                cross_part_edges.append(edge)
                self._cross_part_edges.add((edge.cause.identifier, edge.effect.identifier))

        return cross_part_edges

    def _build_part_mapping(self, wrapper: ProvGraphWrapper) -> Dict[QualifiedName, QualifiedName]:
        """Build mapping from node identifiers to part identifiers"""
        part_mapping = {}

        # Fix: Use _prov_document instead of document
        doc = wrapper._prov_document
        if hasattr(doc, 'bundles') and doc.bundles:
            # Fix: doc.bundles is a dict_values object, need to iterate directly
            try:
                # Try to iterate over bundles directly
                for bundle in doc.bundles:
                    bundle_id = bundle.identifier if hasattr(bundle, 'identifier') else None
                    # All elements in a bundle belong to the same part
                    if hasattr(bundle, 'records') and bundle.records:
                        for record in bundle.records:
                            if hasattr(record, 'identifier') and record.identifier:
                                part_mapping[record.identifier] = bundle_id
            except AttributeError:
                # Fallback: try as dictionary if direct iteration fails
                try:
                    if hasattr(doc.bundles, 'items'):
                        for bundle_id, bundle in doc.bundles.items():
                            if hasattr(bundle, 'records') and bundle.records:
                                for record in bundle.records:
                                    if hasattr(record, 'identifier') and record.identifier:
                                        part_mapping[record.identifier] = bundle_id
                except Exception:
                    pass  # Skip if bundle structure is not as expected

        return part_mapping

    def get_traversal_information(self, edge: GraphEdge) -> Dict[str, Any]:
        """
        Get traversal information for an edge.

        Args:
            edge: Edge to analyze

        Returns:
            Dictionary containing traversal information
        """
        cache_key = f"{edge.cause.identifier}_{edge.effect.identifier}"

        if cache_key in self._traversal_cache:
            return self._traversal_cache[cache_key]

        info = {
            'is_cross_part': (edge.cause.identifier, edge.effect.identifier) in self._cross_part_edges,
            'relation_type': edge.kind,
            'cause_id': edge.cause.identifier,
            'effect_id': edge.effect.identifier,
            'attributes': edge.get_attributes(),
            'traversal_cost': self._calculate_traversal_cost(edge)
        }

        self._traversal_cache[cache_key] = info
        return info

    def _calculate_traversal_cost(self, edge: GraphEdge) -> float:
        """Calculate traversal cost for an edge"""
        base_cost = 1.0

        # Cross-part edges have higher cost
        if (edge.cause.identifier, edge.effect.identifier) in self._cross_part_edges:
            base_cost *= 2.0

        # Different relation types have different costs
        relation_costs = {
            'PROV_GENERATION': 1.0,
            'PROV_USAGE': 1.0,
            'PROV_DERIVATION': 1.5,
            'PROV_ASSOCIATION': 1.2,
            'PROV_ATTRIBUTION': 1.2,
            'PROV_COMMUNICATION': 2.0,
            'PROV_DELEGATION': 2.0
        }

        return base_cost * relation_costs.get(edge.kind, 1.0)

    def clear_cache(self):
        """Clear traversal cache"""
        self._traversal_cache.clear()


class CpmValidator:
    """
    CPM validator with comprehensive validation capabilities.
    """

    def __init__(self):
        self.traversal_strategy = TraversalInformationStrategy()
        self._validation_rules: List[callable] = []
        self._register_default_rules()

    def _register_default_rules(self):
        """Register default validation rules"""
        self._validation_rules.extend([
            self._validate_node_integrity,
            self._validate_edge_integrity,
            self._validate_prov_constraints,
            self._validate_cross_part_consistency,
            self._validate_traversal_properties,
            self._validate_bundle_structure,
            self._validate_identifier_uniqueness,
            self._validate_attribute_consistency
        ])

    def validate(self, wrapper: ProvGraphWrapper,
                 template: Optional[TraversalInformationTemplate] = None) -> ValidationReport:
        """
        Perform comprehensive validation of a CPM graph.

        Args:
            wrapper: Graph wrapper to validate
            template: Optional template for compliance checking

        Returns:
            Complete validation report
        """
        results = []

        # Run all validation rules
        for rule in self._validation_rules:
            try:
                rule_results = rule(wrapper, template)
                if isinstance(rule_results, list):
                    results.extend(rule_results)
                elif rule_results:
                    results.append(rule_results)
            except Exception as e:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    validation_type=ValidationType.STRUCTURAL,
                    message=f"Validation rule failed: {str(e)}",
                    details={'exception': str(e), 'rule': rule.__name__}
                ))

        # Template compliance validation
        if template:
            template_results = self._validate_template_compliance(wrapper, template)
            results.extend(template_results)

        # Compile report
        error_count = len([r for r in results if r.level == ValidationLevel.ERROR])
        warning_count = len([r for r in results if r.level == ValidationLevel.WARNING])
        info_count = len([r for r in results if r.level == ValidationLevel.INFO])

        return ValidationReport(
            results=results,
            is_valid=error_count == 0,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count
        )

    def _validate_node_integrity(self, wrapper: ProvGraphWrapper,
                                 template: Optional[TraversalInformationTemplate] = None) -> List[ValidationResult]:
        results = []

        for node in wrapper.get_nodes():
            if not node.identifier:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    validation_type=ValidationType.STRUCTURAL,
                    message="Node missing identifier",
                    node_id=node.identifier
                ))

            elements = node.elements
            if not elements:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    validation_type=ValidationType.STRUCTURAL,
                    message="Node has no elements",
                    node_id=node.identifier
                ))

            if node.is_isolated():
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    validation_type=ValidationType.STRUCTURAL,
                    message="Isolated node detected",
                    node_id=node.identifier
                ))

        return results

    def _validate_edge_integrity(self, wrapper: ProvGraphWrapper,
                                 template: Optional[TraversalInformationTemplate] = None) -> List[ValidationResult]:
        results = []

        for edge in wrapper.get_edges():
            if not edge.cause:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    validation_type=ValidationType.STRUCTURAL,
                    message="Edge missing cause node",
                    edge_id=edge.identifier
                ))

            if not edge.effect:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    validation_type=ValidationType.STRUCTURAL,
                    message="Edge missing effect node",
                    edge_id=edge.identifier
                ))

            relations = edge.get_relations()
            if not relations:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    validation_type=ValidationType.STRUCTURAL,
                    message="Edge has no relations",
                    edge_id=edge.identifier
                ))

            if edge.cause == edge.effect:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    validation_type=ValidationType.STRUCTURAL,
                    message="Self-loop edge detected",
                    edge_id=edge.identifier
                ))

        return results

    def _validate_prov_constraints(self, wrapper: ProvGraphWrapper,
                                   template: Optional[TraversalInformationTemplate] = None) -> List[ValidationResult]:
        results = []

        for edge in wrapper.get_edges():
            kind = edge.kind
            cause_kind = edge.cause.kind
            effect_kind = edge.effect.kind

            if kind == 'PROV_USAGE':
                if cause_kind != 'PROV_ENTITY' or effect_kind != 'PROV_ACTIVITY':
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        validation_type=ValidationType.SEMANTIC,
                        message=f"Invalid Usage relation: {cause_kind} -> {effect_kind}",
                        edge_id=edge.identifier
                    ))

            elif kind == 'PROV_GENERATION':
                if cause_kind != 'PROV_ACTIVITY' or effect_kind != 'PROV_ENTITY':
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        validation_type=ValidationType.SEMANTIC,
                        message=f"Invalid Generation relation: {cause_kind} -> {effect_kind}",
                        edge_id=edge.identifier
                    ))

            elif kind == 'PROV_ASSOCIATION':
                if cause_kind != 'PROV_ACTIVITY' or effect_kind != 'PROV_AGENT':
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        validation_type=ValidationType.SEMANTIC,
                        message=f"Invalid Association relation: {cause_kind} -> {effect_kind}",
                        edge_id=edge.identifier
                    ))

        return results

    def _validate_cross_part_consistency(self, wrapper: ProvGraphWrapper,
                                         template: Optional[TraversalInformationTemplate] = None) -> List[ValidationResult]:
        results = []

        cross_part_edges = self.traversal_strategy.detect_cross_part_edges(wrapper)

        for edge in cross_part_edges:
            traversal_info = self.traversal_strategy.get_traversal_information(edge)

            if not traversal_info.get('is_cross_part'):
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    validation_type=ValidationType.CROSS_PART,
                    message="Cross-part edge not properly marked",
                    edge_id=edge.identifier
                ))

            cost = traversal_info.get('traversal_cost', 0)
            if cost > 10.0:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    validation_type=ValidationType.TRAVERSAL,
                    message=f"High traversal cost: {cost}",
                    edge_id=edge.identifier,
                    details={'traversal_cost': cost}
                ))

        return results

    def _validate_traversal_properties(self, wrapper: ProvGraphWrapper,
                                       template: Optional[TraversalInformationTemplate] = None) -> List[ValidationResult]:
        results = []

        nodes = wrapper.get_nodes()
        if len(nodes) > 1:
            visited = set()

            def dfs(node, visited_set):
                if node in visited_set:
                    return
                visited_set.add(node)
                for connected_node in node.get_connected_nodes():
                    dfs(connected_node, visited_set)

            if nodes:
                dfs(nodes[0], visited)

                if len(visited) < len(nodes):
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        validation_type=ValidationType.TRAVERSAL,
                        message=f"Graph not fully connected: {len(visited)}/{len(nodes)} nodes reachable",
                        details={'reachable_nodes': len(visited), 'total_nodes': len(nodes)}
                    ))

        return results

    def _validate_bundle_structure(self, wrapper: ProvGraphWrapper,
                                   template: Optional[TraversalInformationTemplate] = None) -> List[ValidationResult]:
        results = []

        doc = wrapper._prov_document
        if hasattr(doc, 'bundles') and doc.bundles:
            try:
                for bundle in doc.bundles:
                    bundle_id = bundle.identifier if hasattr(bundle, 'identifier') else None
                    if not hasattr(bundle, 'records') or not bundle.records:
                        results.append(ValidationResult(
                            level=ValidationLevel.WARNING,
                            validation_type=ValidationType.STRUCTURAL,
                            message="Empty bundle detected",
                            bundle_id=bundle_id
                        ))
            except AttributeError:
                try:
                    if hasattr(doc.bundles, 'items'):
                        for bundle_id, bundle in doc.bundles.items():
                            if not hasattr(bundle, 'records') or not bundle.records:
                                results.append(ValidationResult(
                                    level=ValidationLevel.WARNING,
                                    validation_type=ValidationType.STRUCTURAL,
                                    message="Empty bundle detected",
                                    bundle_id=bundle_id
                                ))
                except Exception:
                    pass
        else:
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                validation_type=ValidationType.STRUCTURAL,
                message="No bundles found in document"
            ))

        return results

    def _validate_identifier_uniqueness(self, wrapper: ProvGraphWrapper,
                                        template: Optional[TraversalInformationTemplate] = None) -> List[ValidationResult]:
        results = []

        node_ids = {}
        edge_ids = {}

        for node in wrapper.get_nodes():
            if node.identifier:
                if node.identifier in node_ids:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        validation_type=ValidationType.STRUCTURAL,
                        message=f"Duplicate node identifier: {node.identifier}",
                        node_id=node.identifier
                    ))
                else:
                    node_ids[node.identifier] = node

        for edge in wrapper.get_edges():
            if edge.identifier:
                if edge.identifier in edge_ids:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        validation_type=ValidationType.STRUCTURAL,
                        message=f"Duplicate edge identifier: {edge.identifier}",
                        edge_id=edge.identifier
                    ))
                else:
                    edge_ids[edge.identifier] = edge

        return results

    def _validate_attribute_consistency(self, wrapper: ProvGraphWrapper,
                                        template: Optional[TraversalInformationTemplate] = None) -> List[ValidationResult]:
        results = []

        for node in wrapper.get_nodes():
            elements = node.elements
            if len(elements) > 1:
                types = set()
                for element in elements:
                    if hasattr(element, 'get_type'):
                        element_type = element.get_type()
                        if element_type:
                            types.add(str(element_type))

                if len(types) > 1:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        validation_type=ValidationType.SEMANTIC,
                        message=f"Node has elements with inconsistent types: {types}",
                        node_id=node.identifier,
                        details={'types': list(types)}
                    ))

        return results

    def _validate_template_compliance(self, wrapper: ProvGraphWrapper,
                                      template: TraversalInformationTemplate) -> List[ValidationResult]:
        results = []

        if not template:
            return results

        from .constants import CPM_MAIN_ACTIVITY, CPM_BACKWARD_CONNECTOR, CPM_FORWARD_CONNECTOR

        main_activities = []
        for node in wrapper.get_nodes():
            node_types = node.get_prov_attribute('prov:type') or []
            if any(str(CPM_MAIN_ACTIVITY) in str(t) or 'MainActivity' in str(t) for t in node_types):
                main_activities.append(node)

        if not main_activities:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                validation_type=ValidationType.TEMPLATE_COMPLIANCE,
                message="Missing required main activity",
                details={'template_main_activity': template.main_activity.id}
            ))

        backward_connectors = []
        forward_connectors = []

        for node in wrapper.get_nodes():
            node_types = node.get_prov_attribute('prov:type') or []
            if any(str(CPM_BACKWARD_CONNECTOR) in str(t) or 'BackwardConnector' in str(t) for t in node_types):
                backward_connectors.append(node)
            elif any(str(CPM_FORWARD_CONNECTOR) in str(t) or 'ForwardConnector' in str(t) for t in node_types):
                forward_connectors.append(node)

        if template.backward_connectors and not backward_connectors:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                validation_type=ValidationType.TEMPLATE_COMPLIANCE,
                message="Template specifies backward connectors but none found in graph",
                details={'expected_backward_connectors': len(template.backward_connectors)}
            ))

        if template.forward_connectors and not forward_connectors:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                validation_type=ValidationType.TEMPLATE_COMPLIANCE,
                message="Template specifies forward connectors but none found in graph",
                details={'expected_forward_connectors': len(template.forward_connectors)}
            ))

        return results

    def add_validation_rule(self, rule: callable):
        """Add a custom validation rule"""
        self._validation_rules.append(rule)

    def remove_validation_rule(self, rule: callable):
        """Remove a validation rule"""
        if rule in self._validation_rules:
            self._validation_rules.remove(rule)


def validate_cpm_graph(wrapper: ProvGraphWrapper,
                       template: Optional[TraversalInformationTemplate] = None,
                       validator: Optional[CpmValidator] = None) -> ValidationReport:
    """
    Convenience function to validate a CPM graph.

    Args:
        wrapper: Graph wrapper to validate
        template: Optional template for compliance checking
        validator: Optional custom validator instance

    Returns:
        ValidationReport with results
    """
    if not validator:
        validator = CpmValidator()

    return validator.validate(wrapper, template)


def create_validation_rule(validation_type: ValidationType, level: ValidationLevel):
    """
    Decorator to create custom validation rules.

    Args:
        validation_type: Type of validation
        level: Severity level

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(wrapper: ProvGraphWrapper, template: Optional[TraversalInformationTemplate] = None):
            try:
                messages = func(wrapper, template)
                if isinstance(messages, str):
                    messages = [messages]

                return [ValidationResult(
                    level=level,
                    validation_type=validation_type,
                    message=msg
                ) for msg in messages if msg]

            except Exception as e:
                return ValidationResult(
                    level=ValidationLevel.ERROR,
                    validation_type=validation_type,
                    message=f"Validation rule error: {str(e)}",
                    details={'exception': str(e)}
                )

        return wrapper
    return decorator
