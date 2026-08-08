import React from 'react';
import { Info, ShieldAlert } from 'lucide-react';

export default function LimitationNotice({ metadata }) {
  if (!metadata || !metadata.model_limitation_note) return null;

  return (
    <div className="card limitation-card">
      <div className="limitation-header">
        <ShieldAlert className="limitation-icon" size={24} />
        <div>
          <h3>Transparency & Model Methodology Disclosure</h3>
          <span className="forecast-method-tag">Methodology: {metadata.forecast_method || 'naive_plus_drift'}</span>
        </div>
      </div>
      <div className="limitation-body">
        <p>{metadata.model_limitation_note}</p>
      </div>
    </div>
  );
}
