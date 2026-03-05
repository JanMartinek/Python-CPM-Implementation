"""
Test Comprehensive Features - Tests for CPM methods implemented in Python

This test suite verifies that the Python implementation provides complete
functionality for the CpmDocument class methods.
"""

from src.cpm.model import CpmDocument
from src.cpm.builder import CpmDocumentBuilder
from src.cpm.validation import CpmValidator
from src.cpm.template import TraversalInformationTemplate, MainActivityTemplate, ConnectorTemplate, AgentTemplate
from prov.model import ProvDocument
import traceback
import sys
import os
sys.path.append('.')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_core_methods():
    try:
        builder = CpmDocumentBuilder("test:bundle")
        cpm_doc = (builder
                   .with_main_activity("test:main", start_time="2024-01-01T00:00:00Z")
                   .with_backward_connector("test:bc1", "test:source_bundle", "hash123")
                   .with_forward_connector("test:fc1", "test:target_bundle", "hash456")
                   .with_sender_agent("test:sender")
                   .with_receiver_agent("test:receiver")
                   .build())

        cpm_doc.add_node('entity', 'test:entity1', {'label': 'Test Entity 1'})
        cpm_doc.add_node('entity', 'test:entity2', {'label': 'Test Entity 2'})
        cpm_doc.add_edge('wasderivedfrom', 'test:entity2', 'test:entity1')

        # Test get_edge_by_id
        edge = cpm_doc.add_edge('used', 'test:main', 'test:entity1', edge_id='test:usage1')
        retrieved_edge = cpm_doc.get_edge_by_id('test:usage1')
        assert retrieved_edge is not None

        # Test get_node_by_id_and_kind
        entity_node = cpm_doc.get_node_by_id_and_kind('test:entity1', 'entity')
        activity_node = cpm_doc.get_node_by_id_and_kind('test:main', 'activity')
        assert entity_node is not None
        assert activity_node is not None

        # Test other methods
        mapped = cpm_doc.are_all_relations_mapped()
        assert isinstance(mapped, bool)

        precursors = cpm_doc.get_precursors('test:bc1')
        successors = cpm_doc.get_successors_connectors('test:fc1')

        bundle_id = cpm_doc.get_bundle_id()
        set_result = cpm_doc.set_bundle_id('test:new_bundle')
        assert bundle_id is not None
        assert isinstance(set_result, bool)

        hash_code = cpm_doc.hash_code()
        equals_self = cpm_doc.equals(cpm_doc)
        assert isinstance(hash_code, int)
        assert equals_self is True

        all_nodes = cpm_doc.get_all_nodes()
        all_edges = cpm_doc.get_all_edges()
        assert isinstance(all_nodes, list)
        assert isinstance(all_edges, list)

        namespaces = cpm_doc.get_namespaces()
        assert isinstance(namespaces, dict)

        prov_doc = cpm_doc.to_document()
        assert isinstance(prov_doc, ProvDocument)

    except Exception as e:
        traceback.print_exc()
        raise


def test_advanced_features():
    try:
        builder = CpmDocumentBuilder("advanced:bundle")
        cpm_doc = (builder
                   .with_main_activity("advanced:main")
                   .with_backward_connector("advanced:bc1", "advanced:source1")
                   .with_backward_connector("advanced:bc2", "advanced:source2")
                   .with_forward_connector("advanced:fc1", "advanced:target1")
                   .build())

        cpm_doc.add_node('entity', 'advanced:collection')
        cpm_doc.add_node('entity', 'advanced:member1')
        cpm_doc.add_node('entity', 'advanced:member2')

        success = cpm_doc.update_collection_members_advanced(
            'advanced:collection', [],
            'advanced:collection', ['advanced:member1', 'advanced:member2'],
            validate_existence=True
        )
        assert isinstance(success, bool)

        issues = cpm_doc.validate_cpm_constraints()
        assert isinstance(issues, dict)
        assert 'critical_errors' in issues
        assert 'warnings' in issues

        analysis = cpm_doc.analyze_document_complexity()
        assert isinstance(analysis, dict)
        assert 'complexity_metrics' in analysis

    except Exception as e:
        traceback.print_exc()
        raise


def test_cpm_document_builder():
    try:
        builder = CpmDocumentBuilder("builder:test")
        doc = (builder
               .with_main_activity("builder:main", start_time="2024-01-01T00:00:00Z")
               .with_backward_connector("builder:bc", "builder:source", "hash123")
               .with_sender_agent("builder:sender", role="DataProvider")
               .with_prefix("custom", "http://custom.org/")
               .build())

        main_activity = doc.get_main_activity()
        assert main_activity is not None

        backward_connectors = doc.get_backward_connectors()
        assert isinstance(backward_connectors, list)

        namespaces = doc.get_namespaces()
        assert isinstance(namespaces, dict)

    except Exception as e:
        traceback.print_exc()
        raise


def test_cpm_validator():
    try:
        builder = CpmDocumentBuilder("validation:test")
        doc = (builder
               .with_main_activity("validation:main")
               .with_backward_connector("validation:bc", "validation:source")
               .build())

        validator = CpmValidator()
        results = validator.validate(doc.to_graph_wrapper())
        assert hasattr(results, 'results')
        assert hasattr(results, 'is_valid')
        assert hasattr(results, 'error_count')
        assert hasattr(results, 'warning_count')

        doc.add_node('entity', 'validation:orphan')
        results2 = validator.validate(doc.to_graph_wrapper())
        assert hasattr(results2, 'results')

    except Exception as e:
        traceback.print_exc()
        raise


def test_error_handling():
    try:
        builder = CpmDocumentBuilder("error:test")
        doc = (builder
               .with_main_activity("error:main")
               .build())

        node = doc.get_node('error:nonexistent')
        assert node is None

        edge = doc.get_edge('error:nonexistent1', 'error:nonexistent2')
        assert edge is None

        try:
            doc.add_edge('invalid_relation', 'error:nonexistent1', 'error:nonexistent2')
            assert False, "Should have raised error"
        except Exception:
            pass  # Expected

    except Exception as e:
        traceback.print_exc()
        raise


def test_performance_operations():
    try:
        builder = CpmDocumentBuilder("perf:test")
        doc = (builder
               .with_main_activity("perf:main")
               .build())

        node_count = 50
        for i in range(node_count):
            doc.add_node('entity', f'perf:entity_{i}', {'index': i})

        edge_count = 0
        for i in range(0, node_count-1, 2):
            try:
                doc.add_edge('wasderivedfrom', f'perf:entity_{i+1}', f'perf:entity_{i}')
                edge_count += 1
            except Exception:
                pass

        stats = doc.get_statistics()
        assert isinstance(stats, dict)
        assert stats['total_nodes'] >= node_count

        analysis = doc.analyze_document_complexity()
        assert isinstance(analysis, dict)

    except Exception as e:
        traceback.print_exc()
        raise


def run_comprehensive_tests():
    test_results = []

    test_results.append(("Core Methods", test_core_methods()))
    test_results.append(("Advanced Features", test_advanced_features()))
    test_results.append(("Document Builder", test_cpm_document_builder()))
    test_results.append(("CPM Validator", test_cpm_validator()))
    test_results.append(("Error Handling", test_error_handling()))
    test_results.append(("Performance Operations", test_performance_operations()))

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    return passed == total


if __name__ == '__main__':
    success = run_comprehensive_tests()
    exit(0 if success else 1)
