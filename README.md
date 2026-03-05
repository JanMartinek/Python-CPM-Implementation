# Chain Provenance Model (CPM) - Python Implementation

A Python implementation of the **Chain Provenance Model (CPM)**, a structured provenance model built on W3C PROV-DM for representing complex provenance chains with traversal information, connectors, and domain-specific components.

## Overview

This project implements the CPM specification, providing:

- **Structured Provenance Documents**: Main activities, forward/backward connectors, agents, and identifier entities
- **Template System**: JSON-based templates for defining traversal information structures
- **Validation Framework**: Comprehensive validation matching reference implementation specifications
- **Graph Operations**: Full CRUD operations on provenance graphs with PROV compliance
- **Bidirectional Conversion**: Templates ↔ PROV documents with complete roundtrip support

## Features

- **CPM Document Management**: Create, modify, and analyze CPM-compliant PROV documents
- **Template Processing**: Serialize/deserialize CPM templates (JSON, EMBRC, JSON-LD formats)
- **Traversal Information (TI)**: Automatic separation of TI and domain-specific (DS) components
- **Graph Wrapper**: Intuitive node-edge representation of PROV documents
- **Comprehensive Validation**: 740 passing tests ensuring complete functionality

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd python-implementation-of-the-cpm

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Requirements

- Python >= 3.8
- prov >= 2.0.0
- networkx >= 2.5
- python-dateutil >= 2.8.0
- rdflib >= 6.0.0 (for RDF/Turtle serialization)

**Optional dependencies:**

- matplotlib >= 3.3.0 (for graph visualization)
- lxml >= 4.6.0 (for XML/RDF processing)
- jsonschema >= 4.0.0 (for JSON schema validation)

## Quick Start

### Creating a CPM Document

```python
from prov.model import ProvDocument
from src.cpm.model import CpmDocument

# Create a basic PROV document
doc = ProvDocument()
doc.add_namespace('ex', 'http://example.org/')

# Wrap it in CPM document for enhanced functionality
cpm_doc = CpmDocument(doc)

# Add nodes
main_activity = cpm_doc.add_node('activity', 'ex:process', {
    'prov:type': 'cpm:MainActivity',
    'prov:label': 'Main Processing Activity'
})

input_entity = cpm_doc.add_node('entity', 'ex:input')
output_entity = cpm_doc.add_node('entity', 'ex:output')

# Add relationships
cpm_doc.add_edge('used', 'ex:process', 'ex:input')
cpm_doc.add_edge('wasgeneratedby', 'ex:process', 'ex:output')

# Query the document
print(f"Total nodes: {cpm_doc.get_statistics()['total_nodes']}")
print(f"Total edges: {cpm_doc.get_statistics()['total_edges']}")
```

### Using the Template System

```python
from src.cpm.template import TraversalInformationTemplate, MainActivityTemplate
from src.cpm.template_mapper import TemplateProvMapper

# Create a template
template = TraversalInformationTemplate(
    bundle_name='ex:workflow',
    main_activity=MainActivityTemplate(
        id='ex:mainProcess'
    ),
    prefixes={'ex': 'http://example.org/'}
)

# Convert template to PROV document
mapper = TemplateProvMapper()
prov_doc = mapper.map_to_document(template)

# Create CPM document from template
cpm_doc = CpmDocument.from_template(template)

# Verify structure
assert cpm_doc.get_main_activity() is not None
```

### Builder Pattern for Complex Documents

```python
from src.cpm.builder import CpmDocumentBuilder

# Use fluent API
cpm_doc = (CpmDocumentBuilder("ex:etl_bundle")
    .with_prefix('ex', 'http://example.org/')
    .with_main_activity('ex:workflow', start_time='2024-01-01T00:00:00Z')
    .with_forward_connector('ex:fc1', 'ex:target_bundle')
    .with_backward_connector('ex:bc1', 'ex:source_bundle')
    .with_sender_agent('ex:sender')
    .with_receiver_agent('ex:receiver')
    .build())

# Document is ready to use
stats = cpm_doc.get_statistics()
print(f"Built document with {stats['total_nodes']} nodes")
```

## Architecture

### Core Components

