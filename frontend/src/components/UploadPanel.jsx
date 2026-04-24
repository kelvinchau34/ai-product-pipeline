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
  mappingRequired,
  mappingReady,
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

      {mappingRequired && !mappingReady ? (
        <div className="notice warning">Map required columns before processing.</div>
      ) : null}

      <button className="submit-button" type="submit" disabled={loading || (mappingRequired && !mappingReady)}>
        {loading ? 'Processing…' : 'Process file'}
      </button>
    </form>
  );
}

export default UploadPanel;
