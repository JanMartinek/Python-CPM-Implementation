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
    TemplateAgentAnalyzer,
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


# ═══════════════════════════════════════════════════════════════════════════════
# Additional coverage tests – serialization, deserialization, validation,
# advanced processing, agent analysis, and pipeline.
# ═══════════════════════════════════════════════════════════════════════════════

import pytest

STANDARD_PREFIXES = {
    "prov": "http://www.w3.org/ns/prov#",
    "cpm": "https://commonprovenancemodel.org/ns/cpm/",
    "ex": "http://example.org/",
}


def _minimal_template_data():
    return {
        "prefixes": STANDARD_PREFIXES,
        "bundleName": "ex:bundle",
        "mainActivity": {"id": "ex:main"},
    }


def _rich_template_data():
    return {
        "prefixes": {**STANDARD_PREFIXES, "custom": "http://custom.org/"},
        "bundleName": "ex:bundle",
        "mainActivity": {
            "id": "ex:main",
            "startTime": "2024-01-01T00:00:00Z",
            "endTime": "2024-01-01T01:00:00Z",
            "referencedMetaBundleId": "ex:meta",
            "used": [{"bcId": "ex:bc1", "relationId": "ex:r1"}],
            "generated": ["ex:fc1"],
            "hasPart": ["ex:part1"],
            "attributes": {"label": "main"},
        },
        "backwardConnectors": [
            {
                "id": "ex:bc1",
                "externalId": "ext1",
                "referencedBundleId": "ex:refBundle",
                "referencedBundleHashValue": "abc123",
                "hashAlg": "sha256",
                "provenanceServiceUri": "http://example.org/prov",
                "derivedFrom": ["ex:other"],
                "specializedBy": ["ex:spec"],
                "attributedTo": {"agentId": "ex:agent1"},
                "attributes": {"note": "bc"},
            }
        ],
        "forwardConnectors": [
            {
                "id": "ex:fc1",
                "specializationOf": "ex:general",
            }
        ],
        "senderAgents": [
            {"id": "ex:agent1", "contactIdPid": "pid1", "attributes": {"role": "sender"}}
        ],
        "receiverAgents": [
            {"id": "ex:agent1", "attributes": {"role": "receiver"}}
        ],
        "identifierEntities": [
            {
                "id": "ex:ie1",
                "externalId": "ext-ie",
                "externalIdType": "DOI",
                "comment": "a comment",
                "attributes": {"tag": "val"},
            }
        ],
    }


# ─── RelationTemplate (extended) ────────────────────────────────────────────

class TestRelationTemplateExtended:
    def test_from_string(self):
        rt = RelationTemplate.from_dict("ex:target")
        assert rt.target_id == "ex:target"
        assert rt.relation_id is None

    def test_from_dict_bcId(self):
        rt = RelationTemplate.from_dict({"bcId": "ex:bc", "relationId": "ex:r"})
        assert rt.target_id == "ex:bc"
        assert rt.relation_id == "ex:r"

    def test_to_dict(self):
        rt = RelationTemplate(target_id="ex:t", relation_id="ex:r")
        d = rt.to_dict()
        assert d["targetId"] == "ex:t"
        assert d["relationId"] == "ex:r"

    def test_to_dict_no_relation_id(self):
        rt = RelationTemplate(target_id="ex:t")
        d = rt.to_dict()
        assert "relationId" not in d


# ─── MainActivityTemplate (extended) ────────────────────────────────────────

class TestMainActivityTemplateExtended:
    def test_from_dict_minimal(self):
        mat = MainActivityTemplate.from_dict({"id": "ex:main"})
        assert mat.id == "ex:main"

    def test_from_dict_full(self):
        data = _rich_template_data()["mainActivity"]
        mat = MainActivityTemplate.from_dict(data)
        assert mat.start_time == "2024-01-01T00:00:00Z"
        assert mat.end_time == "2024-01-01T01:00:00Z"
        assert mat.referenced_meta_bundle_id == "ex:meta"
        assert len(mat.used) == 1
        assert mat.generated == ["ex:fc1"]
        assert mat.has_part == ["ex:part1"]

    def test_to_dict_roundtrip(self):
        data = _rich_template_data()["mainActivity"]
        mat = MainActivityTemplate.from_dict(data)
        d = mat.to_dict()
        assert d["id"] == "ex:main"
        assert "startTime" in d
        assert "endTime" in d
        assert "referencedMetaBundleId" in d
        assert "used" in d
        assert "generated" in d
        assert "hasPart" in d
        assert "attributes" in d


