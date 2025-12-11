"""
CPM Exceptions

Exception classes for CPM document operations.
"""


class CpmDocumentError(Exception):
    """Base exception for CPM document operations"""
    pass


class NodeNotFoundError(CpmDocumentError):
    """Raised when a requested node is not found"""
    pass


class MultipleNodesError(CpmDocumentError):
    """Raised when multiple nodes are found where only one is expected"""
    pass


class EdgeNotFoundError(CpmDocumentError):
    """Raised when a requested edge is not found"""
    pass


class InvalidOperationError(CpmDocumentError):
    """Raised when an invalid operation is attempted"""
    pass


class MultipleEdgesError(CpmDocumentError):
    """Raised when multiple edges are found where only one is expected"""
    pass
