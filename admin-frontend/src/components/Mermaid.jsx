import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
});

const Mermaid = ({ chart }) => {
  const containerRef = useRef(null);
  
  useEffect(() => {
    if (chart && containerRef.current) {
      const id = `mermaid-graph-${Date.now()}`;
      // Ensure the container is empty before rendering
      containerRef.current.innerHTML = `<div id="${id}">${chart}</div>`;
      try {
        mermaid.run({
          nodes: [document.getElementById(id)],
        });
      } catch (e) {
        console.error("Error rendering mermaid:", e);
      }
    }
  }, [chart]);

  return <div ref={containerRef} className="mermaid-container w-full h-full" />;
};

export default Mermaid; 