import React, { useEffect, useRef, useState } from 'react';

interface GraphNode {
  id: string;
  label: string;
  type?: string;
  description?: string;
}

interface GraphEdge {
  source: string;
  target: string;
  weight?: number;
  type?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const GraphVisualization: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [searchText, setSearchText] = useState('');
  const [visibleNodes, setVisibleNodes] = useState<Set<string>>(new Set());
  const [initiallyMatchingNodes, setInitiallyMatchingNodes] = useState<Set<string>>(new Set());
  const [isLayoutCalculated, setIsLayoutCalculated] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    loadGraphData();
  }, []);

  // Detect dark mode changes
  useEffect(() => {
    const checkDarkMode = () => {
      setIsDarkMode(document.body.classList.contains('dark-mode'));
    };

    // Check initial state
    checkDarkMode();

    // Watch for changes
    const observer = new MutationObserver(checkDarkMode);
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });

    return () => observer.disconnect();
  }, []);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      
      // Fetch graph data from the backend API
      const response = await fetch('http://localhost:8000/graph-data');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // The API already provides properly formatted nodes and edges
      const nodes: GraphNode[] = data.nodes.map((node: any) => ({
        id: node.id,
        label: node.label,
        type: node.type,
        description: node.description
      }));
      
      const edges: GraphEdge[] = data.edges.map((edge: any) => ({
        source: edge.source,
        target: edge.target,
        weight: edge.weight,
        type: edge.type
      }));
      
      setGraphData({ nodes, edges });
      console.log(`Loaded ${data.total_nodes} nodes and ${data.total_edges} edges from entities.parquet`);
      
      // Debug: Check edge-node ID matching
      const nodeIds = new Set(nodes.map(n => n.id));
      const edgeSources = new Set(edges.map(e => e.source));
      const edgeTargets = new Set(edges.map(e => e.target));
      
      const matchingSources = [...edgeSources].filter(id => nodeIds.has(id));
      const matchingTargets = [...edgeTargets].filter(id => nodeIds.has(id));
      
      console.log('Node IDs sample:', [...nodeIds].slice(0, 5));
      console.log('Edge sources sample:', [...edgeSources].slice(0, 5));
      console.log('Edge targets sample:', [...edgeTargets].slice(0, 5));
      console.log(`Matching sources: ${matchingSources.length}/${edgeSources.size}`);
      console.log(`Matching targets: ${matchingTargets.length}/${edgeTargets.size}`);
    } catch (error) {
      console.error('Error loading GraphRAG data:', error);
      // Fallback to mock data if loading fails
      loadMockData();
    } finally {
      setLoading(false);
    }
  };

  const loadMockData = () => {
    const mockData: GraphData = {
      nodes: [
        { id: "ALEX CHEN", label: "Alex Chen", type: "person" },
        { id: "UNIVERSITY OF CALIFORNIA, BERKELEY", label: "UC Berkeley", type: "organization" },
        { id: "TECHSTART INC.", label: "TechStart Inc.", type: "organization" },
        { id: "SARAH JOHNSON", label: "Sarah Johnson", type: "person" },
        { id: "META", label: "Meta", type: "organization" },
        { id: "GOOGLE", label: "Google", type: "organization" },
        { id: "MICHAEL RODRIGUEZ", label: "Michael Rodriguez", type: "person" },
        { id: "STANFORD UNIVERSITY", label: "Stanford University", type: "organization" },
      ],
      edges: [
        { source: "ALEX CHEN", target: "UNIVERSITY OF CALIFORNIA, BERKELEY", weight: 0.8 },
        { source: "ALEX CHEN", target: "TECHSTART INC.", weight: 0.9 },
        { source: "SARAH JOHNSON", target: "META", weight: 0.7 },
        { source: "SARAH JOHNSON", target: "GOOGLE", weight: 0.6 },
        { source: "MICHAEL RODRIGUEZ", target: "STANFORD UNIVERSITY", weight: 0.8 },
        { source: "MICHAEL RODRIGUEZ", target: "GOOGLE", weight: 0.9 },
      ]
    };
    setGraphData(mockData);
  };


  // Calculate layout only once when graph data is first loaded
  useEffect(() => {
    if (graphData.nodes.length > 0 && svgRef.current && !isLayoutCalculated) {
      drawGraph();
      setIsLayoutCalculated(true);
    }
  }, [graphData, isLayoutCalculated]);

  // Update colors when dark mode changes (without reshuffling)
  useEffect(() => {
    if (isLayoutCalculated && svgRef.current) {
      updateThemeColors();
    }
  }, [isDarkMode, isLayoutCalculated]);

  // Update visibility without recalculating layout
  useEffect(() => {
    if (isLayoutCalculated && svgRef.current) {
      updateNodeVisibility();
    }
  }, [visibleNodes, isLayoutCalculated]);

  // Handle search text changes
  useEffect(() => {
    if (searchText.trim() === '') {
      setVisibleNodes(new Set());
      setInitiallyMatchingNodes(new Set());
    } else {
      // Split search text by commas and trim each term
      const searchTerms = searchText.split(',').map(term => term.trim()).filter(term => term.length > 0);
      
      // Find initially matching nodes for all search terms
      const allMatchingNodes = new Set<string>();
      searchTerms.forEach(term => {
        const termMatchingNodes = graphData.nodes
          .filter(node => 
            node.label.toLowerCase().includes(term.toLowerCase()) ||
            node.id.toLowerCase().includes(term.toLowerCase())
          )
          .map(node => node.id);
        
        termMatchingNodes.forEach(nodeId => allMatchingNodes.add(nodeId));
      });

      setInitiallyMatchingNodes(allMatchingNodes);

      // Find adjacent nodes (connected to any of the initially matching nodes)
      const adjacentNodes = new Set<string>();
      allMatchingNodes.forEach(nodeId => {
        graphData.edges.forEach(edge => {
          if (edge.source === nodeId) {
            adjacentNodes.add(edge.target);
          }
          if (edge.target === nodeId) {
            adjacentNodes.add(edge.source);
          }
        });
      });

      // Combine initially matching nodes and their adjacent nodes
      const allVisibleNodes = new Set([...allMatchingNodes, ...adjacentNodes]);
      setVisibleNodes(allVisibleNodes);
    }
  }, [searchText, graphData.nodes, graphData.edges]);

  // Apply transform without redrawing the graph
  useEffect(() => {
    const svg = svgRef.current;
    if (svg) {
      const graphGroup = svg.querySelector('#graph-content');
      if (graphGroup) {
        const transformString = `translate(${transform.x}, ${transform.y}) scale(${transform.scale})`;
        graphGroup.setAttribute('transform', transformString);
      }
    }
  }, [transform]);

  // Panning handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setTransform({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
        scale: transform.scale
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const drawGraph = () => {
    const svg = svgRef.current;
    if (!svg) return;

    svg.innerHTML = '';

    const width = 1200;
    const height = 800;
    svg.setAttribute('width', width.toString());
    svg.setAttribute('height', height.toString());

    // Create a group element for the graph content
    const graphGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    graphGroup.setAttribute('id', 'graph-content');
    svg.appendChild(graphGroup);

    // Apply layout to ALL nodes (not filtered)
    const nodes = applySimpleLayout(graphData.nodes, graphData.edges, width, height);

    // Draw ALL edges first (so they appear behind nodes)
    let renderedEdges = 0;
    graphData.edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);
      
      if (sourceNode && targetNode) {
        renderedEdges++;
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sourceNode.x.toString());
        line.setAttribute('y1', sourceNode.y.toString());
        line.setAttribute('x2', targetNode.x.toString());
        line.setAttribute('y2', targetNode.y.toString());
        
        // Style edges based on connection type
        let strokeColor = '#999';
        let strokeWidth = '1';
        
        if (sourceNode.type === 'person' || targetNode.type === 'person') {
          strokeColor = '#4CAF50';
          strokeWidth = '2';
        }
        
        line.setAttribute('stroke', strokeColor);
        line.setAttribute('stroke-width', strokeWidth);
        line.setAttribute('opacity', '0.6');
        line.setAttribute('class', 'graph-edge');
        line.setAttribute('data-source', edge.source);
        line.setAttribute('data-target', edge.target);
        graphGroup.appendChild(line);
      }
    });
    
    console.log(`Rendered ${renderedEdges} edges out of ${graphData.edges.length} total edges`);

    // Draw ALL nodes
    nodes.forEach(node => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', node.x.toString());
      circle.setAttribute('cy', node.y.toString());
      
      // Different sizes for different node types
      let radius = 10;
      if (node.type === 'person') radius = 14;
      else if (node.type === 'organization') radius = 12;
      else if (node.type === 'technology') radius = 11;
      
      circle.setAttribute('r', radius.toString());
      
      let color = '#FF9800'; // default
      if (node.type === 'person') color = '#4CAF50';
      else if (node.type === 'organization') color = '#2196F3';
      else if (node.type === 'technology') color = '#9C27B0';
      
      circle.setAttribute('fill', color);
      circle.setAttribute('stroke', isDarkMode ? '#000' : '#fff');
      circle.setAttribute('stroke-width', '2');
      circle.setAttribute('class', 'graph-node');
      circle.setAttribute('data-node-id', node.id);
      
      graphGroup.appendChild(circle);

      // Add text label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', node.x.toString());
      text.setAttribute('y', (node.y + radius + 15).toString());
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('font-size', node.type === 'person' ? '10' : '9');
      text.setAttribute('fill', isDarkMode ? '#fff' : '#333');
      text.setAttribute('font-weight', node.type === 'person' ? 'bold' : 'normal');
      text.setAttribute('class', 'graph-label');
      text.setAttribute('data-node-id', node.id);
      
      const maxLength = node.type === 'person' ? 20 : 15;
      text.textContent = node.label.length > maxLength ? 
        node.label.substring(0, maxLength) + '...' : node.label;
      graphGroup.appendChild(text);
    });
  };

  const updateNodeVisibility = () => {
    const svg = svgRef.current;
    if (!svg) return;

    // Update node visibility
    const nodes = svg.querySelectorAll('.graph-node');
    const labels = svg.querySelectorAll('.graph-label');
    
    nodes.forEach(node => {
      const nodeId = node.getAttribute('data-node-id');
      if (nodeId) {
        if (searchText.trim() === '' || visibleNodes.has(nodeId)) {
          node.setAttribute('opacity', '1');
        } else {
          node.setAttribute('opacity', '0');
        }
      }
    });

    labels.forEach(label => {
      const nodeId = label.getAttribute('data-node-id');
      if (nodeId) {
        if (searchText.trim() === '' || visibleNodes.has(nodeId)) {
          label.setAttribute('opacity', '1');
        } else {
          label.setAttribute('opacity', '0');
        }
      }
    });

    // Update edge visibility
    const edges = svg.querySelectorAll('.graph-edge');
    edges.forEach(edge => {
      const source = edge.getAttribute('data-source');
      const target = edge.getAttribute('data-target');
      if (source && target) {
        if (searchText.trim() === '' || (visibleNodes.has(source) && visibleNodes.has(target))) {
          edge.setAttribute('opacity', '0.6');
        } else {
          edge.setAttribute('opacity', '0');
        }
      }
    });
  };

  const updateThemeColors = () => {
    const svg = svgRef.current;
    if (!svg) return;

    // Update node stroke colors
    const nodes = svg.querySelectorAll('.graph-node');
    nodes.forEach(node => {
      node.setAttribute('stroke', isDarkMode ? '#000' : '#fff');
    });

    // Update text colors
    const labels = svg.querySelectorAll('.graph-label');
    labels.forEach(label => {
      label.setAttribute('fill', isDarkMode ? '#fff' : '#333');
    });
  };

  const applySimpleLayout = (nodes: GraphNode[], edges: GraphEdge[], width: number, height: number) => {
    // Calculate edge count for each node
    const edgeCounts = new Map<string, number>();
    nodes.forEach(node => edgeCounts.set(node.id, 0));
    edges.forEach(edge => {
      edgeCounts.set(edge.source, (edgeCounts.get(edge.source) || 0) + 1);
      edgeCounts.set(edge.target, (edgeCounts.get(edge.target) || 0) + 1);
    });

    // Sort nodes by edge count (most connected first)
    const sortedNodes = [...nodes].sort((a, b) => {
      const countA = edgeCounts.get(a.id) || 0;
      const countB = edgeCounts.get(b.id) || 0;
      return countB - countA;
    });

    const positionedNodes: (GraphNode & { x: number; y: number })[] = [];
    const usedPositions = new Set<string>();
    const minDistance = 80; // Minimum distance between nodes

    // Position nodes based on connectivity
    sortedNodes.forEach((node) => {
      const edgeCount = edgeCounts.get(node.id) || 0;
      let x, y;
      let attempts = 0;
      const maxAttempts = 100;
      let positionKey: string;

      do {
        if (edgeCount >= 3) {
          // Highly connected nodes go in center area
          const centerX = width / 2;
          const centerY = height / 2;
          const centerRadius = Math.min(width, height) * 0.2;
          
          const angle = Math.random() * 2 * Math.PI;
          const radius = Math.random() * centerRadius;
          x = centerX + radius * Math.cos(angle);
          y = centerY + radius * Math.sin(angle);
        } else if (edgeCount >= 1) {
          // Moderately connected nodes go in middle ring
          const centerX = width / 2;
          const centerY = height / 2;
          const innerRadius = Math.min(width, height) * 0.25;
          const outerRadius = Math.min(width, height) * 0.4;
          
          const angle = Math.random() * 2 * Math.PI;
          const radius = innerRadius + Math.random() * (outerRadius - innerRadius);
          x = centerX + radius * Math.cos(angle);
          y = centerY + radius * Math.sin(angle);
        } else {
          // Unconnected nodes go in outer area
          const padding = 100;
          x = padding + Math.random() * (width - 2 * padding);
          y = padding + Math.random() * (height - 2 * padding);
        }

        // Ensure we don't overlap with existing nodes
        positionKey = `${Math.floor(x / minDistance)},${Math.floor(y / minDistance)}`;
        attempts++;
      } while (usedPositions.has(positionKey) && attempts < maxAttempts);

      // If we couldn't find a non-overlapping position, place it randomly
      if (attempts >= maxAttempts) {
        const padding = 100;
        x = padding + Math.random() * (width - 2 * padding);
        y = padding + Math.random() * (height - 2 * padding);
        positionKey = `${Math.floor(x / minDistance)},${Math.floor(y / minDistance)}`;
      }

      // Mark this position as used
      usedPositions.add(positionKey);

      positionedNodes.push({
        ...node,
        x: Math.max(50, Math.min(width - 50, x)),
        y: Math.max(50, Math.min(height - 50, y))
      });
    });

    return positionedNodes;
  };

  if (loading) {
    return (
      <div className="graph-loading">
        <p>Loading GraphRAG visualization...</p>
      </div>
    );
  }

  return (
    <div className="graph-visualization">
      <div className="graph-header">
        <h3>GraphRAG Knowledge Graph</h3>
        <div className="search-section">
          <div className="search-input-container">
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Search for nodes (e.g., 'Alex', 'Google, Python', 'University, Tech')..."
              className="search-input"
            />
            <div className="search-results">
              {searchText.trim() !== '' && (
                <div className="result-breakdown">
                  <span className="result-count">
                    {initiallyMatchingNodes.size} direct match{initiallyMatchingNodes.size !== 1 ? 'es' : ''}
                  </span>
                  <span className="result-separator">+</span>
                  <span className="result-count">
                    {visibleNodes.size - initiallyMatchingNodes.size} adjacent node{visibleNodes.size - initiallyMatchingNodes.size !== 1 ? 's' : ''}
                  </span>
                  <span className="result-separator">=</span>
                  <span className="result-total">
                    {visibleNodes.size} total
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="graph-legend">
            <div className="legend-item">
              <div className="legend-color person"></div>
              <span>People</span>
            </div>
            <div className="legend-item">
              <div className="legend-color organization"></div>
              <span>Organizations</span>
            </div>
            <div className="legend-item">
              <div className="legend-color technology"></div>
              <span>Technologies</span>
            </div>
            <div className="legend-item">
              <div className="legend-color other"></div>
              <span>Other</span>
            </div>
          </div>
        </div>
      </div>
      
      <div 
        className="graph-container"
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      >
        <svg ref={svgRef} className="graph-svg"></svg>
      </div>
      
      <div className="graph-stats">
        <p>
          Total: {graphData.nodes.length} nodes, {graphData.edges.length} edges | 
          Showing: {visibleNodes.size} nodes, {graphData.edges.filter(edge => 
            visibleNodes.has(edge.source) && visibleNodes.has(edge.target)
          ).length} edges
        </p>
        <p className="instructions">
          🔍 Type terms separated by commas (e.g., "Alex, Google") | 🖱️ Drag to pan around the graph
        </p>
      </div>
    </div>
  );
};

export default GraphVisualization;
