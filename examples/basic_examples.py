#!/usr/bin/env python3
"""
Basic CPM Examples

This file demonstrates fundamental operations of the Common Provenance Model (CPM) 
Python implementation, including:

1. Basic PROV document creation and manipulation
2. Graph wrapper usage for entity-activity relationships
3. Simple graph analysis and visualization
4. Export functionality to different formats
5. Import/export round-trip operations

This covers the core functionality needed for most CPM applications.
"""

import sys
import os
import json
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from prov.model import ProvDocument
from src.graph.wrapper import ProvGraphWrapper
from src.adapters.prov_adapter import ProvAdapter


def create_basic_prov_document() -> ProvDocument:
    """Create a basic PROV document with a simple data processing workflow."""
    print("Creating basic PROV document...")
    
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/')
    
    # Create entities (data items)
    input_data = doc.entity('ex:input_data', {
        'prov:label': 'Input Dataset',
        'prov:type': 'Dataset',
        'ex:size': '1.2GB'
    })
    
    processed_data = doc.entity('ex:processed_data', {
        'prov:label': 'Processed Dataset', 
        'prov:type': 'Dataset'
    })
    
    results = doc.entity('ex:results', {
        'prov:label': 'Analysis Results',
        'prov:type': 'Report'
    })
    
    # Create activities (processing steps)
    processing = doc.activity('ex:data_processing', '2024-01-01T10:00:00Z', '2024-01-01T11:30:00Z', {
        'prov:label': 'Data Processing'
    })
    
    analysis = doc.activity('ex:data_analysis', '2024-01-01T12:00:00Z', '2024-01-01T14:00:00Z', {
        'prov:label': 'Data Analysis'
    })
    
    # Create agent
    scientist = doc.agent('ex:data_scientist', {
        'prov:label': 'Data Scientist',
        'prov:type': 'Person'
    })
    
    # Establish relationships
    doc.usage(processing, input_data, '2024-01-01T10:05:00Z')
    doc.generation(processed_data, processing, '2024-01-01T11:25:00Z')
    
    doc.usage(analysis, processed_data, '2024-01-01T12:05:00Z') 
    doc.generation(results, analysis, '2024-01-01T13:55:00Z')
    
    # Associate activities with agents
    doc.association(processing, scientist)
    doc.association(analysis, scientist)
    
    print(f"✓ Created PROV document with {len(list(doc.get_records()))} records")
    return doc


def demonstrate_graph_wrapper(doc: ProvDocument) -> ProvGraphWrapper:
    """Convert PROV document to graph and demonstrate basic operations."""
    print("\nDemonstrating graph wrapper functionality...")
    
    # Convert to graph representation
    graph = ProvGraphWrapper(doc)
    
    print(f"✓ Created graph with {len(graph)} nodes and {len(graph.get_edges())} edges")
    
    # Display nodes (entities)
    print("\nGraph nodes (entities):")
    for i, node in enumerate(graph.get_nodes(), 1):
        # Get attributes from the PROV entity - attributes is a list of tuples
        entity_type = 'Unknown'
        label = str(node.identifier)
        
        for attr_name, attr_value in node.prov_entity.attributes:
            if str(attr_name) == 'prov:type':
                entity_type = str(attr_value)
            elif str(attr_name) == 'prov:label':
                label = str(attr_value)
        
        print(f"  {i}. {node.identifier} ({entity_type}) - {label}")
    
    # Display edges (activities connecting entities)
    print("\nGraph edges (activities):")
    for i, edge in enumerate(graph.get_edges(), 1):
        cause_id = edge.cause.identifier
        effect_id = edge.effect.identifier
        print(f"  {i}. {cause_id} --[{edge.kind}]--> {effect_id}")
    
    # Demonstrate node connectivity
    print("\nNode connectivity analysis:")
    for node in graph.get_nodes():
        connected_nodes = node.get_connected_nodes()
        if connected_nodes:
            connected_ids = [n.identifier for n in connected_nodes]
            print(f"  {node.identifier} is connected to: {connected_ids}")
    
    return graph


