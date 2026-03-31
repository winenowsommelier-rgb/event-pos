# Deploy PDF Price List Tool on Vercel

This repository now includes a user-facing web app and a Vercel serverless API.

## Included files

- `pdf-tool.html` — end-user upload UI.
- `api/process.js` — serverless endpoint that receives PDF files, extracts rows, validates basic price fields, and returns a cleaned CSV file.
- `package.json` — dependencies (`formidable`, `pdf-parse`).

## Deploy steps

1. Push this repository to GitHub.
2. Import the repo into Vercel.
3. Framework preset: **Other**.
4. Build command: leave empty.
5. Output directory: leave empty (static files served from repo root).
6. Deploy.

This setup relies on Vercel defaults (no custom `vercel.json`) to reduce deployment config errors.

## End-user URL paths

- Main uploader page: `/pdf-tool.html`
- API endpoint: `/api/process`

## Notes

- Extraction in `api/process.js` uses a heuristic parser for text-style price lists.
- Vercel serverless requests can fail with `HTTP 413` for large uploads. The frontend now enforces a per-file size guard (4MB) and uploads files one-by-one.
- For scanned/image PDFs, add OCR (e.g., Tesseract or external OCR API) in the API function.
- For supplier-specific table structures, extend `parseRowsFromText` with custom patterns.
