import { useMemo, useState } from 'react';
import {
  BulkActionToolbar,
  ColumnMappingPanel,
  ExportPanel,
  ProductFilters,
  ProductReviewDrawer,
  ProductTable,
  UploadPanel,
  ValidationSummary,
} from './components';
import {
  applyBulkAction,
  buildSummaryFromProducts,
  canMarkReady,
} from './utils/bulkActions';
import {
  buildExportCounts,
  buildExportRows,
  filterProductsForExport,
  toCsvContent,
} from './utils/exportShopifyCsv';
import {
  applyPreset,
  getRequiredFields,
  parseCsvHeaders,
  suggestMapping,
  WOUD_PRESET,
} from './utils/columnMapping';

const DEFAULT_API_URL = import.meta.env.VITE_API_URL || '';

function buildSummary(result) {
  if (result?.summary) {
    return result.summary;
  }

  if (result?.final_summary) {
    const fallbackTotal = result.final_summary.total_input ?? 0;
    const fallbackProcessed = result.final_summary.successfully_processed ?? 0;
    return {
      total: fallbackTotal,
      ready: fallbackProcessed,
      needs_review: 0,
      missing_fields: Math.max(fallbackTotal - fallbackProcessed, 0),
      exported: result.final_summary.exported ? fallbackProcessed : 0,
    };
  }

  return null;
}

