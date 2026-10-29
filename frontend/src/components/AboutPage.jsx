import React from 'react';
import {
  Info,
  ShieldAlert,
  Server,
  Code2,
  HardHat,
  CheckCircle2,
  ArrowRight,
  Database,
  Cpu
} from 'lucide-react';

export default function AboutPage({ onNavigateHome, onScrollToWorkbench }) {
  return (
    <div className="page-container about-page">
      {/* Header Banner */}
      <div className="page-header-banner blueprint-panel">
        <span className="corner-mark top-left">+</span>
        <span className="corner-mark top-right">+</span>
        <span className="corner-mark bottom-left">+</span>
        <span className="corner-mark bottom-right">+</span>

        <div className="header-badge">
          <Info size={16} />
          <span>ABOUT BUILDCOST AI</span>
        </div>
        <h1 className="page-title">CONSTRUCTION PROCUREMENT OPTIMIZATION ENGINE</h1>
        <p className="page-subtitle">
          Engineered to bridge the gap between Public Works Department reference anchors and 12-month forward macroeconomic Wholesale Price Index trajectories.
        </p>

        <div className="header-actions">
          <button onClick={onNavigateHome} className="btn-submit" style={{ maxWidth: '280px' }}>
            <span>OPTIMIZE NOW</span>
            <ArrowRight size={16} className="btn-arrow" />
          </button>
        </div>
      </div>

      {/* Standalone Uncarded Hero Image */}
      <div className="about-image-wrapper">
        <img
          src="/about_engineers.jpg"
          alt="Construction Engineers analyzing architectural CAD blueprints on site"
          className="about-standalone-image"
        />
      </div>

      {/* Mission & Problem Statement Grid */}
      <div className="about-grid-section">
        <div className="about-card blueprint-panel">
          <div className="card-header-icon">
            <HardHat size={22} className="orange-icon" />
            <h3>The Procurement Challenge</h3>
          </div>
          <p>
            Construction material procurement accounts for <strong>55%–70%</strong> of total project expenditures. Volatile price swings in TMT steel bars, cement bags, sand, bricks, and gravel routinely cause budget overruns of 15%–30% when purchases are executed at market peaks.
          </p>
        </div>

        <div className="about-card blueprint-panel">
          <div className="card-header-icon">
            <Cpu size={22} className="orange-icon" />
            <h3>The BuildCost AI Solution</h3>
          </div>
          <p>
            BuildCost AI eliminates blind purchasing by grounding every single Bill of Materials (BOM) item in official <strong>PWD Schedule of Rates anchors</strong> and projecting <strong>12-month forward price drift curves</strong> using WPI time-series forecasting.
          </p>
        </div>
      </div>

      {/* Stack & System Specs */}
      <div className="system-specs-section blueprint-panel">
        <h2 className="section-grid-title">
          <span className="orange-square-marker"></span>
          TECHNICAL STACK & INFRASTRUCTURE
        </h2>

        <div className="specs-grid">
          <div className="spec-box">
            <Server size={20} className="spec-icon" />
            <div className="spec-info">
              <strong>FastAPI REST Backend</strong>
              <span>Python 3.13 service running on Uvicorn (`http://localhost:8000`) with Pydantic validation.</span>
            </div>
          </div>

          <div className="spec-box">
            <Database size={20} className="spec-icon" />
            <div className="spec-info">
              <strong>SQLite Database Engine</strong>
              <span>`buildcost.db` storing historical WPI indices, PWD anchors, CAD projects, and audit trails.</span>
            </div>
          </div>

          <div className="spec-box">
            <Code2 size={20} className="spec-icon" />
            <div className="spec-info">
              <strong>Vite + React Dashboard</strong>
              <span>React 19 single-page dashboard with Recharts data visualization and JetBrains Mono CAD styling.</span>
            </div>
          </div>

          <div className="spec-box">
            <ShieldAlert size={20} className="spec-icon" />
            <div className="spec-info">
              <strong>WeasyPrint PDF Engine</strong>
              <span>Native HTML/CSS to PDF document rendering with automatic ReportLab stream fallback.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Disclosures Card */}
      <div className="disclosures-footer blueprint-panel">
        <h3>Model Limitations & Algorithmic Disclosures</h3>
        <p>
          Forecast trajectories represent statistical extrapolations based on historical WPI trends and PWD baseline rates. Realized procurement costs may vary due to hyper-local supplier surcharges, haulage fees, or regional tax changes. Always verify estimates against formal vendor quotations.
        </p>
      </div>
    </div>
  );
}
