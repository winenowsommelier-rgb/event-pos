# PDF Price List Workflow

This workflow turns vendor PDF price lists into a clean and validated Excel workbook.

## 1) Prepare Input Files

1. Download PDF files from Google Drive into a local folder, for example `./input_pdfs`.
2. Keep original file names; do not rename pages.
3. Separate non-price documents (catalogs, brochures) from price lists.

## 2) Python Dependencies

Install dependencies in your own environment:

```bash
pip install pandas pdfplumber openpyxl
```

If dependencies are missing, the script exits with a clear message and install command.

## 3) Run the Pipeline

```bash
python scripts/price_list_pipeline.py --input ./input_pdfs --output ./output/pricelist_clean.xlsx
```

## 4) Output Sheets

- `Clean_Data`: normalized rows ready for analysis/import.
- `Validation_Errors`: row-level quality issues.
- `Audit_Log`: totals for quick monitoring.

## 5) Validation Rules Included

- Required fields: `item_code`, `item_name`.
- Price must be numeric and greater than zero.
- Currency must be in supported list: USD, EUR, GBP, SGD, MYR, IDR, THB.
- Duplicate detection by `source_file + item_code + item_name`.

## 6) Recommended Next Enhancements

- Add OCR stage for scanned PDFs.
- Add supplier-specific header mappings.
- Add historical price change checks.
- Add scheduled runs and auto-email summary.

## 7) Lightweight Validation Tests

You can run basic utility tests without installing PDF dependencies:

```bash
python -m unittest tests/test_price_list_pipeline.py
```
