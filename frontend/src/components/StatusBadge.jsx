const STATUS_LABELS = {
  ready: 'Ready',
  needs_review: 'Needs review',
  missing_fields: 'Missing fields',
  exported: 'Exported',
};

function StatusBadge({ status }) {
  const label = STATUS_LABELS[status] || 'Unknown';
  return <span className={`status-badge status-${status}`}>{label}</span>;
}

export default StatusBadge;
