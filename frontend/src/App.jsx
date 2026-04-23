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
      setDatabases(res.data.databases);
    } catch (err) {
      console.error('Failed to fetch databases', err);
    }
  };

  useEffect(() => {
    fetchDatabases(selectedDbType);
  }, [selectedDbType]);

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
        text: typeof res.data.result === 'string' && !res.data.result.startsWith('[') ? res.data.result : `Analysis complete for **${selectedDbName}**.`,
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

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo-section">
          <div className="logo-icon" style={{ background: '#000', color: '#fff' }}><Brain size={18} /></div>
          <div className="logo-text">
            <h1 style={{ letterSpacing: '-0.5px' }}>DataMind</h1>
            <p style={{ textTransform: 'uppercase', fontSize: '0.6rem', fontWeight: 700, color: '#666' }}>Engineered Analytics</p>
          </div>
        </div>

        <div className="sidebar-label">Database Configuration</div>
        <div style={{ padding: '0 12px' }}>
            <div style={{ display: 'flex', gap: '4px', marginBottom: '8px' }}>
                <button 
                    onClick={() => setSelectedDbType('postgres')}
                    className={`nav-item ${selectedDbType === 'postgres' ? 'active' : ''}`}
                    style={{ flex: 1, justifyContent: 'center', fontSize: '0.75rem' }}
                >Postgres</button>
                <button 
                    onClick={() => setSelectedDbType('mysql')}
                    className={`nav-item ${selectedDbType === 'mysql' ? 'active' : ''}`}
                    style={{ flex: 1, justifyContent: 'center', fontSize: '0.75rem' }}
                >MySQL</button>
            </div>
            
            <div className="db-selector" onClick={() => setShowDbDropdown(!showDbDropdown)}>
                <Database size={14} />
                <span style={{ fontSize: '0.85rem', flex: 1 }}>{selectedDbName}</span>
                <ChevronDown size={12} />
            </div>
            
            {showDbDropdown && (
                <div className="db-dropdown" style={{ left: '12px', right: '12px' }}>
                {databases.map(db => (
                    <div 
                    key={db} 
                    className={`db-dropdown-item ${selectedDbName === db ? 'active' : ''}`}
                    onClick={() => { setSelectedDbName(db); setShowDbDropdown(false); }}
                    >
                    {db}
                    </div>
                ))}
                </div>
            )}
        </div>

        <div className="sidebar-label" style={{ marginTop: '24px' }}>Security & Access</div>
        <div style={{ padding: '0 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f8f9fa', padding: '8px', borderRadius: '8px', border: '1px solid #eee' }}>
                <Shield size={14} color={userRole === 'admin' ? '#ef4444' : '#10b981'} />
                <select 
                    value={userRole}
                    onChange={(e) => setUserRole(e.target.value)}
                    style={{ background: 'none', border: 'none', outline: 'none', fontSize: '0.85rem', fontWeight: 600, flex: 1, cursor: 'pointer' }}
                >
                    <option value="admin">Administrator (Full Access)</option>
                    <option value="user">Standard User (Read-Only)</option>
                </select>
            </div>
        </div>

        <div className="sidebar-label" style={{ marginTop: '24px' }}>Navigation</div>
        <div className={`nav-item ${activeView === 'chat' ? 'active' : ''}`} onClick={() => setActiveView('chat')}>
          <TableIcon size={18} /> Analytics Chat
        </div>
        <div className={`nav-item ${activeView === 'history' ? 'active' : ''}`} onClick={() => setActiveView('history')}>
          <History size={18} /> Query Log
        </div>
        <div className={`nav-item ${activeView === 'evaluation' ? 'active' : ''}`} onClick={() => setActiveView('evaluation')}>
          <Activity size={18} /> Benchmarks
        </div>

        <button className="new-analysis-btn" onClick={() => setMessages([{ id: Date.now(), type: 'ai', text: 'How can I help you with your data today?' }])} style={{ marginTop: 'auto', marginBottom: '20px' }}>
          <Plus size={18} /> New Workspace
        </button>
      </aside>

      <main className="main-content">
        <header className="top-bar">
          <div className="breadcrumbs">
            <span style={{ color: '#666' }}>Engine</span>
            <ChevronRight size={14} color="#ccc" />
            <span className="breadcrumb-active" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></div>
                Production-Ready
            </span>
          </div>
          <div className="top-bar-right">
            <div className="search-mini">
              <Search size={14} color="#666" />
              <input type="text" placeholder="Search tables or queries..." />
            </div>
            <div style={{ position: 'relative' }}>
                <Bell size={18} color="#666" />
                <div style={{ position: 'absolute', top: '-2px', right: '-2px', width: '8px', height: '8px', background: '#ef4444', borderRadius: '50%', border: '2px solid #fff' }}></div>
            </div>
            <User size={18} color="#666" />
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
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Cpu size={14} color="#3b82f6" />
                          <span style={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase' }}>Intelligence Layer</span>
                          {msg.latency && <span style={{ color: '#999', fontSize: '0.7rem' }}>• {msg.latency}</span>}
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                             {msg.context_used && <div title="Conversation Context Used" style={{ background: '#eff6ff', color: '#3b82f6', padding: '2px 6px', borderRadius: '4px', fontSize: '0.65rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}><Brain size={10}/> CONTEXT</div>}
                             {msg.confidence_score !== undefined && (
                                <div style={{ background: msg.confidence_level === 'High' ? '#ecfdf5' : '#fff7ed', color: msg.confidence_level === 'High' ? '#10b981' : '#f59e0b', padding: '2px 8px', borderRadius: '4px', fontSize: '0.65rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <Zap size={10} /> {msg.confidence_score}% CONFIDENCE
                                </div>
                             )}
                        </div>
                      </div>
                      
                      <div className="agent-response-card" style={{ border: msg.error ? '1px solid #fecaca' : '1px solid #eee' }}>
                        <div className="markdown-content" style={{ fontSize: '0.95rem', lineHeight: '1.6' }}>
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                        </div>
                        
                        {msg.error && (
                            <div style={{ marginTop: '12px', padding: '12px', background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '8px', color: '#b91c1c', fontSize: '0.85rem', display: 'flex', gap: '8px' }}>
                                <Lock size={16} style={{ flexShrink: 0 }} />
                                <div><strong>System Alert:</strong> {msg.error}</div>
                            </div>
                        )}

                        {msg.sql && renderCodeBlock(msg.sql, msg.id)}

                        <div style={{ marginTop: '16px' }}>
                            <div style={{ display: 'flex', gap: '16px', borderBottom: '1px solid #eee', marginBottom: '12px' }}>
                                <button className="nav-item active" style={{ padding: '8px 0', fontSize: '0.8rem', background: 'none' }}>Data Output</button>
                                {msg.query_plan && <button className="nav-item" style={{ padding: '8px 0', fontSize: '0.8rem', background: 'none' }}>Execution Plan</button>}
                                {msg.explanation && <button className="nav-item" style={{ padding: '8px 0', fontSize: '0.8rem', background: 'none' }}>Insights</button>}
                            </div>
                            
                            {msg.data && renderTable(msg.data)}
                            
                            {msg.explanation && (
                                <div className="markdown-content" style={{ fontSize: '0.85rem', color: '#444', background: '#fcfcfc', padding: '12px', borderRadius: '8px' }}>
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.explanation}</ReactMarkdown>
                                </div>
                            )}

                            {msg.query_plan && (
                                <details style={{ marginTop: '12px' }}>
                                    <summary style={{ fontSize: '0.8rem', color: '#666', cursor: 'pointer' }}>View Raw Execution Plan</summary>
                                    <pre style={{ fontSize: '0.7rem', background: '#f4f4f4', padding: '10px', overflow: 'auto', borderRadius: '4px' }}>{msg.query_plan}</pre>
                                </details>
                            )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bubble" style={{ alignSelf: 'flex-end', background: '#000', color: '#fff', borderRadius: '18px 18px 2px 18px', padding: '12px 20px' }}>{msg.text}</div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="message ai">
                   <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#666', fontSize: '0.8rem' }}>
                        <div className="loading-dots"><div className="dot"></div><div className="dot"></div><div className="dot"></div></div>
                        Processing request through multi-agent orchestration...
                   </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </>
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                <Activity size={48} style={{ margin: '0 auto 20px', opacity: 0.2 }} />
                <h3>Module Under Maintenance</h3>
                <p>History and Benchmarking are being refactored for the multi-database architecture.</p>
                <button onClick={() => setActiveView('chat')} style={{ marginTop: '20px', color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Return to Analytics</button>
            </div>
          )}
        </div>

        {activeView === 'chat' && (
          <div className="input-area" style={{ borderTop: '1px solid #eee', background: '#fff', padding: '20px' }}>
            <div style={{ position: 'relative', width: '100%', display: 'flex', alignItems: 'center' }}>
                <textarea 
                rows="1" 
                placeholder={`Ask ${selectedDbName} a question (e.g., "Why are sales down?")`}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                style={{ width: '100%', padding: '16px 60px 16px 20px', borderRadius: '12px', border: '1px solid #e5e7eb', background: '#f9fafb', fontSize: '1rem', outline: 'none', resize: 'none' }}
                ></textarea>
                <button 
                    className="send-btn" 
                    onClick={() => handleSend()} 
                    disabled={loading || !input.trim()}
                    style={{ position: 'absolute', right: '10px', background: '#000', color: '#fff', width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                <Send size={20} />
                </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
