import React from 'react';
import { Folder, ChevronDown, Plus, Sparkles, Building2, MapPin } from 'lucide-react';

export default function ProjectSelector({ activeProject, onOpenProjectList, onSwitchToStateless }) {
  return (
    <div className="project-selector-bar">
      <div className="selector-left">
        <span className="selector-label">Context:</span>
        {activeProject ? (
          <div className="active-project-pill" onClick={onOpenProjectList}>
            <Building2 size={16} className="active-project-icon" />
            <div className="active-project-info">
              <span className="active-project-name">{activeProject.name}</span>
              <span className="active-project-meta">
                {activeProject.sqft.toLocaleString()} sq.ft {activeProject.region ? `• ${activeProject.region}` : ''}
              </span>
            </div>
            <ChevronDown size={14} className="dropdown-arrow" />
          </div>
        ) : (
          <div className="stateless-pill" onClick={onOpenProjectList}>
            <Sparkles size={15} className="stateless-icon" />
            <span>Stateless (One-Off Forecast)</span>
            <ChevronDown size={14} className="dropdown-arrow" />
          </div>
        )}
      </div>

      <div className="selector-right">
        {activeProject && (
          <button
            onClick={onSwitchToStateless}
            className="btn-switch-stateless"
            title="Switch to Stateless Mode"
          >
            Clear Project Selection
          </button>
        )}
        <button
          onClick={onOpenProjectList}
          className="btn-manage-projects"
        >
          <Folder size={15} /> All Projects
        </button>
      </div>
    </div>
  );
}
