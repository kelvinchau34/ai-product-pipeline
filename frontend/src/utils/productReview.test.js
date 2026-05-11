import { applyProductEdits } from './productReview';

describe('applyProductEdits', () => {
  it('updates normalized and shopify fields', () => {
    const product = {
      product_id: 'row-1',
      normalized_record: { title: 'Old', sku: 'OLD', vendor: '' },
      shopify_row: { Title: 'Old', 'Variant SKU': 'OLD' },
      issues: [{ code: 'missing_vendor', severity: 'warning' }],
      status: 'needs_review',
    };

    const updated = applyProductEdits(product, {
      title: 'New',
      sku: 'NEW',
      vendor: 'Vendor',
      product_type: 'Chair',
      tags: 'tag-1',
      body_html: '<p>Body</p>',
      handle: 'new',
      images: ['https://example.com/image.jpg'],
      seo_title: 'New',
      seo_description: 'Desc',
    });

    expect(updated.normalized_record.title).toBe('New');
    expect(updated.shopify_row.Title).toBe('New');
    expect(updated.issues.length).toBe(0);
    expect(updated.status).toBe('ready');
  });
});
