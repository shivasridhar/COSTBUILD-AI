import React, { useState, useEffect, useRef } from 'react';
import {
  ComposedChart,
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, Layers, Sliders, ShieldCheck } from 'lucide-react';

/**
 * MaterialPanel Sub-Component
 * Handles per-panel IntersectionObserver scroll-triggering, reduced motion preferences,
 * and isolated load-in entrance animation sequencing.
 */
function MaterialPanel({
  mat,
  processedData,
  domain,
  yTickFormatter,
  recommendedYearMonth,
  recommendedMonthIdx,
  recRow,
  mapeVal,
  sampleCount,
  markerCalloutLabel,
  formatINR,
}) {
  const panelRef = useRef(null);
  const [inView, setInView] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  // Check prefers-reduced-motion accessibility setting
  useEffect(() => {
    const checkMotion = () => {
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
      setPrefersReducedMotion(mq.matches);
    };

    checkMotion();
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mq.addEventListener) {
      mq.addEventListener('change', checkMotion);
      return () => mq.removeEventListener('change', checkMotion);
    }
  }, []);

  // IntersectionObserver: trigger animation ONCE when scrolled into view
  useEffect(() => {
    if (prefersReducedMotion) {
      setInView(true);
      return;
    }

    const node = panelRef.current;
    if (!node) return;

    // Reset view state if dataset changed
    setInView(false);

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.unobserve(node);
        }
      },
      { threshold: 0.12 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [processedData, prefersReducedMotion]);

  // Custom Architectural Point Dot Renderer with staggered entrance delay
  const renderArchitecturalDot = (props) => {
    const { cx, cy, payload, index } = props;
    if (!cx || !cy) return null;

    const isRecommended =
      payload.year_month === recommendedYearMonth ||
      payload.month_idx === recommendedMonthIdx;

    const totalPoints = processedData.length || 12;
    const staggerDelayMs = Math.round((index / totalPoints) * 1400);

    if (isRecommended) {
      return (
        <g key={`rec_dot_${payload.month_idx}_${mat.key}`}>
          {/* Pulsing Accent Glow / Background Ring */}
          <rect
            x={cx - 7}
            y={cy - 7}
            width={14}
            height={14}
            fill="#fa3600"
            fillOpacity={0.25}
            stroke="#fa3600"
            strokeWidth={1}
            rx={1}
            className="rec-dimension-callout"
          />
          {/* Solid Blueprint Orange Square Marker */}
          <rect
            x={cx - 5}
            y={cy - 5}
            width={10}
            height={10}
            fill="#fa3600"
            stroke="#111111"
            strokeWidth={1.5}
            rx={1}
            className="rec-dimension-callout"
          />
        </g>
      );
    }

    // Standard receding month marker: small outline circle
    return (
      <circle
        key={`dot_${payload.month_idx}_${mat.key}`}
        cx={cx}
        cy={cy}
        r={3.5}
        fill="#f7f7f2"
        stroke={mat.color}
        strokeWidth={1.5}
        className="arch-point-dot"
        style={{ '--delay': `${staggerDelayMs}ms` }}
      />
    );
  };

  // Direct Line-End Label Renderer
  const renderLineEndLabel = (props) => {
    const { index, x, y } = props;
    if (index !== processedData.length - 1 || !x || !y) return null;

    return (
      <g transform={`translate(${x + 8}, ${y + 4})`} className="arch-point-dot" style={{ '--delay': '1450ms' }}>
        <rect
          x={0}
          y={-14}
          width={mat.shortName.length * 8 + 36}
          height={18}
          fill="#111111"
          rx={2}
        />
        <text
          x={6}
          y={-2}
          fill="#f7f7f2"
          fontSize={10}
          fontFamily="'JetBrains Mono', monospace"
          fontWeight="bold"
        >
          {mat.shortName} ({mat.unit})
        </text>
      </g>
    );
  };

  return (
    <div
      ref={panelRef}
      key={mat.key}
      className={`material-chart-panel ${inView || prefersReducedMotion ? 'is-animated' : ''}`}
      style={{
        border: '1px solid #d1d1cc',
        backgroundColor: '#f7f7f2',
        padding: '16px 16px 8px 16px',
        borderRadius: '2px',
        position: 'relative',
      }}
    >
      {/* Panel Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '10px', height: '10px', backgroundColor: mat.color, display: 'inline-block' }}></span>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, margin: 0, fontFamily: "'JetBrains Mono', monospace", textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            {mat.name} <span style={{ color: '#5e5e5c', fontWeight: 400 }}>({mat.unit})</span>
          </h3>
        </div>

        {recRow && mapeVal !== undefined && mapeVal !== null && (
          <div style={{ fontSize: '0.72rem', fontFamily: "'JetBrains Mono', monospace", color: '#5e5e5c', backgroundColor: '#e8e8e0', padding: '3px 8px', border: '1px solid #d1d1cc' }}>
            M{recommendedMonthIdx} HORIZON ACCURACY:{' '}
            <strong style={{ color: '#111111' }}>
              ±{mapeVal}% (N={sampleCount ?? '30+'})
            </strong>
          </div>
        )}
      </div>

      {/* Chart Frame */}
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart
          data={processedData}
          margin={{ top: 25, right: 110, left: 20, bottom: 20 }}
        >
          {/* SVG Gradient Definition */}
          <defs>
            <linearGradient id={`confidence_grad_${mat.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#fa3600" stopOpacity={0.04} />
              <stop offset="50%" stopColor="#fa3600" stopOpacity={0.32} />
              <stop offset="100%" stopColor="#fa3600" stopOpacity={0.04} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="4 4" stroke="#d1d1cc" vertical={false} />

          <XAxis
            dataKey="year_month"
            tick={{ fontSize: 10, fill: '#5e5e5c', fontFamily: "'JetBrains Mono', monospace" }}
            axisLine={{ stroke: '#b3b3af' }}
            tickLine={{ stroke: '#b3b3af' }}
          />

          <YAxis
            domain={domain}
            tick={{ fontSize: 10, fill: '#5e5e5c', fontFamily: "'JetBrains Mono', monospace" }}
            tickFormatter={yTickFormatter}
            axisLine={{ stroke: '#b3b3af' }}
            tickLine={{ stroke: '#b3b3af' }}
            width={65}
          />

          {/* Dark Coordinate Tooltip */}
          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                const priceVal = data[mat.priceKey];
                const lowVal = data[mat.lowKey];
                const highVal = data[mat.highKey];
                const mape = data[mat.mapeKey];
                const samples = data[mat.countKey];

                return (
                  <div className="dark-coordinate-tooltip">
                    <div className="tooltip-header">
                      COORDINATE READOUT: {label} (M+{data.month_idx})
                    </div>
                    <div className="tooltip-row">
                      <span className="tooltip-label">{mat.shortName} BASELINE:</span>
                      <span className="tooltip-val">{formatINR(priceVal)}/{mat.unit.replace('₹/', '')}</span>
                    </div>
                    {lowVal && highVal && (
                      <div className="tooltip-row">
                        <span className="tooltip-label">ACCURACY BAND (±{mape}%):</span>
                        <span className="tooltip-val accent">
                          {formatINR(lowVal)} – {formatINR(highVal)}
                        </span>
                      </div>
                    )}
                    {samples && (
                      <div className="tooltip-row">
                        <span className="tooltip-label">BACKTEST SAMPLES:</span>
                        <span className="tooltip-val">N={samples}</span>
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />

          {/* Gradient Shaded Walk-Forward Confidence Band */}
          <Area
            type="monotone"
            dataKey={`${mat.key}_band`}
            name={`${mat.shortName} Accuracy Band`}
            stroke="none"
            fill={`url(#confidence_grad_${mat.key})`}
            className="confidence-band-area"
            isAnimationActive={false}
          />

          {/* Fused Architectural Vertical Dimension Line for Recommended Month */}
          {recommendedYearMonth && (
            <ReferenceLine
              x={recommendedYearMonth}
              stroke="#fa3600"
              strokeDasharray="3 3"
              strokeWidth={1.5}
              className="rec-dimension-callout"
              label={{
                value: markerCalloutLabel,
                position: 'top',
                fill: '#fa3600',
                fontSize: 10,
                fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 'bold',
              }}
            />
          )}

          {/* Primary Forecast Trajectory Line */}
          <Line
            type="monotone"
            dataKey={mat.priceKey}
            name={`${mat.name}`}
            stroke={mat.color}
            strokeWidth={2.5}
            className="forecast-line-path"
            isAnimationActive={false}
            dot={renderArchitecturalDot}
            activeDot={{ r: 6, fill: '#fa3600', stroke: '#111111', strokeWidth: 1.5 }}
            label={renderLineEndLabel}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Rebuilt ForecastChart Component for BuildCost AI
 * Blueprint-themed multi-panel chart system for material price trajectories.
 */
export default function ForecastChart({ forecastData, recommendation }) {
  const [viewMode, setViewMode] = useState('split'); // 'split' (small multiples) | 'compare' (normalized % drift)

  if (!forecastData || forecastData.length === 0) return null;

  // Identify recommended procurement month
  const recommendedYearMonth = recommendation?.recommended_year_month;
  const recommendedMonthIdx = recommendation?.recommended_month_idx ?? 1;

  // Currency formatters
  const formatINR = (value) => `₹${Number(value).toLocaleString('en-IN')}`;

  // Smart dynamic Y-axis tick formatter ensuring no duplicate labels on narrow ranges
  const createYAxisFormatter = (domainMin, domainMax, unit) => {
    const range = domainMax - domainMin;
    return (val) => {
      if (unit === '₹/m') return `₹${val.toFixed(1)}`;
      if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
      if (range <= 2500) {
        return `₹${Math.round(val).toLocaleString('en-IN')}`;
      }
      if (range <= 10000) {
        return `₹${(val / 1000).toFixed(1)}k`;
      }
      return `₹${Math.round(val / 1000)}k`;
    };
  };

  // Material Definitions & Meta
  const MATERIAL_CONFIGS = [
    {
      key: 'steel',
      name: 'Structural Steel / TMT Bars',
      shortName: 'STEEL',
      unit: '₹/MT',
      color: '#111111',
      priceKey: 'steel_price_rs_per_MT',
      lowKey: 'steel_confidence_low_rs',
      highKey: 'steel_confidence_high_rs',
      mapeKey: 'steel_mape_pct',
      countKey: 'steel_sample_count',
    },
    {
      key: 'cement',
      name: 'Portland Cement (OPC/PPC)',
      shortName: 'CEMENT',
      unit: '₹/MT',
      color: '#fa3600',
      priceKey: 'cement_price_rs_per_MT',
      lowKey: 'cement_confidence_low_rs',
      highKey: 'cement_confidence_high_rs',
      mapeKey: 'cement_mape_pct',
      countKey: 'cement_sample_count',
    },
    {
      key: 'wiring',
      name: 'Copper Wires & Cable Conduit',
      shortName: 'WIRING',
      unit: '₹/m',
      color: '#4a4a48',
      priceKey: 'wiring_price_rs_per_m',
      lowKey: 'wiring_confidence_low_rs',
      highKey: 'wiring_confidence_high_rs',
      mapeKey: 'wiring_mape_pct',
      countKey: 'wiring_sample_count',
    },
  ];

  // Filter materials actually present in the payload
  const activeMaterials = MATERIAL_CONFIGS.filter((mat) =>
    forecastData.some((row) => row[mat.priceKey] !== undefined && row[mat.priceKey] !== null)
  );

  // Prepare Data for Recharts
  const processedData = forecastData.map((row) => {
    const item = { ...row };
    activeMaterials.forEach((mat) => {
      const price = row[mat.priceKey];
      const low = row[mat.lowKey] ?? price;
      const high = row[mat.highKey] ?? price;
      if (price !== undefined && price !== null) {
        item[`${mat.key}_band`] = [low, high];
        item[`${mat.key}_band_width`] = high - low;
      }
    });

    // Calculate normalized % drift from Month 1 baseline for comparison mode
    if (forecastData.length > 0) {
      const m1 = forecastData[0];
      activeMaterials.forEach((mat) => {
        const basePrice = m1[mat.priceKey];
        const currentPrice = row[mat.priceKey];
        if (basePrice && currentPrice) {
          item[`${mat.key}_pct_change`] = Number((((currentPrice - basePrice) / basePrice) * 100).toFixed(2));
        }
      });
    }

    return item;
  });

  // Calculate explicit, clamped Y-domain per material (never below 0)
  const getClampedDomain = (matKey, lowKey, highKey, priceKey) => {
    const values = [];
    processedData.forEach((row) => {
      if (row[priceKey] !== undefined && row[priceKey] !== null) values.push(row[priceKey]);
      if (row[lowKey] !== undefined && row[lowKey] !== null) values.push(row[lowKey]);
      if (row[highKey] !== undefined && row[highKey] !== null) values.push(row[highKey]);
    });

    if (values.length === 0) return [0, 100];
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const padding = (maxVal - minVal) * 0.12 || minVal * 0.05 || 10;

    const domainMin = Math.max(0, Math.floor(minVal - padding));
    const domainMax = Math.ceil(maxVal + padding);
    return [domainMin, domainMax];
  };

  return (
    <div className="card chart-card blueprint-panel" style={{ marginBottom: '24px' }}>
      {/* CAD Corner Crosshairs */}
      <span className="corner-mark top-left">+</span>
      <span className="corner-mark top-right">+</span>
      <span className="corner-mark bottom-left">+</span>
      <span className="corner-mark bottom-right">+</span>

      {/* Blueprint Header */}
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <TrendingUp className="header-icon" size={22} color="#fa3600" />
          <div>
            <h2>12-Month Dynamic Material Price Trajectory & Accuracy Intervals</h2>
            <p className="subtitle">
              Single-material forecast panels with walk-forward backtest confidence bands (±MAPE %) & recommendation markers.
            </p>
          </div>
        </div>

        {/* View Mode Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            className={`btn-mode-toggle ${viewMode === 'split' ? 'active' : ''}`}
            onClick={() => setViewMode('split')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              fontSize: '0.75rem',
              fontFamily: "'JetBrains Mono', monospace",
              fontWeight: 600,
              textTransform: 'uppercase',
              border: viewMode === 'split' ? '1.5px solid #111111' : '1px solid #b3b3af',
              backgroundColor: viewMode === 'split' ? '#111111' : '#f7f7f2',
              color: viewMode === 'split' ? '#f7f7f2' : '#5e5e5c',
              cursor: 'pointer',
              borderRadius: '2px',
              transition: 'all 0.15s ease',
            }}
          >
            <Layers size={13} />
            <span>Stacked Panels</span>
          </button>
          <button
            type="button"
            className={`btn-mode-toggle ${viewMode === 'compare' ? 'active' : ''}`}
            onClick={() => setViewMode('compare')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              fontSize: '0.75rem',
              fontFamily: "'JetBrains Mono', monospace",
              fontWeight: 600,
              textTransform: 'uppercase',
              border: viewMode === 'compare' ? '1.5px solid #111111' : '1px solid #b3b3af',
              backgroundColor: viewMode === 'compare' ? '#111111' : '#f7f7f2',
              color: viewMode === 'compare' ? '#f7f7f2' : '#5e5e5c',
              cursor: 'pointer',
              borderRadius: '2px',
              transition: 'all 0.15s ease',
            }}
          >
            <Sliders size={13} />
            <span>Compare % Drift</span>
          </button>
        </div>
      </div>

      {/* Recommended Month Monospace Context Legend */}
      <div
        style={{
          margin: '0 24px 16px 24px',
          padding: '10px 14px',
          backgroundColor: '#f0f0e8',
          border: '1px solid #d1d1cc',
          borderLeft: '4px solid #fa3600',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          gap: '12px',
          flexWrap: 'wrap',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '0.78rem',
          color: '#111111',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="orange-square-marker large"></span>
          <span>
            <strong>RECOMMENDED PROCUREMENT WINDOW:</strong>{' '}
            <span style={{ color: '#fa3600', fontWeight: 700 }}>
              M{recommendedMonthIdx} ({recommendedYearMonth || 'Phase Optimal'})
            </span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', color: '#5e5e5c' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ display: 'inline-block', width: '20px', height: '10px', background: 'linear-gradient(to right, rgba(250,54,0,0.05), rgba(250,54,0,0.32), rgba(250,54,0,0.05))', border: '1px solid #fa3600' }}></span>
            <span>Mechanical Pen-Trace Entrance & Center Density Fade</span>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={14} color="#fa3600" />
            <span>Dynamic Non-Overlapping Price Axes</span>
          </span>
        </div>
      </div>

      {/* MAIN VIEW: SPLIT SMALL MULTIPLES PANELS */}
      {viewMode === 'split' ? (
        <div className="small-multiples-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '0 24px 24px 24px' }}>
          {activeMaterials.map((mat) => {
            const domain = getClampedDomain(mat.key, mat.lowKey, mat.highKey, mat.priceKey);
            const yTickFormatter = createYAxisFormatter(domain[0], domain[1], mat.unit);

            const recRow = processedData.find(
              (r) => r.year_month === recommendedYearMonth || r.month_idx === recommendedMonthIdx
            );

            const mapeVal = recRow ? recRow[mat.mapeKey] : null;
            const sampleCount = recRow ? recRow[mat.countKey] : null;

            const markerCalloutLabel = `RECOMMENDED — M${recommendedMonthIdx}${
              mapeVal !== null && mapeVal !== undefined
                ? ` · ±${mapeVal}% (N=${sampleCount ?? 30})`
                : ''
            }`;

            return (
              <MaterialPanel
                key={mat.key}
                mat={mat}
                processedData={processedData}
                domain={domain}
                yTickFormatter={yTickFormatter}
                recommendedYearMonth={recommendedYearMonth}
                recommendedMonthIdx={recommendedMonthIdx}
                recRow={recRow}
                mapeVal={mapeVal}
                sampleCount={sampleCount}
                markerCalloutLabel={markerCalloutLabel}
                formatINR={formatINR}
              />
            );
          })}
        </div>
      ) : (
        /* SECONDARY VIEW: NORMALIZED % DRIFT COMPARISON CHART */
        <div style={{ padding: '0 24px 24px 24px' }}>
          <div
            style={{
              border: '1px solid #d1d1cc',
              backgroundColor: '#f7f7f2',
              padding: '16px',
              borderRadius: '2px',
            }}
          >
            <div style={{ marginBottom: '12px' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 700, margin: 0, fontFamily: "'JetBrains Mono', monospace", textTransform: 'uppercase' }}>
                Normalized Material Price % Change Trajectory (Baseline = Month 1: 0.0%)
              </h3>
              <p style={{ fontSize: '0.78rem', color: '#5e5e5c', margin: '4px 0 0 0' }}>
                Comparing dynamic inflation rates across steel, cement, and wiring on a single percentage scale.
              </p>
            </div>

            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={processedData} margin={{ top: 25, right: 110, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="4 4" stroke="#d1d1cc" vertical={false} />
                <XAxis dataKey="year_month" tick={{ fontSize: 10, fill: '#5e5e5c', fontFamily: "'JetBrains Mono', monospace" }} />
                <YAxis
                  tick={{ fontSize: 10, fill: '#5e5e5c', fontFamily: "'JetBrains Mono', monospace" }}
                  tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}%`}
                  width={50}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="dark-coordinate-tooltip">
                          <div className="tooltip-header">DRIFT COMPARISON: {label}</div>
                          {payload.map((entry) => (
                            <div key={entry.name} className="tooltip-row">
                              <span className="tooltip-label" style={{ color: entry.color }}>
                                {entry.name}:
                              </span>
                              <span className="tooltip-val">
                                {entry.value > 0 ? '+' : ''}
                                {entry.value}%
                              </span>
                            </div>
                          ))}
                        </div>
                      );
                    }
                    return null;
                  }}
                />

                {recommendedYearMonth && (
                  <ReferenceLine
                    x={recommendedYearMonth}
                    stroke="#fa3600"
                    strokeDasharray="3 3"
                    strokeWidth={1.5}
                    label={{
                      value: `REC M${recommendedMonthIdx}`,
                      position: 'top',
                      fill: '#fa3600',
                      fontSize: 10,
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  />
                )}

                {activeMaterials.map((mat) => (
                  <Line
                    key={mat.key}
                    type="monotone"
                    dataKey={`${mat.key}_pct_change`}
                    name={mat.shortName}
                    stroke={mat.color}
                    strokeWidth={2.5}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
