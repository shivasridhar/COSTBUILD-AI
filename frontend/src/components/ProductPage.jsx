import React, { useState } from 'react';
import {
  Cpu,
  TrendingUp,
  ShieldCheck,
  FileSpreadsheet,
  Layers,
  BarChart3,
  CheckCircle2,
  ArrowRight,
  Database,
  Search,
  Sparkles
} from 'lucide-react';

export default function ProductPage({ onNavigateHome, onScrollToWorkbench }) {
  const [activeFeature, setActiveFeature] = useState('forecasting');

  const features = [
    {
      id: 'forecasting',
      icon: <TrendingUp size={20} />,
      title: '12-Month WPI Trend Forecasting',
      tagline: 'Extrapolating wholesale price index drift using walk-forward regression models.',
      desc: 'BuildCost AI processes historical Ministry of Commerce WPI series datasets (2012–2026) for essential building materials. By pairing macroeconomic momentum indicators with seasonal ARIMA & XGBoost baseline models, the engine projects optimal 12-month forward purchasing windows.',
      metrics: [
        { label: 'WPI Series Historical Depth', val: '144 Months' },
        { label: 'Forecast Accuracy Horizon', val: '12 Months Forward' },
        { label: 'Sanity Check Validation', val: 'Automated 1.5x Bound' }
      ]
    },
    {
      id: 'pwd-anchors',
      icon: <Database size={20} />,
      title: 'PWD Schedule of Rates Anchors',
      tagline: 'Grounded in official state & central Public Works Department reference schedules.',
      desc: 'Never purchase above official government benchmarks. BuildCost AI parses and normalizes Public Works Department (PWD) Schedule of Rates (SOR) items, converting raw departmental units (e.g. per cubic meter, 1000 nos) into standardized purchasing quantities.',
      metrics: [
        { label: 'PWD Schedule Sources', val: 'State & CPWD' },
        { label: 'Unit Normalization', val: 'MT, Cu.M, Bags, Nos.' },
        { label: 'Reference Date Baseline', val: 'Real-Time Anchor' }
      ]
    },
    {
      id: 'projects-bom',
      icon: <Layers size={20} />,
      title: 'CAD Project & Phase BOM Engine',
      tagline: 'Staged bill of materials alignment across active construction timelines.',
      desc: 'Attach dynamic procurement estimates directly to registered architectural CAD projects. Define sub-phases (Excavation, Foundation, Superstructure, Finishing) and optimize material procurement timings aligned with exact site execution schedules.',
      metrics: [
        { label: 'Supported BOM Items', val: 'Steel, Cement, Sand, Brick, Gravel, Wiring' },
        { label: 'Phase Isolation', val: 'Multi-Phase Staging' },
        { label: 'Project Persistence', val: 'SQLite CAD Registry' }
      ]
    },
    {
      id: 'pdf-reports',
      icon: <FileSpreadsheet size={20} />,
      title: 'Executive PDF Report Compiler',
      tagline: 'Publication-ready technical PDF documents generated on-demand.',
      desc: 'Export executive-level procurement audits with a single click. Compiled PDFs include high-resolution price trend charts, monthly BOM cost tables, PWD anchor conversion breakdowns, vendor quote audit trails, and model disclosures.',
      metrics: [
        { label: 'PDF Engine', val: 'WeasyPrint + ReportLab Fallback' },
        { label: 'Report Content', val: 'Executive Audit & Disclosures' },
        { label: 'Download Format', val: 'Streamed PDF Stream' }
      ]
    }
  ];

  const currentFeature = features.find((f) => f.id === activeFeature) || features[0];

  return (
    <div className="page-container product-page">
      {/* 1. Page Header Banner */}
      <div className="page-header-banner blueprint-panel">
        <span className="corner-mark top-left">+</span>
        <span className="corner-mark top-right">+</span>
        <span className="corner-mark bottom-left">+</span>
        <span className="corner-mark bottom-right">+</span>

        <div className="header-badge">
          <Cpu size={16} />
          <span>TECHNICAL ARCHITECTURE SPECIFICATION</span>
        </div>
        <h1 className="page-title">BUILDCOST AI BLUEPRINT ENGINE</h1>
        <p className="page-subtitle">
          An AI-powered construction procurement optimization platform combining government reference rates with 12-month WPI price trajectory modeling.
        </p>

        <div className="header-actions">
          <button onClick={onNavigateHome} className="btn-submit" style={{ maxWidth: '280px' }}>
            <span>LAUNCH WORKBENCH</span>
            <ArrowRight size={16} className="btn-arrow" />
          </button>
        </div>
      </div>

      {/* 2. System Architecture Flow Diagram */}
      <div className="architecture-grid-section">
        <h2 className="section-grid-title">
          <span className="orange-square-marker"></span>
          SYSTEM DATA PIPELINE ARCHITECTURE
        </h2>

        <div className="pipeline-flow-cards">
          <div className="flow-card">
            <div className="flow-step-num">01</div>
            <h3>PWD Reference Ingestion</h3>
            <p>Parses official Public Works Department (PWD) Schedule of Rates to establish baseline pricing anchors per metric unit.</p>
          </div>

          <div className="flow-card-connector">→</div>

          <div className="flow-card">
            <div className="flow-step-num">02</div>
            <h3>WPI Trajectory Model</h3>
            <p>12-Month forward price trajectory extrapolation using Ministry of Commerce Wholesale Price Index (WPI) time series.</p>
          </div>

          <div className="flow-card-connector">→</div>

          <div className="flow-card">
            <div className="flow-step-num">03</div>
            <h3>Optimal Window Engine</h3>
            <p>Calculates dynamic monthly BOM costs across target materials to identify minimum purchasing price windows.</p>
          </div>

          <div className="flow-card-connector">→</div>

          <div className="flow-card">
            <div className="flow-step-num">04</div>
            <h3>Vendor Audit & PDF Report</h3>
            <p>Checks single vendor quotes against baseline bounds and compiles downloadable executive PDF reports.</p>
          </div>
        </div>
      </div>

      {/* 3. Interactive Feature Deep Dive Grid */}
      <div className="feature-deepdive-section blueprint-panel">
        <h2 className="section-grid-title">
          <span className="orange-square-marker"></span>
          CORE PLATFORM CAPABILITIES
        </h2>

        <div className="feature-tabs-layout">
          <div className="feature-tabs-menu">
            {features.map((feat) => (
              <div
                key={feat.id}
                className={`feature-tab-item ${activeFeature === feat.id ? 'active' : ''}`}
                onClick={() => setActiveFeature(feat.id)}
              >
                <div className="tab-icon">{feat.icon}</div>
                <div className="tab-text">
                  <strong>{feat.title}</strong>
                  <span>{feat.tagline}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="feature-display-panel">
            <div className="display-header">
              <div className="display-title-group">
                {currentFeature.icon}
                <h3>{currentFeature.title}</h3>
              </div>
              <span className="feature-badge">ACTIVE SPECIFICATION</span>
            </div>

            <p className="display-desc">{currentFeature.desc}</p>

            <div className="display-metrics-grid">
              {currentFeature.metrics.map((m, idx) => (
                <div key={idx} className="metric-box">
                  <span className="metric-label">{m.label}</span>
                  <span className="metric-val">{m.val}</span>
                </div>
              ))}
            </div>

            <div className="display-cta">
              <button
                onClick={() => {
                  onNavigateHome();
                  if (onScrollToWorkbench) onScrollToWorkbench();
                }}
                className="btn-submit"
                style={{ width: 'auto', padding: '12px 24px' }}
              >
                <span>TEST IN WORKBENCH</span>
                <ArrowRight size={16} className="btn-arrow" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Model Disclosure & Accuracy Disclaimers */}
      <div className="disclosure-card blueprint-panel">
        <div className="disclosure-header">
          <ShieldCheck size={20} className="orange-icon" />
          <h3>Algorithmic Transparency & Model Disclosures</h3>
        </div>
        <p>
          BuildCost AI provides automated cost trend forecasts derived from PWD reference rates and WPI macroeconomic index extrapolation models. Forecasts are intended to assist structural procurement planning and should be validated against current local supplier quotes prior to purchase contract execution.
        </p>
      </div>
    </div>
  );
}
