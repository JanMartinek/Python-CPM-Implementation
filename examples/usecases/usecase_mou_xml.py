#!/usr/bin/env python3
"""
Use Case: MOU/BBMRI Biobank - External XML File Transformation

This example demonstrates loading and transforming real BBMRI biobank data
from external XML files (same format as Java implementation).

Data Source:
-----------
Real XML file from java-cpm/cpm-template/src/test/resources/mou/test-data.xml
containing patient and sample records from MOU (Masaryk Oncology Institute).

This matches the Java CpmMouTest use case for interoperability verification.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add project root to path for imports (go up two levels: usecases -> examples -> root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cpm.model import CpmDocument
from prov.identifier import Namespace
from prov.model import ProvDocument


# =============================================================================
# Data Classes (matching XML structure)
# =============================================================================

@dataclass
class TissueSample:
    """LTS (Long Term Storage) tissue sample from XML."""
    sample_id: str
    number: str
    year: str
    samples_no: int
    available_samples_no: int
    material_type: str
    ptnm: str
    morphology: str
    diagnosis: str
    cut_time: Optional[datetime]
    freeze_time: Optional[datetime]
    retrieved: str


@dataclass
class DiagnosisMaterial:
    """STS (Short Term Storage) diagnosis material from XML."""
    sample_id: str
    number: str
    year: str
    material_type: str
    diagnosis: str
    taking_date: Optional[datetime]
    retrieved: str


@dataclass
class Patient:
    """Patient record from XML."""
    patient_id: str
    biobank: str
    consent: bool
    month: str
    sex: str
    year: int
    lts_samples: List[TissueSample]
    sts_samples: List[DiagnosisMaterial]


# =============================================================================
# XML Parser
# =============================================================================

def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime from XML format."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except:
        return None


# XML Namespace for BBMRI data
NS = {'bbmri': 'http://www.bbmri.cz/schemas/biobank/data'}
BBMRI_NS = '{http://www.bbmri.cz/schemas/biobank/data}'


def get_element_text(parent, name: str, default: str = '') -> str:
    """Get text from child element, handling namespaces."""
    # Try with namespace first
    elem = parent.find(f'{BBMRI_NS}{name}')
    if elem is None:
        # Fallback without namespace
        elem = parent.find(name)
    if elem is not None and elem.text:
        return elem.text
    return default


def load_patient_from_xml(xml_path: str) -> Patient:
    """
    Load patient data from MOU XML file.

    This matches the Java XmlMapper.readValue(inputStream, Patient.class)
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Parse patient attributes
    patient_id = root.get('id', '')
    biobank = root.get('biobank', '')
    consent = root.get('consent', 'false').lower() == 'true'
    month = root.get('month', '')
    sex = root.get('sex', '')
    year = int(root.get('year', '0'))

    # Parse LTS (Long Term Storage) samples - with namespace
    lts_samples = []
    lts_elem = root.find(f'{BBMRI_NS}LTS')
    if lts_elem is not None:
        for tissue in lts_elem.findall(f'{BBMRI_NS}tissue'):
            sample = TissueSample(
                sample_id=tissue.get('sampleId', ''),
                number=tissue.get('number', ''),
                year=tissue.get('year', ''),
                samples_no=int(get_element_text(tissue, 'samplesNo', '0')),
                available_samples_no=int(get_element_text(tissue, 'availableSamplesNo', '0')),
                material_type=get_element_text(tissue, 'materialType'),
                ptnm=get_element_text(tissue, 'pTNM'),
                morphology=get_element_text(tissue, 'morphology'),
                diagnosis=get_element_text(tissue, 'diagnosis'),
                cut_time=parse_datetime(get_element_text(tissue, 'cutTime')),
                freeze_time=parse_datetime(get_element_text(tissue, 'freezeTime')),
                retrieved=get_element_text(tissue, 'retrieved')
            )
            lts_samples.append(sample)

    # Parse STS (Short Term Storage) samples - with namespace
    sts_samples = []
    sts_elem = root.find(f'{BBMRI_NS}STS')
    if sts_elem is not None:
        for diag in sts_elem.findall(f'{BBMRI_NS}diagnosisMaterial'):
            sample = DiagnosisMaterial(
                sample_id=diag.get('sampleId', ''),
                number=diag.get('number', ''),
                year=diag.get('year', ''),
                material_type=get_element_text(diag, 'materialType'),
                diagnosis=get_element_text(diag, 'diagnosis'),
                taking_date=parse_datetime(get_element_text(diag, 'takingDate')),
                retrieved=get_element_text(diag, 'retrieved')
            )
            sts_samples.append(sample)

    patient = Patient(
        patient_id=patient_id,
        biobank=biobank,
        consent=consent,
        month=month,
        sex=sex,
        year=year,
        lts_samples=lts_samples,
        sts_samples=sts_samples
    )

    print(f"Loaded patient {patient.patient_id}: {len(lts_samples)} LTS, {len(sts_samples)} STS samples")

    return patient


