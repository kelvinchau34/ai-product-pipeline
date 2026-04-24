function IssueBadge({ issue }) {
  if (!issue) {
    return null;
  }

  const label = issue.code?.replace(/_/g, ' ') || 'issue';
  return (
    <span className={`issue-badge issue-${issue.severity || 'warning'}`} title={issue.message}>
      {label}
    </span>
  );
}

export default IssueBadge;
