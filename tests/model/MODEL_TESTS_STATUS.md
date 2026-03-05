# CPM Model Tests - Java to Python Mapping

## Summary

**Status: 9/14 (64%) Complete**

Last Updated: 2025

## Java Model Tests Structure

### cpm-core/model/

1. **CpmDocumentConstructorTest.java** (656 lines) - Document construction and initialization ✅
2. **CpmDocumentAdditionalTest.java** (~200 lines) - Additional document operations ✅
3. **CpmDocumentEqualsTest.java** (~150 lines) - Equality and comparison operations ✅
4. **CpmDocumentInfluenceTest.java** (~180 lines) - Influence relationships ✅
5. **CpmDocumentModificationTest.java** (235 lines) - Document modification operations ✅
6. **CpmDocumentRemovalTest.java** (~200 lines) - Node and edge removal ✅
7. **CpmProvFactoryTest.java** (~300 lines) - PROV factory operations ✅
8. **CpmUtilitiesTest.java** (~180 lines) - Utility functions ✅

### cpm-core/vanilla/

9. **CpmFactoryTest.java** (~250 lines) - Factory pattern tests ✅

### cpm-core/strategy/

10. **AttributeTIStrategyTest.java** (~200 lines) - Strategy pattern for TI/DS classification ⏳

### cpm-core/divided/

11. **CpmDividedDocumentTest.java** (~250 lines) - Divided document operations ⏳
12. **ordered/CpmOrderedDocumentTest.java** (~180 lines) - Ordered divided documents ⏳
13. **unordered/CpmUnorderedDocumentTest.java** (~180 lines) - Unordered divided documents ⏳

### cpm-core/merged/

14. **CpmMergedDocumentTest.java** (~200 lines) - Merged document operations ⏳

## Python Model Tests - Current File Layout

### tests/model/

| File                           | Covers Java Tests | Notes                                                                   |
| ------------------------------ | ----------------- | ----------------------------------------------------------------------- |
| **test_cpm_document.py**       | #1-#6, #8         | Merged: additional, equals, influence, modification, removal, utilities |
| **test_cpm_prov_factory.py**   | #7                | PROV factory operations                                                 |
| **test_core.py**               | #1, #2, #5, #6    | Thorough core mixin tests (146 tests)                                   |
| **test_analysis.py**           | #10 (partial)     | TI/DS, statistics, cross-part edges, complexity                         |
| **test_traversal.py**          | —                 | Predecessors, successors, components, paths, connectors                 |
| **test_io.py**                 | #3, #6            | Clone, merge, filter, export, equals, hash                              |
| **test_comprehensive.py**      | —                 | Builder, validator, error handling, performance                         |
| **test_model_parity.py**       | —                 | TemplateProvMapper + CpmDocument mapping parity                         |
| **test_advanced_traversal.py** | —                 | Integration: template-based CpmDocument traversal                       |
| **test_mutability.py**         | —                 | CRUD workflow, template-to-advanced pipeline                            |

### ⏳ Pending Tests (5/14)

- **test_cpm_strategy.py** — TI/DS classification strategy
- **test_cpm_divided_document.py** — Divided document operations
- **test_cpm_ordered_document.py** — Ordered divided documents
- **test_cpm_merged_document.py** — Merged document operations
- **test_cpm_unordered_document.py** — Unordered (DEPRECATED in Java)

## API Compatibility Notes

### CpmDocument API

- Use `CpmDocument(prov_document)` not `CpmDocument.from_prov_document()`
- Use `to_prov_document()` not `get_prov_document()`
- Use `get_bundle_id()` not `get_bundle()`

### PROV Library API

- `doc.namespaces` is a set, use list comprehension: `[ns for ns in doc.namespaces if ns.prefix == 'cpm'][0]`
- QualifiedName: use `str(qname.namespace)` not `qname.namespace_uri`
- Import constants: `from prov.model import PROV, PROV_TYPE, PROV_ATTR_STARTTIME, PROV_ATTR_ENDTIME`
