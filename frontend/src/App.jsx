import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import CallbackPage from './pages/CallbackPage';
import HoursPage from './pages/HoursPage';
import LoginPage from './pages/LoginPage';
import PipelinePage from './pages/PipelinePage';
import PortalShell from './pages/PortalShell';

/**
 * Route map:
 *
 *  /              → redirect to /portal
 *  /login         → LoginPage  (public)
 *  /callback      → CallbackPage (OAuth2 redirect landing)
 *  /portal        → PortalShell (authenticated layout)
 *    /pipeline    → PipelinePage
 *    /hours       → HoursPage
 *    (index)      → redirect to /portal/pipeline
 */
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/portal" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/callback" element={<CallbackPage />} />

          <Route path="/portal" element={<PortalShell />}>
            <Route index element={<Navigate to="pipeline" replace />} />
            <Route path="pipeline" element={<PipelinePage />} />
            <Route path="hours" element={<HoursPage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/portal" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
