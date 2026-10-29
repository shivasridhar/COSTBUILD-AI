import React, { useState } from 'react';
import {
  HardHat,
  ArrowRight,
  ArrowUp,
  Mail,
  ExternalLink,
  CheckCircle2,
  Cpu
} from 'lucide-react';

export default function FooterNav({ activeTab = 'home', onTabChange, onLaunchEngine, onOpenProjects }) {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleNavClick = (tab) => {
    if (onTabChange) {
      onTabChange(tab);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
      setTimeout(() => {
        setSubscribed(false);
        setEmail('');
      }, 4000);
    }
  };

  return (
    <footer className="footer-categorized-grid-wrapper" style={{
      width: '100%',
      marginTop: '60px',
      backgroundColor: 'var(--bg-cream)',
      borderTop: '1px solid var(--line-gray)',
      position: 'relative'
    }}>

      {/* Main 4-Column Multi-Row Categorized Drafting Grid */}
      <div className="footer-grid-matrix" style={{
        display: 'grid',
        gridTemplateColumns: '1.2fr 1fr 1fr 1fr',
        width: '100%',
        backgroundColor: 'var(--bg-cream)'
      }}>

        {/* =====================================================================
           ROW 1: SLOGAN BOX + COMPANY + PRODUCT + RESOURCES
           ===================================================================== */}

        {/* Row 1, Col 1: Big Bold Slogan Cell */}
        <div style={{
          padding: '36px 32px',
          borderRight: '1px solid var(--line-gray)',
          borderBottom: '1px solid var(--line-gray)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '24px'
        }}>
          <div>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: 'var(--label-gray)',
              letterSpacing: '0.08em',
              marginBottom: '16px'
            }}>
              BUILDCOST AI
            </div>
            <h2 style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.85rem',
              fontWeight: '800',
              lineHeight: 1.15,
              color: 'var(--ink-black)',
              textTransform: 'uppercase',
              letterSpacing: '-0.03em',
              margin: 0
            }}>
              AN AI AGENT THAT OPTIMIZES YOUR CONSTRUCTION BILL OF MATERIALS
            </h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              backgroundColor: 'var(--ink-black)',
              color: 'var(--accent-orange)',
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <HardHat size={16} />
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: '700', color: 'var(--ink-black)', textTransform: 'uppercase' }}>
              PWD FY 2025-26 ANCHORS
            </span>
          </div>
        </div>

        {/* Row 1, Col 2: COMPANY Links */}
        <div style={{
          padding: '36px 28px',
          borderRight: '1px solid var(--line-gray)',
          borderBottom: '1px solid var(--line-gray)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            fontWeight: '700',
            textTransform: 'uppercase',
            color: 'var(--label-gray)',
            letterSpacing: '0.08em'
          }}>
            COMPANY
          </div>

          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <li onClick={() => handleNavClick('home')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: activeTab === 'home' ? 'var(--accent-orange)' : 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              Home
            </li>
            <li onClick={() => handleNavClick('about')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: activeTab === 'about' ? 'var(--accent-orange)' : 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              About Us
            </li>
            <li onClick={() => handleNavClick('pricing')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: activeTab === 'pricing' ? 'var(--accent-orange)' : 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              Pricing & Tiers
            </li>
            <li onClick={onOpenProjects} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              CAD Projects Registry
            </li>
          </ul>
        </div>

        {/* Row 1, Col 3: PRODUCT Links */}
        <div style={{
          padding: '36px 28px',
          borderRight: '1px solid var(--line-gray)',
          borderBottom: '1px solid var(--line-gray)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            fontWeight: '700',
            textTransform: 'uppercase',
            color: 'var(--label-gray)',
            letterSpacing: '0.08em'
          }}>
            PRODUCT
          </div>

          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <li onClick={() => handleNavClick('engine')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: activeTab === 'engine' ? 'var(--accent-orange)' : 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              Procurement Engine
            </li>
            <li onClick={() => handleNavClick('product')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: activeTab === 'product' ? 'var(--accent-orange)' : 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              12-Month WPI Forecast
            </li>
            <li onClick={() => handleNavClick('engine')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              Vendor Fair Price Audit
            </li>
            <li onClick={() => handleNavClick('engine')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              Executive PDF Generator
            </li>
          </ul>
        </div>

        {/* Row 1, Col 4: RESOURCES Links */}
        <div style={{
          padding: '36px 28px',
          borderBottom: '1px solid var(--line-gray)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            fontWeight: '700',
            textTransform: 'uppercase',
            color: 'var(--label-gray)',
            letterSpacing: '0.08em'
          }}>
            RESOURCES
          </div>

          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <li onClick={() => handleNavClick('resources')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: activeTab === 'resources' ? 'var(--accent-orange)' : 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              PWD Reference Manual
            </li>
            <li onClick={() => handleNavClick('resources')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              WPI Series Datasets
            </li>
            <li onClick={() => handleNavClick('resources')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              Walk-Forward Backtesting
            </li>
            <li onClick={() => handleNavClick('resources')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.05rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}>
              Algorithmic Disclosures
            </li>
          </ul>
        </div>


        {/* =====================================================================
           ROW 2: SUBSCRIBE BOX + ADDRESS + INQUIRIES + CONNECT / SOCIAL
           ===================================================================== */}

        {/* Row 2, Col 1: Subscribe Box */}
        <div style={{
          padding: '32px',
          borderRight: '1px solid var(--line-gray)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '20px'
        }}>
          <div>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: 'var(--label-gray)',
              letterSpacing: '0.08em',
              marginBottom: '12px'
            }}>
              SUBSCRIBE
            </div>
            <p style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '0.98rem',
              lineHeight: 1.4,
              color: 'var(--ink-black)',
              fontWeight: '600',
              margin: 0
            }}>
              Want to receive monthly PWD benchmark updates & WPI drift alerts?
            </p>
          </div>

          <form onSubmit={handleSubscribe} style={{ display: 'flex', border: '1px solid var(--line-gray)', backgroundColor: '#ffffff' }}>
            <input
              type="email"
              placeholder={subscribed ? "SUBSCRIBED SUCCESSFULLY!" : "Enter your email"}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={subscribed}
              style={{
                flex: 1,
                border: 'none',
                padding: '12px 14px',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.82rem',
                color: 'var(--ink-black)',
                backgroundColor: 'transparent',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              style={{
                border: 'none',
                borderLeft: '1px solid var(--line-gray)',
                backgroundColor: 'var(--bg-cream-alt)',
                color: 'var(--ink-black)',
                padding: '12px 16px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background-color 0.2s ease'
              }}
            >
              {subscribed ? <CheckCircle2 size={16} style={{ color: '#22c55e' }} /> : <ArrowRight size={16} />}
            </button>
          </form>
        </div>

        {/* Row 2, Col 2: ADDRESS / LOCATION */}
        <div style={{
          padding: '32px 28px',
          borderRight: '1px solid var(--line-gray)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '20px'
        }}>
          <div>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: 'var(--label-gray)',
              letterSpacing: '0.08em',
              marginBottom: '12px'
            }}>
              ADDRESS
            </div>
            <p style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.02rem',
              fontWeight: '700',
              lineHeight: 1.4,
              color: 'var(--ink-black)',
              margin: 0
            }}>
              TN Public Works Dept Benchmark HQ, Chennai / Coimbatore, India
            </p>
          </div>

          <div style={{
            fontFamily: 'var(--font-headline)',
            fontSize: '0.92rem',
            fontWeight: '700',
            color: 'var(--ink-black)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }} onClick={() => handleNavClick('resources')}>
            <span>Direction & Anchors</span>
            <ArrowRight size={14} style={{ color: 'var(--accent-orange)' }} />
          </div>
        </div>

        {/* Row 2, Col 3: INQUIRIES (Split sub-cells like reference image) */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid var(--line-gray)'
        }}>
          {/* Sub-cell 1: NEW BUSINESS */}
          <div style={{
            padding: '24px 28px',
            borderBottom: '1px solid var(--line-gray)',
            flex: 1
          }}>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: 'var(--label-gray)',
              letterSpacing: '0.08em',
              marginBottom: '8px'
            }}>
              NEW BUSINESS
            </div>
            <a href="mailto:business@buildcost.ai" style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.02rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              textDecoration: 'none'
            }}>
              business@buildcost.ai
            </a>
          </div>

          {/* Sub-cell 2: GENERAL INQUIRIES */}
          <div style={{
            padding: '24px 28px',
            flex: 1
          }}>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: 'var(--label-gray)',
              letterSpacing: '0.08em',
              marginBottom: '8px'
            }}>
              GENERAL INQUIRIES
            </div>
            <a href="mailto:hello@buildcost.ai" style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '1.02rem',
              fontWeight: '700',
              color: 'var(--accent-orange)',
              textDecoration: 'none'
            }}>
              hello@buildcost.ai
            </a>
          </div>
        </div>

        {/* Row 2, Col 4: CONNECT / SOCIAL Grid (Matches reference image) */}
        <div style={{
          padding: '32px 28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            fontWeight: '700',
            textTransform: 'uppercase',
            color: 'var(--label-gray)',
            letterSpacing: '0.08em'
          }}>
            CONNECT & LINKS
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '12px 16px'
          }}>
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '0.98rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              Swagger Docs
            </a>

            <a href="http://localhost:8000/health" target="_blank" rel="noopener noreferrer" style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '0.98rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              Health Check
            </a>

            <span onClick={() => handleNavClick('resources')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '0.98rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer'
            }}>
              WPI Datasets
            </span>

            <span onClick={() => handleNavClick('engine')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '0.98rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer'
            }}>
              Fair Price API
            </span>

            <span onClick={() => handleNavClick('about')} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '0.98rem',
              fontWeight: '700',
              color: 'var(--ink-black)',
              cursor: 'pointer'
            }}>
              System Specs
            </span>

            <span onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} style={{
              fontFamily: 'var(--font-headline)',
              fontSize: '0.98rem',
              fontWeight: '700',
              color: 'var(--accent-orange)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              Back to Top <ArrowUp size={12} />
            </span>
          </div>
        </div>

      </div>

      {/* Bottom Legal Copyright Bar */}
      <div style={{
        backgroundColor: 'var(--bg-cream-alt)',
        borderTop: '1px solid var(--line-gray)',
        padding: '16px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.76rem',
        color: 'var(--label-gray-dark)'
      }}>
        <span>© 2026 BUILDCOST AI • PWD REFERENCE BENCHMARK & WPI TIME-SERIES MODELING</span>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span>FASTAPI 3.13</span>
          <span>•</span>
          <span>SQLITE BUILDCOST.DB</span>
          <span>•</span>
          <span style={{ color: 'var(--accent-orange)', fontWeight: '700' }}>STATUS: OPERATIONAL</span>
        </div>
      </div>
    </footer>
  );
}
