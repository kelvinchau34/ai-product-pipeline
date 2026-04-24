const ACTIONS = [
  { value: 'vendor', label: 'Apply vendor', needsValue: true, placeholder: 'Vendor name' },
  { value: 'product_type', label: 'Apply product type', needsValue: true, placeholder: 'Product type' },
  { value: 'tags', label: 'Add tags', needsValue: true, placeholder: 'tag-1, tag-2' },
  { value: 'lead_time', label: 'Apply lead time note', needsValue: true, placeholder: 'e.g. 4-6 weeks' },
  { value: 'generate_handles', label: 'Generate handles', needsValue: false },
  { value: 'mark_ready', label: 'Mark as ready', needsValue: false },
];

function BulkActionToolbar({
  selectedCount,
  totalCount,
  actionType,
  actionValue,
  onActionChange,
  onValueChange,
  onApply,
  onClear,
  warning,
}) {
  const currentAction = ACTIONS.find((action) => action.value === actionType);
  const needsValue = currentAction?.needsValue;
  const isApplyDisabled = selectedCount === 0 || !actionType || (needsValue && !actionValue.trim());

  return (
    <section className="panel bulk-toolbar">
      <div>
        <p className="eyebrow">Step 3</p>
        <h2>Bulk actions</h2>
        <p className="panel-subtitle">
          Apply quick fixes to multiple products. Changes are local-only for now.
        </p>
      </div>
      <div className="bulk-controls">
        <div className="bulk-status">
          <strong>{selectedCount}</strong>
          <span>of {totalCount} selected</span>
        </div>
        <div className="bulk-actions">
          <select
            className="bulk-select"
            value={actionType}
            onChange={(event) => onActionChange(event.target.value)}
          >
            <option value="">Select action</option>
            {ACTIONS.map((action) => (
              <option key={action.value} value={action.value}>
                {action.label}
              </option>
            ))}
          </select>
          {needsValue ? (
            <input
              type="text"
              className="bulk-input"
              placeholder={currentAction?.placeholder || 'Enter value'}
              value={actionValue}
              onChange={(event) => onValueChange(event.target.value)}
            />
          ) : null}
          <button type="button" className="submit-button" onClick={onApply} disabled={isApplyDisabled}>
            Apply
          </button>
          <button type="button" className="ghost-button" onClick={onClear}>
            Clear selection
          </button>
        </div>
        {warning ? <p className="bulk-warning">{warning}</p> : null}
      </div>
    </section>
  );
}

export default BulkActionToolbar;
