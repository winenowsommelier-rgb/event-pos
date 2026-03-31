# Deploy PDF Price List Tool on Vercel

This repository now includes a user-facing web app and a Vercel serverless API.

## Included files

- `pdf_tool.html` — end-user upload UI.
- `api/process.js` — serverless endpoint that receives PDF files, extracts rows, validates basic price fields, and returns an Excel workbook.
- `vercel.json` — routes and function runtime configuration.
- `package.json` — dependencies (`formidable`, `pdf-parse`, `xlsx`).

## Deploy steps

1. Push this repository to GitHub.
2. Import the repo into Vercel.
3. Framework preset: **Other**.
4. Build command: leave empty.
5. Output directory: leave empty (static files served from repo root).
6. Deploy.

## End-user URL paths

- Main uploader page: `/pdf-tool`
- API endpoint: `/api/process`

## Notes

- Extraction in `api/process.js` uses a heuristic parser for text-style price lists.
- For scanned/image PDFs, add OCR (e.g., Tesseract or external OCR API) in the API function.
- For supplier-specific table structures, extend `parseRowsFromText` with custom patterns.