# ─── ConnectorTemplate ──────────────────────────────────────────────────────

class TestConnectorTemplate:
    def test_from_dict_minimal(self):
        ct = ConnectorTemplate.from_dict({"id": "ex:bc1"})
        assert ct.id == "ex:bc1"

    def test_from_dict_full(self):
        data = _rich_template_data()["backwardConnectors"][0]
        ct = ConnectorTemplate.from_dict(data)
        assert ct.external_id == "ext1"
        assert ct.attributed_to is not None
        assert ct.referenced_bundle_id == "ex:refBundle"
        assert ct.hash_alg == "sha256"
        assert ct.provenance_service_uri == "http://example.org/prov"
        assert "ex:other" in ct.derived_from

    def test_to_dict_roundtrip(self):
        data = _rich_template_data()["backwardConnectors"][0]
        ct = ConnectorTemplate.from_dict(data)
        d = ct.to_dict()
        assert "externalId" in d
        assert "attributedTo" in d
        assert "referencedBundleId" in d
        assert "referencedBundleHashValue" in d
        assert "hashAlg" in d
        assert "provenanceServiceUri" in d
        assert "derivedFrom" in d
        assert "specializedBy" in d

    def test_forward_connector_specialization_of(self):
        data = _rich_template_data()["forwardConnectors"][0]
        ct = ConnectorTemplate.from_dict(data)
        d = ct.to_dict()
        assert "specializationOf" in d


# ─── AgentTemplate ──────────────────────────────────────────────────────────

class TestAgentTemplate:
    def test_from_dict(self):
        at = AgentTemplate.from_dict({"id": "ex:a", "contactIdPid": "pid1", "attributes": {"x": 1}})
        assert at.id == "ex:a"
        assert at.contact_id_pid == "pid1"

    def test_to_dict(self):
        at = AgentTemplate(id="ex:a", contact_id_pid="pid1", attributes={"x": 1})
        d = at.to_dict()
        assert d["contactIdPid"] == "pid1"
        assert d["attributes"] == {"x": 1}


# ─── IdentifierEntityTemplate ───────────────────────────────────────────────

class TestIdentifierEntityTemplate:
    def test_from_dict(self):
        data = _rich_template_data()["identifierEntities"][0]
        iet = IdentifierEntityTemplate.from_dict(data)
        assert iet.external_id == "ext-ie"
        assert iet.external_id_type == "DOI"
        assert iet.comment == "a comment"

    def test_to_dict(self):
        iet = IdentifierEntityTemplate(id="ex:ie", external_id="eid", external_id_type="DOI", comment="c",
                                       attributes={"tag": 1})
        d = iet.to_dict()
        assert "externalId" in d
        assert "externalIdType" in d
        assert "comment" in d
        assert "attributes" in d


# ─── Deserializer ───────────────────────────────────────────────────────────

class TestDeserializer:
    def test_from_json_dict(self):
        t = TraversalInformationDeserializer.from_json(_minimal_template_data())
        assert t.bundle_name == "ex:bundle"

    def test_from_json_string(self):
        t = TraversalInformationDeserializer.from_json(json.dumps(_minimal_template_data()))
        assert t.bundle_name == "ex:bundle"

    def test_from_json_full(self):
        t = TraversalInformationDeserializer.from_json(_rich_template_data())
        assert len(t.backward_connectors) == 1
        assert len(t.forward_connectors) == 1
        assert len(t.sender_agents) == 1
        assert len(t.receiver_agents) == 1
        assert len(t.identifier_entities) == 1

    def test_from_file(self, tmp_path):
        fp = tmp_path / "tmpl.json"
        fp.write_text(json.dumps(_minimal_template_data()), encoding="utf-8")
        t = TraversalInformationDeserializer.from_file(str(fp))
        assert t.bundle_name == "ex:bundle"


# ─── Serializer ─────────────────────────────────────────────────────────────

