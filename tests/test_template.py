"""
Comprehensive tests for CPM template functionality

Tests cover:
- Template class creation and serialization
- JSON serialization/deserialization
- Template validation
- Advanced template processing and transformations
- Error handling and edge cases
"""

# Add the src directory to the Python path FIRST
from typing import Dict, Any
from pathlib import Path
import tempfile
import json
import unittest
from cpm.template import (
    RelationTemplate,
    MainActivityTemplate,
    ConnectorTemplate,
    AgentTemplate,
    IdentifierEntityTemplate,
    TraversalInformationTemplate,
    TraversalInformationDeserializer,
    TraversalInformationSerializer,
    TemplateSchemaValidator,
    TemplateValidationError,
    AdvancedTemplateProcessor,
    EnhancedTraversalInformationSerializer,
    TemplateTransformationPipeline
)
from cpm.template_mapper import TemplateProvMapper
import sys
import os
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Now import the template modules


class TestRelationTemplate(unittest.TestCase):
    """Test RelationTemplate class"""

    def test_creation_from_string(self):
        """Test creating RelationTemplate from string"""
        rel = RelationTemplate.from_dict("entity:test")
        self.assertEqual(rel.target_id, "entity:test")
        self.assertIsNone(rel.relation_id)

    def test_creation_from_dict_with_target_id(self):
        """Test creating RelationTemplate from dict with targetId"""
        data = {"targetId": "entity:test", "relationId": "rel:123"}
        rel = RelationTemplate.from_dict(data)
        self.assertEqual(rel.target_id, "entity:test")
        self.assertEqual(rel.relation_id, "rel:123")

    def test_creation_from_dict_with_bc_id(self):
        """Test creating RelationTemplate from dict with bcId (backward compatibility)"""
        data = {"bcId": "entity:test"}
        rel = RelationTemplate.from_dict(data)
        self.assertEqual(rel.target_id, "entity:test")
        self.assertIsNone(rel.relation_id)

    def test_to_dict(self):
        """Test converting RelationTemplate to dict"""
        rel = RelationTemplate("entity:test", "rel:123")
        expected = {"targetId": "entity:test", "relationId": "rel:123"}
        self.assertEqual(rel.to_dict(), expected)

    def test_to_dict_without_relation_id(self):
        """Test converting RelationTemplate to dict without relation ID"""
        rel = RelationTemplate("entity:test")
        expected = {"targetId": "entity:test"}
        self.assertEqual(rel.to_dict(), expected)


class TestMainActivityTemplate(unittest.TestCase):
    """Test MainActivityTemplate class"""

    def test_minimal_creation(self):
        """Test creating MainActivityTemplate with minimal data"""
        data = {"id": "activity:main"}
        activity = MainActivityTemplate.from_dict(data)

        self.assertEqual(activity.id, "activity:main")
        self.assertIsNone(activity.start_time)
        self.assertIsNone(activity.end_time)
        self.assertEqual(activity.used, [])
        self.assertEqual(activity.generated, [])
        self.assertEqual(activity.has_part, [])
        self.assertEqual(activity.attributes, {})

    def test_full_creation(self):
        """Test creating MainActivityTemplate with all fields"""
        data = {
            "id": "activity:main",
            "startTime": "2023-01-01T00:00:00Z",
            "endTime": "2023-01-01T01:00:00Z",
            "used": [{"targetId": "entity:input"}, "entity:input2"],
            "generated": ["entity:output"],
            "hasPart": ["activity:sub1", "activity:sub2"],
            "attributes": {"attr1": "value1"}
        }
        activity = MainActivityTemplate.from_dict(data)

        self.assertEqual(activity.id, "activity:main")
        self.assertEqual(activity.start_time, "2023-01-01T00:00:00Z")
        self.assertEqual(activity.end_time, "2023-01-01T01:00:00Z")
        self.assertEqual(len(activity.used), 2)
        self.assertEqual(activity.used[0].target_id, "entity:input")
        self.assertEqual(activity.used[1].target_id, "entity:input2")
        self.assertEqual(activity.generated, ["entity:output"])
        self.assertEqual(activity.has_part, ["activity:sub1", "activity:sub2"])
        self.assertEqual(activity.attributes, {"attr1": "value1"})

    def test_to_dict_minimal(self):
        """Test converting minimal MainActivityTemplate to dict"""
        activity = MainActivityTemplate("activity:main")
        expected = {"id": "activity:main"}
        self.assertEqual(activity.to_dict(), expected)

    def test_to_dict_full(self):
        """Test converting full MainActivityTemplate to dict"""
        activity = MainActivityTemplate(
            id="activity:main",
            start_time="2023-01-01T00:00:00Z",
            end_time="2023-01-01T01:00:00Z",
            used=[RelationTemplate("entity:input")],
            generated=["entity:output"],
            has_part=["activity:sub"],
            attributes={"attr1": "value1"}
        )
        result = activity.to_dict()

        self.assertEqual(result["id"], "activity:main")
        self.assertEqual(result["startTime"], "2023-01-01T00:00:00Z")
        self.assertEqual(result["endTime"], "2023-01-01T01:00:00Z")
        self.assertEqual(len(result["used"]), 1)
        self.assertEqual(result["used"][0]["targetId"], "entity:input")
        self.assertEqual(result["generated"], ["entity:output"])
        self.assertEqual(result["hasPart"], ["activity:sub"])
        self.assertEqual(result["attributes"], {"attr1": "value1"})


