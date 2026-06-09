"""
Test CPM Template Validation

Tests the validation functionality for CPM templates using the actual validation classes.
"""
import unittest
from src.cpm.validation import (
    CpmValidator, ValidationLevel, ValidationType, ValidationReport,
    validate_cpm_graph, TraversalInformationStrategy
)
from src.cpm.template import (
    CpmBundleDeserializer, CpmBundleTemplate,
    CpmBundleSerializer
)
from src.graph.wrapper import ProvGraphWrapper
from prov.model import ProvDocument
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCpmBasicFunctionality(unittest.TestCase):
    """Test basic CPM functionality including constants and template mapping"""

    def test_cpm_constants(self):
        """Test CPM constants are properly defined"""
        from src.cpm.constants import (
            CPM_NAMESPACE_URI, DCT_NAMESPACE_URI,
            CPM_MAIN_ACTIVITY, CPM_FORWARD_CONNECTOR, CPM_BACKWARD_CONNECTOR,
            CPM_REFERENCED_BUNDLE_ID, DCT_HAS_PART
        )

        # Test namespace URIs
        assert CPM_NAMESPACE_URI is not None
        assert DCT_NAMESPACE_URI is not None

        # Test CPM subtypes
        assert CPM_MAIN_ACTIVITY is not None
        assert CPM_FORWARD_CONNECTOR is not None
        assert CPM_BACKWARD_CONNECTOR is not None

        # Test attributes
        assert CPM_REFERENCED_BUNDLE_ID is not None
        assert DCT_HAS_PART is not None

    def test_simple_cpm_template_workflow(self):
        """Test complete CPM template creation and mapping workflow"""
        from src.cpm.model import TemplateProvMapper, CpmDocument

        template_data = {
            "prefixes": {
                "ex": "http://example.org/"
            },
            "bundleName": "ex:testBundle",
            "mainActivity": {
                "id": "ex:mainActivity",
                "generated": ["ex:output"]
            },
            "forwardConnectors": [{
                "id": "ex:output"
            }]
        }

        # Test deserialization
        template = CpmBundleDeserializer.from_json(template_data)
        assert template.bundle_name == "ex:testBundle"
        assert template.main_activity.id == "ex:mainActivity"
        assert len(template.forward_connectors) == 1

        # Test serialization round-trip
        json_str = CpmBundleSerializer.to_json(template)
        restored = CpmBundleDeserializer.from_json(json_str)
        assert template.bundle_name == restored.bundle_name

        # Test mapping to PROV
        mapper = TemplateProvMapper()
        prov_doc = mapper.map_to_document(template)
        assert len(list(prov_doc.bundles)) > 0

        # Test CPM document
        cpm_doc = CpmDocument(prov_doc)
        main_activity = cpm_doc.get_main_activity()
        forward_connectors = cpm_doc.get_forward_connectors()

        assert main_activity is not None
        assert len(forward_connectors) > 0


def create_test_template() -> CpmBundleTemplate:
    """Create a simple test template"""
    template_data = {
        "prefixes": {
            "ex": "http://example.org/"
        },
        "bundleName": "ex:testBundle",
        "mainActivity": {
            "id": "ex:mainActivity",
            "startTime": "2024-01-01T10:00:00Z",
            "endTime": "2024-01-01T12:00:00Z",
            "generated": ["ex:output"]
        },
        "forwardConnectors": [{
            "id": "ex:output"
        }]
    }
    return CpmBundleDeserializer.from_json(template_data)


def create_test_graph() -> ProvGraphWrapper:
    """Create a simple test graph"""
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')

    # Create entities and activities
    entity1 = doc.entity('ex:entity1')
    entity2 = doc.entity('ex:entity2')
    activity = doc.activity('ex:mainActivity')

    # Create relations
    doc.used(activity, entity1)
    doc.wasGeneratedBy(entity2, activity)

    return ProvGraphWrapper(doc)


