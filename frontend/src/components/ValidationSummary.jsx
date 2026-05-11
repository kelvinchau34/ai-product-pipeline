const SUMMARY_CARDS = [
  { key: 'total', label: 'Total products' },
  { key: 'ready', label: 'Ready' },
  { key: 'needs_review', label: 'Needs review' },
  { key: 'missing_fields', label: 'Missing fields' },
  { key: 'exported', label: 'Exported' },
];

function ValidationSummary({ summary, loading }) {
  return (
    <section className="panel summary-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Step 2</p>
          <h2>Validation summary</h2>
          <p className="panel-subtitle">Scan overall readiness before reviewing details.</p>
        </div>
      </div>

      {loading ? (
        <p className="empty-state">Processing records. Summary will appear here.</p>
      ) : summary ? (
        <div className="summary-grid">
          {SUMMARY_CARDS.map((card) => (
            <article className="summary-card" key={card.key}>
              <span>{card.label}</span>
              <strong>{summary[card.key] ?? 0}</strong>
            </article>
          ))}
        </div>
      ) : (
        <p className="empty-state">Run a job to see validation totals.</p>
      )}
    </section>
  );
}

export default ValidationSummary;
