import { useEffect, useMemo, useRef, useState } from 'react';
import BeforeAfterPreview from './BeforeAfterPreview';
import IssueBadge from './IssueBadge';
import StatusBadge from './StatusBadge';
import { applyProductEdits, toEditableState, updateImages } from '../utils/productReview';

function ProductReviewDrawer({ product, onClose, onSave }) {
  const [editMode, setEditMode] = useState(false);
  const [localEdits, setLocalEdits] = useState({});
  const [saveNotice, setSaveNotice] = useState('');
  const prevProductIdRef = useRef(null);

  const normalized = product?.normalized_record || {};
  const shopifyRow = product?.shopify_row || {};
  const rawRecord = product?.raw_record || {};

  useEffect(() => {
    if (product) {
      const isNewProduct = product.product_id !== prevProductIdRef.current;
      prevProductIdRef.current = product.product_id;
      setEditMode(false);
      if (isNewProduct) {
        setSaveNotice('');
      }
      setLocalEdits(toEditableState(product));
    }
  }, [product]);

  const issues = useMemo(() => product?.issues || [], [product]);
  const issueCount = issues.length;
  const vendorInfoText = rawRecord.Description || rawRecord['Product Text'] || '';
  const shopifyInfoText = shopifyRow['Body (HTML)'] || '';

  function handleSave() {
    const updated = applyProductEdits(product, {
      ...localEdits,
      images: localEdits.images,
    });
    if (onSave) {
      onSave(updated);
    }
    setSaveNotice('Saved locally. Backend persistence is not enabled yet.');
    setEditMode(false);
  }

  if (!product) {
    return null;
  }

  return (
    <div className="drawer-overlay" role="dialog" aria-modal="true">
      <div className="drawer">
        <div className="drawer-topbar">
          <button className="back-button" type="button" onClick={onClose}>
            ← Back to products
          </button>
          <div className="drawer-actions">
            <button
              type="button"
              className="ghost-button"
              onClick={() => setEditMode((current) => !current)}
            >
              {editMode ? 'Stop editing' : 'Edit fields'}
            </button>
            <button
              type="button"
              className="submit-button drawer-submit"
              onClick={handleSave}
              disabled={!editMode}
            >
              Save edits
            </button>
          </div>
        </div>

        <div className="drawer-header">
          <div>
            <p className="eyebrow">Product review</p>
            <h2>{normalized.title || 'Untitled product'}</h2>
            <div className="drawer-meta">
              <StatusBadge status={product.status} />
              <span>{issueCount} issues</span>
            </div>
          </div>
        </div>

        {saveNotice ? <div className="notice warning">{saveNotice}</div> : null}

        <section className="drawer-section">
          <h3>Issues</h3>
          {issues.length ? (
            <ul className="issue-list">
              {issues.map((issue, index) => (
                <li className="issue-item" key={`${product.product_id}-issue-${index}`}>
                  <IssueBadge issue={issue} />
                  <div>
                    <strong>{issue.field || 'General'}</strong>
                    <span className="issue-severity">{issue.severity || 'warning'}</span>
                    <span>{issue.message || 'Issue detected'}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-state">No issues detected.</p>
          )}
        </section>

        <div className="drawer-grid">
          <div className="drawer-column">
            <section className="drawer-section">
              <h3>Original vendor data</h3>
              <table className="vendor-table">
                <tbody>
                  {[
                    'Item no.', 'Description', 'Description 2', 'EAN',
                    'Category', 'Materials', 'Colour', 'Weight',
                    'Length mm', 'Width mm', 'Height mm',
                    'DE RRP incl. VAT (EUR)', 'Item status',
                    'Packshot 1', 'Packshot 2', 'Lifestyle 1',
                  ].filter((key) => rawRecord[key] != null && rawRecord[key] !== '' && String(rawRecord[key]).toLowerCase() !== 'nan')
                    .map((key) => (
                      <tr key={key}>
                        <th>{key}</th>
                        <td>{String(rawRecord[key])}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </section>
          </div>
          <div className="drawer-column">
            <section className="drawer-section">
              <h3>Shopify-ready output</h3>
              <div className="edit-grid">
                {[
                  { key: 'title', label: 'Title' },
                  { key: 'handle', label: 'Handle' },
                  { key: 'vendor', label: 'Vendor' },
                  { key: 'product_type', label: 'Product type' },
                  { key: 'tags', label: 'Tags' },
                ].map((field) => (
                  <label key={field.key}>
                    <span>{field.label}</span>
                    <input
                      type="text"
                      value={localEdits[field.key] || ''}
                      disabled={!editMode}
                      onChange={(event) =>
                        setLocalEdits((current) => ({
                          ...current,
                          [field.key]: event.target.value,
                        }))
                      }
                    />
                  </label>
                ))}
              </div>

              <div className="textarea-field">
                <span>Body HTML / Info section</span>
                {editMode ? (
                  <textarea
                    rows={6}
                    value={localEdits.body_html || ''}
                    onChange={(event) =>
                      setLocalEdits((current) => ({
                        ...current,
                        body_html: event.target.value,
                      }))
                    }
                  />
                ) : (
                  <div
                    className="body-html-preview"
                    // eslint-disable-next-line react/no-danger
                    dangerouslySetInnerHTML={{ __html: localEdits.body_html || '<em>No description</em>' }}
                  />
                )}
              </div>

              <label className="textarea-field">
                <span>Image URLs (one per line)</span>
                <textarea
                  rows={4}
                  value={localEdits.image_text || ''}
                  disabled={!editMode}
                  onChange={(event) => setLocalEdits(updateImages(localEdits, event.target.value))}
                />
              </label>

              <div className="edit-grid">
                <label>
                  <span>SEO title</span>
                  <input
                    type="text"
                    value={localEdits.seo_title || ''}
                    disabled={!editMode}
                    onChange={(event) =>
                      setLocalEdits((current) => ({
                        ...current,
                        seo_title: event.target.value,
                      }))
                    }
                  />
                </label>
                <label>
                  <span>SEO description</span>
                  <input
                    type="text"
                    value={localEdits.seo_description || ''}
                    disabled={!editMode}
                    onChange={(event) =>
                      setLocalEdits((current) => ({
                        ...current,
                        seo_description: event.target.value,
                      }))
                    }
                  />
                </label>
              </div>
            </section>

          </div>
        </div>

        <BeforeAfterPreview
          beforeTitle="Vendor info"
          afterTitle="Shopify info"
          beforeContent={vendorInfoText}
          afterContent={shopifyInfoText}
        />
      </div>
    </div>
  );
}

export default ProductReviewDrawer;
