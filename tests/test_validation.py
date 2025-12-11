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
    TraversalInformationDeserializer, TraversalInformationTemplate,
    TraversalInformationSerializer
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
        template = TraversalInformationDeserializer.from_json(template_data)
        assert template.bundle_name == "ex:testBundle"
        assert template.main_activity.id == "ex:mainActivity"
        assert len(template.forward_connectors) == 1

        # Test serialization round-trip
        json_str = TraversalInformationSerializer.to_json(template)
        restored = TraversalInformationDeserializer.from_json(json_str)
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


def create_test_template() -> TraversalInformationTemplate:
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
    return TraversalInformationDeserializer.from_json(template_data)


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
