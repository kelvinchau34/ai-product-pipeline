export const INTERNAL_FIELDS = [
  { key: 'title', label: 'Title', required: true },
  { key: 'sku', label: 'SKU', required: true },
  { key: 'barcode', label: 'Barcode', required: false },
  { key: 'price', label: 'Price', required: false },
  { key: 'vendor', label: 'Vendor', required: false },
  { key: 'product_type', label: 'Product type', required: false },
  { key: 'description', label: 'Description', required: false },
  { key: 'dimensions', label: 'Dimensions', required: false },
  { key: 'materials', label: 'Materials', required: false },
  { key: 'colours', label: 'Colours', required: false },
  { key: 'image_1', label: 'Image 1', required: false },
  { key: 'image_2', label: 'Image 2', required: false },
  { key: 'image_3', label: 'Image 3', required: false },
  { key: 'tags', label: 'Tags', required: false },
  { key: 'weight', label: 'Weight', required: false },
  { key: 'lead_time', label: 'Lead time', required: false },
];

const SUGGESTIONS = {
  title: ['title', 'product title', 'name', 'product name', 'description'],
  sku: ['sku', 'item no', 'item number', 'product code'],
  barcode: ['barcode', 'ean', 'upc'],
  price: ['price', 'rrp', 'cost', 'msrp'],
  vendor: ['vendor', 'brand', 'manufacturer'],
  product_type: ['product type', 'category', 'type'],
  description: ['description', 'product text', 'details'],
  dimensions: ['dimensions', 'size'],
  materials: ['materials', 'material'],
  colours: ['colour', 'color', 'colourway'],
  image_1: ['image 1', 'image1', 'image_1', 'packshot 1', 'main image'],
  image_2: ['image 2', 'image2', 'image_2', 'packshot 2'],
  image_3: ['image 3', 'image3', 'image_3', 'packshot 3'],
  tags: ['tags', 'tag'],
  weight: ['weight'],
  lead_time: ['lead time', 'lead_time', 'leadtime'],
};

export const WOUD_PRESET = {
  title: 'Description',
  sku: 'Item no.',
  barcode: 'EAN',
  price: 'DE RRP incl. VAT (EUR)',
  product_type: 'Category',
  description: 'Description',
  materials: 'Materials',
  colours: 'Colour',
  image_1: 'Packshot 1',
  image_2: 'Packshot 2',
  image_3: 'Packshot 3',
  tags: 'Category',
  weight: 'Weight',
};

function normalizeKey(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

export function parseCsvHeaders(fileContent) {
  const line = fileContent.split(/\r?\n/)[0] || '';
  const headers = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }
    if (char === ',' && !inQuotes) {
      headers.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  if (current) {
    headers.push(current.trim());
  }

  return headers.filter(Boolean);
}

export function suggestMapping(headers) {
  const normalizedHeaders = headers.map((header) => ({
    original: header,
    normalized: normalizeKey(header),
  }));

  const mapping = {};
  INTERNAL_FIELDS.forEach((field) => {
    const suggestions = SUGGESTIONS[field.key] || [];
    const match = normalizedHeaders.find((header) =>
      suggestions.some((suggestion) => normalizeKey(suggestion) === header.normalized)
    );
    if (match) {
      mapping[field.key] = match.original;
    }
  });

  return mapping;
}

export function applyPreset(headers, preset) {
  const mapping = {};
  Object.entries(preset).forEach(([field, header]) => {
    if (headers.includes(header)) {
      mapping[field] = header;
    }
  });
  return mapping;
}

export function getRequiredFields() {
  return INTERNAL_FIELDS.filter((field) => field.required).map((field) => field.key);
}
