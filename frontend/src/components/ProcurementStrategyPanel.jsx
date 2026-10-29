import React from 'react';
import { ShieldAlert, Package, Layers, TrendingDown, Info, Calendar, ArrowRight, AlertTriangle } from 'lucide-react';

export default function ProcurementStrategyPanel({ strategyData }) {
  if (!strategyData || !strategyData.advisories || strategyData.advisories.length === 0) {
    return null;
  }

  const { advisories, project_name } = strategyData;

  return (
    <div className="blueprint-panel procurement-strategy-panel" style={{
      backgroundColor: 'var(--bg-cream-alt)',
      border: '1px solid var(--line-gray)',
      padding: '24px 28px',
      marginBottom: '28px',
      position: 'relative'
    }}>
      <span className="corner-mark top-left">+</span>
      <span className="corner-mark top-right">+</span>
      <span className="corner-mark bottom-left">+</span>
      <span className="corner-mark bottom-right">+</span>

      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px',
        borderBottom: '1px solid var(--line-gray)',
        paddingBottom: '16px',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            backgroundColor: 'var(--ink-black)',
            color: 'var(--accent-orange)',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Package size={18} />
          </div>
          <div>
            <h3 style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.15rem',
              fontWeight: '800',
              textTransform: 'uppercase',
              color: 'var(--ink-black)',
              margin: 0
            }}>
              STORAGE-FEASIBILITY PROCUREMENT STRATEGY ADVISORY
            </h3>
            <p style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--label-gray-dark)',
              textTransform: 'uppercase',
              margin: 0
            }}>
              CROSS-PHASE MATERIAL SHELF-LIFE & DEGRADATION RISK EVALUATION • {project_name}
            </p>
          </div>
        </div>

        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          fontWeight: '700',
          backgroundColor: '#ffffff',
          border: '1px solid var(--line-gray)',
          padding: '6px 12px',
          color: 'var(--ink-black)'
        }}>
          {advisories.length} SHARED MATERIAL{advisories.length > 1 ? 'S' : ''} EVALUATED
        </div>
      </div>

      {/* Advisories Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {advisories.map((adv) => {
          const isBulk = adv.strategy === 'bulk';
          const isSafe = adv.storage_safe;

          return (
            <div
              key={adv.material}
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--line-gray)',
                padding: '20px 22px',
                position: 'relative'
              }}
            >
              {/* Material Title Bar */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                flexWrap: 'wrap',
                gap: '12px',
                marginBottom: '14px'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <h4 style={{
                      fontFamily: 'var(--font-headline)',
                      fontSize: '1.1rem',
                      fontWeight: '800',
                      textTransform: 'uppercase',
                      color: 'var(--ink-black)',
                      margin: 0
                    }}>
                      {adv.material.toUpperCase()}
                    </h4>

                    {/* Strategy Badge (Strict Blueprint Palette: Solid Orange for Bulk, Dark Ink for Per-Phase) */}
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.72rem',
                      fontWeight: '800',
                      textTransform: 'uppercase',
                      padding: '4px 10px',
                      backgroundColor: isBulk ? 'var(--accent-orange)' : 'var(--ink-black)',
                      color: '#ffffff',
                      letterSpacing: '0.05em'
                    }}>
                      {isBulk ? 'BULK PURCHASE RECOMMENDED' : 'PER-PHASE PURCHASE RECOMMENDED'}
                    </span>
                  </div>

                  <div style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.76rem',
                    color: 'var(--label-gray-dark)'
                  }}>
                    Phases Involved: <strong>{adv.phases_involved.join(' → ')}</strong>
                  </div>
                </div>

                {/* Technical Readouts */}
                <div style={{
                  display: 'flex',
                  gap: '12px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.76rem'
                }}>
                  <div style={{
                    backgroundColor: 'var(--bg-cream-alt)',
                    border: '1px solid var(--line-gray)',
                    padding: '6px 10px',
                    textAlign: 'center'
                  }}>
                    <span style={{ display: 'block', fontSize: '0.68rem', color: 'var(--label-gray)' }}>PHASE GAP</span>
                    <strong style={{ color: 'var(--ink-black)' }}>{adv.gap_days} DAYS ({adv.gap_months}m)</strong>
                  </div>

                  <div style={{
                    backgroundColor: 'var(--bg-cream-alt)',
                    border: '1px solid var(--line-gray)',
                    padding: '6px 10px',
                    textAlign: 'center'
                  }}>
                    <span style={{ display: 'block', fontSize: '0.68rem', color: 'var(--label-gray)' }}>SAFE STORAGE LIMIT</span>
                    <strong style={{ color: isSafe ? 'var(--ink-black)' : 'var(--accent-orange)' }}>
                      {adv.max_safe_storage_days ? `~${adv.max_safe_storage_days} DAYS` : 'UNLIMITED'}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Reasoning Callout */}
              <div style={{
                backgroundColor: isBulk ? 'rgba(217, 83, 30, 0.05)' : 'var(--bg-cream-alt)',
                borderLeft: `4px solid ${isBulk ? 'var(--accent-orange)' : 'var(--ink-black)'}`,
                padding: '12px 14px',
                marginBottom: '14px',
                fontSize: '0.85rem',
                color: 'var(--ink-soft)',
                lineHeight: '1.5'
              }}>
                <strong style={{ color: 'var(--ink-black)' }}>Advisory Reasoning: </strong>
                {adv.reasoning}
              </div>

              {/* Cost Comparison Readouts (If Bulk vs Per-Phase) */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px',
                marginBottom: '14px',
                padding: '12px 14px',
                backgroundColor: '#ffffff',
                border: '1px dashed var(--line-gray)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.78rem'
              }}>
                <div>
                  <span style={{ color: 'var(--label-gray-dark)', display: 'block', fontSize: '0.7rem' }}>COMBINED BULK COST</span>
                  <strong style={{ fontSize: '0.95rem', color: 'var(--ink-black)' }}>
                    ₹{adv.bulk_cost_estimate_rs.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--label-gray)' }}>
                    Month: {adv.bulk_recommended_month}
                  </span>
                </div>

                <div>
                  <span style={{ color: 'var(--label-gray-dark)', display: 'block', fontSize: '0.7rem' }}>SEPARATE PER-PHASE TOTAL</span>
                  <strong style={{ fontSize: '0.95rem', color: 'var(--ink-black)' }}>
                    ₹{adv.per_phase_cost_estimate_rs.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--label-gray)' }}>
                    Sum across {adv.phase_count} phases
                  </span>
                </div>

                {isBulk && adv.savings_rs > 0 && (
                  <div style={{ backgroundColor: 'rgba(217, 83, 30, 0.08)', padding: '8px 12px', borderLeft: '3px solid var(--accent-orange)' }}>
                    <span style={{ color: 'var(--accent-orange)', fontWeight: '800', display: 'block', fontSize: '0.7rem' }}>PROJECTED BULK SAVINGS</span>
                    <strong style={{ fontSize: '1rem', color: 'var(--accent-orange)' }}>
                      ₹{adv.savings_rs.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </strong>
                    <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--accent-orange)' }}>
                      ({adv.savings_pct}% lower cost)
                    </span>
                  </div>
                )}
              </div>

              {/* Storage & Degradation Notes Disclosure */}
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.72rem',
                color: 'var(--label-gray-dark)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '6px'
              }}>
                <Info size={14} style={{ color: 'var(--label-gray)', flexShrink: 0, marginTop: '2px' }} />
                <span><strong>Storage Site Guidance: </strong>{adv.storage_notes}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
