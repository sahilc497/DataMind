import React from 'react';
import { AlertTriangle, CheckCircle2, Wrench, Zap, Info } from 'lucide-react';

export function MechanicalAnalysisCard({ analysis }) {
  if (!analysis) return null;
  const diagnoses = analysis.diagnoses || [];
  if (diagnoses.length === 0) return null;

  return (
    <div className="mech-analysis-card">
      <div className="mech-analysis-header">
        <div className="mech-analysis-title">
          <Zap size={14} color="#EA580C" /> Mechanical Analysis
        </div>
        <span className={`severity-badge ${diagnoses[0]?.severity || 'low'}`}>
          {diagnoses[0]?.severity?.toUpperCase() || 'OK'}
        </span>
      </div>
      {diagnoses.slice(0, 3).map((d, i) => (
        <div key={i} style={{ marginBottom: i < diagnoses.length - 1 ? 14 : 0 }}>
          <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)', marginBottom: 4 }}>
            {d.issue}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 6 }}>
            <strong>Cause:</strong> {d.cause}
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
            <span className={`severity-badge ${d.severity}`}>{d.severity}</span>
            <span className="badge-pill">{d.confidence}% confidence</span>
            <span className="badge-pill" style={{ background: 'var(--mech-teal-soft)', color: 'var(--mech-teal)', borderColor: 'rgba(13,148,136,0.15)' }}>
              {d.affected_component}
            </span>
          </div>
          {d.physics_explanation && (
            <div className="physics-explanation">
              <Info size={12} style={{ display: 'inline', marginRight: 4 }} />
              {d.physics_explanation}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export function PredictionCard({ prediction }) {
  if (!prediction || prediction.failure_probability === undefined) return null;
  const prob = Math.round(prediction.failure_probability * 100);
  const risk = prediction.risk_level || 'low';

  return (
    <div className="prediction-widget">
      <div className={`prediction-gauge ${risk}`}>{prob}%</div>
      <div className="prediction-details">
        <div className="pred-label">Failure Prediction</div>
        <div className="pred-rul">
          RUL: ~{prediction.remaining_useful_life_hours || '—'}h · Trend: {prediction.trend || 'stable'}
        </div>
        {prediction.contributing_factors?.length > 0 && (
          <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {prediction.contributing_factors.slice(0, 3).map((f, i) => (
              <span key={i} className="badge-pill" style={{ fontSize: '0.62rem' }}>
                {f.factor}: {f.value}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function RecommendationCard({ recommendation }) {
  if (!recommendation || !recommendation.actions?.length) return null;

  const urgencyColors = { critical: '#EF4444', high: '#EA580C', medium: '#D97706', low: '#22C55E', routine: '#94A3B8' };

  return (
    <div className="rec-card">
      <div className="rec-header">
        <Wrench size={16} color={urgencyColors[recommendation.urgency] || '#94A3B8'} />
        <span className="rec-urgency" style={{ color: urgencyColors[recommendation.urgency] }}>
          {recommendation.urgency_label || 'ROUTINE'} — Action Required
        </span>
      </div>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 14, lineHeight: 1.6 }}>
        {recommendation.summary}
      </div>
      <ul className="rec-action-list">
        {recommendation.actions.slice(0, 5).map((a, i) => (
          <li key={i} className="rec-action-item">
            <div className={`rec-action-dot ${a.priority || 'medium'}`}></div>
            <div>
              <div>{a.action}</div>
              {a.skill && <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Requires: {a.skill} · ~{a.time_min}min</span>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function InsightsBanner({ insights }) {
  if (!insights || insights.length === 0) return null;
  return (
    <div>
      {insights.slice(0, 3).map((ins, i) => (
        <div key={i} className="insight-banner">
          <div className="insight-tag">Auto Insight · {ins.severity?.toUpperCase()}</div>
          <div className="insight-text">{ins.text}</div>
        </div>
      ))}
    </div>
  );
}
