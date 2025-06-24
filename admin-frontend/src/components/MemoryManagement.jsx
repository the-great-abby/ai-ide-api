import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Database, 
  RefreshCw, 
  Trash2, 
  TrendingUp,
  BarChart3,
  Target,
  Zap,
  Shield
} from 'lucide-react';

const MemoryManagement = () => {
  const [analytics, setAnalytics] = useState(null);
  const [cleanupReport, setCleanupReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedNamespace, setSelectedNamespace] = useState('');
  const [selectedMemoryIds, setSelectedMemoryIds] = useState([]);
  const [dryRun, setDryRun] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [selectedNamespace]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.get('/memory/analytics/summary', {
        params: { namespace: selectedNamespace || undefined }
      });
      
      setAnalytics(response.data);
    } catch (err) {
      setError('Failed to load analytics');
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCleanupReport = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.get('/memory/cleanup/report', {
        params: { namespace: selectedNamespace || undefined }
      });
      
      setCleanupReport(response.data);
    } catch (err) {
      setError('Failed to load cleanup report');
      console.error('Error loading cleanup report:', err);
    } finally {
      setLoading(false);
    }
  };

  const batchUpdateConfidence = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.post('/memory/confidence/batch-update', null, {
        params: { namespace: selectedNamespace || undefined }
      });
      
      // Reload analytics after update
      await loadAnalytics();
      
      alert(`Updated ${response.data.successful_updates} memories successfully`);
    } catch (err) {
      setError('Failed to update confidence scores');
      console.error('Error updating confidence:', err);
    } finally {
      setLoading(false);
    }
  };

  const inferRelationships = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.post('/memory/relationships/infer', null, {
        params: { 
          namespace: selectedNamespace || undefined,
          limit: 100
        }
      });
      
      alert(`Inferred ${response.data.relationships_inferred} new relationships`);
    } catch (err) {
      setError('Failed to infer relationships');
      console.error('Error inferring relationships:', err);
    } finally {
      setLoading(false);
    }
  };

  const executeCleanup = async () => {
    if (!cleanupReport || cleanupReport.candidates.length === 0) {
      alert('No cleanup candidates available');
      return;
    }

    const candidateIds = cleanupReport.candidates.map(c => c.id);
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.post('/memory/cleanup/execute', {
        memory_ids: candidateIds,
        dry_run: dryRun
      });
      
      if (dryRun) {
        alert(`Dry run completed: ${response.data.successful} memories would be deleted`);
      } else {
        alert(`Cleanup completed: ${response.data.successful} memories deleted`);
        // Reload reports
        await loadCleanupReport();
        await loadAnalytics();
      }
    } catch (err) {
      setError('Failed to execute cleanup');
      console.error('Error executing cleanup:', err);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceIcon = (score) => {
    if (score >= 0.7) return <CheckCircle className="h-4 w-4" />;
    if (score >= 0.4) return <AlertTriangle className="h-4 w-4" />;
    return <AlertTriangle className="h-4 w-4" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading memory management...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Memory Management</h1>
            <p className="text-sm text-gray-600">Advanced memory lifecycle and confidence management</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadAnalytics}
              className="p-2 text-gray-400 hover:text-gray-600"
              title="Refresh Analytics"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Namespace Filter
            </label>
            <input
              type="text"
              placeholder="All namespaces"
              value={selectedNamespace}
              onChange={(e) => setSelectedNamespace(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div className="flex items-end space-x-2">
            <button
              onClick={batchUpdateConfidence}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2"
            >
              <Zap className="h-4 w-4" />
              <span>Update Confidence</span>
            </button>
            
            <button
              onClick={inferRelationships}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center space-x-2"
            >
              <Target className="h-4 w-4" />
              <span>Infer Relationships</span>
            </button>
            
            <button
              onClick={loadCleanupReport}
              className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 flex items-center space-x-2"
            >
              <Trash2 className="h-4 w-4" />
              <span>Cleanup Report</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="text-red-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Analytics Summary */}
      {analytics && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2" />
            Memory Analytics Summary
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Total Memories */}
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Database className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-blue-600">Total Memories</p>
                  <p className="text-2xl font-bold text-blue-900">{analytics.total_memories}</p>
                </div>
              </div>
            </div>
            
            {/* Total Relationships */}
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Target className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-600">Total Relationships</p>
                  <p className="text-2xl font-bold text-green-900">{analytics.total_relationships}</p>
                </div>
              </div>
            </div>
            
            {/* Average Confidence */}
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Shield className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-purple-600">Avg Confidence</p>
                  <p className="text-2xl font-bold text-purple-900">
                    {(analytics.analytics.confidence.average * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
            
            {/* Average Age */}
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Clock className="h-6 w-6 text-orange-600" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-orange-600">Avg Age</p>
                  <p className="text-2xl font-bold text-orange-900">
                    {analytics.analytics.age.average_days.toFixed(0)} days
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Analytics */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Confidence Distribution */}
            <div>
              <h3 className="text-md font-medium text-gray-900 mb-3">Confidence Distribution</h3>
              <div className="space-y-2">
                {Object.entries(analytics.analytics.confidence.distribution).map(([level, count]) => (
                  <div key={level} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{level}</span>
                    <span className="text-sm font-medium text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Age Distribution */}
            <div>
              <h3 className="text-md font-medium text-gray-900 mb-3">Age Distribution</h3>
              <div className="space-y-2">
                {Object.entries(analytics.analytics.age.distribution).map(([age, count]) => (
                  <div key={age} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{age.replace('_', ' ')}</span>
                    <span className="text-sm font-medium text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Top Tags */}
          {analytics.analytics.top_tags.length > 0 && (
            <div className="mt-6">
              <h3 className="text-md font-medium text-gray-900 mb-3">Top Tags</h3>
              <div className="flex flex-wrap gap-2">
                {analytics.analytics.top_tags.slice(0, 10).map(([tag, count]) => (
                  <span key={tag} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    {tag} ({count})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Cleanup Report */}
      {cleanupReport && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Trash2 className="h-5 w-5 mr-2" />
              Cleanup Report
            </h2>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="dryRun"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <label htmlFor="dryRun" className="text-sm text-gray-700">
                  Dry Run
                </label>
              </div>
              
              <button
                onClick={executeCleanup}
                disabled={cleanupReport.candidates.length === 0}
                className={`px-4 py-2 rounded-md flex items-center space-x-2 ${
                  cleanupReport.candidates.length === 0
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-red-600 text-white hover:bg-red-700'
                }`}
              >
                <Trash2 className="h-4 w-4" />
                <span>{dryRun ? 'Simulate Cleanup' : 'Execute Cleanup'}</span>
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-red-100 rounded-lg">
                  <AlertTriangle className="h-6 w-6 text-red-600" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-600">Total Candidates</p>
                  <p className="text-2xl font-bold text-red-900">{cleanupReport.total_candidates}</p>
                </div>
              </div>
            </div>
            
            {Object.entries(cleanupReport.by_confidence).map(([level, count]) => (
              <div key={level} className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <Shield className="h-6 w-6 text-gray-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-600 capitalize">{level} Confidence</p>
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Cleanup Candidates */}
          {cleanupReport.candidates.length > 0 && (
            <div>
              <h3 className="text-md font-medium text-gray-900 mb-3">Cleanup Candidates</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {cleanupReport.candidates.map((candidate) => (
                  <div key={candidate.id} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {candidate.content_preview}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Namespace: {candidate.namespace} • Age: {candidate.age_days} days
                        </p>
                        <p className="text-xs text-gray-500">
                          Confidence: {(candidate.confidence_score * 100).toFixed(1)}% • 
                          Importance: {(candidate.importance_score * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="ml-3">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {candidate.cleanup_reason}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MemoryManagement; 