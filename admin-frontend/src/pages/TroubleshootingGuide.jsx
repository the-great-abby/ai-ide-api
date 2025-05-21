import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MermaidDiagram from '../components/MermaidDiagram';

const TroubleshootingGuide = () => {
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGuide = async () => {
      try {
        const response = await axios.get('/api/troubleshooting-guide');
        setGuide(response.data);
      } catch (err) {
        setError('Failed to load troubleshooting guide');
        console.error('Error fetching guide:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGuide();
  }, []);

  if (loading) return <div>Loading troubleshooting guide...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!guide) return <div>No guide content available</div>;

  // Extract the Mermaid diagram from the markdown content
  const mermaidMatch = guide.content.match(/```mermaid\n([\s\S]*?)```/);
  const mermaidDiagram = mermaidMatch ? mermaidMatch[1] : null;

  return (
    <div className="troubleshooting-guide">
      <h1>Troubleshooting Guide</h1>
      
      {mermaidDiagram && (
        <div className="diagram-container">
          <h2>System Health Check Flow</h2>
          <MermaidDiagram diagram={mermaidDiagram} />
        </div>
      )}

      <div className="guide-content">
        {/* Render the rest of the markdown content */}
        <div dangerouslySetInnerHTML={{ __html: guide.html }} />
      </div>
    </div>
  );
};

export default TroubleshootingGuide; 