# =============================================================================
# Transform to CPM
# =============================================================================

def transform_acquisition_to_cpm(patient: Patient) -> List[ProvDocument]:
    """
    Transform patient data to CPM acquisition bundles.

    This matches Java's CpmAcquisitionTransformer.toDocuments()
    """
    print("Transforming to CPM Acquisition bundles...")

    documents = []

    # Combine all samples
    all_samples = [(s.sample_id, s.diagnosis, 'LTS') for s in patient.lts_samples]
    all_samples += [(s.sample_id, s.diagnosis, 'STS') for s in patient.sts_samples]

    # Define namespaces (matching Java)
    bbmri_ns = 'http://www.bbmri.cz/schemas/biobank/data#'
    cpm_ns = 'https://www.commonprovenancemodel.org/cpm-namespace-v1-0/'
    pbm_ns = 'http://commonprovenancemodel.org/ns/pbm/'
    dct_ns = 'http://purl.org/dc/terms/'

    for sample_id, diagnosis, storage_type in all_samples:
        doc = ProvDocument()

        bbmri = Namespace('bbmri', bbmri_ns)
        cpm = Namespace('cpm', cpm_ns)
        pbm = Namespace('pbm', pbm_ns)
        dct = Namespace('dct', dct_ns)

        doc.add_namespace(bbmri)
        doc.add_namespace(cpm)
        doc.add_namespace(pbm)
        doc.add_namespace(dct)

        # Create bundle
        sample_id_safe = sample_id.replace(':', '-')
        bundle = doc.bundle(bbmri[f'acquisitionBundle-{patient.patient_id}-{sample_id_safe}'])

        # Main Activity (CPM)
        main_activity = bundle.activity(
            bbmri[f'acquisition-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': cpm['mainActivity'],
                dct['hasPart']: bbmri[f'acquisitionAct-{patient.patient_id}-{sample_id_safe}']
            }
        )

        # Forward Connector (CPM)
        forward_connector = bundle.entity(
            bbmri[f'sampleAcqConnector-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': cpm['forwardConnector']
            }
        )

        # Forward Connector Spec with reference to storage bundle
        forward_connector_spec = bundle.entity(
            bbmri[f'sampleAcqConnectorSpec-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': cpm['forwardConnector'],
                cpm['referencedBundleId']: bbmri[f'storageBundle-{patient.patient_id}-{sample_id_safe}']
            }
        )

        # Receiver Agent (CPM)
        receiver_agent = bundle.agent(
            bbmri[patient.biobank],
            other_attributes={
                'prov:type': cpm['receiverAgent']
            }
        )

        # Domain-specific: Sample
        sample_entity = bundle.entity(
            bbmri[f'sample-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': pbm['sample'],
                bbmri['sampleId']: sample_id
            }
        )

        # Domain-specific: Acquisition Activity
        acquisition_activity = bundle.activity(
            bbmri[f'acquisitionAct-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': pbm['acquisitionActivity']
            }
        )

        # Relations
        bundle.generation(forward_connector, main_activity)
        bundle.specialization(forward_connector_spec, forward_connector)
        bundle.attribution(forward_connector_spec, receiver_agent)
        bundle.specialization(sample_entity, forward_connector)
        bundle.generation(sample_entity, acquisition_activity)

        documents.append(doc)

    print(f"Created {len(documents)} acquisition bundle(s)")
    return documents


