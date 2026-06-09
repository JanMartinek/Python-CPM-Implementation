# CPM Python Documentation

This folder contains practical project documentation for the Python implementation
of the Common Provenance Model (CPM).

The Markdown files added here are meant for day-to-day development and usage.
The existing TeX sources remain the academic design and implementation record.

## Start Here

- [Usage Guide](USAGE_GUIDE.md) for the main workflows: creating documents, using templates, validating, and exporting.
- [API Reference](API_REFERENCE.md) for the public classes, dataclasses, and helper modules.
- [Development Notes](DEVELOPMENT.md) for project layout, test commands, and repository-specific conventions.
- [Thesis source](thesis.tex) for the detailed design rationale and formal write-up.

## Import Convention Used In This Repository

Most tests and examples in this repository import modules through the `src`
package, for example `from src.cpm.model import CpmDocument`. The documentation in
this folder follows that convention so that code snippets work directly from the
repository checkout.

If you are consuming the library from a separately packaged environment, adapt the
imports to the package layout exposed by that environment.

## Recommended Reading Order

1. Read [Usage Guide](USAGE_GUIDE.md).
2. Keep [API Reference](API_REFERENCE.md) open while working with the code.
3. Use [Development Notes](DEVELOPMENT.md) when running tests, examples, or making changes.

## Related Repository Areas

- `examples/` contains runnable scripts for basic, advanced, and real-world use cases.
- `tests/` contains the reference behavior for the implementation.
- `src/cpm/` contains CPM-specific logic.
- `src/graph/` contains the graph abstraction layer built on top of PROV.
