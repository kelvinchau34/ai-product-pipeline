import { INTERNAL_FIELDS } from '../utils/columnMapping';

function ColumnMappingPanel({ headers, mapping, onChange, onConfirm, onApplyPreset, error }) {
  return (
    <section className="panel mapping-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Step 2</p>
          <h2>Map vendor columns</h2>
          <p className="panel-subtitle">
            Match vendor columns to internal product fields. Required fields are marked.
          </p>
        </div>
        <button type="button" className="ghost-button" onClick={onApplyPreset}>
          Use WOUD preset
        </button>
      </div>

      {error ? <div className="notice warning">{error}</div> : null}

      <div className="mapping-grid">
        {INTERNAL_FIELDS.map((field) => (
          <label key={field.key} className={field.required ? 'mapping-required' : ''}>
            <span>
              {field.label}
              {field.required ? <strong>Required</strong> : <em>Optional</em>}
            </span>
            <select
              value={mapping[field.key] || ''}
              onChange={(event) => onChange(field.key, event.target.value)}
            >
              <option value="">Not mapped</option>
              {headers.map((header) => (
                <option key={header} value={header}>
                  {header}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>

      <div className="mapping-actions">
        <button type="button" className="submit-button" onClick={onConfirm}>
          Continue to processing
        </button>
        <p className="panel-subtitle">
          Mapping is stored locally until backend presets are available.
        </p>
      </div>
    </section>
  );
}

export default ColumnMappingPanel;
