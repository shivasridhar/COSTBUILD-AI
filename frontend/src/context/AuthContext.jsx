import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginApi, registerApi, getMeApi } from '../api/client';

/**
 * TOKEN STORAGE SECURITY TRADEOFF NOTE:
 * We store the JWT access token in React state and persist it in `localStorage`.
 * 
 * Tradeoff comparison:
 * 1. `localStorage`: Easy to set up in client-side SPA with cross-domain or decoupled backends.
 *    Vulnerability: Susceptible to token extraction via Cross-Site Scripting (XSS) attacks.
 * 2. `httpOnly` Cookies: Immune to client-side XSS token theft.
 *    Drawback: Requires same-origin domain setup, CORS credentials handling, and Cross-Site Request Forgery (CSRF) protection.
 * 
 * For the scope of this project, `localStorage` is used as a deliberate, documented simplification.
 */

const TOKEN_KEY = 'buildcost_jwt_token';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || null);
  const [loading, setLoading] = useState(true);

  // Validate existing token on mount and handle runtime 401 unauthorized events
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const userData = await getMeApi(storedToken);
        setUser(userData);
        setToken(storedToken);
      } catch (err) {
        console.warn('Session restoration failed (malformed or expired token):', err.message);
        // Cleanly clear invalid/expired token without crashing app state
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    const handleUnauthorized = () => {
      console.warn('Received 401 Unauthorized signal. Resetting auth state.');
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
    };

    window.addEventListener('buildcost_auth_unauthorized', handleUnauthorized);
    initAuth();

    return () => {
      window.removeEventListener('buildcost_auth_unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (email, password) => {
    const data = await loginApi(email, password);
    const { access_token, user: userData } = data;
    localStorage.setItem(TOKEN_KEY, access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, name) => {
    const data = await registerApi(email, password, name);
    const { access_token, user: userData } = data;
    localStorage.setItem(TOKEN_KEY, access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!token && !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
