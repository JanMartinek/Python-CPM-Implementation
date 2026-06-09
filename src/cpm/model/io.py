"""
CPM Document - I/O Operations Mixin

I/O, serialization, and document manipulation operations.
"""

from typing import Dict, List, Optional, Any, Set, Union, Tuple
from prov.model import ProvDocument, ProvBundle, ProvEntity, ProvActivity, ProvAgent, ProvRecord
from prov.identifier import QualifiedName, Namespace
from prov.constants import PROV_TYPE, PROV_LABEL, PROV_VALUE
import copy

from src.graph.node import GraphNode
from src.graph.wrapper import ProvGraphWrapper
from src.cpm.constants import *
from src.cpm.template import CpmBundleTemplate
from src.cpm.template_mapper import TemplateProvMapper
from src.cpm.ti_algorithm import TraversalInformationAlgorithm
from src.cpm.exceptions import *


class CpmDocumentIOMixin:
    """
    Mixin providing I/O and serialization operations for CPM documents.

    This mixin handles:
    - Template conversion
    - Document cloning and merging
    - Filtering and subgraph extraction
    - Format export
    - Document comparison

    Note: This mixin expects the following attributes to be available:
    - self.graph_wrapper: ProvGraphWrapper instance
    - self.ti_algorithm: TI algorithm instance
    - self._bundle: Current bundle
    - self._modified: Modification flag
    """

    @classmethod
    def from_template(cls, template: CpmBundleTemplate,
                      domain_specific_doc: Optional[ProvDocument] = None) -> 'CpmDocument':
        """
        Create CPM document from template and optional domain-specific provenance.

        Args:
            template: Traversal information template
            domain_specific_doc: Optional domain-specific provenance document

        Returns:
            CpmDocument instance
        """
        mapper = TemplateProvMapper()
        ti_doc = mapper.map_to_document(template)

        if domain_specific_doc:
            # Merge traversal information with domain-specific provenance
            ti_doc.update(domain_specific_doc)

        # Create CpmDocument and ensure graph wrapper is properly initialized
        cpm_doc = cls(ti_doc)

        # Force re-initialization of graph wrapper to ensure all nodes are properly loaded
        cpm_doc._reinitialize_graph_wrapper()

        return cpm_doc

    def clone(self) -> 'CpmDocument':
        """
        Create a deep copy of this CPM document.

        Returns:
            A new CpmDocument instance with copied content
        """
        # Create a deep copy of the PROV document
        prov_doc = self.to_prov_document()
        cloned_doc = copy.deepcopy(prov_doc)
        return self.__class__(cloned_doc)

    def merge_with(self, other: 'CpmDocument',
                   conflict_resolution: str = 'keep_both') -> 'CpmDocument':
        """
        Merge this document with another CPM document.

        Args:
            other: The other CPM document to merge with
            conflict_resolution: How to handle conflicts ('keep_both', 'keep_first', 'keep_second')

        Returns:
            A new merged CpmDocument

        Raises:
            InvalidOperationError: If conflict resolution strategy is invalid
        """
        if conflict_resolution not in ['keep_both', 'keep_first', 'keep_second']:
            raise InvalidOperationError(f"Invalid conflict resolution strategy: {conflict_resolution}")

        # Start with a copy of this document
        merged_doc = self.clone()
        other_prov_doc = other.to_prov_document()

        # Merge the documents based on conflict resolution
        if conflict_resolution == 'keep_both':
            # Add all records from other document, renaming conflicts
            merged_doc._merge_records_keep_both(other_prov_doc)
        elif conflict_resolution == 'keep_first':
            # Only add non-conflicting records from other document
            merged_doc._merge_records_keep_first(other_prov_doc)
        elif conflict_resolution == 'keep_second':
            # Replace conflicting records with ones from other document
            merged_doc._merge_records_keep_second(other_prov_doc)

        return merged_doc

    def filter_by_time_range(self, start_time: Optional[Any] = None,
                             end_time: Optional[Any] = None) -> 'CpmDocument':
        """
        Filter document to include only elements within a time range.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            A new filtered CpmDocument
        """
        filtered_doc = self.__class__(ProvDocument())

        for node in self.graph_wrapper.get_nodes():
            # Check if node has time attributes within range
            include_node = True

            try:
                if isinstance(node.prov_entity, ProvActivity):
                    start_attr = node.get_prov_attribute('prov:startTime')
                    end_attr = node.get_prov_attribute('prov:endTime')

                    if start_time and start_attr:
                        if start_attr[0] < start_time:
                            include_node = False

                    if end_time and end_attr:
                        if end_attr[0] > end_time:
                            include_node = False
            except (AttributeError, IndexError, TypeError, ValueError):
                pass

            if include_node:
                # Add node to filtered document
                node_type = node.node_type_name

                # Extract attributes
                attributes = {}
                for attr_name, attr_value in node.prov_entity.attributes:
                    if attr_name != PROV_TYPE:
                        attributes[str(attr_name)] = attr_value

                prov_types = node.get_prov_attribute(str(PROV_TYPE))
                prov_type = prov_types[0] if prov_types else None

                try:
                    filtered_doc.add_node(node_type, node.identifier, attributes, prov_type)
                except (AttributeError, TypeError, ValueError, InvalidOperationError, CpmDocumentError):
                    pass  # Skip if unable to add

        return filtered_doc

    def export_to_formats(self) -> Dict[str, str]:
        """
        Export the document to various formats.

        Returns:
            Dictionary with format names as keys and serialized content as values
        """
        prov_doc = self.to_prov_document()
        exports = {}

        try:
            # PROV-N format
            exports['provn'] = prov_doc.get_provn()
        except (AttributeError, TypeError, ValueError, NotImplementedError):
            exports['provn'] = "Error: Could not export to PROV-N"

        try:
            # JSON format
            exports['json'] = prov_doc.serialize(format='json')
        except (AttributeError, TypeError, ValueError, NotImplementedError):
            exports['json'] = "Error: Could not export to JSON"

        try:
            # XML format
            exports['xml'] = prov_doc.serialize(format='xml')
        except (AttributeError, TypeError, ValueError, NotImplementedError):
            exports['xml'] = "Error: Could not export to XML"

        return exports

    def _get_existing_identifiers(self) -> Set[str]:
        """Return a set of stringified identifiers for all nodes in this document."""
        return {str(n.identifier) for n in self.get_all_nodes()}

    def _add_records_from(self, other_doc: ProvDocument, skip_existing: bool = False):
        """
        Add records from *other_doc* into this document.

        Args:
            other_doc: Source PROV document whose records will be imported.
            skip_existing: If True, skip records whose identifier already
                           exists in this document (used by keep_first).
        """
        existing_ids = self._get_existing_identifiers() if skip_existing else set()

        for record in other_doc.get_records():
            record_id = str(record.identifier) if hasattr(record, 'identifier') and record.identifier else None
            if skip_existing and record_id and record_id in existing_ids:
                continue
            try:
                if isinstance(record, ProvEntity):
                    self.add_node('entity', record.identifier,
                                  {str(k): v for k, v in record.attributes if k != PROV_TYPE})
                elif isinstance(record, ProvActivity):
                    self.add_node('activity', record.identifier,
                                  {str(k): v for k, v in record.attributes if k != PROV_TYPE})
                elif isinstance(record, ProvAgent):
                    self.add_node('agent', record.identifier,
                                  {str(k): v for k, v in record.attributes if k != PROV_TYPE})
            except (AttributeError, TypeError, ValueError, InvalidOperationError, CpmDocumentError):
                pass  # Skip records that cannot be added (e.g. duplicates)

        # Also import records from bundles inside other_doc (only ProvDocument has bundles)
        if isinstance(other_doc, ProvDocument):
            for bundle in other_doc.bundles:
                self._add_records_from(bundle, skip_existing=skip_existing)

    def _merge_records_keep_both(self, other_doc: ProvDocument):
        """
        Merge records keeping both in case of conflicts.

        All records from *other_doc* are added. If an identifier already
        exists the new record is silently skipped (PROV does not allow true
        duplicates), but non-conflicting records are always added.
        """
        self._add_records_from(other_doc, skip_existing=False)

    def _merge_records_keep_first(self, other_doc: ProvDocument):
        """
        Merge records keeping first (this document's) in case of conflicts.

        Only records whose identifier does NOT already exist in this
        document are imported from *other_doc*.
        """
        self._add_records_from(other_doc, skip_existing=True)

    def _merge_records_keep_second(self, other_doc: ProvDocument):
        """
        Merge records keeping second (other document's) in case of conflicts.

        Conflicting records in this document are removed first, then all
        records from *other_doc* are added.
        """
        other_ids: Set[str] = set()
        for record in other_doc.get_records():
            if hasattr(record, 'identifier') and record.identifier:
                other_ids.add(str(record.identifier))
        for bundle in other_doc.bundles:
            for record in bundle.get_records():
                if hasattr(record, 'identifier') and record.identifier:
                    other_ids.add(str(record.identifier))

        # Remove conflicting nodes from this document
        for node in list(self.get_all_nodes()):
            if str(node.identifier) in other_ids:
                try:
                    self.remove_node(node.identifier)
                except (AttributeError, TypeError, ValueError, InvalidOperationError, CpmDocumentError):
                    pass

        self._add_records_from(other_doc, skip_existing=False)

    def equals(self, other: 'CpmDocument') -> bool:
        """
        Check equality with another CPM document.
        """
        if not isinstance(other, self.__class__):
            return False

        # Compare basic properties
        if self.get_bundle_id() != other.get_bundle_id():
            return False

        # Compare node counts
        self_stats = self.get_statistics()
        other_stats = other.get_statistics()

        for key in ['total_nodes', 'entities', 'activities', 'agents']:
            if self_stats.get(key, 0) != other_stats.get(key, 0):
                return False

        # Compare edge counts
        self_edges = len(self.get_all_edges())
        other_edges = len(other.get_all_edges())

        return self_edges == other_edges

    def hash_code(self) -> int:
        """
        Generate hash code for the document.
        """
        bundle_id = self.get_bundle_id() or ""
        stats = self.get_statistics()

        # Create hash from key document properties
        hash_components = [
            bundle_id,
            stats.get('total_nodes', 0),
            stats.get('entities', 0),
            stats.get('activities', 0),
            stats.get('agents', 0),
            len(self.get_all_edges())
        ]

        return hash(tuple(hash_components))
