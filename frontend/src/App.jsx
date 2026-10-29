import React, { useState, useRef } from 'react';
import { predictOptimalBuildWindow, downloadReport, getProjectForecast } from './api/client';
import HeaderNav from './components/HeaderNav';
import FooterNav from './components/FooterNav';
import HeroLanding from './components/HeroLanding';
import ProcurementEngineGuide from './components/ProcurementEngineGuide';
import ProductPage from './components/ProductPage';
import PricingPage from './components/PricingPage';
import ResourcesPage from './components/ResourcesPage';
import AboutPage from './components/AboutPage';
import HealthBadge from './components/HealthBadge';
import InputForm from './components/InputForm';
import VendorQuoteCard from './components/VendorQuoteCard';
import RecommendationCard from './components/RecommendationCard';
import ForecastChart from './components/ForecastChart';
import BomTable from './components/BomTable';
import AnchorConversionCard from './components/AnchorConversionCard';
import LimitationNotice from './components/LimitationNotice';
import ProjectList from './components/ProjectList';
import ProjectSelector from './components/ProjectSelector';
import ProjectDetail from './components/ProjectDetail';
import { HardHat, FileText, Download, Loader2, AlertCircle, RefreshCw, ArrowRight, Cpu } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('home'); // 'home' | 'engine' | 'product' | 'pricing' | 'resources' | 'about'
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [results, setResults] = useState(null);

  // Active Project State
  const [activeProject, setActiveProject] = useState(null);
  const [showProjectModal, setShowProjectModal] = useState(false);

  // Form payload tracking for report generation
  const [currentSqft, setCurrentSqft] = useState(1000);
  const [currentMaterials, setCurrentMaterials] = useState(['steel', 'cement', 'sand', 'brick', 'gravel', 'wiring']);
  const [currentRegion, setCurrentRegion] = useState(null);
  const [sessionQuoteIds, setSessionQuoteIds] = useState([]);

  // PDF report state
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  // Workbench / Guide Ref for smooth scrolling
  const guideRef = useRef(null);

  const scrollToGuide = () => {
    if (guideRef.current) {
      guideRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectProject = async (project) => {
    setActiveProject(project);
    setShowProjectModal(false);
    setLoading(true);
    setApiError(null);
    setBannerDismissed(false);
    setCurrentSqft(project.sqft);
    setCurrentMaterials(project.target_materials);
    setCurrentRegion(project.region || null);

    try {
      const data = await getProjectForecast(project.id);
      setResults(data);
    } catch (err) {
      setResults(null);
      setApiError(err.message || 'Failed to calculate forecast for selected project.');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchToStateless = () => {
    setActiveProject(null);
    setResults(null);
    setApiError(null);
  };

  const handleFormSubmit = async (payload) => {
    setLoading(true);
    setApiError(null);
    setBannerDismissed(false);
    setCurrentSqft(payload.sqft);
    if (payload.target_materials) {
      setCurrentMaterials(payload.target_materials);
    }
    setCurrentRegion(payload.region || null);

    try {
      const data = await predictOptimalBuildWindow(payload);
      setResults(data);
    } catch (err) {
      setResults(null);
      setApiError(err.message || 'An unexpected error occurred while contacting the API.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuoteChecked = (quoteId) => {
    if (quoteId && !sessionQuoteIds.includes(quoteId)) {
      setSessionQuoteIds((prev) => [...prev, quoteId]);
    }
  };

  const handleDownloadPdf = async () => {
    if (!results && !activeProject) return;
    setPdfLoading(true);
    setPdfError(null);

    try {
      await downloadReport({
        sqft: activeProject ? undefined : currentSqft,
        target_materials: activeProject ? undefined : currentMaterials,
        region: activeProject ? undefined : (currentRegion || undefined),
        project_id: activeProject ? activeProject.id : undefined,
        include_vendor_quotes: true,
        vendor_quote_ids: sessionQuoteIds.length > 0 ? sessionQuoteIds : undefined,
      });
    } catch (err) {
      setPdfError(err.message || 'Failed to generate PDF report.');
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Universal Top Header Nav across all views */}
      <HeaderNav
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onOpenAuthModal={() => setShowProjectModal(true)}
      />

      {/* Main View Router */}
      {activeTab === 'home' && (
        <>
          <HeroLanding
            onOpenProjects={() => setShowProjectModal(true)}
            onScrollToWorkbench={scrollToGuide}
            onLaunchEngine={() => handleTabChange('engine')}
          />

          <div id="guide" ref={guideRef} className="guide-section">
            <ProcurementEngineGuide
              onLaunchEngine={() => handleTabChange('engine')}
              onOpenProjects={() => setShowProjectModal(true)}
            />
          </div>
        </>
      )}

      {/* Dedicated Interactive Procurement Engine Workbench Page */}
      {activeTab === 'engine' && (
        <div id="workbench" className="workbench-section" style={{ paddingTop: '100px', width: '100%', maxWidth: '100%', margin: 0, paddingLeft: '36px', paddingRight: '36px' }}>
          {/* Workbench Header Banner */}
          <div className="blueprint-panel" style={{ backgroundColor: 'var(--bg-cream-alt)', border: '1px solid var(--line-gray)', padding: '20px 24px', marginBottom: '24px', position: 'relative' }}>
            <span className="corner-mark top-left">+</span>
            <span className="corner-mark top-right">+</span>
            <span className="corner-mark bottom-left">+</span>
            <span className="corner-mark bottom-right">+</span>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ backgroundColor: 'var(--ink-black)', color: 'var(--accent-orange)', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Cpu size={20} />
                </div>
                <div>
                  <h2 style={{ fontFamily: 'var(--font-headline)', fontSize: '1.3rem', fontWeight: '800', textTransform: 'uppercase', color: 'var(--ink-black)', margin: 0 }}>
                    PROCUREMENT ENGINE WORKBENCH
                  </h2>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--label-gray-dark)', textTransform: 'uppercase', margin: 0 }}>
                    INTERACTIVE BOM COST CALCULATION, WPI FORECAST TRAJECTORIES & FAIR PRICE CHECKS
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <HealthBadge />
                <button
                  onClick={() => handleTabChange('home')}
                  style={{ background: 'none', border: '1px solid var(--line-gray)', color: 'var(--ink-black)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem', fontWeight: '700', textTransform: 'uppercase', padding: '8px 14px', cursor: 'pointer' }}
                >
                  &larr; BACK TO GUIDANCE
                </button>
              </div>
            </div>
          </div>

          <ProjectSelector
            activeProject={activeProject}
            onOpenProjectList={() => setShowProjectModal(true)}
            onSwitchToStateless={handleSwitchToStateless}
          />

          {activeProject && (
            <ProjectDetail
              project={activeProject}
              onProjectUpdated={(updated) => {
                setActiveProject(updated);
                handleSelectProject(updated);
              }}
            />
          )}

          <section className="input-section">
            {!activeProject && (
              <InputForm onSubmit={handleFormSubmit} loading={loading} apiError={apiError} />
            )}
            <VendorQuoteCard
              onQuoteChecked={handleQuoteChecked}
              activeProjectId={activeProject?.id}
              activeProjectName={activeProject?.name}
            />
          </section>

          {results && (
            <main className="results-section">
              {pdfError && (
                <div className="error-banner" style={{ marginBottom: '16px' }}>
                  <AlertCircle size={18} />
                  <span>{pdfError}</span>
                </div>
              )}

              <RecommendationCard recommendation={results.recommendation} />
              <ForecastChart forecastData={results.forecast} recommendation={results.recommendation} />
              <BomTable
                bomData={results.bom_cost_by_month}
                recommendedMonth={results.recommendation?.recommended_year_month}
              />
              <AnchorConversionCard anchorData={results.anchor_conversion} />
              <LimitationNotice metadata={results.metadata} />
            </main>
          )}
        </div>
      )}

      {activeTab === 'product' && (
        <ProductPage
          onNavigateHome={() => handleTabChange('home')}
          onScrollToWorkbench={() => handleTabChange('engine')}
        />
      )}

      {activeTab === 'pricing' && (
        <PricingPage
          onNavigateHome={() => handleTabChange('home')}
          onScrollToWorkbench={() => handleTabChange('engine')}
        />
      )}

      {activeTab === 'resources' && (
        <ResourcesPage
          onNavigateHome={() => handleTabChange('home')}
        />
      )}

      {activeTab === 'about' && (
        <AboutPage
          onNavigateHome={() => handleTabChange('home')}
          onScrollToWorkbench={() => handleTabChange('engine')}
        />
      )}

      {/* Viewport Anchored Bottom Action / Staleness Banner */}
      {(!bannerDismissed) && (
        <div className="bottom-banner-bar">
          <div className="bottom-banner-content">
            <span className="orange-square-marker large"></span>
            <div className="bottom-banner-text">
              {results ? (
                <>
                  <strong>Procurement Analysis Ready:</strong> Executive report compiled with 12-month WPI drift trajectory & vendor quote audit trail.
                </>
              ) : activeProject ? (
                <>
                  <strong>Active CAD Project Loaded:</strong> {activeProject.name} — ({activeProject.sqft.toLocaleString()} sq.ft).
                </>
              ) : (
                <>
                  <strong>BuildCost AI Blueprint Engine:</strong> Real-time PWD anchor drift & walk-forward backtest estimation ready.
                </>
              )}
            </div>
          </div>
          <div className="bottom-banner-actions">
            {results && (
              <button
                onClick={handleDownloadPdf}
                className="btn-banner-primary"
                disabled={pdfLoading}
              >
                {pdfLoading ? (
                  <>
                    <Loader2 className="spinner" size={16} /> Compiling PDF...
                  </>
                ) : (
                  <>
                    <FileText size={16} /> Generate Executive Report
                  </>
                )}
              </button>
            )}
            <button
              onClick={() => setBannerDismissed(true)}
              className="btn-banner-ghost"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Projects Modal */}
      {showProjectModal && (
        <ProjectList
          activeProjectId={activeProject?.id}
          onSelectProject={(proj) => {
            handleSelectProject(proj);
            handleTabChange('engine');
          }}
          onClose={() => setShowProjectModal(false)}
        />
      )}

      {/* Universal Full-Width Architectural Drafting Footer Grid */}
      <FooterNav
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onLaunchEngine={() => handleTabChange('engine')}
        onOpenProjects={() => setShowProjectModal(true)}
      />
    </div>
  );
}
