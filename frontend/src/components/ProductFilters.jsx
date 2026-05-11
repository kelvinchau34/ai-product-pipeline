const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'ready', label: 'Ready' },
  { key: 'needs_review', label: 'Needs Review' },
  { key: 'missing_fields', label: 'Missing Fields' },
  { key: 'exported', label: 'Exported' },
];

function ProductFilters({ selected, onChange, counts }) {
  return (
    <section className="filters">
      {FILTERS.map((filter) => (
        <button
          key={filter.key}
          type="button"
          className={selected === filter.key ? 'filter-button active' : 'filter-button'}
          onClick={() => onChange(filter.key)}
        >
          {filter.label}
          <span>{counts?.[filter.key] ?? 0}</span>
        </button>
      ))}
    </section>
  );
}

export default ProductFilters;
