"""
CPM Document - Combined Model using Mixins

This module combines all mixin classes to create the complete CpmDocument class.
"""

from typing import Optional, Any
from prov.model import ProvDocument

from src.graph.wrapper import ProvGraphWrapper
from src.cpm.ti_algorithm import TraversalInformationAlgorithm
from .core import CpmDocumentCoreMixin
from .traversal import CpmDocumentTraversalMixin
from .analysis import CpmDocumentAnalysisMixin
from .io import CpmDocumentIOMixin


class CpmDocument(
    CpmDocumentCoreMixin,
    CpmDocumentTraversalMixin,
    CpmDocumentAnalysisMixin,
    CpmDocumentIOMixin
):
    """
    Combined Provenance Model (CPM) Document.

    This class uses the mixin pattern to combine functionality from multiple focused classes:
    - CpmDocumentCoreMixin: Core CRUD operations for nodes and edges
    - CpmDocumentTraversalMixin: Graph traversal and path operations
    - CpmDocumentAnalysisMixin: Analysis, validation, and metrics
    - CpmDocumentIOMixin: I/O, serialization, and format conversion

    The CPM document represents a provenance graph that separates:
    - Traversal Information (TI): Structure for navigating the graph
    - Domain-Specific (DS): Actual domain data and provenance information

    Example:
        >>> doc = CpmDocument(prov_doc)
        >>> doc.add_node(node)
        >>> predecessors = doc.get_predecessors(node_id)
        >>> stats = doc.get_statistics()
        >>> template = doc.to_template()
    """

    def __init__(
        self,
        prov_document: Optional[ProvDocument] = None,
        ti_algorithm=None,
        bundle: Optional[Any] = None
    ):
        """
        Initialize CPM document.

        Args:
            prov_document: Optional PROV document to initialize from
            ti_algorithm: Optional TI algorithm (defaults to belongs_to_traversal_information)
            bundle: Optional bundle to work with
        """
        # Initialize graph wrapper
        if prov_document is not None:
            self.graph_wrapper = ProvGraphWrapper(prov_document)
        else:
            self.graph_wrapper = ProvGraphWrapper(ProvDocument())

        # Set TI algorithm - use an instance, not the class
        if ti_algorithm is None:
            self.ti_algorithm = TraversalInformationAlgorithm()
        else:
            self.ti_algorithm = ti_algorithm

        # Set bundle - call _get_bundle() to get the first bundle or the document
        if bundle is None:
            self._bundle = self._get_bundle()
        else:
            self._bundle = bundle

        # Bundle ID management
        self._custom_bundle_id = None

        # Track modifications
        self._modified = False

    def __repr__(self) -> str:
        """String representation of the document."""
        stats = self.get_statistics()
        return (
            f"CpmDocument("
            f"nodes={stats.get('total_nodes', 0)}, "
            f"edges={stats.get('total_edges', 0)}, "
            f"modified={self._modified}"
            f")"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.__repr__()


# Re-export for convenience
__all__ = ['CpmDocument']