class TestSerializer:
    def test_to_dict(self):
        t = TraversalInformationDeserializer.from_json(_rich_template_data())
        d = TraversalInformationSerializer.to_dict(t)
        assert "prefixes" in d
        assert "bundleName" in d
        assert "mainActivity" in d
        assert "backwardConnectors" in d
        assert "forwardConnectors" in d
        assert "senderAgents" in d
        assert "receiverAgents" in d
        assert "identifierEntities" in d

    def test_to_json(self):
        t = TraversalInformationDeserializer.from_json(_minimal_template_data())
        j = TraversalInformationSerializer.to_json(t, indent=2)
        parsed = json.loads(j)
        assert parsed["bundleName"] == "ex:bundle"

    def test_to_file(self, tmp_path):
        t = TraversalInformationDeserializer.from_json(_minimal_template_data())
        fp = tmp_path / "out.json"
        TraversalInformationSerializer.to_file(t, str(fp))
        assert fp.exists()
        loaded = json.loads(fp.read_text(encoding="utf-8"))
        assert loaded["bundleName"] == "ex:bundle"


# ─── TemplateSchemaValidator (extended) ─────────────────────────────────────

class TestTemplateSchemaValidatorExtended:
    def test_validate_minimal(self):
        v = TemplateSchemaValidator()
        assert v.validate_template(_minimal_template_data()) is True

    def test_missing_bundle_name(self):
        v = TemplateSchemaValidator()
        with pytest.raises(TemplateValidationError, match="bundleName"):
            v.validate_template({"mainActivity": {"id": "ex:m"}})

    def test_missing_main_activity(self):
        v = TemplateSchemaValidator()
        with pytest.raises(TemplateValidationError, match="mainActivity"):
            v.validate_template({"bundleName": "ex:b"})

    def test_main_activity_missing_id(self):
        v = TemplateSchemaValidator()
        with pytest.raises(TemplateValidationError, match="id"):
            v.validate_template({"bundleName": "ex:b", "mainActivity": {}})

    def test_connector_missing_id(self):
        v = TemplateSchemaValidator()
        data = {**_minimal_template_data(), "backwardConnectors": [{"externalId": "x"}]}
        with pytest.raises(TemplateValidationError):
            v.validate_template(data)

    def test_agent_missing_id(self):
        v = TemplateSchemaValidator()
        data = {**_minimal_template_data(), "senderAgents": [{"contactIdPid": "x"}]}
        with pytest.raises(TemplateValidationError):
            v.validate_template(data)

    def test_validate_template_object(self):
        v = TemplateSchemaValidator()
        t = TraversalInformationDeserializer.from_json(_minimal_template_data())
        assert v.validate_template_object(t) is True

    def test_bad_schema_path(self):
        with pytest.raises(TemplateValidationError):
            TemplateSchemaValidator(schema_path="/nonexistent/schema.json")


# ─── AdvancedTemplateProcessor ──────────────────────────────────────────────

class TestAdvancedTemplateProcessor:
    def test_process_with_validation(self):
        p = AdvancedTemplateProcessor()
        t = p.process_template_with_validation(_minimal_template_data())
        assert t.bundle_name == "ex:bundle"

    def test_transform_embrc_template_empty(self):
        p = AdvancedTemplateProcessor()
        result = p.transform_embrc_template({"@id": "embrc:b"})
        assert result["bundleName"] == "embrc:b"

    def test_transform_embrc_template_with_graph(self):
        p = AdvancedTemplateProcessor()
        embrc = {
            "@context": {"prov": "http://www.w3.org/ns/prov#"},
            "@id": "embrc:bundle",
            "@graph": [
                {"@id": "embrc:act", "@type": "Activity", "prov:startedAtTime": "2024-01-01"},
                {"@id": "embrc:e1", "@type": "Entity", "prov:wasUsedBy": "embrc:act"},
                {"@id": "embrc:e2", "@type": "Entity", "prov:wasGeneratedBy": "embrc:act"},
            ],
        }
        result = p.transform_embrc_template(embrc)
        assert "mainActivity" in result
        assert result["mainActivity"]["id"] == "embrc:act"

    def test_is_activity(self):
        p = AdvancedTemplateProcessor()
        assert p._is_activity({"@type": "Activity"})
        assert not p._is_activity({"@type": "Entity"})

    def test_is_entity(self):
        p = AdvancedTemplateProcessor()
        assert p._is_entity({"@type": "Entity"})
        assert not p._is_entity({"@type": "Activity"})

    def test_transform_connector_with_derivation(self):
        p = AdvancedTemplateProcessor()
        entity = {
            "@id": "ex:e1",
            "prov:wasDerivedFrom": [{"@id": "ex:e2"}, "ex:e3"],
        }
        result = p._transform_connector(entity)
        assert result["id"] == "ex:e1"
        assert len(result["derivedFrom"]) == 2

    def test_transform_connector_with_single_derivation(self):
        p = AdvancedTemplateProcessor()
        entity = {
            "@id": "ex:e1",
            "prov:wasDerivedFrom": {"@id": "ex:e2"},
        }
        result = p._transform_connector(entity)
        assert "derivedFrom" in result


