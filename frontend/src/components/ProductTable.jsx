import IssueBadge from './IssueBadge';
import StatusBadge from './StatusBadge';

function ProductTable({
  products,
  loading,
  onSelectProduct,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
}) {
  const allSelected = products.length > 0 && products.every((product) => selectedIds.has(product.product_id));

  return (
    <section className="panel table-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Step 4</p>
          <h2>Product review queue</h2>
          <p className="panel-subtitle">Review issues and open each product for details.</p>
        </div>
      </div>

      {loading ? (
        <p className="empty-state">Loading product details…</p>
      ) : products.length === 0 ? (
        <p className="empty-state">No products match this filter.</p>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={(event) => onToggleSelectAll(event.target.checked)}
                  />
                </th>
                <th>Status</th>
                <th>Title</th>
                <th>SKU</th>
                <th>Vendor</th>
                <th>Product type</th>
                <th>Issues</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => {
                const normalized = product.normalized_record || {};
                const issues = product.issues || [];
                const displayIssues = issues.slice(0, 3);
                const remainingCount = issues.length - displayIssues.length;

                return (
                  <tr key={product.product_id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(product.product_id)}
                        onChange={(event) => onToggleSelect(product.product_id, event.target.checked)}
                      />
                    </td>
                    <td>
                      <StatusBadge status={product.status} />
                    </td>
                    <td>
                      <div className="title-cell">
                        <strong>{normalized.title || 'Untitled product'}</strong>
                        <span>Row {product.row_index}</span>
                      </div>
                    </td>
                    <td>{normalized.sku || '—'}</td>
                    <td>{normalized.vendor || '—'}</td>
                    <td>{normalized.product_type || '—'}</td>
                    <td>
                      <div className="issue-stack">
                        {displayIssues.map((issue, index) => (
                          <IssueBadge issue={issue} key={`${product.product_id}-issue-${index}`} />
                        ))}
                        {remainingCount > 0 ? (
                          <span className="issue-more">+{remainingCount} more</span>
                        ) : null}
                      </div>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="table-action"
                        onClick={() => onSelectProduct(product)}
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default ProductTable;
