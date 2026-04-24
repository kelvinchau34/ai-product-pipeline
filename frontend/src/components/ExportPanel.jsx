const EXPORT_OPTIONS = [
  { value: 'all', label: 'All products' },
  { value: 'ready', label: 'Ready products only' },
  { value: 'selected', label: 'Selected products only' },
  { value: 'include_warnings', label: 'Products including warnings' },
];

function ExportPanel({ downloadUrl, counts, exportOption, onOptionChange, onDownload, loading }) {
  const canDownload = counts.total > 0 && !loading;

  return (
    <section className="panel export-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Step 5</p>
          <h2>Export to Shopify</h2>
          <p className="panel-subtitle">Regenerate a CSV from the current review state.</p>
        </div>
      </div>

      <div className="export-stats">
        <div>
          <span>Total products</span>
          <strong>{counts.total}</strong>
        </div>
        <div>
          <span>Ready products</span>
          <strong>{counts.ready}</strong>
        </div>
        <div>
          <span>Warnings</span>
          <strong>{counts.warnings}</strong>
        </div>
        <div>
          <span>Blocking errors</span>
          <strong>{counts.blocking}</strong>
        </div>
        <div>
          <span>Selected</span>
          <strong>{counts.selected}</strong>
        </div>
      </div>

      <div className="export-controls">
        <label>
          <span>Export option</span>
          <select value={exportOption} onChange={(event) => onOptionChange(event.target.value)}>
            {EXPORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <button className="submit-button" type="button" disabled={!canDownload} onClick={onDownload}>
          Download CSV
        </button>
        {downloadUrl ? (
          <a className="primary-link" href={downloadUrl} target="_blank" rel="noreferrer">
            Open last server export
          </a>
        ) : (
          <span className="muted">No server export yet</span>
        )}
      </div>
    </section>
  );
}

export default ExportPanel;
