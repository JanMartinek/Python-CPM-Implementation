# Usage Guide

This guide covers the most common workflows when working with the CPM Python
implementation from this repository.

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

For repository-local scripts and notebooks, the codebase currently uses imports
under `src.cpm`, `src.graph`, and related modules.

## Workflow 1: Build A CPM Bundle Fluently

Use `CpmDocumentBuilder` when you want to assemble a CPM bundle from its main
structural components.

```python
from src.cpm.builder import CpmDocumentBuilder
from src.cpm.validation import CpmValidator

cpm_doc = (
    CpmDocumentBuilder("ex:bundle")
    .with_prefix("ex", "http://example.org/")
    .with_main_activity("ex:process")
    .with_backward_connector("ex:input_connector", "ex:upstream_bundle")
    .with_forward_connector("ex:output_connector", "ex:downstream_bundle")
    .with_sender_agent("ex:sender")
    .with_receiver_agent("ex:receiver")
    .build()
)

stats = cpm_doc.get_statistics()
report = CpmValidator().validate(cpm_doc.to_graph_wrapper())

print(stats)
print(report.is_valid, report.error_count, report.warning_count)
```

Use the builder when the bundle shape is known upfront and you want readable,
chainable construction code.

## Workflow 2: Start From A PROV Document And Edit It Directly

Use `CpmDocument` directly when you already have a `ProvDocument` or when you
need low-level node and edge manipulation.

```python
from prov.model import ProvDocument

from src.cpm.model import CpmDocument

prov_doc = ProvDocument()
prov_doc.add_namespace("ex", "http://example.org/")

cpm_doc = CpmDocument(prov_doc)

cpm_doc.add_node("activity", "ex:process", prov_type="cpm:MainActivity")
cpm_doc.add_node("entity", "ex:input")
cpm_doc.add_node("entity", "ex:output")

cpm_doc.add_edge("used", "ex:process", "ex:input")
cpm_doc.add_edge("wasgeneratedby", "ex:process", "ex:output")

main_activity = cpm_doc.get_main_activity()
predecessors = cpm_doc.get_predecessors("ex:process")
successors = cpm_doc.get_successors("ex:process")
```

The `add_edge` API uses `(relation_type, source_id, target_id)` consistently,
even for PROV relations whose underlying library call uses a different order.

## Workflow 3: Create Documents From Templates

Use templates when you want deterministic JSON serialization or when you need
to exchange the CPM bundle structure with another implementation.

```python
from src.cpm.model import CpmDocument
from src.cpm.template import (
    AgentTemplate,
    ConnectorTemplate,
    CpmBundleSerializer,
    CpmBundleTemplate,
    MainActivityTemplate,
)

template = CpmBundleTemplate(
    prefixes={"ex": "http://example.org/"},
    bundle_name="ex:bundle",
    main_activity=MainActivityTemplate(id="ex:process"),
    backward_connectors=[
        ConnectorTemplate(
            id="ex:input_connector",
            referenced_bundle_id="ex:upstream_bundle",
        )
    ],
    sender_agents=[AgentTemplate(id="ex:sender")],
)

cpm_doc = CpmDocument.from_template(template)
json_payload = CpmBundleSerializer.to_json(template, indent=2)
```

Template JSON can also be stored and loaded through
`CpmBundleSerializer.to_file(...)` and `CpmBundleDeserializer.from_file(...)`.

## Workflow 4: Analyze Traversal Information And Structure

`CpmDocument` provides analysis helpers on top of the graph wrapper.

```python
ti_nodes = cpm_doc.get_traversal_information_nodes()
ds_nodes = cpm_doc.get_domain_specific_nodes()
stats = cpm_doc.get_statistics()

structure_report = cpm_doc.validate_structure()
constraint_report = cpm_doc.validate_cpm_constraints()
```

Use the analysis mixin methods for lightweight checks and use `CpmValidator`
when you need a structured validation report with severity levels and counts.

## Workflow 5: Export And Clone Documents

```python
exports = cpm_doc.export_to_formats()
clone = cpm_doc.clone()
merged = cpm_doc.merge_with(clone, conflict_resolution="keep_both")

print(exports["json"])
print(cpm_doc.equals(clone))
```

`export_to_formats()` returns a dictionary with `provn`, `json`, and `xml`
payloads.

## Workflow 6: Work With The Lower Graph Layer

Use `ProvGraphWrapper` if you need explicit graph objects, NetworkX access, or
graph-specific operations outside the CPM facade.

```python
from src.graph.wrapper import ProvGraphWrapper

wrapper = ProvGraphWrapper(cpm_doc.to_prov_document())
graph = wrapper.get_networkx_graph()
neighbors = wrapper.get_neighbors("ex:process")
```

This layer is useful for custom graph analysis and visualization.

## Examples In The Repository

- `examples/basic_examples.py` demonstrates baseline PROV and wrapper usage.
- `examples/cpmdocument_examples.py` focuses on `CpmDocument`.
- `examples/template_examples.py` and `examples/template_advanced_examples.py` cover templates.
- `examples/usecases/` contains end-to-end domain use cases.

## Common Pitfalls

- Declare namespaces before creating prefixed identifiers such as `ex:item1`.
- Mark the main activity explicitly through the CPM type, usually `cpm:MainActivity`.
- Prefer the repository's `src.cpm...` imports when running examples from the checkout.
- Use `CpmValidator().validate(...)` for full validation and the analysis mixin for lighter checks.