```
src/
├── cpm/                         # CPM implementation
│   ├── model/                   # Mixin-based document classes
│   │   ├── cpm_document.py      # Main CpmDocument class
│   │   ├── core.py              # CRUD operations
│   │   ├── io.py                # Serialization/I/O
│   │   ├── analysis.py          # Analysis & metrics
│   │   └── traversal.py         # Graph traversal
│   ├── template.py              # Template data structures
│   ├── template_mapper.py       # Template ↔ PROV conversion
│   ├── ti_algorithm.py          # TI/DS separation algorithm
│   ├── builder.py               # Builder pattern
│   ├── validation.py            # Validation framework
│   ├── constants.py             # CPM constants
│   └── exceptions.py            # Custom exceptions
├── graph/                       # Graph operations
│   ├── wrapper.py               # ProvGraphWrapper
│   ├── node.py                  # GraphNode
│   ├── edge.py                  # GraphEdge
│   └── factory.py               # Graph factories (DividedCpmFactory, MergedCpmFactory)
├── adapters/                    # External integrations
│   └── prov_adapter.py          # PROV utilities
└── utils/                       # Utility functions
    └── graph_utils.py
```

### Design Patterns

1. **Mixin Architecture**
   - Separates concerns into focused mixins
   - `Core`: Node/edge CRUD operations
   - `IO`: Template serialization, document I/O
   - `Analysis`: Statistics, validation, analysis
   - `Traversal`: Graph traversal and path finding

2. **Builder Pattern** (`CpmDocumentBuilder`)
   - Fluent API for document construction
   - Validates structure during build
   - Simplifies complex document creation

3. **Factory Pattern** (`CpmFactory`)
   - Creates pre-configured document structures
   - Ensures consistency across documents

4. **Template System**
   - JSON-based declarative document definition
   - Bidirectional conversion (Template ↔ PROV)
   - Multiple format support (CPM, EMBRC, JSON-LD)

## Key Concepts

### Chain Provenance Model (CPM)

CPM extends PROV-DM with structured components:

- **Main Activity**: The primary activity in a provenance chain
- **Forward Connectors**: Activities that prepare inputs for the main activity
- **Backward Connectors**: Activities that process outputs from the main activity
- **Traversal Information (TI)**: Infrastructure for connecting provenance chains
- **Domain Specific (DS)**: The actual data and processing logic

### Traversal Information Algorithm

Automatically identifies and separates TI from DS components:

```python
from src.cpm.ti_algorithm import TraversalInformationAlgorithm

# Check if a PROV element belongs to traversal information
if TraversalInformationAlgorithm.belongs_to_traversal_information(node.prov_entity):
    print("This is a TI node")
else:
    print("This is a DS node")

# Get only domain-specific nodes via CpmDocument
ds_nodes = cpm_doc.get_domain_specific_nodes()
```

## Advanced Usage

### CRUD Operations

```python
# Create
cpm_doc.add_node('entity', 'ex:data', {'label': 'Dataset'})
cpm_doc.add_edge('wasgeneratedby', 'ex:activity', 'ex:data')

# Read
node = cpm_doc.get_node('ex:data')
edges = cpm_doc.get_edges('ex:activity', 'ex:data')

# Delete
cpm_doc.remove_edge('ex:activity', 'ex:data')
cpm_doc.remove_node('ex:data')
```

### Template Operations

```python
from src.cpm.template import (
    TraversalInformationTemplate,
    TraversalInformationSerializer,
    TraversalInformationDeserializer
)

# Serialize to JSON
json_str = TraversalInformationSerializer.to_json(template, indent=2)

# Deserialize from JSON (accepts dict or JSON string)
template = TraversalInformationDeserializer.from_json(json_data)

# Save to file
TraversalInformationSerializer.to_file(template, 'workflow.json')

# Load from file
template = TraversalInformationDeserializer.from_file('workflow.json')
```

### Validation

```python
from src.cpm.validation import CpmValidator

# Validate CPM document (accepts a ProvGraphWrapper)
validator = CpmValidator()
report = validator.validate(cpm_doc.to_graph_wrapper())

# Check results
print(f"Valid: {report.is_valid}")
print(f"Errors: {report.error_count}, Warnings: {report.warning_count}")

for error in report.get_errors():
    print(f"  ERROR: {error.message}")

for warning in report.get_warnings():
    print(f"  WARNING: {warning.message}")
```

### Graph Analysis

