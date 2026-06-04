function UploadPanel({
  apiUrl,
  onApiUrlChange,
  file,
  onFileChange,
  aiEnhance,
  onAiEnhanceChange,
  dryRun,
  onDryRunChange,
  onSubmit,
  loading,
  warning,
  error,
  mappedCount,
}) {
  const selectedName = file ? file.name : 'No file selected';

  return (
    <form className="panel upload-panel" onSubmit={onSubmit}>
      <div className="panel-header">
        <div>
          <p className="eyebrow">Step 1</p>
          <h2>Upload supplier data</h2>
          <p className="panel-subtitle">Send vendor CSV or JSON to the processing API.</p>
        </div>
        <div className="status-chip">Bulk review</div>
      </div>

      <div className="field">
        <label htmlFor="apiUrl">API Gateway endpoint</label>
        <input
          id="apiUrl"
          type="url"
          placeholder="https://...execute-api....amazonaws.com/dev/process"
          value={apiUrl}
          onChange={(event) => onApiUrlChange(event.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="fileInput">Supplier file</label>
        <input
          id="fileInput"
          type="file"
          accept=".csv,.json,text/csv,application/json"
          onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
        />
        <p className="helper">{selectedName}</p>
      </div>

      {mappedCount > 0 ? (
        <div className="mapping-badge">
          <span className="mapping-badge-dot" />
          {mappedCount} columns auto-mapped
        </div>
      ) : null}

      <div className="toggles">
        <label className="toggle">
          <input
            type="checkbox"
            checked={aiEnhance}
            onChange={(event) => onAiEnhanceChange(event.target.checked)}
          />
          <span>
            <strong>AI enhance</strong>
            <small>Uses the backend AI step when enabled.</small>
          </span>
        </label>

        <label className="toggle">
          <input
            type="checkbox"
            checked={dryRun}
            onChange={(event) => onDryRunChange(event.target.checked)}
          />
          <span>
            <strong>Dry run</strong>
            <small>Skip Shopify upload and only generate the CSV.</small>
          </span>
        </label>
      </div>

      {warning ? <div className="notice warning">{warning}</div> : null}
      {error ? <div className="notice error">{error}</div> : null}

      <button className="submit-button" type="submit" disabled={loading}>
        {loading ? 'Processing…' : 'Process file'}
      </button>

      {loading ? (
        <div className="processing-status">
          <div className="progress-bar">
            <div className="progress-bar-fill" />
          </div>
          <p className="processing-label">Processing {file?.name} — this may take 10–30 seconds</p>
        </div>
      ) : null}
    </form>
  );
}

export default UploadPanel;
