#!/usr/bin/env python3
"""
CPM Template Examples

This file demonstrates the CPM template system and validation functionality, including:

1. Creating CPM templates from JSON specifications
2. Template serialization and deserialization  
3. Converting templates to PROV documents and graphs
4. Template validation and constraint checking
5. Template-based workflow creation
6. Error handling and validation reporting

This covers the CPM template system for structured provenance workflows.
"""

from prov.model import ProvDocument
from src.graph.wrapper import ProvGraphWrapper
import sys
import os
import json
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.cpm.template import (
        TraversalInformationTemplate,
        TraversalInformationDeserializer,
        TraversalInformationSerializer
    )
    from src.cpm.model import CpmDocument, TemplateProvMapper
    from src.cpm.constants import CPM_MAIN_ACTIVITY, CPM_FORWARD_CONNECTOR, CPM_BACKWARD_CONNECTOR
    CPM_AVAILABLE = True
except ImportError as e:
    print(f"CPM modules not available: {e}")
    CPM_AVAILABLE = False

try:
    from src.cpm.validation import CpmValidator, ValidationLevel, ValidationType
    VALIDATION_AVAILABLE = True
except ImportError as e:
    print(f"Validation module not available: {e}")
    VALIDATION_AVAILABLE = False


def create_basic_template() -> Dict[str, Any]:
    """Create a basic CPM template for data processing workflow."""
    print("Creating basic CPM template...")

    template_data = {
        "prefixes": {
            "ex": "http://example.org/",
            "cpm": "https://commonprovenancemodel.org/ns/cpm/",
            "data": "http://data.example.org/"
        },
        "bundleName": "data:processingWorkflow",
        "mainActivity": {
            "id": "data:dataProcessing",
            "startTime": "2024-01-01T10:00:00Z",
            "endTime": "2024-01-01T12:00:00Z",
            "used": [
                {"bcId": "data:inputConnector"},
                "data:configFile"
            ],
            "generated": [
                "data:outputConnector",
                "data:logFile"
            ],
            "hasPart": [
                "data:preprocessing",
                "data:analysis",
                "data:postprocessing"
            ]
        },
        "backwardConnectors": [
            {
                "id": "data:inputConnector",
                "referencedBundleId": "ex:sourceBundle",
                "hashAlg": "SHA256",
                "referencedBundleHashValue": "abc123def456789...",
                "derivedFrom": ["ex:sourceData"]
            }
        ],
        "forwardConnectors": [
            {
                "id": "data:outputConnector",
                "referencedBundleId": "ex:targetBundle",
                "hashAlg": "SHA256",
                "referencedBundleHashValue": "def456abc123789...",
                "attributedTo": {
                    "agentId": "ex:processingSystem"
                }
            }
        ],
        "entities": [
            {
                "id": "data:configFile",
                "type": "Configuration",
                "attributes": {
                    "version": "1.2.0",
                    "format": "JSON"
                }
            },
            {
                "id": "data:logFile",
                "type": "Log",
                "attributes": {
                    "level": "INFO",
                    "format": "plaintext"
                }
            }
        ],
        "activities": [
            {
                "id": "data:preprocessing",
                "startTime": "2024-01-01T10:05:00Z",
                "endTime": "2024-01-01T10:30:00Z",
                "used": ["data:configFile"],
                "generated": []
            },
            {
                "id": "data:analysis",
                "startTime": "2024-01-01T10:35:00Z",
                "endTime": "2024-01-01T11:30:00Z",
                "used": [],
                "generated": []
            },
            {
                "id": "data:postprocessing",
                "startTime": "2024-01-01T11:35:00Z",
                "endTime": "2024-01-01T11:55:00Z",
                "used": [],
                "generated": ["data:logFile"]
            }
        ],
        "agents": [
            {
                "id": "ex:processingSystem",
                "type": "SoftwareAgent",
                "attributes": {
                    "version": "2.1.0",
                    "platform": "Linux"
                }
            }
        ]
    }

    print(f"✓ Created template with {len(template_data.get('entities', []))} entities")
    print(f"  - {len(template_data.get('activities', []))} activities")
    print(f"  - {len(template_data.get('backwardConnectors', []))} backward connectors")
    print(f"  - {len(template_data.get('forwardConnectors', []))} forward connectors")

    return template_data


def demonstrate_template_processing(template_data: Dict[str, Any]):
    """Demonstrate template deserialization and processing."""
    print("\nDemonstrating template processing...")

    if not CPM_AVAILABLE:
        print("  ⚠ CPM modules not available - skipping template processing")
        return None, None

    try:
        # Deserialize template
        template = TraversalInformationDeserializer.from_json(template_data)
        print(f"✓ Deserialized template: {template.bundle_name}")

        # Convert to CPM document
        cpm_doc = CpmDocument.from_template(template)
        print(f"✓ Created CPM document with template")

        # Get graph representation
        graph = cpm_doc.to_graph_wrapper()
        print(f"✓ Created graph with {len(graph)} nodes and {len(graph.get_edges())} edges")

        return template, graph

    except Exception as e:
        print(f"✗ Template processing failed: {e}")
        return None, None


