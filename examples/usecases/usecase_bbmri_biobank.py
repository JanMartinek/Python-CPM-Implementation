#!/usr/bin/env python3
"""
Use Case: BBMRI Biobank Data Transformation to CPM

This example demonstrates the transformation of real-world biobank data
from the BBMRI-ERIC (Biobanking and BioMolecular resources Research Infrastructure)
into the Common Provenance Model (CPM) representation.

Use Case Context:
-----------------
BBMRI biobanks track biological samples (tissue, blood, etc.) through their lifecycle:
1. ACQUISITION - Sample is taken from a patient
2. STORAGE - Sample is transported and stored in the biobank
3. DISTRIBUTION - Sample may be shared with researchers

This use case shows how existing biobank data (from CSV/database records)
can be transformed into CPM representation using the Python CPM library.

Data Source:
-----------
Based on real BBMRI data structures from the MMCI (Masaryk Memorial Cancer Institute) 
biobank, part of the Java CPM implementation test data.

Requirements Addressed:
----------------------
- Transform information from existing formats into CPM (Thesis Requirement #6)
- Support retrieving specific parts of generated provenance (Requirement #3)
- Demonstrate interoperability with Java implementation data (Requirement #5)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Add project root to path for imports (go up two levels: usecases -> examples -> root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from prov.model import ProvDocument
from prov.identifier import Namespace
from src.graph.wrapper import ProvGraphWrapper
from src.cpm.model import CpmDocument
from src.cpm.constants import *


# =============================================================================
# SECTION 1: Raw Data Structures (Simulating CSV/Database Records)
# =============================================================================

@dataclass
class PatientRecord:
    """Represents a patient record from hospital database."""
    patient_id: str
    sex: str
    birth_year: int
    gave_consent: bool


@dataclass
class SampleRecord:
    """Represents a biological sample record from biobank database."""
    sample_id: str
    patient_id: str
    material_type: str  # S=Serum, P=Plasma, T=Tissue
    storage_type: str   # STS=Standard Storage, LTS=Long Term Storage
    diagnosis: str      # ICD-10 code
    taking_date: datetime
    hospital_id: str


@dataclass
class StorageRecord:
    """Represents storage operation from biobank log."""
    storage_id: str
    sample_id: str
    storage_location: str
    stored_at: datetime
    operator_id: str


def load_raw_biobank_data() -> tuple:
    """
    Simulate loading raw biobank data from CSV/database.

    In a real scenario, this would read from:
    - Hospital database (patient records)
    - Laboratory Information System (sample records)
    - Biobank storage logs

    Returns:
        Tuple of (patients, samples, storage_records)
    """
    # Patient data (from hospital database)
    patients = [
        PatientRecord(
            patient_id="33",
            sex="female",
            birth_year=1999,
            gave_consent=True
        )
    ]

    # Sample data (from laboratory system)
    samples = [
        SampleRecord(
            sample_id="BBM:2032:136043",
            patient_id="33",
            material_type="S",  # Serum
            storage_type="STS",  # Standard Storage
            diagnosis="C509",   # Breast cancer, unspecified
            taking_date=datetime(2032, 10, 4, 10, 2, 0),
            hospital_id="UNI"
        )
    ]

    # Storage operation logs
    storage_records = [
        StorageRecord(
            storage_id="storage-33-BBM:2032:136043",
            sample_id="BBM:2032:136043",
            storage_location="Freezer-A-42",
            stored_at=datetime(2032, 10, 4, 14, 30, 0),
            operator_id="OP-001"
        )
    ]

    print(f"Loaded {len(patients)} patient(s), {len(samples)} sample(s), {len(storage_records)} storage record(s)")

    return patients, samples, storage_records


# =============================================================================
# SECTION 2: Transform to PROV Document
# =============================================================================

def transform_to_prov(patients: List[PatientRecord],
                      samples: List[SampleRecord],
                      storage_records: List[StorageRecord]) -> ProvDocument:
    """
    Transform raw biobank records into PROV document.

    This is the KEY TRANSFORMATION step - converting from
    existing format (database records) to standardized PROV/CPM.

    Args:
        patients: Patient records
        samples: Sample records
        storage_records: Storage operation records

    Returns:
        ProvDocument with CPM structure
    """
    doc = ProvDocument()

    # Define namespaces (matching Java implementation)
    bbmri = Namespace('bbmri', 'http://www.bbmri.cz/schemas/biobank/data#')
    cpm = Namespace('cpm', 'https://www.commonprovenancemodel.org/cpm-namespace-v1-0/')
    pbm = Namespace('pbm', 'http://commonprovenancemodel.org/ns/pbm/')
    dct = Namespace('dct', 'http://purl.org/dc/terms/')

    doc.add_namespace(bbmri)
    doc.add_namespace(cpm)
    doc.add_namespace(pbm)
    doc.add_namespace(dct)

    # Create bundle for this storage operation
    bundle = doc.bundle(bbmri['storageBundle-33-BBM-2032-136043'])

    # Process each sample
    for sample in samples:
        patient = next((p for p in patients if p.patient_id == sample.patient_id), None)
        storage = next((s for s in storage_records if s.sample_id == sample.sample_id), None)

        # ===== MAIN ACTIVITY (CPM requirement) =====
        main_activity = bundle.activity(
            bbmri[f'storage-{sample.patient_id}-{sample.sample_id.replace(":", "-")}'],
            other_attributes={
                'prov:type': cpm['mainActivity'],
                dct['hasPart']: bbmri[f'transport-{sample.patient_id}-{sample.sample_id.replace(":", "-")}'],
            }
        )

        # ===== BACKWARD CONNECTOR (link to previous bundle) =====
        backward_connector = bundle.entity(
            bbmri[f'sampleAcqConnector-{sample.patient_id}-{sample.sample_id.replace(":", "-")}'],
            other_attributes={
                'prov:type': cpm['backwardConnector'],
                cpm['referencedBundleId']: bbmri[f'acquisitionBundle-{sample.patient_id}-{sample.sample_id.replace(":", "-")}']
            }
        )

        # ===== FORWARD CONNECTOR (link to next bundle) =====
        forward_connector = bundle.entity(
            bbmri[f'sampleStorConnector-{sample.patient_id}-{sample.sample_id.replace(":", "-")}'],
            other_attributes={
                'prov:type': cpm['forwardConnector']
            }
        )

        # ===== SENDER AGENT =====
        sender_agent = bundle.agent(
            bbmri[sample.hospital_id],
            other_attributes={
                'prov:type': cpm['senderAgent']
            }
        )

        # ===== CPM RELATIONS =====
        bundle.usage(main_activity, backward_connector)
        bundle.generation(forward_connector, main_activity)
        bundle.attribution(backward_connector, sender_agent)
        bundle.derivation(forward_connector, backward_connector)

        # ===== DOMAIN-SPECIFIC: Transport Activity =====
        transport_activity = bundle.activity(
            bbmri[f'transport-{sample.patient_id}-{sample.sample_id.replace(":", "-")}'],
            other_attributes={
                'prov:type': pbm['transportActivity']
            }
        )

        # ===== DOMAIN-SPECIFIC: Sample Entity =====
        sample_entity = bundle.entity(
            bbmri[f'sampleTrans-{sample.patient_id}-{sample.sample_id.replace(":", "-")}'],
            other_attributes={
                'prov:type': pbm['sample'],
                bbmri['sampleId']: sample.sample_id
            }
        )
        bundle.generation(sample_entity, transport_activity)
        bundle.specialization(sample_entity, backward_connector)

        # ===== DOMAIN-SPECIFIC: Storage Activity =====
        storage_activity = bundle.activity(
            bbmri[f'storageAct-{sample.patient_id}-{sample.sample_id.replace(":", "-")}'],
            other_attributes={
                'prov:type': pbm['storageActivity']
            }
        )
        bundle.usage(storage_activity, sample_entity)

        # ===== DOMAIN-SPECIFIC: Stored Sample Entity =====
        stored_sample = bundle.entity(
            bbmri[f'sampleStorage-{sample.patient_id}-{sample.sample_id.replace(":", "-")}'],
            other_attributes={
                'prov:type': pbm['sample'],
                'prov:type': bbmri['diagnosticMaterial'],
                bbmri['sampleId']: sample.sample_id,
                bbmri['storageType']: sample.storage_type,
                bbmri['materialType']: sample.material_type,
                bbmri['diagnosis']: sample.diagnosis,
                bbmri['takingDate']: sample.taking_date.isoformat() + 'Z'
            }
        )
        bundle.generation(stored_sample, storage_activity)
        bundle.specialization(stored_sample, forward_connector)

        # ===== DOMAIN-SPECIFIC: Patient/Source Entity =====
        if patient:
            patient_entity = bundle.entity(
                bbmri[f'patient-{patient.patient_id}'],
                other_attributes={
                    'prov:type': pbm['source'],
                    bbmri['sex']: patient.sex,
                    bbmri['birthYear']: str(patient.birth_year),
                    bbmri['gaveConsent']: str(patient.gave_consent).lower()
                }
            )
            bundle.derivation(sample_entity, patient_entity)
            bundle.derivation(stored_sample, patient_entity)

    return doc


# =============================================================================
# SECTION 3: Wrap with CPM and Analyze
# =============================================================================

def analyze_cpm_document(cpm_doc: CpmDocument, prov_doc: ProvDocument):
    """
    Analyze the CPM structure of the transformed document.

    This demonstrates:
    - Identifying CPM components (main activity, connectors)
    - TI/DS separation
    - Querying provenance information
    """
    # Get statistics
    stats = cpm_doc.get_statistics()
    print(f"Total nodes: {stats.get('total_nodes', 0)}, Total edges: {stats.get('total_edges', 0)}")

    # Direct analysis from bundle (more reliable for this use case)
    bundle = list(prov_doc.bundles)[0] if prov_doc.bundles else prov_doc

    main_activity = None
    backward_connectors = []
    forward_connectors = []
    ti_nodes = []
    ds_nodes = []

    for record in bundle.get_records():
        if hasattr(record, 'attributes'):
            prov_types = [str(v) for k, v in record.attributes if 'type' in str(k).lower()]

            is_ti = False
            for ptype in prov_types:
                ptype_lower = ptype.lower()
                if 'mainactivity' in ptype_lower:
                    main_activity = record
                    is_ti = True
                elif 'backwardconnector' in ptype_lower:
                    backward_connectors.append(record)
                    is_ti = True
                elif 'forwardconnector' in ptype_lower:
                    forward_connectors.append(record)
                    is_ti = True
                elif 'senderagent' in ptype_lower or 'receiveragent' in ptype_lower:
                    is_ti = True

            if is_ti:
                ti_nodes.append(record)
            else:
                ds_nodes.append(record)

    if main_activity:
        print(f"Main Activity: {main_activity.identifier}")

    print(f"Backward Connectors: {len(backward_connectors)}, Forward Connectors: {len(forward_connectors)}")
    print(f"TI nodes: {len(ti_nodes)}, DS nodes: {len(ds_nodes)}")


# =============================================================================
# SECTION 4: Query Domain-Specific Information
# =============================================================================

def query_sample_information(cpm_doc: CpmDocument):
    """
    Query domain-specific sample information from the CPM document.

    This demonstrates Requirement #3: retrieving specific parts of provenance.
    """
    sample_count = 0
    source_count = 0
    for node in cpm_doc.graph_wrapper.get_nodes():
        prov_types = node.get_prov_attribute('prov:type')
        if any('sample' in str(t).lower() for t in prov_types):
            sample_count += 1
        if any('source' in str(t).lower() for t in prov_types):
            source_count += 1

    print(f"Found {sample_count} sample record(s) and {source_count} patient/source record(s)")


# =============================================================================
# SECTION 5: Export and Verify
# =============================================================================

def export_and_verify(cpm_doc: CpmDocument, output_dir: Path):
    """
    Export the CPM document and verify the transformation.
    """
    output_dir.mkdir(exist_ok=True)
    prov_doc = cpm_doc.graph_wrapper.to_prov_document()

    # Export to PROV-N
    try:
        provn_path = output_dir / "bbmri_storage_transformed.provn"
        prov_doc.serialize(str(provn_path), format='provn')
        print(f"Exported PROV-N: {provn_path.name}")
    except Exception as e:
        print(f"PROV-N export failed: {e}")

    # Export to JSON
    try:
        json_path = output_dir / "bbmri_storage_transformed.json"
        prov_doc.serialize(str(json_path), format='json')
        print(f"Exported JSON: {json_path.name}")
    except Exception as e:
        print(f"JSON export failed: {e}")


# =============================================================================
# SECTION 6: Summary
# =============================================================================

def print_summary():
    """Print summary of the use case demonstration."""
    print("\nSummary: BBMRI Biobank Use Case")
    print("  Transformation pipeline: load raw data -> PROV/CPM -> analyze -> export")
    print("  Requirements addressed: #3 (retrieve provenance), #5 (Java interop), #6 (transform to CPM)")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution of the BBMRI Biobank use case."""
    print("USE CASE: BBMRI Biobank Data Transformation to CPM")

    try:
        # Section 1: Load raw data
        patients, samples, storage_records = load_raw_biobank_data()

        # Section 2: Transform to PROV
        prov_doc = transform_to_prov(patients, samples, storage_records)

        # Section 3: Wrap with CPM
        cpm_doc = CpmDocument(prov_doc)
        analyze_cpm_document(cpm_doc, prov_doc)

        # Section 4: Query domain-specific
        query_sample_information(cpm_doc)

        # Section 5: Export
        output_dir = Path(__file__).parent / "output"
        export_and_verify(cpm_doc, output_dir)

        # Section 6: Summary
        print_summary()

        print("\nUse case completed successfully.")

    except Exception as e:
        print(f"\nError during use case execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
