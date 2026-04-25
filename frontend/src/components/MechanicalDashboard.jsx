import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings, AlertTriangle, CheckCircle2, Thermometer, Activity, Gauge, Wrench, Zap, RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const QUICK_QUERIES = [
  { icon: '🔍', text: 'Which machine is likely to fail?' },
  { icon: '🔥', text: 'Why is Machine 2 overheating?' },
  { icon: '🛠️', text: 'What should I do about Machine 5?' },
  { icon: '📊', text: 'Show sensor data for all machines' },
  { icon: '⚡', text: 'Simulate: increase load by 20% on Machine 1' },
];

function MachineCard({ machine }) {
  const h = machine.health || {};
  const p = machine.prediction || {};
  const m = machine.metrics || {};
  const status = h.status || 'unknown';
  const color = h.color || 'green';
  const prob = p.failure_probability || 0;
  const probPct = Math.round(prob * 100);
  const riskClass = probPct > 60 ? 'high' : probPct > 30 ? 'medium' : 'low';

  const getMetricClass = (key, val) => {
    if (key === 'temperature' && val > 90) return 'danger';
    if (key === 'temperature' && val > 75) return 'warning';
    if (key === 'vibration' && val > 4.5) return 'danger';
    if (key === 'vibration' && val > 3.0) return 'warning';
    if (key === 'efficiency' && val < 65) return 'danger';
    if (key === 'efficiency' && val < 78) return 'warning';
    return '';
  };

  return (
    <div className={`machine-card ${status}`}>
      <div className="machine-card-header">
        <div>
          <div className="machine-card-name">{machine.name}</div>
          <div className="machine-card-type">{machine.type} · {machine.location}</div>
        </div>
        <div className={`health-dot ${color}`}></div>
      </div>
      <div className="metrics-grid">
        <div className="metric-item">
          <div className="metric-label">Temperature</div>
          <div className={`metric-value ${getMetricClass('temperature', m.avg_temperature)}`}>
            {m.avg_temperature?.toFixed(1) || '—'}°C
          </div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Vibration</div>
          <div className={`metric-value ${getMetricClass('vibration', m.avg_vibration)}`}>
            {m.avg_vibration?.toFixed(2) || '—'} mm/s
          </div>
        </div>
        <div className="metric-item">
          <div className="metric-label">RPM</div>
          <div className="metric-value">{Math.round(m.avg_rpm || 0)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Efficiency</div>
          <div className={`metric-value ${getMetricClass('efficiency', m.avg_efficiency)}`}>
            {m.avg_efficiency?.toFixed(1) || '—'}%
          </div>
        </div>
      </div>
      <div className="failure-bar-container">
        <div className="failure-bar-label">
          <span>Failure Risk</span>
          <span style={{ color: probPct > 60 ? '#EF4444' : probPct > 30 ? '#D97706' : '#22C55E' }}>{probPct}%</span>
        </div>
        <div className="failure-bar">
          <div className={`failure-bar-fill ${riskClass}`} style={{ width: `${probPct}%` }}></div>
        </div>
      </div>
    </div>
  );
}

export default function MechanicalDashboard({ onQuerySelect }) {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/dashboard`);
      setDashboard(res.data);
    } catch (err) {
      console.error('Dashboard fetch failed', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDashboard(); }, []);

  if (loading) {
    return (
      <div className="mech-loading">
        <Settings size={48} className="gear-spin" style={{ color: '#EA580C', opacity: 0.3 }} />
        <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontWeight: 600 }}>Loading Fleet Intelligence...</span>
      </div>
    );
  }

  const d = dashboard || {};
  return (
    <div style={{ animation: 'slideInUp 0.4s ease-out' }}>
      <div className="dashboard-header">
        <div>
          <div className="dashboard-title">🛡️ Sentinel Fleet Intelligence</div>
          <div className="dashboard-subtitle">{d.total_machines || 0} machines monitored · Real-time analysis</div>
        </div>
        <button onClick={fetchDashboard} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '8px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', fontFamily: 'inherit' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="fleet-stats">
        <div className="fleet-stat">
          <div className="fleet-stat-value" style={{ color: '#22C55E' }}>{d.healthy_count || 0}</div>
          <div className="fleet-stat-label">Healthy</div>
        </div>
        <div className="fleet-stat">
          <div className="fleet-stat-value" style={{ color: '#D97706' }}>{d.warning_count || 0}</div>
          <div className="fleet-stat-label">Warning</div>
        </div>
        <div className="fleet-stat">
          <div className="fleet-stat-value" style={{ color: '#EF4444' }}>{d.critical_count || 0}</div>
          <div className="fleet-stat-label">Critical</div>
        </div>
        <div className="fleet-stat">
          <div className="fleet-stat-value" style={{ color: 'var(--text-primary)' }}>{d.total_machines || 0}</div>
          <div className="fleet-stat-label">Total</div>
        </div>
      </div>

      {d.fleet_insights && d.fleet_insights.length > 0 && (
        <div style={{ padding: '0 24px' }}>
          {d.fleet_insights.map((ins, i) => (
            <div key={i} className="insight-banner">
              <div className="insight-tag">Fleet Insight</div>
              <div className="insight-text">{ins.text}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ padding: '16px 24px 4px' }}>
        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Quick Actions</div>
      </div>
      <div className="quick-actions">
        {QUICK_QUERIES.map((q, i) => (
          <button key={i} className="quick-chip" onClick={() => onQuerySelect(q.text)}>
            <span>{q.icon}</span> {q.text}
          </button>
        ))}
      </div>

      <div className="fleet-grid">
        {(d.machines || []).map(m => <MachineCard key={m.id} machine={m} />)}
      </div>
    </div>
  );
}
