import React, { useState } from 'react';
import {
  Check,
  Zap,
  Building,
  Shield,
  ArrowRight,
  HelpCircle,
  Sparkles
} from 'lucide-react';

export default function PricingPage({ onNavigateHome, onScrollToWorkbench }) {
  const [billingCycle, setBillingCycle] = useState('annual'); // 'monthly' | 'annual'

  const plans = [
    {
      id: 'stateless',
      name: 'STATELESS FREE',
      tagline: 'Ideal for quick one-off build area material calculations & price trajectory checks.',
      monthlyPrice: '₹0',
      annualPrice: '₹0',
      period: 'Forever Free',
      badge: null,
      features: [
        'Stateless 12-Month WPI Price Trajectory Forecast',
        'PWD Reference Anchor Rate Normalization',
        'Single Vendor Quote Fair Price Verification',
        'Support for Steel, Cement, Sand, Brick, Gravel',
        'Standard Web Dashboard Access'
      ],
      ctaText: 'USE FREE WORKBENCH',
      isPrimary: false
    },
    {
      id: 'pro',
      name: 'PRO BUILDER',
      tagline: 'Complete CAD project persistence, multi-phase BOM tracking, and executive reports.',
      monthlyPrice: '₹4,999',
      annualPrice: '₹3,999',
      period: 'per month, billed annually',
      badge: 'MOST POPULAR',
      features: [
        'Everything in Stateless Free',
        'Unlimited Registered CAD Projects Storage',
        'Staged Construction Phase Management',
        'Unlimited Executive PDF Report Generation',
        'Vendor Quote Audit Trail & Session History',
        'Email & PDF Stream Support'
      ],
      ctaText: 'START PRO WORKBENCH',
      isPrimary: true
    },
    {
      id: 'enterprise',
      name: 'ENTERPRISE SOR',
      tagline: 'Custom regional PWD schedule imports, REST API access, and multi-user sync.',
      monthlyPrice: '₹14,999',
      annualPrice: '₹11,999',
      period: 'per month, billed annually',
      badge: 'CUSTOM SCHEDULES',
      features: [
        'Everything in Pro Builder',
        'Custom State PWD Schedule Imports',
        'FastAPI REST Service API Keys & Endpoints',
        'Multi-User Team Quote Approvals',
        'Dedicated Procurement Specialist Support',
        'Custom WPI Model Weight Adjustments'
      ],
      ctaText: 'CONTACT ENTERPRISE',
      isPrimary: false
    }
  ];

  const featureMatrix = [
    { name: '12-Month WPI Forecast Trajectories', free: '✓', pro: '✓', enterprise: '✓' },
    { name: 'PWD Baseline Rate Verification', free: '✓', pro: '✓', enterprise: '✓' },
    { name: 'Single Vendor Quote Fair Price Check', free: '✓', pro: '✓', enterprise: '✓' },
    { name: 'Registered CAD Project Persistence', free: '—', pro: 'Unlimited', enterprise: 'Unlimited' },
    { name: 'Multi-Phase Construction Staging', free: '—', pro: '✓', enterprise: '✓' },
    { name: 'Executive PDF Audit Reports', free: 'Watermarked', pro: 'Unlimited Stream', enterprise: 'Custom Branding' },
    { name: 'FastAPI Backend REST API Keys', free: '—', pro: '—', enterprise: 'Included' },
    { name: 'Custom State PWD SOR Schedules', free: '—', pro: '—', enterprise: 'Included' },
  ];

  return (
    <div className="page-container pricing-page">
      {/* Header Banner */}
      <div className="page-header-banner blueprint-panel text-center">
        <span className="corner-mark top-left">+</span>
        <span className="corner-mark top-right">+</span>
        <span className="corner-mark bottom-left">+</span>
        <span className="corner-mark bottom-right">+</span>

        <div className="header-badge" style={{ margin: '0 auto 12px auto' }}>
          <Zap size={16} />
          <span>TRANSPARENT BLUEPRINT PRICING</span>
        </div>
        <h1 className="page-title">BUILDCOST AI PROCUREMENT PLANS</h1>
        <p className="page-subtitle" style={{ maxWidth: '680px', margin: '0 auto 24px auto' }}>
          Choose the right operational plan for your construction team—from quick stateless calculations to enterprise CAD project phase management.
        </p>

        {/* Billing Cycle Toggle */}
        <div className="billing-toggle-container">
          <button
            className={`toggle-btn ${billingCycle === 'monthly' ? 'active' : ''}`}
            onClick={() => setBillingCycle('monthly')}
          >
            Monthly Billing
          </button>
          <button
            className={`toggle-btn ${billingCycle === 'annual' ? 'active' : ''}`}
            onClick={() => setBillingCycle('annual')}
          >
            Annual Billing <span className="discount-chip">SAVE 20%</span>
          </button>
        </div>
      </div>

      {/* Pricing Cards Grid */}
      <div className="pricing-cards-grid">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`pricing-card blueprint-panel ${plan.isPrimary ? 'primary-card' : ''}`}
          >
            {plan.badge && <div className="card-badge">{plan.badge}</div>}

            <h3 className="plan-name">{plan.name}</h3>
            <p className="plan-tagline">{plan.tagline}</p>

            <div className="plan-price-block">
              <span className="price-val">
                {billingCycle === 'annual' ? plan.annualPrice : plan.monthlyPrice}
              </span>
              <span className="price-period">{plan.period}</span>
            </div>

            <ul className="plan-features-list">
              {plan.features.map((feat, idx) => (
                <li key={idx}>
                  <Check size={16} className="check-icon" />
                  <span>{feat}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={() => {
                onNavigateHome();
                if (onScrollToWorkbench) onScrollToWorkbench();
              }}
              className={`btn-submit ${plan.isPrimary ? 'primary-btn' : ''}`}
            >
              <span>{plan.ctaText}</span>
              <ArrowRight size={16} className="btn-arrow" />
            </button>
          </div>
        ))}
      </div>

      {/* Feature Comparison Matrix */}
      <div className="feature-matrix-section blueprint-panel">
        <h2 className="section-grid-title">
          <span className="orange-square-marker"></span>
          DETAILED TECHNICAL FEATURE COMPARISON
        </h2>

        <div className="matrix-table-wrapper">
          <table className="matrix-table">
            <thead>
              <tr>
                <th>PLATFORM CAPABILITY</th>
                <th>STATELESS FREE</th>
                <th>PRO BUILDER</th>
                <th>ENTERPRISE SOR</th>
              </tr>
            </thead>
            <tbody>
              {featureMatrix.map((row, idx) => (
                <tr key={idx}>
                  <td className="feature-name-col">{row.name}</td>
                  <td className="matrix-cell">{row.free}</td>
                  <td className="matrix-cell highlight">{row.pro}</td>
                  <td className="matrix-cell">{row.enterprise}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