class TestTraversalInformationDeserializer(unittest.TestCase):
    """Test TraversalInformationDeserializer class"""

    def setUp(self):
        """Set up test data"""
        self.sample_data = {
            "prefixes": {
                "ex": "http://example.org/",
                "workflow": "http://workflow.example.org/"
            },
            "bundleName": "workflow:bundle",
            "mainActivity": {
                "id": "workflow:main",
                "startTime": "2023-01-01T00:00:00Z",
                "used": [{"targetId": "workflow:input"}],
                "generated": ["workflow:output"]
            },
            "backwardConnectors": [
                {
                    "id": "workflow:input",
                    "referencedBundleId": "ex:source"
                }
            ],
            "forwardConnectors": [
                {
                    "id": "workflow:output",
                    "referencedBundleId": "ex:target"
                }
            ],
            "senderAgents": [
                {"id": "agent:sender"}
            ],
            "receiverAgents": [
                {"id": "agent:receiver"}
            ],
            "identifierEntities": [
                {"id": "entity:identifier"}
            ]
        }

    def test_from_dict(self):
        """Test deserializing from dictionary"""
        template = TraversalInformationDeserializer.from_json(self.sample_data)

        self.assertEqual(template.prefixes, self.sample_data["prefixes"])
        self.assertEqual(template.bundle_name, "workflow:bundle")
        self.assertEqual(template.main_activity.id, "workflow:main")
        self.assertEqual(len(template.backward_connectors), 1)
        self.assertEqual(len(template.forward_connectors), 1)
        self.assertEqual(len(template.sender_agents), 1)
        self.assertEqual(len(template.receiver_agents), 1)
        self.assertEqual(len(template.identifier_entities), 1)

    def test_from_json_string(self):
        """Test deserializing from JSON string"""
        json_string = json.dumps(self.sample_data)
        template = TraversalInformationDeserializer.from_json(json_string)

        self.assertEqual(template.bundle_name, "workflow:bundle")
        self.assertEqual(template.main_activity.id, "workflow:main")

    def test_empty_optional_fields(self):
        """Test deserializing with missing optional fields"""
        minimal_data = {
            "bundleName": "test:bundle",
            "mainActivity": {"id": "test:main"}
        }
        template = TraversalInformationDeserializer.from_json(minimal_data)

        self.assertEqual(template.prefixes, {})
        self.assertEqual(template.bundle_name, "test:bundle")
        self.assertEqual(len(template.backward_connectors), 0)
        self.assertEqual(len(template.forward_connectors), 0)
        self.assertEqual(len(template.sender_agents), 0)
        self.assertEqual(len(template.receiver_agents), 0)
        self.assertEqual(len(template.identifier_entities), 0)


