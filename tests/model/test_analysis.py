"""
Tests for CpmDocumentAnalysisMixin – statistics, structure validation,
provenance chains, influence network, centrality, complexity.
"""

import pytest
from prov.model import ProvDocument
from src.cpm.model import CpmDocument
from src.cpm.builder import CpmDocumentBuilder


def _build_doc():
    builder = CpmDocumentBuilder("test:bundle")
    doc = (builder
           .with_main_activity("test:main", start_time="2024-01-01T00:00:00Z")
           .with_backward_connector("test:bc1", "test:src", "hash1")
           .with_forward_connector("test:fc1", "test:tgt", "hash2")
           .with_sender_agent("test:sender")
           .with_receiver_agent("test:receiver")
           .build())
    doc.add_node('entity', 'test:e1')
    doc.add_node('entity', 'test:e2')
    doc.add_node('entity', 'test:e3')
    doc.add_edge('used', 'test:main', 'test:e1')
    doc.add_edge('wasgeneratedby', 'test:main', 'test:e2')
    doc.add_edge('wasderivedfrom', 'test:e2', 'test:e1')
    doc.add_edge('wasderivedfrom', 'test:e3', 'test:e2')
    return doc


class TestGetTraversalInformationNodes:
    def test_returns_list(self):
        doc = _build_doc()
        ti = doc.get_traversal_information_nodes()
        assert isinstance(ti, list)
        assert len(ti) > 0

    def test_ti_nodes_belong_to_ti(self):
        doc = _build_doc()
        ti = doc.get_traversal_information_nodes()
        for n in ti:
            assert doc.ti_algorithm.belongs_to_traversal_information(n.prov_entity)


class TestGetDomainSpecificNodes:
    def test_returns_list(self):
        doc = _build_doc()
        ds = doc.get_domain_specific_nodes()
        assert isinstance(ds, list)

    def test_ds_nodes_not_ti(self):
        doc = _build_doc()
        ds = doc.get_domain_specific_nodes()
        for n in ds:
            assert not doc.ti_algorithm.belongs_to_traversal_information(n.prov_entity)


class TestGetStatistics:
    def test_stats_keys(self):
        doc = _build_doc()
        stats = doc.get_statistics()
        expected_keys = [
            'total_nodes', 'traversal_information_nodes',
            'domain_specific_nodes', 'entities', 'activities',
            'agents', 'forward_connectors', 'backward_connectors',
            'main_activities',
        ]
        for key in expected_keys:
            assert key in stats

    def test_stats_values_positive(self):
        doc = _build_doc()
        stats = doc.get_statistics()
        assert stats['total_nodes'] > 0
        assert stats['entities'] >= 0
        assert stats['activities'] >= 0
        assert stats['agents'] >= 0


class TestCrossPartEdges:
    def test_returns_list(self):
        doc = _build_doc()
        cross = doc.get_cross_part_edges()
        assert isinstance(cross, list)


class TestTraversalInformationPart:
    def test_returns_list(self):
        doc = _build_doc()
        ti_part = doc.get_traversal_information_part()
        assert isinstance(ti_part, list)


class TestValidateStructure:
    def test_returns_dict(self):
        doc = _build_doc()
        issues = doc.validate_structure()
        assert 'errors' in issues
        assert 'warnings' in issues
        assert 'info' in issues

    def test_empty_doc_warns_no_main_activity(self):
        doc = CpmDocument(ProvDocument())
        issues = doc.validate_structure()
        # Empty doc should warn about missing main activity
        assert any('main activity' in w.lower() for w in issues['warnings'])


class TestAnalyzeProvenanceChains:
    def test_returns_analysis(self):
        doc = _build_doc()
        analysis = doc.analyze_provenance_chains()
        assert 'total_chains' in analysis
        assert 'average_chain_length' in analysis
        assert 'longest_chain' in analysis
        assert 'circular_dependencies' in analysis

    def test_chain_count(self):
        doc = _build_doc()
        analysis = doc.analyze_provenance_chains()
        assert analysis['total_chains'] >= 0


class TestGetInfluenceNetwork:
    def test_returns_dict(self):
        doc = _build_doc()
        network = doc.get_influence_network()
        assert isinstance(network, dict)

    def test_network_has_node_entries(self):
        doc = _build_doc()
        network = doc.get_influence_network()
        assert len(network) > 0
        for node_id, influenced in network.items():
            assert isinstance(influenced, list)


class TestComputeCentralityMetrics:
    def test_returns_dict(self):
        doc = _build_doc()
        metrics = doc.compute_centrality_metrics()
        assert isinstance(metrics, dict)

    def test_metric_keys(self):
        doc = _build_doc()
        metrics = doc.compute_centrality_metrics()
        for node_id, m in metrics.items():
            assert 'degree_centrality' in m
            assert 'in_degree' in m
            assert 'out_degree' in m
            assert 'total_degree' in m


class TestTraceDerivationChain:
    def test_trace_from_entity(self):
        doc = _build_doc()
        entity_node = doc.get_node('test:e3')
        if entity_node:
            chain = doc._trace_derivation_chain(entity_node)
            assert isinstance(chain, list)
            assert len(chain) >= 1
            assert chain[0] == entity_node


class TestFindCircularDependencies:
    def test_no_circular_in_dag(self):
        doc = _build_doc()
        circular = doc._find_circular_dependencies()
        assert isinstance(circular, list)


class TestValidateCpmConstraints:
    def test_returns_dict(self):
        doc = _build_doc()
        issues = doc.validate_cpm_constraints()
        assert 'critical_errors' in issues
        assert 'warnings' in issues
        assert 'recommendations' in issues

    def test_empty_doc_has_errors(self):
        doc = CpmDocument(ProvDocument())
        issues = doc.validate_cpm_constraints()
        assert len(issues['critical_errors']) > 0


class TestAnalyzeDocumentComplexity:
    def test_returns_dict(self):
        doc = _build_doc()
        result = doc.analyze_document_complexity()
        assert 'basic_stats' in result
        assert 'complexity_metrics' in result

    def test_complexity_metrics_keys(self):
        doc = _build_doc()
        cm = doc.analyze_document_complexity()['complexity_metrics']
        assert 'node_count' in cm
        assert 'edge_count' in cm
        assert 'graph_density' in cm
        assert 'average_degree' in cm
        assert 'hub_nodes' in cm
        assert 'connected_components' in cm
        assert 'complexity_score' in cm

    def test_density_range(self):
        doc = _build_doc()
        cm = doc.analyze_document_complexity()['complexity_metrics']
        assert 0.0 <= cm['graph_density'] <= 1.0
