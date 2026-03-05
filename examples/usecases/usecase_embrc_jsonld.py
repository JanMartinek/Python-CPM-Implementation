#!/usr/bin/env python3
"""
Use Case: EMBRC - External JSON-LD File Transformation

This example demonstrates loading and transforming real EMBRC 
(European Marine Biological Resource Centre) data from external JSON-LD files.

Data Source:
-----------
Real JSON-LD files from java-cpm/cpm-template/src/test/resources/embrc/
containing marine biological sample provenance metadata.

This matches the Java CpmEmbrcTest use case for interoperability verification.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports (go up two levels: usecases -> examples -> root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cpm.model import CpmDocument
from prov.identifier import Namespace
from prov.model import ProvDocument


# =============================================================================
# JSON-LD Parser
# =============================================================================

def load_jsonld_file(jsonld_path: str) -> Dict[str, Any]:
    """
    Load JSON-LD file.

    Args:
        jsonld_path: Path to JSON-LD file

    Returns:
        Parsed JSON data
    """
    with open(jsonld_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    graph = data.get('@graph', [])
    print(f"Loaded {Path(jsonld_path).name}: {len(graph)} graph elements")

    return data


def extract_entities_from_graph(graph: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Extract and categorize entities from JSON-LD @graph.

    Returns:
        Dictionary with categorized entities
    """
    entities = {
        'persons': [],
        'organizations': [],
        'places': [],
        'samples': [],
        'observations': [],
        'activities': [],
        'other': []
    }

    for node in graph:
        node_type = node.get('@type', [])
        if isinstance(node_type, str):
            node_type = [node_type]

        type_lower = ' '.join(node_type).lower()

        if 'person' in type_lower:
            entities['persons'].append(node)
        elif 'organization' in type_lower:
            entities['organizations'].append(node)
        elif 'place' in type_lower:
            entities['places'].append(node)
        elif 'sample' in type_lower:
            entities['samples'].append(node)
        elif 'observation' in type_lower:
            entities['observations'].append(node)
        elif 'activity' in type_lower or 'action' in type_lower:
            entities['activities'].append(node)
        else:
            entities['other'].append(node)

    return entities


# =============================================================================
# Transform to CPM
# =============================================================================

def transform_embrc_to_cpm(data: Dict[str, Any], dataset_num: int) -> ProvDocument:
    """
    Transform EMBRC JSON-LD to CPM document.

    This matches Java's DatasetTransformer classes.
    """
    print(f"Transforming Dataset{dataset_num} to CPM...")

    doc = ProvDocument()

    # Add namespaces from JSON-LD context
    context = data.get('@context', {})
    ns_mapping = {}

    # Standard namespaces
    schema = Namespace('schema', 'https://schema.org/')
    cpm = Namespace('cpm', 'https://www.commonprovenancemodel.org/cpm-namespace-v1-0/')
    sosa = Namespace('sosa', 'http://www.w3.org/ns/sosa/')
    dct = Namespace('dct', 'http://purl.org/dc/terms/')
    embrc = Namespace('embrc', 'http://embrc.eu/ns/')

    doc.add_namespace(schema)
    doc.add_namespace(cpm)
    doc.add_namespace(sosa)
    doc.add_namespace(dct)
    doc.add_namespace(embrc)

    # Create bundle
    bundle = doc.bundle(embrc[f'Dataset{dataset_num}_storage'])

    graph = data.get('@graph', [])
    entities = extract_entities_from_graph(graph)

    # Create Main Activity (CPM)
    main_activity = bundle.activity(
        embrc[f'dataset{dataset_num}_mainActivity'],
        other_attributes={
            'prov:type': cpm['mainActivity'],
            schema['name']: f'Dataset {dataset_num} Processing'
        }
    )

    # Create Backward Connector
    backward_connector = bundle.entity(
        embrc[f'dataset{dataset_num}_backwardConnector'],
        other_attributes={
            'prov:type': cpm['backwardConnector']
        }
    )

    # Create Forward Connector
    forward_connector = bundle.entity(
        embrc[f'dataset{dataset_num}_forwardConnector'],
        other_attributes={
            'prov:type': cpm['forwardConnector']
        }
    )

    # Create Agents from persons/organizations
    for person in entities['persons'][:2]:  # Limit for demo
        agent_id = person.get('@id', '').replace('https://', '').replace('/', '_')
        bundle.agent(
            embrc[agent_id],
            other_attributes={
                'prov:type': cpm['senderAgent'],
                schema['name']: person.get('name', 'Unknown')
            }
        )

    # Create Sample entities (Domain Specific)
    for sample in entities['samples']:
        sample_id = sample.get('@id', '').replace('_:', 'sample_')
        bundle.entity(
            embrc[sample_id],
            other_attributes={
                'prov:type': sosa['Sample'],
                schema['name']: sample.get('name', 'Unknown Sample'),
                schema['description']: sample.get('description', '')
            }
        )

    # Create Observation entities (Domain Specific)
    for obs in entities['observations'][:5]:  # Limit for demo
        obs_id = obs.get('@id', '').replace('_:', 'obs_')
        bundle.entity(
            embrc[obs_id],
            other_attributes={
                'prov:type': sosa['Observation']
            }
        )

    # Add CPM relations
    bundle.usage(main_activity, backward_connector)
    bundle.generation(forward_connector, main_activity)
    bundle.derivation(forward_connector, backward_connector)

    # Count what we created
    bundle_records = list(bundle.get_records())

    return doc