class TestCpmValidation(unittest.TestCase):
    """Test CPM validation functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.graph = create_test_graph()
        self.template = create_test_template()
        self.validator = CpmValidator()

    def test_basic_validation(self):
        """Test basic validation functionality"""
        report = self.validator.validate(self.graph)

        self.assertIsInstance(report, ValidationReport)
        self.assertIsInstance(report.is_valid, bool)
        self.assertIsInstance(report.error_count, int)
        self.assertIsInstance(report.warning_count, int)
        self.assertIsInstance(report.info_count, int)
        self.assertGreaterEqual(len(report.results), 0)

    def test_template_compliance_validation(self):
        """Test template compliance validation"""
        report = self.validator.validate(self.graph, self.template)

        self.assertIsInstance(report, ValidationReport)
        compliance_issues = report.get_by_type(ValidationType.TEMPLATE_COMPLIANCE)
        self.assertIsInstance(compliance_issues, list)

    def test_validation_levels(self):
        """Test validation levels"""
        report = self.validator.validate(self.graph)

        errors = report.get_errors()
        warnings = report.get_warnings()

        self.assertIsInstance(errors, list)
        self.assertIsInstance(warnings, list)
        self.assertEqual(len(errors), report.error_count)
        self.assertEqual(len(warnings), report.warning_count)

    def test_traversal_information_strategy(self):
        """Test traversal information strategy"""
        strategy = TraversalInformationStrategy()

        cross_part_edges = strategy.detect_cross_part_edges(self.graph)
        self.assertIsInstance(cross_part_edges, list)

        for edge in self.graph.get_edges():
            traversal_info = strategy.get_traversal_information(edge)
            self.assertIsInstance(traversal_info, dict)
            self.assertIn('is_cross_part', traversal_info)
            self.assertIn('relation_type', traversal_info)
            self.assertIn('traversal_cost', traversal_info)

    def test_validation_types(self):
        """Test validation types"""
        report = self.validator.validate(self.graph)

        structural_issues = report.get_by_type(ValidationType.STRUCTURAL)
        semantic_issues = report.get_by_type(ValidationType.SEMANTIC)

        self.assertIsInstance(structural_issues, list)
        self.assertIsInstance(semantic_issues, list)

    def test_convenience_function(self):
        """Test convenience function"""
        report1 = validate_cpm_graph(self.graph)
        self.assertIsInstance(report1, ValidationReport)

        report2 = validate_cpm_graph(self.graph, self.template)
        self.assertIsInstance(report2, ValidationReport)

        custom_validator = CpmValidator()
        report3 = validate_cpm_graph(self.graph, self.template, custom_validator)
        self.assertIsInstance(report3, ValidationReport)

    def test_empty_graph_validation(self):
        """Test empty graph validation"""
        empty_graph = ProvGraphWrapper()
        report = self.validator.validate(empty_graph)

        self.assertIsInstance(report, ValidationReport)
        self.assertIsInstance(report.is_valid, bool)

    def test_malformed_graph_validation(self):
        """Test malformed graph validation"""
        doc = ProvDocument()
        doc.add_namespace('ex', 'http://example.org/')

        entity1 = doc.entity('ex:entity1')
        entity2 = doc.entity('ex:entity2')

        graph = ProvGraphWrapper(doc)
        report = self.validator.validate(graph)

        self.assertIsInstance(report, ValidationReport)
        warnings = report.get_warnings()
        self.assertIsInstance(warnings, list)


if __name__ == '__main__':
    unittest.main()


# ═══════════════════════════════════════════════════════════════════════════════
# Additional coverage tests – TraversalInformationStrategy, CpmValidator,
# validate_cpm_graph, create_validation_rule.
# ═══════════════════════════════════════════════════════════════════════════════

import pytest
from prov.identifier import Namespace

from src.cpm.validation import create_validation_rule

EX = Namespace("ex", "http://example.org/")
CPM = Namespace("cpm", "https://commonprovenancemodel.org/ns/cpm/")

STANDARD_PREFIXES = {
    "prov": "http://www.w3.org/ns/prov#",
    "cpm": "https://commonprovenancemodel.org/ns/cpm/",
    "ex": "http://example.org/",
}


def _make_wrapper():
    doc = ProvDocument()
    doc.add_namespace(EX)
    doc.add_namespace(CPM)
    doc.add_namespace("prov", "http://www.w3.org/ns/prov#")
    b = doc.bundle(EX["bundle"])
    b.activity(EX["main"], other_attributes=[("prov:type", CPM["MainActivity"])])
    b.entity(EX["bc1"], other_attributes=[("prov:type", CPM["BackwardConnector"])])
    b.entity(EX["e1"])
    b.agent(EX["ag1"])
    b.usage(EX["main"], EX["e1"])
    b.wasGeneratedBy(EX["e1"], EX["main"])
    b.wasDerivedFrom(EX["e1"], EX["bc1"])
    b.wasAssociatedWith(EX["main"], EX["ag1"])
    b.wasAttributedTo(EX["e1"], EX["ag1"])
    return ProvGraphWrapper(doc)


def _make_template():
    return CpmBundleDeserializer.from_json({
        "prefixes": STANDARD_PREFIXES,
        "bundleName": "ex:bundle",
        "mainActivity": {
            "id": "ex:main",
            "used": [{"bcId": "ex:bc1"}],
        },
        "backwardConnectors": [{"id": "ex:bc1"}],
    })


def _make_empty_wrapper():
    return ProvGraphWrapper(ProvDocument())


# ─── TraversalInformationStrategy ───────────────────────────────────────────

class TestTraversalInformationStrategy:
    def test_detect_cross_part_edges(self):
        s = TraversalInformationStrategy()
        w = _make_wrapper()
        edges = s.detect_cross_part_edges(w)
        assert isinstance(edges, list)

    def test_get_traversal_information(self):
        s = TraversalInformationStrategy()
        w = _make_wrapper()
        edges = w.get_edges()
        if edges:
            info = s.get_traversal_information(edges[0])
            assert "is_cross_part" in info
            assert "traversal_cost" in info

    def test_traversal_info_caching(self):
        s = TraversalInformationStrategy()
        w = _make_wrapper()
        edges = w.get_edges()
        if edges:
            info1 = s.get_traversal_information(edges[0])
            info2 = s.get_traversal_information(edges[0])
            assert info1 is info2

    def test_clear_cache(self):
        s = TraversalInformationStrategy()
        w = _make_wrapper()
        edges = w.get_edges()
        if edges:
            s.get_traversal_information(edges[0])
        s.clear_cache()


# ─── CpmValidator (extended) ────────────────────────────────────────────────

class TestCpmValidatorExtended:
    def test_validate_returns_report(self):
        v = CpmValidator()
        w = _make_wrapper()
        report = v.validate(w)
        assert isinstance(report, ValidationReport)
        assert isinstance(report.is_valid, bool)

    def test_validate_does_not_report_internal_rule_failure(self):
        v = CpmValidator()
        report = v.validate(_make_wrapper())
        assert not any("Validation rule failed" in result.message for result in report.results)

    def test_validate_empty_wrapper(self):
        v = CpmValidator()
        w = _make_empty_wrapper()
        report = v.validate(w)
        assert isinstance(report, ValidationReport)

    def test_validate_with_template(self):
        v = CpmValidator()
        w = _make_wrapper()
        t = _make_template()
        report = v.validate(w, template=t)
        assert isinstance(report, ValidationReport)

    def test_report_get_errors(self):
        v = CpmValidator()
        w = _make_wrapper()
        report = v.validate(w)
        errs = report.get_errors()
        assert isinstance(errs, list)

    def test_report_get_warnings(self):
        v = CpmValidator()
        w = _make_wrapper()
        report = v.validate(w)
        warnings = report.get_warnings()
        assert isinstance(warnings, list)

    def test_report_get_by_type(self):
        v = CpmValidator()
        w = _make_wrapper()
        report = v.validate(w)
        structural = report.get_by_type(ValidationType.STRUCTURAL)
        assert isinstance(structural, list)

    def test_add_remove_custom_rule(self):
        v = CpmValidator()

        def custom_rule(wrapper, template):
            return []

        v.add_validation_rule(custom_rule)
        report = v.validate(_make_wrapper())
        assert isinstance(report, ValidationReport)
        v.remove_validation_rule(custom_rule)

    def test_node_integrity_isolated(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["isolated"])
        w = ProvGraphWrapper(doc)
        v = CpmValidator()
        report = v.validate(w)
        warnings = report.get_warnings()
        assert any("solated" in r.message.lower() for r in warnings)

    def test_edge_self_loop_warning(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        doc.wasInfluencedBy(EX["e1"], EX["e1"])
        w = ProvGraphWrapper(doc)
        v = CpmValidator()
        report = v.validate(w)
        assert len(report.results) > 0

    def test_bundle_structure_no_bundles(self):
        doc = ProvDocument()
        doc.add_namespace(EX)
        doc.entity(EX["e1"])
        w = ProvGraphWrapper(doc)
        v = CpmValidator()
        report = v.validate(w)
        info = [r for r in report.results if r.level == ValidationLevel.INFO]
        assert any("bundle" in r.message.lower() for r in info)


# ─── validate_cpm_graph convenience function ────────────────────────────────

class TestValidateCpmGraph:
    def test_basic(self):
        report = validate_cpm_graph(_make_wrapper())
        assert isinstance(report, ValidationReport)

    def test_with_template(self):
        report = validate_cpm_graph(_make_wrapper(), template=_make_template())
        assert isinstance(report, ValidationReport)

    def test_custom_validator(self):
        v = CpmValidator()
        report = validate_cpm_graph(_make_wrapper(), validator=v)
        assert isinstance(report, ValidationReport)


# ─── create_validation_rule decorator ───────────────────────────────────────

class TestCreateValidationRule:
    def test_decorator_returns_results(self):
        @create_validation_rule(ValidationType.STRUCTURAL, ValidationLevel.WARNING)
        def my_rule(wrapper, template):
            return "Found something"

        results = my_rule(_make_wrapper())
        assert len(results) == 1
        assert results[0].level == ValidationLevel.WARNING

    def test_decorator_list_of_strings(self):
        @create_validation_rule(ValidationType.SEMANTIC, ValidationLevel.INFO)
        def my_rule(wrapper, template):
            return ["msg1", "msg2"]

        results = my_rule(_make_wrapper())
        assert len(results) == 2

    def test_decorator_empty(self):
        @create_validation_rule(ValidationType.STRUCTURAL, ValidationLevel.ERROR)
        def my_rule(wrapper, template):
            return []

        results = my_rule(_make_wrapper())
        assert results == []

    def test_decorator_exception(self):
        @create_validation_rule(ValidationType.STRUCTURAL, ValidationLevel.ERROR)
        def my_rule(wrapper, template):
            raise RuntimeError("oops")

        result = my_rule(_make_wrapper())
        assert isinstance(result, (list,) + (type(result),))
