import React, { useState, useEffect, useRef } from 'react';
import { HardHat, ArrowRight, User, LogOut, LogIn, Cpu } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function HeaderNav({ activeTab = 'home', onTabChange, onOpenAuthModal }) {
  const [navVisible, setNavVisible] = useState(true);
  const lastScrollY = useRef(0);
  const { user, isAuthenticated, logout } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY <= 10) {
        setNavVisible(true);
      } else if (currentScrollY > lastScrollY.current + 5) {
        setNavVisible(false);
      } else if (currentScrollY < lastScrollY.current - 5) {
        setNavVisible(true);
      }

      lastScrollY.current = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavClick = (tab) => {
    if (onTabChange) {
      onTabChange(tab);
    }
  };

  return (
    <div className="hero-nav-wrapper">
      <header className={`hero-top-nav ${navVisible ? 'nav-visible' : 'nav-hidden'}`}>
        <div
          className="hero-brand-col"
          onClick={() => handleNavClick('home')}
          style={{ cursor: 'pointer' }}
          title="Return to Home Dashboard"
        >
          <div className="hero-brand-icon">
            <HardHat size={24} />
          </div>
          <span className="hero-brand-name">BUILDCOST AI</span>
        </div>

        <div className="hero-nav-cols">
          <div
            className={`hero-nav-cell bracket-cell ${activeTab === 'engine' ? 'active-nav-cell' : ''}`}
            onClick={() => handleNavClick('engine')}
            title="Procurement Engine Interactive Workbench"
          >
            <Cpu size={14} style={{ color: 'var(--accent-orange)' }} />
            <span>ENGINE</span>
          </div>

          <div
            className={`hero-nav-cell ${activeTab === 'product' ? 'active-nav-cell' : ''}`}
            onClick={() => handleNavClick('product')}
          >
            <span>PRODUCT</span>
          </div>

          <div
            className={`hero-nav-cell bracket-cell ${activeTab === 'pricing' ? 'active-nav-cell' : ''}`}
            onClick={() => handleNavClick('pricing')}
          >
            <span>PRICING</span>
          </div>

          <div
            className={`hero-nav-cell ${activeTab === 'resources' ? 'active-nav-cell' : ''}`}
            onClick={() => handleNavClick('resources')}
          >
            <span>RESOURCES</span>
          </div>

          <div
            className={`hero-nav-cell bracket-cell ${activeTab === 'about' ? 'active-nav-cell' : ''}`}
            onClick={() => handleNavClick('about')}
          >
            <span>ABOUT</span>
          </div>

          {/* User Auth Status Cell */}
          {isAuthenticated ? (
            <div
              className="hero-nav-cell"
              style={{ color: 'var(--ink-black)', gap: '6px' }}
              title={`Logged in as ${user?.email}`}
            >
              <User size={14} style={{ color: 'var(--accent-orange)' }} />
              <span style={{ maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 700 }}>
                {user?.name || user?.email?.split('@')[0]}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  logout();
                }}
                title="Log Out"
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#ef4444',
                  cursor: 'pointer',
                  padding: '2px 4px',
                  display: 'flex',
                  alignItems: 'center',
                  marginLeft: '4px'
                }}
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <div
              className="hero-nav-cell"
              onClick={onOpenAuthModal}
              style={{ color: 'var(--accent-orange)', cursor: 'pointer', gap: '6px' }}
              title="Engineer Sign In / Register"
            >
              <LogIn size={14} />
              <span>SIGN IN</span>
            </div>
          )}

          <div
            className="hero-nav-cell cta-cell"
            onClick={() => handleNavClick('engine')}
          >
            <span>OPTIMIZE NOW</span>
            <ArrowRight size={14} className="cell-arrow" />
          </div>
        </div>
      </header>
    </div>
  );
}
