"""
Graph Package

This package contains the graph wrapper and related classes for working with
PROV documents as node-edge graphs.

Main classes:
- ProvGraphWrapper: Main graph interface wrapping PROV documents
- GraphNode: Node representation in the graph
- GraphEdge: Edge representation in the graph
- ICpmFactory: Abstract factory for creating CPM structures
- DividedCpmFactory: Factory for divided graph structures
- MergedCpmFactory: Factory for merged graph structures
"""

from .wrapper import ProvGraphWrapper
from .node import GraphNode, DividedGraphNode, MergedGraphNode
from .edge import GraphEdge, DividedGraphEdge, MergedGraphEdge, EdgeFilter, EdgeBuilder
from .factory import (
    ICpmFactory,
    DividedCpmFactory,
    MergedCpmFactory,
    CpmFactoryManager
)

__all__ = [
    # Main classes
    'ProvGraphWrapper',
    'GraphNode',
    'GraphEdge',
    # Node types
    'DividedGraphNode',
    'MergedGraphNode',
    # Edge types
    'DividedGraphEdge',
    'MergedGraphEdge',
    'EdgeFilter',
    'EdgeBuilder',
    # Factories
    'ICpmFactory',
    'DividedCpmFactory',
    'MergedCpmFactory',
    'CpmFactoryManager',
]
