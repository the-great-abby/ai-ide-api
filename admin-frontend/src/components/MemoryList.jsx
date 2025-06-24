import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';
import { Search, Filter, Edit, Eye, Calendar, Tag, Hash } from 'lucide-react';

const MemoryList = ({ onMemorySelect, selectedMemoryId }) => {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [namespaceFilter, setNamespaceFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState(null);
  const [editingMemory, setEditingMemory] = useState(null);

  useEffect(() => {
    fetchMemories();
  }, []);

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/memory/nodes');
      setMemories(response.data || []);
    } catch (err) {
      setError('Failed to fetch memories');
      console.error('Error fetching memories:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredMemories = memories.filter(memory => {
    const matchesSearch = memory.content?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         memory.namespace?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         memory.meta?.name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesNamespace = !namespaceFilter || memory.namespace === namespaceFilter;
    const matchesTag = !tagFilter || memory.tags?.includes(tagFilter);
    
    return matchesSearch && matchesNamespace && matchesTag;
  });

  const handleMemoryClick = (memory) => {
    setSelectedMemory(memory);
    setShowDetailModal(true);
    if (onMemorySelect) {
      onMemorySelect(memory.id);
    }
  };

  const handleEditMemory = (memory) => {
    setEditingMemory({ ...memory });
  };

  const handleSaveMemory = async () => {
    try {
      await apiClient.put(`/memory/nodes/${editingMemory.id}`, editingMemory);
      await fetchMemories();
      setEditingMemory(null);
      setShowDetailModal(false);
    } catch (err) {
      console.error('Error updating memory:', err);
    }
  };

  const handleCancelEdit = () => {
    setEditingMemory(null);
  };

  const getNamespaces = () => {
    const namespaces = [...new Set(memories.map(m => m.namespace))];
    return namespaces.filter(Boolean);
  };

  const getAllTags = () => {
    const allTags = memories.flatMap(m => m.tags || []);
    return [...new Set(allTags)];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600">
        <p>{error}</p>
        <button 
          onClick={fetchMemories}
          className="mt-2 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold mb-2">Memories</h2>
        <p className="text-sm text-gray-600">{filteredMemories.length} of {memories.length} memories</p>
      </div>

      {/* Search and Filters */}
      <div className="p-4 border-b border-gray-200 space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search memories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={namespaceFilter}
            onChange={(e) => setNamespaceFilter(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Namespaces</option>
            {getNamespaces().map(namespace => (
              <option key={namespace} value={namespace}>{namespace}</option>
            ))}
          </select>

          <select
            value={tagFilter}
            onChange={(e) => setTagFilter(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Tags</option>
            {getAllTags().map(tag => (
              <option key={tag} value={tag}>{tag}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Memory List */}
      <div className="flex-1 overflow-y-auto">
        {filteredMemories.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <p>No memories found</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredMemories.map((memory) => (
              <div
                key={memory.id}
                className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                  selectedMemoryId === memory.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                }`}
                onClick={() => handleMemoryClick(memory)}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-medium text-gray-900 truncate">
                    {memory.meta?.name || memory.namespace || 'Untitled Memory'}
                  </h3>
                  <div className="flex gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditMemory(memory);
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Edit"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                  {memory.content}
                </p>

                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <Hash className="w-3 h-3" />
                    <span>{memory.namespace}</span>
                  </div>
                  {memory.created_at && (
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>{formatDate(memory.created_at)}</span>
                    </div>
                  )}
                </div>

                {memory.tags && memory.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {memory.tags.slice(0, 3).map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                    {memory.tags.length > 3 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        +{memory.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail/Edit Modal */}
      {showDetailModal && selectedMemory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-semibold">
                  {editingMemory ? 'Edit Memory' : 'Memory Details'}
                </h2>
                <button
                  onClick={() => {
                    setShowDetailModal(false);
                    setSelectedMemory(null);
                    setEditingMemory(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {editingMemory ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Name
                    </label>
                    <input
                      type="text"
                      value={editingMemory.meta?.name || ''}
                      onChange={(e) => setEditingMemory({
                        ...editingMemory,
                        meta: { ...editingMemory.meta, name: e.target.value }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Content
                    </label>
                    <textarea
                      value={editingMemory.content || ''}
                      onChange={(e) => setEditingMemory({
                        ...editingMemory,
                        content: e.target.value
                      })}
                      rows={6}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tags (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={editingMemory.tags?.join(', ') || ''}
                      onChange={(e) => setEditingMemory({
                        ...editingMemory,
                        tags: e.target.value.split(',').map(tag => tag.trim()).filter(Boolean)
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-4">
                    <button
                      onClick={handleCancelEdit}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveMemory}
                      className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                    >
                      Save
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {selectedMemory.meta?.name || 'Untitled Memory'}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Namespace: {selectedMemory.namespace}
                    </p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Content</h4>
                    <p className="text-gray-600 whitespace-pre-wrap">
                      {selectedMemory.content}
                    </p>
                  </div>

                  {selectedMemory.tags && selectedMemory.tags.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-700 mb-2">Tags</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedMemory.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end gap-2 pt-4">
                    <button
                      onClick={() => handleEditMemory(selectedMemory)}
                      className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                    >
                      Edit
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoryList; 