import React from 'react';
import { TrendingUp, ShieldCheck, DollarSign, Calendar, ArrowRight } from 'lucide-react';

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
  } = recommendation;

  return (
    <div className={`card recommendation-card ${is_immediate_recommended ? 'highlight-immediate' : 'highlight-optimal'}`}>
      <div className="recommendation-header">
        <div className="badge-recommendation">
          <ShieldCheck size={16} />
          <span>Optimal Window Decision</span>
        </div>
        <span className="build-size-pill">Project Size: {sqft} sq ft</span>
      </div>

      <div className="recommendation-grid">
        <div className="rec-metric-card primary">
          <div className="metric-label">
            <Calendar size={16} /> Recommended Purchase Month
          </div>
          <div className="metric-value highlight">{recommended_year_month}</div>
          <div className="metric-subtext">
            {is_immediate_recommended ? 'Immediate Procurement Advised' : `Optimal Window (Month Index)`}
          </div>
        </div>

        <div className="rec-metric-card">
          <div className="metric-label">Optimal BOM Cost</div>
          <div className="metric-value">{formatINR(optimal_cost_rs)}</div>
          <div className="metric-subtext">Total Estimated Baseline</div>
        </div>

        <div className="rec-metric-card">
          <div className="metric-label">Immediate Purchase Cost ({immediate_month})</div>
          <div className="metric-value">{formatINR(immediate_cost_rs)}</div>
          <div className="metric-subtext">Current Reference Anchor</div>
        </div>

        <div className="rec-metric-card savings">
          <div className="metric-label">
            <DollarSign size={16} /> Projected Savings
          </div>
          <div className="metric-value savings-text">
            {formatINR(savings_rs)} ({savings_percent.toFixed(2)}%)
          </div>
          <div className="metric-subtext">
            {savings_rs > 0 ? 'Cost Avoidance Achieved' : 'No Additional Delay Savings'}
          </div>
        </div>
      </div>

      <div className="summary-message-box">
        <TrendingUp size={20} className="summary-icon" />
        <div className="summary-text-wrapper">
          <strong>Strategic Recommendation:</strong>
          <p>{summary_message}</p>
        </div>
      </div>
    </div>
  );
}
