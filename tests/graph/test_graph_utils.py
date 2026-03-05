"""
Tests for graph_utils.py - GraphAnalyzer and PriorityBasedScheduler.
"""

import pytest
from prov.model import ProvDocument
from src.cpm.model import CpmDocument
from src.cpm.builder import CpmDocumentBuilder
from src.utils.graph_utils import GraphAnalyzer, PriorityBasedScheduler


def _build_simple_doc():
    """Helper: build a simple CpmDocument with a few nodes and edges."""
    builder = CpmDocumentBuilder("test:bundle")
    doc = (builder
           .with_main_activity("test:main", start_time="2024-01-01T00:00:00Z")
           .with_backward_connector("test:bc1", "test:src_bundle", "hash1")
           .with_forward_connector("test:fc1", "test:tgt_bundle", "hash2")
           .with_sender_agent("test:sender")
           .with_receiver_agent("test:receiver")
           .build())
    doc.add_node('entity', 'test:e1', {'label': 'E1'})
    doc.add_node('entity', 'test:e2', {'label': 'E2'})
    doc.add_edge('used', 'test:main', 'test:e1')
    doc.add_edge('wasgeneratedby', 'test:main', 'test:e2')
    doc.add_edge('wasderivedfrom', 'test:e2', 'test:e1')
    return doc


def _build_chain_doc():
    """Helper: build a doc with a linear chain e1 -> e2 -> e3."""
    builder = CpmDocumentBuilder("test:bundle")
    doc = (builder
           .with_main_activity("test:main")
           .with_backward_connector("test:bc1", "test:src", "h")
           .build())
    doc.add_node('entity', 'test:e1')
    doc.add_node('entity', 'test:e2')
    doc.add_node('entity', 'test:e3')
    doc.add_edge('wasderivedfrom', 'test:e2', 'test:e1')
    doc.add_edge('wasderivedfrom', 'test:e3', 'test:e2')
    doc.add_edge('used', 'test:main', 'test:e1')
    return doc


# ─── GraphAnalyzer ───────────────────────────────────────────────────────────

