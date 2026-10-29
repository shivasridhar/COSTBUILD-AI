import React, { useState, useEffect } from 'react';
import { checkFairPrice, getPhases } from '../api/client';
import {
  Tag,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Info,
  Calendar,
  DollarSign,
  Loader2,
  AlertCircle,
  ArrowRight
} from 'lucide-react';

const MATERIAL_OPTIONS = [
  { id: 'steel', label: 'Steel', defaultUnit: 'MT' },
  { id: 'cement', label: 'Cement', defaultUnit: 'MT' },
  { id: 'wiring', label: 'Wiring (Electrical)', defaultUnit: 'Rmt' },
  { id: 'sand', label: 'Sand', defaultUnit: 'cum' },
  { id: 'brick', label: 'Bricks', defaultUnit: '1000 Nos.' },
  { id: 'gravel', label: 'Gravel', defaultUnit: 'cum' },
];

export default function VendorQuoteCard({ onQuoteChecked, activeProjectId, activeProjectName }) {
  const [material, setMaterial] = useState('steel');
  const [quotedRate, setQuotedRate] = useState('59000');
  const [quotedUnit, setQuotedUnit] = useState('MT');
  const [quotedDate, setQuotedDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  });
  const [sourceNote, setSourceNote] = useState('');
  
  const [phases, setPhases] = useState([]);
  const [selectedPhaseId, setSelectedPhaseId] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (activeProjectId) {
      getPhases(activeProjectId)
        .then((data) => setPhases(data || []))
        .catch(() => setPhases([]));
    } else {
      setPhases([]);
      setSelectedPhaseId('');
    }
  }, [activeProjectId]);

  const handleMaterialChange = (e) => {
    const selectedMat = e.target.value;
    setMaterial(selectedMat);
    const found = MATERIAL_OPTIONS.find((m) => m.id === selectedMat);
    if (found) {
      setQuotedUnit(found.defaultUnit);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    const rateNum = parseFloat(quotedRate);
    if (isNaN(rateNum) || rateNum <= 0) {
      setError('Please enter a valid positive quoted rate.');
      return;
    }

    if (!quotedUnit.trim()) {
      setError('Please specify the quoted unit of measurement.');
      return;
    }

    if (!quotedDate.trim()) {
      setError('Please select or enter a valid quote date.');
      return;
    }

    setLoading(true);

    try {
      const res = await checkFairPrice({
        material,
        quoted_rate: rateNum,
        quoted_unit: quotedUnit.trim(),
        quoted_date: quotedDate.trim(),
        source_note: sourceNote.trim() || undefined,
        project_id: activeProjectId || undefined,
        phase_id: selectedPhaseId ? parseInt(selectedPhaseId, 10) : undefined
      });
      setResult(res);
      if (res.quote_id && onQuoteChecked) {
        onQuoteChecked(res.quote_id);
      }
    } catch (err) {
      setError(err.message || 'Failed to check fair price.');
    } finally {
      setLoading(false);
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

  const getVerdictStyle = (verdict) => {
    switch (verdict) {
      case 'at market':
        return {
          bgClass: 'verdict-at-market',
          badgeText: 'AT MARKET PRICE',
          icon: <CheckCircle2 size={16} />,
        };
      case 'below market':
        return {
          bgClass: 'verdict-below-market',
          badgeText: 'BELOW MARKET PRICE',
          icon: <TrendingDown size={16} />,
        };
      case 'above market':
        return {
          bgClass: 'verdict-above-market',
          badgeText: 'ABOVE MARKET PRICE',
          icon: <TrendingUp size={16} />,
        };
      case 'unit mismatch':
        return {
          bgClass: 'verdict-unit-mismatch',
          badgeText: 'UNIT MISMATCH WARNING',
          icon: <AlertTriangle size={16} />,
        };
      case 'date out of range':
        return {
          bgClass: 'verdict-range-warning',
          badgeText: 'DATE OUT OF RANGE',
          icon: <Info size={16} />,
        };
      default:
        return {
          bgClass: 'verdict-neutral',
          badgeText: String(verdict).toUpperCase(),
          icon: <Info size={16} />,
        };
    }
  };

  return (
    <div className="card vendor-quote-card blueprint-panel">
      <span className="corner-mark top-left">+</span>
      <span className="corner-mark top-right">+</span>
      <span className="corner-mark bottom-left">+</span>
      <span className="corner-mark bottom-right">+</span>

      <div className="card-header" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Tag className="header-icon" size={22} />
          <div>
            <h2 className="card-title">Single Vendor Quote Fair Price Check</h2>
            <p className="card-subtitle">
              Validate a vendor quote against official PWD rates & 12-month WPI market baseline trajectories.
            </p>
          </div>
        </div>
        {activeProjectId && (
          <div className="project-quote-badge">
            <span className="project-quote-dot"></span>
            Attaching quote to <strong>{activeProjectName || `Project #${activeProjectId}`}</strong>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="vendor-form">
        <div className="form-row-grid">
          {/* Material Selector */}
          <div className="form-group">
            <label htmlFor="quote-material" className="form-label">Material</label>
            <select
              id="quote-material"
              value={material}
              onChange={handleMaterialChange}
              className="form-control"
              disabled={loading}
            >
              {MATERIAL_OPTIONS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label} ({m.defaultUnit})
                </option>
              ))}
            </select>
          </div>

          {/* Quoted Rate */}
          <div className="form-group">
            <label htmlFor="quote-rate" className="form-label">Quoted Rate (₹)</label>
            <input
              id="quote-rate"
              type="number"
              step="any"
              min="0.01"
              value={quotedRate}
              onChange={(e) => setQuotedRate(e.target.value)}
              placeholder="e.g. 59000"
              className="form-control"
              disabled={loading}
              required
            />
          </div>

          {/* Quoted Unit */}
          <div className="form-group">
            <label htmlFor="quote-unit" className="form-label">Quoted Unit</label>
            <input
              id="quote-unit"
              type="text"
              value={quotedUnit}
              onChange={(e) => setQuotedUnit(e.target.value)}
              placeholder="e.g. MT, Rmt, cum, 1000 Nos."
              className="form-control"
              disabled={loading}
              required
            />
          </div>

          {/* Quote Date */}
          <div className="form-group">
            <label htmlFor="quote-date" className="form-label">Quote Date</label>
            <input
              id="quote-date"
              type="date"
              value={quotedDate}
              onChange={(e) => setQuotedDate(e.target.value)}
              className="form-control"
              disabled={loading}
              required
            />
          </div>
        </div>

        {/* Optional Source Note & Construction Phase Selection */}
        <div className="form-row-grid" style={{ marginTop: '12px' }}>
          {phases.length > 0 && (
            <div className="form-group">
              <label htmlFor="quote-phase" className="form-label">Construction Phase (Optional)</label>
              <select
                id="quote-phase"
                value={selectedPhaseId}
                onChange={(e) => setSelectedPhaseId(e.target.value)}
                className="form-control"
                disabled={loading}
              >
                <option value="">-- Whole Project (Unassigned) --</option>
                {phases.map((p) => (
                  <option key={p.id} value={p.id}>
                    Phase #{p.sequence_order}: {p.phase_name} (Starts Month {p.expected_start_month})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="quote-source" className="form-label">Vendor / Reference Note (Optional)</label>
            <input
              id="quote-source"
              type="text"
              value={sourceNote}
              onChange={(e) => setSourceNote(e.target.value)}
              placeholder="e.g. Vendor Name, Invoice #, Tender Ref."
              className="form-control"
              disabled={loading}
            />
          </div>
        </div>

        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="spinner" size={18} />
              <span>Evaluating Quote...</span>
            </>
          ) : (
            <>
              <span>CHECK FAIR PRICE</span>
              <ArrowRight size={16} className="btn-arrow" />
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="error-banner">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Single Quote Result Card */}
      {result && (
        <div className="quote-result-card">
          <div className="quote-result-header">
            <div className={`badge-verdict ${getVerdictStyle(result.verdict).bgClass}`}>
              {getVerdictStyle(result.verdict).icon}
              <span>{getVerdictStyle(result.verdict).badgeText}</span>
            </div>
            <span className="quote-date-pill">QUOTE DATE: {quotedDate}</span>
          </div>

          <div className="quote-metrics-grid">
            {/* Quoted Rate Metric */}
            <div className="quote-metric-item">
              <div className="metric-label">QUOTED VENDOR RATE</div>
              <div className="metric-value mono-readout">
                {formatINR(parseFloat(quotedRate))} / {quotedUnit}
              </div>
              <div className="metric-subtext">Submitted Quote Value</div>
            </div>

            {/* Baseline Rate Metric */}
            <div className="quote-metric-item">
              <div className="metric-label">MARKET BASELINE RATE</div>
              <div className="metric-value highlight mono-readout">
                {formatINR(result.baseline_rate)} / {result.baseline_unit}
              </div>
              <div className="metric-subtext">PWD Anchor + Drift Forecast</div>
            </div>

            {/* Deviation Metric */}
            <div className="quote-metric-item">
              <div className="metric-label">RATE DEVIATION</div>
              <div className="metric-value mono-readout">
                {result.verdict === 'unit mismatch' || result.verdict === 'date out of range' ? (
                  <span className="neutral-text">N/A</span>
                ) : (
                  <span className={result.deviation_pct > 0 ? 'above-text' : 'below-text'}>
                    {result.deviation_pct > 0 ? '+' : ''}
                    {result.deviation_pct.toFixed(2)}%
                  </span>
                )}
              </div>
              <div className="metric-subtext">
                {result.verdict === 'unit mismatch' || result.verdict === 'date out of range'
                  ? 'Non-comparable'
                  : 'Compared to baseline'}
              </div>
            </div>
          </div>

          {/* Explanatory Note Box (Dark Coordinate Readout Style) */}
          <div className="verdict-note-box">
            <Info size={18} className="note-icon" />
            <div className="note-content">
              <strong style={{ color: 'var(--accent-orange-soft)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>VERDICT READOUT DETAIL:</strong>
              <p style={{ marginTop: '4px' }}>{result.note}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
