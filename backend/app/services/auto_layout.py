"""
Auto-Layout Service for Flow Network Visualization

Provides automatic layout algorithms for flow network nodes:
- Hierarchical layout (sources → processing → sinks)
- Force-directed layout
- Grid-based layout
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class NodePosition:
    """Node position in the layout."""
    node_id: str
    x: float
    y: float
    width: float = 120
    height: float = 60


@dataclass
class LayoutResult:
    """Result of auto-layout calculation."""
    positions: List[NodePosition]
    bounds: Dict[str, float]  # minX, minY, maxX, maxY
    algorithm: str


class AutoLayoutService:
    """
    Automatic layout algorithms for flow networks.
    """
    
    def __init__(self):
        self.node_spacing_x = 180
        self.node_spacing_y = 100
        self.margin = 50
    
    def hierarchical_layout(
        self,
        nodes: List[Dict],
        edges: List[Dict]
    ) -> LayoutResult:
        """
        Layout nodes in hierarchical layers based on flow direction.
        
        Sources (no incoming edges) on left, sinks (no outgoing) on right.
        """
        # Build adjacency lists
        outgoing = {n['node_id']: [] for n in nodes}
        incoming = {n['node_id']: [] for n in nodes}
        
        for edge in edges:
            source = edge.get('source_node_id') or edge.get('from_node_id')
            target = edge.get('target_node_id') or edge.get('to_node_id')
            if source in outgoing:
                outgoing[source].append(target)
            if target in incoming:
                incoming[target].append(source)
        
        # Assign layers using longest path algorithm
        layers = self._assign_layers(nodes, outgoing, incoming)
        
        # Position nodes within layers
        positions = []
        layer_counts = {}
        
        for node in nodes:
            layer = layers.get(node['node_id'], 0)
            if layer not in layer_counts:
                layer_counts[layer] = 0
            
            x = self.margin + layer * self.node_spacing_x
            y = self.margin + layer_counts[layer] * self.node_spacing_y
            
            positions.append(NodePosition(
                node_id=node['node_id'],
                x=x,
                y=y
            ))
            
            layer_counts[layer] += 1
        
        # Center layers vertically
        positions = self._center_layers(positions, layers)
        
        return LayoutResult(
            positions=positions,
            bounds=self._calculate_bounds(positions),
            algorithm='hierarchical'
        )
    
    def _assign_layers(
        self,
        nodes: List[Dict],
        outgoing: Dict,
        incoming: Dict
    ) -> Dict[str, int]:
        """Assign layer numbers using topological sort."""
        layers = {}
        visited = set()
        
        # Find sources (no incoming edges)
        sources = [n['node_id'] for n in nodes if not incoming.get(n['node_id'])]
        
        # If no clear sources, start with first node
        if not sources:
            sources = [nodes[0]['node_id']] if nodes else []
        
        # BFS from sources
        queue = [(s, 0) for s in sources]
        
        while queue:
            node_id, layer = queue.pop(0)
            
            if node_id in visited:
                layers[node_id] = max(layers.get(node_id, 0), layer)
                continue
            
            visited.add(node_id)
            layers[node_id] = layer
            
            for target in outgoing.get(node_id, []):
                queue.append((target, layer + 1))
        
        # Handle unvisited nodes
        for node in nodes:
            if node['node_id'] not in layers:
                layers[node['node_id']] = 0
        
        return layers
    
    def _center_layers(
        self,
        positions: List[NodePosition],
        layers: Dict[str, int]
    ) -> List[NodePosition]:
        """Center nodes within each layer vertically."""
        layer_positions = {}
        
        for pos in positions:
            layer = layers.get(pos.node_id, 0)
            if layer not in layer_positions:
                layer_positions[layer] = []
            layer_positions[layer].append(pos)
        
        # Find max height
        max_nodes = max(len(nodes) for nodes in layer_positions.values())
        center_y = (max_nodes * self.node_spacing_y) / 2
        
        # Center each layer
        centered = []
        for pos in positions:
            layer = layers.get(pos.node_id, 0)
            layer_nodes = layer_positions[layer]
            layer_height = len(layer_nodes) * self.node_spacing_y
            offset = center_y - layer_height / 2
            
            idx = next(i for i, p in enumerate(layer_nodes) if p.node_id == pos.node_id)
            new_y = offset + idx * self.node_spacing_y + self.margin
            
            centered.append(NodePosition(
                node_id=pos.node_id,
                x=pos.x,
                y=new_y
            ))
        
        return centered
    
    def force_directed_layout(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        iterations: int = 50
    ) -> LayoutResult:
        """
        Force-directed layout using spring simulation.
        
        Nodes repel each other, edges act as springs.
        """
        # Initialize random positions
        import random
        random.seed(42)
        
        positions = {
            n['node_id']: {
                'x': random.uniform(100, 600),
                'y': random.uniform(100, 400)
            }
            for n in nodes
        }
        
        # Constants
        repulsion = 5000
        attraction = 0.01
        damping = 0.85
        
        for _ in range(iterations):
            forces = {n['node_id']: {'fx': 0, 'fy': 0} for n in nodes}
            
            # Repulsion between all nodes
            for i, n1 in enumerate(nodes):
                for n2 in nodes[i+1:]:
                    dx = positions[n1['node_id']]['x'] - positions[n2['node_id']]['x']
                    dy = positions[n1['node_id']]['y'] - positions[n2['node_id']]['y']
                    dist = max(math.sqrt(dx*dx + dy*dy), 1)
                    
                    force = repulsion / (dist * dist)
                    fx = force * dx / dist
                    fy = force * dy / dist
                    
                    forces[n1['node_id']]['fx'] += fx
                    forces[n1['node_id']]['fy'] += fy
                    forces[n2['node_id']]['fx'] -= fx
                    forces[n2['node_id']]['fy'] -= fy
            
            # Attraction along edges
            for edge in edges:
                source = edge.get('source_node_id') or edge.get('from_node_id')
                target = edge.get('target_node_id') or edge.get('to_node_id')
                
                if source not in positions or target not in positions:
                    continue
                
                dx = positions[target]['x'] - positions[source]['x']
                dy = positions[target]['y'] - positions[source]['y']
                dist = max(math.sqrt(dx*dx + dy*dy), 1)
                
                fx = attraction * dx
                fy = attraction * dy
                
                forces[source]['fx'] += fx
                forces[source]['fy'] += fy
                forces[target]['fx'] -= fx
                forces[target]['fy'] -= fy
            
            # Apply forces
            for node_id in positions:
                positions[node_id]['x'] += forces[node_id]['fx'] * damping
                positions[node_id]['y'] += forces[node_id]['fy'] * damping
        
        # Convert to NodePosition
        result_positions = [
            NodePosition(
                node_id=n['node_id'],
                x=positions[n['node_id']]['x'],
                y=positions[n['node_id']]['y']
            )
            for n in nodes
        ]
        
        return LayoutResult(
            positions=result_positions,
            bounds=self._calculate_bounds(result_positions),
            algorithm='force_directed'
        )
    
    def grid_layout(
        self,
        nodes: List[Dict],
        columns: int = 4
    ) -> LayoutResult:
        """
        Simple grid layout for nodes.
        """
        positions = []
        
        for i, node in enumerate(nodes):
            col = i % columns
            row = i // columns
            
            positions.append(NodePosition(
                node_id=node['node_id'],
                x=self.margin + col * self.node_spacing_x,
                y=self.margin + row * self.node_spacing_y
            ))
        
        return LayoutResult(
            positions=positions,
            bounds=self._calculate_bounds(positions),
            algorithm='grid'
        )
    
    def _calculate_bounds(self, positions: List[NodePosition]) -> Dict[str, float]:
        """Calculate bounding box of all positions."""
        if not positions:
            return {'minX': 0, 'minY': 0, 'maxX': 0, 'maxY': 0}
        
        return {
            'minX': min(p.x for p in positions),
            'minY': min(p.y for p in positions),
            'maxX': max(p.x + p.width for p in positions),
            'maxY': max(p.y + p.height for p in positions)
        }
    
    def layout(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        algorithm: str = 'hierarchical'
    ) -> LayoutResult:
        """
        Apply layout algorithm.
        
        Args:
            nodes: List of node dictionaries with node_id
            edges: List of edge dictionaries with source/target
            algorithm: 'hierarchical', 'force_directed', or 'grid'
        """
        if algorithm == 'force_directed':
            return self.force_directed_layout(nodes, edges)
        elif algorithm == 'grid':
            return self.grid_layout(nodes)
        else:
            return self.hierarchical_layout(nodes, edges)


# Singleton instance
auto_layout_service = AutoLayoutService()
