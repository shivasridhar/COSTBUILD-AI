import React from 'react';

/**
 * Magic UI Border Beam Component
 * Renders a glowing, animated light beam that continuously travels along the border of its parent container.
 */
export default function BorderBeam({
  size = 200,
  duration = 8,
  borderWidth = 2,
  colorFrom = '#fa3600',
  colorTo = '#ff6b00',
  delay = 0,
  className = '',
}) {
  return (
    <div
      className={`border-beam-wrapper ${className}`}
      style={{
        '--beam-size': `${size}px`,
        '--beam-duration': `${duration}s`,
        '--beam-border-width': `${borderWidth}px`,
        '--beam-color-from': colorFrom,
        '--beam-color-to': colorTo,
        '--beam-delay': `-${delay}s`,
      }}
    >
      <div className="border-beam-motion" />
    </div>
  );
}