```python
# Get statistics
stats = cpm_doc.get_statistics()
print(f"Nodes: {stats['total_nodes']}")
print(f"Edges: {stats['total_edges']}")
print(f"Entities: {stats['entities']}")
print(f"Activities: {stats['activities']}")
print(f"Agents: {stats['agents']}")

# Analyze structure
print(f"Has main activity: {cpm_doc.get_main_activity() is not None}")
print(f"Forward connectors: {len(cpm_doc.get_forward_connectors())}")
print(f"Backward connectors: {len(cpm_doc.get_backward_connectors())}")

# Check equality
if cpm_doc1.equals(cpm_doc2):
    print("Documents are structurally equivalent")
```

### Graph Traversal

```python
# Find paths between nodes
paths = cpm_doc.find_paths('ex:source', 'ex:target', max_length=5)

# Get predecessors and successors
predecessors = cpm_doc.get_predecessors('ex:node', max_depth=3)
successors = cpm_doc.get_successors('ex:node', max_depth=3)

# Get connected components
components = cpm_doc.get_connected_components()
```

## Examples

Run the provided examples to see the CPM system in action:

```bash
# Start here: Basic CPM operations and PROV document handling
python examples/basic_examples.py

# Advanced: Complex workflows, graph analysis, subgraph filtering, and performance
python examples/advanced_examples.py

# Templates: CPM template system, validation, and structured workflows
python examples/template_examples.py

# Advanced Templates: Template processing pipeline and format conversion
python examples/template_advanced_examples.py

# CPM Document: Comprehensive usage examples for CpmDocument class
python examples/cpmdocument_examples.py

# Use Case: BBMRI Biobank - Transform real-world biobank data to CPM
python examples/usecases/usecase_bbmri_biobank.py

# Use Case: MOU XML - Load external XML file (same as Java test resources)
python examples/usecases/usecase_mou_xml.py

# Use Case: EMBRC JSON-LD - Load marine biology provenance data
python examples/usecases/usecase_embrc_jsonld.py
```

### External File Use Cases (Standalone)

The library provides use cases that load external data files included in the project:

#### MOU/BBMRI XML Use Case (`usecase_mou_xml.py`)

Loads `test-data.xml` and transforms to CPM:

```bash
python examples/usecases/usecase_mou_xml.py
```

- **Input**: `examples/usecases/data/mou/test-data.xml`
- **Output**: PROV-N files in `examples/usecases/output/mou/`
- **Creates**: Acquisition and Storage bundles (matches Java CpmMouTest)

#### EMBRC JSON-LD Use Case (`usecase_embrc_jsonld.py`)

Loads Dataset\*\_ProvenanceMetadata.jsonld files:

```bash
python examples/usecases/usecase_embrc_jsonld.py
```

- **Input**: `examples/usecases/data/embrc/dataset*/`
- **Output**: PROV-N files in `examples/usecases/output/embrc/`
- **Creates**: CPM documents from 4 marine biology datasets (matches Java CpmEmbrcTest)

### BBMRI Biobank Use Case

The `usecase_bbmri_biobank.py` demonstrates a complete real-world transformation pipeline:

1. **Load raw data** - Simulates loading patient, sample, and storage records from CSV/database
2. **Transform to CPM** - Converts raw records to PROV document with full CPM structure
3. **Analyze structure** - Identifies main activity, connectors, and TI/DS separation
4. **Query domain data** - Retrieves specific sample and patient information
5. **Export** - Saves to PROV-N and JSON formats

This use case uses real BBMRI-ERIC (Biobanking and BioMolecular resources Research Infrastructure)
data structures, demonstrating interoperability with the Java CPM implementation.

The examples demonstrate all major functionality including the new subgraph filtering capabilities.

## Running Tests

The project includes a comprehensive test suite with **740 passing tests** covering all functionality.

### Quick Test Run

```bash
# Run all tests with pytest (recommended)
python -m pytest tests/ -v

# Run all tests quietly
python -m pytest tests/ -q

# Run specific test suites
python -m pytest tests/template/ -v
python -m pytest tests/model/ -v
python -m pytest tests/graph/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Using Make

```bash
# Run all tests
make test

# Run with coverage
make test-coverage
```

### Platform-Specific Setup

```bash
# Windows Command Prompt
cd python-implementation-of-the-cpm
python -m pytest tests/ -q

# Windows PowerShell
cd python-implementation-of-the-cpm
python -m pytest tests/ -q

