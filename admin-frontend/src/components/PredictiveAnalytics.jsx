import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PredictiveAnalytics = () => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [projectAnalytics, setProjectAnalytics] = useState(null);
  const [activeTab, setActiveTab] = useState('analysis');
  const [error, setError] = useState(null);

  const languages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'cpp', label: 'C++' },
    { value: 'csharp', label: 'C#' }
  ];

  const analyzeCode = async () => {
    if (!code.trim()) {
      setError('Please enter some code to analyze');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://api:8000/predictive/analyze', {
        code: code,
        language: language,
        file_path: 'test.py',
        project_name: 'test-project',
        namespace: 'test-project/private'
      });

      setAnalysisResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getProjectAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get('http://api:8000/predictive/project/test-project/analytics');
      setProjectAnalytics(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load project analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'project') {
      getProjectAnalytics();
    }
  }, [activeTab]);

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const renderAnalysisTab = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Code Analysis</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Programming Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {languages.map(lang => (
                <option key={lang.value} value={lang.value}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Code to Analyze
          </label>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter your code here..."
            className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          />
        </div>

        <button
          onClick={analyzeCode}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Analyze Code'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {analysisResult && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Analysis Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className={`text-2xl font-bold ${getRiskLevelColor(analysisResult.risk_level)}`}>
                  {analysisResult.risk_level.toUpperCase()}
                </div>
                <div className="text-sm text-gray-600">Risk Level</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {analysisResult.confidence.toFixed(2)}
                </div>
                <div className="text-sm text-gray-600">Confidence</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {analysisResult.predictions.length}
                </div>
                <div className="text-sm text-gray-600">Predictions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {analysisResult.recommendations.length}
                </div>
                <div className="text-sm text-gray-600">Recommendations</div>
              </div>
            </div>
          </div>

          {/* Predictions */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Predictions</h3>
            <div className="space-y-4">
              {analysisResult.predictions.map((prediction, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-gray-900">{prediction.message}</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Category: {prediction.category} | Confidence: {(prediction.confidence * 100).toFixed(1)}%
                      </p>
                      {prediction.line && (
                        <p className="text-sm text-gray-500 mt-1">
                          Line {prediction.line}, Column {prediction.column}
                        </p>
                      )}
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(prediction.severity)}`}>
                      {prediction.severity}
                    </span>
                  </div>
                  {prediction.fix && (
                    <div className="mt-2 p-3 bg-blue-50 rounded">
                      <p className="text-sm font-medium text-blue-800">Fix:</p>
                      <p className="text-sm text-blue-700">{prediction.fix}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Factors */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Analysis Factors</h3>
            <div className="flex flex-wrap gap-2">
              {analysisResult.factors.map((factor, index) => (
                <span key={index} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                  {factor}
                </span>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
            <div className="space-y-3">
              {analysisResult.recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start">
                  <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-green-600 text-sm">✓</span>
                  </div>
                  <p className="text-gray-700">{recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderProjectTab = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Project Analytics</h3>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading project analytics...</p>
          </div>
        ) : projectAnalytics ? (
          <div className="space-y-6">
            {/* Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className={`text-2xl font-bold ${getRiskLevelColor(projectAnalytics.overall_risk_level)}`}>
                  {projectAnalytics.overall_risk_level.toUpperCase()}
                </div>
                <div className="text-sm text-gray-600">Overall Risk</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {projectAnalytics.high_risk_issues}
                </div>
                <div className="text-sm text-gray-600">High Risk Issues</div>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {projectAnalytics.medium_risk_issues}
                </div>
                <div className="text-sm text-gray-600">Medium Risk Issues</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {projectAnalytics.low_risk_issues}
                </div>
                <div className="text-sm text-gray-600">Low Risk Issues</div>
              </div>
            </div>

            {/* Trend Analysis */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">Trend Analysis</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Risk Trend</div>
                  <div className={`font-medium ${projectAnalytics.trend_analysis.risk_trend === 'decreasing' ? 'text-green-600' : 'text-red-600'}`}>
                    {projectAnalytics.trend_analysis.risk_trend}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Code Quality Score</div>
                  <div className="font-medium text-blue-600">
                    {projectAnalytics.trend_analysis.code_quality_score}/100
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Prediction Count</div>
                  <div className="font-medium text-gray-900">
                    {projectAnalytics.trend_analysis.prediction_count}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">High Risk Issues</div>
                  <div className={`font-medium ${projectAnalytics.trend_analysis.high_risk_issues === 'decreasing' ? 'text-green-600' : 'text-red-600'}`}>
                    {projectAnalytics.trend_analysis.high_risk_issues}
                  </div>
                </div>
              </div>
            </div>

            {/* Top Recommendations */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Top Recommendations</h4>
              <div className="space-y-2">
                {projectAnalytics.top_recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                      <span className="text-blue-600 text-sm">{index + 1}</span>
                    </div>
                    <p className="text-gray-700">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-600">
            No project analytics available
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Predictive Analytics</h1>
        <p className="text-gray-600">
          Advanced code analysis that predicts potential issues before they become problems
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('analysis')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'analysis'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Code Analysis
          </button>
          <button
            onClick={() => setActiveTab('project')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'project'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Project Analytics
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'analysis' ? renderAnalysisTab() : renderProjectTab()}
    </div>
  );
};

export default PredictiveAnalytics; 