class TestGraphAnalyzer:
    def test_compute_graph_metrics(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        metrics = analyzer.compute_graph_metrics()

        assert 'node_count' in metrics
        assert 'edge_count' in metrics
        assert 'density' in metrics
        assert 'connected_components' in metrics
        assert 'diameter' in metrics
        assert 'clustering_coefficient' in metrics
        assert 'centrality_distribution' in metrics
        assert 'node_type_distribution' in metrics
        assert metrics['node_count'] > 0

    def test_graph_metrics_caching(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        m1 = analyzer.compute_graph_metrics()
        m2 = analyzer.compute_graph_metrics()  # should hit cache
        assert m1 is m2

    def test_find_critical_paths(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        paths = analyzer.find_critical_paths()
        assert isinstance(paths, list)

    def test_detect_anomalies(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        anomalies = analyzer.detect_anomalies()

        assert 'isolated_nodes' in anomalies
        assert 'high_degree_nodes' in anomalies
        assert 'missing_timestamps' in anomalies
        assert 'broken_chains' in anomalies
        assert 'unusual_patterns' in anomalies

    def test_compute_influence_scores(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        scores = analyzer.compute_influence_scores()
        assert isinstance(scores, dict)
        assert all(isinstance(v, (int, float)) for v in scores.values())

    def test_adjacency_list_caching(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        adj1 = analyzer._build_adjacency_list()
        adj2 = analyzer._build_adjacency_list()  # cached
        assert adj1 is adj2

    def test_count_edges(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        count = analyzer._count_edges()
        assert count >= 0

    def test_compute_density(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        density = analyzer._compute_density(adj, len(doc.graph_wrapper.get_nodes()))
        assert 0.0 <= density <= 1.0

    def test_compute_density_single_node(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        assert analyzer._compute_density({}, 1) == 0.0
        assert analyzer._compute_density({}, 0) == 0.0

    def test_find_connected_components(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        components = analyzer._find_connected_components(adj)
        assert isinstance(components, list)

    def test_compute_diameter(self):
        doc = _build_chain_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        diameter = analyzer._compute_diameter(adj)
        assert isinstance(diameter, int)
        assert diameter >= 0

    def test_bfs_distances(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        if adj:
            start = next(iter(adj.keys()))
            distances = analyzer._bfs_distances(start, adj)
            assert distances[start] == 0

    def test_compute_clustering_coefficient(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        cc = analyzer._compute_clustering_coefficient(adj)
        assert 0.0 <= cc <= 1.0

    def test_clustering_coefficient_empty(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        assert analyzer._compute_clustering_coefficient({}) == 0.0

    def test_centrality_distribution(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        centrality = analyzer._compute_centrality_distribution()
        assert 'degree' in centrality
        assert 'betweenness' in centrality
        assert 'closeness' in centrality
        assert 'priority_based' in centrality

    def test_betweenness_centrality(self):
        doc = _build_chain_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        bc = analyzer._compute_betweenness_centrality(adj)
        assert isinstance(bc, dict)

    def test_closeness_centrality(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        cc = analyzer._compute_closeness_centrality(adj)
        assert isinstance(cc, dict)

    def test_priority_centrality(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        pc = analyzer._compute_priority_centrality()
        assert isinstance(pc, dict)

    def test_node_type_distribution(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        dist = analyzer._compute_node_type_distribution()
        assert isinstance(dist, dict)

    def test_find_longest_paths_from(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        nodes = doc.graph_wrapper.get_nodes()
        if nodes:
            paths = analyzer._find_longest_paths_from(nodes[0])
            assert isinstance(paths, list)

    def test_is_isolated(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        # Add an isolated node
        doc.add_node('entity', 'test:isolated')
        isolated_node = doc.get_node('test:isolated')
        assert analyzer._is_isolated(isolated_node)

    def test_compute_node_degree(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        nodes = doc.graph_wrapper.get_nodes()
        for n in nodes:
            degree = analyzer._compute_node_degree(n)
            assert degree >= 0

    def test_has_valid_timestamps(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        nodes = doc.graph_wrapper.get_nodes()
        for n in nodes:
            result = analyzer._has_valid_timestamps(n)
            assert isinstance(result, bool)

    def test_find_broken_chains(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        broken = analyzer._find_broken_chains()
        assert isinstance(broken, list)

    def test_find_all_shortest_paths(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        nodes_list = list(adj.keys())
        if len(nodes_list) >= 2:
            paths = analyzer._find_all_shortest_paths(nodes_list[0], nodes_list[1], adj)
            assert isinstance(paths, list)

    def test_find_all_shortest_paths_same_node(self):
        doc = _build_simple_doc()
        analyzer = GraphAnalyzer(doc)
        adj = analyzer._build_adjacency_list()
        if adj:
            node = next(iter(adj.keys()))
            paths = analyzer._find_all_shortest_paths(node, node, adj)
            assert len(paths) == 1
            assert paths[0] == [node]


# ─── PriorityBasedScheduler ─────────────────────────────────────────────────

class TestPriorityBasedScheduler:
    def test_compute_node_priorities(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        priorities = scheduler.compute_node_priorities()
        assert isinstance(priorities, dict)
        assert len(priorities) > 0
        assert all(isinstance(v, float) for v in priorities.values())

    def test_priority_caching(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        p1 = scheduler.compute_node_priorities()
        p2 = scheduler.compute_node_priorities()
        assert p1 is p2

    def test_get_execution_order(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        order = scheduler.get_execution_order()
        assert isinstance(order, list)
        assert len(order) > 0

    def test_find_lowest_priority_nodes(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        lowest = scheduler.find_lowest_priority_nodes(3)
        assert isinstance(lowest, list)
        assert len(lowest) <= 3
        # Should be sorted ascending
        if len(lowest) >= 2:
            assert lowest[0][1] <= lowest[1][1]

    def test_find_highest_priority_nodes(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        highest = scheduler.find_highest_priority_nodes(3)
        assert isinstance(highest, list)
        assert len(highest) <= 3
        # Should be sorted descending
        if len(highest) >= 2:
            assert highest[0][1] >= highest[1][1]

    def test_diagnose_priority_issues(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        diagnosis = scheduler.diagnose_priority_issues()
        assert 'zero_priority_nodes' in diagnosis
        assert 'negative_priority_nodes' in diagnosis
        assert 'priority_conflicts' in diagnosis
        assert 'dependency_violations' in diagnosis

    def test_calculate_node_priority(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        nodes = doc.graph_wrapper.get_nodes()
        for n in nodes:
            priority = scheduler._calculate_node_priority(n)
            assert isinstance(priority, float)
            assert priority >= 0

    def test_compute_in_degrees(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        in_deg = scheduler._compute_in_degrees()
        assert isinstance(in_deg, dict)
        assert all(isinstance(v, int) for v in in_deg.values())

    def test_is_on_critical_path(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        nodes = doc.graph_wrapper.get_nodes()
        for n in nodes:
            result = scheduler._is_on_critical_path(n)
            assert isinstance(result, bool)

    def test_find_priority_dependency_violations(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        scheduler.compute_node_priorities()  # populate cache
        violations = scheduler._find_priority_dependency_violations()
        assert isinstance(violations, list)

    def test_find_priority_conflicts(self):
        doc = _build_simple_doc()
        scheduler = PriorityBasedScheduler(doc)
        scheduler.compute_node_priorities()
        conflicts = scheduler._find_priority_conflicts()
        assert isinstance(conflicts, list)
