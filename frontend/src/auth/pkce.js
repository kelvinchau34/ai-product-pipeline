/**
 * PKCE (Proof Key for Code Exchange) helpers for OAuth 2.0.
 *
 * Why PKCE?
 * A browser SPA can't safely store a client_secret (anyone can read it).
 * PKCE proves that the browser which started the login is the same one
 * completing it — without ever sending a secret over the wire.
 *
 * Flow:
 *  1. Generate a random code_verifier
 *  2. SHA-256 hash it → code_challenge
 *  3. Send code_challenge in the /authorize redirect (safe to expose)
 *  4. When exchanging the auth code for tokens, send the original code_verifier
 *  5. Cognito re-hashes the verifier and checks it matches the challenge
 */

/** Random 43-char base64url string — the "secret" that never leaves the browser. */
export function generateCodeVerifier() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64urlEncode(array);
}

/** SHA-256 hash of the verifier, base64url-encoded. Sent in the authorize URL. */
export async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return base64urlEncode(new Uint8Array(digest));
}

function base64urlEncode(bytes) {
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

/**
 * Build the Cognito /oauth2/authorize URL.
 * Saves the code_verifier to sessionStorage so CallbackPage can retrieve it.
 */
export async function buildAuthorizeUrl({ domain, clientId, redirectUri }) {
  const verifier = generateCodeVerifier();
  const challenge = await generateCodeChallenge(verifier);

  // Store verifier — must survive the full-page redirect to Google and back
  sessionStorage.setItem('pkce_verifier', verifier);

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: 'openid email profile',
    code_challenge: challenge,
    code_challenge_method: 'S256',
  });

  return `${domain}/oauth2/authorize?${params.toString()}`;
}

/**
 * Exchange the auth code for tokens at the Cognito token endpoint.
 * This is a server-side-style POST from the browser — no client_secret needed (PKCE).
 */
export async function exchangeCodeForTokens({ domain, clientId, redirectUri, code, codeVerifier }) {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: clientId,
    redirect_uri: redirectUri,
    code,
    code_verifier: codeVerifier,
  });

  const res = await fetch(`${domain}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Token exchange failed: ${text}`);
  }

  return res.json();
  // { id_token, access_token, refresh_token, expires_in, token_type }
}

/** Build the Cognito logout URL to fully clear the Cognito session. */
export function buildLogoutUrl({ domain, clientId, logoutUri }) {
  const params = new URLSearchParams({
    client_id: clientId,
    logout_uri: logoutUri,
  });
  return `${domain}/logout?${params.toString()}`;
}

/**
 * Decode the JWT id_token payload (no signature verification — Cognito Authorizer
 * handles that on the backend; here we only need the claims for UI rendering).
 */
export function decodeIdToken(idToken) {
  try {
    const [, payload] = idToken.split('.');
    // base64url → base64 → JSON
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch {
    return null;
  }
}
