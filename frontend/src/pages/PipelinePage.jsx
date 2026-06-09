import { useMemo, useState } from 'react';
import {
  BulkActionToolbar,
  ExportPanel,
  ProductFilters,
  ProductReviewDrawer,
  ProductTable,
  UploadPanel,
  ValidationSummary,
} from '../components';
import {
  applyBulkAction,
  buildSummaryFromProducts,
  canMarkReady,
} from '../utils/bulkActions';
import {
  buildExportCounts,
  buildExportRows,
  filterProductsForExport,
  toCsvContent,
} from '../utils/exportShopifyCsv';
import {
  parseCsvHeaders,
  suggestMapping,
} from '../utils/columnMapping';
import { useAuth } from '../auth/AuthContext';

const DEFAULT_API_URL = import.meta.env.VITE_API_URL || '';

function buildSummary(result) {
  if (result?.summary) return result.summary;
  if (result?.final_summary) {
    const total = result.final_summary.total_input ?? 0;
    const processed = result.final_summary.successfully_processed ?? 0;
    return {
      total,
      ready: processed,
      needs_review: 0,
      missing_fields: Math.max(total - processed, 0),
      exported: result.final_summary.exported ? processed : 0,
    };
  }
  return null;
}

function PipelinePage() {
  const { idToken } = useAuth();

  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [file, setFile] = useState(null);
  const [aiEnhance, setAiEnhance] = useState(false);
  const [dryRun, setDryRun] = useState(true);
  const [loading, setLoading] = useState(false);
  const [warning, setWarning] = useState('');
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);
  const [products, setProducts] = useState([]);
  const [downloadUrl, setDownloadUrl] = useState('');
  const [exportOption, setExportOption] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [activeProduct, setActiveProduct] = useState(null);
  const [bulkActionType, setBulkActionType] = useState('');
  const [bulkActionValue, setBulkActionValue] = useState('');
  const [bulkWarning, setBulkWarning] = useState('');
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [columnMapping, setColumnMapping] = useState({});
  const [mappingReady, setMappingReady] = useState(false);
  const [mappingError, setMappingError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setWarning(''); setError(''); setSummary(null); setProducts([]);
    setDownloadUrl(''); setExportOption('all'); setSelectedIds(new Set());
    setActiveProduct(null); setBulkActionType(''); setBulkActionValue('');
    setBulkWarning(''); setMappingReady(false); setMappingError('');

    if (!apiUrl.trim()) { setError('Set VITE_API_URL or enter an API endpoint first.'); return; }
    if (!file) { setError('Choose a CSV or JSON file to upload.'); return; }

    setLoading(true);
    try {
      const fileContent = await file.text();

      // Attach JWT Bearer token if the user is authenticated
      const headers = { 'Content-Type': 'application/json' };
      if (idToken) headers['Authorization'] = `Bearer ${idToken}`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          file_name: file.name,
          file_content: fileContent,
          export_csv: true,
          dry_run: dryRun,
          upload_shopify: !dryRun,
          ai_provider: aiEnhance ? 'openai' : 'none',
          column_mapping: mappingReady ? columnMapping : null,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.result?.final_summary?.error || data?.error || 'Request failed.');
      }

      const result = data?.result || {};
      setSummary(buildSummary(result));
      setDownloadUrl(
        result?.output?.download_url ||
        result?.output?.csv_key ||
        data?.request?.download_url ||
        result?.download_url ||
        result?.output_s3_uri ||
        ''
      );
      setProducts(
        (result.products || []).map((p, i) => ({
          ...p,
          product_id: p.product_id || `row-${p.row_index ?? i + 1}`,
        }))
      );

      if (result?.final_summary?.error) setWarning(result.final_summary.error);
      else if (dryRun) setWarning('Dry run is enabled, so Shopify upload was skipped.');
      if (aiEnhance) setWarning((c) => c || 'AI enhance is enabled but the backend AI step is a stub unless configured.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected request error.');
    } finally {
      setLoading(false);
    }
  }

  const filteredProducts = useMemo(
    () => selectedStatus === 'all' ? products : products.filter((p) => p.status === selectedStatus),
    [products, selectedStatus]
  );

  const statusCounts = useMemo(() => {
    const counts = { all: products.length, ready: 0, needs_review: 0, missing_fields: 0, exported: 0 };
    products.forEach((p) => { if (counts[p.status] !== undefined) counts[p.status] += 1; });
    return counts;
  }, [products]);

  const filterCounts = useMemo(() => summary ? {
    all: summary.total ?? statusCounts.all,
    ready: summary.ready ?? 0,
    needs_review: summary.needs_review ?? 0,
    missing_fields: summary.missing_fields ?? 0,
    exported: summary.exported ?? 0,
  } : statusCounts, [summary, statusCounts]);

  const exportCounts = useMemo(() => buildExportCounts(products, selectedIds), [products, selectedIds]);

  async function handleFileChange(nextFile) {
    setFile(nextFile); setCsvHeaders([]); setColumnMapping({});
    setMappingReady(false); setMappingError('');
    if (!nextFile || !nextFile.name.toLowerCase().endsWith('.csv')) return;
    const content = await nextFile.text();
    const headers = parseCsvHeaders(content);
    setCsvHeaders(headers);
    setColumnMapping(suggestMapping(headers));
    setMappingReady(true);
  }

  function handleApplyBulkAction() {
    if (!bulkActionType) return;
    let skipped = 0;
    const updated = products.map((p) => {
      if (!selectedIds.has(p.product_id)) return p;
      if (bulkActionType === 'mark_ready' && !canMarkReady(p)) { skipped += 1; return p; }
      return applyBulkAction(p, bulkActionType, bulkActionValue.trim());
    });
    setProducts(updated);
    setSummary(buildSummaryFromProducts(updated));
    setBulkWarning(bulkActionType === 'mark_ready' && skipped > 0
      ? `${skipped} products still have blocking errors and were not marked ready.` : '');
  }

  function handleDownloadExport() {
    const filtered = filterProductsForExport(products, exportOption, selectedIds);
    if (!filtered.length) { setWarning('No products available for the selected export option.'); return; }
    const csv = toCsvContent(buildExportRows(filtered));
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = Object.assign(document.createElement('a'), { href: url, download: `shopify_export_${exportOption}.csv` });
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="page-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Product Pipeline</p>
          <h1>Bulk product review, built for fast decisions.</h1>
          <p className="lede">Upload vendor files, review issues, and export a Shopify-ready CSV.</p>
        </div>
        <div className="header-card">
          <span>Run status</span>
          <strong>{loading ? 'Processing' : summary ? 'Ready to review' : 'Awaiting upload'}</strong>
          <small>{summary ? `${summary.total ?? 0} products in queue` : 'No file processed yet'}</small>
        </div>
      </header>

      <section className="grid-layout">
        <div className="stack">
          <UploadPanel
            apiUrl={apiUrl} onApiUrlChange={setApiUrl}
            file={file} onFileChange={handleFileChange}
            aiEnhance={aiEnhance} onAiEnhanceChange={setAiEnhance}
            dryRun={dryRun} onDryRunChange={setDryRun}
            onSubmit={handleSubmit} loading={loading}
            warning={warning} error={error}
            mappedCount={Object.values(columnMapping).filter(Boolean).length}
          />
          <ValidationSummary summary={summary} loading={loading} />
          {selectedIds.size > 0 && (
            <BulkActionToolbar
              selectedCount={selectedIds.size} totalCount={products.length}
              actionType={bulkActionType} actionValue={bulkActionValue}
              onActionChange={(a) => { setBulkActionType(a); setBulkActionValue(''); setBulkWarning(''); }}
              onValueChange={setBulkActionValue}
              onApply={handleApplyBulkAction}
              onClear={() => { setSelectedIds(new Set()); setBulkWarning(''); }}
              warning={bulkWarning}
            />
          )}
          <ProductFilters selected={selectedStatus} onChange={setSelectedStatus} counts={filterCounts} />
          <ProductTable
            products={filteredProducts} loading={loading} onSelectProduct={setActiveProduct}
            selectedIds={selectedIds}
            onToggleSelect={(id, checked) => setSelectedIds((c) => { const n = new Set(c); checked ? n.add(id) : n.delete(id); return n; })}
            onToggleSelectAll={(checked) => setSelectedIds((c) => {
              const n = new Set(c);
              filteredProducts.forEach((p) => checked ? n.add(p.product_id) : n.delete(p.product_id));
              return n;
            })}
          />
        </div>
        <aside className="sidebar">
          <ExportPanel
            downloadUrl={downloadUrl} counts={exportCounts}
            exportOption={exportOption} onOptionChange={setExportOption}
            onDownload={handleDownloadExport} loading={loading}
          />
        </aside>
      </section>

      <ProductReviewDrawer
        product={activeProduct}
        onClose={() => setActiveProduct(null)}
        onSave={(updated) => {
          const next = products.map((p) => p.product_id === updated.product_id ? updated : p);
          setProducts(next);
          setSummary(buildSummaryFromProducts(next));
          setActiveProduct(updated);
        }}
      />
    </main>
  );
}

export default PipelinePage;
