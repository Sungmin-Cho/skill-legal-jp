from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentDocsTest(unittest.TestCase):
    def assert_provenance_contract(self, content):
        self.assertIn("dataset", content)
        self.assertIn("provenance", content)
        self.assertIn("rev-parse --short HEAD", content)
        self.assertIn("log -1 --format=%cs", content)
        self.assertIn("commit/date provenance", content)

    def test_codex_workflow_requires_dataset_provenance(self):
        self.assert_provenance_contract((ROOT / "AGENTS.md").read_text(encoding="utf-8"))

    def test_claude_skill_requires_dataset_provenance(self):
        self.assert_provenance_contract(
            (ROOT / ".claude" / "skills" / "legal-jp" / "SKILL.md").read_text(
                encoding="utf-8"
            )
        )

    def test_codex_project_skill_requires_dataset_provenance(self):
        content = (
            ROOT / ".agents" / "skills" / "legal-jp" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assert_provenance_contract(content)
        self.assertIn(".claude/skills/legal-jp/scripts", content)
        self.assertIn("pull --ff-only", content)


if __name__ == "__main__":
    unittest.main()
