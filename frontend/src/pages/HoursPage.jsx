import { useAuth } from '../auth/AuthContext';

/**
 * Working Hours Logging — placeholder.
 * Colleague view: submit fortnightly hours form.
 * Manager view: all submissions, approve/reject, export CSV.
 * Backend: DynamoDB (TimeEntries table) + Lambda CRUD functions.
 */
function HoursPage() {
  const { user, isManager } = useAuth();

  return (
    <main className="page-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Hours Logging</p>
          <h1>{isManager() ? 'Team hours overview.' : 'Log your working hours.'}</h1>
          <p className="lede">
            {isManager()
              ? 'Review, approve or reject fortnightly submissions from your team.'
              : 'Submit your fortnightly hours for manager review.'}
          </p>
        </div>
        <div className="header-card">
          <span>Signed in as</span>
          <strong>{user?.name}</strong>
          <small>{isManager() ? 'Manager' : 'Colleague'}</small>
        </div>
      </header>

      <div className="hours-placeholder panel">
        <p className="eyebrow">Coming next</p>
        <h2>Working Hours Module</h2>
        <p className="panel-subtitle">
          This module is in the implementation backlog. The backend
          design (DynamoDB table, Lambda CRUD) is documented in{' '}
          <code>docs/prd.md</code> and <code>docs/architecture.md</code>.
        </p>

        <div className="hours-features">
          {isManager() ? (
            <>
              <div className="hours-feature-card">
                <strong>All submissions</strong>
                <span>Browse every colleague's fortnightly entry, filterable by period and status.</span>
              </div>
              <div className="hours-feature-card">
                <strong>Approve / reject</strong>
                <span>One-click approval with optional comment on rejection.</span>
              </div>
              <div className="hours-feature-card">
                <strong>Export CSV</strong>
                <span>Download any period's submissions as a CSV for payroll.</span>
              </div>
            </>
          ) : (
            <>
              <div className="hours-feature-card">
                <strong>Fortnightly form</strong>
                <span>Enter daily hours for the current two-week period. Total is calculated automatically.</span>
              </div>
              <div className="hours-feature-card">
                <strong>Submission history</strong>
                <span>View your past 6 fortnights with status — Submitted, Approved, or Rejected.</span>
              </div>
              <div className="hours-feature-card">
                <strong>Resubmit on rejection</strong>
                <span>If a manager rejects your entry, you can correct and resubmit.</span>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

export default HoursPage;
