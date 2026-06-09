# API Reference

This reference summarizes the main public classes and modules exposed by the
repository.

## Package Map

| Module                      | Responsibility                            | Main entry points                                    |
| --------------------------- | ----------------------------------------- | ---------------------------------------------------- |
| `src.cpm.model`             | High-level CPM document API               | `CpmDocument`, `TemplateProvMapper`, `CpmValidator`  |
| `src.cpm.builder`           | Fluent bundle construction                | `CpmDocumentBuilder`                                 |
| `src.cpm.template`          | Template dataclasses and JSON processing  | `CpmBundleTemplate`, serializer/deserializer classes |
| `src.cpm.validation`        | Structured validation over graph wrappers | `CpmValidator`, `TraversalInformationStrategy`       |
| `src.cpm.ti_algorithm`      | Traversal information classification      | `TraversalInformationAlgorithm`                      |
| `src.graph.wrapper`         | Graph abstraction over `ProvDocument`     | `ProvGraphWrapper`                                   |
| `src.graph.node`            | Graph node abstraction                    | `GraphNode`, `DividedGraphNode`, `MergedGraphNode`   |
| `src.graph.edge`            | Graph edge abstraction and helpers        | `GraphEdge`, `EdgeBuilder`                           |
| `src.adapters.prov_adapter` | PROV import/export helpers                | `ProvAdapter`                                        |

## `CpmDocument`

`CpmDocument` combines four mixins: core CRUD operations, traversal,
analysis, and I/O.

### Construction And Conversion

- `CpmDocument(prov_document=None, ti_algorithm=None, bundle=None)` wraps an existing PROV document or creates a new one.
- `from_template(template, domain_specific_doc=None)` creates a document from a `CpmBundleTemplate`.
- `to_prov_document()` returns the underlying PROV document.
- `to_graph_wrapper()` returns the synchronized `ProvGraphWrapper`.
- `clone()` deep-copies the document.
- `merge_with(other, conflict_resolution="keep_both")` merges two documents.
- `filter_by_time_range(start_time=None, end_time=None)` returns a filtered copy.
- `export_to_formats()` returns serialized `provn`, `json`, and `xml` content.
- `equals(other)` and `hash_code()` support document comparison.

### Node Operations

- `add_node(node_type, identifier, attributes=None, prov_type=None)` creates an entity, activity, or agent.
- `get_node(identifier)` returns a single node or `None`.
- `get_nodes(identifier)` returns all nodes matching an identifier.
- `get_nodes_by_type(prov_type)` filters by PROV or CPM type.
- `get_nodes_by_attribute(attribute_name, attribute_value=None)` filters by attributes.
- `update_node_identifier(old_identifier, new_identifier)` renames a node.
- `remove_node(identifier, node_type=None)` removes a single node.
- `remove_nodes(identifier)` removes all nodes with the same identifier.
- `get_all_nodes()` returns every graph node.
- `get_nodes_map()` returns the internal identifier-to-nodes mapping.

### CPM-Specific Helpers

- `get_main_activity()` returns the CPM main activity.
- `get_forward_connectors()` returns all forward connectors.
- `get_backward_connectors()` returns all backward connectors.
- `get_current_agents()` returns current agents.
- `get_bundle_id()` and `set_bundle_id(bundle_id)` read and update the bundle identifier.
- `get_namespaces()` returns the active namespace mapping.

### Edge Operations

- `add_edge(relation_type, source_id, target_id, edge_id=None, attributes=None)` creates a PROV relation.
- `get_edge(source_id, target_id, relation_type=None)` returns one matching edge.
- `get_edges(source_id=None, target_id=None, relation_type=None)` filters edges.
- `remove_edge(source_id, target_id, relation_type=None)` removes one edge.
- `remove_edges(source_id=None, target_id=None, relation_type=None)` removes multiple edges.
- `get_edge_by_id(edge_id)` and `get_edges_by_id(edge_id)` query relations by identifier.
- `remove_edge_by_id(edge_id)` removes an identified relation.
- `get_all_edges()` returns all relation records.

### Traversal Operations

- `get_predecessors(node_id, max_depth=1, relation_types=None)` traverses incoming neighbors.
- `get_successors(node_id, max_depth=1, relation_types=None)` traverses outgoing neighbors.
- `get_connected_components()` returns disconnected subgraphs as node lists.
- `find_paths(source_id, target_id, max_length=None)` enumerates paths.
- `get_precursors(connector_id)` follows precursor connectors.
- `get_successors_connectors(connector_id)` follows successor connectors.
- `get_related_connectors(connector_id, max_depth=1)` traverses connector relationships.
- `get_subgraph(node_ids, preserve_context=True)` extracts a focused sub-document.

### Analysis And Validation Operations

- `get_traversal_information_nodes()` returns nodes classified as traversal information.
- `get_domain_specific_nodes()` returns nodes classified as domain-specific.
- `get_statistics()` returns counts and summary metrics.
- `get_cross_part_edges()` detects edges crossing part boundaries.
- `get_traversal_information_part()` extracts the traversal-information slice.
- `validate_structure()` performs lightweight structural checks.
- `validate_cpm_constraints()` performs CPM-specific constraint checks.
- `analyze_provenance_chains()` summarizes chain structure.
- `get_influence_network()` builds influence mappings.
- `compute_centrality_metrics()` exposes centrality measures.
- `analyze_document_complexity()` reports density and structural complexity.

### Low-Level Compatibility Helpers

These methods exist mainly for parity with the reference implementation or for
advanced internal workflows:

- `are_all_relations_mapped()`
- `set_new_cause_and_effect(...)`
- `set_collection_members(...)`
- `update_element_identifier(...)`
- `get_edge_with_kind(...)`
- `get_edges_by_relation(...)`
- `set_new_cause_and_effect_by_kind(...)`
- `get_node_by_element(...)`
- `get_node_by_id_and_kind(...)`
- `remove_node_by_kind(...)`
- `remove_edges_by_kind(...)`
- `set_ti_strategy(strategy)`
- `to_document()`
- `update_collection_members_advanced(...)`
- `set_element_identifier_advanced(...)`

## `CpmDocumentBuilder`

Use `CpmDocumentBuilder` when you want a fluent bundle construction API.

### Main Builder Methods

- `with_prefix(prefix, uri)` registers namespaces.
- `with_main_activity(activity_id, start_time=None, end_time=None, **attributes)` sets the required main activity.
- `with_forward_connector(connector_id, referenced_bundle_id, hash_value=None, **attributes)` adds a forward connector.
- `with_backward_connector(connector_id, referenced_bundle_id, hash_value=None, **attributes)` adds a backward connector.
- `with_sender_agent(agent_id, **attributes)` adds a sender agent.
- `with_receiver_agent(agent_id, **attributes)` adds a receiver agent.
- `with_current_agent(agent_id, **attributes)` adds a current agent.
- `with_used_relation(target_id, relation_id=None)` records a `used` relation on the main activity.
- `with_generated_entity(entity_id)` records a generated entity.
- `with_sub_activity(sub_activity_id)` records `hasPart` links.
- `build()` returns a `CpmDocument` and raises `InvalidOperationError` if the main activity is missing.

## Template API

The template module provides both simple dataclasses and higher-level JSON
processing helpers.

### Core Dataclasses

- `RelationTemplate`
- `MainActivityTemplate`
- `ConnectorTemplate`
- `AgentTemplate`
- `IdentifierEntityTemplate`
- `CpmBundleTemplate`

### Serialization And Deserialization

- `CpmBundleDeserializer.from_json(json_data)`
- `CpmBundleDeserializer.from_file(file_path)`
- `CpmBundleSerializer.to_dict(template)`
- `CpmBundleSerializer.to_json(template, indent=None)`
- `CpmBundleSerializer.to_file(template, file_path, indent=2)`

### Extended Template Helpers

- `TemplateSchemaValidator` performs JSON-schema-backed validation when `jsonschema` is installed.
- `AdvancedTemplateProcessor` provides enhanced transformation support.
- `EnhancedCpmBundleSerializer` extends the base serializer.
- `TemplateAgentAnalyzer` analyzes agent structure inside templates.
- `TemplateTransformationPipeline` chains template transformations.

## Validation API

`CpmValidator` works on `ProvGraphWrapper` and returns a structured
`ValidationReport`.

### Main Types

- `ValidationLevel`: `ERROR`, `WARNING`, `INFO`
- `ValidationType`: structural, semantic, template-compliance, cross-part, traversal
- `ValidationResult`: a single validation finding
- `ValidationReport`: aggregate result with counts and helper accessors

### `ValidationReport` Accessors

- `report.is_valid`
- `report.error_count`
- `report.warning_count`
- `report.info_count`
- `report.get_errors()`
- `report.get_warnings()`
- `report.get_by_type(validation_type)`

### Validator Entry Points

- `CpmValidator.validate(wrapper, template=None)` runs all registered rules.
- `TraversalInformationStrategy.detect_cross_part_edges(wrapper)` finds cross-part edges.
- `TraversalInformationStrategy.get_traversal_information(edge)` returns cached traversal metadata for an edge.

## Graph Layer

### `ProvGraphWrapper`

- `get_nodes()` returns `GraphNode` objects.
- `get_edges()` returns `GraphEdge` objects.
- `get_node_by_id(node_id)` and `get_edge_by_id(edge_id)` perform direct lookup.
- `get_networkx_graph()` exposes the underlying `networkx.DiGraph`.
- `get_neighbors(node_id)`, `get_predecessors(node_id)`, and `get_successors(node_id)` provide graph navigation.
- `visualize(filename=None, layout="spring", show_labels=True)` renders a graph when visualization dependencies are available.
- `to_prov_document()` rebuilds a `ProvDocument`.
- `create_subgraph(node_filter_func)` returns a filtered wrapper.
- `clear()` resets the wrapper.

### `GraphNode`

- `identifier`, `kind`, `node_type_name`, `degree`, `in_degree`, `out_degree`
- `get_prov_attribute(attribute_name)`
- `has_prov_type(prov_type)`
- `get_edges_by_relation_type(relation_type)`
- `get_connected_nodes(relation_types=None)`
- `is_isolated()`
- `clone()`

### `GraphEdge`

- `identifier`, `kind`, `cause`, `effect`
- `set_cause(cause)` and `set_effect(effect)`
- `get_attributes()` and `get_attribute_values(attribute_name)`
- `has_attribute(attribute_name)`
- `is_between(cause, effect)` and `connects_node(node)`
- `get_other_node(node)`
- `reverse()`
- `clone()`

### Edge Utilities

- `EdgeBuilder` builds `GraphEdge` objects through chained setters.
- Edge filter helpers in `src.graph.edge` can filter by cause, effect, kind, node, or attribute.

## Adapter Layer

### `ProvAdapter`

`ProvAdapter` is used by examples and utilities to export and import PROV data
in supported formats. Use it when you need an explicit adapter around format
conversion rather than the higher-level `CpmDocument` API.