# ─── EnhancedTraversalInformationSerializer ─────────────────────────────────

class TestEnhancedSerializer:
    def test_to_json_with_validation(self):
        s = EnhancedTraversalInformationSerializer(validate_output=True)
        t = TraversalInformationDeserializer.from_json(_minimal_template_data())
        j = s.to_json_with_validation(t)
        assert json.loads(j)["bundleName"] == "ex:bundle"

    def test_to_json_no_pretty(self):
        s = EnhancedTraversalInformationSerializer(pretty_print=False)
        t = TraversalInformationDeserializer.from_json(_minimal_template_data())
        j = s.to_json_with_validation(t)
        assert "\n" not in j

    def test_to_file_with_validation(self, tmp_path):
        s = EnhancedTraversalInformationSerializer(validate_output=True)
        t = TraversalInformationDeserializer.from_json(_minimal_template_data())
        fp = tmp_path / "out.json"
        s.to_file_with_validation(t, str(fp))
        assert fp.exists()

    def test_serialize_datetime_iso(self):
        s = EnhancedTraversalInformationSerializer()
        assert s._serialize_datetime("2024-01-01T10:00:00Z") == "2024-01-01T10:00:00"

    def test_serialize_datetime_none(self):
        s = EnhancedTraversalInformationSerializer()
        assert s._serialize_datetime(None) is None

    def test_serialize_datetime_already_iso(self):
        s = EnhancedTraversalInformationSerializer()
        assert s._serialize_datetime("2024-01-01T10:00:00") == "2024-01-01T10:00:00"


# ─── TemplateAgentAnalyzer ──────────────────────────────────────────────────

class TestTemplateAgentAnalyzer:
    def test_no_overlap(self):
        t = TraversalInformationDeserializer.from_json(_minimal_template_data())
        a = TemplateAgentAnalyzer()
        result = a.analyze_agent_overlap(t)
        assert result["overlapping_count"] == 0

    def test_with_overlap(self):
        t = TraversalInformationDeserializer.from_json(_rich_template_data())
        a = TemplateAgentAnalyzer()
        result = a.analyze_agent_overlap(t)
        assert result["overlapping_count"] >= 1
        assert result["merge_recommended"] is True

    def test_no_merge(self):
        t = TraversalInformationDeserializer.from_json(_rich_template_data())
        a = TemplateAgentAnalyzer(merge_agents=False)
        result = a.analyze_agent_overlap(t)
        assert result["merge_recommended"] is False


# ─── TemplateTransformationPipeline ─────────────────────────────────────────

class TestPipeline:
    def test_standard_format(self):
        p = TemplateTransformationPipeline()
        t = p.transform_and_validate(_minimal_template_data())
        assert t.bundle_name == "ex:bundle"

    def test_embrc_format(self):
        p = TemplateTransformationPipeline()
        embrc = {
            "@context": {"prov": "http://www.w3.org/ns/prov#"},
            "@id": "embrc:bundle",
            "@graph": [
                {"@id": "embrc:act", "@type": "Activity"},
            ],
        }
        t = p.transform_and_validate(embrc, source_format="embrc")
        assert t is not None

    def test_mou_format_passthrough(self):
        p = TemplateTransformationPipeline()
        t = p.transform_and_validate(_minimal_template_data(), source_format="mou")
        assert t.bundle_name == "ex:bundle"

    def test_analyze_template_quality(self):
        p = TemplateTransformationPipeline()
        t = TraversalInformationDeserializer.from_json(_rich_template_data())
        quality = p.analyze_template_quality(t)
        assert "statistics" in quality
        assert "quality_metrics" in quality
        assert "agent_analysis" in quality
        assert "complexity_assessment" in quality
        assert quality["quality_metrics"]["quality_score"] >= 0

    def test_full_pipeline(self):
        p = TemplateTransformationPipeline()
        result = p.full_pipeline(_rich_template_data())
        assert result["processing_successful"] is True
        assert result["template"] is not None
        assert result["analysis"] is not None
