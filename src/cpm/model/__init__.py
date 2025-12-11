"""
CPM Model Package

This package contains the CPM document implementation using the mixin pattern.

Structure:
- core_mixin.py: Core CRUD operations (56 methods)
- traversal_mixin.py: Graph traversal operations (7 methods)
- analysis_mixin.py: Analysis and validation operations (13 methods)
- io_mixin.py: I/O and serialization operations (11 methods)
- cpm_document.py: Combined class using all mixins

The mixin pattern allows logical separation while maintaining a single CpmDocument class.
"""

from .cpm_document import CpmDocument

# Re-export exception classes from parent module
from ..exceptions import (
    CpmDocumentError,
    NodeNotFoundError,
    MultipleNodesError,
    EdgeNotFoundError,
    InvalidOperationError,
    MultipleEdgesError
)

# Re-export template mapper from parent module
from ..template_mapper import TemplateProvMapper

# Re-export TI algorithm from parent module
from ..ti_algorithm import TraversalInformationAlgorithm

# Re-export builder from parent module
from ..builder import CpmDocumentBuilder

# Re-export validator from parent module
from ..validation import CpmValidator

__all__ = [
    'CpmDocument',
    # Exceptions
    'CpmDocumentError',
    'NodeNotFoundError',
    'MultipleNodesError',
    'EdgeNotFoundError',
    'InvalidOperationError',
    'MultipleEdgesError',
    # Classes
    'TemplateProvMapper',
    'TraversalInformationAlgorithm',
    'CpmDocumentBuilder',
    'CpmValidator',
]