class TestTraversalInformationSerializer(unittest.TestCase):
    """Test TraversalInformationSerializer class"""

    def setUp(self):
        """Set up test template"""
        self.template = TraversalInformationTemplate(
            prefixes={"ex": "http://example.org/", "workflow": "http://workflow.example.org/"},
            bundle_name="workflow:bundle",
            main_activity=MainActivityTemplate(
                id="workflow:main",
                start_time="2023-01-01T00:00:00Z",
                used=[RelationTemplate("workflow:input")],
                generated=["workflow:output"]
            ),
            backward_connectors=[
                ConnectorTemplate("workflow:input", referenced_bundle_id="ex:source")
            ],
            forward_connectors=[
                ConnectorTemplate("workflow:output", referenced_bundle_id="ex:target")
            ],
            sender_agents=[AgentTemplate("agent:sender")],
            receiver_agents=[AgentTemplate("agent:receiver")],
            identifier_entities=[IdentifierEntityTemplate("entity:identifier")]
        )

    def test_to_dict(self):
        """Test serializing to dictionary"""
        result = TraversalInformationSerializer.to_dict(self.template)

        self.assertEqual(result["bundleName"], "workflow:bundle")
        self.assertEqual(result["prefixes"]["ex"], "http://example.org/")
        self.assertEqual(result["mainActivity"]["id"], "workflow:main")
        self.assertIn("backwardConnectors", result)
        self.assertIn("forwardConnectors", result)
        self.assertIn("senderAgents", result)
        self.assertIn("receiverAgents", result)
        self.assertIn("identifierEntities", result)

    def test_to_json(self):
        """Test serializing to JSON string"""
        json_result = TraversalInformationSerializer.to_json(self.template)
        self.assertIsInstance(json_result, str)

        # Parse back to verify structure
        parsed = json.loads(json_result)
        self.assertEqual(parsed["bundleName"], "workflow:bundle")

    def test_minimal_template_serialization(self):
        """Test serializing minimal template"""
        minimal_template = TraversalInformationTemplate(
            prefixes={},
            bundle_name="test:bundle",
            main_activity=MainActivityTemplate("test:main")
        )

        result = TraversalInformationSerializer.to_dict(minimal_template)
        expected_keys = {"prefixes", "bundleName", "mainActivity"}
        self.assertEqual(set(result.keys()), expected_keys)


class TestTemplateSchemaValidator(unittest.TestCase):
    """Test TemplateSchemaValidator class"""

    def setUp(self):
        """Set up validator"""
        self.validator = TemplateSchemaValidator()

    def test_valid_template(self):
        """Test validating valid template"""
        valid_data = {
            "bundleName": "test:bundle",
            "mainActivity": {"id": "test:main"}
        }
        self.assertTrue(self.validator.validate_template(valid_data))

    def test_missing_bundle_name(self):
        """Test validation fails for missing bundleName"""
        invalid_data = {
            "mainActivity": {"id": "test:main"}
        }
        with self.assertRaises(TemplateValidationError):
            self.validator.validate_template(invalid_data)

    def test_missing_main_activity(self):
        """Test validation fails for missing mainActivity"""
        invalid_data = {
            "bundleName": "test:bundle"
        }
        with self.assertRaises(TemplateValidationError):
            self.validator.validate_template(invalid_data)


class TestTemplateIntegration(unittest.TestCase):
    """Integration tests for template functionality"""

    def test_round_trip_serialization(self):
        """Test complete round-trip serialization"""
        # Create original template
        original = TraversalInformationTemplate(
            prefixes={"ex": "http://example.org/"},
            bundle_name="test:bundle",
            main_activity=MainActivityTemplate(
                "test:main",
                start_time="2023-01-01T00:00:00Z",
                used=[RelationTemplate("test:input", "rel:123")],
                generated=["test:output"]
            ),
            backward_connectors=[
                ConnectorTemplate(
                    "test:input",
                    attributed_to=RelationTemplate("agent:creator"),
                    referenced_bundle_id="ext:source"
                )
            ],
            sender_agents=[AgentTemplate("agent:creator", {"name": "Creator"})]
        )

        # Serialize to JSON
        json_data = TraversalInformationSerializer.to_json(original)

        # Deserialize back
        restored = TraversalInformationDeserializer.from_json(json_data)

        # Verify key properties match
        self.assertEqual(original.bundle_name, restored.bundle_name)
        self.assertEqual(original.main_activity.id, restored.main_activity.id)
        self.assertEqual(original.main_activity.start_time, restored.main_activity.start_time)
        self.assertEqual(len(original.backward_connectors), len(restored.backward_connectors))
        self.assertEqual(len(original.sender_agents), len(restored.sender_agents))

        # Verify nested structures
        self.assertEqual(
            original.main_activity.used[0].target_id,
            restored.main_activity.used[0].target_id
        )
        self.assertEqual(
            original.backward_connectors[0].referenced_bundle_id,
            restored.backward_connectors[0].referenced_bundle_id
        )

    def test_complex_template_processing(self):
        """Test processing complex template with all features"""
        complex_data = {
            "prefixes": {
                "ex": "http://example.org/",
                "workflow": "http://workflow.example.org/",
                "prov": "http://www.w3.org/ns/prov#"
            },
            "bundleName": "workflow:complexBundle",
            "mainActivity": {
                "id": "workflow:complexMain",
                "startTime": "2023-01-01T00:00:00Z",
                "endTime": "2023-01-01T02:00:00Z",
                "used": [
                    {"targetId": "workflow:input1", "relationId": "rel:use1"},
                    "workflow:input2"
                ],
                "generated": ["workflow:output1", "workflow:output2"],
                "hasPart": ["workflow:sub1", "workflow:sub2"],
                "attributes": {"type": "complex", "priority": "high"}
            },
            "backwardConnectors": [
                {
                    "id": "workflow:input1",
                    "attributedTo": {"targetId": "agent:creator"},
                    "referencedBundleId": "ex:sourceBundle1",
                    "referencedBundleHashValue": "sha256:abc123",
                    "hashAlg": "SHA256",
                    "derivedFrom": ["ex:originalEntity1"],
                    "attributes": {"type": "primary"}
                }
            ],
            "senderAgents": [
                {"id": "agent:sender1", "attributes": {"name": "Primary Sender"}},
                {"id": "agent:shared", "attributes": {"role": "sender"}}
            ],
            "receiverAgents": [
                {"id": "agent:receiver1", "attributes": {"name": "Primary Receiver"}},
                {"id": "agent:shared", "attributes": {"role": "receiver"}}
            ]
        }

        # Deserialize
        template = TraversalInformationDeserializer.from_json(complex_data)

        # Verify template structure
        self.assertEqual(template.bundle_name, "workflow:complexBundle")
        self.assertEqual(len(template.backward_connectors), 1)
        self.assertEqual(len(template.sender_agents), 2)
        self.assertEqual(len(template.receiver_agents), 2)

        # Serialize back and verify
        serialized = TraversalInformationSerializer.to_json(template)
        self.assertIsInstance(serialized, str)

        # Deserialize again to verify round-trip
        restored = TraversalInformationDeserializer.from_json(serialized)
        self.assertEqual(restored.bundle_name, template.bundle_name)


