# Development Notes

This document summarizes repository-specific conventions that are useful when
extending or maintaining the project.

## Project Layout

- `src/cpm/` contains CPM-specific logic: templates, validation, builder, constants, and the `CpmDocument` mixins.
- `src/cpm/model/` contains the main document facade split into `core.py`, `traversal.py`, `analysis.py`, and `io.py`.
- `src/graph/` contains `ProvGraphWrapper`, graph node and edge abstractions, and factory support.
- `src/adapters/` contains integration helpers for PROV serialization and import/export.
- `src/utils/` contains shared graph helpers.
- `examples/` contains runnable demonstrations and domain use cases.
- `tests/` is the executable reference for expected behavior.
- `docs/thesis.tex` and related TeX assets contain the academic design and implementation narrative.

## Import Style In This Repository

The repository currently mixes two import styles in tests:

- `from src.cpm...` is the dominant style and is used by the examples.
- `from cpm...` appears in a smaller subset of tests.

For consistency with the checked-in examples and the internal absolute imports,
prefer `src.cpm...` when writing scripts directly against the repository checkout.

## Main Execution Paths

### Run The Test Suite

```bash
pip install -r requirements.txt
# or: pip install -e ".[dev]"
python -m pytest tests/ -v
```

The checked-in test suite covers XML export, so `lxml` must be installed before
running the full suite.

### Run A Narrower Test Slice

```bash
pytest tests/model/test_core.py
pytest tests/template/test_template.py
```

### Run Example Scripts

```bash
python examples/basic_examples.py
python examples/cpmdocument_examples.py
python examples/template_examples.py
```

## Suggested Documentation Sources While Developing

- Read `tests/` first when behavior is unclear.
- Read `examples/` when you need a realistic usage pattern.
- Read `docs/thesis.tex` when you need the design rationale behind CPM-specific choices.

## Core Design Facts

- `CpmDocument` keeps a PROV document and a graph wrapper in sync.
- Traversal information and domain-specific content are separated by CPM types and attribute rules.
- Validation is available in two layers: light dictionary-based checks on `CpmDocument` and structured `ValidationReport` output through `CpmValidator`.
- Templates are dataclass-based and serialize to JSON for interchange with the reference implementation.

## When To Use Which Layer

- Use `CpmDocument` for most application code.
- Use `CpmDocumentBuilder` when the bundle shape is known and you want fluent creation.
- Use template classes when JSON interchange matters.
- Use `ProvGraphWrapper` when you need direct graph access or NetworkX operations.
- Use `ProvAdapter` when format conversion should be handled explicitly outside the CPM facade.

## Documentation Maintenance

Update the Markdown docs in this folder when one of these changes happens:

- public method names or signatures change
- example import paths change
- template JSON structure changes
- validation report semantics change
- new user-facing workflows are added to `examples/`
