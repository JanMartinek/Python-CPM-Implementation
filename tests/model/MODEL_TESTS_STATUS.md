# CPM Model Tests - Java to Python Mapping

## Summary

**Status: 9/14 (64%) Complete**

Last Updated: 2024

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

## Python Model Tests - Current Status

### ✅ Completed Core Tests (9/14)
- **test_cpm_factory.py** - ✅ COMPLETE (6 test classes, 20+ tests)
- **test_cpm_prov_factory.py** - ✅ COMPLETE (2 test classes, 18+ tests)
- **test_cpm_document_constructor.py** - ✅ COMPLETE (6 test classes, ~25 tests)
- **test_cpm_document_modification.py** - ✅ COMPLETE (6 test classes)
- **test_cpm_document_removal.py** - ✅ COMPLETE (5 test classes)
- **test_cpm_document_equals.py** - ✅ COMPLETE (5 test classes)
- **test_cpm_document_additional.py** - ✅ COMPLETE (5 test classes)
- **test_cpm_document_influence.py** - ✅ COMPLETE (4 test classes)
- **test_cpm_utilities.py** - ✅ COMPLETE (5 test classes)

### ⏳ Pending Tests (5/14)
- **test_cpm_strategy.py** - ⏳ PENDING (TI/DS classification strategy)
- **test_cpm_divided_document.py** - ⏳ PENDING (Divided document operations)
- **test_cpm_ordered_document.py** - ⏳ PENDING (Ordered divided documents)
- **test_cpm_merged_document.py** - ⏳ PENDING (Merged document operations)
- **test_cpm_unordered_document.py** - ⏳ PENDING (Unordered - DEPRECATED)

### 📁 Other Test Files (moved to model folder)
- test_model_parity.py - General model parity tests (MOVED)
- test_java_parity_comprehensive.py - Comprehensive Java parity (MOVED)

## API Compatibility Notes

### CpmDocument API
- Use `CpmDocument(prov_document)` not `CpmDocument.from_prov_document()`
- Use `to_prov_document()` not `get_prov_document()`
- Use `get_bundle_id()` not `get_bundle()`

### PROV Library API
- `doc.namespaces` is a set, use list comprehension: `[ns for ns in doc.namespaces if ns.prefix == 'cpm'][0]`
- QualifiedName: use `str(qname.namespace)` not `qname.namespace_uri`
- Import constants: `from prov.model import PROV, PROV_TYPE, PROV_ATTR_STARTTIME, PROV_ATTR_ENDTIME`

## Summary

### Completed: 9/14 model test files (64%)
✅ Core factory and document operation tests complete
✅ Factory patterns, PROV factory, constructor tests complete
✅ Modification, removal, equality, additional, influence, utilities tests complete

### Remaining: 5/14 model test files (36%)
⏳ Strategy and advanced document tests pending

## Priority Actions

1. **MEDIUM PRIORITY - Strategy Pattern**:
   - Implement test_cpm_strategy.py (TI/DS classification)

2. **LOWER PRIORITY - Divided/Merged Documents**:
   - Implement test_cpm_merged_document.py
   - Implement test_cpm_ordered_document.py
   - Implement test_cpm_divided_document.py
   - Implement test_cpm_unordered_document.py (DEPRECATED in Java)

## Notes
- Created tests/model/ folder for organized model test structure
- 9/14 core model tests now complete with proper API usage
- All tests use pytest with class-based organization
- Fixed all lint errors and API compatibility issues
- Java tests provide comprehensive reference implementation

- Current tests in tests/ folder (test_model_parity.py, test_java_parity_comprehensive.py, etc.) 
  provide some coverage but are not organized by Java test structure
