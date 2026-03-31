#!/usr/bin/env python3
"""Extract, clean, validate, and export PDF price lists to Excel.

Usage:
  python scripts/price_list_pipeline.py --input ./input_pdfs --output ./output/pricelist_clean.xlsx
"""

from __future__ import annotations

import argparse
import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Iterable

EXPECTED_COLUMNS = [
    "item_code",
    "item_name",
    "pack_size",
    "unit",
    "currency",
    "list_price",
    "discount",
    "net_price",
]


@dataclass
class ValidationIssue:
    source_file: str
    page: int
    row_number: int
    column: str
    issue: str
    value: str


def discover_pdfs(input_dir: Path) -> list[Path]:
    return sorted(input_dir.rglob("*.pdf"))


def require_dependencies() -> None:
    required = ["pandas", "pdfplumber", "openpyxl"]
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            f"Missing dependencies: {missing_text}. Install them with: pip install pandas pdfplumber openpyxl"
        )


def normalize_header(header: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", header.strip().lower()).strip("_")
    aliases = {
        "item": "item_name",
        "product": "item_name",
        "product_name": "item_name",
        "sku": "item_code",
        "code": "item_code",
        "price": "list_price",
        "list": "list_price",
        "uom": "unit",
        "size": "pack_size",
    }
    return aliases.get(cleaned, cleaned)


def safe_to_float(value: object) -> float | None:
    if value is None:
        return None
    txt = str(value).strip()
    if not txt:
        return None
    txt = txt.replace(",", "")
    txt = re.sub(r"[^0-9.\-]", "", txt)
    if txt in {"", ".", "-", "-."}:
        return None
    return float(txt)


def extract_tables_from_pdf(pdf_path: Path):
    import pandas as pd
    import pdfplumber

    records: list[dict[str, object]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) < 2:
                    continue

                headers = [normalize_header(h or "") for h in table[0]]
                for row_idx, row in enumerate(table[1:], start=2):
                    values = {headers[i]: row[i] if i < len(row) else None for i in range(len(headers))}
                    values["source_file"] = pdf_path.name
                    values["source_page"] = page_num
                    values["source_row"] = row_idx
                    records.append(values)

    if not records:
        return pd.DataFrame(columns=EXPECTED_COLUMNS + ["source_file", "source_page", "source_row"])

    df = pd.DataFrame.from_records(records)
    return df


def standardize_schema(df):
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df["currency"] = df["currency"].fillna("USD").astype(str).str.upper().str.strip()
    df["unit"] = (
        df["unit"].fillna("").astype(str).str.upper().str.strip().replace({"PCS": "EA", "PIECE": "EA"})
    )

    for col in ["list_price", "discount", "net_price"]:
        df[col] = df[col].map(safe_to_float)

    df["item_code"] = df["item_code"].fillna("").astype(str).str.strip()
    df["item_name"] = df["item_name"].fillna("").astype(str).str.strip()
    df["pack_size"] = df["pack_size"].fillna("").astype(str).str.strip()

    return df


def validate_rows(df) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for idx, row in df.iterrows():
        src_file = str(row.get("source_file", ""))
        src_page = int(row.get("source_page", 0) or 0)
        src_row = int(row.get("source_row", idx + 1) or (idx + 1))

        if not row.get("item_code"):
            issues.append(ValidationIssue(src_file, src_page, src_row, "item_code", "missing_item_code", ""))

        if not row.get("item_name"):
            issues.append(ValidationIssue(src_file, src_page, src_row, "item_name", "missing_item_name", ""))

        currency = str(row.get("currency", "")).upper()
        if currency not in {"USD", "EUR", "GBP", "SGD", "MYR", "IDR", "THB"}:
            issues.append(
                ValidationIssue(src_file, src_page, src_row, "currency", "unsupported_currency", currency)
            )

        list_price = row.get("list_price")
        if list_price is None or (isinstance(list_price, float) and list_price <= 0):
            issues.append(
                ValidationIssue(src_file, src_page, src_row, "list_price", "invalid_or_missing_price", str(list_price))
            )

    duplicate_mask = df.duplicated(subset=["source_file", "item_code", "item_name"], keep=False)
    for idx in df[duplicate_mask].index:
        row = df.loc[idx]
        issues.append(
            ValidationIssue(
                str(row.get("source_file", "")),
                int(row.get("source_page", 0) or 0),
                int(row.get("source_row", idx + 1) or (idx + 1)),
                "item_code/item_name",
                "duplicate_row_in_source",
                f"{row.get('item_code', '')} | {row.get('item_name', '')}",
            )
        )

    return issues


def run_pipeline(input_dir: Path, output_file: Path) -> tuple[Any, Any]:
    require_dependencies()
    import pandas as pd

    pdfs = discover_pdfs(input_dir)
    all_frames = [extract_tables_from_pdf(path) for path in pdfs]

    if all_frames:
        raw = pd.concat(all_frames, ignore_index=True)
    else:
        raw = pd.DataFrame(columns=EXPECTED_COLUMNS + ["source_file", "source_page", "source_row"])

    clean = standardize_schema(raw)
    issues = validate_rows(clean)
    issues_df = pd.DataFrame([issue.__dict__ for issue in issues])

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        clean.to_excel(writer, sheet_name="Clean_Data", index=False)
        issues_df.to_excel(writer, sheet_name="Validation_Errors", index=False)

        summary = pd.DataFrame(
            {
                "metric": ["total_rows", "total_pdfs", "validation_issues"],
                "value": [len(clean), len(pdfs), len(issues_df)],
            }
        )
        summary.to_excel(writer, sheet_name="Audit_Log", index=False)

    return clean, issues_df


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract and validate PDF price lists into a structured Excel file")
    parser.add_argument("--input", required=True, type=Path, help="Directory containing input PDF files")
    parser.add_argument("--output", required=True, type=Path, help="Output Excel file path")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    try:
        clean_df, issues_df = run_pipeline(args.input, args.output)
        print(f"Processed rows: {len(clean_df)}")
        print(f"Validation issues: {len(issues_df)}")
        print(f"Excel written to: {args.output}")
        return 0
    except RuntimeError as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
