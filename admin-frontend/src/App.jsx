import { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [proposals, setProposals] = useState([]);
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [approving, setApproving] = useState({});
  const [rejecting, setRejecting] = useState({});
  const [showDetails, setShowDetails] = useState({});
  const [showRuleDetails, setShowRuleDetails] = useState({});

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [proposalsRes, rulesRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/pending-rule-changes`),
        axios.get(`${API_BASE_URL}/rules`)
      ]);
      setProposals(proposalsRes.data);
      setRules(rulesRes.data);
    } catch (err) {
      setError('Failed to fetch proposals or rules');
    }
    setLoading(false);
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

  return (
    <div className="App">
      <h1>Admin Rule Proposals</h1>
      <button onClick={fetchAll} style={{ marginBottom: 20 }}>Refresh</button>
      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p style={{ color: 'red' }}>{error}</p>
      ) : (
        <>
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
                      <button onClick={() => toggleDetails(p.id)}>
                        {showDetails[p.id] ? 'Hide Details' : 'Details'}
                      </button>
                    </td>
                  </tr>
                  {showDetails[p.id] && (
                    <tr>
                      <td colSpan={5} style={{ background: '#f9f9f9', textAlign: 'left' }}>
                        <strong>Full Proposal:</strong>
                        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{JSON.stringify(p, null, 2)}</pre>
                        {p.diff && (
                          <>
                            <strong>Diff:</strong>
                            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#eee', padding: 8 }}>{p.diff}</pre>
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

          <h2 style={{ marginTop: 40 }}>Approved Rules</h2>
          {rules.length === 0 ? (
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
                {rules.map((r) => (
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
                        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{JSON.stringify(r, null, 2)}</pre>
                        {r.diff && (
                          <>
                            <strong>Diff:</strong>
                            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#eee', padding: 8 }}>{r.diff}</pre>
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
        </>
      )}
    </div>
  );
}

export default App;