def transform_storage_to_cpm(patient: Patient) -> List[ProvDocument]:
    """
    Transform patient data to CPM storage bundles.

    This matches Java's CpmStorageTransformer.toDocuments()
    """
    print("Transforming to CPM Storage bundles...")

    documents = []

    # Combine all samples
    all_samples = []
    for s in patient.lts_samples:
        all_samples.append({
            'sample_id': s.sample_id,
            'diagnosis': s.diagnosis,
            'storage_type': 'LTS',
            'material_type': s.material_type,
            'freeze_time': s.freeze_time
        })
    for s in patient.sts_samples:
        all_samples.append({
            'sample_id': s.sample_id,
            'diagnosis': s.diagnosis,
            'storage_type': 'STS',
            'material_type': s.material_type,
            'taking_date': s.taking_date
        })

    # Define namespaces
    bbmri_ns = 'http://www.bbmri.cz/schemas/biobank/data#'
    cpm_ns = 'https://www.commonprovenancemodel.org/cpm-namespace-v1-0/'
    pbm_ns = 'http://commonprovenancemodel.org/ns/pbm/'
    dct_ns = 'http://purl.org/dc/terms/'

    for sample in all_samples:
        sample_id = sample['sample_id']
        sample_id_safe = sample_id.replace(':', '-')

        doc = ProvDocument()

        bbmri = Namespace('bbmri', bbmri_ns)
        cpm = Namespace('cpm', cpm_ns)
        pbm = Namespace('pbm', pbm_ns)
        dct = Namespace('dct', dct_ns)

        doc.add_namespace(bbmri)
        doc.add_namespace(cpm)
        doc.add_namespace(pbm)
        doc.add_namespace(dct)

        # Create bundle
        bundle = doc.bundle(bbmri[f'storageBundle-{patient.patient_id}-{sample_id_safe}'])

        # Main Activity
        main_activity = bundle.activity(
            bbmri[f'storage-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': cpm['mainActivity'],
                dct['hasPart']: bbmri[f'transport-{patient.patient_id}-{sample_id_safe}'],
            }
        )

        # Backward Connector (link to acquisition)
        backward_connector = bundle.entity(
            bbmri[f'sampleAcqConnector-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': cpm['backwardConnector'],
                cpm['referencedBundleId']: bbmri[f'acquisitionBundle-{patient.patient_id}-{sample_id_safe}']
            }
        )

        # Forward Connector
        forward_connector = bundle.entity(
            bbmri[f'sampleStorConnector-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': cpm['forwardConnector']
            }
        )

        # Sender Agent
        sender_agent = bundle.agent(
            bbmri['UNI'],
            other_attributes={
                'prov:type': cpm['senderAgent']
            }
        )

        # Domain-specific: Transport Activity
        transport_activity = bundle.activity(
            bbmri[f'transport-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': pbm['transportActivity']
            }
        )

        # Domain-specific: Sample (transport)
        sample_trans = bundle.entity(
            bbmri[f'sampleTrans-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': pbm['sample'],
                bbmri['sampleId']: sample_id
            }
        )

        # Domain-specific: Storage Activity
        storage_activity = bundle.activity(
            bbmri[f'storageAct-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': pbm['storageActivity']
            }
        )

        # Domain-specific: Stored Sample
        stored_sample = bundle.entity(
            bbmri[f'sampleStorage-{patient.patient_id}-{sample_id_safe}'],
            other_attributes={
                'prov:type': pbm['sample'],
                'prov:type': bbmri['diagnosticMaterial'],
                bbmri['sampleId']: sample_id,
                bbmri['storageType']: sample['storage_type'],
                bbmri['materialType']: sample['material_type'],
                bbmri['diagnosis']: sample['diagnosis']
            }
        )

        # Domain-specific: Patient entity
        patient_entity = bundle.entity(
            bbmri[f'patient-{patient.patient_id}'],
            other_attributes={
                'prov:type': pbm['source'],
                bbmri['sex']: patient.sex,
                bbmri['birthYear']: str(patient.year),
                bbmri['gaveConsent']: str(patient.consent).lower()
            }
        )

        # Relations
        bundle.usage(main_activity, backward_connector)
        bundle.generation(forward_connector, main_activity)
        bundle.attribution(backward_connector, sender_agent)
        bundle.derivation(forward_connector, backward_connector)
        bundle.generation(sample_trans, transport_activity)
        bundle.specialization(sample_trans, backward_connector)
        bundle.usage(storage_activity, sample_trans)
        bundle.generation(stored_sample, storage_activity)
        bundle.specialization(stored_sample, forward_connector)
        bundle.derivation(sample_trans, patient_entity)
        bundle.derivation(stored_sample, patient_entity)

        documents.append(doc)

    print(f"Created {len(documents)} storage bundle(s)")
    return documents


