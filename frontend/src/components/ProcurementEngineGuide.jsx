import React from 'react';
import {
  Cpu,
  BookOpen,
  ArrowRight,
  Folder,
  ShieldCheck,
  TrendingUp,
  Layers,
  FileSearch,
  CheckCircle2,
  Zap,
  ChevronRight
} from 'lucide-react';

export default function ProcurementEngineGuide({ onLaunchEngine, onOpenProjects }) {
  const [activeStepId, setActiveStepId] = React.useState('01');
  const [displayedStepId, setDisplayedStepId] = React.useState('01');
  const [isDiminishing, setIsDiminishing] = React.useState(false);
  const transitionTimerRef = React.useRef(null);
  const stepRefs = React.useRef({});

  const stepsData = [
    {
      id: '01',
      title: 'PWD BASE ANCHOR RATES',
      icon: ShieldCheck,
      badgeText: 'FY 2025-26 ANCHOR BASE',
      imgSrc: '/step_1_blueprint.jpg',
      desc: 'Pulls FY 2025-26 official PWD baseline anchors and converts reference rates to baseline conversion multipliers (₹ per WPI index point).',
      supportingContent: 'Integrates official Public Works Department (PWD) Schedule of Rates reference benchmarks as the baseline cost ceiling for all raw material calculations. Converts reference rates into baseline conversion multipliers (₹ per WPI index point) to anchor forward forecasts in government policy standards.'
    },
    {
      id: '02',
      title: '12-MONTH WPI DRIFT',
      icon: TrendingUp,
      badgeText: 'WALK-FORWARD FORECAST',
      imgSrc: '/step_2_blueprint.jpg',
      desc: 'Extrapolates 12-month forward price trajectories using recent index drift rate forecasting for cement, steel, wiring, and structural aggregates.',
      supportingContent: 'Applies macroeconomic Wholesale Price Index (WPI) time-series forecasting to project 12-month forward price trajectories for high-volume structural materials (cement, steel, wiring, sand, bricks, and gravel), identifying market trends and commodity cost inflation windows.'
    },
    {
      id: '03',
      title: 'BOM COST BREAKDOWN',
      icon: Layers,
      badgeText: 'OPTIMAL WINDOW ENGINE',
      imgSrc: '/step_3_blueprint.jpg',
      desc: 'Calculates monthly project Bill of Materials totals, recommending optimal purchasing months to maximize savings over immediate purchasing.',
      supportingContent: 'Aggregates project-level Bill of Materials scaled to total square footage, analyzing month-by-month purchasing costs across the 12-month timeline to pinpoint the single optimal purchasing window that minimizes overall project spend.'
    },
    {
      id: '04',
      title: 'VENDOR QUOTE AUDIT',
      icon: FileSearch,
      badgeText: 'CONTRACTOR PRICE AUDIT',
      imgSrc: '/step_4_blueprint.jpg',
      desc: 'Evaluates individual contractor quotes against expected market rates and standard units, detecting price gouging or unit mismatches.',
      supportingContent: 'Audits individual contractor and supplier proposals against expected market rate windows derived from PWD baseline anchors and WPI trend forecasts. Automatically normalizes measurement units and flags price gouging or unit conversion discrepancies.'
    }
  ];

  React.useEffect(() => {
    const updateActiveStep = () => {
      // Threshold Y for step switching (35% down viewport, aligning with sticky container)
      const thresholdY = Math.max(220, window.innerHeight * 0.35);
      let activeId = stepsData[0].id;

      for (const step of stepsData) {
        const el = stepRefs.current[step.id];
        if (!el) continue;
        const rect = el.getBoundingClientRect();
        if (rect.top <= thresholdY) {
          activeId = step.id;
        }
      }

      // Force first step when near top of workflow guide container
      const firstEl = stepRefs.current[stepsData[0].id];
      if (firstEl) {
        const firstRect = firstEl.getBoundingClientRect();
        if (firstRect.top > thresholdY - 80) {
          activeId = stepsData[0].id;
        }
      }

      // Force last step when scrolled to bottom of workflow container or page
      const lastEl = stepRefs.current[stepsData[stepsData.length - 1].id];
      if (lastEl) {
        const lastRect = lastEl.getBoundingClientRect();
        if (lastRect.top <= thresholdY + 120 || (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 100)) {
          activeId = stepsData[stepsData.length - 1].id;
        }
      }

      setActiveStepId((prev) => (prev !== activeId ? activeId : prev));
    };

    window.addEventListener('scroll', updateActiveStep, { passive: true, capture: true });
    document.addEventListener('scroll', updateActiveStep, { passive: true, capture: true });

    // Poll every 50ms for continuous sync during smooth scrolling
    const timer = setInterval(updateActiveStep, 50);
    updateActiveStep();

    return () => {
      window.removeEventListener('scroll', updateActiveStep, { capture: true });
      document.removeEventListener('scroll', updateActiveStep, { capture: true });
      clearInterval(timer);
    };
  }, []);

  // Ultra-smooth diminishing (350ms exit) & slow, cinematic appearing transition (700ms ease-out) when active step changes
  React.useEffect(() => {
    if (activeStepId !== displayedStepId) {
      setIsDiminishing(true);
      if (transitionTimerRef.current) {
        clearTimeout(transitionTimerRef.current);
      }
      transitionTimerRef.current = setTimeout(() => {
        setDisplayedStepId(activeStepId);
        setIsDiminishing(false);
      }, 350);
    }
  }, [activeStepId, displayedStepId]);

  const displayedStepData = stepsData.find((s) => s.id === displayedStepId) || stepsData[0];

  return (
    <div className="procurement-guide-section" style={{ padding: 0, width: '100%', maxWidth: '100%', margin: 0 }}>
      <div className="blueprint-panel" style={{
        backgroundColor: 'var(--bg-cream-alt)',
        borderTop: 'none',
        borderBottom: 'var(--border-hairline)',
        borderLeft: 'none',
        borderRight: 'none',
        padding: '36px 48px',
        position: 'relative',
        width: '100%'
      }}>
        <span className="corner-mark top-left">+</span>
        <span className="corner-mark top-right">+</span>
        <span className="corner-mark bottom-left">+</span>
        <span className="corner-mark bottom-right">+</span>

        {/* Section Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '20px', borderBottom: '1px solid var(--line-gray)', paddingBottom: '20px', marginBottom: '28px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <div style={{
                backgroundColor: 'var(--ink-black)',
                color: 'var(--accent-orange)',
                width: '36px',
                height: '36px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Cpu size={20} />
              </div>
              <h2 style={{
                fontFamily: 'var(--font-headline)',
                fontSize: '1.5rem',
                fontWeight: '800',
                textTransform: 'uppercase',
                color: 'var(--ink-black)',
                margin: 0
              }}>
                BUILDCOST PROCUREMENT ENGINE — GUIDANCE & SYSTEM SPECIFICATION
              </h2>
            </div>
            <p style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.82rem',
              color: 'var(--label-gray-dark)',
              textTransform: 'uppercase',
              margin: 0
            }}>
              TECHNICAL SPECIFICATION MANUAL • PWD SCHEDULE OF RATES & 12-MONTH WPI DRIFT TRAJECTORY MODELING
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={onLaunchEngine}
              className="btn-submit"
              style={{ margin: 0, padding: '12px 24px', fontSize: '0.85rem' }}
            >
              <span>LAUNCH PROCUREMENT ENGINE</span>
              <ArrowRight size={16} className="btn-arrow" />
            </button>
          </div>
        </div>

        {/* Overview Box */}
        <div style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--line-gray)',
          padding: '20px 24px',
          marginBottom: '28px'
        }}>
          <h3 style={{
            fontFamily: 'var(--font-headline)',
            fontSize: '1.05rem',
            fontWeight: '700',
            textTransform: 'uppercase',
            color: 'var(--ink-black)',
            marginBottom: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <BookOpen size={18} style={{ color: 'var(--accent-orange)' }} />
            SYSTEM OVERVIEW & PURPOSE
          </h3>
          <p style={{ color: 'var(--ink-soft)', fontSize: '0.92rem', lineHeight: 1.6, margin: 0 }}>
            The <strong>BuildCost AI Procurement Engine</strong> bridges public policy reference benchmarks and dynamic commodity markets. By calibrating official Public Works Department (PWD) baseline Schedule of Rates against 12-month Wholesale Price Index (WPI) trend extrapolations, the engine identifies cost-optimal purchasing windows for high-volume structural materials (steel, cement, wiring, sand, bricks, and gravel).
          </p>
        </div>

        {/* CAD Blueprint Vertical Workflow Grid Section with Sticky Left Transportable Grid */}
        <div style={{
          border: '1px solid var(--line-gray)',
          backgroundColor: 'var(--bg-cream)',
          marginBottom: '32px',
          display: 'grid',
          gridTemplateColumns: 'minmax(280px, 340px) 1fr',
          position: 'relative'
        }}>
          {/* Left Column: Sticky Transportable Grid Column */}
          <div style={{
            gridColumn: '1',
            backgroundColor: 'var(--bg-cream-alt)',
            position: 'relative',
            borderRight: '1px solid var(--line-gray)',
            display: 'flex',
            flexDirection: 'column',
            height: '100%'
          }}>
            {/* Vertical CAD Drafting Margin Line running down the left side */}
            <div style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: '12px',
              width: '1px',
              backgroundColor: 'var(--line-gray)',
              pointerEvents: 'none',
              zIndex: 2
            }} />

            {/* Sticky Transportable Title Shower Grid Box (Single Grid Cell Alone) */}
            <div style={{
              position: 'sticky',
              top: '84px',
              alignSelf: 'start',
              width: '100%',
              backgroundColor: 'var(--bg-cream-alt)',
              borderBottom: '1px solid var(--line-gray)',
              borderTop: '1px solid var(--line-gray)',
              padding: '36px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              boxSizing: 'border-box'
            }}>
              <div
                key={displayedStepData.id}
                className={isDiminishing ? 'title-shower-diminishing' : 'title-shower-appearing'}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  width: '100%'
                }}
              >
                {/* Step Index Number: e.g. [01], [02], [03], [04] */}
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.92rem',
                  color: 'var(--label-gray-dark)',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  marginBottom: '24px'
                }}>
                  [{displayedStepData.id}]
                </div>

                {/* Main Title: e.g. PWD BASE ANCHOR RATES, HERON DASHBOARD style */}
                <h3 style={{
                  fontFamily: 'var(--font-headline)',
                  fontSize: '1.85rem',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  color: 'var(--ink-black)',
                  margin: 0,
                  lineHeight: '1.15',
                  letterSpacing: '-0.02em',
                  maxWidth: '260px',
                  wordBreak: 'break-word'
                }}>
                  {displayedStepData.title}
                </h3>

                {/* Subtitle / Badge text */}
                {displayedStepData.badgeText && (
                  <div style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.72rem',
                    color: 'var(--accent-orange)',
                    textTransform: 'uppercase',
                    fontWeight: 700,
                    letterSpacing: '0.08em',
                    marginTop: '16px'
                  }}>
                    {displayedStepData.badgeText}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Main Scrollable Vertical Steps Area */}
          <div style={{ gridColumn: '2', display: 'flex', flexDirection: 'column' }}>
            {stepsData.map((step, idx) => {
              const isLast = idx === stepsData.length - 1;
              const isActive = step.id === activeStepId;

              return (
                <div
                  key={step.id}
                  data-step-id={step.id}
                  ref={(el) => (stepRefs.current[step.id] = el)}
                  onClick={() => {
                    setActiveStepId(step.id);
                    stepRefs.current[step.id]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }}
                  style={{
                    borderBottom: isLast ? 'none' : '1px solid var(--line-gray)',
                    padding: '36px 36px',
                    backgroundColor: isActive ? 'var(--bg-cream-alt)' : '#ffffff',
                    borderLeft: isActive ? '4px solid var(--accent-orange)' : '4px solid transparent',
                    transition: 'all 0.25s ease-in-out',
                    cursor: 'pointer',
                    minHeight: '320px'
                  }}
                >
                  {/* Step Main Description */}
                  <p style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '1.08rem',
                    fontWeight: 500,
                    lineHeight: 1.65,
                    color: 'var(--ink-black)',
                    marginBottom: '20px'
                  }}>
                    {step.desc}
                  </p>

                  {/* Side-by-Side Row: Left Blended Image, Right Supporting Methodology Text */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'minmax(240px, 280px) 1fr',
                    gap: '24px',
                    alignItems: 'stretch'
                  }}>
                    {/* Left Side: Seamlessly Blended Blueprint Sketch Image */}
                    <div style={{
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: 'transparent',
                      overflow: 'hidden'
                    }}>
                      <img
                        src={step.imgSrc}
                        alt={step.title}
                        style={{
                          width: '100%',
                          height: '100%',
                          minHeight: '170px',
                          maxHeight: '210px',
                          display: 'block',
                          objectFit: 'cover',
                          objectPosition: 'center',
                          mixBlendMode: 'multiply',
                          filter: 'contrast(1.04) saturate(1.05)',
                          WebkitMaskImage: 'radial-gradient(ellipse at center, rgba(0,0,0,1) 55%, rgba(0,0,0,0) 98%)',
                          maskImage: 'radial-gradient(ellipse at center, rgba(0,0,0,1) 55%, rgba(0,0,0,0) 98%)'
                        }}
                      />
                    </div>

                    {/* Right Side: Supporting Topic Text Content Box */}
                    <div style={{
                      backgroundColor: 'var(--bg-cream-alt)',
                      border: '1px solid var(--line-gray)',
                      padding: '20px 22px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center'
                    }}>
                      <div style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.82rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        color: 'var(--accent-orange)',
                        marginBottom: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <CheckCircle2 size={16} />
                        METHODOLOGY & TECHNICAL SPECIFICATION
                      </div>
                      <p style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: '1.02rem',
                        lineHeight: 1.65,
                        color: 'var(--ink-soft)',
                        margin: 0
                      }}>
                        {step.supportingContent}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}

