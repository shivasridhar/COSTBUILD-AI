import React, { useState } from 'react';
import { createPhase, updatePhase } from '../api/client';
import { Layers, X, Loader2, AlertCircle, Calendar, Hash } from 'lucide-react';

export default function PhaseForm({ projectId, projectTargetMaterials = [], phaseToEdit, onClose, onPhaseSaved }) {
  const [phaseName, setPhaseName] = useState(phaseToEdit ? phaseToEdit.phase_name : '');
  const [selectedMaterials, setSelectedMaterials] = useState(
    phaseToEdit ? phaseToEdit.materials : (projectTargetMaterials.length > 0 ? projectTargetMaterials : ['steel', 'cement'])
  );
  const [expectedStartMonth, setExpectedStartMonth] = useState(
    phaseToEdit ? String(phaseToEdit.expected_start_month) : '0'
  );
  const [sequenceOrder, setSequenceOrder] = useState(
    phaseToEdit ? String(phaseToEdit.sequence_order) : '1'
  );

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const toggleMaterial = (matId) => {
    setSelectedMaterials((prev) =>
      prev.includes(matId) ? prev.filter((m) => m !== matId) : [...prev, matId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!phaseName.trim()) {
      setError('Please enter a phase name (e.g. Foundation, Structure, Electrical Fit-Out).');
      return;
    }

    if (selectedMaterials.length === 0) {
      setError('Please select at least one material for this phase.');
      return;
    }

    const startMonthNum = parseInt(expectedStartMonth, 10);
    if (isNaN(startMonthNum) || startMonthNum < 0) {
      setError('Expected start month must be a valid non-negative integer (0 = immediate).');
      return;
    }

    const seqNum = parseInt(sequenceOrder, 10);
    if (isNaN(seqNum) || seqNum < 1) {
      setError('Sequence order must be a positive integer (e.g. 1, 2, 3).');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        phase_name: phaseName.trim(),
        materials: selectedMaterials,
        expected_start_month: startMonthNum,
        sequence_order: seqNum,
      };

      let result;
      if (phaseToEdit) {
        result = await updatePhase(projectId, phaseToEdit.id, payload);
      } else {
        result = await createPhase(projectId, payload);
      }

      if (onPhaseSaved) onPhaseSaved(result);
      if (onClose) onClose();
    } catch (err) {
      setError(err.message || 'Failed to save construction phase.');
    } finally {
      setSaving(false);
    }
  };

  const availableMaterials = projectTargetMaterials.length > 0
    ? projectTargetMaterials
    : ['steel', 'cement', 'sand', 'brick', 'gravel', 'wiring'];

  return (
    <div className="inner-modal-backdrop">
      <div className="inner-modal-card">
        <div className="inner-modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers className="header-icon" size={20} />
            <h3>{phaseToEdit ? 'Edit Construction Phase' : 'Add Construction Phase'}</h3>
          </div>
          <button onClick={onClose} className="btn-close-inner">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="create-project-form">
          {error && (
            <div className="error-banner" style={{ marginBottom: '12px' }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="phaseName">Phase Name *</label>
            <input
              id="phaseName"
              type="text"
              placeholder="e.g. Foundation & Substructure"
              value={phaseName}
              onChange={(e) => setPhaseName(e.target.value)}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group half">
              <label htmlFor="expectedStartMonth">
                <Calendar size={13} /> Expected Start (Month) *
              </label>
              <input
                id="expectedStartMonth"
                type="number"
                min="0"
                placeholder="0 = immediate, 6 = Month 6"
                value={expectedStartMonth}
                onChange={(e) => setExpectedStartMonth(e.target.value)}
                required
              />
            </div>
            <div className="form-group half">
              <label htmlFor="sequenceOrder">
                <Hash size={13} /> Sequence Order *
              </label>
              <input
                id="sequenceOrder"
                type="number"
                min="1"
                placeholder="1, 2, 3..."
                value={sequenceOrder}
                onChange={(e) => setSequenceOrder(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Phase Material Scope (From Project Target Materials)</label>
            <div className="materials-checkbox-grid">
              {availableMaterials.map((m) => (
                <label key={m} className="checkbox-chip">
                  <input
                    type="checkbox"
                    checked={selectedMaterials.includes(m)}
                    onChange={() => toggleMaterial(m)}
                  />
                  <span style={{ textTransform: 'capitalize' }}>{m}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="inner-modal-footer">
            <button type="button" onClick={onClose} className="btn-cancel" disabled={saving}>
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn-submit-create">
              {saving ? (
                <>
                  <Loader2 className="spinner" size={16} /> Saving...
                </>
              ) : (
                phaseToEdit ? 'Update Phase' : 'Create Phase'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
