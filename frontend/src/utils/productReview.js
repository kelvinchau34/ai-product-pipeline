const REQUIRED_FIELDS = ['title', 'sku'];

function removeResolvedIssues(issues, updates) {
  return (issues || []).filter((issue) => {
    if (!issue?.code) {
      return true;
    }
    if (issue.code === 'missing_title' && updates.title) {
      return false;
    }
    if (issue.code === 'missing_sku' && updates.sku) {
      return false;
    }
    if (issue.code === 'missing_vendor' && updates.vendor) {
      return false;
    }
    if (issue.code === 'missing_images' && updates.images?.length) {
      return false;
    }
    return true;
  });
}

function hasBlockingErrors(issues) {
  return (issues || []).some((issue) => issue.severity === 'error');
}

function computeStatus(normalized, issues) {
  const hasMissingRequired = REQUIRED_FIELDS.some((field) => !normalized[field]);
  if (hasMissingRequired || hasBlockingErrors(issues)) {
    return 'missing_fields';
  }
  if ((issues || []).length > 0) {
    return 'needs_review';
  }
  return 'ready';
}

function parseImages(value) {
  if (!value) {
    return [];
  }
  return value
    .split('\n')
    .map((entry) => entry.trim())
    .filter(Boolean);
}

export function applyProductEdits(product, edits) {
  const normalized = { ...product.normalized_record };
  const shopifyRow = { ...product.shopify_row };

  normalized.title = edits.title;
  normalized.sku = edits.sku;
  normalized.vendor = edits.vendor;
  normalized.product_type = edits.product_type;
  normalized.tags = edits.tags;
  normalized.body_html = edits.body_html;
  normalized.images = edits.images;
  normalized.handle = edits.handle;

  shopifyRow.Title = edits.title;
  shopifyRow['Variant SKU'] = edits.sku;
  shopifyRow.Vendor = edits.vendor;
  shopifyRow.Type = edits.product_type;
  shopifyRow.Tags = edits.tags;
  shopifyRow['Body (HTML)'] = edits.body_html;
  shopifyRow.Handle = edits.handle;
  shopifyRow['Image Src'] = edits.images?.[0] || '';
  shopifyRow['Image Position'] = edits.images?.length ? '1' : '';
  shopifyRow['Image Alt Text'] = edits.title || '';
  shopifyRow['SEO Title'] = edits.seo_title;
  shopifyRow['SEO Description'] = edits.seo_description;

  const nextIssues = removeResolvedIssues(product.issues, {
    title: edits.title,
    sku: edits.sku,
    vendor: edits.vendor,
    images: edits.images,
  });

  return {
    ...product,
    normalized_record: normalized,
    shopify_row: shopifyRow,
    issues: nextIssues,
    status: computeStatus(normalized, nextIssues),
  };
}

export function toEditableState(product) {
  const normalized = product?.normalized_record || {};
  const shopifyRow = product?.shopify_row || {};
  const images = normalized.images || [];

  return {
    title: normalized.title || '',
    sku: normalized.sku || '',
    vendor: normalized.vendor || '',
    product_type: normalized.product_type || '',
    tags: normalized.tags || shopifyRow.Tags || '',
    body_html: normalized.body_html || shopifyRow['Body (HTML)'] || '',
    handle: normalized.handle || shopifyRow.Handle || '',
    image_text: images.join('\n'),
    images,
    seo_title: shopifyRow['SEO Title'] || '',
    seo_description: shopifyRow['SEO Description'] || '',
  };
}

export function updateImages(editState, imageText) {
  const images = parseImages(imageText);
  return {
    ...editState,
    image_text: imageText,
    images,
  };
}
