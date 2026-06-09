"""
Tests for CpmDocumentIOMixin – clone, merge, filter, subgraph, export, equals, hash.
"""

import pytest
from prov.model import ProvDocument
from src.cpm.model import CpmDocument
from src.cpm.builder import CpmDocumentBuilder
from src.cpm.exceptions import InvalidOperationError


def _build_doc():
    builder = CpmDocumentBuilder("test:bundle")
    doc = (builder
           .with_main_activity("test:main", start_time="2024-01-01T00:00:00Z")
           .with_backward_connector("test:bc1", "test:src", "hash1")
           .with_forward_connector("test:fc1", "test:tgt", "hash2")
           .with_sender_agent("test:sender")
           .with_receiver_agent("test:receiver")
           .build())
    doc.add_node('entity', 'test:e1', {'label': 'Entity1'})
    doc.add_node('entity', 'test:e2', {'label': 'Entity2'})
    doc.add_edge('used', 'test:main', 'test:e1')
    doc.add_edge('wasgeneratedby', 'test:main', 'test:e2')
    return doc


class TestClone:
    def test_clone_returns_new_instance(self):
        doc = _build_doc()
        cloned = doc.clone()
        assert cloned is not doc
        assert isinstance(cloned, CpmDocument)

    def test_clone_preserves_node_count(self):
        doc = _build_doc()
        cloned = doc.clone()
        assert len(cloned.get_all_nodes()) == len(doc.get_all_nodes())

    def test_clone_is_independent(self):
        doc = _build_doc()
        cloned = doc.clone()
        cloned.add_node('entity', 'test:extra')
        assert doc.get_node('test:extra') is None


class TestMerge:
    def test_merge_invalid_strategy_raises(self):
        doc = _build_doc()
        doc2 = _build_doc()
        with pytest.raises(InvalidOperationError):
            doc.merge_with(doc2, conflict_resolution='invalid')

    def test_merge_keep_both(self):
        doc = _build_doc()
        doc2 = _build_doc()
        doc2.add_node('entity', 'test:extra_entity')
        merged = doc.merge_with(doc2, conflict_resolution='keep_both')
        assert isinstance(merged, CpmDocument)
        # The extra entity from doc2 should be present in the merge
        assert merged.get_node('test:extra_entity') is not None

    def test_merge_keep_first(self):
        doc = _build_doc()
        doc2 = _build_doc()
        doc2.add_node('entity', 'test:unique_in_doc2')
        merged = doc.merge_with(doc2, conflict_resolution='keep_first')
        assert isinstance(merged, CpmDocument)
        # Non-conflicting node from doc2 should be present
        assert merged.get_node('test:unique_in_doc2') is not None

    def test_merge_keep_second(self):
        doc = _build_doc()
        doc2 = _build_doc()
        doc2.add_node('entity', 'test:unique_in_doc2')
        merged = doc.merge_with(doc2, conflict_resolution='keep_second')
        assert isinstance(merged, CpmDocument)
        assert merged.get_node('test:unique_in_doc2') is not None


class TestFilterByTimeRange:
    def test_filter_returns_cpm_document(self):
        doc = _build_doc()
        filtered = doc.filter_by_time_range()
        assert isinstance(filtered, CpmDocument)

    def test_filter_no_constraints_returns_document(self):
        doc = _build_doc()
        filtered = doc.filter_by_time_range()
        # Without time constraints, returns a CpmDocument (may be empty)
        assert isinstance(filtered, CpmDocument)

    def test_filter_with_start_time(self):
        doc = _build_doc()
        filtered = doc.filter_by_time_range(start_time="2023-01-01T00:00:00Z")
        assert isinstance(filtered, CpmDocument)

    def test_filter_with_end_time(self):
        doc = _build_doc()
        filtered = doc.filter_by_time_range(end_time="2025-01-01T00:00:00Z")
        assert isinstance(filtered, CpmDocument)


class TestExportToFormats:
    def test_export_returns_dict(self):
        doc = _build_doc()
        exports = doc.export_to_formats()
        assert isinstance(exports, dict)

    def test_export_has_provn(self):
        doc = _build_doc()
        exports = doc.export_to_formats()
        assert 'provn' in exports
        assert isinstance(exports['provn'], str)

    def test_export_has_json(self):
        doc = _build_doc()
        exports = doc.export_to_formats()
        assert 'json' in exports

    def test_export_has_xml(self):
        doc = _build_doc()
        exports = doc.export_to_formats()
        assert 'xml' in exports


class TestEquals:
    def test_equal_documents(self):
        doc1 = _build_doc()
        doc2 = _build_doc()
        assert doc1.equals(doc2)

    def test_not_equal_to_none(self):
        doc = _build_doc()
        assert not doc.equals(None)

    def test_not_equal_to_string(self):
        doc = _build_doc()
        assert not doc.equals("not a doc")

    def test_different_documents_not_equal(self):
        doc1 = _build_doc()
        doc2 = _build_doc()
        doc2.add_node('entity', 'test:extra')
        assert not doc1.equals(doc2)


class TestHashCode:
    def test_hash_code_is_int(self):
        doc = _build_doc()
        h = doc.hash_code()
        assert isinstance(h, int)

    def test_same_doc_same_hash(self):
        doc = _build_doc()
        assert doc.hash_code() == doc.hash_code()

    def test_equal_docs_same_hash(self):
        doc1 = _build_doc()
        doc2 = _build_doc()
        assert doc1.hash_code() == doc2.hash_code()
