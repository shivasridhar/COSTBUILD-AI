import React from 'react';
import { Table, Layers } from 'lucide-react';

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
    <div className="card table-card">
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
              <th>Month</th>
              <th>Year-Month</th>
              <th>Cement (₹)</th>
              <th>Steel (₹)</th>
              <th>Sand (₹)</th>
              <th>Bricks (₹)</th>
              <th>Gravel (₹)</th>
              <th>Total BOM Cost (₹)</th>
            </tr>
          </thead>
          <tbody>
            {bomData.map((row) => {
              const isRecommended = row.year_month === recommendedMonth;
              return (
                <tr key={row.month_idx} className={isRecommended ? 'row-recommended' : ''}>
                  <td className="font-medium">Month {row.month_idx}</td>
                  <td>
                    <span className="ym-badge">
                      {row.year_month}
                      {isRecommended && <span className="rec-tag">Optimal</span>}
                    </span>
                  </td>
                  <td>{row.cement_cost_rs ? formatINR(row.cement_cost_rs) : '-'}</td>
                  <td>{row.steel_cost_rs ? formatINR(row.steel_cost_rs) : '-'}</td>
                  <td>{row.sand_cost_rs ? formatINR(row.sand_cost_rs) : '-'}</td>
                  <td>{row.bricks_cost_rs ? formatINR(row.bricks_cost_rs) : '-'}</td>
                  <td>{row.gravel_cost_rs ? formatINR(row.gravel_cost_rs) : '-'}</td>
                  <td className="total-cell font-semibold">{formatINR(row.total_bom_cost_rs)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