function App() {
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
    setWarning('');
    setError('');
    setSummary(null);
    setProducts([]);
    setDownloadUrl('');
    setExportOption('all');
    setSelectedIds(new Set());
    setActiveProduct(null);
    setBulkActionType('');
    setBulkActionValue('');
    setBulkWarning('');
    setMappingReady(false);
    setMappingError('');

    if (!apiUrl.trim()) {
      setError('Set VITE_API_URL or enter an API endpoint first.');
      return;
    }

    if (!file) {
      setError('Choose a CSV or JSON file to upload.');
      return;
    }

    if (csvHeaders.length > 0 && !mappingReady) {
      setError('Map required columns before processing.');
      return;
    }

    setLoading(true);

    try {
      const fileContent = await file.text();
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
        const message = data?.result?.final_summary?.error || data?.error || 'Request failed.';
        throw new Error(message);
      }

      const result = data?.result || {};
      const nextSummary = buildSummary(result);
      setSummary(nextSummary);

      const resolvedDownloadUrl =
        result?.output?.download_url ||
        result?.output?.csv_key ||
        data?.request?.download_url ||
        result?.download_url ||
        result?.output_s3_uri ||
        '';
      setDownloadUrl(resolvedDownloadUrl);

      const nextProducts = (result.products || []).map((product, index) => ({
        ...product,
        product_id: product.product_id || `row-${product.row_index ?? index + 1}`,
      }));
      setProducts(nextProducts);

      if (result?.final_summary?.error) {
        setWarning(result.final_summary.error);
      } else if (dryRun) {
        setWarning('Dry run is enabled, so Shopify upload was skipped.');
      }

      if (aiEnhance) {
        setWarning((current) => current || 'AI enhance is enabled. The backend currently uses a placeholder AI step unless configured.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected request error.');
    } finally {
      setLoading(false);
    }
  }

  const filteredProducts = useMemo(() => {
    if (selectedStatus === 'all') {
      return products;
    }
    return products.filter((product) => product.status === selectedStatus);
  }, [products, selectedStatus]);

  const statusCounts = useMemo(() => {
    const counts = {
      all: products.length,
      ready: 0,
      needs_review: 0,
      missing_fields: 0,
      exported: 0,
    };
    products.forEach((product) => {
      if (counts[product.status] !== undefined) {
        counts[product.status] += 1;
      }
    });
    return counts;
  }, [products]);

  const filterCounts = useMemo(() => {
    if (!summary) {
      return statusCounts;
    }
    return {
      all: summary.total ?? statusCounts.all,
      ready: summary.ready ?? 0,
      needs_review: summary.needs_review ?? 0,
      missing_fields: summary.missing_fields ?? 0,
      exported: summary.exported ?? 0,
    };
  }, [summary, statusCounts]);

  const exportCounts = useMemo(
    () => buildExportCounts(products, selectedIds),
    [products, selectedIds]
  );

  async function handleFileChange(nextFile) {
    setFile(nextFile);
    setCsvHeaders([]);
    setColumnMapping({});
    setMappingReady(false);
    setMappingError('');

    if (!nextFile) {
      return;
    }

    if (!nextFile.name.toLowerCase().endsWith('.csv')) {
      return;
    }

    const content = await nextFile.text();
    const headers = parseCsvHeaders(content);
    setCsvHeaders(headers);
    const suggested = suggestMapping(headers);
    setColumnMapping(suggested);
  }

  function handleApplyBulkAction() {
    if (!bulkActionType) {
      return;
    }

    let skipped = 0;
    const updatedProducts = products.map((product) => {
      if (!selectedIds.has(product.product_id)) {
        return product;
      }

      if (bulkActionType === 'mark_ready' && !canMarkReady(product)) {
        skipped += 1;
        return product;
      }

      return applyBulkAction(product, bulkActionType, bulkActionValue.trim());
    });

    setProducts(updatedProducts);
    setSummary(buildSummaryFromProducts(updatedProducts));

    if (bulkActionType === 'mark_ready' && skipped > 0) {
      setBulkWarning(`${skipped} products still have blocking errors and were not marked ready.`);
    } else {
      setBulkWarning('');
    }
  }

  function handleClearSelection() {
    setSelectedIds(new Set());
    setBulkWarning('');
  }

  function handleDownloadExport() {
    const filtered = filterProductsForExport(products, exportOption, selectedIds);
    if (filtered.length === 0) {
      setWarning('No products available for the selected export option.');
      return;
    }
    const rows = buildExportRows(filtered);
    const csv = toCsvContent(rows);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `shopify_export_${exportOption}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="page-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">AI Product Pipeline</p>
          <h1>Bulk product review, built for fast decisions.</h1>
          <p className="lede">
            Upload vendor files, review issues at the product level, and export a Shopify-ready CSV.
          </p>
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
            apiUrl={apiUrl}
            onApiUrlChange={setApiUrl}
            file={file}
            onFileChange={handleFileChange}
            aiEnhance={aiEnhance}
            onAiEnhanceChange={setAiEnhance}
            dryRun={dryRun}
            onDryRunChange={setDryRun}
            onSubmit={handleSubmit}
            loading={loading}
            warning={warning}
            error={error}
            mappingRequired={csvHeaders.length > 0}
            mappingReady={mappingReady}
          />

          {csvHeaders.length > 0 ? (
            <ColumnMappingPanel
              headers={csvHeaders}
              mapping={columnMapping}
              error={mappingError}
              onApplyPreset={() => {
                setColumnMapping((current) => ({
                  ...current,
                  ...applyPreset(csvHeaders, WOUD_PRESET),
                }));
              }}
              onChange={(field, value) => {
                setColumnMapping((current) => ({
                  ...current,
                  [field]: value,
                }));
              }}
              onConfirm={() => {
                const requiredFields = getRequiredFields();
                const missing = requiredFields.filter((field) => !columnMapping[field]);
                if (missing.length > 0) {
                  setMappingError('Map required fields before continuing.');
                  return;
                }
                setMappingError('');
                setMappingReady(true);
              }}
            />
          ) : null}

          <ValidationSummary summary={summary} loading={loading} />

          {selectedIds.size > 0 ? (
            <BulkActionToolbar
              selectedCount={selectedIds.size}
              totalCount={products.length}
              actionType={bulkActionType}
              actionValue={bulkActionValue}
              onActionChange={(nextAction) => {
                setBulkActionType(nextAction);
                setBulkActionValue('');
                setBulkWarning('');
              }}
              onValueChange={setBulkActionValue}
              onApply={handleApplyBulkAction}
              onClear={handleClearSelection}
              warning={bulkWarning}
            />
          ) : null}

          <ProductFilters
            selected={selectedStatus}
            onChange={setSelectedStatus}
            counts={filterCounts}
          />

          <ProductTable
            products={filteredProducts}
            loading={loading}
            onSelectProduct={setActiveProduct}
            selectedIds={selectedIds}
            onToggleSelect={(productId, checked) => {
              setSelectedIds((current) => {
                const next = new Set(current);
                if (checked) {
                  next.add(productId);
                } else {
                  next.delete(productId);
                }
                return next;
              });
            }}
            onToggleSelectAll={(checked) => {
              setSelectedIds((current) => {
                const next = new Set(current);
                filteredProducts.forEach((product) => {
                  if (checked) {
                    next.add(product.product_id);
                  } else {
                    next.delete(product.product_id);
                  }
                });
                return next;
              });
            }}
          />
        </div>

        <aside className="sidebar">
          <ExportPanel
            downloadUrl={downloadUrl}
            counts={exportCounts}
            exportOption={exportOption}
            onOptionChange={setExportOption}
            onDownload={handleDownloadExport}
            loading={loading}
          />
        </aside>
      </section>

      <ProductReviewDrawer
        product={activeProduct}
        onClose={() => setActiveProduct(null)}
        onSave={(updatedProduct) => {
          const nextProducts = products.map((product) =>
            product.product_id === updatedProduct.product_id ? updatedProduct : product
          );
          setProducts(nextProducts);
          setSummary(buildSummaryFromProducts(nextProducts));
          setActiveProduct(updatedProduct);
        }}
      />
    </main>
  );
}

export default App;