# =============================================================================
# Analyze and Export
# =============================================================================

def analyze_documents(docs: List[ProvDocument], doc_type: str):
    """Analyze CPM structure of documents."""
    for i, doc in enumerate(docs[:3]):
        bundle = list(doc.bundles)[0] if doc.bundles else doc
        cpm_doc = CpmDocument(doc)

        ti_count = 0
        ds_count = 0

        for record in bundle.get_records():
            if hasattr(record, 'attributes'):
                prov_types = [str(v) for k, v in record.attributes if 'type' in str(k).lower()]
                is_ti = any('cpm:' in t.lower() for t in prov_types)
                if is_ti:
                    ti_count += 1
                else:
                    ds_count += 1

        print(f"{doc_type} bundle {i+1} ({bundle.identifier}): TI={ti_count}, DS={ds_count}")

    if len(docs) > 3:
        print(f"... and {len(docs) - 3} more {doc_type} bundles")


def export_documents(docs: List[ProvDocument], output_dir: Path, prefix: str):
    """Export documents to PROV-N format."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for doc in docs:
        bundle = list(doc.bundles)[0] if doc.bundles else None
        if bundle:
            bundle_name = str(bundle.identifier).split(':')[-1].replace(':', '-')
            output_file = output_dir / f"{bundle_name}.provn"

            try:
                doc.serialize(str(output_file), format='provn')
            except Exception as e:
                print(f"Failed to export {bundle_name}: {e}")

    print(f"Exported {len(docs)} {prefix} files to {output_dir.name}/")


# =============================================================================
# Main
# =============================================================================

def main():
    """Main execution."""
    print("USE CASE: MOU/BBMRI Biobank - External XML File Transformation")

    # Find the XML file - first try local data folder, then fallback to java-cpm
    local_data = Path(__file__).parent / "data" / "mou" / "test-data.xml"
    java_data = Path(__file__).parent.parent.parent.parent / "java-cpm" / "java-cpm" / "cpm-template" / "src" / "test" / "resources" / "mou" / "test-data.xml"

    if local_data.exists():
        xml_file = local_data
    elif java_data.exists():
        xml_file = java_data
    else:
        print(f"XML file not found at {local_data} or {java_data}")
        return

    try:
        # Load XML
        patient = load_patient_from_xml(str(xml_file))

        # Transform to Acquisition bundles
        acquisition_docs = transform_acquisition_to_cpm(patient)
        analyze_documents(acquisition_docs, "Acquisition")

        # Transform to Storage bundles
        storage_docs = transform_storage_to_cpm(patient)
        analyze_documents(storage_docs, "Storage")

        # Export
        output_dir = Path(__file__).parent / "output" / "mou"
        export_documents(acquisition_docs, output_dir / "acquisition", "acquisition")
        export_documents(storage_docs, output_dir / "storage", "storage")

        # Summary
        total_samples = len(patient.lts_samples) + len(patient.sts_samples)
        print(f"\nSummary: patient {patient.patient_id}, {total_samples} samples, "
              f"{len(acquisition_docs)} acquisition + {len(storage_docs)} storage bundles")
        print("Use case completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
