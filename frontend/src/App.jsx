import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Database, Send, Table as TableIcon, ChevronRight, ChevronDown, Search, RefreshCw, Terminal,
  Columns, Cpu, History, Settings, Plus, Copy, Bell, User, Paperclip, CheckCircle2, Clock,
  Shield, Zap, BarChart3, Info, Brain, Activity, Lock, Play, Edit2
} from 'lucide-react';
import MechanicalDashboard from './components/MechanicalDashboard';
import CodeBlock from './components/CodeBlock';
import { MechanicalAnalysisCard, PredictionCard, RecommendationCard, InsightsBanner } from './components/MechanicalCards';

const API_BASE = 'http://localhost:8000';

function App() {
  const [databases, setDatabases] = useState([]);
  const [selectedDbType, setSelectedDbType] = useState('postgres');
  const [selectedDbName, setSelectedDbName] = useState('postgres');
  const [activeView, setActiveView] = useState('chat');
  const [showDbDropdown, setShowDbDropdown] = useState(false);
  const [appMode, setAppMode] = useState('data'); // 'data' or 'mechanical'
  const [messages, setMessages] = useState([
    { id: 1, type: 'ai', text: '# Sentinel AI Platform\nWelcome. I can help you analyze data across PostgreSQL and MySQL.\n\n**Select your database source on the left to begin.**' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [queryHistory, setQueryHistory] = useState([]);
  const [userRole, setUserRole] = useState('admin');
  const [threadId] = useState(() => `session_${Date.now()}`);
  const [evalStats, setEvalStats] = useState(null);
  const chatEndRef = useRef(null);

  const fetchDatabases = async (type = selectedDbType) => {
    try {
      const res = await axios.get(`${API_BASE}/databases?db_type=${type}`);
      setDatabases(res.data.databases || []);
    } catch (err) {
      setDatabases([]);
      setSelectedDbName('Offline / No Connection');
    }
  };

  useEffect(() => { fetchDatabases(selectedDbType); }, [selectedDbType]);
  useEffect(() => {
    if (databases.length > 0 && !databases.includes(selectedDbName)) setSelectedDbName(databases[0]);
  }, [databases]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Switch DB when entering mechanical mode
  useEffect(() => {
    if (appMode === 'mechanical') {
      setSelectedDbType('mysql');
      setSelectedDbName('mech_ai_demo');
      setActiveView('dashboard');
      setMessages([{ id: Date.now(), type: 'ai', text: '# 🛡️ Sentinel Industrial Intelligence\nIndustrial Intelligence Mode active. I can analyze machine health, predict failures, and recommend maintenance actions.\n\n**Use the dashboard or ask me a question about your machines.**' }]);
    } else {
      setActiveView('chat');
      fetchDatabases('postgres');
      setMessages([{ id: 1, type: 'ai', text: '# Sentinel AI Platform\nWelcome. I can help you analyze data across PostgreSQL and MySQL.\n\n**Select your database source on the left to begin.**' }]);
    }
  }, [appMode]);

  const handleSend = async (customQuery = null, isRetry = false) => {
    const queryToSend = customQuery || input;
    if (!queryToSend.trim() || loading) return;
    if (!isRetry) {
      setMessages(prev => [...prev, { id: Date.now(), type: 'user', text: queryToSend }]);
      setInput('');
    }
    if (appMode === 'mechanical') setActiveView('chat');
    setLoading(true);
    try {
      const dbName = appMode === 'mechanical' ? 'mech_ai_demo' : selectedDbName;
      const dbType = appMode === 'mechanical' ? 'mysql' : selectedDbType;
      const res = await axios.post(`${API_BASE}/chat`, {
        query: queryToSend, db_type: dbType, database: dbName,
        thread_id: threadId, role: userRole, mode: appMode
      });
      const d = res.data;
      const aiMsg = {
        id: Date.now() + 1, type: 'ai',
        text: typeof d.result === 'string' ? d.result : (Array.isArray(d.result) && typeof d.result[0] === 'string' ? d.result.join(', ') : `Analysis complete for **${dbName}**.`),
        sql: d.sql, explanation: d.explanation, query_plan: d.query_plan,
        confidence_score: d.confidence_score, confidence_level: d.confidence_level,
        chart: d.chart, data: Array.isArray(d.result) ? d.result : null,
        intent: d.intent, error: d.error, context_used: d.context_used, latency: d.latency,
        mechanical_analysis: d.mechanical_analysis, prediction: d.prediction,
        recommendation: d.recommendation, insights: d.insights
      };
      setMessages(prev => [...prev, aiMsg]);
      if (d.sql) setQueryHistory(prev => [{ query: queryToSend, sql: d.sql, date: new Date().toISOString() }, ...prev].slice(0, 50));
    } catch (err) {
      setMessages(prev => [...prev, { id: Date.now() + 1, type: 'ai', text: 'Backend communication error. Please check if the server is running.' }]);
    } finally { setLoading(false); }
  };

  const copyToClipboard = (text) => navigator.clipboard.writeText(text);


  const renderTable = (data) => {
    if (!data || !Array.isArray(data) || data.length === 0) return null;
    const columns = Object.keys(data[0]);
    return (
      <div className="data-table-container" style={{ marginTop: '16px', maxHeight: '300px', overflow: 'auto' }}>
        <table className="data-table">
          <thead><tr>{columns.map(col => <th key={col}>{col}</th>)}</tr></thead>
          <tbody>{data.slice(0, 50).map((row, i) => (<tr key={i}>{columns.map(col => <td key={col}>{String(row[col])}</td>)}</tr>))}</tbody>
        </table>
      </div>
    );
  };

  const renderMessageContent = (msg) => {
    if (msg.text.includes(': ') && (msg.text.toLowerCase().includes('databases') || msg.text.toLowerCase().includes('tables'))) {
      const [prefix, listStr] = msg.text.split(': ');
      const items = listStr.split(',').map(s => s.trim()).filter(s => s);
      return (<div className="markdown-content"><p><strong>{prefix}:</strong></p><div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap' }}>{items.map(item => (<span key={item} className="data-badge">{item}</span>))}</div></div>);
    }
    return (<div className="markdown-content" style={{ fontSize: '1rem', lineHeight: '1.6' }}><ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown></div>);
  };

  const runBenchmark = async () => {
    setLoading(true); setActiveView('evaluation');
    try { const res = await axios.get(`${API_BASE}/benchmark`); setEvalStats(res.data); } catch (err) { console.error('Benchmark failed', err); } finally { setLoading(false); }
  };

  const renderEvaluationView = () => {
    if (!evalStats) return (
      <div style={{ padding: '100px 40px', textAlign: 'center' }}>
        <Activity size={64} style={{ margin: '0 auto 24px', opacity: 0.08, color: 'var(--accent)' }} />
        <h3 style={{ fontSize: '1.5rem', fontWeight: 700 }}>System Performance Audit</h3>
        <p style={{ marginTop: '12px', fontSize: '0.95rem', maxWidth: '500px', margin: '12px auto', color: 'var(--text-secondary)' }}>Analyze the accuracy and latency of the multi-agent SQL engine.</p>
        <button onClick={runBenchmark} disabled={loading} style={{ marginTop: '32px', background: 'linear-gradient(135deg, #2563EB, #4F46E5)', color: 'white', border: 'none', padding: '12px 32px', borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer', boxShadow: '0 4px 16px rgba(37, 99, 235, 0.3)', fontSize: '0.85rem' }}>{loading ? 'Executing...' : 'Launch Benchmark'}</button>
      </div>
    );
    return (
      <div style={{ animation: 'slideInUp 0.4s ease-out' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '32px' }}>
          {[{ label: 'Accuracy', value: evalStats.accuracy, icon: <CheckCircle2 size={18} color="var(--success)" /> },
            { label: 'Avg. Latency', value: evalStats.avg_latency, icon: <Clock size={18} color="var(--accent)" /> },
            { label: 'Confidence', value: evalStats.avg_confidence, icon: <Zap size={18} color="var(--warning)" /> },
            { label: 'Coverage', value: `${evalStats.total_queries} Queries`, icon: <Database size={18} color="var(--violet)" /> }
          ].map((stat, i) => (
            <div key={i} className="agent-response-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{stat.label}</span>{stat.icon}
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.02em' }}>{stat.value}</div>
            </div>
          ))}
        </div>
        <div className="agent-response-card" style={{ padding: '0' }}>
          <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700 }}>Audit Logs</h3>
            <button onClick={runBenchmark} style={{ background: 'none', border: 'none', color: 'var(--accent)', fontWeight: 600, fontSize: '0.8rem', cursor: 'pointer' }}>Re-run</button>
          </div>
          <div className="data-table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table className="data-table">
              <thead><tr><th>Engine</th><th>Database</th><th>Query</th><th>Status</th><th>Latency</th></tr></thead>
              <tbody>{evalStats.details.map((row, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 700, fontSize: '0.75rem' }}>{row.db_type.toUpperCase()}</td>
                  <td><span className="data-badge" style={{ margin: 0 }}>{row.db}</span></td>
                  <td style={{ fontSize: '0.85rem' }}>{row.query}</td>
                  <td><div style={{ color: row.success ? '#10b981' : '#ef4444', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>{row.success ? <CheckCircle2 size={12} /> : <Lock size={12} />}{row.success ? 'PASSED' : 'FAILED'}</div></td>
                  <td style={{ color: '#64748b', fontSize: '0.85rem' }}>{row.latency_ms}ms</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const isMech = appMode === 'mechanical';

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo-section">
          <div className="logo-icon" style={isMech ? { background: 'linear-gradient(135deg, #EA580C, #DC2626)' } : {}}>
            {isMech ? <Settings size={20} color="white" /> : <Brain size={20} color="white" />}
          </div>
          <div className="logo-text">
            <h1>Sentinel</h1>
            <p>{isMech ? 'Industrial Intelligence' : 'AI Platform'}</p>
          </div>
        </div>

        <div className="sidebar-label">System Mode</div>
        <div style={{ padding: '0 12px' }}>
          <div className="mode-toggle">
            <div className={`mode-slider ${appMode}`}></div>
            <button className={appMode === 'data' ? 'active' : ''} onClick={() => setAppMode('data')}>📊 Data</button>
            <button className={appMode === 'mechanical' ? 'active' : ''} onClick={() => setAppMode('mechanical')}>⚙️ Mechanical</button>
          </div>
        </div>

        {!isMech && (
          <>
            <div className="sidebar-label">Database Configuration</div>
            <div style={{ padding: '0 12px' }}>
              <div className="segmented-control">
                <div className="segmented-slider" style={{ transform: selectedDbType === 'mysql' ? 'translateX(100%)' : 'translateX(0)' }}></div>
                <button className={selectedDbType === 'postgres' ? 'active' : ''} onClick={() => setSelectedDbType('postgres')}>Postgres</button>
                <button className={selectedDbType === 'mysql' ? 'active' : ''} onClick={() => setSelectedDbType('mysql')}>MySQL</button>
              </div>
              <div className="db-selector" onClick={() => setShowDbDropdown(!showDbDropdown)} style={{ position: 'relative', background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border-sidebar)', borderRadius: 'var(--radius-md)', padding: '10px 14px', marginTop: '12px' }}>
                <Database size={14} color={selectedDbType === 'mysql' ? '#F59E0B' : '#93BBFD'} />
                <span style={{ fontSize: '0.82rem', flex: 1, fontWeight: 500, marginLeft: '8px', color: 'var(--text-inverse)' }}>{selectedDbName}</span>
                <ChevronDown size={12} color="var(--text-muted)" />
                {showDbDropdown && (
                  <div className="db-dropdown" style={{ background: 'var(--bg-surface-1)', border: '1px solid var(--border)', top: 'calc(100% + 6px)', boxShadow: 'var(--shadow-lg)', borderRadius: 'var(--radius-md)' }}>
                    {databases.map(db => (<div key={db} className="db-dropdown-item" style={{ color: 'var(--text-primary)', padding: '10px 16px' }} onClick={(e) => { e.stopPropagation(); setSelectedDbName(db); setShowDbDropdown(false); }}>{db}</div>))}
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        <div className="sidebar-label">Navigation</div>
        {isMech && (
          <div className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveView('dashboard')}>
            <Settings size={16} /> Fleet Dashboard
          </div>
        )}
        <div className={`nav-item ${activeView === 'chat' ? 'active' : ''}`} onClick={() => setActiveView('chat')}>
          <TableIcon size={16} /> {isMech ? 'Copilot Chat' : 'Analytics Chat'}
        </div>
        {!isMech && (
          <>
            <div className={`nav-item ${activeView === 'history' ? 'active' : ''}`} onClick={() => setActiveView('history')}><History size={16} /> Query Log</div>
            <div className={`nav-item ${activeView === 'evaluation' ? 'active' : ''}`} onClick={() => setActiveView('evaluation')}><Activity size={16} /> Engine Audit</div>
          </>
        )}

        <div className="sidebar-label" style={{ marginTop: 'auto' }}>Security</div>
        <div className="nav-item" style={{ background: 'rgba(34, 197, 94, 0.06)', border: '1px solid rgba(34, 197, 94, 0.1)' }}>
          <Shield size={14} color="var(--success)" />
          <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.03em', color: 'var(--success)' }}>{userRole.toUpperCase()} ACCESS</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="top-bar">
          <div className="breadcrumbs">
            <span>{isMech ? 'Mechanical Intelligence' : 'Analytics'}</span>
            <ChevronRight size={12} />
            <span className="breadcrumb-active">
              {activeView === 'dashboard' ? 'Fleet Dashboard' : activeView === 'chat' ? (isMech ? 'Copilot Chat' : selectedDbName) : 'Engine Audit'}
            </span>
          </div>
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            <div className="status-badge" style={isMech ? { background: 'rgba(234,88,12,0.08)', color: '#EA580C', borderColor: 'rgba(234,88,12,0.15)' } : {}}>
              <div className="status-dot" style={isMech ? { background: '#EA580C', boxShadow: '0 0 6px rgba(234,88,12,0.4)' } : {}}></div>
              {isMech ? 'Mechanical Mode' : 'System Online'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', borderLeft: '1px solid var(--border)', paddingLeft: '20px' }}>
              <Search size={16} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
              <Bell size={16} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
              <div style={{ width: '30px', height: '30px', background: 'var(--bg-surface-1)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border)' }}>
                <User size={14} color="var(--text-secondary)" />
              </div>
            </div>
          </div>
        </header>

        <div className="chat-view">
          {activeView === 'dashboard' && isMech ? (
            <MechanicalDashboard onQuerySelect={(q) => handleSend(q)} />
          ) : activeView === 'chat' ? (
            <>
              {messages.map(msg => (
                <div key={msg.id} className={`message ${msg.type}`}>
                  {msg.type === 'ai' ? (
                    <div className="ai-container" style={{ width: '100%' }}>
                      <div className="agent-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: isMech ? 'linear-gradient(135deg, #EA580C, #DC2626)' : 'var(--accent-gradient)', boxShadow: isMech ? '0 0 8px rgba(234,88,12,0.4)' : '0 0 8px rgba(37, 99, 235, 0.4)' }}></div>
                          <span style={{ fontWeight: 700, fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            {isMech ? 'Sentinel Industrial' : 'Sentinel AI'}
                          </span>
                          {msg.latency && <span className="badge-pill" style={{ background: 'var(--bg-surface-2)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>{msg.latency}</span>}
                        </div>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          {msg.confidence_score !== undefined && <div className="badge-pill">{msg.confidence_score}% Confidence</div>}
                        </div>
                      </div>
                      <div className="agent-response-card">
                        {renderMessageContent(msg)}
                        {msg.error && (
                          <div style={{ marginTop: '16px', padding: '14px 16px', background: 'var(--error-soft)', border: '1px solid rgba(239, 68, 68, 0.12)', borderRadius: 'var(--radius-md)', color: 'var(--error)', fontSize: '0.85rem', display: 'flex', gap: '10px', alignItems: 'center' }}>
                            <Lock size={14} style={{ flexShrink: 0 }} /><div><strong>Access Restriction:</strong> {msg.error}</div>
                          </div>
                        )}
                        {msg.sql && (
                          <CodeBlock 
                            sql={msg.sql} 
                            dbType={selectedDbType} 
                            onCopy={copyToClipboard} 
                            onRerun={(sql) => handleSend(sql, true)} 
                          />
                        )}

                        {/* Mechanical Intelligence Cards */}
                        {isMech && msg.mechanical_analysis && <MechanicalAnalysisCard analysis={msg.mechanical_analysis} />}
                        {isMech && msg.prediction && <PredictionCard prediction={msg.prediction} />}
                        {isMech && msg.recommendation && <RecommendationCard recommendation={msg.recommendation} />}
                        {isMech && msg.insights && <InsightsBanner insights={msg.insights} />}

                        {(msg.data || msg.explanation || msg.query_plan) && (
                          <div style={{ marginTop: '20px', borderTop: '1px solid var(--border)', paddingTop: '20px' }}>
                            <div style={{ display: 'flex', gap: '16px', marginBottom: '14px' }}>
                              <button style={{ padding: '0 0 6px', borderRadius: 0, background: 'none', border: 'none', borderBottom: '2px solid var(--accent)', color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.75rem', cursor: 'pointer', fontFamily: 'inherit', textTransform: 'uppercase', letterSpacing: '0.03em' }}>Dataset</button>
                              {msg.explanation && <button style={{ padding: '0 0 6px', borderRadius: 0, background: 'none', border: 'none', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', cursor: 'pointer', fontFamily: 'inherit', textTransform: 'uppercase', letterSpacing: '0.03em' }}>Analysis</button>}
                            </div>
                            {msg.data && renderTable(msg.data)}
                            {msg.explanation && (
                              <div className="markdown-content" style={{ marginTop: '14px', color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: '1.6' }}>
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.explanation}</ReactMarkdown>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="bubble">{msg.text}</div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="message ai">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-secondary)', fontSize: '0.82rem', background: 'var(--bg-surface-1)', padding: '10px 18px', borderRadius: 'var(--radius-md)', width: 'fit-content', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)' }}>
                    <div className="loading-dots"><div className="dot"></div><div className="dot"></div><div className="dot"></div></div>
                    <span style={{ fontWeight: 600 }}>{isMech ? 'Sentinel analyzing industrial data...' : 'Sentinel executing multi-agent workflow...'}</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </>
          ) : (
            renderEvaluationView()
          )}
        </div>

        {(activeView === 'chat' || (activeView === 'dashboard' && isMech)) && (
          <div className="input-area">
            <div className="input-container" style={isMech ? { borderColor: 'rgba(234,88,12,0.1)' } : {}}>
              <textarea
                rows="1"
                placeholder={isMech ? 'Ask about machine health, failures, or simulate scenarios...' : `Search within ${selectedDbName}...`}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              />
              <button className="send-btn" onClick={() => handleSend()} disabled={loading || !input.trim()}
                style={isMech ? { background: 'linear-gradient(135deg, #EA580C, #DC2626)', boxShadow: '0 2px 8px rgba(234,88,12,0.25)' } : {}}>
                <Send size={16} />
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
