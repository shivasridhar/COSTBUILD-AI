import React from 'react';
import { ArrowRight } from 'lucide-react';
import Text3DFlip from './ui/Text3DFlip';

export default function HeroLanding({ onOpenProjects, onScrollToWorkbench, onLaunchEngine }) {
  const headlineLines = [
    <h1 key="1" className="hero-massive-headline">AI-POWERED CONSTRUCTION PROCUREMENT</h1>,
    <h1 key="2" className="hero-massive-headline">OPTIMIZING BILL OF MATERIALS PURCHASING</h1>,
    <h1 key="3" className="hero-massive-headline">
      <span className="orange-accent-dot"></span>WITH REAL-TIME PWD & WPI FORECASTS
    </h1>
  ];

  const handleOptimizeClick = () => {
    if (onLaunchEngine) {
      onLaunchEngine();
    } else if (onScrollToWorkbench) {
      onScrollToWorkbench();
    }
  };

  return (
    <div className="hero-landing-container">

      {/* 2. Main Hero Image Frame */}
      <div className="hero-drafting-frame">
        {/* Central CAD Architectural Model Rendering Image */}
        <div className="empty-image-canvas">
          <img
            src="/costbuild_hero.jpg"
            alt="BuildCost AI Architectural Concrete Model Rendering"
            className="hero-cad-image"
          />
        </div>
      </div>

      {/* 3. Lower 3-Column Section */}
      <div className="hero-bottom-grid">
        {/* Left Column: 3D Text Flip Animation Container */}
        <div className="hero-left-col">
          <Text3DFlip
            lines={headlineLines}
            interval={3200}
            rotateDirection="top"
            showIndicators={false}
          />
        </div>

        {/* Middle Column: Description Block & Bottom Action Bar */}
        <div className="hero-middle-col">
          <div className="hero-description-text">
            BuildCost AI reviews your model, identifies cost anomalies, and proposes optimal procurement windows. Upon approval, it calculates dynamic 12-month WPI drift trajectories.
          </div>

          {/* Bottom Action Bar */}
          <div className="hero-action-bar">
            <span className="action-bar-text">This platform uses real-time PWD anchors. <a href="#guide" onClick={onScrollToWorkbench} className="learn-more-link">LEARN MORE</a></span>
            <div className="action-bar-buttons">
              <button onClick={handleOptimizeClick} className="btn-hero-primary">
                OPTIMIZE
              </button>
              <button onClick={onOpenProjects} className="btn-hero-ghost">
                VIEW PROJECTS
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Discover More */}
        <div className="hero-right-col" onClick={handleOptimizeClick}>
          <div className="discover-more-box">
            <span className="discover-text">LAUNCH ENGINE</span>
            <ArrowRight size={16} className="discover-arrow" />
          </div>
        </div>
      </div>
    </div>
  );
}
