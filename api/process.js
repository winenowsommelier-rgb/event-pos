const formidable = require('formidable');
const pdfParse = require('pdf-parse');
const OUTPUT_HEADERS = [
  'item_code',
  'item_name',
  'pack_size',
  'unit',
  'currency',
  'list_price',
  'discount',
  'net_price',
  'source_file',
  'source_page',
  'source_row'
];

function escapeCsvValue(value) {
  const text = value == null ? '' : String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function toCsv(rows, headers) {
  const headerLine = headers.join(',');
  const body = rows.map((row) => headers.map((header) => escapeCsvValue(row[header])).join(',')).join('\n');
  return body ? `${headerLine}\n${body}\n` : `${headerLine}\n`;
}

function parseRowsFromText(text, sourceFile) {
  const rows = [];
  const errors = [];
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  const rowPattern = /^(\S+)\s+(.+?)\s+([\d,]+(?:\.\d+)?)$/;

  lines.forEach((line, index) => {
    const match = line.match(rowPattern);
    if (!match) {
      return;
    }

    const [, itemCode, itemName, rawPrice] = match;
    const listPrice = Number(String(rawPrice).replace(/,/g, ''));

    if (!Number.isFinite(listPrice) || listPrice <= 0) {
      errors.push({
        source_file: sourceFile,
        row_number: index + 1,
        column: 'list_price',
        issue: 'invalid_or_missing_price',
        value: rawPrice
      });
      return;
    }

    rows.push({
      item_code: itemCode,
      item_name: itemName,
      pack_size: '',
      unit: '',
      currency: 'USD',
      list_price: listPrice,
      discount: '',
      net_price: '',
      source_file: sourceFile,
      source_page: 1,
      source_row: index + 1
    });
  });

  return { rows, errors };
}

async function parseMultipart(req) {
  const form = formidable({ multiples: true, keepExtensions: true });
  return new Promise((resolve, reject) => {
    form.parse(req, (err, fields, files) => {
      if (err) {
        reject(err);
        return;
      }
      resolve({ fields, files });
    });
  });
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.statusCode = 405;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ error: 'Method not allowed. Use POST.' }));
    return;
  }

  try {
    const { files } = await parseMultipart(req);
    const uploaded = files.files || [];
    const uploadedList = Array.isArray(uploaded) ? uploaded : [uploaded];

    if (!uploadedList.length) {
      res.statusCode = 400;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ error: 'No files uploaded. Use form field name "files".' }));
      return;
    }

    const cleanRows = [];
    const errorRows = [];

    for (const file of uploadedList) {
      const data = await pdfParse(require('fs').readFileSync(file.filepath));
      const parsed = parseRowsFromText(data.text || '', file.originalFilename || 'uploaded.pdf');
      cleanRows.push(...parsed.rows);
      errorRows.push(...parsed.errors);
    }

    const rowsWithErrorCount = cleanRows.map((row) => ({
      ...row,
      validation_issues_in_file: errorRows.filter((e) => e.source_file === row.source_file).length
    }));
    const csv = toCsv(rowsWithErrorCount, [...OUTPUT_HEADERS, 'validation_issues_in_file']);

    res.statusCode = 200;
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', 'attachment; filename="pricelist_clean.csv"');
    res.end(csv);
  } catch (error) {
    res.statusCode = 500;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ error: `Processing failed: ${error.message}` }));
  }
};
