import React, { useState } from 'react';
import { Calculator, AlertCircle, Loader2, CheckSquare, Square } from 'lucide-react';

const AVAILABLE_MATERIALS = [
  { id: 'steel', label: 'Steel (MT)', color: '#6366f1' },
  { id: 'cement', label: 'Cement (Bags/MT)', color: '#0ea5e9' },
  { id: 'sand', label: 'Sand (Cu.M)', color: '#f59e0b' },
  { id: 'brick', label: 'Bricks (Nos)', color: '#ef4444' },
  { id: 'gravel', label: 'Gravel (Cu.M)', color: '#10b981' },
];

export default function InputForm({ onSubmit, loading, apiError }) {
  const [sqft, setSqft] = useState(1000);
  const [targetMaterials, setTargetMaterials] = useState(['steel', 'cement', 'sand', 'brick', 'gravel']);
  const [clientError, setClientError] = useState(null);

  const toggleMaterial = (matId) => {
    if (targetMaterials.includes(matId)) {
      if (targetMaterials.length === 1) {
        setClientError('At least one material must be selected.');
        return;
      }
      setClientError(null);
      setTargetMaterials(targetMaterials.filter((m) => m !== matId));
    } else {
      setClientError(null);
      setTargetMaterials([...targetMaterials, matId]);
    }
  };

  const handleSelectAll = () => {
    setClientError(null);
    setTargetMaterials(AVAILABLE_MATERIALS.map((m) => m.id));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setClientError(null);

    const parsedSqft = Number(sqft);
    // Client-side validation matching API's gt=0 validation
    if (isNaN(parsedSqft) || parsedSqft <= 0) {
      setClientError('Square footage must be a positive integer greater than 0.');
      return;
    }

    if (!targetMaterials || targetMaterials.length === 0) {
      setClientError('Please select at least one material to include in the BOM optimization.');
      return;
    }

    onSubmit({ sqft: parsedSqft, target_materials: targetMaterials });
  };

  return (
    <div className="card input-card">
      <div className="card-header">
        <Calculator className="header-icon" size={22} />
        <div>
          <h2>Procurement Optimization Inputs</h2>
          <p className="subtitle">Enter build area and target Bill of Materials parameters</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form-container">
        <div className="form-group">
          <label htmlFor="sqft-input" className="form-label">
            Project Build Area (Square Feet) <span className="required-star">*</span>
          </label>
          <div className="input-wrapper">
            <input
              id="sqft-input"
              type="number"
              min="-10000"
              step="1"
              value={sqft}
              onChange={(e) => setSqft(e.target.value)}
              placeholder="e.g. 1000"
              className={`text-input ${clientError ? 'input-invalid' : ''}`}
              disabled={loading}
            />
            <span className="input-unit">sq. ft.</span>
          </div>
          <small className="help-text">Must be a positive integer greater than 0.</small>
        </div>

        <div className="form-group">
          <div className="materials-header">
            <label className="form-label">Target Materials Selection</label>
            <button
              type="button"
              className="btn-select-all"
              onClick={handleSelectAll}
              disabled={loading || targetMaterials.length === AVAILABLE_MATERIALS.length}
            >
              Select All
            </button>
          </div>

          <div className="materials-checkbox-grid">
            {AVAILABLE_MATERIALS.map((mat) => {
              const isChecked = targetMaterials.includes(mat.id);
              return (
                <div
                  key={mat.id}
                  className={`checkbox-chip ${isChecked ? 'active' : ''}`}
                  onClick={() => !loading && toggleMaterial(mat.id)}
                >
                  {isChecked ? (
                    <CheckSquare size={18} style={{ color: mat.color }} />
                  ) : (
                    <Square size={18} className="checkbox-empty" />
                  )}
                  <span className="chip-label">{mat.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Client side error banner */}
        {clientError && (
          <div className="alert alert-warning" role="alert">
            <AlertCircle size={18} />
            <span>{clientError}</span>
          </div>
        )}

        {/* API error banner (422 / 500 / network failure) */}
        {apiError && (
          <div className="alert alert-danger" role="alert">
            <AlertCircle size={20} className="alert-icon" />
            <div>
              <strong>API Error Response:</strong>
              <div className="error-detail-text">{apiError}</div>
            </div>
          </div>
        )}

        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="spin-icon" size={18} />
              <span>Evaluating 12-Month Trajectories...</span>
            </>
          ) : (
            <>
              <Calculator size={18} />
              <span>Predict Optimal Build Window</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
