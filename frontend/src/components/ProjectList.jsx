import React, { useState, useEffect } from 'react';
import { getProjects, createProject, archiveProject } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Login from './Login';
import Register from './Register';
import {
  Folder,
  Plus,
  Search,
  Building2,
  MapPin,
  Calendar,
  Layers,
  Archive,
  CheckCircle2,
  Clock,
  Check,
  X,
  Loader2,
  AlertCircle,
  Lock
} from 'lucide-react';

const MATERIAL_OPTIONS = [
  { id: 'steel', label: 'Steel' },
  { id: 'cement', label: 'Cement' },
  { id: 'wiring', label: 'Wiring' },
  { id: 'sand', label: 'Sand' },
  { id: 'brick', label: 'Bricks' },
  { id: 'gravel', label: 'Gravel' }
];

export default function ProjectList({ onSelectProject, activeProjectId, onClose }) {
  const { isAuthenticated } = useAuth();
  const [authTab, setAuthTab] = useState('login'); // 'login' | 'register'

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // New Project Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newSqft, setNewSqft] = useState('1500');
  const [newRegion, setNewRegion] = useState('Tamil Nadu');
  const [newNotes, setNewNotes] = useState('');
  const [selectedMaterials, setSelectedMaterials] = useState(['steel', 'cement', 'sand', 'brick', 'gravel', 'wiring']);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState(null);

  useEffect(() => {
    if (isAuthenticated) {
      fetchProjects();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      setError(err.message || 'Failed to load projects list.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setCreateError(null);

    if (!newProjectName.trim()) {
      setCreateError('Please enter a project name.');
      return;
    }

    const sqftNum = parseFloat(newSqft);
    if (isNaN(sqftNum) || sqftNum <= 0) {
      setCreateError('Please enter a valid positive square footage.');
      return;
    }

    if (selectedMaterials.length === 0) {
      setCreateError('Please select at least one material.');
      return;
    }

    setCreating(true);
    try {
      const created = await createProject({
        name: newProjectName.trim(),
        sqft: sqftNum,
        target_materials: selectedMaterials,
        region: newRegion.trim() || undefined,
        notes: newNotes.trim() || undefined,
      });

      setShowCreateModal(false);
      // Reset form
      setNewProjectName('');
      setNewSqft('1500');
      setNewNotes('');

      await fetchProjects();
      if (onSelectProject) {
        onSelectProject(created);
      }
    } catch (err) {
      setCreateError(err.message || 'Failed to create project.');
    } finally {
      setCreating(false);
    }
  };

  const handleArchive = async (e, projectId) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to archive this project? Vendor quotes and reports will be preserved.')) {
      return;
    }
    try {
      await archiveProject(projectId);
      await fetchProjects();
    } catch (err) {
      alert('Archive failed: ' + err.message);
    }
  };

  const toggleMaterial = (matId) => {
    setSelectedMaterials((prev) =>
      prev.includes(matId) ? prev.filter((m) => m !== matId) : [...prev, matId]
    );
  };

  const filteredProjects = projects.filter((p) => {
    const matchesStatus = statusFilter === 'all' || p.status.toLowerCase() === statusFilter.toLowerCase();
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (p.region && p.region.toLowerCase().includes(searchQuery.toLowerCase())) ||
                          (p.notes && p.notes.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'in_progress':
        return <span className="status-pill status-in-progress"><Clock size={12} /> In Progress</span>;
      case 'completed':
        return <span className="status-pill status-completed"><CheckCircle2 size={12} /> Completed</span>;
      case 'archived':
        return <span className="status-pill status-archived"><Archive size={12} /> Archived</span>;
      default:
        return <span className="status-pill status-planning"><Layers size={12} /> Planning</span>;
    }
  };

  return (
    <div className="project-modal-backdrop">
      <div className="project-modal-container" style={{ maxWidth: isAuthenticated ? '900px' : '520px' }}>
        {/* Modal Header */}
        <div className="project-modal-header">
          <div className="modal-title-group">
            <div className="project-modal-icon">
              {isAuthenticated ? <Folder size={22} /> : <Lock size={22} />}
            </div>
            <div>
              <h2 className="modal-title">
                {isAuthenticated ? 'Saved Construction Projects' : 'Engineer Authentication'}
              </h2>
              <p className="modal-subtitle">
                {isAuthenticated
                  ? 'Select, manage, or create persistent project spaces'
                  : 'Sign in to access persistent project spaces & scoped BOM forecasts'}
              </p>
            </div>
          </div>
          {onClose && (
            <button onClick={onClose} className="btn-close-modal" aria-label="Close modal">
              <X size={20} />
            </button>
          )}
        </div>

        {/* Unauthenticated State: Render Login or Register Component */}
        {!isAuthenticated ? (
          <div style={{ padding: '12px 0 24px 0' }}>
            {authTab === 'login' ? (
              <Login
                onSwitchToRegister={() => setAuthTab('register')}
                onSuccess={() => {
                  fetchProjects();
                }}
              />
            ) : (
              <Register
                onSwitchToLogin={() => setAuthTab('login')}
                onSuccess={() => {
                  fetchProjects();
                }}
              />
            )}
          </div>
        ) : (
          /* Authenticated State: Projects List View */
          <>
            {/* Filter Bar */}
            <div className="project-filter-bar">
              <div className="search-input-wrapper">
                <Search size={16} className="search-icon" />
                <input
                  type="text"
                  placeholder="Search by project name, region, or notes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="project-search-input"
                />
              </div>
              <div className="status-filter-pills">
                {['all', 'planning', 'in_progress', 'completed', 'archived'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`filter-pill ${statusFilter === st ? 'active' : ''}`}
                  >
                    {st === 'all' ? 'All Status' : st.replace('_', ' ')}
                  </button>
                ))}
              </div>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn-create-project"
                style={{ marginLeft: 'auto' }}
              >
                <Plus size={16} /> New Project
              </button>
            </div>

            {/* Main Content Area */}
            {loading ? (
              <div className="projects-loading-state">
                <Loader2 className="spinner" size={28} />
                <p>Loading persistent projects database...</p>
              </div>
            ) : error ? (
              <div className="error-banner">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            ) : filteredProjects.length === 0 ? (
              <div className="empty-projects-state">
                <Building2 size={42} className="empty-icon" />
                <h3>No Projects Found</h3>
                <p>No projects match your filter criteria. Create a new project to attach forecasts and vendor quotes.</p>
                <button onClick={() => setShowCreateModal(true)} className="btn-create-project-empty">
                  <Plus size={16} /> Create First Project
                </button>
              </div>
            ) : (
              <div className="projects-grid">
                {filteredProjects.map((p) => {
                  const isActive = activeProjectId === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => {
                        if (onSelectProject) onSelectProject(p);
                        if (onClose) onClose();
                      }}
                      className={`project-card ${isActive ? 'active-project' : ''}`}
                    >
                      <div className="project-card-header">
                        <h3 className="project-card-title">{p.name}</h3>
                        {getStatusBadge(p.status)}
                      </div>

                      <div className="project-card-metrics">
                        <div className="project-metric-item">
                          <Building2 size={15} />
                          <span>{p.sqft.toLocaleString()} sq.ft</span>
                        </div>
                        {p.region && (
                          <div className="project-metric-item">
                            <MapPin size={15} />
                            <span>{p.region}</span>
                          </div>
                        )}
                        <div className="project-metric-item">
                          <Calendar size={15} />
                          <span>Updated {new Date(p.updated_at).toLocaleDateString()}</span>
                        </div>
                      </div>

                      <div className="project-card-materials">
                        <span className="materials-label">Materials:</span>
                        <div className="materials-tags">
                          {p.target_materials.map((m) => (
                            <span key={m} className="mat-tag">{m}</span>
                          ))}
                        </div>
                      </div>

                      {p.notes && (
                        <p className="project-card-notes">"{p.notes}"</p>
                      )}

                      <div className="project-card-footer">
                        {isActive ? (
                          <span className="active-indicator">
                            <Check size={14} /> Currently Active
                          </span>
                        ) : (
                          <span className="select-action">Open Project &rarr;</span>
                        )}

                        {p.status !== 'archived' && (
                          <button
                            onClick={(e) => handleArchive(e, p.id)}
                            className="btn-archive-icon"
                            title="Archive Project"
                          >
                            <Archive size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* Create Project Modal Overlay */}
        {showCreateModal && (
          <div className="inner-modal-backdrop">
            <div className="inner-modal-card">
              <div className="inner-modal-header">
                <h3>Create New Persistent Project</h3>
                <button onClick={() => setShowCreateModal(false)} className="btn-close-inner">
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleCreateSubmit} className="create-project-form">
                {createError && (
                  <div className="error-banner" style={{ marginBottom: '12px' }}>
                    <AlertCircle size={16} />
                    <span>{createError}</span>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="newProjectName">Project Name *</label>
                  <input
                    id="newProjectName"
                    type="text"
                    placeholder="e.g. Priya — Coimbatore House"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-row">
                  <div className="form-group half">
                    <label htmlFor="newSqft">Built Area (sq.ft) *</label>
                    <input
                      id="newSqft"
                      type="number"
                      min="1"
                      placeholder="1500"
                      value={newSqft}
                      onChange={(e) => setNewSqft(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group half">
                    <label htmlFor="newRegion">Region / Location</label>
                    <input
                      id="newRegion"
                      type="text"
                      placeholder="e.g. Tamil Nadu"
                      value={newRegion}
                      onChange={(e) => setNewRegion(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Target Materials Included in BOM</label>
                  <div className="materials-checkbox-grid">
                    {MATERIAL_OPTIONS.map((m) => (
                      <label key={m.id} className="checkbox-chip">
                        <input
                          type="checkbox"
                          checked={selectedMaterials.includes(m.id)}
                          onChange={() => toggleMaterial(m.id)}
                        />
                        <span>{m.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="newNotes">Engineer Notes (Optional)</label>
                  <textarea
                    id="newNotes"
                    rows="2"
                    placeholder="Client requirements, phase targets, special notes..."
                    value={newNotes}
                    onChange={(e) => setNewNotes(e.target.value)}
                  />
                </div>

                <div className="inner-modal-footer">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="btn-cancel"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="btn-submit-create"
                  >
                    {creating ? (
                      <>
                        <Loader2 className="spinner" size={16} /> Creating...
                      </>
                    ) : (
                      'Save & Open Project'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
