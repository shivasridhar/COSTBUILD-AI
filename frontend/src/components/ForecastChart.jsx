import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp } from 'lucide-react';

export default function ForecastChart({ forecastData }) {
  if (!forecastData || forecastData.length === 0) return null;

  const formatINR = (value) => `₹${Number(value).toLocaleString('en-IN')}`;

  return (
    <div className="card chart-card">
      <div className="card-header">
        <TrendingUp className="header-icon" size={22} />
        <div>
          <h2>12-Month Dynamic Material Price Trajectory (₹/MT)</h2>
          <p className="subtitle">
            WPI Index Drift Extrapolation for Key Structural Inputs (Cement & Steel)
          </p>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={forecastData} margin={{ top: 10, right: 30, left: 20, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="year_month"
              tick={{ fontSize: 12, fill: '#64748b' }}
              angle={-25}
              textAnchor="end"
            />
            <YAxis
              yAxisId="left"
              orientation="left"
              stroke="#0ea5e9"
              tick={{ fontSize: 12, fill: '#0ea5e9' }}
              tickFormatter={(v) => `₹${v}`}
              domain={['dataMin - 100', 'dataMax + 100']}
              label={{ value: 'Cement (₹/MT)', angle: -90, position: 'insideLeft', style: { fill: '#0ea5e9', fontSize: 12 } }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#6366f1"
              tick={{ fontSize: 12, fill: '#6366f1' }}
              tickFormatter={(v) => `₹${Math.round(v / 1000)}k`}
              domain={['dataMin - 500', 'dataMax + 500']}
              label={{ value: 'Steel (₹/MT)', angle: 90, position: 'insideRight', style: { fill: '#6366f1', fontSize: 12 } }}
            />
            <Tooltip
              formatter={(value, name) => [
                formatINR(value),
                name === 'cement_price_rs_per_MT' ? 'Cement (₹/MT)' : 'Steel (₹/MT)',
              ]}
              labelFormatter={(label) => `Forecast Month: ${label}`}
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '13px',
              }}
            />
            <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '15px' }} />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="cement_price_rs_per_MT"
              name="Cement Price (₹/MT)"
              stroke="#0ea5e9"
              strokeWidth={3}
              dot={{ r: 4, fill: '#0ea5e9' }}
              activeDot={{ r: 7 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="steel_price_rs_per_MT"
              name="Steel Price (₹/MT)"
              stroke="#6366f1"
              strokeWidth={3}
              dot={{ r: 4, fill: '#6366f1' }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
