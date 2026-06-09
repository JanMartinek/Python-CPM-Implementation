"""
Graph utility functions and classes for advanced CPM operations.
"""

import copy
from typing import Dict, List, Set, Optional, Any, Tuple, Callable
from collections import defaultdict, deque
import hashlib
import json
from datetime import datetime

from ..cpm.model import CpmDocument
from ..graph import GraphNode
from ..cpm.constants import *


class GraphAnalyzer:
    """
    Advanced graph analysis utilities for CPM documents.
    """

    def __init__(self, cpm_doc: CpmDocument):
        self.cpm_doc = cpm_doc
        self._adjacency_cache = None
        self._metrics_cache = None

    def compute_graph_metrics(self) -> Dict[str, Any]:
        if self._metrics_cache:
            return self._metrics_cache

        nodes = self.cpm_doc.graph_wrapper.get_nodes()
        node_count = len(nodes)

        # Build adjacency representation for efficient computation
        adjacency = self._build_adjacency_list()

        metrics = {
            'node_count': node_count,
            'edge_count': self._count_edges(),
            'density': self._compute_density(adjacency, node_count),
            'connected_components': self._find_connected_components(adjacency),
            'diameter': self._compute_diameter(adjacency),
            'clustering_coefficient': self._compute_clustering_coefficient(adjacency),
            'centrality_distribution': self._compute_centrality_distribution(),
            'node_type_distribution': self._compute_node_type_distribution()
        }

        self._metrics_cache = metrics
        return metrics

    def find_critical_paths(self) -> List[List[str]]:
        critical_paths = []

        # Start from main activities
        main_activities = [n for n in self.cpm_doc.get_traversal_information_nodes()
                           if self.cpm_doc._has_cpm_type(n, CPM_MAIN_ACTIVITY)]

        for main_activity in main_activities:
            # Trace longest paths from main activity
            paths = self._find_longest_paths_from(main_activity)
            critical_paths.extend(paths)

        return critical_paths

    def detect_anomalies(self) -> Dict[str, List[str]]:
        anomalies = {
            'isolated_nodes': [],
            'high_degree_nodes': [],
            'missing_timestamps': [],
            'broken_chains': [],
            'unusual_patterns': []
        }

        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            node_id = str(node.identifier)

            # Check for isolation
            if self._is_isolated(node):
                anomalies['isolated_nodes'].append(node_id)

            # Check for unusually high degree
            degree = self._compute_node_degree(node)
            if degree > len(nodes) * 0.1:  # More than 10% of total nodes
                anomalies['high_degree_nodes'].append(node_id)

            # Check for missing timestamps in activities
            if hasattr(node.prov_entity, 'startTime') or hasattr(node.prov_entity, 'endTime'):
                if not self._has_valid_timestamps(node):
                    anomalies['missing_timestamps'].append(node_id)

        # Check for broken provenance chains
        anomalies['broken_chains'] = self._find_broken_chains()

        return anomalies

    def compute_influence_scores(self) -> Dict[str, float]:
        scores = {}
        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            # Influence based on out-degree and depth of influence
            direct_influence = len(self.cpm_doc.get_successors(node.identifier, max_depth=1))
            indirect_influence = len(self.cpm_doc.get_successors(node.identifier, max_depth=3))

            # Weighted score
            influence_score = direct_influence * 2 + indirect_influence * 0.5
            scores[str(node.identifier)] = influence_score

        return scores

    def _build_adjacency_list(self) -> Dict[str, Set[str]]:
        if self._adjacency_cache:
            return self._adjacency_cache

        adjacency = defaultdict(set)
        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            node_id = str(node.identifier)
            successors = self.cpm_doc.get_successors(node.identifier, max_depth=1)
            for successor in successors:
                adjacency[node_id].add(str(successor.identifier))

        self._adjacency_cache = dict(adjacency)
        return self._adjacency_cache

    def _count_edges(self) -> int:
        adjacency = self._build_adjacency_list()
        return sum(len(neighbors) for neighbors in adjacency.values())

    def _compute_density(self, adjacency: Dict[str, Set[str]], node_count: int) -> float:
        if node_count <= 1:
            return 0.0

        edge_count = sum(len(neighbors) for neighbors in adjacency.values())
        max_edges = node_count * (node_count - 1)
        return edge_count / max_edges if max_edges > 0 else 0.0

    def _find_connected_components(self, adjacency: Dict[str, Set[str]]) -> List[List[str]]:
        visited = set()
        components = []

        def dfs(node: str, component: List[str]):
            if node in visited:
                return
            visited.add(node)
            component.append(node)

            # Visit neighbors (both directions for undirected analysis)
            for neighbor in adjacency.get(node, []):
                dfs(neighbor, component)

            # Check reverse edges
            for other_node, neighbors in adjacency.items():
                if node in neighbors and other_node not in visited:
                    dfs(other_node, component)

        for node in adjacency:
            if node not in visited:
                component = []
                dfs(node, component)
                if component:
                    components.append(component)

        return components

    def _compute_diameter(self, adjacency: Dict[str, Set[str]]) -> int:
        max_distance = 0

        for start_node in adjacency:
            distances = self._bfs_distances(start_node, adjacency)
            if distances:
                max_distance = max(max_distance, max(distances.values()))

        return max_distance

    def _bfs_distances(self, start: str, adjacency: Dict[str, Set[str]]) -> Dict[str, int]:
        distances = {start: 0}
        queue = deque([start])

        while queue:
            current = queue.popleft()
            current_dist = distances[current]

            for neighbor in adjacency.get(current, []):
                if neighbor not in distances:
                    distances[neighbor] = current_dist + 1
                    queue.append(neighbor)

        return distances

    def _compute_clustering_coefficient(self, adjacency: Dict[str, Set[str]]) -> float:
        coefficients = []

        for node in adjacency:
            neighbors = list(adjacency.get(node, []))
            if len(neighbors) < 2:
                coefficients.append(0.0)
                continue

            # Count edges between neighbors
            edge_count = 0
            for i, neighbor1 in enumerate(neighbors):
                for neighbor2 in neighbors[i+1:]:
                    if neighbor2 in adjacency.get(neighbor1, []):
                        edge_count += 1

            # Clustering coefficient for this node
            max_edges = len(neighbors) * (len(neighbors) - 1) // 2
            coeff = edge_count / max_edges if max_edges > 0 else 0.0
            coefficients.append(coeff)

        return sum(coefficients) / len(coefficients) if coefficients else 0.0

    def _compute_centrality_distribution(self) -> Dict[str, Dict[str, float]]:
        nodes = self.cpm_doc.graph_wrapper.get_nodes()
        adjacency = self._build_adjacency_list()

        centrality = {
            'degree': {},
            'betweenness': {},
            'closeness': {},
            'priority_based': {}
        }

        # Degree centrality
        for node in nodes:
            node_id = str(node.identifier)
            degree = len(adjacency.get(node_id, []))
            centrality['degree'][node_id] = degree

        # Betweenness centrality (simplified)
        centrality['betweenness'] = self._compute_betweenness_centrality(adjacency)

        # Closeness centrality
        centrality['closeness'] = self._compute_closeness_centrality(adjacency)

        # Priority-based centrality (custom for CPM)
        centrality['priority_based'] = self._compute_priority_centrality()

        return centrality

    def _compute_betweenness_centrality(self, adjacency: Dict[str, Set[str]]) -> Dict[str, float]:
        centrality = defaultdict(float)
        nodes = list(adjacency.keys())

        for source in nodes:
            for target in nodes:
                if source != target:
                    paths = self._find_all_shortest_paths(source, target, adjacency)
                    if len(paths) > 0:
                        for path in paths:
                            for node in path[1:-1]:  # Exclude source and target
                                centrality[node] += 1.0 / len(paths)

        # Normalize
        n = len(nodes)
        if n > 2:
            norm_factor = 2.0 / ((n - 1) * (n - 2))
            for node in centrality:
                centrality[node] *= norm_factor

        return dict(centrality)

    def _compute_closeness_centrality(self, adjacency: Dict[str, Set[str]]) -> Dict[str, float]:
        centrality = {}

        for node in adjacency:
            distances = self._bfs_distances(node, adjacency)
            if len(distances) > 1:
                avg_distance = sum(distances.values()) / (len(distances) - 1)
                centrality[node] = 1.0 / avg_distance if avg_distance > 0 else 0.0
            else:
                centrality[node] = 0.0

        return centrality

    def _compute_priority_centrality(self) -> Dict[str, float]:
        centrality = {}
        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            node_id = str(node.identifier)
            priority_score = 0.0

            # Priority based on node type
            if self.cpm_doc._has_cpm_type(node, CPM_MAIN_ACTIVITY):
                priority_score += 10.0
            elif self.cpm_doc._has_cpm_type(node, CPM_SUB_ACTIVITY):
                priority_score += 5.0
            elif self.cpm_doc._has_cpm_type(node, CPM_STORAGE_ACTIVITY):
                priority_score += 3.0

            # Priority based on temporal information
            if hasattr(node.prov_entity, 'startTime'):
                priority_score += 2.0
            if hasattr(node.prov_entity, 'endTime'):
                priority_score += 2.0

            # Priority based on connections
            successors = self.cpm_doc.get_successors(node.identifier, max_depth=1)
            predecessors = self.cpm_doc.get_predecessors(node.identifier, max_depth=1)
            priority_score += len(successors) * 0.5 + len(predecessors) * 0.3

            centrality[node_id] = priority_score

        return centrality

    def _compute_node_type_distribution(self) -> Dict[str, int]:
        distribution = defaultdict(int)
        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            if hasattr(node.prov_entity, 'type'):
                node_type = str(node.prov_entity.type)
                distribution[node_type] += 1
            else:
                distribution['unknown'] += 1

        return dict(distribution)

    def _find_longest_paths_from(self, start_node) -> List[List[str]]:
        paths = []
        visited = set()
        current_path = []

        def dfs_longest(node, path):
            if str(node.identifier) in visited:
                return

            visited.add(str(node.identifier))
            path.append(str(node.identifier))

            successors = self.cpm_doc.get_successors(node.identifier, max_depth=1)
            if not successors:
                # Leaf node - save path
                paths.append(path.copy())
            else:
                for successor in successors:
                    dfs_longest(successor, path)

            path.pop()
            visited.remove(str(node.identifier))

        dfs_longest(start_node, current_path)

        # Return only the longest paths
        if paths:
            max_length = max(len(path) for path in paths)
            return [path for path in paths if len(path) == max_length]

        return []

    def _is_isolated(self, node) -> bool:
        successors = self.cpm_doc.get_successors(node.identifier, max_depth=1)
        predecessors = self.cpm_doc.get_predecessors(node.identifier, max_depth=1)
        return len(successors) == 0 and len(predecessors) == 0

    def _compute_node_degree(self, node) -> int:
        successors = self.cpm_doc.get_successors(node.identifier, max_depth=1)
        predecessors = self.cpm_doc.get_predecessors(node.identifier, max_depth=1)
        return len(successors) + len(predecessors)

    def _has_valid_timestamps(self, node) -> bool:
        has_start = hasattr(node.prov_entity, 'startTime') and node.prov_entity.startTime is not None
        has_end = hasattr(node.prov_entity, 'endTime') and node.prov_entity.endTime is not None
        return has_start or has_end

    def _find_broken_chains(self) -> List[str]:
        broken = []
        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            if self.cpm_doc._has_cpm_type(node, CPM_MAIN_ACTIVITY):
                # Main activities should have proper chains
                successors = self.cpm_doc.get_successors(node.identifier, max_depth=1)
                if not successors:
                    broken.append(str(node.identifier))

        return broken

    def _find_all_shortest_paths(self, source: str, target: str, adjacency: Dict[str, Set[str]]) -> List[List[str]]:
        if source == target:
            return [[source]]

        paths = []
        queue = deque([(source, [source])])
        visited_distances = {source: 0}
        target_distance = None

        while queue:
            current, path = queue.popleft()
            current_distance = len(path) - 1

            if target_distance is not None and current_distance > target_distance:
                break

            for neighbor in adjacency.get(current, []):
                new_path = path + [neighbor]
                new_distance = len(new_path) - 1

                if neighbor == target:
                    if target_distance is None:
                        target_distance = new_distance
                    if new_distance == target_distance:
                        paths.append(new_path)
                elif neighbor not in visited_distances or visited_distances[neighbor] >= new_distance:
                    visited_distances[neighbor] = new_distance
                    queue.append((neighbor, new_path))

        return paths


