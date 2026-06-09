import { createContext, useContext, useEffect, useState } from 'react';
import {
  buildAuthorizeUrl,
  buildLogoutUrl,
  decodeIdToken,
} from './pkce';

/**
 * Auth configuration read from Vite env vars.
 * If VITE_COGNITO_DOMAIN is not set, auth is bypassed (dev mode).
 */
const COGNITO_DOMAIN = import.meta.env.VITE_COGNITO_DOMAIN || '';
const COGNITO_CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID || '';
const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI || `${window.location.origin}/callback`;
const LOGOUT_URI = import.meta.env.VITE_LOGOUT_URI || `${window.location.origin}/`;

export const AUTH_ENABLED = Boolean(COGNITO_DOMAIN && COGNITO_CLIENT_ID);

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);      // decoded JWT claims
  const [idToken, setIdToken] = useState(null); // raw JWT (sent as Bearer token)
  const [loading, setLoading] = useState(true);

  // On mount: restore session from sessionStorage if tokens are still fresh
  useEffect(() => {
    if (!AUTH_ENABLED) {
      // Dev mode — treat everyone as a manager so all features are accessible
      setUser({ email: 'dev@local', name: 'Dev User', role: 'manager', groups: ['managers'] });
      setLoading(false);
      return;
    }

    const stored = sessionStorage.getItem('id_token');
    if (stored) {
      const claims = decodeIdToken(stored);
      // Check expiry (exp is Unix seconds)
      if (claims && claims.exp * 1000 > Date.now()) {
        setUser(normaliseClaims(claims));
        setIdToken(stored);
      } else {
        sessionStorage.removeItem('id_token');
      }
    }
    setLoading(false);
  }, []);

  /** Redirect to Cognito Hosted UI (Google login). */
  async function login() {
    const url = await buildAuthorizeUrl({
      domain: COGNITO_DOMAIN,
      clientId: COGNITO_CLIENT_ID,
      redirectUri: REDIRECT_URI,
    });
    window.location.href = url;
  }

  /** Called by CallbackPage after successful token exchange. */
  function setTokens(rawIdToken) {
    const claims = decodeIdToken(rawIdToken);
    if (!claims) throw new Error('Invalid id_token');
    sessionStorage.setItem('id_token', rawIdToken);
    setIdToken(rawIdToken);
    setUser(normaliseClaims(claims));
  }

  /** Clear local state and redirect to Cognito logout (clears Cognito session cookie). */
  function logout() {
    sessionStorage.removeItem('id_token');
    sessionStorage.removeItem('pkce_verifier');
    setUser(null);
    setIdToken(null);
    if (AUTH_ENABLED) {
      window.location.href = buildLogoutUrl({
        domain: COGNITO_DOMAIN,
        clientId: COGNITO_CLIENT_ID,
        logoutUri: LOGOUT_URI,
      });
    }
  }

  const isManager = () => user?.role === 'manager';

  return (
    <AuthContext.Provider value={{
      user,
      idToken,
      loading,
      login,
      logout,
      setTokens,
      isManager,
      cognitoDomain: COGNITO_DOMAIN,
      cognitoClientId: COGNITO_CLIENT_ID,
      redirectUri: REDIRECT_URI,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

/**
 * Normalise Cognito JWT claims into a simple user object.
 * The Pre Token Generation Lambda adds 'custom:role'.
 * 'cognito:groups' is added automatically by Cognito.
 */
function normaliseClaims(claims) {
  return {
    email: claims.email || '',
    name: claims.name || claims.email || 'User',
    role: claims['custom:role'] || 'colleague',
    groups: claims['cognito:groups'] || [],
    sub: claims.sub,
  };
}
