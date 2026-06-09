"""
Test CPM Document Mutability Features

Tests the CRUD operations and mutability functionality using the actual CpmDocument implementation.
This unified test suite demonstrates a complete workflow from template creation to advanced operations.
"""

import pytest
from prov.model import ProvDocument
from src.cpm.constants import CPM_MAIN_ACTIVITY, CPM_FORWARD_CONNECTOR, CPM_BACKWARD_CONNECTOR
from src.cpm.template import CpmBundleDeserializer
from src.cpm.model import (
    CpmDocument, TemplateProvMapper,
    CpmDocumentError, NodeNotFoundError, MultipleNodesError, InvalidOperationError
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Shared test data and fixtures
STANDARD_PREFIXES = {
    "ex": "http://example.org/",
    "cpm": "https://commonprovenancemodel.org/ns/cpm/"
}


def create_base_template():
    """Create a standard template for testing"""
    return {
        "prefixes": STANDARD_PREFIXES,
        "bundleName": "ex:testWorkflow",
        "mainActivity": {
            "id": "ex:dataProcessing",
            "startTime": "2024-01-01T09:00:00Z",
            "endTime": "2024-01-01T17:00:00Z",
            "used": [{"bcId": "ex:rawData"}],
            "generated": ["ex:processedData"]
        },
        "backwardConnectors": [{
            "id": "ex:rawData",
            "referencedBundleId": "ex:sourceSystem"
        }],
        "forwardConnectors": [{
            "id": "ex:processedData",
            "referencedBundleId": "ex:targetSystem"
        }],
        "senderAgents": [{"id": "ex:dataProvider"}],
        "receiverAgents": [{"id": "ex:dataConsumer"}]
    }


def create_manual_cpm_document():
    """Create a CPM document manually for testing CRUD operations"""
    doc = ProvDocument()
    doc.add_namespace("ex", "http://example.org/")
    doc.add_namespace("cpm", "https://commonprovenancemodel.org/ns/cpm/")
    bundle = doc.bundle("ex:manualTest")
    return CpmDocument(doc)


def test_unified_crud_and_relation_operations():
    """Unified test for CRUD operations and relation management"""
    cpm_doc = create_manual_cpm_document()

    # CREATE Operations - Build a complete workflow
    main_activity = cpm_doc.add_node('activity', "ex:processActivity",
                                     {"startTime": "2024-01-01T10:00:00Z",
                                      "endTime": "2024-01-01T12:00:00Z"},
                                     prov_type=CPM_MAIN_ACTIVITY)

    input_entity = cpm_doc.add_node('entity', "ex:input",
                                    {"label": "Input Data"},
                                    prov_type=CPM_BACKWARD_CONNECTOR)

    output_entity = cpm_doc.add_node('entity', "ex:output",
                                     {"label": "Output Data"},
                                     prov_type=CPM_FORWARD_CONNECTOR)

    processor_agent = cpm_doc.add_node('agent', "ex:processor", {"name": "Data Processor"})

    # Add intermediate processing step
    intermediate_entity = cpm_doc.add_node('entity', "ex:intermediate", {"step": "preprocessing"})
    preprocessing_activity = cpm_doc.add_node('activity', "ex:preprocessing",
                                              {"startTime": "2024-01-01T10:30:00Z",
                                               "endTime": "2024-01-01T11:00:00Z"})

    # CREATE Relations - Build the complete provenance chain
    cpm_doc.add_edge('used', "ex:processActivity", "ex:input", edge_id="ex:usage1")
    cpm_doc.add_edge('wasgeneratedby', "ex:processActivity", "ex:output")
    cpm_doc.add_edge('wasattributedto', "ex:output", "ex:processor")
    cpm_doc.add_edge('wasderivedfrom', "ex:output", "ex:input")

    # Intermediate processing relations
    cpm_doc.add_edge('used', "ex:preprocessing", "ex:input")
    cpm_doc.add_edge('wasgeneratedby', "ex:preprocessing", "ex:intermediate")
    cpm_doc.add_edge('used', "ex:processActivity", "ex:intermediate")

    # READ Operations - Verify the structure
    found_main = cpm_doc.get_main_activity()
    found_input = cpm_doc.get_node("ex:input")
    all_edges = cpm_doc.get_edges()
    stats = cpm_doc.get_statistics()

    assert found_main is not None
    assert found_input is not None
    assert stats['total_nodes'] == 6  # 4 original + 2 intermediate
    assert len(all_edges) >= 6  # All the relations we created

    # Edge-specific operations
    # For Usage relation: edge direction is entity → activity (PROV-DM)
    specific_edges = cpm_doc.get_edges('ex:input', 'ex:processActivity')
    assert len(specific_edges) > 0

    # UPDATE/MODIFY Operations - Add domain-specific content
    cpm_doc.add_node('entity', "ex:metadata", {"type": "metadata", "version": "1.0"})
    cpm_doc.add_edge('wasattributedto', "ex:metadata", "ex:processor")

    updated_stats = cpm_doc.get_statistics()
    assert updated_stats['total_nodes'] > stats['total_nodes']

    # DELETE Operations - Clean up intermediate node
    removed_edge = cpm_doc.remove_edge('ex:preprocessing', 'ex:intermediate')
    removed_node = cpm_doc.remove_node("ex:intermediate")

    assert removed_edge is True
    assert removed_node is True
    assert cpm_doc.get_node("ex:intermediate") is None


def test_unified_error_handling_and_validation():
    """Unified test for error handling across all operations"""
    cpm_doc = create_manual_cpm_document()

    # Test node creation errors
    cpm_doc.add_node('entity', "ex:duplicate")
    with pytest.raises(InvalidOperationError):
        cpm_doc.add_node('entity', "ex:duplicate")

    # Test relation errors with missing nodes
    with pytest.raises(NodeNotFoundError):
        cpm_doc.add_edge('used', "ex:missingActivity", "ex:missingEntity")

    # Test query operations with non-existent items
    missing_node = cpm_doc.get_node("ex:nonExistent")
    assert missing_node is None

    removed_nonexistent = cpm_doc.remove_node("ex:nonExistent")
    assert removed_nonexistent is False

    removed_nonexistent_edge = cpm_doc.remove_edge("ex:missing1", "ex:missing2")
    assert removed_nonexistent_edge is False


def test_unified_template_to_advanced_operations():
    """Unified test showing the complete workflow from template to advanced operations"""

    # Start with template-based document
    template_data = create_base_template()
    template = CpmBundleDeserializer.from_json(template_data)
    cpm_doc = CpmDocument.from_template(template)
    initial_stats = cpm_doc.get_statistics()

    # Extend with domain-specific content
    preprocessing_activity = cpm_doc.add_node('activity', "ex:preprocessing",
                                              {"startTime": "2024-01-01T10:00:00Z",
                                               "endTime": "2024-01-01T11:00:00Z"})

    intermediate_data = cpm_doc.add_node('entity', "ex:intermediateData",
                                         {"step": "preprocessing", "format": "csv"})

    quality_agent = cpm_doc.add_node('agent', "ex:qualityChecker",
                                     {"role": "validation"})

    # Build extended provenance chain
    cpm_doc.add_edge('used', "ex:preprocessing", "ex:rawData")
    cpm_doc.add_edge('wasgeneratedby', "ex:preprocessing", "ex:intermediateData")
    cpm_doc.add_edge('used', "ex:dataProcessing", "ex:intermediateData")
    cpm_doc.add_edge('wasassociatedwith', "ex:preprocessing", "ex:qualityChecker")

    # Test advanced analysis operations
    modified_stats = cpm_doc.get_statistics()
    assert modified_stats['total_nodes'] > initial_stats['total_nodes']

    # Test TI/DS separation
    ti_nodes = cpm_doc.get_traversal_information_nodes()
    ds_nodes = cpm_doc.get_domain_specific_nodes()
    assert len(ti_nodes) > 0
    assert len(ds_nodes) > 0

    # Test document analysis
    complexity_analysis = cpm_doc.analyze_document_complexity()
    assert 'complexity_metrics' in complexity_analysis

    # Test validation
    validation_results = cpm_doc.validate_structure()
    assert isinstance(validation_results, dict)
    assert 'errors' in validation_results
    assert 'warnings' in validation_results

    # Test cloning
    cloned_doc = cpm_doc.clone()
    assert cloned_doc.get_statistics()['total_nodes'] == cpm_doc.get_statistics()['total_nodes']

    # Create second document for merging test
    template_data2 = {
        "prefixes": STANDARD_PREFIXES,
        "bundleName": "ex:additionalWorkflow",
        "mainActivity": {
            "id": "ex:analysisActivity",
            "used": [{"bcId": "ex:analysisInput"}]
        },
        "backwardConnectors": [{"id": "ex:analysisInput"}]
    }

    template2 = CpmBundleDeserializer.from_json(template_data2)
    doc2 = CpmDocument.from_template(template2)

    # Test merging
    merged_doc = cpm_doc.merge_with(doc2, conflict_resolution='keep_both')
    assert isinstance(merged_doc, CpmDocument)


def test_unified_comprehensive_workflow():
    """Complete end-to-end workflow test combining all features"""

    # Phase 1: Template-based initialization
    template_data = create_base_template()
    template = CpmBundleDeserializer.from_json(template_data)
    workflow_doc = CpmDocument.from_template(template)

    # Phase 2: Dynamic content addition
    # Add preprocessing pipeline
    steps = ["validation", "cleaning", "transformation"]
    previous_entity = "ex:rawData"

    for i, step in enumerate(steps):
        step_activity = workflow_doc.add_node('activity', f"ex:{step}Activity",
                                              {"step": step, "order": i})
        step_output = workflow_doc.add_node('entity', f"ex:{step}Output",
                                            {"stage": step})

        workflow_doc.add_edge('used', f"ex:{step}Activity", previous_entity)
        workflow_doc.add_edge('wasgeneratedby', f"ex:{step}Activity", f"ex:{step}Output")
        previous_entity = f"ex:{step}Output"

    # Connect final preprocessing output to main activity
    workflow_doc.add_edge('used', "ex:dataProcessing", previous_entity)

    # Phase 3: Quality assurance and monitoring
    qa_agent = workflow_doc.add_node('agent', "ex:qaAgent", {"role": "quality_assurance"})
    monitor_entity = workflow_doc.add_node('entity', "ex:qualityMetrics",
                                           {"type": "metrics"})

    # Associate QA with all activities
    for step in steps:
        workflow_doc.add_edge('wasassociatedwith', f"ex:{step}Activity", "ex:qaAgent")

    workflow_doc.add_edge('wasgeneratedby', "ex:qaAgent", "ex:qualityMetrics")

    # Phase 4: Comprehensive testing and validation
    final_stats = workflow_doc.get_statistics()
    assert final_stats['total_nodes'] >= 10  # Significant content added

    # Test all major operations work together
    validation_results = workflow_doc.validate_structure()
    complexity_analysis = workflow_doc.analyze_document_complexity()
    ti_nodes = workflow_doc.get_traversal_information_nodes()
    ds_nodes = workflow_doc.get_domain_specific_nodes()

    assert isinstance(validation_results, dict)
    assert isinstance(complexity_analysis, dict)
    assert len(ti_nodes) > 0
    assert len(ds_nodes) > 0

    # Test that the document maintains integrity
    main_activity = workflow_doc.get_main_activity()
    assert main_activity is not None
    assert main_activity.identifier == "ex:dataProcessing"


def run_all_mutability_tests():
    """Run all unified tests"""
    try:
        test_unified_crud_and_relation_operations()
        test_unified_error_handling_and_validation()
        test_unified_template_to_advanced_operations()
        test_unified_comprehensive_workflow()
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_all_mutability_tests()
