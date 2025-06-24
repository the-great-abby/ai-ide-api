import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';
import Mermaid from './Mermaid';

const KnowledgeGraph = () => {
  const [mermaidData, setMermaidData] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadGraphData = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get('/memory/visualization?format=mermaid');
        setMermaidData(response.data.diagram);
      } catch (err) {
        setError('Failed to load graph data');
        console.error('Error loading graph data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadGraphData();
  }, []);

  if (loading) {
    return <div>Loading knowledge graph...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <div className="w-full h-full">
      <Mermaid chart={mermaidData} />
    </div>
  );
};

export default KnowledgeGraph;