class PriorityBasedScheduler:
    """
    Priority-based node scheduler for CPM graph processing.
    Helps resolve issues with node priority and execution order.
    """

    def __init__(self, cpm_doc: CpmDocument):
        self.cpm_doc = cpm_doc
        self.priority_cache = {}

    def compute_node_priorities(self) -> Dict[str, float]:
        if self.priority_cache:
            return self.priority_cache

        priorities = {}
        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            node_id = str(node.identifier)
            priority = self._calculate_node_priority(node)
            priorities[node_id] = priority

        self.priority_cache = priorities
        return priorities

    def get_execution_order(self) -> List[str]:
        priorities = self.compute_node_priorities()

        # Topological sort with priority
        in_degree = self._compute_in_degrees()
        queue = []

        # Start with nodes that have no dependencies, sorted by priority
        for node_id, degree in in_degree.items():
            if degree == 0:
                queue.append((priorities.get(node_id, 0), node_id))

        queue.sort(reverse=True)  # Higher priority first
        execution_order = []

        while queue:
            _, current_id = queue.pop(0)
            execution_order.append(current_id)

            # Find node by ID
            current_node = None
            for node in self.cpm_doc.graph_wrapper.get_nodes():
                if str(node.identifier) == current_id:
                    current_node = node
                    break

            if current_node:
                successors = self.cpm_doc.get_successors(current_node.identifier, max_depth=1)
                for successor in successors:
                    successor_id = str(successor.identifier)
                    in_degree[successor_id] -= 1

                    if in_degree[successor_id] == 0:
                        priority = priorities.get(successor_id, 0)
                        # Insert in priority order
                        inserted = False
                        for i, (p, _) in enumerate(queue):
                            if priority > p:
                                queue.insert(i, (priority, successor_id))
                                inserted = True
                                break
                        if not inserted:
                            queue.append((priority, successor_id))

        return execution_order

    def find_lowest_priority_nodes(self, count: int = 5) -> List[Tuple[str, float]]:
        priorities = self.compute_node_priorities()

        # Sort by priority (ascending for lowest)
        sorted_priorities = sorted(priorities.items(), key=lambda x: x[1])

        return sorted_priorities[:count]

    def find_highest_priority_nodes(self, count: int = 5) -> List[Tuple[str, float]]:
        priorities = self.compute_node_priorities()

        # Sort by priority (descending for highest)
        sorted_priorities = sorted(priorities.items(), key=lambda x: x[1], reverse=True)

        return sorted_priorities[:count]

    def diagnose_priority_issues(self) -> Dict[str, Any]:
        priorities = self.compute_node_priorities()

        diagnosis = {
            'zero_priority_nodes': [],
            'negative_priority_nodes': [],
            'priority_conflicts': [],
            'dependency_violations': []
        }

        # Find problematic priorities
        for node_id, priority in priorities.items():
            if priority == 0:
                diagnosis['zero_priority_nodes'].append(node_id)
            elif priority < 0:
                diagnosis['negative_priority_nodes'].append(node_id)

        # Check for dependency violations
        diagnosis['dependency_violations'] = self._find_priority_dependency_violations()

        # Check for priority conflicts
        diagnosis['priority_conflicts'] = self._find_priority_conflicts()

        return diagnosis

    def _calculate_node_priority(self, node) -> float:
        priority = 0.0

        # Base priority by type
        if self.cpm_doc._has_cpm_type(node, CPM_MAIN_ACTIVITY):
            priority += 100.0
        elif self.cpm_doc._has_cpm_type(node, CPM_SUB_ACTIVITY):
            priority += 50.0
        elif self.cpm_doc._has_cpm_type(node, CPM_STORAGE_ACTIVITY):
            priority += 30.0
        else:
            priority += 10.0

        # Temporal priority (earlier activities get higher priority)
        if hasattr(node.prov_entity, 'startTime'):
            try:
                # Earlier start times get higher priority
                start_time = node.prov_entity.startTime
                if start_time:
                    # Use timestamp for priority (reversed so earlier = higher)
                    priority += 1000.0 / (1.0 + hash(str(start_time)) % 1000)
            except (AttributeError, TypeError, ValueError):
                pass

        # Dependency priority (nodes with more dependencies get higher priority)
        predecessors = self.cpm_doc.get_predecessors(node.identifier, max_depth=1)
        successors = self.cpm_doc.get_successors(node.identifier, max_depth=1)

        priority += len(predecessors) * 2.0  # More dependencies = higher priority
        priority += len(successors) * 1.0    # More dependents = higher priority

        # Critical path priority
        if self._is_on_critical_path(node):
            priority += 50.0

        return priority

    def _compute_in_degrees(self) -> Dict[str, int]:
        in_degrees = defaultdict(int)
        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            node_id = str(node.identifier)
            in_degrees[node_id] = 0  # Initialize

        for node in nodes:
            successors = self.cpm_doc.get_successors(node.identifier, max_depth=1)
            for successor in successors:
                successor_id = str(successor.identifier)
                in_degrees[successor_id] += 1

        return dict(in_degrees)

    def _is_on_critical_path(self, node) -> bool:
        successors = self.cpm_doc.get_successors(node.identifier, max_depth=3)
        return len(successors) > 2  # Nodes with many downstream dependencies

    def _find_priority_dependency_violations(self) -> List[Dict[str, str]]:
        violations = []
        priorities = self.compute_node_priorities()
        nodes = self.cpm_doc.graph_wrapper.get_nodes()

        for node in nodes:
            node_id = str(node.identifier)
            node_priority = priorities.get(node_id, 0)

            predecessors = self.cpm_doc.get_predecessors(node.identifier, max_depth=1)
            for pred in predecessors:
                pred_id = str(pred.identifier)
                pred_priority = priorities.get(pred_id, 0)

                if pred_priority > node_priority:
                    violations.append({
                        'dependent': node_id,
                        'dependency': pred_id,
                        'dependent_priority': node_priority,
                        'dependency_priority': pred_priority
                    })

        return violations

    def _find_priority_conflicts(self) -> List[Dict[str, Any]]:
        conflicts = []
        priorities = self.compute_node_priorities()

        # Group by similar priority ranges
        priority_groups = defaultdict(list)
        for node_id, priority in priorities.items():
            # Group by priority ranges of 10
            group_key = int(priority // 10) * 10
            priority_groups[group_key].append((node_id, priority))

        # Find groups with multiple high-priority nodes
        for group_key, nodes in priority_groups.items():
            if len(nodes) > 3 and group_key >= 50:  # Multiple high-priority nodes
                conflicts.append({
                    'priority_range': f"{group_key}-{group_key + 9}",
                    'conflicting_nodes': [{'id': nid, 'priority': p} for nid, p in nodes]
                })

        return conflicts
