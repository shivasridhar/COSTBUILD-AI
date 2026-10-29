import React, { useEffect, useState } from 'react';
import { getHealth } from '../api/client';
import { CheckCircle, AlertTriangle, RefreshCw } from 'lucide-react';

export default function HealthBadge() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkStatus = async () => {
    setLoading(true);
    try {
      const res = await getHealth();
      setHealth(res);
    } catch (err) {
      setHealth({ status: 'error', database_connected: false, message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === 'ok' && health?.database_connected;

  return (
    <div className="health-badge-container">
      <div className={`health-badge ${isHealthy ? 'healthy' : 'unhealthy'}`}>
        <div className="status-indicator">
          {loading ? (
            <RefreshCw className="spinner" size={13} />
          ) : isHealthy ? (
            <CheckCircle size={13} className="icon-success" />
          ) : (
            <AlertTriangle size={13} className="icon-error" />
          )}
          <span className="status-text">
            {loading
              ? 'CHECKING STATUS...'
              : isHealthy
              ? 'SYSTEM ONLINE • DB CONNECTED'
              : `SYS WARNING: ${health?.message || 'DISCONNECTED'}`}
          </span>
        </div>
        <button className="btn-refresh-status" onClick={checkStatus} title="Refresh System Health">
          <RefreshCw size={11} />
        </button>
      </div>
    </div>
  );
}
