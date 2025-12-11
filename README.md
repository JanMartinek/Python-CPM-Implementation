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

-  **CPM Document Management**: Create, modify, and analyze CPM-compliant PROV documents
-  **Template Processing**: Serialize/deserialize CPM templates (JSON, EMBRC, JSON-LD formats)
-  **Traversal Information (TI)**: Automatic separation of TI and domain-specific (DS) components
-  **Graph Wrapper**: Intuitive node-edge representation of PROV documents
-  **Comprehensive Validation**: 311 passing tests ensuring complete functionality


## Installation

```bash
# Clone the repository
git clone <repository-url>
cd python-implementation-of-the-cpm

# Install dependencies
pip install -r requirements.txt
```

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
        activity_id='ex:mainProcess',
        label='Data Processing Pipeline'
    )
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
cpm_doc = (CpmDocumentBuilder()
    .with_namespace('ex', 'http://example.org/')
    .with_main_activity('ex:workflow', label='ETL Pipeline')
    .with_forward_connector('ex:fc1', label='Data Extractor')
    .with_backward_connector('ex:bc1', label='Result Writer')
    .add_agent('ex:system', label='Processing System')
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
│   │   ├── mixin.py             # CRUD operations
│   │   ├── mixin.py             # Serialization/I/O
│   │   ├── analysis.py          # Analysis & metrics
│   │   └── traversal.py         # Graph traversal
│   ├── template.py              # Template data structures
│   ├── template_mapper.py       # Template ↔ PROV conversion
│   ├── ti_algorithm.py          # TI/DS separation algorithm
│   ├── builder.py               # Builder pattern
│   ├── factory.py               # Factory pattern
│   ├── validation.py            # Validation framework
│   ├── constants.py             # CPM constants
│   └── exceptions.py            # Custom exceptions
├── graph/                       # Graph operations
│   ├── wrapper.py               # ProvGraphWrapper
│   ├── node.py                  # GraphNode
│   ├── edge.py                  # GraphEdge
│   └── factory.py               # Graph factory
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
# Check if node belongs to traversal information
if cpm_doc.ti_algorithm.belongs_to_traversal_information(node.prov_entity):
    print("This is a TI node")
else:
    print("This is a DS node")

# Get only domain-specific nodes
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

# Update
cpm_doc.update_node('ex:data', {'label': 'Updated Dataset'})

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
serializer = TraversalInformationSerializer()
json_str = serializer.to_json(template, indent=2)

# Deserialize from JSON
deserializer = TraversalInformationDeserializer()
template = deserializer.from_json(json_str)

# Save to file
serializer.to_json_file(template, 'workflow.json')

# Load from file
template = deserializer.from_json_file('workflow.json')
```

### Validation

```python
from src.cpm.validation import CpmValidator

# Validate CPM document
validator = CpmValidator()
results = validator.validate_document(cpm_doc)

# Check for errors
if results['errors']:
    print("Validation errors found:")
    for error in results['errors']:
        print(f"  - {error.message}")

# Check warnings
for warning in results['warnings']:
    print(f"Warning: {warning.message}")
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
paths = cpm_doc.find_paths('ex:source', 'ex:target', max_depth=5)

# Get predecessors and successors
predecessors = cpm_doc.get_predecessors('ex:node')
successors = cpm_doc.get_successors('ex:node')

# Traverse from node
visited = cpm_doc.traverse_from('ex:start', direction='forward')
```

## Examples

Run the provided examples to see the CPM system in action:

```bash
# Start here: Basic CPM operations and PROV document handling
python examples/basic_examples.py

# Advanced: Complex workflows, graph analysis, and performance
python examples/advanced_examples.py

# Templates: CPM template system, validation, and structured workflows
python examples/template_examples.py
```

The examples have been consolidated from 11+ redundant files into 3 comprehensive demonstrations covering all major functionality. See `examples/README.md` for detailed descriptions.

## Running Tests

The project includes a comprehensive test suite with **311 passing tests** covering all functionality.

### Quick Test Run

```bash
# Run all tests with pytest (recommended)
python -m pytest tests/ -v

# Run all tests quietly
python -m pytest tests/ -q

# Run specific test suites
python -m pytest tests/test_template.py -v
python -m pytest tests/model/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Using Make

```bash
# Run all tests
make test

# Run with coverage
make coverage
```

### Using Python unittest

```bash
# Windows Command Prompt
cd python-implementation-of-the-cpm
set PYTHONPATH=src;%PYTHONPATH%
python -m pytest tests/ -q

# Windows PowerShell  
cd python-implementation-of-the-cpm
$env:PYTHONPATH="src;$env:PYTHONPATH"
python -m pytest tests/ -q

# Linux/Mac
cd python-implementation-of-the-cpm
export PYTHONPATH=src:$PYTHONPATH
python -m pytest tests/ -q
```

### Test Coverage

The test suite covers:

**Core CPM Functionality** (311 tests):
- **Document Operations** (`tests/model/`) - 40+ tests
  - `test_cpm_document_constructor.py` - Document construction (11 tests)
  - `test_cpm_document_modification.py` - Node/edge modification (4 tests)
  - `test_cpm_document_removal.py` - Removal operations (4 tests)
  - `test_cpm_document_equals.py` - Equality comparison (4 tests)
  - `test_cpm_document_additional.py` - Additional operations (5 tests)
  - `test_cpm_document_influence.py` - Influence relations (5 tests)
  - `test_cpm_utilities.py` - Utility functions (5 tests)
  - `test_cpm_prov_factory.py` - PROV factory (7 tests)

- **Template System** (`tests/test_template.py`) - Serialization, deserialization, validation
- **Graph Operations** (`tests/graph/`) - Node, edge, wrapper functionality
- **Comprehensive Features** (`tests/test_comprehensive_features.py`) - Full CPM implementation verification
- **Validation** (`tests/test_validation.py`) - Comprehensive validation rules
- **Advanced Features** (`tests/test_mutability.py`, `tests/test_advanced_traversal.py`) - Complex operations
- **Model Parity** (`tests/test_model_parity.py`) - Template mapping verification


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
- `update_node(identifier, attributes)` - Update node attributes
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
- `validate()` - Run validation rules

**I/O:**
- `to_json()` - Export to JSON
- `to_prov_document()` - Convert to PROV document
- `serialize()` - Serialize to various formats

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
builder = CpmDocumentBuilder()
    .with_namespace(prefix, uri)
    .with_main_activity(id, label=None)
    .with_forward_connector(id, label=None)
    .with_backward_connector(id, label=None)
    .add_agent(id, label=None)
    .add_identifier_entity(id, label=None)
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
results = validator.validate_document(cpm_doc)
# Returns: {'errors': [...], 'warnings': [...], 'info': [...]}
```

## Dependencies

Core dependencies:
- **prov** (>= 2.0.0) - W3C PROV-DM implementation
- **python** (>= 3.8) - Python runtime

Development dependencies:
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **jsonschema** - Template validation (optional)

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
│   │   ├── template.py          # Template system
│   │   ├── validation.py        # Validation framework
│   │   └── ...
│   ├── graph/                    # Graph operations
│   └── utils/                    # Utilities
├── tests/                        # Test suite (311 tests)
│   ├── model/                    # Model tests
│   ├── graph/                    # Graph tests
│   └── ...
├── examples/                     # Example scripts
│   ├── basic_examples.py
│   ├── advanced_examples.py
│   ├── template_examples.py
│   ├── template_output.json     # Generated template output
│   └── demo_template_output.json # Demo template output
├── requirements.txt              # Dependencies
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
