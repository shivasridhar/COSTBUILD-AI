import React, { useState } from 'react';
import { deletePhase } from '../api/client';
import {
  Layers,
  Calendar,
  DollarSign,
  TrendingDown,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Info,
  Edit2,
  Trash2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Plus
} from 'lucide-react';

export default function PhaseTimeline({ projectId, phasesSummary = [], onEditPhase, onPhaseDeleted, onAddPhaseClick }) {
  const [expandedPhaseId, setExpandedPhaseId] = useState(null);

  const handleDelete = async (phaseId, phaseName) => {
    if (!window.confirm(`Are you sure you want to delete phase "${phaseName}"?`)) {
      return;
    }
    try {
      await deletePhase(projectId, phaseId);
      if (onPhaseDeleted) onPhaseDeleted(phaseId);
    } catch (err) {
      alert('Failed to delete phase: ' + err.message);
    }
  };

  const formatINR = (val) => {
    if (val === undefined || val === null) return '₹0.00';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  const getStatusPill = (status) => {
    switch (status) {
      case 'active':
        return <span className="status-pill status-in-progress"><Clock size={11} /> ACTIVE</span>;
      case 'completed':
        return <span className="status-pill status-completed"><CheckCircle2 size={11} /> COMPLETED</span>;
      default:
        return <span className="status-pill status-planning"><Layers size={11} /> UPCOMING</span>;
    }
  };

  if (!phasesSummary || phasesSummary.length === 0) {
    return (
      <div className="empty-phases-card blueprint-panel">
        <span className="corner-mark top-left">+</span>
        <span className="corner-mark top-right">+</span>
        <span className="corner-mark bottom-left">+</span>
        <span className="corner-mark bottom-right">+</span>
        <Layers size={36} className="empty-phases-icon" style={{ color: 'var(--accent-orange)' }} />
        <h3 style={{ fontFamily: 'var(--font-headline)', textTransform: 'uppercase', marginTop: '12px', fontWeight: 800 }}>No Construction Phases Defined</h3>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--label-gray-dark)', margin: '8px 0 16px 0' }}>
          Split your build into sequential phases (e.g. Foundation, Structure, Fit-Out) to get phase-scoped procurement recommendations with true-horizon confidence bands.
        </p>
        <button onClick={onAddPhaseClick} className="btn-add-phase">
          <Plus size={15} /> Add First Phase
        </button>
      </div>
    );
  }

  return (
    <div className="phase-timeline-wrapper">
      <div className="timeline-header-bar">
        <div>
          <h3 className="timeline-main-title">Staged Construction Procurement Sequence</h3>
          <p className="timeline-main-subtitle">
            Phase-scoped procurement recommendations evaluated over each phase's offset timeframe.
          </p>
        </div>
        <button onClick={onAddPhaseClick} className="btn-add-phase">
          <Plus size={15} /> Add Phase
        </button>
      </div>

      <div className="timeline-stepper">
        {phasesSummary.map((item, idx) => {
          const ph = item.phase;
          const rec = item.recommendation;
          const isExpanded = expandedPhaseId === ph.id;
          const hasSavings = rec && rec.savings_rs > 0;

          return (
            <div key={ph.id} className="timeline-item">
              {/* Stepper Node Square Icon */}
              <div className={`timeline-node ${ph.status}`}>
                <span>#{ph.sequence_order}</span>
              </div>

              {/* Connector Dashed Line */}
              {idx < phasesSummary.length - 1 && <div className="timeline-connector"></div>}

              {/* Phase Content Card */}
              <div className="timeline-content-card blueprint-panel">
                <span className="corner-mark top-left">+</span>
                <span className="corner-mark top-right">+</span>
                <span className="corner-mark bottom-left">+</span>
                <span className="corner-mark bottom-right">+</span>

                <div className="phase-card-header">
                  <div className="phase-title-group">
                    <h4 className="phase-name-text">{ph.phase_name}</h4>
                    {getStatusPill(ph.status)}
                    <span className="start-offset-chip">
                      <Calendar size={12} />
                      STARTS MONTH {ph.expected_start_month} {ph.expected_start_month === 0 ? '(IMMEDIATE)' : `(+${ph.expected_start_month}M)`}
                    </span>
                  </div>

                  <div className="phase-actions">
                    <button onClick={() => onEditPhase(ph)} className="btn-phase-icon" title="Edit Phase">
                      <Edit2 size={13} />
                    </button>
                    <button onClick={() => handleDelete(ph.id, ph.phase_name)} className="btn-phase-icon text-danger" title="Delete Phase">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                {/* Scope Badges */}
                <div className="phase-materials-bar">
                  <span className="scope-label">PHASE SCOPE:</span>
                  <div className="scope-chips">
                    {ph.materials.map((m) => (
                      <span key={m} className="mat-badge">{m}</span>
                    ))}
                  </div>
                </div>

                {/* Recommendation Banner */}
                {rec && (
                  <div className={`phase-rec-card ${rec.is_immediate_recommended ? 'immediate' : 'optimal'}`}>
                    <div className="phase-rec-header">
                      <div className="phase-rec-title">
                        {rec.is_immediate_recommended ? (
                          <>
                            <Sparkles size={15} color="var(--accent-orange)" /> PROCURE AT PHASE START ({rec.immediate_month})
                          </>
                        ) : (
                          <>
                            <TrendingDown size={15} color="var(--accent-orange)" /> OPTIMAL WINDOW: MONTH {rec.recommended_month_idx} ({rec.recommended_year_month})
                          </>
                        )}
                      </div>
                      <div className="phase-savings-tag">
                        {hasSavings ? (
                          <span>SAVE {formatINR(rec.savings_rs)} ({rec.savings_percent}%)</span>
                        ) : (
                          <span>BUY AT START</span>
                        )}
                      </div>
                    </div>

                    <p className="phase-summary-text">{rec.summary_message}</p>

                    {/* Cost Metrics Breakdown */}
                    <div className="phase-cost-grid">
                      <div className="phase-cost-metric">
                        <span className="metric-lbl">START COST (MONTH {ph.expected_start_month + 1}):</span>
                        <span className="metric-val">{formatINR(rec.immediate_cost_rs)}</span>
                      </div>
                      <div className="phase-cost-metric">
                        <span className="metric-lbl">OPTIMAL PHASE COST:</span>
                        <span className="metric-val highlight">{formatINR(rec.optimal_cost_rs)}</span>
                      </div>
                      <div className="phase-cost-metric">
                        <span className="metric-lbl">TARGET WINDOW:</span>
                        <span className="metric-val">{rec.recommended_year_month}</span>
                      </div>
                    </div>

                    {/* True-Horizon Reliability Notice (Dark Coordinate Box) */}
                    {rec.reliability_subtext && (
                      <div className="phase-reliability-footnote">
                        <Info size={14} style={{ color: 'var(--accent-orange)', flexShrink: 0 }} />
                        <span>READOUT: {rec.reliability_subtext}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Expand / Collapse Forecast Table Toggle */}
                {item.forecast && (
                  <div className="phase-table-toggle">
                    <button
                      onClick={() => setExpandedPhaseId(isExpanded ? null : ph.id)}
                      className="btn-toggle-table"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp size={13} /> HIDE MONTHLY COST BREAKDOWN
                        </>
                      ) : (
                        <>
                          <ChevronDown size={13} /> VIEW 12-MONTH PHASE COST BREAKDOWN
                        </>
                      )}
                    </button>

                    {isExpanded && (
                      <div className="phase-forecast-table-container">
                        <table className="phase-mini-table">
                          <thead>
                            <tr>
                              <th>HORIZON</th>
                              <th>YEAR-MONTH</th>
                              <th>PHASE BOM COST (₹)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {item.bom_cost_by_month.map((row) => (
                              <tr
                                key={row.year_month}
                                className={row.year_month === rec?.recommended_year_month ? 'rec-row' : ''}
                              >
                                <td>Month {row.month_idx}</td>
                                <td>{row.year_month}</td>
                                <td><strong>{formatINR(row.total_bom_cost_rs)}</strong></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
