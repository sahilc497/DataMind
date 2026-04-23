import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Database, 
  Send, 
  Table as TableIcon, 
  ChevronRight, 
  ChevronDown, 
  Search, 
  RefreshCw, 
  Terminal,
  Columns,
  Cpu,
  History,
  Settings,
  Plus,
  Copy,
  Bell,
  User,
  Paperclip,
  CheckCircle2,
  Clock,
  Shield,
  Zap,
  BarChart3,
  Info,
  Brain,
  Activity,
  Lock,
  Play,
  Edit2
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [databases, setDatabases] = useState([]);
  const [selectedDbType, setSelectedDbType] = useState('postgres');
  const [selectedDbName, setSelectedDbName] = useState('postgres');
  const [activeView, setActiveView] = useState('chat');
  const [showDbDropdown, setShowDbDropdown] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, type: 'ai', text: '# Enterprise SQL Assistant\nWelcome. I can help you analyze data across PostgreSQL and MySQL.\n\n**Select your database source on the left to begin.**' }
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
      console.error('Failed to fetch databases', err);
      setDatabases([]);
      setSelectedDbName('Offline / No Connection');
    }
  };

  useEffect(() => {
    fetchDatabases(selectedDbType);
  }, [selectedDbType]);

  useEffect(() => {
    if (databases.length > 0 && !databases.includes(selectedDbName)) {
      setSelectedDbName(databases[0]);
    }
  }, [databases]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (customQuery = null, isRetry = false) => {
    const queryToSend = customQuery || input;
    if (!queryToSend.trim() || loading) return;

    if (!isRetry) {
      const userMsg = { id: Date.now(), type: 'user', text: queryToSend };
      setMessages(prev => [...prev, userMsg]);
      setInput('');
    }
    
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/chat`, { 
        query: queryToSend,
        db_type: selectedDbType,
        database: selectedDbName,
        thread_id: threadId,
        role: userRole
      });
      
      const aiMsg = { 
        id: Date.now() + 1, 
        type: 'ai', 
        text: typeof res.data.result === 'string' ? res.data.result : (Array.isArray(res.data.result) && typeof res.data.result[0] === 'string' ? res.data.result.join(', ') : `Analysis complete for **${selectedDbName}**.`),
        sql: res.data.sql,
        explanation: res.data.explanation,
        query_plan: res.data.query_plan,
        confidence_score: res.data.confidence_score,
        confidence_level: res.data.confidence_level,
        chart: res.data.chart,
        data: Array.isArray(res.data.result) ? res.data.result : null,
        intent: res.data.intent,
        error: res.data.error,
        context_used: res.data.context_used,
        latency: res.data.latency
      };
      
      setMessages(prev => [...prev, aiMsg]);
      
      if (res.data.sql) {
        const newHistory = [{ query: queryToSend, sql: res.data.sql, date: new Date().toISOString() }, ...queryHistory].slice(0, 50);
        setQueryHistory(newHistory);
      }
    } catch (err) {
      setMessages(prev => [...prev, { id: Date.now() + 1, type: 'ai', text: 'Backend communication error. Please check if the server is running.' }]);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const renderCodeBlock = (sql, msgId) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedSql, setEditedSql] = useState(sql);

    return (
      <div className="code-container" style={{ position: 'relative' }}>
        <div className="code-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={12} />
            <span>{selectedDbType.toUpperCase()} QUERY</span>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button onClick={() => setIsEditing(!isEditing)} style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}>
              <Edit2 size={12} /> {isEditing ? 'Cancel' : 'Edit'}
            </button>
            <button onClick={() => copyToClipboard(sql)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}>
              <Copy size={12} /> Copy
            </button>
          </div>
        </div>
        {isEditing ? (
          <div style={{ padding: '12px', background: '#1e1e1e' }}>
            <textarea 
              value={editedSql}
              onChange={(e) => setEditedSql(e.target.value)}
              style={{ width: '100%', background: '#2d2d2d', color: '#d4d4d4', border: '1px solid #444', borderRadius: '4px', padding: '8px', fontFamily: 'monospace', fontSize: '0.85rem' }}
              rows={4}
            />
            <button 
              onClick={() => {
                handleSend(editedSql, true);
                setIsEditing(false);
              }}
              style={{ marginTop: '8px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', padding: '4px 12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}
            >
              <Play size={12} /> Re-run Query
            </button>
          </div>
        ) : (
          <div className="code-content" style={{ fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
            {sql}
          </div>
        )}
      </div>
    );
  };

  const renderTable = (data) => {
    if (!data || !Array.isArray(data) || data.length === 0) return null;
    const columns = Object.keys(data[0]);
    return (
      <div className="data-table-container" style={{ marginTop: '16px', maxHeight: '300px', overflow: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>{columns.map(col => <th key={col}>{col}</th>)}</tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((row, i) => (
              <tr key={i}>{columns.map(col => <td key={col}>{String(row[col])}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const runBenchmark = async () => {
    setLoading(true);
    setActiveView('evaluation');
    try {
      const res = await axios.get(`${API_BASE}/benchmark`);
      setEvalStats(res.data);
    } catch (err) {
      console.error('Benchmark failed', err);
    } finally {
      setLoading(false);
    }
  };

  const renderEvaluationView = () => {
    if (!evalStats) {
      return (
        <div style={{ padding: '80px 40px', textAlign: 'center', color: '#64748b' }}>
            <Activity size={80} style={{ margin: '0 auto 32px', opacity: 0.1, color: '#3b82f6' }} />
            <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a' }}>System Performance Audit</h3>
            <p style={{ marginTop: '16px', fontSize: '1.1rem', maxWidth: '600px', margin: '16px auto' }}>
                Analyze the accuracy and latency of the multi-agent SQL engine across all connected databases.
            </p>
            <button 
                onClick={runBenchmark} 
                disabled={loading}
                style={{ marginTop: '40px', background: '#3b82f6', color: 'white', border: 'none', padding: '16px 40px', borderRadius: '16px', fontWeight: 700, cursor: 'pointer', boxShadow: '0 10px 20px rgba(59, 130, 246, 0.2)' }}
            >
                {loading ? 'Executing Audit...' : 'Launch Production Benchmark'}
            </button>
        </div>
      );
    }

    return (
      <div style={{ animation: 'slideInUp 0.4s ease-out' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', marginBottom: '40px' }}>
            {[
                { label: 'System Accuracy', value: evalStats.accuracy, icon: <CheckCircle2 size={20} color="#10b981" /> },
                { label: 'Avg. Latency', value: evalStats.avg_latency, icon: <Clock size={20} color="#3b82f6" /> },
                { label: 'Confidence Floor', value: evalStats.avg_confidence, icon: <Zap size={20} color="#f59e0b" /> },
                { label: 'Test Coverage', value: `${evalStats.total_queries} Queries`, icon: <Database size={20} color="#8b5cf6" /> }
            ].map((stat, i) => (
                <div key={i} className="agent-response-card" style={{ padding: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase' }}>{stat.label}</span>
                        {stat.icon}
                    </div>
                    <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a' }}>{stat.value}</div>
                </div>
            ))}
        </div>

        <div className="agent-response-card" style={{ padding: '0' }}>
            <div style={{ padding: '24px 32px', borderBottom: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>Audit Logs</h3>
                <button onClick={runBenchmark} style={{ background: 'none', border: 'none', color: '#3b82f6', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}>Re-run Audit</button>
            </div>
            <div className="data-table-container" style={{ border: 'none', borderRadius: 0 }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Engine</th>
                            <th>Database</th>
                            <th>Natural Language Query</th>
                            <th>Status</th>
                            <th>Latency</th>
                        </tr>
                    </thead>
                    <tbody>
                        {evalStats.details.map((row, i) => (
                            <tr key={i}>
                                <td style={{ fontWeight: 700, fontSize: '0.75rem' }}>{row.db_type.toUpperCase()}</td>
                                <td><span className="data-badge" style={{ margin: 0 }}>{row.db}</span></td>
                                <td style={{ fontSize: '0.85rem' }}>{row.query}</td>
                                <td>
                                    <div style={{ color: row.success ? '#10b981' : '#ef4444', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        {row.success ? <CheckCircle2 size={12} /> : <Lock size={12} />}
                                        {row.success ? 'PASSED' : 'FAILED'}
                                    </div>
                                </td>
                                <td style={{ color: '#64748b', fontSize: '0.85rem' }}>{row.latency_ms}ms</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo-section">
          <div className="logo-icon"><Brain size={20} color="white" /></div>
          <div className="logo-text">
            <h1>DataMind</h1>
            <p>Intelligence Engine</p>
          </div>
        </div>

        <div className="sidebar-label">Database Configuration</div>
        <div style={{ padding: '0 8px' }}>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                <button 
                    onClick={() => setSelectedDbType('postgres')}
                    className={`nav-item ${selectedDbType === 'postgres' ? 'active' : ''}`}
                    style={{ flex: 1, justifyContent: 'center', fontSize: '0.8rem', padding: '10px' }}
                >Postgres</button>
                <button 
                    onClick={() => setSelectedDbType('mysql')}
                    className={`nav-item ${selectedDbType === 'mysql' ? 'active' : ''}`}
                    style={{ flex: 1, justifyContent: 'center', fontSize: '0.8rem', padding: '10px' }}
                >MySQL</button>
            </div>
            
            <div className="db-selector" onClick={() => setShowDbDropdown(!showDbDropdown)} style={{ position: 'relative' }}>
                <Database size={16} color={selectedDbType === 'mysql' ? '#f59e0b' : '#3b82f6'} />
                <span style={{ fontSize: '0.9rem', flex: 1, fontWeight: 500 }}>{selectedDbName}</span>
                <ChevronDown size={14} />
                
                {showDbDropdown && (
                    <div className="db-dropdown">
                    {databases.map(db => (
                        <div 
                        key={db} 
                        className={`db-dropdown-item ${selectedDbName === db ? 'active' : ''}`}
                        onClick={(e) => { e.stopPropagation(); setSelectedDbName(db); setShowDbDropdown(false); }}
                        >
                        {db}
                        </div>
                    ))}
                    </div>
                )}
            </div>
        </div>

        <div className="sidebar-label">Navigation</div>
        <div className={`nav-item ${activeView === 'chat' ? 'active' : ''}`} onClick={() => setActiveView('chat')}>
          <TableIcon size={18} /> Analytics Chat
        </div>
        <div className={`nav-item ${activeView === 'history' ? 'active' : ''}`} onClick={() => setActiveView('history')}>
          <History size={18} /> Query Log
        </div>
        <div className={`nav-item ${activeView === 'evaluation' ? 'active' : ''}`} onClick={() => setActiveView('evaluation')}>
          <Activity size={18} /> Engine Audit
        </div>

        <div className="sidebar-label" style={{ marginTop: 'auto' }}>Security</div>
        <div className="nav-item" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <Shield size={16} color="#10b981" />
            <span style={{ fontSize: '0.85rem' }}>{userRole.toUpperCase()} ACCESS</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="top-bar">
          <div className="breadcrumbs">
            <span style={{ opacity: 0.5 }}>Analytics</span>
            <ChevronRight size={14} />
            <span className="breadcrumb-active" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={14} color="#3b82f6" />
                {activeView === 'chat' ? selectedDbName : 'System Audit'}
            </span>
          </div>
          <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
            <div className="status-badge">
                <div className="status-dot"></div>
                SYSTEM ONLINE
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', borderLeft: '1px solid #e2e8f0', paddingLeft: '24px' }}>
                <Search size={20} color="#94a3b8" style={{ cursor: 'pointer' }} />
                <Bell size={20} color="#94a3b8" style={{ cursor: 'pointer' }} />
                <div style={{ width: '36px', height: '36px', background: '#f1f5f9', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #e2e8f0' }}>
                    <User size={20} color="#64748b" />
                </div>
            </div>
          </div>
        </header>

        <div className="chat-view">
          {activeView === 'chat' ? (
            <>
              {messages.map(msg => (
                <div key={msg.id} className={`message ${msg.type}`}>
                  {msg.type === 'ai' ? (
                    <div className="ai-container" style={{ width: '100%' }}>
                      <div className="agent-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div style={{ width: '32px', height: '32px', background: 'white', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'var(--shadow-md)', border: '1px solid #f1f5f9' }}>
                            <Cpu size={18} color="#3b82f6" />
                          </div>
                          <span style={{ fontWeight: 800, fontSize: '0.85rem', letterSpacing: '0.02em', color: '#1e293b' }}>INTELLIGENCE LAYER</span>
                          {msg.latency && <span style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 600 }}>• {msg.latency}</span>}
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                             {msg.confidence_score !== undefined && (
                                <div style={{ background: msg.confidence_level === 'High' ? '#f0fdf4' : '#fffbeb', color: msg.confidence_level === 'High' ? '#16a34a' : '#d97706', padding: '6px 14px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 800, border: '1px solid currentColor' }}>
                                    {msg.confidence_score}% CONFIDENCE
                                </div>
                             )}
                        </div>
                      </div>
                      
                      <div className="agent-response-card">
                        {renderMessageContent(msg)}
                        
                        {msg.error && (
                            <div style={{ marginTop: '24px', padding: '20px', background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '16px', color: '#b91c1c', fontSize: '0.95rem', display: 'flex', gap: '16px', alignItems: 'center' }}>
                                <Lock size={20} style={{ flexShrink: 0 }} />
                                <div><strong style={{ display: 'block', marginBottom: '2px' }}>Security Protocol Alert</strong> {msg.error}</div>
                            </div>
                        )}

                        {msg.sql && renderCodeBlock(msg.sql, msg.id)}

                        {(msg.data || msg.explanation || msg.query_plan) && (
                            <div style={{ marginTop: '32px', borderTop: '1px solid #f1f5f9', paddingTop: '32px' }}>
                                <div style={{ display: 'flex', gap: '32px', marginBottom: '20px' }}>
                                    <button className="nav-item active" style={{ padding: '0 0 12px', borderRadius: 0, background: 'none', border: 'none', borderBottom: '2px solid #3b82f6', width: 'auto', fontSize: '0.85rem' }}>RESULT DATA</button>
                                    {msg.explanation && <button className="nav-item" style={{ padding: '0 0 12px', borderRadius: 0, background: 'none', border: 'none', opacity: 0.4, width: 'auto', fontSize: '0.85rem' }}>ANALYSIS</button>}
                                </div>
                                
                                {msg.data && renderTable(msg.data)}
                                
                                {msg.explanation && (
                                    <div className="markdown-content" style={{ marginTop: '20px', background: '#f8fafc', padding: '24px', borderRadius: '16px', border: '1px solid #e2e8f0', color: '#334155' }}>
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
                   <div style={{ display: 'flex', alignItems: 'center', gap: '20px', color: '#64748b', fontSize: '0.95rem', background: 'white', padding: '20px 32px', borderRadius: '24px', width: 'fit-content', boxShadow: 'var(--shadow-xl)', border: '1px solid #f1f5f9' }}>
                        <div className="loading-dots"><div className="dot"></div><div className="dot"></div><div className="dot"></div></div>
                        <span style={{ fontWeight: 600 }}>Executing multi-agent chain...</span>
                   </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </>
          ) : (
            renderEvaluationView()
          )}
        </div>

        {activeView === 'chat' && (
          <div className="input-area">
            <div className="input-container">
                <textarea 
                    rows="1" 
                    placeholder={`Query ${selectedDbName}...`}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                />
                <button 
                    className="send-btn" 
                    onClick={() => handleSend()} 
                    disabled={loading || !input.trim()}
                >
                    <Send size={18} />
                </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
