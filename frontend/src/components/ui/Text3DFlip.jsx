import React, { useState, useEffect } from 'react';

export default function Text3DFlip({ lines, interval = 3200, rotateDirection = 'top', showIndicators = false }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (!lines || lines.length === 0) return;
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % lines.length);
    }, interval);
    return () => clearInterval(timer);
  }, [lines, interval]);

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % lines.length);
  };

  if (!lines || lines.length === 0) return null;

  return (
    <div className="text-3d-flip-container" onClick={handleNext} title="Click to flip 3D text">
      <div className="text-3d-flip-viewport">
        {lines.map((line, idx) => {
          const isCurrent = idx === currentIndex;
          const isPrev = idx === (currentIndex - 1 + lines.length) % lines.length;

          let statusClass = 'hidden-next';
          if (isCurrent) statusClass = 'current-active';
          else if (isPrev) statusClass = 'hidden-prev';

          return (
            <div
              key={idx}
              className={`text-3d-flip-slide ${statusClass} ${rotateDirection}`}
            >
              {typeof line === 'string' ? (
                <h1 className="hero-massive-headline">{line}</h1>
              ) : (
                line
              )}
            </div>
          );
        })}
      </div>

      {/* CAD Step Line Indicators */}
      {showIndicators && (
        <div className="text-3d-flip-indicators">
          {lines.map((_, idx) => (
            <span
              key={idx}
              className={`flip-dot ${idx === currentIndex ? 'active' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                setCurrentIndex(idx);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
