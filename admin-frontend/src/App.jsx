import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import AdminDashboard from './components/AdminDashboard';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage';
import MemoryManagement from './components/MemoryManagement';
import AdvancedSearch from './components/AdvancedSearch';
import PredictiveAnalytics from './components/PredictiveAnalytics';
import { Database, Network, Settings, Search, TrendingUp } from 'lucide-react';
import './App.css';

// Navigation component
const Navigation = () => {
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">AI-IDE Admin</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link
                to="/"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                <Database className="h-4 w-4 mr-2" />
                Dashboard
              </Link>
              <Link
                to="/knowledge-graph"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                <Network className="h-4 w-4 mr-2" />
                Knowledge Graph
              </Link>
              <Link
                to="/advanced-search"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                <Search className="h-4 w-4 mr-2" />
                Advanced Search
              </Link>
              <Link
                to="/memory-management"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                <Settings className="h-4 w-4 mr-2" />
                Memory Management
              </Link>
              <Link
                to="/predictive-analytics"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                Predictive Analytics
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Main App component with routing
function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<AdminDashboard />} />
            <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />
            <Route path="/advanced-search" element={<AdvancedSearch />} />
            <Route path="/memory-management" element={<MemoryManagement />} />
            <Route path="/predictive-analytics" element={<PredictiveAnalytics />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
