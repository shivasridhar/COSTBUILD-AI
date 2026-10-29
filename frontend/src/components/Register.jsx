import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { UserPlus, User, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';

export default function Register({ onSwitchToLogin, onSuccess }) {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Email and password are required.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await register(email, password, name || undefined);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
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
            <UserPlus size={22} />
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
            REGISTER ACCOUNT
          </h2>
          <p style={{
            fontFamily: 'var(--font-mono)',
            color: 'var(--label-gray-dark)',
            fontSize: '0.78rem',
            textTransform: 'uppercase',
            margin: 0
          }}>
            CREATE AN ACCOUNT TO PERSIST & ISOLATE PROJECT BOMS
          </p>
        </div>

        {error && (
          <div className="error-banner" style={{ marginBottom: '20px' }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
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
              FULL NAME (OPTIONAL)
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--label-gray-dark)' }} />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Priya Sharma"
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
              PASSWORD (MIN 6 CHARS) <span style={{ color: 'var(--accent-orange)' }}>*</span>
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
              CONFIRM PASSWORD <span style={{ color: 'var(--accent-orange)' }}>*</span>
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--label-gray-dark)' }} />
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
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
            <span>{loading ? 'CREATING ACCOUNT...' : 'REGISTER & AUTO-LOGIN'}</span>
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
            ALREADY REGISTERED?{' '}
          </span>
          <button
            type="button"
            onClick={onSwitchToLogin}
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
            SIGN IN HERE
          </button>
        </div>
      </div>
    </div>
  );
}
