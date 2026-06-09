import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { exchangeCodeForTokens } from '../auth/pkce';
import { useAuth } from '../auth/AuthContext';

/**
 * Landing page after Cognito redirects back with ?code=...
 *
 * What happens here:
 *  1. Read the auth code from the URL
 *  2. Retrieve the code_verifier from sessionStorage (set before the redirect)
 *  3. POST to Cognito /oauth2/token — exchange code + verifier for JWT tokens
 *  4. Store the id_token, update auth context, redirect to /portal
 */
function CallbackPage() {
  const { setTokens, cognitoDomain, cognitoClientId, redirectUri } = useAuth();
  const navigate = useNavigate();
  const ran = useRef(false); // prevent double-invocation in React StrictMode

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    async function handleCallback() {
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const error = params.get('error');

      if (error) {
        navigate(`/login?error=${encodeURIComponent(error)}`, { replace: true });
        return;
      }

      if (!code) {
        navigate('/login', { replace: true });
        return;
      }

      const codeVerifier = sessionStorage.getItem('pkce_verifier');
      if (!codeVerifier) {
        // Verifier missing — likely page refresh mid-flow; restart
        navigate('/login', { replace: true });
        return;
      }

      try {
        const tokens = await exchangeCodeForTokens({
          domain: cognitoDomain,
          clientId: cognitoClientId,
          redirectUri,
          code,
          codeVerifier,
        });

        sessionStorage.removeItem('pkce_verifier');
        setTokens(tokens.id_token);
        navigate('/portal', { replace: true });
      } catch (err) {
        console.error('Token exchange error:', err);
        navigate('/login?error=token_exchange_failed', { replace: true });
      }
    }

    handleCallback();
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="login-page">
      <div className="login-card">
        <p className="eyebrow">Signing you in</p>
        <div className="callback-spinner" aria-label="Loading" />
        <p className="login-subtitle" style={{ marginTop: 16 }}>
          Completing sign-in — please wait…
        </p>
      </div>
    </div>
  );
}

export default CallbackPage;
