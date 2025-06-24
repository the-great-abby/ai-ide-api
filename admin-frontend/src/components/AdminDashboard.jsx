import React, { useEffect, useState } from 'react';
import apiClient from '../utils/apiClient';

function AdminDashboard() {
  const [proposals, setProposals] = useState([]);
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [approving, setApproving] = useState({});
  const [rejecting, setRejecting] = useState({});
  const [showDetails, setShowDetails] = useState({});
  const [showRuleDetails, setShowRuleDetails] = useState({});
  const [categoryFilter, setCategoryFilter] = useState([]);
  const [tagFilter, setTagFilter] = useState([]);
  const [bugDescription, setBugDescription] = useState("");
  const [bugReporter, setBugReporter] = useState("");
  const [bugPage, setBugPage] = useState("/admin");
  const [bugStatus, setBugStatus] = useState(null);
  const [bugSubmitting, setBugSubmitting] = useState(false);
  const [enhancements, setEnhancements] = useState([]);
  const [loadingEnhancements, setLoadingEnhancements] = useState(true);
  const [enhancementsError, setEnhancementsError] = useState(null);
  const [transferring, setTransferring] = useState({});
  const [transferStatus, setTransferStatus] = useState({});
  const [rejectingEnh, setRejectingEnh] = useState({});
  const [rejectStatus, setRejectStatus] = useState({});
  const [reverting, setReverting] = useState({});
  const [revertStatus, setRevertStatus] = useState({});
  const [acceptingEnh, setAcceptingEnh] = useState({});
  const [acceptStatus, setAcceptStatus] = useState({});
  const [completingEnh, setCompletingEnh] = useState({});
  const [completeStatus, setCompleteStatus] = useState({});
  const [warning, setWarning] = useState(null);
  const [showEnhancementDetails, setShowEnhancementDetails] = useState({});

  // Extract unique categories and tags from rules
  const uniqueCategories = Array.from(new Set(rules.flatMap(r => r.categories || []))).filter(Boolean);
  const uniqueTags = Array.from(new Set(rules.flatMap(r => r.tags || []))).filter(Boolean);

  useEffect(() => {
    fetchAll();
    fetchEnhancements();
  }, []);

  const fetchAll = async (categories = categoryFilter, tags = tagFilter) => {
    setLoading(true);
    setError(null);
    let proposalsData = null;
    let rulesData = null;
    let proposalsError = null;
    let rulesError = null;
    try {
      const proposalsPromise = apiClient.get(`/pending-rule-changes`).then(res => res.data.pending_changes).catch(e => { proposalsError = e; return null; });
      const rulesPromise = apiClient.get(`/rules`, {
        params: {
          category: categories.join(','),
          tag: tags.join(',')
        }
      }).then(res => res.data).catch(e => { rulesError = e; return null; });
      [proposalsData, rulesData] = await Promise.all([proposalsPromise, rulesPromise]);
      if (proposalsData) setProposals(proposalsData);
      if (rulesData) setRules(rulesData);
      if (proposalsError && rulesError) {
        setError('Failed to fetch proposals and rules');
        console.error('Both proposals and rules fetch failed:', proposalsError, rulesError);
      } else if (proposalsError || rulesError) {
        setError(null);
        setWarning('Some data could not be loaded.');
        if (proposalsError) console.warn('Failed to fetch proposals:', proposalsError);
        if (rulesError) console.warn('Failed to fetch rules:', rulesError);
      } else {
        setError(null);
        setWarning(null);
      }
    } catch (err) {
      setError('Unexpected error fetching proposals or rules');
      console.error('Unexpected fetchAll error:', err);
    }
    setLoading(false);
    console.log('fetchAll: fetching proposals and rules', { categories, tags });
    console.log('fetchAll results:', {
      proposalsData,
      rulesData,
      proposalsError,
      rulesError
    });
  };

  const fetchEnhancements = async () => {
    setLoadingEnhancements(true);
    setEnhancementsError(null);
    try {
      const res = await apiClient.get(`/enhancements`);
      setEnhancements(res.data);
    } catch (err) {
      setEnhancementsError('Failed to fetch enhancements');
    }
    setLoadingEnhancements(false);
  };

  // Remove client-side category filtering for rules
  const filteredRules = rules.filter(r => {
    const tagMatch = tagFilter.length === 0 || r.tags.some(tag => tagFilter.includes(tag));
    return tagMatch;
  });

  // When category filter changes, fetch from backend
  const handleCategoryFilter = (e) => {
    const selected = Array.from(e.target.selectedOptions, option => option.value);
    setCategoryFilter(selected);
    fetchAll(selected, tagFilter);
  };

  // When tag filter changes, fetch from backend
  const handleTagFilter = (e) => {
    const selected = Array.from(e.target.selectedOptions, option => option.value);
    setTagFilter(selected);
    fetchAll(categoryFilter, selected);
  };

  // Clear filters and fetch all rules
  const clearFilters = () => {
    setCategoryFilter([]);
    setTagFilter([]);
    fetchAll([], []);
  };

  const approveProposal = async (id) => {
    setApproving((prev) => ({ ...prev, [id]: true }));
    try {
      await apiClient.put(`/rule-changes/${id}/approve`);
      setProposals((prev) => prev.filter((p) => p.id !== id));
      fetchAll(); // Refresh rules
    } catch (err) {
      alert('Failed to approve proposal');
    }
    setApproving((prev) => ({ ...prev, [id]: false }));
  };

  const rejectProposal = async (id) => {
    setRejecting((prev) => ({ ...prev, [id]: true }));
    try {
      await apiClient.post(`/reject-rule-change/${id}`);
      setProposals((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      alert('Failed to reject proposal');
    }
    setRejecting((prev) => ({ ...prev, [id]: false }));
  };

  const toggleDetails = (id) => {
    setShowDetails((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleRuleDetails = (id) => {
    setShowRuleDetails((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const submitBugReport = async (e) => {
    e.preventDefault();
    setBugSubmitting(true);
    setBugStatus(null);
    try {
      const res = await apiClient.post(`/bug-report`, {
        description: bugDescription,
        reporter: bugReporter,
        page: bugPage,
      });
      setBugStatus({ success: true, id: res.data.id });
      setBugDescription("");
      setBugReporter("");
      setBugPage("/admin");
    } catch (err) {
      setBugStatus({ success: false, error: err?.response?.data?.detail || "Failed to submit bug report" });
    }
    setBugSubmitting(false);
  };

  const transferEnhancement = async (id) => {
    setTransferring((prev) => ({ ...prev, [id]: true }));
    setTransferStatus((prev) => ({ ...prev, [id]: null }));
    try {
      const res = await apiClient.post(`/enhancement-to-proposal/${id}`);
      setTransferStatus((prev) => ({ ...prev, [id]: { success: true, proposal_id: res.data.proposal_id } }));
      fetchEnhancements();
      fetchAll();
    } catch (err) {
      setTransferStatus((prev) => ({ ...prev, [id]: { success: false, error: err?.response?.data?.detail || 'Failed to transfer' } }));
    }
    setTransferring((prev) => ({ ...prev, [id]: false }));
  };

  const rejectEnhancement = async (id) => {
    setRejectingEnh((prev) => ({ ...prev, [id]: true }));
    setRejectStatus((prev) => ({ ...prev, [id]: null }));
    try {
      const res = await apiClient.post(`/reject-enhancement/${id}`);
      setRejectStatus((prev) => ({ ...prev, [id]: { success: true } }));
      fetchEnhancements();
    } catch (err) {
      setRejectStatus((prev) => ({ ...prev, [id]: { success: false, error: err?.response?.data?.detail || 'Failed to reject' } }));
    }
    setRejectingEnh((prev) => ({ ...prev, [id]: false }));
  };

  const revertProposalToEnhancement = async (id) => {
    setReverting((prev) => ({ ...prev, [id]: true }));
    setRevertStatus((prev) => ({ ...prev, [id]: null }));
    try {
      const res = await apiClient.post(`/proposal-to-enhancement/${id}`);
      setRevertStatus((prev) => ({ ...prev, [id]: { success: true, enhancement_id: res.data.enhancement_id } }));
      fetchEnhancements();
      fetchAll();
    } catch (err) {
      setRevertStatus((prev) => ({ ...prev, [id]: { success: false, error: err?.response?.data?.detail || 'Failed to revert' } }));
    }
    setReverting((prev) => ({ ...prev, [id]: false }));
  };

  const acceptEnhancement = async (id) => {
    setAcceptingEnh((prev) => ({ ...prev, [id]: true }));
    setAcceptStatus((prev) => ({ ...prev, [id]: null }));
    try {
      const res = await apiClient.post(`/accept-enhancement/${id}`);
      setAcceptStatus((prev) => ({ ...prev, [id]: { success: true } }));
      fetchEnhancements();
    } catch (err) {
      setAcceptStatus((prev) => ({ ...prev, [id]: { success: false, error: err?.response?.data?.detail || 'Failed to accept' } }));
    }
    setAcceptingEnh((prev) => ({ ...prev, [id]: false }));
  };

  const completeEnhancement = async (id) => {
    setCompletingEnh((prev) => ({ ...prev, [id]: true }));
    setCompleteStatus((prev) => ({ ...prev, [id]: null }));
    try {
      const res = await apiClient.post(`/complete-enhancement/${id}`);
      setCompleteStatus((prev) => ({ ...prev, [id]: { success: true } }));
      fetchEnhancements();
    } catch (err) {
      setCompleteStatus((prev) => ({ ...prev, [id]: { success: false, error: err?.response?.data?.detail || 'Failed to complete' } }));
    }
    setCompletingEnh((prev) => ({ ...prev, [id]: false }));
  };

  const toggleEnhancementDetails = (id) => {
    setShowEnhancementDetails((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Admin Rule Proposals</h1>
      <button 
        onClick={() => fetchAll(categoryFilter, tagFilter)} 
        className="mb-6 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Refresh
      </button>
      
      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          {error && <p className="text-red-600 mb-4">{error}</p>}
          {warning && <p className="text-orange-600 mb-4">{warning}</p>}

          <h2 className="text-2xl font-semibold mb-4">Pending Proposals</h2>
          {proposals.length === 0 ? (
            <p>No pending proposals.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300 mb-8">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 px-4 py-2">ID</th>
                    <th className="border border-gray-300 px-4 py-2">Type</th>
                    <th className="border border-gray-300 px-4 py-2">Description</th>
                    <th className="border border-gray-300 px-4 py-2">Submitted By</th>
                    <th className="border border-gray-300 px-4 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {proposals.map((p) => (
                    <React.Fragment key={p.id}>
                      <tr>
                        <td className="border border-gray-300 px-4 py-2">{p.id}</td>
                        <td className="border border-gray-300 px-4 py-2">{p.rule_type}</td>
                        <td className="border border-gray-300 px-4 py-2">{p.description}</td>
                        <td className="border border-gray-300 px-4 py-2">{p.submitted_by}</td>
                        <td className="border border-gray-300 px-4 py-2">
                          <button
                            onClick={() => approveProposal(p.id)}
                            disabled={approving[p.id]}
                            className="mr-2 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                          >
                            {approving[p.id] ? 'Approving...' : 'Approve'}
                          </button>
                          <button
                            onClick={() => rejectProposal(p.id)}
                            disabled={rejecting[p.id]}
                            className="mr-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                          >
                            {rejecting[p.id] ? 'Rejecting...' : 'Reject'}
                          </button>
                          <button 
                            onClick={() => toggleDetails(p.id)}
                            className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
                          >
                            {showDetails[p.id] ? 'Hide Details' : 'Details'}
                          </button>
                        </td>
                      </tr>
                      {showDetails[p.id] && (
                        <tr>
                          <td colSpan={5} className="border border-gray-300 px-4 py-2 bg-gray-50">
                            <strong>Full Proposal:</strong>
                            <pre className="bg-gray-100 p-4 rounded mt-2 overflow-x-auto whitespace-pre-wrap">
                              {JSON.stringify(p, null, 2)}
                            </pre>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h2 className="text-2xl font-semibold mb-4">Approved Rules</h2>
          {filteredRules.length === 0 ? (
            <p>No approved rules.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300 mb-8">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 px-4 py-2">ID</th>
                    <th className="border border-gray-300 px-4 py-2">Type</th>
                    <th className="border border-gray-300 px-4 py-2">Description</th>
                    <th className="border border-gray-300 px-4 py-2">User Story</th>
                    <th className="border border-gray-300 px-4 py-2">Added By</th>
                    <th className="border border-gray-300 px-4 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRules.map((r) => (
                    <React.Fragment key={r.id}>
                      <tr>
                        <td className="border border-gray-300 px-4 py-2">{r.id}</td>
                        <td className="border border-gray-300 px-4 py-2">{r.rule_type}</td>
                        <td className="border border-gray-300 px-4 py-2">{r.description}</td>
                        <td className="border border-gray-300 px-4 py-2">{r.user_story || <span className="text-gray-400">—</span>}</td>
                        <td className="border border-gray-300 px-4 py-2">{r.added_by}</td>
                        <td className="border border-gray-300 px-4 py-2">
                          <button 
                            onClick={() => toggleRuleDetails(r.id)}
                            className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
                          >
                            {showRuleDetails[r.id] ? 'Hide Details' : 'Details'}
                          </button>
                        </td>
                      </tr>
                      {showRuleDetails[r.id] && (
                        <tr>
                          <td colSpan={6} className="border border-gray-300 px-4 py-2 bg-gray-50">
                            <strong>Full Rule:</strong>
                            <pre className="bg-gray-100 p-4 rounded mt-2 overflow-x-auto whitespace-pre-wrap">
                              {JSON.stringify(r, null, 2)}
                            </pre>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Bug Report Form */}
          <div className="mt-10 p-6 border border-gray-300 rounded-lg max-w-2xl mx-auto">
            <h2 className="text-2xl font-semibold mb-4">Report a Bug</h2>
            <form onSubmit={submitBugReport}>
              <div className="mb-4">
                <label className="block mb-2">
                  Description (required):
                  <textarea 
                    value={bugDescription} 
                    onChange={e => setBugDescription(e.target.value)} 
                    required 
                    rows={3} 
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </label>
              </div>
              <div className="mb-4">
                <label className="block mb-2">
                  Your Name or Email (optional):
                  <input 
                    type="text" 
                    value={bugReporter} 
                    onChange={e => setBugReporter(e.target.value)} 
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </label>
              </div>
              <div className="mb-4">
                <label className="block mb-2">
                  Page (optional):
                  <input 
                    type="text" 
                    value={bugPage} 
                    onChange={e => setBugPage(e.target.value)} 
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </label>
              </div>
              <button 
                type="submit" 
                disabled={bugSubmitting || !bugDescription}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {bugSubmitting ? 'Submitting...' : 'Submit Bug Report'}
              </button>
            </form>
            {bugStatus && bugStatus.success && (
              <p className="text-green-600 mt-4">Thank you! Bug report submitted (ID: {bugStatus.id})</p>
            )}
            {bugStatus && !bugStatus.success && (
              <p className="text-red-600 mt-4">Error: {bugStatus.error}</p>
            )}
          </div>

          {/* Enhancements Section */}
          <div className="mt-10 p-6 border border-gray-300 rounded-lg max-w-6xl mx-auto">
            <h2 className="text-2xl font-semibold mb-4">Suggested Enhancements</h2>
            <button 
              onClick={fetchEnhancements} 
              className="mb-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Refresh Enhancements
            </button>
            
            {loadingEnhancements ? (
              <p>Loading enhancements...</p>
            ) : enhancementsError ? (
              <p className="text-red-600">{enhancementsError}</p>
            ) : enhancements.length === 0 ? (
              <p>No enhancements submitted yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300 text-sm">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-300 px-4 py-2">ID</th>
                      <th className="border border-gray-300 px-4 py-2">Description</th>
                      <th className="border border-gray-300 px-4 py-2">Suggested By</th>
                      <th className="border border-gray-300 px-4 py-2">Page</th>
                      <th className="border border-gray-300 px-4 py-2">Tags</th>
                      <th className="border border-gray-300 px-4 py-2">Categories</th>
                      <th className="border border-gray-300 px-4 py-2">Timestamp</th>
                      <th className="border border-gray-300 px-4 py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enhancements.map(e => (
                      <React.Fragment key={e.id}>
                        <tr>
                          <td className="border border-gray-300 px-4 py-2 max-w-32 break-all">{e.id}</td>
                          <td className="border border-gray-300 px-4 py-2">{e.description}</td>
                          <td className="border border-gray-300 px-4 py-2">{e.suggested_by}</td>
                          <td className="border border-gray-300 px-4 py-2">{e.page}</td>
                          <td className="border border-gray-300 px-4 py-2">{(e.tags || []).join(', ')}</td>
                          <td className="border border-gray-300 px-4 py-2">{(e.categories || []).join(', ')}</td>
                          <td className="border border-gray-300 px-4 py-2">{e.timestamp}</td>
                          <td className="border border-gray-300 px-4 py-2">
                            {e.status === 'open' ? (
                              <>
                                <button
                                  onClick={() => transferEnhancement(e.id)}
                                  disabled={transferring[e.id]}
                                  className="mr-2 px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-xs"
                                >
                                  {transferring[e.id] ? 'Transferring...' : 'Transfer to Proposal'}
                                </button>
                                <button
                                  onClick={() => rejectEnhancement(e.id)}
                                  disabled={rejectingEnh[e.id]}
                                  className="mr-2 px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 text-xs"
                                >
                                  {rejectingEnh[e.id] ? 'Rejecting...' : 'Reject'}
                                </button>
                                <button
                                  onClick={() => acceptEnhancement(e.id)}
                                  disabled={acceptingEnh[e.id]}
                                  className="mr-2 px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-xs"
                                >
                                  {acceptingEnh[e.id] ? 'Accepting...' : 'Accept'}
                                </button>
                              </>
                            ) : e.status === 'accepted' ? (
                              <>
                                <button
                                  onClick={() => completeEnhancement(e.id)}
                                  disabled={completingEnh[e.id]}
                                  className="mr-2 px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-xs"
                                >
                                  {completingEnh[e.id] ? 'Completing...' : 'Complete'}
                                </button>
                                <span className="text-blue-600 text-xs">Accepted</span>
                              </>
                            ) : e.status === 'completed' ? (
                              <span className="text-green-600 text-xs">Completed</span>
                            ) : e.status === 'transferred' ? (
                              <span className="text-gray-600 text-xs">Transferred</span>
                            ) : (
                              <span className="text-red-600 text-xs">Rejected</span>
                            )}
                            <button 
                              onClick={() => toggleEnhancementDetails(e.id)} 
                              className="ml-2 px-2 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 text-xs"
                            >
                              {showEnhancementDetails[e.id] ? 'Hide Details' : 'Details'}
                            </button>
                          </td>
                        </tr>
                        {showEnhancementDetails[e.id] && (
                          <tr>
                            <td colSpan={8} className="border border-gray-300 px-4 py-2 bg-gray-50">
                              <strong>Full Enhancement:</strong>
                              <pre className="bg-gray-100 p-4 rounded mt-2 overflow-x-auto whitespace-pre-wrap">
                                {JSON.stringify(e, null, 2)}
                              </pre>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default AdminDashboard; 