import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';
import { 
  Search, 
  Clock, 
  Globe, 
  Target, 
  Filter, 
  Calendar,
  Tag,
  Hash,
  TrendingUp,
  Link,
  Sparkles,
  BookOpen,
  RefreshCw,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

const AdvancedSearch = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('advanced');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Advanced search filters
  const [filters, setFilters] = useState({
    namespace: '',
    tags: '',
    categories: '',
    startDate: '',
    endDate: '',
    minConfidence: '',
    maxConfidence: '',
    timePeriod: ''
  });
  
  // Recommendation state
  const [selectedMemoryId, setSelectedMemoryId] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationType, setRecommendationType] = useState('similar');
  
  // UI state
  const [showFilters, setShowFilters] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);

  // RAG Search state
  const [ragQuestion, setRagQuestion] = useState('');
  const [ragAnswer, setRagAnswer] = useState(null);
  const [ragContexts, setRagContexts] = useState([]);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://api:8000';

  const performSearch = async () => {
    if (!searchQuery.trim() && searchType !== 'temporal' && searchType !== 'cross-project') {
      setError('Please enter a search query');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      let response;
      switch (searchType) {
        case 'semantic':
          response = await apiClient.post('/memory/search/semantic', {
            query: searchQuery,
            namespace: filters.namespace || undefined,
            limit: 20,
            min_similarity: 0.6
          });
          break;

        case 'temporal':
          response = await apiClient.get('/memory/search/temporal', {
            params: {
              namespace: filters.namespace || undefined,
              time_period: filters.timePeriod || undefined,
              start_date: filters.startDate || undefined,
              end_date: filters.endDate || undefined,
              limit: 50
            }
          });
          break;

        case 'cross-project':
          response = await apiClient.get('/memory/search/cross-project', {
            params: {
              query: searchQuery || undefined,
              tags: filters.tags || undefined,
              categories: filters.categories || undefined,
              limit: 20
            }
          });
          break;

        case 'advanced':
        default:
          response = await apiClient.get('/memory/search/advanced', {
            params: {
              query: searchQuery || undefined,
              namespace: filters.namespace || undefined,
              tags: filters.tags || undefined,
              categories: filters.categories || undefined,
              start_date: filters.startDate || undefined,
              end_date: filters.endDate || undefined,
              min_confidence: filters.minConfidence || undefined,
              max_confidence: filters.maxConfidence || undefined,
              search_type: 'combined',
              limit: 20
            }
          });
          break;
      }

      if (searchType === 'cross-project') {
        // Handle cross-project results differently
        const allMemories = [];
        Object.values(response.data.memories_by_namespace || {}).forEach(memories => {
          allMemories.push(...memories);
        });
        setSearchResults(allMemories);
      } else {
        setSearchResults(response.data.memories || []);
      }

    } catch (err) {
      setError('Search failed: ' + (err.response?.data?.detail || err.message));
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendations = async (memoryId, type = 'similar') => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.get(`/memory/recommendations/${memoryId}`, {
        params: {
          recommendation_type: type,
          limit: 10
        }
      });
      
      setRecommendations(response.data.recommendations || []);
      setSelectedMemoryId(memoryId);
      setRecommendationType(type);
      setShowRecommendations(true);
      
    } catch (err) {
      setError('Failed to get recommendations: ' + (err.response?.data?.detail || err.message));
      console.error('Recommendations error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    performSearch();
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setError(null);
    setFilters({
      namespace: '',
      tags: '',
      categories: '',
      startDate: '',
      endDate: '',
      minConfidence: '',
      maxConfidence: '',
      timePeriod: ''
    });
  };

  const getSearchTypeIcon = (type) => {
    switch (type) {
      case 'semantic': return <Sparkles className="h-4 w-4" />;
      case 'temporal': return <Clock className="h-4 w-4" />;
      case 'cross-project': return <Globe className="h-4 w-4" />;
      default: return <Search className="h-4 w-4" />;
    }
  };

  const getSearchTypeLabel = (type) => {
    switch (type) {
      case 'semantic': return 'Semantic Search';
      case 'temporal': return 'Temporal Search';
      case 'cross-project': return 'Cross-Project Search';
      default: return 'Advanced Search';
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSimilarityColor = (score) => {
    if (score >= 0.8) return 'text-blue-600';
    if (score >= 0.6) return 'text-purple-600';
    return 'text-gray-600';
  };

  const handleRAGSearch = async (e) => {
    e.preventDefault();
    if (!ragQuestion.trim()) {
      setRagError('Please enter a question for RAG search.');
      return;
    }
    setRagLoading(true);
    setRagError(null);
    setRagAnswer(null);
    setRagContexts([]);
    try {
      const response = await apiClient.post('/memory/rag_search', {
        question: ragQuestion,
        top_k: 5
      });
      setRagAnswer(response.data.answer || 'No answer returned.');
      setRagContexts(response.data.contexts || response.data.memories || []);
    } catch (err) {
      setRagError('RAG search failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRagLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* RAG Search Panel */}
      <div className="p-4 border-b border-gray-200 bg-blue-50 mb-2 rounded">
        <form onSubmit={handleRAGSearch} className="flex flex-col gap-2">
          <label className="font-semibold text-blue-900">RAG Search (Ask a question):</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={ragQuestion}
              onChange={e => setRagQuestion(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 px-3 py-2 border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              disabled={ragLoading}
            >
              {ragLoading ? 'Searching...' : 'Ask'}
            </button>
          </div>
          {ragError && <div className="text-red-600 text-sm">{ragError}</div>}
        </form>
        {ragAnswer && (
          <div className="mt-4">
            <div className="font-bold text-blue-800 mb-1">RAG Answer:</div>
            <div className="bg-white border border-blue-200 rounded p-3 mb-2 text-gray-900">{ragAnswer}</div>
            {ragContexts.length > 0 && (
              <div>
                <div className="font-semibold text-blue-700 mb-1">Supporting Memories:</div>
                <ul className="space-y-2">
                  {ragContexts.map((ctx, idx) => (
                    <li key={ctx.id || idx} className="bg-blue-100 border border-blue-200 rounded p-2">
                      <div className="font-medium text-blue-900">{ctx.meta?.name || ctx.namespace || 'Memory Node'}</div>
                      <div className="text-xs text-blue-700 mb-1">ID: {ctx.id}</div>
                      <div className="text-gray-800">{ctx.content}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Advanced Search & Discovery</h1>
            <p className="text-sm text-gray-600">Find memories using semantic search, temporal filters, and cross-project discovery</p>
          </div>
        </div>
      </div>

      {/* Search Controls */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search Type Selector */}
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700">Search Type:</label>
            <div className="flex space-x-2">
              {['advanced', 'semantic', 'temporal', 'cross-project'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSearchType(type)}
                  className={`px-3 py-2 rounded-md text-sm font-medium flex items-center space-x-2 ${
                    searchType === type
                      ? 'bg-blue-100 text-blue-700 border border-blue-300'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {getSearchTypeIcon(type)}
                  <span>{getSearchTypeLabel(type)}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Search Query */}
          <div className="flex space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Query
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={searchType === 'temporal' ? 'Optional query for temporal search' : 'Enter your search query...'}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex items-end space-x-2">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                <span>Search</span>
              </button>
              
              <button
                type="button"
                onClick={clearSearch}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Filters Toggle */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800"
            >
              <Filter className="h-4 w-4" />
              <span>Advanced Filters</span>
              {showFilters ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Namespace
                </label>
                <input
                  type="text"
                  value={filters.namespace}
                  onChange={(e) => setFilters({...filters, namespace: e.target.value})}
                  placeholder="Filter by namespace"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags
                </label>
                <input
                  type="text"
                  value={filters.tags}
                  onChange={(e) => setFilters({...filters, tags: e.target.value})}
                  placeholder="tag1,tag2,tag3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Categories
                </label>
                <input
                  type="text"
                  value={filters.categories}
                  onChange={(e) => setFilters({...filters, categories: e.target.value})}
                  placeholder="category1,category2"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  value={filters.startDate}
                  onChange={(e) => setFilters({...filters, startDate: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  value={filters.endDate}
                  onChange={(e) => setFilters({...filters, endDate: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Time Period
                </label>
                <select
                  value={filters.timePeriod}
                  onChange={(e) => setFilters({...filters, timePeriod: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All time</option>
                  <option value="today">Today</option>
                  <option value="week">Last week</option>
                  <option value="month">Last month</option>
                  <option value="quarter">Last quarter</option>
                  <option value="year">Last year</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Min Confidence
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={filters.minConfidence}
                  onChange={(e) => setFilters({...filters, minConfidence: e.target.value})}
                  placeholder="0.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Confidence
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={filters.maxConfidence}
                  onChange={(e) => setFilters({...filters, maxConfidence: e.target.value})}
                  placeholder="1.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="text-red-600">
              <span className="text-lg">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Search Results ({searchResults.length})
            </h2>
            <div className="text-sm text-gray-500">
              {getSearchTypeLabel(searchType)}
            </div>
          </div>
          
          <div className="space-y-4">
            {searchResults.map((memory) => (
              <div key={memory.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-medium text-gray-900">
                        {memory.content.substring(0, 100)}...
                      </span>
                      {memory.similarity_score && (
                        <span className={`text-xs px-2 py-1 rounded-full ${getSimilarityColor(memory.similarity_score)} bg-blue-50`}>
                          {(memory.similarity_score * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="flex items-center space-x-1">
                        <Hash className="h-3 w-3" />
                        <span>{memory.namespace}</span>
                      </span>
                      
                      {memory.confidence && (
                        <span className={`flex items-center space-x-1 ${getConfidenceColor(memory.confidence)}`}>
                          <Target className="h-3 w-3" />
                          <span>{(memory.confidence * 100).toFixed(0)}% confidence</span>
                        </span>
                      )}
                      
                      <span className="flex items-center space-x-1">
                        <Calendar className="h-3 w-3" />
                        <span>{new Date(memory.created_at).toLocaleDateString()}</span>
                      </span>
                    </div>
                    
                    {memory.tags && memory.tags.length > 0 && (
                      <div className="flex items-center space-x-2 mt-2">
                        <Tag className="h-3 w-3 text-gray-400" />
                        <div className="flex flex-wrap gap-1">
                          {memory.tags.slice(0, 3).map((tag, index) => (
                            <span key={index} className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                              {tag}
                            </span>
                          ))}
                          {memory.tags.length > 3 && (
                            <span className="text-xs text-gray-500">+{memory.tags.length - 3} more</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => getRecommendations(memory.id, 'similar')}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-md"
                      title="Get similar memories"
                    >
                      <Target className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => getRecommendations(memory.id, 'related')}
                      className="p-2 text-green-600 hover:bg-green-50 rounded-md"
                      title="Get related memories"
                    >
                      <Link className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => getRecommendations(memory.id, 'trending')}
                      className="p-2 text-purple-600 hover:bg-purple-50 rounded-md"
                      title="Get trending memories"
                    >
                      <TrendingUp className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations Panel */}
      {showRecommendations && recommendations.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Recommendations ({recommendations.length})
            </h2>
            <div className="flex items-center space-x-2">
              <select
                value={recommendationType}
                onChange={(e) => getRecommendations(selectedMemoryId, e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="similar">Similar Content</option>
                <option value="related">Graph Related</option>
                <option value="trending">Trending</option>
              </select>
              <button
                onClick={() => setShowRecommendations(false)}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <span className="text-lg">×</span>
              </button>
            </div>
          </div>
          
          <div className="space-y-3">
            {recommendations.map((rec) => (
              <div key={rec.id} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 mb-1">
                      {rec.content.substring(0, 80)}...
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>{rec.namespace}</span>
                      {rec.similarity_score && (
                        <span className={`${getSimilarityColor(rec.similarity_score)}`}>
                          {(rec.similarity_score * 100).toFixed(0)}% similar
                        </span>
                      )}
                      <span>{rec.recommendation_reason}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && searchResults.length === 0 && !error && (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No memories found</h3>
          <p className="text-gray-500">
            Try adjusting your search criteria or use different search types to find relevant memories.
          </p>
        </div>
      )}
    </div>
  );
};

export default AdvancedSearch; 