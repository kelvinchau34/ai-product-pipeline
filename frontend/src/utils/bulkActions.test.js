import { buildSummaryFromProducts, generateHandle, mergeTags } from './bulkActions';

describe('bulkActions', () => {
  it('merges tags without duplicates', () => {
    expect(mergeTags('a, b', 'b, c')).toBe('a, b, c');
  });

  it('generates handles', () => {
    expect(generateHandle('Sample Chair!')).toBe('sample-chair');
  });

  it('builds summary from products', () => {
    const summary = buildSummaryFromProducts([
      { status: 'ready' },
      { status: 'needs_review' },
    ]);
    expect(summary.total).toBe(2);
    expect(summary.ready).toBe(1);
    expect(summary.needs_review).toBe(1);
  });
});
