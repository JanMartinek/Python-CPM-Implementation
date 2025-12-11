"""
CPM Model - Compatibility Module

This module re-exports all CPM model classes for backward compatibility.
The implementation has been split into multiple modules:

- exceptions.py: Exception classes (CpmDocumentError, NodeNotFoundError, etc.)
- template_mapper.py: TemplateProvMapper for converting templates to PROV
- ti_algorithm.py: TraversalInformationAlgorithm for TI/DS separation
- document.py: CpmDocument main class (2536 lines)
- builder.py: CpmDocumentBuilder and CpmValidator

Import from this module to maintain compatibility with existing code.
"""

# Re-export all exception classes
from .exceptions import (
    CpmDocumentError,
    NodeNotFoundError,
    MultipleNodesError,
    EdgeNotFoundError,
    InvalidOperationError,
    MultipleEdgesError
)

# Re-export template mapper
from .template_mapper import TemplateProvMapper

# Re-export TI algorithm
from .ti_algorithm import TraversalInformationAlgorithm

# Re-export main document class from the model subdirectory
from .model import CpmDocument

# Re-export builder
from .builder import CpmDocumentBuilder

# Re-export validator
from .validation import CpmValidator

# Define what gets exported with "from cpm.model import *"
__all__ = [
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
    'CpmDocument',
    'CpmDocumentBuilder',
    'CpmValidator',
]