# Linux/Mac
cd python-implementation-of-the-cpm
python -m pytest tests/ -q
```

### Test Coverage

The test suite covers:

**Core CPM Functionality** (740 tests):

- **Model** (`tests/model/`) — CpmDocument CRUD, analysis, traversal, IO, equality, influence, mutability
  - `test_core.py` — Core mixin: nodes, edges, attributes, bundles (146 tests)
  - `test_cpm_document.py` — Utilities, namespaces, serialization, equality, modification, removal
  - `test_analysis.py` — TI/DS separation, statistics, complexity, constraints
  - `test_traversal.py` — Predecessors, successors, paths, connected components, connectors
  - `test_io.py` — Clone, merge, filter, export formats, equals, hash
  - `test_comprehensive.py` — Builder, validator, error handling, performance
  - `test_mutability.py` — CRUD workflow, template-to-advanced pipeline
  - `test_advanced_traversal.py` — Integration: template-based traversal
  - `test_cpm_prov_factory.py` — PROV factory operations
  - `test_model_parity.py` — TemplateProvMapper parity

- **Graph** (`tests/graph/`) — Graph abstraction layer
  - `test_node.py` — GraphNode, DividedGraphNode, MergedGraphNode
  - `test_edge.py` — GraphEdge variants, EdgeFilter, EdgeBuilder
  - `test_wrapper.py` — ProvGraphWrapper, subgraph creation
  - `test_factory.py` — DividedCpmFactory, MergedCpmFactory, managers
  - `test_graph_utils.py` — GraphAnalyzer, PriorityBasedScheduler

- **Template** (`tests/template/`) — Template system
  - `test_template.py` — Serialization, deserialization, validation, roundtrip
  - `test_template_mapper.py` — TemplateProvMapper mapping and agent merging

- **Validation** (`tests/validation/`) — Validation framework
  - `test_validation.py` — CpmValidator, ValidationReport, custom rules

- **Adapters** (`tests/adapters/`) — External integrations
  - `test_prov_adapter.py` — PROV document conversion, import/export

## API Reference

### CpmDocument

Main class for CPM document manipulation:

**Creation:**

- `CpmDocument(prov_document)` - Create from PROV document
- `CpmDocument.from_template(template)` - Create from CPM template

**Node Operations:**

- `add_node(node_type, identifier, attributes)` - Add entity/activity/agent
- `get_node(identifier)` - Get node by ID
- `get_nodes(identifier=None, node_type=None)` - Query nodes
- `remove_node(identifier)` - Remove node

**Edge Operations:**

- `add_edge(relation_type, source_id, target_id)` - Add relationship
- `get_edge(source_id, target_id, relation_type)` - Get single edge
- `get_edges(source_id, target_id, relation_type)` - Query edges
- `remove_edge(source_id, target_id, relation_type)` - Remove edge

**CPM-Specific:**

- `get_main_activity()` - Get main activity node
- `get_forward_connectors()` - Get forward connector nodes
- `get_backward_connectors()` - Get backward connector nodes
- `get_domain_specific_nodes()` - Get non-TI nodes

**Analysis:**

- `get_statistics()` - Document statistics
- `equals(other)` - Structural equality check
- `validate_structure()` - Run structural validation
- `validate_cpm_constraints()` - Validate CPM-specific rules
- `analyze_document_complexity()` - Complexity metrics

**I/O:**

- `to_prov_document()` - Convert to PROV document
- `export_to_formats()` - Export to JSON, XML, PROV-N
- `clone()` - Deep copy the document
- `merge_with(other, conflict_resolution)` - Merge two documents

### TraversalInformationTemplate

Template data structure:

```python
@dataclass
class TraversalInformationTemplate:
    bundle_name: str
    main_activity: MainActivityTemplate
    forward_connectors: List[ConnectorTemplate] = field(default_factory=list)
    backward_connectors: List[ConnectorTemplate] = field(default_factory=list)
    agents: List[AgentTemplate] = field(default_factory=list)
    identifier_entities: List[IdentifierEntityTemplate] = field(default_factory=list)
    prefixes: Dict[str, str] = field(default_factory=dict)