def demonstrate_template_serialization(template_data: Dict[str, Any]):
    """Demonstrate template serialization capabilities."""
    print("\nDemonstrating template serialization...")

    if not CPM_AVAILABLE:
        print("  ⚠ CPM modules not available - skipping serialization")
        return

    try:
        # Round-trip serialization test
        template = TraversalInformationDeserializer.from_json(template_data)

        serialized_json = TraversalInformationSerializer.to_json(template)
        print(f"✓ Serialized template to JSON ({len(serialized_json)} characters)")

        # Verify round-trip
        deserialized_again = TraversalInformationDeserializer.from_json(serialized_json)
        print(f"✓ Round-trip serialization successful")

        # Save to file for inspection
        output_file = os.path.join(os.path.dirname(__file__), 'template_output.json')
        with open(output_file, 'w') as f:
            json.dump(json.loads(serialized_json), f, indent=2)
        print(f"✓ Saved template to: {output_file}")

    except Exception as e:
        print(f"✗ Serialization failed: {e}")


def demonstrate_template_validation(template_data: Dict[str, Any]):
    """Demonstrate template validation capabilities."""
    print("\nDemonstrating template validation...")

    if not CPM_AVAILABLE or not VALIDATION_AVAILABLE:
        print("  ⚠ Validation modules not available - skipping validation")
        return

    try:
        # Create template and convert to graph for validation
        template = TraversalInformationDeserializer.from_json(template_data)

        cpm_doc = CpmDocument.from_template(template)
        graph = cpm_doc.to_graph_wrapper()

        # Run validation
        validator = CpmValidator()
        report = validator.validate(graph, template)

        print(f"✓ Validation completed")
        print(f"  - Valid: {report.is_valid}")
        print(f"  - Errors: {report.error_count}")
        print(f"  - Warnings: {report.warning_count}")

        # Show validation results
        for result in report.results[:5]:  # Show first 5 results
            level_symbol = "❌" if result.level == ValidationLevel.ERROR else "⚠️" if result.level.name == "WARNING" else "ℹ️"
            print(f"  {level_symbol} {result.validation_type.name}: {result.message}")

        if len(report.results) > 5:
            print(f"  ... and {len(report.results) - 5} more results")

    except Exception as e:
        print(f"✗ Validation failed: {e}")


def create_acquisition_workflow_template() -> Dict[str, Any]:
    """Create a more complex acquisition workflow template."""
    print("\nCreating acquisition workflow template...")

    template_data = {
        "prefixes": {
            "acq": "http://acquisition.example.org/",
            "mmci": "http://mmci.cz/ns#",
            "cpm": "https://commonprovenancemodel.org/ns/cpm/"
        },
        "bundleName": "acq:sampleAcquisitionBundle",
        "mainActivity": {
            "id": "acq:sampleAcquisition",
            "startTime": "2024-01-15T09:00:00Z",
            "endTime": "2024-01-15T12:00:00Z",
            "hasPart": [
                "acq:tissueExtraction",
                "acq:samplePreparation",
                "acq:qualityControl"
            ],
            "used": [
                {"bcId": "acq:patientDataConnector"},
                "acq:extractionProtocol"
            ],
            "generated": [
                "acq:sampleConnector",
                "acq:qualityReport"
            ]
        },
        "backwardConnectors": [
            {
                "id": "acq:patientDataConnector",
                "referencedBundleId": "mmci:patientRecordBundle",
                "hashAlg": "SHA256",
                "referencedBundleHashValue": "patient123abc456def...",
                "attributedTo": {
                    "agentId": "mmci:ethicsBoard"
                }
            }
        ],
        "forwardConnectors": [
            {
                "id": "acq:sampleConnector",
                "referencedBundleId": "acq:storageBundle",
                "hashAlg": "SHA256",
                "referencedBundleHashValue": "sample456def789abc...",
                "attributedTo": {
                    "agentId": "acq:labTechnician"
                }
            }
        ],
        "entities": [
            {
                "id": "acq:extractionProtocol",
                "type": "Protocol",
                "attributes": {
                    "version": "2.1",
                    "approvedBy": "IRB-2024-001"
                }
            },
            {
                "id": "acq:qualityReport",
                "type": "QualityAssessment",
                "attributes": {
                    "passedQC": True,
                    "purity": "95.2%"
                }
            }
        ],
        "activities": [
            {
                "id": "acq:tissueExtraction",
                "startTime": "2024-01-15T09:15:00Z",
                "endTime": "2024-01-15T10:30:00Z",
                "used": ["acq:extractionProtocol"],
                "generated": [],
                "attributes": {
                    "method": "surgical_biopsy",
                    "location": "OR-3"
                }
            },
            {
                "id": "acq:samplePreparation",
                "startTime": "2024-01-15T10:45:00Z",
                "endTime": "2024-01-15T11:30:00Z",
                "used": [],
                "generated": [],
                "attributes": {
                    "method": "cryopreservation",
                    "temperature": "-80C"
                }
            },
            {
                "id": "acq:qualityControl",
                "startTime": "2024-01-15T11:35:00Z",
                "endTime": "2024-01-15T11:55:00Z",
                "used": [],
                "generated": ["acq:qualityReport"],
                "attributes": {
                    "tests": ["purity", "viability", "contamination"]
                }
            }
        ],
        "agents": [
            {
                "id": "acq:labTechnician",
                "type": "Person",
                "attributes": {
                    "certification": "CLIA-certified",
                    "experience": "5 years"
                }
            },
            {
                "id": "mmci:ethicsBoard",
                "type": "Organization",
                "attributes": {
                    "approval": "IRB-2024-001",
                    "jurisdiction": "EU-GDPR"
                }
            }
        ]
    }

    print(f"✓ Created acquisition template with {len(template_data.get('activities', []))} activities")
    return template_data