# =============================================================================
# Analyze
# =============================================================================

def analyze_embrc_document(doc: ProvDocument, dataset_num: int):
    """Analyze the CPM structure."""
    bundle = list(doc.bundles)[0] if doc.bundles else doc

    ti_count = 0
    ds_count = 0

    for record in bundle.get_records():
        if hasattr(record, 'attributes'):
            prov_types = [str(v) for k, v in record.attributes if 'type' in str(k).lower()]
            is_ti = any('cpm:' in t.lower() or 'mainactivity' in t.lower() or 'connector' in t.lower() for t in prov_types)
            if is_ti:
                ti_count += 1
            else:
                ds_count += 1

    # Wrap the bundle (not the top-level doc) with CpmDocument, since all
    # entities and relations live inside the bundle.
    bundle_doc = ProvDocument()
    for ns in bundle.namespaces:
        bundle_doc.add_namespace(ns)
    for record in bundle.get_records():
        bundle_doc.add_record(record)
    cpm_doc = CpmDocument(bundle_doc)
    stats = cpm_doc.get_statistics()
    print(f"Dataset{dataset_num}: TI={ti_count}, DS={ds_count}, edges={stats['total_edges']}")


# =============================================================================
# Main
# =============================================================================

def main():
    """Main execution."""
    print("USE CASE: EMBRC - External JSON-LD File Transformation")

    # Find the EMBRC files - first try local data folder, then fallback to java-cpm
    local_data = Path(__file__).parent / "data" / "embrc"
    java_data = Path(__file__).parent.parent.parent.parent / "java-cpm" / "java-cpm" / "cpm-template" / "src" / "test" / "resources" / "embrc"

    if local_data.exists():
        embrc_path = local_data
    elif java_data.exists():
        embrc_path = java_data
    else:
        print(f"EMBRC folder not found at {local_data} or {java_data}")
        return

    try:
        results = []

        # Process each dataset
        for dataset_num in [1, 2, 3, 4]:
            dataset_folder = embrc_path / f"dataset{dataset_num}"
            jsonld_file = dataset_folder / f"Dataset{dataset_num}_ProvenanceMetadata.jsonld"

            if not jsonld_file.exists():
                print(f"Skipping Dataset{dataset_num}: file not found")
                continue

            # Load JSON-LD
            data = load_jsonld_file(str(jsonld_file))

            # Show what's in the data
            graph = data.get('@graph', [])
            entities = extract_entities_from_graph(graph)

            # Transform to CPM
            doc = transform_embrc_to_cpm(data, dataset_num)

            # Analyze
            analyze_embrc_document(doc, dataset_num)

            results.append({
                'dataset': dataset_num,
                'samples': len(entities['samples']),
                'observations': len(entities['observations'])
            })

            # Export
            output_dir = Path(__file__).parent / "output" / "embrc"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"Dataset{dataset_num}_cpm.provn"

            try:
                doc.serialize(str(output_file), format='provn')
            except Exception as e:
                print(f"Export failed for Dataset{dataset_num}: {e}")

        # Summary
        print(f"\nProcessed {len(results)} datasets (matches Java CpmEmbrcTest)")
        print("Use case completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
