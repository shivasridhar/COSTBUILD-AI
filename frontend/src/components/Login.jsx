import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { LogIn, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';

export default function Login({ onSwitchToRegister, onSuccess }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await login(email, password);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '460px', margin: '0 auto', padding: '16px 0' }}>
      <div className="blueprint-panel" style={{
        backgroundColor: 'var(--bg-cream-alt)',
        border: '1px solid var(--line-gray)',
        padding: '32px',
        position: 'relative'
      }}>
        <span className="corner-mark top-left">+</span>
        <span className="corner-mark top-right">+</span>
        <span className="corner-mark bottom-left">+</span>
        <span className="corner-mark bottom-right">+</span>

        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '44px',
            height: '44px',
            backgroundColor: 'var(--ink-black)',
            color: 'var(--accent-orange)',
            marginBottom: '12px'
          }}>
            <LogIn size={22} />
          </div>
          <h2 style={{
            fontFamily: 'var(--font-headline)',
            color: 'var(--ink-black)',
            fontSize: '1.4rem',
            fontWeight: '800',
            textTransform: 'uppercase',
            letterSpacing: '0.02em',
            margin: '0 0 4px 0'
          }}>
            ENGINEER SIGN IN
          </h2>
          <p style={{
            fontFamily: 'var(--font-mono)',
            color: 'var(--label-gray-dark)',
            fontSize: '0.78rem',
            textTransform: 'uppercase',
            margin: 0
          }}>
            ACCESS ISOLATED PROJECT BOMS & RATE CHECKS
          </p>
        </div>

        {error && (
          <div className="error-banner" style={{ marginBottom: '20px' }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label style={{
              display: 'block',
              fontFamily: 'var(--font-mono)',
              color: 'var(--ink-black)',
              fontSize: '0.8rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '6px'
            }}>
              WORK EMAIL <span style={{ color: 'var(--accent-orange)' }}>*</span>
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--label-gray-dark)' }} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="engineer@company.com"
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  padding: '10px 12px 10px 38px',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--line-gray)',
                  color: 'var(--ink-black)',
                  fontSize: '0.9rem',
                  fontFamily: 'var(--font-body)',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label style={{
              display: 'block',
              fontFamily: 'var(--font-mono)',
              color: 'var(--ink-black)',
              fontSize: '0.8rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '6px'
            }}>
              PASSWORD <span style={{ color: 'var(--accent-orange)' }}>*</span>
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--label-gray-dark)' }} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  padding: '10px 12px 10px 38px',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--line-gray)',
                  color: 'var(--ink-black)',
                  fontSize: '0.9rem',
                  fontFamily: 'var(--font-body)',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-submit"
            style={{ marginTop: '8px' }}
          >
            <span>{loading ? 'AUTHENTICATING...' : 'SIGN IN TO WORKSPACE'}</span>
            {!loading && <ArrowRight size={16} className="btn-arrow" />}
          </button>
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '20px',
          paddingTop: '16px',
          borderTop: '1px solid var(--line-gray)'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--label-gray-dark)', fontSize: '0.8rem' }}>
            DON'T HAVE AN ENGINEER ACCOUNT?{' '}
          </span>
          <button
            type="button"
            onClick={onSwitchToRegister}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--accent-orange)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              cursor: 'pointer',
              padding: 0,
              textDecoration: 'underline'
            }}
          >
            REGISTER HERE
          </button>
        </div>
      </div>
    </div>
  );
}
