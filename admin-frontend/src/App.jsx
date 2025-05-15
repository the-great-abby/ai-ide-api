import { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9103';

function App() {
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
      const proposalsPromise = axios.get(`${API_BASE_URL}/pending-rule-changes`).then(res => res.data).catch(e => { proposalsError = e; return null; });
      const rulesPromise = axios.get(`${API_BASE_URL}/rules`, {
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
      const res = await axios.get(`${API_BASE_URL}/enhancements`);
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
      await axios.post(`${API_BASE_URL}/approve-rule-change/${id}`);
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
      await axios.post(`${API_BASE_URL}/reject-rule-change/${id}`);
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
      const res = await axios.post(`${API_BASE_URL}/bug-report`, {
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
      const res = await axios.post(`${API_BASE_URL}/enhancement-to-proposal/${id}`);
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
      const res = await axios.post(`${API_BASE_URL}/reject-enhancement/${id}`);
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
      const res = await axios.post(`${API_BASE_URL}/proposal-to-enhancement/${id}`);
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
      const res = await axios.post(`${API_BASE_URL}/accept-enhancement/${id}`);
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
      const res = await axios.post(`${API_BASE_URL}/complete-enhancement/${id}`);
      setCompleteStatus((prev) => ({ ...prev, [id]: { success: true } }));
      fetchEnhancements();
    } catch (err) {
      setCompleteStatus((prev) => ({ ...prev, [id]: { success: false, error: err?.response?.data?.detail || 'Failed to complete' } }));
    }
    setCompletingEnh((prev) => ({ ...prev, [id]: false }));
  };

  return (
    <div className="App">
      <h1>Admin Rule Proposals</h1>
      <button onClick={() => fetchAll(categoryFilter, tagFilter)} style={{ marginBottom: 20 }}>Refresh</button>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          {/* Show error/warning above tables if present */}
          {error && <p style={{ color: 'red' }}>{error}</p>}
          {warning && <p style={{ color: 'orange' }}>{warning}</p>}

          <h2>Pending Proposals</h2>
          {proposals.length === 0 ? (
            <p>No pending proposals.</p>
          ) : (
            <table style={{ margin: '0 auto' }}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Submitted By</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {proposals.map((p) => (
                  <>
                  <tr key={p.id}>
                    <td>{p.id}</td>
                    <td>{p.rule_type}</td>
                    <td>{p.description}</td>
                    <td>{p.submitted_by}</td>
                    <td>
                      <button
                        onClick={() => approveProposal(p.id)}
                        disabled={approving[p.id]}
                        style={{ marginRight: 8 }}
                      >
                        {approving[p.id] ? 'Approving...' : 'Approve'}
                      </button>
                      <button
                        onClick={() => rejectProposal(p.id)}
                        disabled={rejecting[p.id]}
                        style={{ marginRight: 8 }}
                      >
                        {rejecting[p.id] ? 'Rejecting...' : 'Reject'}
                      </button>
                      {(p.status === 'pending' || p.status === 'rejected') && (
                        <button
                          onClick={() => revertProposalToEnhancement(p.id)}
                          disabled={reverting[p.id]}
                          style={{ marginRight: 8 }}
                        >
                          {reverting[p.id] ? 'Reverting...' : 'Move back to Enhancement'}
                        </button>
                      )}
                      <button onClick={() => toggleDetails(p.id)}>
                        {showDetails[p.id] ? 'Hide Details' : 'Details'}
                      </button>
                    </td>
                  </tr>
                  {showDetails[p.id] && (
                    <tr>
                      <td colSpan={5} style={{ background: '#f9f9f9', textAlign: 'left' }}>
                        <strong>Full Proposal:</strong>
                        <pre style={{
                          background: '#f5f5f5',
                          color: '#222',
                          padding: 8,
                          borderRadius: 4,
                          fontSize: '1em',
                          overflowX: 'auto',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word'
                        }}>{JSON.stringify(p, null, 2)}</pre>
                        {p.diff && (
                          <>
                            <strong>Diff:</strong>
                            <pre style={{
                              background: '#f5f5f5',
                              color: '#222',
                              padding: 8,
                              borderRadius: 4,
                              fontSize: '1em',
                              overflowX: 'auto',
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word'
                            }}>{p.diff}</pre>
                          </>
                        )}
                      </td>
                    </tr>
                  )}
                  {revertStatus[p.id] && revertStatus[p.id].success && (
                    <tr>
                      <td colSpan={5} style={{ background: '#f9f9f9', textAlign: 'left' }}>
                        <strong>Reverted to Enhancement:</strong>
                        <div style={{ color: 'green', fontSize: 12 }}>Reverted! Enhancement ID: {revertStatus[p.id].enhancement_id}</div>
                      </td>
                    </tr>
                  )}
                  {revertStatus[p.id] && !revertStatus[p.id].success && (
                    <tr>
                      <td colSpan={5} style={{ background: '#f9f9f9', textAlign: 'left' }}>
                        <strong>Revert Error:</strong>
                        <div style={{ color: 'red', fontSize: 12 }}>{revertStatus[p.id].error}</div>
                      </td>
                    </tr>
                  )}
                  </>
                ))}
              </tbody>
            </table>
          )}

          <h2 style={{ marginTop: 40 }}>Approved Rules</h2>
          {uniqueCategories.length > 0 || uniqueTags.length > 0 ? (
            <div style={{ marginBottom: 16 }}>
              <label style={{ marginRight: 8 }}>
                Categories:
                <select multiple value={categoryFilter} onChange={handleCategoryFilter} style={{ marginLeft: 4, marginRight: 8 }}>
                  {uniqueCategories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </label>
              <label style={{ marginRight: 8 }}>
                Tags:
                <select multiple value={tagFilter} onChange={handleTagFilter} style={{ marginLeft: 4, marginRight: 8 }}>
                  {uniqueTags.map(tag => (
                    <option key={tag} value={tag}>{tag}</option>
                  ))}
                </select>
              </label>
              <button onClick={clearFilters}>Clear Filters</button>
            </div>
          ) : null}
          {(categoryFilter.length > 0 || tagFilter.length > 0) && (
            <div style={{ marginBottom: 8 }}>
              <strong>Current Filters:</strong>
              {categoryFilter.length > 0 && <span> Categories: {categoryFilter.join(', ')}</span>}
              {tagFilter.length > 0 && <span> Tags: {tagFilter.join(', ')}</span>}
            </div>
          )}
          {filteredRules.length === 0 ? (
            <p>No approved rules.</p>
          ) : (
            <table style={{ margin: '0 auto' }}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Added By</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRules.map((r) => (
                  <>
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td>{r.rule_type}</td>
                    <td>{r.description}</td>
                    <td>{r.added_by}</td>
                    <td>
                      <button onClick={() => toggleRuleDetails(r.id)}>
                        {showRuleDetails[r.id] ? 'Hide Details' : 'Details'}
                      </button>
                    </td>
                  </tr>
                  {showRuleDetails[r.id] && (
                    <tr>
                      <td colSpan={5} style={{ background: '#f0f0f0', textAlign: 'left' }}>
                        <strong>Full Rule:</strong>
                        <pre style={{
                          background: '#f5f5f5',
                          color: '#222',
                          padding: 8,
                          borderRadius: 4,
                          fontSize: '1em',
                          overflowX: 'auto',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word'
                        }}>{JSON.stringify(r, null, 2)}</pre>
                        {r.diff && (
                          <>
                            <strong>Diff:</strong>
                            <pre style={{
                              background: '#f5f5f5',
                              color: '#222',
                              padding: 8,
                              borderRadius: 4,
                              fontSize: '1em',
                              overflowX: 'auto',
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word'
                            }}>{r.diff}</pre>
                          </>
                        )}
                      </td>
                    </tr>
                  )}
                  </>
                ))}
              </tbody>
            </table>
          )}

          {/* Bug Report Form */}
          <div style={{ marginTop: 40, padding: 20, border: '1px solid #ccc', borderRadius: 8, maxWidth: 600, marginLeft: 'auto', marginRight: 'auto' }}>
            <h2>Report a Bug</h2>
            <form onSubmit={submitBugReport}>
              <div style={{ marginBottom: 12 }}>
                <label>Description (required):<br />
                  <textarea value={bugDescription} onChange={e => setBugDescription(e.target.value)} required rows={3} style={{ width: '100%' }} />
                </label>
              </div>
              <div style={{ marginBottom: 12 }}>
                <label>Your Name or Email (optional):<br />
                  <input type="text" value={bugReporter} onChange={e => setBugReporter(e.target.value)} style={{ width: '100%' }} />
                </label>
              </div>
              <div style={{ marginBottom: 12 }}>
                <label>Page (optional):<br />
                  <input type="text" value={bugPage} onChange={e => setBugPage(e.target.value)} style={{ width: '100%' }} />
                </label>
              </div>
              <button type="submit" disabled={bugSubmitting || !bugDescription}>{bugSubmitting ? 'Submitting...' : 'Submit Bug Report'}</button>
            </form>
            {bugStatus && bugStatus.success && (
              <p style={{ color: 'green', marginTop: 10 }}>Thank you! Bug report submitted (ID: {bugStatus.id})</p>
            )}
            {bugStatus && !bugStatus.success && (
              <p style={{ color: 'red', marginTop: 10 }}>Error: {bugStatus.error}</p>
            )}
          </div>

          {/* Enhancements Section */}
          <div style={{ marginTop: 40, padding: 20, border: '1px solid #ccc', borderRadius: 8, maxWidth: 900, marginLeft: 'auto', marginRight: 'auto' }}>
            <h2>Suggested Enhancements</h2>
            <button onClick={fetchEnhancements} style={{ marginBottom: 16 }}>Refresh Enhancements</button>
            {loadingEnhancements ? (
              <p>Loading enhancements...</p>
            ) : enhancementsError ? (
              <p style={{ color: 'red' }}>{enhancementsError}</p>
            ) : enhancements.length === 0 ? (
              <p>No enhancements submitted yet.</p>
            ) : (
              <table style={{ margin: '0 auto', width: '100%', fontSize: 14 }}>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Description</th>
                    <th>Suggested By</th>
                    <th>Page</th>
                    <th>Tags</th>
                    <th>Categories</th>
                    <th>Timestamp</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {enhancements.map(e => (
                    <tr key={e.id}>
                      <td style={{ maxWidth: 120, wordBreak: 'break-all' }}>{e.id}</td>
                      <td>{e.description}</td>
                      <td>{e.suggested_by}</td>
                      <td>{e.page}</td>
                      <td>{(e.tags || []).join(', ')}</td>
                      <td>{(e.categories || []).join(', ')}</td>
                      <td>{e.timestamp}</td>
                      <td>
                        {e.status === 'open' ? (
                          <>
                            <button
                              onClick={() => transferEnhancement(e.id)}
                              disabled={transferring[e.id]}
                              style={{ marginRight: 8 }}
                            >
                              {transferring[e.id] ? 'Transferring...' : 'Transfer to Proposal'}
                            </button>
                            <button
                              onClick={() => rejectEnhancement(e.id)}
                              disabled={rejectingEnh[e.id]}
                              style={{ marginRight: 8 }}
                            >
                              {rejectingEnh[e.id] ? 'Rejecting...' : 'Reject'}
                            </button>
                            <button
                              onClick={() => acceptEnhancement(e.id)}
                              disabled={acceptingEnh[e.id]}
                              style={{ marginRight: 8 }}
                            >
                              {acceptingEnh[e.id] ? 'Accepting...' : 'Accept'}
                            </button>
                          </>
                        ) : e.status === 'accepted' ? (
                          <>
                            <button
                              onClick={() => completeEnhancement(e.id)}
                              disabled={completingEnh[e.id]}
                              style={{ marginRight: 8 }}
                            >
                              {completingEnh[e.id] ? 'Completing...' : 'Complete'}
                            </button>
                            <span style={{ color: 'blue' }}>Accepted</span>
                          </>
                        ) : e.status === 'completed' ? (
                          <span style={{ color: 'green' }}>Completed</span>
                        ) : e.status === 'transferred' ? (
                          <span style={{ color: 'gray' }}>Transferred</span>
                        ) : (
                          <span style={{ color: 'red' }}>Rejected</span>
                        )}
                        {transferStatus[e.id] && transferStatus[e.id].success && (
                          <div style={{ color: 'green', fontSize: 12 }}>Transferred! Proposal ID: {transferStatus[e.id].proposal_id}</div>
                        )}
                        {transferStatus[e.id] && !transferStatus[e.id].success && (
                          <div style={{ color: 'red', fontSize: 12 }}>Error: {transferStatus[e.id].error}</div>
                        )}
                        {rejectStatus[e.id] && rejectStatus[e.id].success && (
                          <div style={{ color: 'red', fontSize: 12 }}>Rejected!</div>
                        )}
                        {rejectStatus[e.id] && !rejectStatus[e.id].success && (
                          <div style={{ color: 'red', fontSize: 12 }}>Error: {rejectStatus[e.id].error}</div>
                        )}
                        {acceptStatus[e.id] && acceptStatus[e.id].success && (
                          <div style={{ color: 'blue', fontSize: 12 }}>Accepted!</div>
                        )}
                        {acceptStatus[e.id] && !acceptStatus[e.id].success && (
                          <div style={{ color: 'red', fontSize: 12 }}>{acceptStatus[e.id].error}</div>
                        )}
                        {completeStatus[e.id] && completeStatus[e.id].success && (
                          <div style={{ color: 'green', fontSize: 12 }}>Completed!</div>
                        )}
                        {completeStatus[e.id] && !completeStatus[e.id].success && (
                          <div style={{ color: 'red', fontSize: 12 }}>{completeStatus[e.id].error}</div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default App;
