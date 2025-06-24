import React, { useState } from 'react';
import KnowledgeGraph from '../components/KnowledgeGraph';
import MemoryList from '../components/MemoryList';
import MemoryGraphD3 from '../components/MemoryGraphD3';
import { 
  Settings, 
  Bug, 
  BarChart3, 
  Info,
  ChevronDown,
  ChevronUp,
  Database,
  X
} from 'lucide-react';

const KnowledgeGraphPage = () => {
  const [showMemorySidebar, setShowMemorySidebar] = useState(false);
  const [selectedMemoryId, setSelectedMemoryId] = useState(null);
  const [graphView, setGraphView] = useState('d3'); // 'mermaid' or 'd3'

  const handleMemorySelect = (memoryId) => {
    setSelectedMemoryId(memoryId);
  };

  const handleMemoryFocus = (memoryNode) => {
    // This callback is called when a memory node is focused in the graph
    // We can use this to sync the memory list selection if needed
    console.log('Memory focused in graph:', memoryNode);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Top Navigation Bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900">AI-IDE Knowledge Graph</h1>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Memory Sidebar Toggle */}
            <button
              onClick={() => setShowMemorySidebar(!showMemorySidebar)}
              className={`p-2 rounded-md transition-colors ${
                showMemorySidebar 
                  ? 'bg-blue-100 text-blue-600' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              title={showMemorySidebar ? 'Hide Memory Browser' : 'Show Memory Browser'}
            >
              <Database className="h-5 w-5" />
            </button>
            
            {/* Info Button */}
            <button
              className="p-2 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
              title="About Knowledge Graph"
            >
              <Info className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Memory Sidebar */}
        {showMemorySidebar && (
          <div className="w-96 bg-white border-r border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Memory Browser</h2>
                <button
                  onClick={() => setShowMemorySidebar(false)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden">
              <MemoryList 
                onMemorySelect={handleMemorySelect}
                selectedMemoryId={selectedMemoryId}
              />
            </div>
          </div>
        )}

        {/* Knowledge Graph */}
        <div className="flex-1 flex flex-col">
          <div className="flex items-center gap-2 p-2 bg-gray-50 border-b">
            <button
              className={`px-3 py-1 rounded-md ${graphView === 'mermaid' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'}`}
              onClick={() => setGraphView('mermaid')}
            >
              Mermaid View
            </button>
            <button
              className={`px-3 py-1 rounded-md ${graphView === 'd3' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'}`}
              onClick={() => setGraphView('d3')}
            >
              D3 View
            </button>
          </div>
          {graphView === 'mermaid' ? <KnowledgeGraph /> : <MemoryGraphD3 />}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphPage; 