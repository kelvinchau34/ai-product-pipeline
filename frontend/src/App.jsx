import { useMemo, useState } from 'react';

const DEFAULT_API_URL = import.meta.env.VITE_API_URL || '';

function formatSummary(summary) {
  if (!summary) {
    return [];
  }

  return [
    { label: 'Input rows', value: summary.total_input ?? 0 },
    { label: 'Processed', value: summary.successfully_processed ?? 0 },
    { label: 'Exported', value: summary.exported ? 'Yes' : 'No' },
    { label: 'Uploaded', value: summary.uploaded ? 'Yes' : 'No' },
  ];
}

function App() {
  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [file, setFile] = useState(null);
  const [aiEnhance, setAiEnhance] = useState(false);
  const [dryRun, setDryRun] = useState(true);
  const [loading, setLoading] = useState(false);
  const [warning, setWarning] = useState('');
  const [error, setError] = useState('');
  const [payloadSummary, setPayloadSummary] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState('');

  const summaryCards = useMemo(() => formatSummary(payloadSummary), [payloadSummary]);

  async function handleSubmit(event) {
    event.preventDefault();
    setWarning('');
    setError('');
    setPayloadSummary(null);
    setDownloadUrl('');

    if (!apiUrl.trim()) {
      setError('Set VITE_API_URL or enter an API endpoint first.');
      return;
    }

    if (!file) {
      setError('Choose a CSV or JSON file to upload.');
      return;
    }

    setLoading(true);

    try {
      const fileContent = await file.text();
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_name: file.name,
          file_content: fileContent,
          export_csv: true,
          dry_run: dryRun,
          upload_shopify: !dryRun,
          ai_provider: aiEnhance ? 'openai' : 'none',
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        const message = data?.result?.final_summary?.error || data?.error || 'Request failed.';
        throw new Error(message);
      }

      const result = data?.result || {};
      const summary = result.final_summary || {};
      setPayloadSummary(summary);

      const resolvedDownloadUrl = data?.request?.download_url || result.download_url || result.output_s3_uri || '';
      setDownloadUrl(resolvedDownloadUrl);

      if (summary.error) {
        setWarning(summary.error);
      } else if (dryRun) {
        setWarning('Dry run is enabled, so Shopify upload was skipped.');
      }

      if (aiEnhance) {
        setWarning((current) => current || 'AI enhance is enabled. The backend currently uses a placeholder AI step unless configured.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected request error.');
    } finally {
      setLoading(false);
    }
  }

  const selectedName = file ? file.name : 'No file selected';

  return (
    <main className="page-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">AI Product Pipeline</p>
          <h1>Upload supplier data and generate Shopify CSV output.</h1>
          <p className="lede">
            A compact frontend for the API Gateway endpoint. Keep it clean, fast, and easy to deploy.
          </p>
        </div>
        <div className="status-chip">Static React + Vite</div>
      </section>

      <section className="layout">
        <form className="panel" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="apiUrl">API Gateway endpoint</label>
            <input
              id="apiUrl"
              type="url"
              placeholder="https://...execute-api....amazonaws.com/dev/process"
              value={apiUrl}
              onChange={(event) => setApiUrl(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="fileInput">Supplier file</label>
            <input
              id="fileInput"
              type="file"
              accept=".csv,.json,text/csv,application/json"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <p className="helper">{selectedName}</p>
          </div>

          <div className="toggles">
            <label className="toggle">
              <input
                type="checkbox"
                checked={aiEnhance}
                onChange={(event) => setAiEnhance(event.target.checked)}
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
                onChange={(event) => setDryRun(event.target.checked)}
              />
              <span>
                <strong>Dry run</strong>
                <small>Skip Shopify upload and only generate the CSV.</small>
              </span>
            </label>
          </div>

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? 'Processing…' : 'Submit'}
          </button>
        </form>

        <aside className="panel results-panel">
          <div className="panel-header">
            <h2>Result Summary</h2>
            {downloadUrl ? (
              <a className="download-link" href={downloadUrl} target="_blank" rel="noreferrer">
                Download CSV
              </a>
            ) : (
              <span className="download-link disabled">Download CSV</span>
            )}
          </div>

          {warning ? <div className="notice warning">{warning}</div> : null}
          {error ? <div className="notice error">{error}</div> : null}

          <div className="summary-grid">
            {summaryCards.length > 0 ? (
              summaryCards.map((item) => (
                <article className="summary-card" key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </article>
              ))
            ) : (
              <p className="empty-state">Run a job to see the summary here.</p>
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}

export default App;
