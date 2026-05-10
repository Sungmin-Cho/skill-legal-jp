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

    def _run_search_failure(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

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
        self.assertTrue(all(result["name"] for result in results))

    def test_abbr_search_hydrates_source_hits_to_canonical_laws(self):
        law_dir = self.repo / "law"
        laws = json.loads((law_dir / "list.json").read_text(encoding="utf-8"))
        laws.extend(
            [
                {"name": "労働基準法", "num": "昭和二十二年法律第四十九号"},
                {"name": "沖縄の復帰に伴う労働省関係法令の適用の特別措置等に関する政令", "num": "昭和四十七年政令第百五十六号"},
            ]
        )
        self._write_json(law_dir / "list.json", laws)
        self._write_json(law_dir / "egov_abb.json", [{"num": "昭和二十二年法律第四十九号", "abbs": ["労基法"]}])
        self._write_json(
            law_dir / "law_abb.json",
            {
                "昭和四十七年労働省令第十八号": [
                    {"num": "昭和二十二年法律第四十九号", "name": "労基法"}
                ]
            },
        )
        self._write_json(
            law_dir / "ryakusyou.json",
            [
                {
                    "num": "昭和四十七年政令第百五十六号",
                    "ryakusyou_lst": [{"ryakusyou": "労基法", "seishiki": "労働基準法"}],
                }
            ],
        )

        results, _ = self._run_search("--abbr", "労基法", "--limit", "5")

        self.assertEqual(1, len(results))
        self.assertEqual("労働基準法", results[0]["name"])
        self.assertEqual("昭和二十二年法律第四十九号", results[0]["num"])
        self.assertEqual("law/list.json", results[0]["source_file"])
        self.assertNotEqual("昭和四十七年政令第百五十六号", results[0]["num"])

    def test_abbr_search_keeps_unresolved_ryakusyou_usage_evidence(self):
        laws = json.loads((self.repo / "law" / "list.json").read_text(encoding="utf-8"))
        laws.append(
            {
                "name": "経済産業省・財務省・内閣府関係株式会社商工組合中央金庫法施行規則",
                "num": "平成二十年内閣府・財務省・経済産業省令第一号",
            }
        )
        self._write_json(self.repo / "law" / "list.json", laws)
        self._write_json(
            self.repo / "law" / "ryakusyou.json",
            [
                {
                    "num": "平成二十年内閣府・財務省・経済産業省令第一号",
                    "chapter": {"chapter": 4, "article": "83"},
                    "ryakusyou_lst": [
                        {
                            "ryakusyou": "報酬等",
                            "seishiki": "報酬、賞与その他の職務執行の対価",
                        }
                    ],
                }
            ],
        )

        results, _ = self._run_search("--abbr", "報酬等", "--limit", "5")

        self.assertEqual(1, len(results))
        self.assertIsNone(results[0]["name"])
        self.assertEqual("abbreviation_usage", results[0]["status"])
        self.assertEqual("law/ryakusyou.json", results[0]["source_file"])
        self.assertEqual("平成二十年内閣府・財務省・経済産業省令第一号", results[0]["num"])
        self.assertEqual("報酬等", results[0]["ryakusyou_lst"][0]["ryakusyou"])

    def test_abbr_search_keeps_multiple_unresolved_ryakusyou_usages_for_same_law(self):
        law_num = "平成二十年内閣府・財務省・経済産業省令第一号"
        laws = json.loads((self.repo / "law" / "list.json").read_text(encoding="utf-8"))
        laws.append({"name": "株式会社商工組合中央金庫法施行規則", "num": law_num})
        self._write_json(self.repo / "law" / "list.json", laws)
        self._write_json(
            self.repo / "law" / "ryakusyou.json",
            [
                {
                    "num": law_num,
                    "chapter": {"chapter": 4, "article": "83"},
                    "ryakusyou_lst": [
                        {
                            "ryakusyou": "報酬等",
                            "seishiki": "報酬、賞与その他の職務執行の対価",
                        }
                    ],
                },
                {
                    "num": law_num,
                    "chapter": {"chapter": 5, "article": "84"},
                    "ryakusyou_lst": [
                        {
                            "ryakusyou": "報酬等",
                            "seishiki": "報酬その他これに準ずる対価",
                        }
                    ],
                },
            ],
        )

        results, _ = self._run_search("--abbr", "報酬等", "--limit", "5")

        usages = [result for result in results if result["status"] == "abbreviation_usage"]
        self.assertEqual(2, len(usages))
        self.assertEqual([{"chapter": 4, "article": "83"}, {"chapter": 5, "article": "84"}], [result["chapter"] for result in usages])

    def test_abbr_search_does_not_match_ryakusyou_formal_text_only(self):
        self._write_json(
            self.repo / "law" / "ryakusyou.json",
            [
                {
                    "num": "平成二十年内閣府・財務省・経済産業省令第一号",
                    "ryakusyou_lst": [
                        {
                            "ryakusyou": "改正法",
                            "seishiki": "民法の一部を改正する法律",
                        }
                    ],
                }
            ],
        )

        results, _ = self._run_search("--abbr", "民法", "--limit", "10")

        self.assertTrue(all(result["status"] != "abbreviation_usage" for result in results))
        self.assertTrue(all(result["ryakusyou_lst"] is None for result in results))

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

    def test_unreadable_required_ryakusyou_exits_nonzero_with_empty_json(self):
        path = self.repo / "law" / "ryakusyou.json"
        path.chmod(0)
        try:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--abbr", "存在しない略称"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
        finally:
            path.chmod(0o644)

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("unreadable JSON file", proc.stderr)
        self.assertIn("ryakusyou.json", proc.stderr)

    def test_required_ryakusyou_directory_exits_nonzero_with_empty_json(self):
        path = self.repo / "law" / "ryakusyou.json"
        path.unlink()
        path.mkdir()

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
        self.assertIn("unreadable JSON file", proc.stderr)
        self.assertIn("ryakusyou.json", proc.stderr)

    def test_abbr_validates_later_required_sources_even_when_limit_is_filled(self):
        (self.repo / "law" / "ryakusyou.json").unlink()

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--abbr", "民法", "--limit", "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(2, proc.returncode)
        self.assertEqual([], json.loads(proc.stdout))
        self.assertIn("JSON file not found", proc.stderr)
        self.assertIn("ryakusyou.json", proc.stderr)

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

    def test_malformed_ryakusyou_array_separators_exit_nonzero_with_empty_json(self):
        malformed_payloads = [
            '[{"chapter":"x"} {"chapter":"y"}]',
            '[,{"chapter":"x"}]',
            '[{"chapter":"x"},,{"chapter":"y"}]',
            '[{"chapter":"x"},]',
        ]
        for payload in malformed_payloads:
            with self.subTest(payload=payload):
                (self.repo / "law" / "ryakusyou.json").write_text(payload, encoding="utf-8")

                proc = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--repo",
                        str(self.repo),
                        "--abbr",
                        "存在しない略称",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )

                self.assertEqual(2, proc.returncode)
                self.assertEqual([], json.loads(proc.stdout))
                self.assertIn("JSON array", proc.stderr)
                self.assertIn("ryakusyou.json", proc.stderr)

    def test_yomikae_search_preserves_matching_data(self):
        results, stdout = self._run_search("--yomikae", "清算人", "--limit", "5")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual("law/yomikae.json", results[0]["source_file"])
        self.assertEqual("清算人", results[0]["data"][0]["after_word"])
        self.assertIn("清算人", stdout)

    def test_empty_law_queries_exit_nonzero_with_empty_json(self):
        cases = [
            ("--name", ""),
            ("--name", "   "),
            ("--exact", ""),
            ("--abbr", " \t "),
            ("--yomikae", ""),
        ]
        for option, value in cases:
            with self.subTest(option=option, value=value):
                proc = self._run_search_failure(option, value)

                self.assertEqual(2, proc.returncode)
                self.assertEqual([], json.loads(proc.stdout))
                self.assertIn("empty", proc.stderr)


if __name__ == "__main__":
    unittest.main()