def demonstrate_graph_analysis(graph: ProvGraphWrapper):
    """Demonstrate various graph analysis operations."""
    print("\nPerforming graph analysis...")
    
    # Find nodes by type
    nodes = list(graph.get_nodes())
    if nodes:
        sample_node = nodes[0]
        
        # Get edges by relation type
        usage_edges = sample_node.get_edges_by_relation_type('PROV_USAGE')
        generation_edges = sample_node.get_edges_by_relation_type('PROV_GENERATION')
        
        print(f"  {sample_node.identifier} has {len(usage_edges)} usage edges")
        print(f"  {sample_node.identifier} has {len(generation_edges)} generation edges")
        
        # Get all edges for this node
        all_edges = sample_node.all_edges
        print(f"  {sample_node.identifier} has {len(all_edges)} total edges")
    
    # Analyze graph structure
    print(f"\nGraph structure summary:")
    print(f"  - Total nodes: {len(graph)}")
    print(f"  - Total edges: {len(graph.get_edges())}")
    print(f"  - Graph density: {len(graph.get_edges()) / len(graph) if len(graph) > 0 else 0:.2f} edges/node")


def demonstrate_export_import(doc: ProvDocument):
    """Demonstrate export and import functionality."""
    print("\nDemonstrating export/import functionality...")
    
    try:
        # Use the adapter for export/import operations
        adapter = ProvAdapter()
        graph = ProvGraphWrapper(doc)
        
        # Export to different formats
        print("Exporting to different formats:")
        
        # Export to JSON-LD (most reliable format)
        try:
            json_export = adapter.export_to_formats(graph, ['json'])
            if json_export and 'json' in json_export:
                print(f"  ✓ JSON-LD export: {len(json_export['json'])} characters")
                
                # Test round-trip: import the exported JSON
                imported_graph = adapter.import_from_formats(json_export['json'], 'json')
                if imported_graph:
                    print(f"  ✓ JSON-LD round-trip successful: {len(imported_graph)} nodes")
                else:
                    print("  ✗ JSON-LD import failed")
            else:
                print("  ✗ JSON-LD export failed")
        except Exception as e:
            print(f"  ✗ JSON-LD export/import failed: {e}")
        
        # Try PROVN format if available
        try:
            provn_export = adapter.export_to_formats(graph, ['provn'])
            if provn_export and 'provn' in provn_export:
                print(f"  ✓ PROV-N export: {len(provn_export['provn'])} characters")
            else:
                print("  ⚠ PROV-N export not available or failed")
        except Exception as e:
            print(f"  ⚠ PROV-N export failed: {e}")
    
    except Exception as e:
        print(f"  ✗ Adapter operations failed: {e}")


def demonstrate_error_handling():
    """Demonstrate error handling for common issues."""
    print("\nDemonstrating error handling...")
    
    # Test with invalid document
    try:
        empty_doc = ProvDocument()
        graph = ProvGraphWrapper(empty_doc)
        print(f"  ✓ Empty document handling: {len(graph)} nodes")
    except Exception as e:
        print(f"  ✗ Empty document failed: {e}")
    
    # Test module imports
    try:
        from src.cpm.template import CpmBundleTemplate
        print("  ✓ CPM Template module available")
    except ImportError:
        print("  ⚠ CPM Template module not available")
    
    try:
        from src.cpm.validation import CpmValidator
        print("  ✓ CPM Validation module available")
    except ImportError:
        print("  ⚠ CPM Validation module not available")


def main():
    """Main demonstration function."""
    print("=== CPM Basic Examples ===")
    print("This demonstrates fundamental CPM operations\n")
    
    try:
        # 1. Basic PROV document creation
        doc = create_basic_prov_document()
        
        # 2. Graph wrapper operations
        graph = demonstrate_graph_wrapper(doc)
        
        # 3. Graph analysis
        demonstrate_graph_analysis(graph)
        
        # 4. Export/import functionality
        demonstrate_export_import(doc)
        
        # 5. Error handling
        demonstrate_error_handling()
        

    except Exception as e:
        print(f"\n Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())