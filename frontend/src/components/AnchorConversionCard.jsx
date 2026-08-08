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
    <div className="card anchor-card">
      <div className="card-header space-between">
        <div className="flex-align">
          <Anchor className="header-icon" size={22} />
          <div>
            <h2>PWD FY 2025-26 Reference Anchor Conversion</h2>
            <p className="subtitle">Official Schedule of Rates baseline calibrated to index points</p>
          </div>
        </div>

        {/* Visible Sanity Check Confirmation Badge */}
        <div className={`sanity-badge ${sanity_check_passed ? 'passed' : 'failed'}`}>
          {sanity_check_passed ? (
            <>
              <CheckCircle2 size={18} />
              <span>Sanity Check Passed</span>
            </>
          ) : (
            <>
              <XCircle size={18} />
              <span>Sanity Check Failed</span>
            </>
          )}
        </div>
      </div>

      <div className="anchor-grid">
        {cement && (
          <div className="anchor-material-box">
            <h3 className="mat-title cement">Cement Anchor Data</h3>
            <div className="anchor-details">
              <div className="detail-row">
                <span>PWD Reference Rate (FY 25-26):</span>
                <strong>{formatINR(cement.converted_anchor_price_rs)} / MT</strong>
              </div>
              <div className="detail-row">
                <span>FY 25-26 Avg WPI Index:</span>
                <strong>{cement.fy25_26_avg_wpi?.toFixed(2)} pts</strong>
              </div>
              <div className="detail-row">
                <span>Calibrated Conversion Factor:</span>
                <strong>₹{cement.rs_per_index_point?.toFixed(2)} / index pt</strong>
              </div>
            </div>
          </div>
        )}

        {steel && (
          <div className="anchor-material-box">
            <h3 className="mat-title steel">Steel Anchor Data</h3>
            <div className="anchor-details">
              <div className="detail-row">
                <span>PWD Reference Rate (FY 25-26):</span>
                <strong>{formatINR(steel.converted_anchor_price_rs)} / MT</strong>
              </div>
              <div className="detail-row">
                <span>FY 25-26 Avg WPI Index:</span>
                <strong>{steel.fy25_26_avg_wpi?.toFixed(2)} pts</strong>
              </div>
              <div className="detail-row">
                <span>Calibrated Conversion Factor:</span>
                <strong>₹{steel.rs_per_index_point?.toFixed(2)} / index pt</strong>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
