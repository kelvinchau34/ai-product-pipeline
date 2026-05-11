const SHOPIFY_HEADERS = [
  'Handle',
  'Title',
  'Body (HTML)',
  'Vendor',
  'Product Category',
  'Type',
  'Tags',
  'Published',
  'Option1 Name',
  'Option1 Value',
  'Option2 Name',
  'Option2 Value',
  'Option3 Name',
  'Option3 Value',
  'Variant SKU',
  'Variant Grams',
  'Variant Inventory Tracker',
  'Variant Inventory Qty',
  'Variant Inventory Policy',
  'Variant Fulfillment Service',
  'Variant Price',
  'Variant Compare At Price',
  'Variant Requires Shipping',
  'Variant Taxable',
  'Variant Barcode',
  'Image Src',
  'Image Position',
  'Image Alt Text',
  'Gift Card',
  'SEO Title',
  'SEO Description',
  'Google Shopping / Google Product Category',
  'Google Shopping / Gender',
  'Google Shopping / Age Group',
  'Google Shopping / MPN',
  'Google Shopping / Condition',
  'Google Shopping / Custom Product',
  'Variant Image',
  'Variant Weight Unit',
  'Variant Tax Code',
  'Cost per item',
  'Included / United States',
  'Price / United States',
  'Compare At Price / United States',
  'Included / International',
  'Price / International',
  'Compare At Price / International',
  'Status',
];

function sanitizeValue(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value);
}

function toCsvCell(value) {
  const text = sanitizeValue(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function generateHandle(title) {
  return sanitizeValue(title)
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function buildBaseRow(product) {
  const normalized = product.normalized_record || {};
  const shopify = product.shopify_row || {};
  const title = shopify.Title || normalized.title || '';
  const handle = shopify.Handle || normalized.handle || generateHandle(title);

  const base = {
    ...shopify,
    Handle: handle,
    Title: title,
    Vendor: shopify.Vendor || normalized.vendor || '',
    Type: shopify.Type || normalized.product_type || '',
    Tags: shopify.Tags || normalized.tags || '',
    'Body (HTML)': shopify['Body (HTML)'] || normalized.body_html || '',
    'Variant SKU': shopify['Variant SKU'] || normalized.sku || '',
    'Variant Price': shopify['Variant Price'] || normalized.price || '',
  };

  return { base, handle };
}

function buildImageRows(product, handle) {
  const normalized = product.normalized_record || {};
  const images = normalized.images || [];
  if (!images.length) {
    return [];
  }

  return images.slice(1).map((imageUrl, index) => ({
    Handle: handle,
    'Image Src': imageUrl,
    'Image Position': String(index + 2),
    'Image Alt Text': normalized.title || '',
  }));
}

export function buildExportRows(products) {
  const rows = [];
  products.forEach((product) => {
    const { base, handle } = buildBaseRow(product);
    const row = { ...base };
    if (product.normalized_record?.images?.length && !row['Image Src']) {
      row['Image Src'] = product.normalized_record.images[0];
      row['Image Position'] = row['Image Position'] || '1';
      row['Image Alt Text'] = row['Image Alt Text'] || product.normalized_record.title || '';
    }
    rows.push(row);
    rows.push(...buildImageRows(product, handle));
  });
  return rows;
}

export function toCsvContent(rows) {
  const headerLine = SHOPIFY_HEADERS.join(',');
  const dataLines = rows.map((row) =>
    SHOPIFY_HEADERS.map((header) => toCsvCell(row?.[header] ?? '')).join(',')
  );
  return [headerLine, ...dataLines].join('\n');
}

export function filterProductsForExport(products, option, selectedIds) {
  if (option === 'ready') {
    return products.filter((product) => product.status === 'ready' || product.status === 'exported');
  }
  if (option === 'selected') {
    if (!selectedIds || selectedIds.size === 0) {
      return [];
    }
    return products.filter((product) => selectedIds.has(product.product_id));
  }
  if (option === 'include_warnings') {
    return products.filter((product) => product.status !== 'missing_fields');
  }
  return products;
}

export function hasBlockingErrors(issues) {
  return (issues || []).some((issue) => issue.severity === 'error');
}

export function buildExportCounts(products, selectedIds) {
  const total = products.length;
  let ready = 0;
  let warnings = 0;
  let blocking = 0;

  products.forEach((product) => {
    if (product.status === 'ready' || product.status === 'exported') {
      ready += 1;
    }
    if (hasBlockingErrors(product.issues)) {
      blocking += 1;
    } else if ((product.issues || []).length > 0) {
      warnings += 1;
    }
  });

  return {
    total,
    ready,
    warnings,
    blocking,
    selected: selectedIds?.size || 0,
  };
}