```

### CpmDocumentBuilder

Fluent API for document construction:

```python
builder = CpmDocumentBuilder("ex:bundle")
    .with_prefix(prefix, uri)
    .with_main_activity(activity_id, start_time=None, end_time=None)
    .with_forward_connector(connector_id, referenced_bundle_id, hash_value=None)
    .with_backward_connector(connector_id, referenced_bundle_id, hash_value=None)
    .with_sender_agent(agent_id)
    .with_receiver_agent(agent_id)
    .build()
```

### TemplateProvMapper

Convert templates to PROV documents:

```python
mapper = TemplateProvMapper(merge_agents=True)
prov_doc = mapper.map_to_document(template)
```

### CpmValidator

Validate CPM documents:

```python
validator = CpmValidator()
report = validator.validate(cpm_doc.to_graph_wrapper())
# Returns: ValidationReport with .is_valid, .error_count, .warning_count
# Methods: .get_errors(), .get_warnings(), .get_by_type(type)
```

## Dependencies

**Core dependencies:**

- **prov** >= 2.0.0 - W3C PROV-DM implementation
- **networkx** >= 2.5 - Graph data structure and algorithms
- **python-dateutil** >= 2.8.0 - Date/time utilities
- **rdflib** >= 6.0.0 - RDF/Turtle serialization support
- **python** >= 3.8 - Python runtime

**Development dependencies:**

- **pytest** >= 8.0.0 - Testing framework
- **pytest-cov** >= 4.0.0 - Coverage reporting

**Optional dependencies:**

- **matplotlib** >= 3.3.0 - Graph visualization
- **lxml** >= 4.6.0 - XML/RDF processing
- **jsonschema** >= 4.0.0 - JSON schema validation

Install all dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

```
python-implementation-of-the-cpm/
├── src/                          # Source code
│   ├── cpm/                      # CPM implementation
│   │   ├── model/               # Mixin-based document classes
│   │   │   ├── cpm_document.py  # Combined CpmDocument class
│   │   │   ├── core.py          # Core CRUD operations
│   │   │   ├── io.py            # I/O and serialization
│   │   │   ├── analysis.py      # Analysis and metrics
│   │   │   └── traversal.py     # Graph traversal
│   │   ├── template.py          # Template system
│   │   ├── template_mapper.py   # Template-PROV conversion
│   │   ├── validation.py        # Validation framework
│   │   └── ...
│   ├── graph/                    # Graph operations
│   │   ├── wrapper.py           # ProvGraphWrapper
│   │   ├── node.py              # GraphNode classes
│   │   ├── edge.py              # GraphEdge classes
│   │   └── factory.py           # Graph factories
│   └── utils/                    # Utilities
├── tests/                        # Test suite (740 tests)
│   ├── model/                    # CpmDocument, core, analysis, traversal, IO
│   ├── graph/                    # GraphNode, GraphEdge, wrapper, factory
│   ├── template/                 # Template serialization and mapping
│   ├── validation/               # CpmValidator and rules
│   └── adapters/                 # PROV adapter tests
├── examples/                     # Example scripts
│   ├── basic_examples.py        # Basic operations
│   ├── advanced_examples.py     # Advanced features
│   ├── template_examples.py     # Template system
│   ├── template_advanced_examples.py  # Advanced template processing
│   ├── cpmdocument_examples.py  # CPM document usage
│   └── usecases/                 # Real-world use cases
│       ├── usecase_bbmri_biobank.py  # BBMRI biobank (simulated data)
│       ├── usecase_mou_xml.py        # MOU XML (external file)
│       ├── usecase_embrc_jsonld.py   # EMBRC JSON-LD (external file)
│       ├── data/                      # Test data files (standalone)
│       │   ├── mou/test-data.xml
│       │   └── embrc/dataset*/
│       └── output/                    # Generated PROV-N outputs
├── requirements.txt              # Dependencies
├── setup.py                      # Package setup
├── pyproject.toml               # Project configuration
├── Makefile                     # Build automation (Unix)
├── make.bat                     # Build automation (Windows)
├── .gitignore                   # Git ignore rules
└── README.md                     # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- **W3C PROV-DM**: https://www.w3.org/TR/prov-dm/
- **PROV Python Library**: https://github.com/trungdong/prov
- **Chain Provenance Model**: [CPM specification/documentation]

## Citation

If you use this implementation in your research, please cite:

```bibtex
@software{cpm_python,
  title={Chain Provenance Model - Python Implementation},
  author={[Authors]},
  year={2025},
  url={[Repository URL]}
}
```