def demonstrate_error_handling():
    """Demonstrate error handling for template operations."""
    print("\nDemonstrating template error handling...")

    # Test with invalid template
    invalid_template = {
        "bundleName": "test:invalid",
        "mainActivity": {
            # Missing required fields
        }
    }

    if CPM_AVAILABLE:
        try:
            template = TraversalInformationDeserializer.from_json(invalid_template)
            print("✗ Invalid template was unexpectedly accepted")
        except Exception as e:
            print(f"✓ Invalid template correctly rejected: {type(e).__name__}")

    # Test with malformed JSON
    malformed_json = '{"bundleName": "test:malformed", "mainActivity": {'

    if CPM_AVAILABLE:
        try:
            template = TraversalInformationDeserializer.from_json(malformed_json)
            print("✗ Malformed JSON was unexpectedly accepted")
        except Exception as e:
            print(f"✓ Malformed JSON correctly rejected: {type(e).__name__}")


def demonstrate_template_analysis(template_data: Dict[str, Any]):
    """Analyze template structure and content."""
    print("\nAnalyzing template structure...")

    # Basic structure analysis
    main_activity = template_data.get('mainActivity', {})
    entities = template_data.get('entities', [])
    activities = template_data.get('activities', [])
    agents = template_data.get('agents', [])
    backward_connectors = template_data.get('backwardConnectors', [])
    forward_connectors = template_data.get('forwardConnectors', [])

    print(f"Template structure:")
    print(f"  - Bundle: {template_data.get('bundleName', 'Unknown')}")
    print(f"  - Main activity: {main_activity.get('id', 'Unknown')}")
    print(f"  - Entities: {len(entities)}")
    print(f"  - Sub-activities: {len(activities)}")
    print(f"  - Agents: {len(agents)}")
    print(f"  - Backward connectors: {len(backward_connectors)}")
    print(f"  - Forward connectors: {len(forward_connectors)}")

    # Analyze relationships
    total_used = len(main_activity.get('used', []))
    total_generated = len(main_activity.get('generated', []))
    total_parts = len(main_activity.get('hasPart', []))

    print(f"Main activity relationships:")
    print(f"  - Used entities: {total_used}")
    print(f"  - Generated entities: {total_generated}")
    print(f"  - Sub-parts: {total_parts}")

    # Analyze temporal coverage
    start_time = main_activity.get('startTime')
    end_time = main_activity.get('endTime')
    if start_time and end_time:
        print(f"Temporal coverage: {start_time} to {end_time}")


def main():
    """Main demonstration function."""
    print("=== CPM Template Examples ===")
    print("This demonstrates CPM template system and validation\n")

    try:
        # 1. Basic template creation and processing
        basic_template = create_basic_template()
        template, graph = demonstrate_template_processing(basic_template)

        # 2. Template serialization
        demonstrate_template_serialization(basic_template)

        # 3. Template validation
        demonstrate_template_validation(basic_template)

        # 4. Complex workflow template
        acquisition_template = create_acquisition_workflow_template()
        demonstrate_template_processing(acquisition_template)

        # 5. Template analysis
        demonstrate_template_analysis(acquisition_template)

        # 6. Error handling
        demonstrate_error_handling()

        print(f"\n✅ Template examples completed successfully!")
        print("Previous: basic_examples.py for fundamental operations")
        print("         advanced_examples.py for complex operations")

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