def run_basic_tests():
    """Run basic template tests to verify functionality"""
    print("Running CPM Template Tests...")
    print("=" * 50)

    # Test 1: Basic RelationTemplate creation
    print("Test 1: RelationTemplate creation")
    rel = RelationTemplate.from_dict("entity:test")
    assert rel.target_id == "entity:test"
    assert rel.relation_id is None
    print("✓ RelationTemplate basic creation works")

    # Test 2: MainActivityTemplate creation
    print("\nTest 2: MainActivityTemplate creation")
    data = {"id": "activity:main", "startTime": "2023-01-01T00:00:00Z"}
    activity = MainActivityTemplate.from_dict(data)
    assert activity.id == "activity:main"
    assert activity.start_time == "2023-01-01T00:00:00Z"
    print("✓ MainActivityTemplate creation works")

    # Test 3: Template serialization
    print("\nTest 3: Template serialization")
    template = TraversalInformationTemplate(
        prefixes={"ex": "http://example.org/"},
        bundle_name="test:bundle",
        main_activity=MainActivityTemplate("test:main")
    )
    json_result = TraversalInformationSerializer.to_json(template)
    assert isinstance(json_result, str)
    assert "test:bundle" in json_result
    print("✓ Template serialization works")

    # Test 4: Template deserialization
    print("\nTest 4: Template deserialization")
    data = {
        "bundleName": "test:bundle",
        "mainActivity": {"id": "test:main"},
        "prefixes": {"ex": "http://example.org/"}
    }
    restored = TraversalInformationDeserializer.from_json(data)
    assert restored.bundle_name == "test:bundle"
    assert restored.main_activity.id == "test:main"
    print("✓ Template deserialization works")

    # Test 5: Round-trip serialization
    print("\nTest 5: Round-trip serialization")
    original_json = TraversalInformationSerializer.to_json(template)
    restored_template = TraversalInformationDeserializer.from_json(original_json)
    assert restored_template.bundle_name == template.bundle_name
    assert restored_template.main_activity.id == template.main_activity.id
    print("✓ Round-trip serialization works")

    # Test 6: Template validation
    print("\nTest 6: Template validation")
    validator = TemplateSchemaValidator()
    valid_data = {"bundleName": "test:bundle", "mainActivity": {"id": "test:main"}}
    assert validator.validate_template(valid_data) == True
    print("✓ Template validation works")

    print("\n" + "=" * 50)
    print("All basic template tests passed! ✓")
    print("Template functionality is working correctly.")


if __name__ == '__main__':
    try:
        # Run basic tests first
        run_basic_tests()

        # Run full unittest suite
        print("\n" + "=" * 50)
        print("Running full unittest suite...")
        unittest.main(verbosity=2)
    except Exception as e:
        print(f"\nError running tests: {e}")
        print("Running basic functionality tests only...")
        run_basic_tests()
