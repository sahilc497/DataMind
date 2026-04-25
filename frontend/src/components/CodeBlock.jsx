import React, { useState } from 'react';
import { Terminal, Edit2, Copy, Play } from 'lucide-react';

export default function CodeBlock({ sql, dbType, onCopy, onRerun }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedSql, setEditedSql] = useState(sql);

  return (
    <div className="code-container" style={{ position: 'relative' }}>
      <div className="code-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Terminal size={12} /><span>{(dbType || 'SQL').toUpperCase()} QUERY</span>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button onClick={() => setIsEditing(!isEditing)} style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}>
            <Edit2 size={12} /> {isEditing ? 'Cancel' : 'Edit'}
          </button>
          <button onClick={() => onCopy(sql)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}>
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
            onClick={() => { onRerun(editedSql); setIsEditing(false); }}
            style={{ marginTop: '8px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', padding: '4px 12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}
          >
            <Play size={12} /> Re-run Query
          </button>
        </div>
      ) : (
        <div className="code-content" style={{ fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>{sql}</div>
      )}
    </div>
  );
}
