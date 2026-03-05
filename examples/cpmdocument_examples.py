#!/usr/bin/env python3
"""
CPM Document Usage Examples

This file demonstrates complete usage of the CpmDocument class including:
1. Creating a CPM document from scratch
2. Adding nodes (entities, activities, agents)
3. Creating relationships between nodes
4. Querying and traversing the graph
5. Modifying the document
6. Exporting to various formats

Author: Example
Date: December 2025
"""

import sys
import os
from typing import List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from prov.model import ProvDocument
from src.cpm.model import CpmDocument
from src.graph.node import GraphNode
from src.graph.factory import DividedCpmFactory


def example_1_creating_cpm_document():
    """Example 1: Create a CPM document from scratch"""
    print("=" * 60)
    print("Example 1: Creating CPM Document from Scratch")
    print("=" * 60)
    
    # Create base PROV document
    prov_doc = ProvDocument()
    prov_doc.add_namespace('ex', 'http://example.org/')
    prov_doc.add_namespace('data', 'http://data.example.org/')
    
    # Create a bundle for CPM
    bundle = prov_doc.bundle('ex:cpm_bundle')
    
    # Add entities (data)
    raw_data = bundle.entity('data:raw_dataset', {
        'prov:type': 'Dataset',
        'prov:label': 'Raw Sensor Data',
        'ex:size': '1.2GB',
        'ex:format': 'CSV'
    })
    
    processed_data = bundle.entity('data:processed_dataset', {
        'prov:type': 'Dataset',
        'prov:label': 'Cleaned Data',
        'ex:size': '800MB',
        'ex:format': 'Parquet'
    })
    
    # Add activity (processing)
    cleaning = bundle.activity('ex:data_cleaning', 
                               '2024-01-15T09:00:00',
                               '2024-01-15T10:30:00')
    
    # Add agent (who did it)
    data_engineer = bundle.agent('ex:john_doe', {
        'prov:type': 'Person',
        'prov:label': 'John Doe',
        'ex:role': 'Data Engineer'
    })
    
    # Create relationships
    bundle.usage(cleaning, raw_data)  # Activity used entity
    bundle.generation(processed_data, cleaning)  # Activity generated entity
    bundle.association(cleaning, data_engineer)  # Agent performed activity
    bundle.derivation(processed_data, raw_data)  # Data derived from other data
    
    # Create CPM document from PROV
    cpm_doc = CpmDocument(prov_doc)
    
    print(f"✓ Created CPM document")
    print(f"  Nodes: {len(cpm_doc.get_all_nodes())}")
    print(f"  Edges: {len(cpm_doc.get_all_edges())}")
    print(f"  Bundle ID: {cpm_doc.get_bundle_id()}")
    
    return cpm_doc


def example_2_querying_nodes(cpm_doc: CpmDocument):
    """Example 2: Query nodes in various ways"""
    print("\n" + "=" * 60)
    print("Example 2: Querying Nodes")
    print("=" * 60)
    
    # Get all nodes
    all_nodes = cpm_doc.get_all_nodes()
    print(f"\n1. All nodes ({len(all_nodes)}):")
    for node in all_nodes:
        node_type = type(node.prov_entity).__name__
        print(f"   - {node.identifier} ({node_type})")
    
    # Get specific node
    node = cpm_doc.get_node('data:raw_dataset')
    if node:
        print(f"\n2. Specific node: {node.identifier}")
        print(f"   Type: {type(node.prov_entity).__name__}")
        print(f"   Attributes:")
        for attr_name, attr_value in node.prov_entity.attributes:
            print(f"     - {attr_name}: {attr_value}")
    
    # Get nodes by type
    entities = cpm_doc.get_nodes_by_type('prov:Entity')
    print(f"\n3. Entities found: {len(entities)}")
    for entity in entities:
        print(f"   - {entity.identifier}")
    
    # Get nodes by attribute
    datasets = cpm_doc.get_nodes_by_attribute('prov:type', 'Dataset')
    print(f"\n4. Datasets (by attribute): {len(datasets)}")
    for dataset in datasets:
        label = dataset.get_prov_attribute('prov:label')
        print(f"   - {dataset.identifier}: {label[0] if label else 'No label'}")


def example_3_querying_edges(cpm_doc: CpmDocument):
    """Example 3: Query relationships/edges"""
    print("\n" + "=" * 60)
    print("Example 3: Querying Edges/Relations")
    print("=" * 60)
    
    # Get all edges
    all_edges = cpm_doc.get_all_edges()
    print(f"\n1. All edges: {len(all_edges)}")
    for edge in all_edges:
        edge_type = type(edge).__name__
        print(f"   - {edge_type}")
    
    # Get edges from specific node
    edges_from_cleaning = cpm_doc.get_edges(source_id='ex:data_cleaning')
    print(f"\n2. Edges from 'ex:data_cleaning': {len(edges_from_cleaning)}")
    for edge in edges_from_cleaning:
        print(f"   - {type(edge).__name__}")
    
    # Get edges to specific node
    edges_to_processed = cpm_doc.get_edges(target_id='data:processed_dataset')
    print(f"\n3. Edges to 'data:processed_dataset': {len(edges_to_processed)}")
    for edge in edges_to_processed:
        print(f"   - {type(edge).__name__}")
    
    # Get specific edge type
    derivations = cpm_doc.get_edges(relation_type='derivation')
    print(f"\n4. Derivation edges: {len(derivations)}")
    for deriv in derivations:
        source, target = cpm_doc._extract_edge_endpoints(deriv)
        print(f"   - {target} ← derived from ← {source}")


