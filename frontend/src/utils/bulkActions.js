const TAG_SEPARATOR = ',';

function normalizeTag(tag) {
  return tag.trim();
}

function splitTags(value) {
  if (!value) {
    return [];
  }
  return value
    .split(TAG_SEPARATOR)
    .map((tag) => normalizeTag(tag))
    .filter(Boolean);
}

export function mergeTags(existing, incoming) {
  const existingTags = splitTags(existing);
  const incomingTags = splitTags(incoming);
  const merged = new Set([...existingTags, ...incomingTags]);
  return Array.from(merged).join(`${TAG_SEPARATOR} `).trim();
}

export function generateHandle(title) {
  if (!title) {
    return '';
  }
  return String(title)
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function appendLeadTime(bodyHtml, leadTime) {
  if (!leadTime) {
    return bodyHtml || '';
  }
  const note = `<p><strong>Lead time:</strong> ${leadTime}</p>`;
  if (!bodyHtml) {
    return note;
  }
  if (bodyHtml.includes(note)) {
    return bodyHtml;
  }
  return `${bodyHtml}\n${note}`;
}

function hasBlockingErrors(issues) {
  return (issues || []).some((issue) => issue.severity === 'error');
}

export function applyBulkAction(product, actionType, actionValue) {
  const normalized = product.normalized_record || {};
  const shopifyRow = product.shopify_row || {};
  const next = {
    ...product,
    normalized_record: { ...normalized },
    shopify_row: { ...shopifyRow },
  };

  switch (actionType) {
    case 'vendor':
      next.normalized_record.vendor = actionValue;
      next.shopify_row.Vendor = actionValue;
      break;
    case 'product_type':
      next.normalized_record.product_type = actionValue;
      next.shopify_row.Type = actionValue;
      break;
    case 'tags': {
      const mergedTags = mergeTags(normalized.tags, actionValue);
      next.normalized_record.tags = mergedTags;
      next.shopify_row.Tags = mergeTags(shopifyRow.Tags, actionValue);
      break;
    }
    case 'lead_time':
      next.normalized_record.lead_time = actionValue;
      next.shopify_row['Body (HTML)'] = appendLeadTime(shopifyRow['Body (HTML)'], actionValue);
      break;
    case 'generate_handles': {
      const title = normalized.title || '';
      const handle = generateHandle(title);
      next.normalized_record.handle = handle;
      next.shopify_row.Handle = handle;
      break;
    }
    case 'mark_ready':
      if (!hasBlockingErrors(product.issues)) {
        next.status = 'ready';
      }
      break;
    default:
      break;
  }

  return next;
}

export function canMarkReady(product) {
  return !hasBlockingErrors(product.issues);
}

export function buildSummaryFromProducts(products) {
  const summary = {
    total: products.length,
    ready: 0,
    needs_review: 0,
    missing_fields: 0,
    exported: 0,
  };

  products.forEach((product) => {
    if (summary[product.status] !== undefined) {
      summary[product.status] += 1;
    }
  });

  return summary;
}
