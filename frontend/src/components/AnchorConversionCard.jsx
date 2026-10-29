import React from 'react';
import { Anchor, CheckCircle2, XCircle } from 'lucide-react';

export default function AnchorConversionCard({ anchorData }) {
  if (!anchorData) return null;

  const { cement, steel, sanity_check_passed } = anchorData;

  const formatINR = (val) => {
    if (val === undefined || val === null) return '-';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  return (
    <div className="card anchor-card blueprint-panel">
      <span className="corner-mark top-left">+</span>
      <span className="corner-mark top-right">+</span>
      <span className="corner-mark bottom-left">+</span>
      <span className="corner-mark bottom-right">+</span>

      <div className="card-header space-between">
        <div className="flex-align">
          <Anchor className="header-icon" size={22} />
          <div>
            <h2>PWD FY 2025-26 Reference Anchor Conversion & Vendor Quote Corrections</h2>
            <p className="subtitle">Official Schedule of Rates baseline calibrated to index points & nudged by real market quotes</p>
          </div>
        </div>

        {/* Sanity Check Confirmation Badge */}
        <div className={`badge-verdict ${sanity_check_passed ? 'verdict-at-market' : 'verdict-above-market'}`}>
          {sanity_check_passed ? (
            <>
              <CheckCircle2 size={15} />
              <span>SANITY CHECK PASSED</span>
            </>
          ) : (
            <>
              <XCircle size={15} />
              <span>SANITY CHECK FAILED</span>
            </>
          )}
        </div>
      </div>

      <div className="anchor-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {cement && (
          <div className="anchor-material-box" style={{ backgroundColor: 'var(--bg-cream)', border: 'var(--border-hairline)', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 className="mat-title cement" style={{ margin: 0, fontFamily: 'var(--font-headline)', textTransform: 'uppercase', fontSize: '1rem', fontWeight: 800 }}>Cement Anchor</h3>
              {cement.correction && (
                <span className={`badge-verdict ${cement.correction.correction_applied ? 'verdict-above-market' : 'verdict-below-market'}`} style={{ fontSize: '9px', padding: '2px 6px' }}>
                  {cement.correction.correction_applied ? 'VENDOR CORRECTED' : 'WPI ANCHOR ONLY'}
                </span>
              )}
            </div>
            <div className="anchor-details" style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
              <div className="detail-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--label-gray-dark)' }}>PWD Reference Rate (FY 25-26):</span>
                <strong>{formatINR(cement.pwd_rate_rs_per_MT)} / MT</strong>
              </div>
              {cement.effective_rate_rs_per_MT && (
                <div className="detail-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--label-gray-dark)' }}>Effective Market Baseline:</span>
                  <strong style={{ color: 'var(--accent-orange)' }}>{formatINR(cement.effective_rate_rs_per_MT)} / MT</strong>
                </div>
              )}
              <div className="detail-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--label-gray-dark)' }}>FY 25-26 Avg WPI Index:</span>
                <strong>{cement.fy25_26_avg_wpi?.toFixed(2)} pts</strong>
              </div>
              <div className="detail-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--label-gray-dark)' }}>Conversion Factor:</span>
                <strong>₹{cement.rs_per_index_point?.toFixed(2)} / pt</strong>
              </div>
              {cement.correction && cement.correction.correction_applied && (
                <div className="dark-coordinate-tooltip" style={{ marginTop: '8px' }}>
                  Blended from {cement.correction.quote_count} recent vendor quotes (Median: {formatINR(cement.correction.vendor_median_rate)})
                </div>
              )}
            </div>
          </div>
        )}

        {steel && (
          <div className="anchor-material-box" style={{ backgroundColor: 'var(--bg-cream)', border: 'var(--border-hairline)', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 className="mat-title steel" style={{ margin: 0, fontFamily: 'var(--font-headline)', textTransform: 'uppercase', fontSize: '1rem', fontWeight: 800 }}>Steel Anchor</h3>
              {steel.correction && (
                <span className={`badge-verdict ${steel.correction.correction_applied ? 'verdict-above-market' : 'verdict-below-market'}`} style={{ fontSize: '9px', padding: '2px 6px' }}>
                  {steel.correction.correction_applied ? 'VENDOR CORRECTED' : 'WPI ANCHOR ONLY'}
                </span>
              )}
            </div>
            <div className="anchor-details" style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
              <div className="detail-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--label-gray-dark)' }}>PWD Reference Rate (FY 25-26):</span>
                <strong>{formatINR(steel.pwd_rate_rs_per_MT)} / MT</strong>
              </div>
              {steel.effective_rate_rs_per_MT && (
                <div className="detail-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--label-gray-dark)' }}>Effective Market Baseline:</span>
                  <strong style={{ color: 'var(--accent-orange)' }}>{formatINR(steel.effective_rate_rs_per_MT)} / MT</strong>
                </div>
              )}
              <div className="detail-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--label-gray-dark)' }}>FY 25-26 Avg WPI Index:</span>
                <strong>{steel.fy25_26_avg_wpi?.toFixed(2)} pts</strong>
              </div>
              <div className="detail-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--label-gray-dark)' }}>Conversion Factor:</span>
                <strong>₹{steel.rs_per_index_point?.toFixed(2)} / pt</strong>
              </div>
              {steel.correction && steel.correction.correction_applied && (
                <div className="dark-coordinate-tooltip" style={{ marginTop: '8px' }}>
                  Blended from {steel.correction.quote_count} recent vendor quotes (Median: {formatINR(steel.correction.vendor_median_rate)})
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
