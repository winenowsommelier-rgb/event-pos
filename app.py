import cgi
import csv
import io
import json
import os
import uuid
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib import request

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_CATEGORIES = {"Wine", "Spirit", "Beer", "Sake", "Accessory", "Other"}


def normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "product_name_standard": str(raw.get("product_name_standard", "")).strip(),
        "category": str(raw.get("category", "Other")).strip() or "Other",
        "style": str(raw.get("style", "")).strip(),
        "classification": str(raw.get("classification", "")).strip(),
        "country": str(raw.get("country", "")).strip(),
        "region": str(raw.get("region", "")).strip(),
        "sub_region": str(raw.get("sub_region", "")).strip(),
        "short_description_en": str(raw.get("short_description_en", "")).strip(),
        "short_description_th": str(raw.get("short_description_th", "")).strip(),
        "confidence_score": raw.get("confidence_score", 0),
        "remark": str(raw.get("remark", "")).strip(),
    }
    try:
        out["confidence_score"] = max(0.0, min(1.0, float(out["confidence_score"])))
    except (TypeError, ValueError):
        out["confidence_score"] = 0.0
    if out["category"] not in ALLOWED_CATEGORIES:
        out["category"] = "Other"
    return out


def fallback_enrich(product: Dict[str, str]) -> Dict[str, Any]:
    name = (product.get("product_name") or product.get("name") or "Unknown Product").strip()
    lower = name.lower()
    if any(k in lower for k in ["cabernet", "merlot", "chardonnay", "pinot", "wine"]):
        category = "Wine"
    elif any(k in lower for k in ["whisky", "gin", "rum", "vodka", "tequila", "cognac"]):
        category = "Spirit"
    elif "beer" in lower:
        category = "Beer"
    elif "sake" in lower:
        category = "Sake"
    elif any(k in lower for k in ["glass", "opener", "accessory"]):
        category = "Accessory"
    else:
        category = "Other"
    return {
        "product_name_standard": name.title(),
        "category": category,
        "style": category,
        "classification": "Unspecified",
        "country": product.get("country", "Unknown"),
        "region": product.get("region", "Unknown"),
        "sub_region": product.get("sub_region", ""),
        "short_description_en": f"{name.title()} for product catalog enrichment.",
        "short_description_th": f"{name.title()} สำหรับการเสริมข้อมูลสินค้า",
        "confidence_score": 0.62,
        "remark": "Fallback enrichment used.",
    }


def call_gemini(product: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    prompt = {
        "contents": [{"parts": [{"text": "Return only JSON with required fields. Input: " + json.dumps(product, ensure_ascii=False)}]}]
    }
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + api_key
    req = request.Request(url, data=json.dumps(prompt).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=30) as resp:  # nosec B310
        payload = json.loads(resp.read().decode("utf-8"))

    text = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    usage = int(payload.get("usageMetadata", {}).get("totalTokenCount", 0))
    return normalize_record(json.loads(text)), usage


def process_batch(rows: List[Dict[str, str]], batch_id: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    enriched_rows: List[Dict[str, Any]] = []
    logs: List[Dict[str, Any]] = []
    for row in rows:
        sku = row.get("sku") or row.get("SKU") or ""
        now = datetime.utcnow().isoformat()
        try:
            try:
                enriched, token_usage = call_gemini(row)
                status = "success"
            except Exception:
                enriched = normalize_record(fallback_enrich(row))
                token_usage = 0
                status = "fallback"
            enriched_rows.append({**row, **enriched})
            logs.append({"batch_id": batch_id, "sku": sku, "status": status, "confidence_score": enriched["confidence_score"], "token_usage": token_usage, "error_message": "", "timestamp": now})
        except Exception as exc:  # pylint: disable=broad-except
            logs.append({"batch_id": batch_id, "sku": sku, "status": "error", "confidence_score": 0, "token_usage": 0, "error_message": str(exc), "timestamp": now})
    return enriched_rows, logs


def process_rows(rows: List[Dict[str, str]], batch_size: int) -> Dict[str, Any]:
    all_enriched: List[Dict[str, Any]] = []
    all_logs: List[Dict[str, Any]] = []
    size = max(1, batch_size)
    for i in range(0, len(rows), size):
        batch_id = (i // size) + 1
        enriched, logs = process_batch(rows[i:i + size], batch_id)
        all_enriched.extend(enriched)
        all_logs.extend(logs)

    run_id = uuid.uuid4().hex[:10]
    out_name = f"{run_id}_product_intelligence_output.csv"
    log_name = f"{run_id}_processing_log.csv"

    with (OUTPUT_DIR / out_name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_enriched[0].keys()))
        writer.writeheader()
        writer.writerows(all_enriched)

    with (OUTPUT_DIR / log_name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_logs[0].keys()))
        writer.writeheader()
        writer.writerows(all_logs)

    return {
        "progress": 100,
        "processed": len(all_enriched),
        "total": len(rows),
        "error_count": sum(1 for x in all_logs if x["status"] == "error"),
        "estimated_completion": "done",
        "preview": all_enriched[:50],
        "logs": all_logs[-100:],
        "output_file": f"/download/{out_name}",
        "log_file": f"/download/{log_name}",
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], status: int = 200):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/":
            body = (BASE_DIR / "index.html").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith("/download/"):
            filename = self.path.split("/download/", 1)[1]
            path = OUTPUT_DIR / filename
            if path.exists() and path.is_file():
                body = path.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if self.path != "/api/process":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        ctype, pdict = cgi.parse_header(self.headers.get("content-type", ""))
        if ctype != "multipart/form-data":
            self._send_json({"error": "multipart/form-data required"}, 400)
            return

        pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
        form = cgi.parse_multipart(self.rfile, pdict)

        files = form.get("file")
        batch_sizes = form.get("batch_size", ["20"])
        if not files:
            self._send_json({"error": "Please upload a CSV file."}, 400)
            return

        try:
            batch_size = int(batch_sizes[0])
        except (TypeError, ValueError):
            batch_size = 20

        csv_data = files[0]
        if isinstance(csv_data, bytes):
            csv_text = csv_data.decode("utf-8")
        else:
            csv_text = str(csv_data)

        rows = list(csv.DictReader(io.StringIO(csv_text)))
        if not rows:
            self._send_json({"error": "CSV contains no rows."}, 400)
            return

        result = process_rows(rows, batch_size)
        self._send_json(result, 200)


def run_server():
    server = ThreadingHTTPServer(("0.0.0.0", 7860), Handler)
    print("Server running on http://0.0.0.0:7860")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
