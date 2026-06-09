import { NavLink, Navigate, Outlet } from 'react-router-dom';
import { AUTH_ENABLED, useAuth } from '../auth/AuthContext';

/**
 * Authenticated layout wrapper.
 * - Redirects to /login if user is not authenticated (and auth is enabled)
 * - Renders top nav with role-aware links
 * - <Outlet /> renders the active child route (Pipeline or Hours)
 */
function PortalShell() {
  const { user, logout, isManager, loading } = useAuth();

  if (loading) {
    return <div className="login-page"><div className="callback-spinner" /></div>;
  }

  if (AUTH_ENABLED && !user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div>
      <nav className="portal-nav">
        <span className="portal-nav-brand">AI Product Pipeline</span>

        <div className="portal-nav-links">
          <NavLink
            to="/portal/pipeline"
            className={({ isActive }) =>
              isActive ? 'portal-nav-link active' : 'portal-nav-link'
            }
          >
            Product Pipeline
          </NavLink>

          <NavLink
            to="/portal/hours"
            className={({ isActive }) =>
              isActive ? 'portal-nav-link active' : 'portal-nav-link'
            }
          >
            Hours Logging
            {isManager() && <span className="portal-nav-badge">Mgr</span>}
          </NavLink>
        </div>

        <div className="portal-nav-user">
          <span title={user?.email}>{user?.name}</span>
          {isManager() && <span className="role-chip">Manager</span>}
          <button className="portal-logout-button" type="button" onClick={logout}>
            Sign out
          </button>
        </div>
      </nav>

      <Outlet />
    </div>
  );
}

export default PortalShell;
