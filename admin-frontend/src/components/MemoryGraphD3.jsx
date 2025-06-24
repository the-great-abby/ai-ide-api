import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import apiClient from '../utils/apiClient';

const width = 900;
const height = 600;

const MemoryGraphD3 = () => {
  const svgRef = useRef();
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [nodesRes, edgesRes] = await Promise.all([
          apiClient.get('/memory/nodes'),
          apiClient.get('/memory/edges'),
        ]);
        setNodes(nodesRes.data || []);
        setEdges(edgesRes.data || []);
      } catch (err) {
        setError('Failed to load memory graph data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Defensive: Remove any nodes that are undefined or missing an id
  const filteredNodes = nodes.filter(
    n => n && typeof n.id === 'string' && (
      n.content?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.namespace?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.meta?.name?.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );
  const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
  // Defensive: Only include edges where both endpoints exist and are valid
  let filteredEdges = (edges || []).filter(
    e => e && typeof e.from_id === 'string' && typeof e.to_id === 'string' && filteredNodeIds.has(e.from_id) && filteredNodeIds.has(e.to_id)
  );
  // Remove duplicate edges (same from_id, to_id, and rel_type)
  const edgeKey = e => `${e.from_id}|${e.to_id}|${e.rel_type}`;
  const seenEdges = new Set();
  filteredEdges = filteredEdges.filter(e => {
    const key = edgeKey(e);
    if (seenEdges.has(key)) return false;
    seenEdges.add(key);
    return true;
  });
  // Separate self-loops (from_id === to_id)
  const selfLoops = filteredEdges.filter(e => e.from_id === e.to_id);
  const normalEdges = filteredEdges.filter(e => e.from_id !== e.to_id);

  // Debug logging
  console.log('Filtered Nodes:', filteredNodes);
  console.log('Filtered Edges:', filteredEdges);

  // D3 rendering effect (only runs when data changes and there is data to render)
  useEffect(() => {
    if (loading || error || filteredNodes.length === 0 || (filteredNodes.length > 0 && filteredEdges.length === 0)) {
      // Don't render D3 if not ready or nothing to show
      return;
    }
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous

    // Build node map for quick lookup
    const nodeMap = Object.fromEntries(filteredNodes.map(n => [n.id, n]));
    console.log('Node Map:', nodeMap);
    // Log any edge that references a missing node
    filteredEdges.forEach(e => {
      if (!nodeMap[e.from_id] || !nodeMap[e.to_id]) {
        console.warn('Edge references missing node:', e);
      }
    });

    // Map edges to D3 format with source/target
    const d3Edges = normalEdges.map(e => ({
      ...e,
      source: e.from_id,
      target: e.to_id
    }));

    // D3 force simulation (only normal edges)
    const simulation = d3.forceSimulation(filteredNodes)
      .force('link', d3.forceLink(d3Edges).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Draw normal links
    svg
      .append('g')
      .attr('stroke', '#aaa')
      .selectAll('line')
      .data(d3Edges)
      .join('line')
      .attr('stroke-width', 2);

    // Draw self-loops as small circles around the node
    if (selfLoops.length > 0) {
      svg.append('g')
        .selectAll('ellipse')
        .data(selfLoops)
        .join('ellipse')
        .attr('cx', d => nodeMap[d.from_id]?.x || width/2)
        .attr('cy', d => nodeMap[d.from_id]?.y || height/2)
        .attr('rx', 24)
        .attr('ry', 12)
        .attr('stroke', '#f39c12')
        .attr('stroke-width', 2)
        .attr('fill', 'none');
    }

    // Draw nodes
    svg
      .append('g')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .selectAll('circle')
      .data(filteredNodes)
      .join('circle')
      .attr('r', 18)
      .attr('fill', d => d.namespace ? d3.schemeCategory10[d.namespace.length % 10] : '#69b3a2')
      .call(drag(simulation))
      .on('click', (event, d) => setSelectedNode(d));

    // Node labels
    svg
      .append('g')
      .selectAll('text')
      .data(filteredNodes)
      .join('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .attr('font-size', 10)
      .attr('pointer-events', 'none')
      .text(d => d.meta?.name || d.namespace || '');

    simulation.on('tick', () => {
      svg.selectAll('line')
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      svg.selectAll('circle')
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
      svg.selectAll('text')
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });

    function drag(simulation) {
      function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }
      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }
      function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }
      return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended);
    }
  }, [filteredNodes, filteredEdges, loading, error]);

  // Early returns for rendering only (after all hooks)
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">Loading memory graph...</div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center text-red-600">{error}</div>
    );
  }

  if (!nodes || nodes.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
        <div className="text-2xl mb-2">No memory nodes found</div>
        <div className="text-sm">Add some memories to see the graph visualization.</div>
      </div>
    );
  }

  if (filteredNodes.length > 0 && filteredEdges.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
        <div className="text-2xl mb-2">No relationships found between memory nodes</div>
        <div className="text-sm">Nodes exist, but no edges connect them. Add relationships to see the full graph.</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col">
      <div className="p-2 flex items-center gap-2 bg-gray-100 border-b">
        <input
          type="text"
          placeholder="Search nodes..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="px-3 py-1 border rounded w-64"
        />
        {loading && <span className="ml-2 text-gray-500">Loading...</span>}
        {error && <span className="ml-2 text-red-600">{error}</span>}
      </div>
      <svg ref={svgRef} width={width} height={height} className="bg-white border flex-shrink-0" />
      {selectedNode && (
        <div className="p-4 border-t bg-gray-50">
          <h3 className="font-bold text-lg mb-2">{selectedNode.meta?.name || selectedNode.namespace || 'Memory Node'}</h3>
          <div className="mb-1 text-sm text-gray-600">ID: {selectedNode.id}</div>
          <div className="mb-1 text-sm text-gray-600">Namespace: {selectedNode.namespace}</div>
          <div className="mb-1 text-sm text-gray-600">Created: {selectedNode.created_at}</div>
          <div className="mb-2 text-gray-800">{selectedNode.content}</div>
          <button className="mt-2 px-3 py-1 bg-blue-500 text-white rounded" onClick={() => setSelectedNode(null)}>Close</button>
        </div>
      )}
    </div>
  );
};

export default MemoryGraphD3; 