import React, { useState, useEffect, useCallback } from 'react';
import { updateProject, getPhasesSummary, getProjectProcurementStrategy } from '../api/client';
import PhaseTimeline from './PhaseTimeline';
import PhaseForm from './PhaseForm';
import ProcurementStrategyPanel from './ProcurementStrategyPanel';
import {
  Building2,
  MapPin,
  Calendar,
  Layers,
  FileText,
  Clock,
  Edit2,
  Check,
  X,
  Loader2,
  Plus
} from 'lucide-react';

export default function ProjectDetail({ project, onProjectUpdated }) {
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesText, setNotesText] = useState(project?.notes || '');
  const [savingNotes, setSavingNotes] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  // Staged procurement phases state
  const [phasesSummary, setPhasesSummary] = useState([]);
  const [strategyData, setStrategyData] = useState(null);
  const [loadingPhases, setLoadingPhases] = useState(false);
  const [phasesError, setPhasesError] = useState(null);

  // Phase modal state
  const [showPhaseModal, setShowPhaseModal] = useState(false);
  const [editingPhase, setEditingPhase] = useState(null);

  // Sync notes text when active project changes
  useEffect(() => {
    if (project) {
      setNotesText(project.notes || '');
    }
  }, [project?.id, project?.notes]);

  const loadPhasesSummary = useCallback(async () => {
    if (!project?.id) return;
    setLoadingPhases(true);
    setPhasesError(null);
    try {
      const [summary, strat] = await Promise.all([
        getPhasesSummary(project.id),
        getProjectProcurementStrategy(project.id).catch(() => null)
      ]);
      setPhasesSummary(summary);
      setStrategyData(strat);
    } catch (err) {
      setPhasesError(err.message || 'Failed to load project construction phases.');
    } finally {
      setLoadingPhases(false);
    }
  }, [project?.id]);

  useEffect(() => {
    if (project?.id) {
      loadPhasesSummary();
    }
  }, [project?.id, loadPhasesSummary]);

  if (!project) return null;

  const handleStatusChange = async (e) => {
    const newStatus = e.target.value;
    setUpdatingStatus(true);
    try {
      const updated = await updateProject(project.id, { status: newStatus });
      if (onProjectUpdated) onProjectUpdated(updated);
    } catch (err) {
      alert('Failed to update project status: ' + err.message);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleSaveNotes = async () => {
    setSavingNotes(true);
    try {
      const updated = await updateProject(project.id, { notes: notesText.trim() });
      if (onProjectUpdated) onProjectUpdated(updated);
      setEditingNotes(false);
    } catch (err) {
      alert('Failed to update notes: ' + err.message);
    } finally {
      setSavingNotes(false);
    }
  };

  const handleOpenAddPhase = () => {
    setEditingPhase(null);
    setShowPhaseModal(true);
  };

  const handleOpenEditPhase = (phase) => {
    setEditingPhase(phase);
    setShowPhaseModal(true);
  };

  const handlePhaseSaved = () => {
    loadPhasesSummary();
  };

  const handlePhaseDeleted = () => {
    loadPhasesSummary();
  };

  return (
    <section className="project-detail-banner">
      <span className="corner-mark top-left">+</span>
      <span className="corner-mark top-right">+</span>
      <span className="corner-mark bottom-left">+</span>
      <span className="corner-mark bottom-right">+</span>

      <div className="project-detail-main">
        {/* Project Header Summary */}
        <div className="project-detail-header">
          <div className="project-title-area">
            <h2 className="project-name">{project.name}</h2>
            <div className="project-status-selector">
              <select
                value={project.status}
                onChange={handleStatusChange}
                disabled={updatingStatus}
                className={`status-select status-${project.status}`}
              >
                <option value="planning">Status: Planning</option>
                <option value="in_progress">Status: In Progress</option>
                <option value="completed">Status: Completed</option>
                <option value="archived">Status: Archived</option>
              </select>
            </div>
          </div>

          <div className="project-meta-chips">
            <span className="meta-chip">
              <Building2 size={14} /> Built Area: <strong>{project.sqft.toLocaleString()} sq.ft</strong>
            </span>
            {project.region && (
              <span className="meta-chip">
                <MapPin size={14} /> Region: <strong>{project.region}</strong>
              </span>
            )}
            <span className="meta-chip">
              <Calendar size={14} /> Last Updated: <strong>{new Date(project.updated_at).toLocaleDateString()}</strong>
            </span>
            <span className="meta-chip">
              <Layers size={14} /> Phases: <strong>{phasesSummary.length}</strong>
            </span>
          </div>

          <div className="project-materials-row">
            <span className="mats-label">BOM Scope:</span>
            <div className="mats-list">
              {project.target_materials.map((m) => (
                <span key={m} className="mat-badge">{m}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Dashed Alignment Ruler */}
        <div className="ruler-line-dashed">
          <div className="ruler-segment-solid" style={{ left: '0%', width: '180px' }}></div>
          <span className="ruler-coord-label">CAD-REF: PROJ-{project.id}</span>
        </div>

        {/* Engineer Notes Section */}
        <div className="project-notes-section">
          <div className="notes-header">
            <span className="notes-label">
              <FileText size={14} /> Engineer Notes:
            </span>
            {!editingNotes && (
              <button onClick={() => setEditingNotes(true)} className="btn-edit-notes">
                <Edit2 size={12} /> Edit Notes
              </button>
            )}
          </div>

          {editingNotes ? (
            <div className="notes-edit-box">
              <textarea
                value={notesText}
                onChange={(e) => setNotesText(e.target.value)}
                placeholder="Enter client preferences, contractor details, or site constraints..."
                rows="2"
              />
              <div className="notes-edit-actions">
                <button
                  onClick={() => setEditingNotes(false)}
                  className="btn-cancel-sm"
                  disabled={savingNotes}
                >
                  <X size={14} /> Cancel
                </button>
                <button
                  onClick={handleSaveNotes}
                  className="btn-save-sm"
                  disabled={savingNotes}
                >
                  {savingNotes ? <Loader2 className="spinner" size={14} /> : <Check size={14} />} Save Notes
                </button>
              </div>
            </div>
          ) : (
            <p className="notes-display">
              {project.notes ? project.notes : <em>No notes recorded for this project yet. Click 'Edit Notes' to add.</em>}
            </p>
          )}
        </div>

        {/* Staged Construction Procurement Timeline Section */}
        <div className="project-staged-procurement-section">
          {loadingPhases ? (
            <div className="phases-loading-box">
              <Loader2 className="spinner" size={24} />
              <span>Evaluating staged construction procurement timeline...</span>
            </div>
          ) : phasesError ? (
            <div className="error-banner" style={{ marginTop: '16px' }}>
              <span>{phasesError}</span>
            </div>
          ) : (
            <>
              <PhaseTimeline
                projectId={project.id}
                phasesSummary={phasesSummary}
                onEditPhase={handleOpenEditPhase}
                onPhaseDeleted={handlePhaseDeleted}
                onAddPhaseClick={handleOpenAddPhase}
              />
              <ProcurementStrategyPanel strategyData={strategyData} />
            </>
          )}
        </div>
      </div>

      {/* Modal for Creating/Editing Phase */}
      {showPhaseModal && (
        <PhaseForm
          projectId={project.id}
          projectTargetMaterials={project.target_materials}
          phaseToEdit={editingPhase}
          onClose={() => setShowPhaseModal(false)}
          onPhaseSaved={handlePhaseSaved}
        />
      )}
    </section>
  );
}
