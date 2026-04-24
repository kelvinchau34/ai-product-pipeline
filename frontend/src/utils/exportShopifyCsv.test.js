import { buildExportCounts, buildExportRows, filterProductsForExport, toCsvContent } from './exportShopifyCsv';

describe('exportShopifyCsv', () => {
  const products = [
    {
      product_id: 'row-1',
      status: 'ready',
      issues: [],
      normalized_record: { title: 'Chair', sku: 'C1', images: ['https://example.com/1.jpg'] },
      shopify_row: { Title: 'Chair', 'Variant SKU': 'C1' },
    },
    {
      product_id: 'row-2',
      status: 'needs_review',
      issues: [{ severity: 'warning', code: 'missing_images' }],
      normalized_record: { title: 'Table', sku: 'T1' },
      shopify_row: { Title: 'Table', 'Variant SKU': 'T1' },
    },
    {
      product_id: 'row-3',
      status: 'missing_fields',
      issues: [{ severity: 'error', code: 'missing_title' }],
      normalized_record: { title: '', sku: '' },
      shopify_row: {},
    },
  ];

  it('filters products by export option', () => {
    const ready = filterProductsForExport(products, 'ready');
    expect(ready.length).toBe(1);

    const warnings = filterProductsForExport(products, 'include_warnings');
    expect(warnings.length).toBe(2);
  });

  it('builds export counts', () => {
    const counts = buildExportCounts(products, new Set(['row-1']));
    expect(counts.total).toBe(3);
    expect(counts.ready).toBe(1);
    expect(counts.warnings).toBe(1);
    expect(counts.blocking).toBe(1);
    expect(counts.selected).toBe(1);
  });

  it('builds CSV content', () => {
    const rows = buildExportRows(products.slice(0, 1));
    const csv = toCsvContent(rows);
    expect(csv).toContain('Handle,Title,Body (HTML)');
    expect(csv).toContain('Chair');
  });
});
