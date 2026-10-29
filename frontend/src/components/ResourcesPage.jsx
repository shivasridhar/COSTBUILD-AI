import React, { useState } from 'react';
import {
  BookOpen,
  FileText,
  Code,
  CheckSquare,
  Download,
  ExternalLink,
  Search,
  ArrowRight,
  Database
} from 'lucide-react';

export default function ResourcesPage({ onNavigateHome }) {
  const [filterCategory, setFilterCategory] = useState('all');

  const resources = [
    {
      id: 'pwd-guide',
      category: 'pwd',
      icon: <Database size={22} />,
      title: 'PWD Schedule of Rates (SOR) Reference Manual',
      desc: 'Comprehensive reference catalog for Public Works Department baseline rates across civil engineering items.',
      tag: 'PWD GUIDE',
      type: 'Documentation',
      linkText: 'View PWD Reference Docs'
    },
    {
      id: 'wpi-paper',
      category: 'wpi',
      icon: <FileText size={22} />,
      title: '12-Month WPI Trajectory Extrapolation Methodology',
      desc: 'Technical whitepaper explaining walk-forward ARIMA and XGBoost regression models on Ministry of Commerce WPI series.',
      tag: 'WHITEPAPER',
      type: 'PDF Paper',
      linkText: 'Download Methodology Paper'
    },
    {
      id: 'api-spec',
      category: 'api',
      icon: <Code size={22} />,
      title: 'FastAPI Backend REST Service OpenAPI Spec',
      desc: 'Interactive Swagger UI endpoint specs for /predict-optimal-build-window, /check-fair-price, and /generate-report.',
      tag: 'API SPEC',
      type: 'Developer Spec',
      linkText: 'Explore API Endpoints'
    },
    {
      id: 'sanity-guide',
      category: 'pwd',
      icon: <CheckSquare size={22} />,
      title: 'Sanity Check Rate Bounds & Unit Normalization Rules',
      desc: 'Operational guide on automated 1.5x upper/lower sanity check bounds and unit conversion formulas.',
      tag: 'STANDARDS',
      type: 'Technical Guide',
      linkText: 'Read Conversion Specs'
    },
    {
      id: 'bom-playbook',
      category: 'whitepaper',
      icon: <BookOpen size={22} />,
      title: 'Construction Procurement Optimization Playbook 2026',
      desc: 'Practical guide for civil contractors on mitigating raw material price spikes through staged procurement timing.',
      tag: 'PLAYBOOK',
      type: 'Guide',
      linkText: 'Read Playbook'
    }
  ];

  const filteredResources = filterCategory === 'all'
    ? resources
    : resources.filter((r) => r.category === filterCategory);

  return (
    <div className="page-container resources-page">
      {/* Header Banner */}
      <div className="page-header-banner blueprint-panel">
        <span className="corner-mark top-left">+</span>
        <span className="corner-mark top-right">+</span>
        <span className="corner-mark bottom-left">+</span>
        <span className="corner-mark bottom-right">+</span>

        <div className="header-badge">
          <BookOpen size={16} />
          <span>TECHNICAL RESOURCE REPOSITORY</span>
        </div>
        <h1 className="page-title">DOCUMENTATION & RESEARCH KNOWLEDGE BASE</h1>
        <p className="page-subtitle">
          Access PWD Schedule of Rates reference guides, WPI forecasting whitepapers, API specs, and procurement optimization playbooks.
        </p>

        {/* Category Filters */}
        <div className="category-filter-chips">
          <button
            className={`filter-chip ${filterCategory === 'all' ? 'active' : ''}`}
            onClick={() => setFilterCategory('all')}
          >
            All Resources ({resources.length})
          </button>
          <button
            className={`filter-chip ${filterCategory === 'pwd' ? 'active' : ''}`}
            onClick={() => setFilterCategory('pwd')}
          >
            PWD Schedules
          </button>
          <button
            className={`filter-chip ${filterCategory === 'wpi' ? 'active' : ''}`}
            onClick={() => setFilterCategory('wpi')}
          >
            WPI Models
          </button>
          <button
            className={`filter-chip ${filterCategory === 'api' ? 'active' : ''}`}
            onClick={() => setFilterCategory('api')}
          >
            API Docs
          </button>
          <button
            className={`filter-chip ${filterCategory === 'whitepaper' ? 'active' : ''}`}
            onClick={() => setFilterCategory('whitepaper')}
          >
            Whitepapers
          </button>
        </div>
      </div>

      {/* Resource Cards Grid */}
      <div className="resources-grid">
        {filteredResources.map((res) => (
          <div key={res.id} className="resource-card blueprint-panel">
            <div className="resource-card-header">
              <div className="resource-icon-box">{res.icon}</div>
              <span className="resource-tag">{res.tag}</span>
            </div>

            <h3 className="resource-title">{res.title}</h3>
            <p className="resource-desc">{res.desc}</p>

            <div className="resource-footer">
              <span className="resource-type">{res.type}</span>
              <a
                href={res.category === 'api' ? 'http://localhost:8000/docs' : '#'}
                target={res.category === 'api' ? '_blank' : '_self'}
                rel="noreferrer"
                className="resource-link"
              >
                <span>{res.linkText}</span>
                <ExternalLink size={14} />
              </a>
            </div>
          </div>
        ))}
      </div>

      {/* API Quick Access Card */}
      <div className="api-quick-card blueprint-panel">
        <div className="api-card-content">
          <Code size={24} className="orange-icon" />
          <div>
            <h3>Interactive FastAPI Swagger Specification</h3>
            <p>Direct REST service running on <code>http://localhost:8000/docs</code> with health checks, forecast calculations, and PDF generation streams.</p>
          </div>
        </div>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="btn-submit"
          style={{ width: 'auto', padding: '12px 24px' }}
        >
          <span>OPEN SWAGGER DOCS</span>
          <ArrowRight size={16} className="btn-arrow" />
        </a>
      </div>
    </div>
  );
}
