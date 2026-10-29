import React from 'react';
import { TrendingUp, ShieldCheck, DollarSign, Calendar } from 'lucide-react';
import BorderBeam from './ui/BorderBeam';

export default function RecommendationCard({ recommendation }) {
  if (!recommendation) return null;

  const formatINR = (val) => {
    if (val === undefined || val === null) return '₹0.00';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  const {
    sqft,
    immediate_month,
    immediate_cost_rs,
    recommended_year_month,
    optimal_cost_rs,
    savings_rs,
    savings_percent,
    is_immediate_recommended,
    summary_message,
    steel_horizon_mape_pct,
    steel_horizon_sample_count,
    reliability_subtext,
  } = recommendation;

  return (
    <div className={`card recommendation-card blueprint-panel ${is_immediate_recommended ? 'highlight-immediate' : 'highlight-optimal'}`}>
      <span className="corner-mark top-left">+</span>
      <span className="corner-mark top-right">+</span>
      <span className="corner-mark bottom-left">+</span>
      <span className="corner-mark bottom-right">+</span>

      <div className="recommendation-header">
        <div className="badge-recommendation">
          <ShieldCheck size={16} />
          <span>OPTIMAL WINDOW DECISION</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {steel_horizon_mape_pct !== undefined && (
            <div className="dark-coordinate-tooltip" style={{ padding: '4px 10px' }}>
              <span className="tooltip-label">BACKTEST ACCURACY: </span>
              <span className="tooltip-val accent">±{steel_horizon_mape_pct}%</span>
              {steel_horizon_sample_count && (
                <span className="tooltip-val" style={{ marginLeft: '6px' }}>(N={steel_horizon_sample_count})</span>
              )}
            </div>
          )}
          <span className="build-size-pill mono-readout">PROJECT SIZE: {sqft} SQ FT</span>
        </div>
      </div>

      <div className="recommendation-grid">
        <div className="rec-metric-card primary">
          <div className="metric-label">
            <Calendar size={15} /> RECOMMENDED PURCHASE MONTH
          </div>
          <div className="metric-value highlight mono-readout">{recommended_year_month}</div>
          <div className="metric-subtext">
            {is_immediate_recommended ? 'IMMEDIATE PROCUREMENT ADVISED' : 'OPTIMAL WINDOW TARGET'}
          </div>
        </div>

        <div className="rec-metric-card">
          <div className="metric-label">OPTIMAL BOM COST</div>
          <div className="metric-value mono-readout">{formatINR(optimal_cost_rs)}</div>
          <div className="metric-subtext">TOTAL ESTIMATED BASELINE</div>
        </div>

        <div className="rec-metric-card">
          <div className="metric-label">IMMEDIATE PURCHASE COST ({immediate_month})</div>
          <div className="metric-value mono-readout">{formatINR(immediate_cost_rs)}</div>
          <div className="metric-subtext">CURRENT REFERENCE ANCHOR</div>
        </div>

        <div className="rec-metric-card savings">
          <div className="metric-label">
            <DollarSign size={15} /> PROJECTED SAVINGS
          </div>
          <div className="metric-value savings-text mono-readout">
            {formatINR(savings_rs)} ({savings_percent.toFixed(2)}%)
          </div>
          <div className="metric-subtext">
            {savings_rs > 0 ? 'COST AVOIDANCE ACHIEVED' : 'NO ADDITIONAL DELAY SAVINGS'}
          </div>
        </div>
      </div>

      <div className="summary-message-box" style={{ position: 'relative', overflow: 'hidden' }}>
        <BorderBeam size={260} duration={6} colorFrom="#fa3600" colorTo="#ff7a00" borderWidth={2} />
        <TrendingUp size={20} className="summary-icon" />
        <div className="summary-text-wrapper">
          <strong>STRATEGIC RECOMMENDATION READOUT:</strong>
          <p>{summary_message}</p>
          {reliability_subtext && (
            <p className="readout-note">
              READOUT NOTE: {reliability_subtext}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
