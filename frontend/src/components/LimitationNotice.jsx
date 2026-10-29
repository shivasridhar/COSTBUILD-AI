import React from 'react';

export default function LimitationNotice({ metadata }) {
  if (!metadata || !metadata.model_limitation_note) return null;

  const formattedMethod = String(metadata.forecast_method || 'naive_plus_drift')
    .toUpperCase()
    .replace(/_/g, ' + ');

  return (
    <div className="card limitation-card blueprint-panel">
      <span className="corner-mark top-left">+</span>
      <span className="corner-mark top-right">+</span>
      <span className="corner-mark bottom-left">+</span>
      <span className="corner-mark bottom-right">+</span>

      <div className="limitation-header">
        <div>
          <h3>Transparency & Model Methodology Disclosure</h3>
          <span className="forecast-method-tag">METHODOLOGY: {formattedMethod}</span>
        </div>
      </div>

      <div className="limitation-body">
        <p className="limitation-main-text">{metadata.model_limitation_note}</p>

        {metadata.methodology_note && (
          <div className="limitation-material-note">
            <strong>Material Methodology Note</strong>
            <p>{metadata.methodology_note}</p>
          </div>
        )}
      </div>
    </div>
  );
}
