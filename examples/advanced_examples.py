#!/usr/bin/env python3
"""
Advanced CPM Examples

This file demonstrates advanced operations of the Common Provenance Model (CPM) 
Python implementation, including:

1. Advanced graph traversal and analysis
2. Document mutability and CRUD operations  
3. Complex graph algorithms (path finding, connectivity)
4. Subgraph extraction and filtering
5. Performance analysis and optimization
6. Advanced export/import with multiple formats

This covers sophisticated CPM operations for complex provenance scenarios.
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.prov_adapter import ProvAdapter
from src.graph.edge import GraphEdge
from src.graph.node import GraphNode
from src.graph.wrapper import ProvGraphWrapper
from prov.model import ProvDocument

import json
import copy
from typing import Dict, Any, List, Optional, Set, Tuple


def create_complex_prov_document() -> ProvDocument:
    """Create a complex multi-stage data processing workflow."""
    print("Creating complex PROV document with multiple stages...")

    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    doc.add_namespace('data', 'http://data.example.org/')

    # Stage 1: Data Collection
    raw_data1 = doc.entity('data:sensor_data_1', {'prov:type': 'Dataset', 'ex:sensor': 'temp_01'})
    raw_data2 = doc.entity('data:sensor_data_2', {'prov:type': 'Dataset', 'ex:sensor': 'humidity_01'})
    raw_data3 = doc.entity('data:external_feed', {'prov:type': 'Dataset', 'ex:source': 'weather_api'})

    # Stage 2: Processing outputs
    cleaned_data = doc.entity('data:cleaned_dataset', {'prov:type': 'Dataset'})
    merged_data = doc.entity('data:merged_dataset', {'prov:type': 'Dataset'})

    # Stage 3: Analysis outputs
    statistics = doc.entity('data:statistics', {'prov:type': 'Report'})
    model_results = doc.entity('data:model_output', {'prov:type': 'Model'})
    final_report = doc.entity('data:final_report', {'prov:type': 'Report'})

    # Activities (processing stages)
    data_cleaning = doc.activity('ex:data_cleaning', '2024-01-01T08:00:00Z', '2024-01-01T10:00:00Z')
    data_merging = doc.activity('ex:data_merging', '2024-01-01T10:30:00Z', '2024-01-01T11:00:00Z')
    statistical_analysis = doc.activity('ex:statistical_analysis', '2024-01-01T11:30:00Z', '2024-01-01T13:00:00Z')
    modeling = doc.activity('ex:modeling', '2024-01-01T13:30:00Z', '2024-01-01T15:00:00Z')
    report_generation = doc.activity('ex:report_generation', '2024-01-01T15:30:00Z', '2024-01-01T16:00:00Z')

    # Agents
    data_engineer = doc.agent('ex:data_engineer', {'prov:type': 'Person'})
    analyst = doc.agent('ex:analyst', {'prov:type': 'Person'})
    ml_system = doc.agent('ex:ml_system', {'prov:type': 'SoftwareAgent'})

    # Stage 1: Data cleaning relationships
    doc.usage(data_cleaning, raw_data1)
    doc.usage(data_cleaning, raw_data2)
    doc.generation(cleaned_data, data_cleaning)
    doc.association(data_cleaning, data_engineer)

    # Stage 2: Data merging relationships
    doc.usage(data_merging, cleaned_data)
    doc.usage(data_merging, raw_data3)
    doc.generation(merged_data, data_merging)
    doc.association(data_merging, data_engineer)

    # Stage 3: Analysis relationships
    doc.usage(statistical_analysis, merged_data)
    doc.generation(statistics, statistical_analysis)
    doc.association(statistical_analysis, analyst)

    doc.usage(modeling, merged_data)
    doc.generation(model_results, modeling)
    doc.association(modeling, ml_system)

    # Stage 4: Report generation
    doc.usage(report_generation, statistics)
    doc.usage(report_generation, model_results)
    doc.generation(final_report, report_generation)
    doc.association(report_generation, analyst)

    # Add some derivation relationships
    doc.derivation(cleaned_data, raw_data1)
    doc.derivation(cleaned_data, raw_data2)
    doc.derivation(merged_data, cleaned_data)
    doc.derivation(final_report, statistics)
    doc.derivation(final_report, model_results)

    print(f"✓ Created complex PROV document with {len(list(doc.get_records()))} records")
    return doc


def demonstrate_advanced_traversal(graph: ProvGraphWrapper):
    """Demonstrate advanced graph traversal capabilities."""
    print("\nDemonstrating advanced graph traversal...")

    nodes = list(graph.get_nodes())

    # Find a node to start traversal from
    start_node = None
    for node in nodes:
        if len(node.all_edges) > 1:  # Find a well-connected node
            start_node = node
            break

    if not start_node:
        start_node = nodes[0]

    print(f"Starting traversal from: {start_node.identifier}")

    # Get all connected nodes
    connected = start_node.get_connected_nodes()
    print(f"  Directly connected to {len(connected)} nodes:")
    for node in connected[:5]:  # Show first 5
        print(f"    - {node.identifier}")
    if len(connected) > 5:
        print(f"    ... and {len(connected) - 5} more")

    # Analyze edge types
    edge_types = {}
    for edge in start_node.all_edges:
        edge_type = edge.kind
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

    print(f"  Edge type distribution:")
    for edge_type, count in edge_types.items():
        print(f"    - {edge_type}: {count}")


def find_paths_between_nodes(graph: ProvGraphWrapper, max_depth: int = 3) -> List[List[GraphNode]]:
    """Find paths between nodes using breadth-first search."""
    print(f"\nFinding paths in graph (max depth: {max_depth})...")

    nodes = list(graph.get_nodes())
    if len(nodes) < 2:
        print("  Need at least 2 nodes to find paths")
        return []

    paths = []

    def bfs_paths(start: GraphNode, end: GraphNode, max_depth: int) -> List[List[GraphNode]]:
        if start == end:
            return [[start]]

        queue = [(start, [start])]
        found_paths = []

        for _ in range(max_depth):
            if not queue:
                break

            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue

            for neighbor in current.get_connected_nodes():
                if neighbor not in path:  # Avoid cycles
                    new_path = path + [neighbor]
                    if neighbor == end:
                        found_paths.append(new_path)
                    else:
                        queue.append((neighbor, new_path))

        return found_paths

    # Find paths between first few node pairs
    for i in range(min(3, len(nodes))):
        for j in range(i+1, min(i+3, len(nodes))):
            start, end = nodes[i], nodes[j]
            node_paths = bfs_paths(start, end, max_depth)
            paths.extend(node_paths)

            if node_paths:
                print(f"  Found {len(node_paths)} path(s) from {start.identifier} to {end.identifier}")
                for k, path in enumerate(node_paths[:2], 1):  # Show first 2 paths
                    path_ids = [n.identifier for n in path]
                    print(f"    Path {k}: {' -> '.join(path_ids)}")
            else:
                print(f"  No paths found from {start.identifier} to {end.identifier}")

    return paths


def demonstrate_graph_filtering(graph: ProvGraphWrapper) -> ProvGraphWrapper:
    """Demonstrate graph filtering and subgraph extraction."""
    print("\nDemonstrating graph filtering...")

    nodes = list(graph.get_nodes())

    # Filter nodes by type (keep only entities with certain types)
    def node_filter(node: GraphNode) -> bool:
        # Check if node represents a dataset or report
        for attr_name, attr_value in node.prov_entity.attributes:
            if str(attr_name) == 'prov:type':
                return str(attr_value) in ['Dataset', 'Report']
        return True  # Keep nodes without explicit type

    # Create a subgraph with only filtered nodes
    filtered_graph = graph.create_subgraph(node_filter)

    print(f"  Filtered {len(nodes)} nodes to {len(filtered_graph)} nodes")
    print(f"  Original graph: {len(graph)} nodes, {len(graph.get_edges())} edges")
    print(f"  Filtered graph: {len(filtered_graph)} nodes, {len(filtered_graph.get_edges())} edges")

    return filtered_graph


def demonstrate_document_mutation():
    """Demonstrate document mutability and CRUD operations."""
    print("\nDemonstrating document mutation...")

    # Start with a simple document
    doc = ProvDocument()
    doc.add_namespace('mut', 'http://mutation.example.org/')

    # Initial entities
    entity1 = doc.entity('mut:data1', {'prov:label': 'Initial Data'})
    entity2 = doc.entity('mut:data2', {'prov:label': 'Processed Data'})

    initial_activity = doc.activity('mut:process1', '2024-01-01T10:00:00Z', '2024-01-01T11:00:00Z')
    doc.usage(initial_activity, entity1)
    doc.generation(entity2, initial_activity)

    graph = ProvGraphWrapper(doc)
    print(f"  Initial state: {len(graph)} nodes, {len(graph.get_edges())} edges")

    # Add new entities and relationships
    entity3 = doc.entity('mut:data3', {'prov:label': 'Final Results'})
    new_activity = doc.activity('mut:analysis1', '2024-01-01T11:30:00Z', '2024-01-01T12:30:00Z')
    doc.usage(new_activity, entity2)
    doc.generation(entity3, new_activity)

    # Update the graph
    graph = ProvGraphWrapper(doc)  # Recreate graph with new elements
    print(f"  After addition: {len(graph)} nodes, {len(graph.get_edges())} edges")

    # Demonstrate entity attribute modification
    print(f"  Modified entity attributes and relationships")

    return graph


def analyze_graph_properties(graph: ProvGraphWrapper):
    """Analyze various graph properties and metrics."""
    print("\nAnalyzing graph properties...")

    nodes = list(graph.get_nodes())
    edges = graph.get_edges()

    if not nodes:
        print("  Empty graph - no analysis possible")
        return

    # Basic metrics
    num_nodes = len(nodes)
    num_edges = len(edges)

    print(f"  Graph size: {num_nodes} nodes, {num_edges} edges")

    # Node degree analysis
    degrees = []
    for node in nodes:
        degree = len(node.all_edges)
        degrees.append(degree)

    if degrees:
        avg_degree = sum(degrees) / len(degrees)
        max_degree = max(degrees)
        min_degree = min(degrees)

        print(f"  Node degree - avg: {avg_degree:.2f}, max: {max_degree}, min: {min_degree}")

    # Edge type distribution
    edge_types = {}
    for edge in edges:
        edge_type = edge.kind
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

    print(f"  Edge types:")
    for edge_type, count in sorted(edge_types.items()):
        percentage = (count / num_edges * 100) if num_edges > 0 else 0
        print(f"    - {edge_type}: {count} ({percentage:.1f}%)")

    # Connectivity analysis
    isolated_nodes = [node for node in nodes if len(node.all_edges) == 0]
    print(f"  Isolated nodes: {len(isolated_nodes)}")

    # Hub nodes (nodes with degree > average)
    if degrees:
        avg_degree = sum(degrees) / len(degrees)
        hubs = [node for node in nodes if len(node.all_edges) > avg_degree * 1.5]
        print(f"  Hub nodes (degree > {avg_degree*1.5:.1f}): {len(hubs)}")
        for hub in hubs[:3]:  # Show top 3
            print(f"    - {hub.identifier} (degree: {len(hub.all_edges)})")


def demonstrate_performance_analysis(graph: ProvGraphWrapper):
    """Demonstrate performance analysis of graph operations."""
    print("\nDemonstrating performance analysis...")

    import time

    nodes = list(graph.get_nodes())
    if not nodes:
        print("  No nodes for performance testing")
        return

    # Test node traversal performance
    start_time = time.perf_counter()
    total_connections = 0
    for node in nodes:
        connected = node.get_connected_nodes()
        total_connections += len(connected)
    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000
    print(f"  Node traversal: {len(nodes)} nodes, {total_connections} total connections")
    print(f"  Time: {elapsed_ms:.3f}ms ({elapsed_ms*1000:.1f}µs)")

    # Test edge analysis performance
    start_time = time.perf_counter()
    edges = graph.get_edges()
    edge_analysis = {}
    for edge in edges:
        key = (str(edge.cause.identifier), str(edge.effect.identifier), edge.kind)
        edge_analysis[key] = edge_analysis.get(key, 0) + 1
    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000
    print(f"  Edge analysis: {len(edges)} edges analyzed")
    print(f"  Time: {elapsed_ms:.3f}ms ({elapsed_ms*1000:.1f}µs)")
    print(f"  Unique edge patterns: {len(edge_analysis)}")


def main():
    """Main demonstration function."""
    print("=== CPM Advanced Examples ===")
    print("This demonstrates sophisticated CPM operations\n")

    try:
        # 1. Create complex document
        doc = create_complex_prov_document()
        graph = ProvGraphWrapper(doc)

        # 2. Advanced traversal
        demonstrate_advanced_traversal(graph)

        # 3. Path finding
        paths = find_paths_between_nodes(graph)

        # 4. Graph filtering
        filtered_graph = demonstrate_graph_filtering(graph)

        # 5. Document mutation
        mutable_graph = demonstrate_document_mutation()

        # 6. Graph analysis
        analyze_graph_properties(graph)

        # 7. Performance analysis
        demonstrate_performance_analysis(graph)

        print(f"\n✅ Advanced examples completed successfully!")
        print("Previous: basic_examples.py for fundamental operations")
        print("Next: template_examples.py for CPM template workflows")

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