def example_4_graph_traversal(cpm_doc: CpmDocument):
    """Example 4: Graph traversal operations"""
    print("\n" + "=" * 60)
    print("Example 4: Graph Traversal")
    print("=" * 60)
    
    # Get a starting node
    start_node = cpm_doc.get_node('data:raw_dataset')
    if not start_node:
        print("Node not found!")
        return
    
    print(f"\n1. Starting from: {start_node.identifier}")
    
    # Get connected nodes
    connected = start_node.get_connected_nodes()
    print(f"\n2. Directly connected nodes: {len(connected)}")
    for node in connected:
        print(f"   - {node.identifier}")
    
    # Get all edges for this node
    all_edges = start_node.all_edges
    print(f"\n3. All edges: {len(all_edges)}")
    for edge in all_edges:
        print(f"   - {edge.kind} ({edge.cause.identifier} → {edge.effect.identifier})")


def example_5_modifying_document(cpm_doc: CpmDocument):
    """Example 5: Modify the CPM document"""
    print("\n" + "=" * 60)
    print("Example 5: Modifying CPM Document")
    print("=" * 60)
    
    # Add new node
    print("\n1. Adding new entity...")
    try:
        new_node = cpm_doc.add_node(
            node_type='entity',
            identifier='data:final_report',
            attributes={
                'prov:label': 'Final Analysis Report',
                'ex:format': 'PDF'
            },
            prov_type='Report'
        )
        print(f"   ✓ Added: {new_node.identifier}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Add new relationship
    print("\n2. Adding new relationship...")
    try:
        edge = cpm_doc.add_edge(
            relation_type='wasderivedfrom',
            source_id='data:processed_dataset',
            target_id='data:final_report'
        )
        print(f"   ✓ Added derivation edge")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Update node attributes
    print("\n3. Current state:")
    print(f"   Nodes: {len(cpm_doc.get_all_nodes())}")
    print(f"   Edges: {len(cpm_doc.get_all_edges())}")
    
    # Check if modified
    print(f"   Modified: {cpm_doc.is_modified()}")


def example_6_filtering_and_analysis(cpm_doc: CpmDocument):
    """Example 6: Filtering and analysis"""
    print("\n" + "=" * 60)
    print("Example 6: Filtering and Analysis")
    print("=" * 60)
    
    # Get graph wrapper
    graph = cpm_doc.to_graph_wrapper()
    
    # Filter nodes by type
    def is_dataset(node: GraphNode) -> bool:
        types = node.get_prov_attribute('prov:type')
        if types:
            return 'Dataset' in [str(t) for t in types]
        return False
    
    print("\n1. Filtering datasets...")
    all_nodes = graph.get_nodes()
    datasets = [node for node in all_nodes if is_dataset(node)]
    print(f"   Found {len(datasets)} datasets:")
    for ds in datasets:
        print(f"   - {ds.identifier}")
    
    # Analyze connectivity
    print("\n2. Node connectivity analysis:")
    for node in datasets:
        degree = len(node.all_edges)
        connected = node.get_connected_nodes()
        print(f"   {node.identifier}:")
        print(f"     Total edges: {degree}")
        print(f"     Connected nodes: {len(connected)}")


def example_7_export_formats(cpm_doc: CpmDocument):
    """Example 7: Export to various formats"""
    print("\n" + "=" * 60)
    print("Example 7: Export Formats")
    print("=" * 60)
    
    # Export to PROV document
    prov_doc = cpm_doc.to_prov_document()
    print(f"\n1. PROV Document:")
    print(f"   Records: {len(list(prov_doc.get_records()))}")
    print(f"   Namespaces: {len(prov_doc.namespaces)}")
    
    # Export to JSON
    try:
        json_str = prov_doc.serialize(format='json', indent=2)
        if json_str:
            print(f"\n2. JSON format:")
            print(f"   Size: {len(json_str)} characters")
            print(f"   First 200 chars:")
            print(f"   {json_str[:800]}...")
    except Exception as e:
        print(f"   Error serializing to JSON: {e}")
    
    # Get namespaces
    namespaces = cpm_doc.get_namespaces()
    print(f"\n3. Namespaces:")
    for prefix, uri in namespaces.items():
        print(f"   {prefix}: {uri}")


def example_8_complex_workflow():
    """Example 8: Complete data processing workflow"""
    print("\n" + "=" * 60)
    print("Example 8: Complete Data Processing Workflow")
    print("=" * 60)
    
    # Create PROV document
    prov_doc = ProvDocument()
    prov_doc.add_namespace('wf', 'http://workflow.example.org/')
    prov_doc.add_namespace('data', 'http://data.example.org/')
    
    bundle = prov_doc.bundle('wf:data_pipeline')
    
    # Create CPM document
    cpm_doc = CpmDocument(prov_doc)
    
    print("\n1. Creating data pipeline workflow...")
    
    # Stage 1: Data Collection
    sensor1 = cpm_doc.add_node('entity', 'data:sensor_1', 
                               {'prov:type': 'Dataset', 'prov:label': 'Temperature Sensor'})
    sensor2 = cpm_doc.add_node('entity', 'data:sensor_2',
                               {'prov:type': 'Dataset', 'prov:label': 'Humidity Sensor'})
    
    collection = cpm_doc.add_node('activity', 'wf:data_collection')
    collector_agent = cpm_doc.add_node('agent', 'wf:iot_system',
                                       {'prov:type': 'SoftwareAgent'})
    
    cpm_doc.add_edge('wasgeneratedby', 'wf:data_collection', 'data:sensor_1')
    cpm_doc.add_edge('wasgeneratedby', 'wf:data_collection', 'data:sensor_2')
    cpm_doc.add_edge('wasassociatedwith', 'wf:iot_system', 'wf:data_collection')
    
    # Stage 2: Data Processing
    cleaned = cpm_doc.add_node('entity', 'data:cleaned_data',
                               {'prov:type': 'Dataset', 'prov:label': 'Cleaned Data'})
    processing = cpm_doc.add_node('activity', 'wf:data_processing')
    processor = cpm_doc.add_node('agent', 'wf:etl_system',
                                {'prov:type': 'SoftwareAgent'})
    
    cpm_doc.add_edge('used', 'wf:data_processing', 'data:sensor_1')
    cpm_doc.add_edge('used', 'wf:data_processing', 'data:sensor_2')
    cpm_doc.add_edge('wasgeneratedby', 'wf:data_processing', 'data:cleaned_data')
    cpm_doc.add_edge('wasassociatedwith', 'wf:etl_system', 'wf:data_processing')
    cpm_doc.add_edge('wasderivedfrom', 'data:sensor_1', 'data:cleaned_data')
    
    # Stage 3: Analysis
    results = cpm_doc.add_node('entity', 'data:analysis_results',
                              {'prov:type': 'Report', 'prov:label': 'Analysis Results'})
    analysis = cpm_doc.add_node('activity', 'wf:statistical_analysis')
    analyst = cpm_doc.add_node('agent', 'wf:analyst',
                               {'prov:type': 'Person', 'prov:label': 'Data Analyst'})
    
    cpm_doc.add_edge('used', 'wf:statistical_analysis', 'data:cleaned_data')
    cpm_doc.add_edge('wasgeneratedby', 'wf:statistical_analysis', 'data:analysis_results')
    cpm_doc.add_edge('wasassociatedwith', 'wf:analyst', 'wf:statistical_analysis')
    cpm_doc.add_edge('wasderivedfrom', 'data:cleaned_data', 'data:analysis_results')
    
    print("   ✓ Workflow created")
    print(f"   Total nodes: {len(cpm_doc.get_all_nodes())}")
    print(f"   Total edges: {len(cpm_doc.get_all_edges())}")
    
    # Analyze workflow
    print("\n2. Workflow analysis:")
    entities = cpm_doc.get_nodes_by_type('prov:Entity')
    activities = cpm_doc.get_nodes_by_type('prov:Activity')
    agents = cpm_doc.get_nodes_by_type('prov:Agent')
    
    print(f"   Entities: {len(entities)}")
    print(f"   Activities: {len(activities)}")
    print(f"   Agents: {len(agents)}")
    
    # Show data lineage
    print("\n3. Data lineage for 'data:analysis_results':")
    result_node = cpm_doc.get_node('data:analysis_results')
    if result_node:
        print(f"   Starting from: {result_node.identifier}")
        
        # Trace back through derivations
        def trace_lineage(node: GraphNode, depth: int = 0):
            indent = "     " * depth
            print(f"{indent}└─ {node.identifier}")
            
            # Find what this was derived from
            derivations = cpm_doc.get_edges(target_id=node.identifier, relation_type='derivation')
            for deriv in derivations:
                source, _ = cpm_doc._extract_edge_endpoints(deriv)
                if source:
                    source_node = cpm_doc.get_node(source)
                    if source_node and depth < 3:  # Prevent infinite recursion
                        trace_lineage(source_node, depth + 1)
        
        trace_lineage(result_node)
    
    return cpm_doc


def main():
    """Main function to run all examples"""
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "CPM DOCUMENT USAGE EXAMPLES" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # Run examples
        cpm_doc = example_1_creating_cpm_document()
        example_2_querying_nodes(cpm_doc)
        example_3_querying_edges(cpm_doc)
        example_4_graph_traversal(cpm_doc)
        example_5_modifying_document(cpm_doc)
        example_6_filtering_and_analysis(cpm_doc)
        example_7_export_formats(cpm_doc)
        example_8_complex_workflow()
        
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
