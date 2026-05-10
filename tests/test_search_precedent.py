import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "legal-jp" / "scripts" / "search_precedent.py"


class SearchPrecedentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "data_set"
        self.precedent_dir = self.repo / "precedent" / "2020"
        self.precedent_dir.mkdir(parents=True)

        self.supreme_item = {
            "case_number": "令和2(受)123",
            "court_name": "最高裁判所第一小法廷",
            "date": {"era": "Reiwa", "year": 2, "month": 5, "day": 1},
            "trial_type": "SupremeCourt",
            "lawsuit_id": "1",
        }
        self.lower_item = {
            "case_number": "令和2(行ウ)999",
            "court_name": "東京地方裁判所",
            "date": {"era": "Reiwa", "year": 2, "month": 6, "day": 1},
            "trial_type": "LowerCourt",
            "lawsuit_id": "1",
        }
        self._write_json(self.precedent_dir / "list.json", [self.supreme_item, self.lower_item])
        self._write_json(
            self.precedent_dir / "令和2(受)123_最高裁判所第一小法廷_SupremeCourt_1.json",
            {
                "case_name": "損害賠償請求事件",
                "case_number": "令和2(受)123",
                "court_name": "最高裁判所第一小法廷",
                "trial_type": "SupremeCourt",
                "lawsuit_id": "1",
                "contents": "不法行為に基づく損害賠償について判断した。",
            },
        )
        self._write_json(
            self.precedent_dir / "令和2(行ウ)999_東京地方裁判所_LowerCourt_1.json",
            {
                "case_name": "行政処分取消請求事件",
                "case_number": "令和2(行ウ)999",
                "court_name": "東京地方裁判所",
                "trial_type": "LowerCourt",
                "lawsuit_id": "1",
                "contents": "下級審の判断。",
            },
        )
        self._write_json(
            self.precedent_dir / "昭和27(オ)1250_最高裁判所第三小法廷_SupremeCourt_73986.json",
            {
                "case_name": "所有権確認請求事件",
                "case_number": "昭和27(オ)1250",
                "court_name": "最高裁判所第三小法廷",
                "trial_type": "SupremeCourt",
                "lawsuit_id": "73986",
                "contents": "list.jsonにない判例。",
            },
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _write_json(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def _run_search(self, *args):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return json.loads(proc.stdout), proc.stdout

    def _run_search_failure(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def _load_module(self):
        spec = importlib.util.spec_from_file_location("search_precedent", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_title_search_returns_title_decade_and_preserved_date(self):
        results, _ = self._run_search("--title", "損害賠償", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual("損害賠償請求事件", results[0]["title"])
        self.assertEqual("2020", results[0]["decade"])
        self.assertEqual({"era": "Reiwa", "year": 2, "month": 5, "day": 1}, results[0]["date"])

    def test_case_number_search_returns_first_matching_case(self):
        results, _ = self._run_search("--case-number", "令和2", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual("令和2(受)123", results[0]["case_number"])

    def test_case_number_search_normalizes_common_citation_forms(self):
        results, _ = self._run_search("--case-number", "令和２年（受）第１２３号", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual("令和2(受)123", results[0]["case_number"])

    def test_case_number_search_normalizes_missing_parentheses(self):
        results, _ = self._run_search("--case-number", "令和2年受第123号", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual("令和2(受)123", results[0]["case_number"])

    def test_case_number_search_can_match_lawsuit_id(self):
        results, _ = self._run_search("--case-number", "1", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(
            "precedent/2020/令和2(受)123_最高裁判所第一小法廷_SupremeCourt_1.json",
            results[0]["json_path"],
        )

    def test_duplicate_lawsuit_id_uses_matching_trial_type_details(self):
        results, _ = self._run_search("--case-number", "令和2(行ウ)999", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(
            "precedent/2020/令和2(行ウ)999_東京地方裁判所_LowerCourt_1.json",
            results[0]["json_path"],
        )

    def test_case_number_search_does_not_load_unmatched_detail(self):
        detail_path = self.precedent_dir / "令和2(受)123_最高裁判所第一小法廷_SupremeCourt_1.json"
        detail_path.write_text("{", encoding="utf-8")

        results, _ = self._run_search("--case-number", "令和2(行ウ)999", "--decade", "2020", "--limit", "1")

        self.assertEqual("令和2(行ウ)999", results[0]["case_number"])

    def test_case_number_search_does_not_disambiguate_unmatched_detail(self):
        rows = json.loads((self.precedent_dir / "list.json").read_text(encoding="utf-8"))
        rows.insert(0, {"case_number": "平成1(未)111", "lawsuit_id": "dup"})
        self._write_json(self.precedent_dir / "list.json", rows)
        (self.precedent_dir / "bad_A_LowerCourt_dup.json").write_text("{", encoding="utf-8")
        self._write_json(
            self.precedent_dir / "good_B_SupremeCourt_dup.json",
            {
                "case_name": "重複候補事件",
                "case_number": "平成1(未)111",
                "lawsuit_id": "dup",
            },
        )

        results, _ = self._run_search("--case-number", "令和2(行ウ)999", "--decade", "2020", "--limit", "1")

        self.assertEqual("令和2(行ウ)999", results[0]["case_number"])

    def test_case_number_search_includes_orphan_detail_json(self):
        results, _ = self._run_search("--case-number", "昭和27(オ)1250", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(
            "precedent/2020/昭和27(オ)1250_最高裁判所第三小法廷_SupremeCourt_73986.json",
            results[0]["json_path"],
        )

    def test_text_search_returns_snippet(self):
        results, _ = self._run_search("--text", "不法行為", "--decade", "2020", "--snippet", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertIn("不法行為", results[0]["snippet"])

    def test_title_search_can_filter_by_court(self):
        results, _ = self._run_search("--title", "損害賠償", "--court", "最高裁", "--limit", "5")

        self.assertEqual(1, len(results))

    def test_court_filter_can_match_trial_type(self):
        results, _ = self._run_search(
            "--title", "損害賠償", "--court", "SupremeCourt", "--limit", "5"
        )

        self.assertEqual(1, len(results))
        self.assertEqual("令和2(受)123", results[0]["case_number"])

    def test_content_output_keeps_raw_light(self):
        results, _ = self._run_search("--title", "損害賠償", "--content", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertIn("不法行為", results[0]["content"])
        self.assertNotIn("contents", results[0]["raw"])

    def test_metadata_search_stops_before_orphan_details_after_limit(self):
        module = self._load_module()
        calls = []
        original_entry_from_detail = module.entry_from_detail

        def tracking_entry_from_detail(*args, **kwargs):
            calls.append(args[2])
            return original_entry_from_detail(*args, **kwargs)

        module.entry_from_detail = tracking_entry_from_detail
        results = module.metadata_search(self.repo, "title", "損害賠償", limit=1)

        self.assertEqual(1, len(results))
        self.assertEqual([], calls)

    def test_title_search_does_not_match_court_only_fields(self):
        results, _ = self._run_search("--title", "最高裁", "--limit", "5")

        self.assertEqual([], results)

    def test_missing_precedent_directory_exits_nonzero_with_empty_json(self):
        self.repo = Path(self.tmp.name) / "missing_data_set"

        proc = self._run_search_failure("--title", "損害賠償")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("precedent directory not found", proc.stderr)

    def test_malformed_list_json_exits_nonzero_with_empty_json(self):
        (self.precedent_dir / "list.json").write_text("[", encoding="utf-8")

        proc = self._run_search_failure("--title", "損害賠償", "--decade", "2020")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("invalid JSON", proc.stderr)
        self.assertIn("list.json", proc.stderr)

    def test_malformed_selected_detail_json_exits_nonzero_with_empty_json(self):
        detail_path = self.precedent_dir / "令和2(受)123_最高裁判所第一小法廷_SupremeCourt_1.json"
        detail_path.write_text("{", encoding="utf-8")

        proc = self._run_search_failure("--title", "損害賠償", "--decade", "2020")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("invalid JSON", proc.stderr)
        self.assertIn(detail_path.name, proc.stderr)

    def test_explicit_absolute_detail_path_exits_nonzero(self):
        outside_path = Path(self.tmp.name) / "outside.json"
        self._write_json(
            outside_path,
            {
                "case_name": "外部ファイル事件",
                "case_number": "令和2(外)1",
                "contents": "outside",
            },
        )
        item = dict(self.supreme_item)
        item["json_path"] = str(outside_path)
        self._write_json(self.precedent_dir / "list.json", [item])

        proc = self._run_search_failure("--title", "外部ファイル", "--decade", "2020")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("absolute precedent detail path is not allowed", proc.stderr)

    def test_explicit_relative_detail_path_cannot_escape_decade_dir(self):
        outside_path = self.repo / "precedent" / "outside.json"
        self._write_json(
            outside_path,
            {
                "case_name": "外部ファイル事件",
                "case_number": "令和2(外)1",
                "contents": "outside",
            },
        )
        item = dict(self.supreme_item)
        item["json_path"] = "../outside.json"
        self._write_json(self.precedent_dir / "list.json", [item])

        proc = self._run_search_failure("--title", "外部ファイル", "--decade", "2020")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("escapes dataset directory", proc.stderr)

    def test_discovered_detail_symlink_cannot_escape_decade_dir(self):
        outside_path = Path(self.tmp.name) / "outside.json"
        self._write_json(
            outside_path,
            {
                "case_name": "外部ファイル事件",
                "case_number": "令和2(外)777",
                "court_name": "外部裁判所",
                "trial_type": "SupremeCourt",
                "lawsuit_id": "777",
                "contents": "outside",
            },
        )
        link_path = self.precedent_dir / "令和2(外)777_外部裁判所_SupremeCourt_777.json"
        os.symlink(outside_path, link_path)
        self._write_json(
            self.precedent_dir / "list.json",
            [
                {
                    "case_number": "令和2(外)777",
                    "court_name": "外部裁判所",
                    "trial_type": "SupremeCourt",
                    "lawsuit_id": "777",
                }
            ],
        )

        proc = self._run_search_failure("--title", "外部ファイル", "--decade", "2020")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("escapes dataset directory", proc.stderr)

    def test_implicit_decade_symlink_cannot_escape_precedent_dir(self):
        outside_decade = Path(self.tmp.name) / "outside_decade"
        outside_decade.mkdir()
        self._write_json(
            outside_decade / "list.json",
            [
                {
                    "case_name": "外部ディレクトリ事件",
                    "case_number": "令和2(外)888",
                    "court_name": "外部裁判所",
                }
            ],
        )
        symlink_dir = self.repo / "precedent" / "2030"
        os.symlink(outside_decade, symlink_dir)

        proc = self._run_search_failure("--title", "外部ディレクトリ")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("escapes dataset directory", proc.stderr)

    def test_decade_path_escape_exits_nonzero_with_empty_json(self):
        proc = self._run_search_failure("--title", "民法", "--decade", "../law")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("invalid precedent decade", proc.stderr)

    def test_missing_explicit_decade_exits_nonzero_with_empty_json(self):
        proc = self._run_search_failure("--title", "損害賠償", "--decade", "2099")

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("precedent decade directory not found", proc.stderr)


if __name__ == "__main__":
    unittest.main()
