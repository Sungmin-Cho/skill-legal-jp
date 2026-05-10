import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "legal-jp" / "scripts" / "search_law.py"


class SearchLawTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "data_set"
        law_dir = self.repo / "law"
        law_dir.mkdir(parents=True)

        self._write_json(
            law_dir / "list.json",
            [
                {
                    "name": "総務大臣の所管に属する特例民法法人の監督に関する省令",
                    "num": "平成二十年総務省令第百号",
                    "date": {"era": "平成", "year": 20},
                    "id": {"law_id": "dummy"},
                    "patch": [],
                },
                {
                    "name": "民法",
                    "num": "明治二十九年法律第八十九号",
                    "date": {"era": "明治", "year": 29, "month": 4, "day": 27},
                    "id": {"law_id": "129AC0000000089"},
                    "patch": [{"date": "2026-04-01", "type": "amendment"}],
                },
                {
                    "name": "会社法",
                    "num": "平成十七年法律第八十六号",
                    "date": {"era": "平成", "year": 17, "month": 7, "day": 26},
                    "id": {"law_id": "417AC0000000086"},
                    "patch": [],
                },
            ],
        )
        self._write_json(
            law_dir / "repeal_list.json",
            [
                {
                    "name": "旧民法",
                    "num": "明治二十三年法律第二十八号",
                    "date": {"era": "明治", "year": 23},
                    "id": {"law_id": "old-civil-code"},
                    "patch": [],
                }
            ],
        )
        self._write_json(
            law_dir / "egov_abb.json",
            [{"num": "明治二十九年法律第八十九号", "abbs": ["民法"]}],
        )
        self._write_json(
            law_dir / "law_abb.json",
            {
                "明治二十九年法律第八十九号": [
                    {
                        "num": "明治二十九年法律第八十九号",
                        "name": "民法",
                        "note": "民法の法令略称",
                    }
                ]
            },
        )
        self._write_json(
            law_dir / "ryakusyou.json",
            [
                {
                    "chapter": "会社法",
                    "ryakusyou_lst": [
                        {
                            "num": "平成十七年法律第八十六号",
                            "name": "会社法",
                            "abb": "会社法",
                        }
                    ],
                }
            ],
        )
        self._write_json(
            law_dir / "yomikae.json",
            [
                {
                    "article": "第九百三十六条",
                    "data": [{"before_word": "取締役", "after_word": "清算人"}],
                }
            ],
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

    def test_missing_law_directory_exits_nonzero_with_empty_json(self):
        missing_repo = Path(self.tmp.name) / "missing_data_set"

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(missing_repo), "--name", "民法"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("law directory not found", proc.stderr)

    def test_missing_required_law_list_exits_nonzero_with_empty_json(self):
        (self.repo / "law" / "list.json").unlink()

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--name", "民法"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("JSON file not found", proc.stderr)
        self.assertIn("list.json", proc.stderr)

    def test_malformed_required_law_list_exits_nonzero_with_empty_json(self):
        (self.repo / "law" / "list.json").write_text("[", encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--name", "民法"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("invalid JSON", proc.stderr)
        self.assertIn("list.json", proc.stderr)

    def test_name_search_ranks_exact_active_minpo_first(self):
        results, _ = self._run_search("--name", "民法", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual("民法", results[0]["name"])
        self.assertEqual("active", results[0]["status"])
        self.assertEqual("law/list.json", results[0]["source_file"])

    def test_name_search_can_include_repealed_laws(self):
        results, _ = self._run_search("--name", "旧民法", "--include-repealed", "--limit", "5")

        repealed = [result for result in results if result["name"] == "旧民法"]
        self.assertEqual("repealed", repealed[0]["status"])

    def test_include_repealed_ranks_exact_before_active_partials(self):
        self._write_json(
            self.repo / "law" / "list.json",
            [
                {"name": "旧特別措置法施行規則", "num": "令和元年府令第一号"},
                {"name": "旧特別措置法施行令", "num": "令和元年政令第二号"},
            ],
        )
        self._write_json(
            self.repo / "law" / "repeal_list.json",
            [{"name": "旧特別措置法", "num": "昭和四十年法律第一号"}],
        )

        results, _ = self._run_search(
            "--name", "旧特別措置法", "--include-repealed", "--limit", "1"
        )

        self.assertEqual("旧特別措置法", results[0]["name"])
        self.assertEqual("repealed", results[0]["status"])

    def test_abbr_search_includes_egov_and_container_key_results(self):
        results, _ = self._run_search("--abbr", "民法", "--limit", "5")

        self.assertEqual("民法", results[0]["name"])
        self.assertEqual("law/list.json", results[0]["source_file"])
        self.assertTrue(any(result["source_file"] == "law/egov_abb.json" for result in results))
        self.assertTrue(any(result["abbs"] == ["民法"] for result in results))
        self.assertTrue(
            any(result["container_key"] == "明治二十九年法律第八十九号" for result in results)
        )

    def test_missing_required_abbr_source_exits_nonzero_with_empty_json(self):
        (self.repo / "law" / "egov_abb.json").unlink()

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--abbr", "民法"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("JSON file not found", proc.stderr)
        self.assertIn("egov_abb.json", proc.stderr)

    def test_malformed_required_ryakusyou_exits_nonzero_with_empty_json(self):
        (self.repo / "law" / "ryakusyou.json").write_text('[{"chapter":"x"}', encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--abbr", "存在しない略称"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("unterminated JSON array", proc.stderr)
        self.assertIn("ryakusyou.json", proc.stderr)

    def test_trailing_garbage_in_required_ryakusyou_exits_nonzero_with_empty_json(self):
        (self.repo / "law" / "ryakusyou.json").write_text(
            '[{"chapter":"x","ryakusyou_lst":[{"ryakusyou":"存在しない略称"}]}] trailing',
            encoding="utf-8",
        )

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--abbr", "存在しない略称"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("trailing data", proc.stderr)
        self.assertIn("ryakusyou.json", proc.stderr)

    def test_yomikae_search_preserves_matching_data(self):
        results, stdout = self._run_search("--yomikae", "清算人", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual("law/yomikae.json", results[0]["source_file"])
        self.assertEqual("清算人", results[0]["data"][0]["after_word"])
        self.assertIn("清算人", stdout)


if __name__ == "__main__":
    unittest.main()
