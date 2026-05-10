from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentDocsTest(unittest.TestCase):
    def test_codex_workflow_requires_dataset_provenance(self):
        content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("dataset provenance", content)
        self.assertIn("git -C data_set rev-parse --short HEAD", content)
        self.assertIn("git -C data_set log -1 --format=%cs", content)
        self.assertIn("commit/date provenance", content)


if __name__ == "__main__":
    unittest.main()
