import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.price_list_pipeline import discover_pdfs, normalize_header, require_dependencies, safe_to_float


class TestPriceListPipelineUtils(unittest.TestCase):
    def test_normalize_header_aliases(self):
        self.assertEqual(normalize_header("SKU"), "item_code")
        self.assertEqual(normalize_header("Product Name"), "item_name")
        self.assertEqual(normalize_header("UOM"), "unit")

    def test_safe_to_float_values(self):
        self.assertEqual(safe_to_float("1,234.50"), 1234.50)
        self.assertEqual(safe_to_float("$99.99"), 99.99)
        self.assertIsNone(safe_to_float(""))
        self.assertIsNone(safe_to_float(None))

    def test_discover_pdfs_recursive(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.pdf").write_text("x", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "b.pdf").write_text("x", encoding="utf-8")
            (root / "nested" / "note.txt").write_text("x", encoding="utf-8")

            found = discover_pdfs(root)
            self.assertEqual([p.name for p in found], ["a.pdf", "b.pdf"])

    @patch("scripts.price_list_pipeline.importlib.util.find_spec")
    def test_require_dependencies_message(self, mock_find_spec):
        mock_find_spec.side_effect = lambda name: None if name == "pdfplumber" else object()
        with self.assertRaises(RuntimeError) as exc:
            require_dependencies()
        self.assertIn("Missing dependencies: pdfplumber", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
