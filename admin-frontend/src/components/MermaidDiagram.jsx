import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'monospace',
});

const MermaidDiagram = ({ diagram }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      // Clear previous content
      containerRef.current.innerHTML = '';
      
      // Render the diagram
      mermaid.render('mermaid-diagram', diagram).then(({ svg }) => {
        containerRef.current.innerHTML = svg;
      }).catch(error => {
        console.error('Error rendering mermaid diagram:', error);
        containerRef.current.innerHTML = 'Error rendering diagram';
      });
    }
  }, [diagram]);

  return (
    <div 
      ref={containerRef} 
      className="mermaid-diagram"
      style={{
        padding: '1rem',
        backgroundColor: '#f5f5f5',
        borderRadius: '4px',
        overflow: 'auto'
      }}
    />
  );
};

export default MermaidDiagram; 