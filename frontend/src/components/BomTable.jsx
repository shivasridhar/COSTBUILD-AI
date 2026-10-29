import React from 'react';
import { Table } from 'lucide-react';

export default function BomTable({ bomData, recommendedMonth }) {
  if (!bomData || bomData.length === 0) return null;

  const formatINR = (val) => {
    if (val === undefined || val === null) return '-';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  return (
    <div className="card table-card blueprint-panel">
      <span className="corner-mark top-left">+</span>
      <span className="corner-mark top-right">+</span>
      <span className="corner-mark bottom-left">+</span>
      <span className="corner-mark bottom-right">+</span>

      <div className="card-header">
        <Table className="header-icon" size={22} />
        <div>
          <h2>12-Month Bill of Materials (BOM) Cost Forecast</h2>
          <p className="subtitle">Monthly component breakdown and total BOM expenditure over the 1-year horizon</p>
        </div>
      </div>

      <div className="table-responsive">
        <table className="bom-table">
          <thead>
            <tr>
              <th>HORIZON</th>
              <th>YEAR-MONTH</th>
              <th>CEMENT (₹)</th>
              <th>STEEL (₹)</th>
              <th>WIRING (₹)</th>
              <th>SAND (₹)</th>
              <th>BRICKS (₹)</th>
              <th>GRAVEL (₹)</th>
              <th>TOTAL BOM COST (₹)</th>
            </tr>
          </thead>
          <tbody>
            {bomData.map((row) => {
              const isRecommended = row.year_month === recommendedMonth;
              return (
                <tr key={row.month_idx} className={isRecommended ? 'row-recommended' : ''}>
                  <td className="font-medium mono-readout">Month {row.month_idx}</td>
                  <td>
                    <span className="ym-badge mono-readout">
                      {row.year_month}
                      {isRecommended && <span className="rec-tag">OPTIMAL</span>}
                    </span>
                  </td>
                  <td className="mono-readout">{row.cement_cost_rs ? formatINR(row.cement_cost_rs) : '-'}</td>
                  <td className="mono-readout">{row.steel_cost_rs ? formatINR(row.steel_cost_rs) : '-'}</td>
                  <td className="mono-readout">{row.wiring_cost_rs ? formatINR(row.wiring_cost_rs) : '-'}</td>
                  <td className="mono-readout">{row.sand_cost_rs ? formatINR(row.sand_cost_rs) : '-'}</td>
                  <td className="mono-readout">{row.bricks_cost_rs ? formatINR(row.bricks_cost_rs) : '-'}</td>
                  <td className="mono-readout">{row.gravel_cost_rs ? formatINR(row.gravel_cost_rs) : '-'}</td>
                  <td className="total-cell mono-readout">{formatINR(row.total_bom_cost_rs)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
