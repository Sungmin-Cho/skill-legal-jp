# legal-jp Dual Skill MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repo-local Japanese legal information skill that works in Claude Code and Codex using the shared `japanese-law-analysis/data_set` repository and deterministic search scripts.

**Architecture:** Keep all agent-facing instructions thin and put repeatable lookup behavior in Python scripts under `.claude/skills/legal-jp/scripts/`. `data_set/` remains the local source clone; scripts read it directly and return JSON so both Claude and Codex can cite the same evidence.

**Tech Stack:** Python 3.10+ standard library, Git, Markdown skill docs, `unittest` for script smoke tests.

---

## File Structure

- Create: `.gitignore` — ignore local dataset clone, outputs, caches, and OS noise.
- Create: `README.md` — project overview, setup, script commands, data/license notes.
- Create: `CLAUDE.md` — Claude Code project orientation and skill routing.
- Create: `AGENTS.md` — Codex project contract and workflow.
- Create: `.claude/skills/legal-jp/SKILL.md` — Claude skill definition and workflow.
- Create: `.claude/skills/legal-jp/scripts/search_law.py` — Japanese law metadata, abbreviation, and replacement-reading search.
- Create: `.claude/skills/legal-jp/scripts/search_precedent.py` — Japanese precedent metadata and JSON/text search.
- Create: `tests/test_search_law.py` — script tests with synthetic `data_set/law` fixtures.
- Create: `tests/test_search_precedent.py` — script tests with synthetic `data_set/precedent` fixtures.
- Runtime local only: `data_set/` — cloned `japanese-law-analysis/data_set`, ignored by git.
- Runtime local only: `outputs/` — generated analysis outputs, ignored by git except optional `.gitkeep` if needed later.

---

### Task 1: Repository Support Files

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `CLAUDE.md`
- Create: `AGENTS.md`

- [ ] **Step 1: Create `.gitignore`**

Write exactly:

```gitignore
.DS_Store
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/

data_set/
outputs/
```

- [ ] **Step 2: Create `README.md`**

Write a concise project README with these sections:

````markdown
# legal-jp

Japanese law and precedent research skill for Claude Code and Codex.

## Overview

This repository provides a repo-local skill modeled after `/Users/sungmin/Dev/legal-kr`.
It uses local data from `japanese-law-analysis/data_set` and deterministic Python scripts to search Japanese law metadata, law abbreviations, replacement-reading data, and precedent JSON files.

## Data Source

- Repository: https://github.com/japanese-law-analysis/data_set
- License: CC0-1.0 as stated by the source repository
- Local path: `data_set/`

The dataset README describes Japanese law and judgment data as non-copyrightable under Japanese Copyright Act Article 13 and releases the generated dataset under CC0.

## Setup

```bash
git clone https://github.com/japanese-law-analysis/data_set.git data_set
```

To refresh the local snapshot:

```bash
git -C data_set pull --ff-only
```

## Usage

Law search:

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py --name 民法 --limit 3
python3 .claude/skills/legal-jp/scripts/search_law.py --abbr 民法 --limit 3
python3 .claude/skills/legal-jp/scripts/search_law.py --yomikae 会社法 --limit 3
```

Precedent search:

```bash
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title 損害賠償 --decade 2020 --limit 3
python3 .claude/skills/legal-jp/scripts/search_precedent.py --text 損害賠償 --decade 2020 --snippet --limit 3
```

## Agent Surfaces

- Claude Code: `.claude/skills/legal-jp/SKILL.md`
- Codex: `AGENTS.md`

## Disclaimer

This project provides AI-assisted legal information from a local dataset snapshot. It is not a substitute for advice from a licensed Japanese legal professional.
````

- [ ] **Step 3: Create `CLAUDE.md`**

Write:

```markdown
# CLAUDE.md — legal-jp

Use `.claude/skills/legal-jp/SKILL.md` for Japanese legal information, law lookup, precedent lookup, and fact-specific Japanese legal research.

## Project Contract

- Use `data_set/` as the source of truth.
- If `data_set/` is missing, clone `https://github.com/japanese-law-analysis/data_set.git`.
- If `data_set/` exists, try `git -C data_set pull --ff-only`; continue with the existing snapshot if update fails.
- Use the scripts under `.claude/skills/legal-jp/scripts/` before answering Japanese legal questions.
- Separate source-backed findings from legal analysis.
- State that answers are based on the local Japanese dataset snapshot and are not legal advice.
- Save requested reports to `outputs/{topic}_{work_type}_YYYYMMDD.md`.
```

- [ ] **Step 4: Create `AGENTS.md`**

Write:

````markdown
# AGENTS.md — legal-jp

## Required Workflow

For Japanese law, precedent, legal research, or fact-specific legal questions:

1. Ensure `data_set/` exists. Clone `https://github.com/japanese-law-analysis/data_set.git` if missing.
2. Try `git -C data_set pull --ff-only`; if it fails, mention that the existing snapshot is being used.
3. Search local evidence with:
   - `python3 .claude/skills/legal-jp/scripts/search_law.py`
   - `python3 .claude/skills/legal-jp/scripts/search_precedent.py`
4. Cite evidence using local paths and metadata returned by the scripts.
5. Separate confirmed source data from legal analysis or practical suggestions.
6. Include the disclaimer that this is AI-assisted legal information, not a substitute for licensed Japanese legal advice.

## Output Files

When the user asks for a report or saved output, create `outputs/` and save Markdown by default:

```text
outputs/{topic}_{work_type}_YYYYMMDD.md
```

Use `.docx`, `.xlsx`, `.pptx`, or `.pdf` only when explicitly requested.
````

- [ ] **Step 5: Commit support files**

Run:

```bash
git add .gitignore README.md CLAUDE.md AGENTS.md
git commit -m "chore: add legal-jp project support files"
```

Expected: commit succeeds.

---

### Task 2: Law Search Script

**Files:**
- Create: `.claude/skills/legal-jp/scripts/search_law.py`
- Create: `tests/test_search_law.py`

- [ ] **Step 1: Create failing tests for law search**

Create `tests/test_search_law.py`:

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "legal-jp" / "scripts" / "search_law.py"


class SearchLawTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        law = self.repo / "law"
        law.mkdir()
        (law / "list.json").write_text(json.dumps([
            {"name": "総務大臣の所管に属する特例民法法人の監督に関する省令", "num": "平成二十年総務省令第百号"},
            {
                "date": {"era": "Meiji", "year": 29, "month": 4, "day": 27},
                "name": "民法",
                "num": "明治二十九年法律第八十九号",
                "id": {"era": "Meiji", "year": 29, "law_id_type": {"Act": {"num": 89}}},
                "patch": [{"patch_date": {"era": "Reiwa", "year": 5, "month": 4, "day": 1}}],
            },
            {"name": "会社法", "num": "平成十七年法律第八十六号"},
        ], ensure_ascii=False), encoding="utf-8")
        (law / "repeal_list.json").write_text(json.dumps([
            {"name": "旧民法", "num": "明治二十三年法律第二十八号"}
        ], ensure_ascii=False), encoding="utf-8")
        (law / "egov_abb.json").write_text(json.dumps([
            {"num": "明治二十九年法律第八十九号", "abbs": ["民法"]}
        ], ensure_ascii=False), encoding="utf-8")
        (law / "law_abb.json").write_text(json.dumps({
            "明治二十九年法律第八十九号": [
                {"num": "明治二十九年法律第八十九号", "name": "民法", "note": None}
            ]
        }, ensure_ascii=False), encoding="utf-8")
        (law / "ryakusyou.json").write_text(json.dumps([
            {
                "num": "平成十七年法律第八十六号",
                "chapter": {"article": "1", "paragraph": "1"},
                "ryakusyou_lst": [{"ryakusyou": "会社法", "seishiki": "会社法"}],
            }
        ], ensure_ascii=False), encoding="utf-8")
        (law / "yomikae.json").write_text(json.dumps([
            {
                "num": "平成十七年法律第八十六号",
                "article": {"article": "1", "paragraph": "1"},
                "data": [{"before_words": ["取締役"], "after_word": "清算人"}],
            }
        ], ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(proc.stdout)

    def test_name_search_finds_active_law(self):
        data = self.run_script("--name", "民法", "--limit", "5")
        self.assertEqual(data[0]["name"], "民法")
        self.assertEqual(data[0]["status"], "active")
        self.assertEqual(data[0]["source_file"], "law/list.json")

    def test_include_repealed_adds_repealed_results(self):
        data = self.run_script("--name", "旧民法", "--include-repealed", "--limit", "5")
        self.assertEqual(data[0]["name"], "旧民法")
        self.assertEqual(data[0]["status"], "repealed")

    def test_abbreviation_search_returns_match_source(self):
        data = self.run_script("--abbr", "民法", "--limit", "5")
        self.assertTrue(any(item["source_file"] == "law/egov_abb.json" for item in data))
        self.assertTrue(any(item.get("abbs") == ["民法"] for item in data))
        self.assertTrue(any(item.get("container_key") == "明治二十九年法律第八十九号" for item in data))

    def test_yomikae_search_returns_text_match(self):
        data = self.run_script("--yomikae", "清算人", "--limit", "5")
        self.assertEqual(data[0]["source_file"], "law/yomikae.json")
        self.assertEqual(data[0]["data"][0]["after_word"], "清算人")
        self.assertIn("清算人", json.dumps(data[0], ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run law tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_search_law.py -v
```

Expected: FAIL because `search_law.py` does not exist yet.

- [ ] **Step 3: Implement `search_law.py`**

Create `.claude/skills/legal-jp/scripts/search_law.py` with:

```python
#!/usr/bin/env python3
"""Search japanese-law-analysis/data_set law JSON files."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


DEFAULT_REPO = os.environ.get(
    "LEGAL_JP_DATA_SET_PATH",
    str(Path(__file__).resolve().parents[4] / "data_set"),
)


def load_json(path: Path) -> Any:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def stream_json_array(path: Path):
    """Yield objects from a top-level JSON array without materializing the file."""
    decoder = json.JSONDecoder()
    with path.open(encoding="utf-8") as f:
        buffer = ""
        eof = False
        started = False
        while True:
            if not eof and len(buffer) < 65536:
                chunk = f.read(65536)
                if chunk:
                    buffer += chunk
                else:
                    eof = True
            buffer = buffer.lstrip()
            if not started:
                if not buffer:
                    if eof:
                        return
                    continue
                if buffer[0] != "[":
                    raise ValueError(f"Expected top-level JSON array: {path}")
                buffer = buffer[1:]
                started = True
                continue
            buffer = buffer.lstrip()
            if buffer.startswith("]"):
                return
            if buffer.startswith(","):
                buffer = buffer[1:]
                continue
            try:
                item, idx = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                if eof:
                    raise
                chunk = f.read(65536)
                if chunk:
                    buffer += chunk
                    continue
                eof = True
                continue
            yield item
            buffer = buffer[idx:]


def with_container_key(value: Any, container_key: str | None) -> dict[str, Any]:
    if isinstance(value, dict):
        item = dict(value)
    else:
        item = {"value": value}
    if container_key is not None:
        item["container_key"] = container_key
    return item


def iter_json_records(path: Path):
    if not path.exists():
        return
    if path.name == "ryakusyou.json":
        for item in stream_json_array(path):
            yield with_container_key(item, None)
        return
    data = load_json(path)
    if isinstance(data, list):
        for item in data:
            yield with_container_key(item, None)
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                for child in value:
                    yield with_container_key(child, str(key))
            else:
                yield with_container_key(value, str(key))


def as_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def contains(value: Any, keyword: str) -> bool:
    return keyword.lower() in as_text(value).lower()


def normalize_name(name: str) -> str:
    return "".join(str(name).split()).lower()


def law_entry(entry: dict[str, Any], source_file: str, status: str, matches: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": entry.get("name") or entry.get("law_name") or entry.get("formal") or entry.get("title"),
        "num": entry.get("num") or entry.get("container_key"),
        "id": entry.get("id"),
        "date": entry.get("date"),
        "source_file": source_file,
        "status": status,
        "patch": entry.get("patch"),
        "matches": matches or [],
        "container_key": entry.get("container_key"),
        "abbs": entry.get("abbs"),
        "ryakusyou_lst": entry.get("ryakusyou_lst"),
        "data": entry.get("data"),
        "article": entry.get("article"),
        "chapter": entry.get("chapter"),
        "raw": entry,
    }


def search_law_names(repo: Path, keyword: str, exact: bool, include_repealed: bool, limit: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    targets = [("law/list.json", "active")]
    if include_repealed:
        targets.append(("law/repeal_list.json", "repealed"))
    normalized_keyword = normalize_name(keyword)
    for rel, status in targets:
        data = load_json(repo / rel)
        if not isinstance(data, list):
            continue
        exact_matches: list[dict[str, Any]] = []
        partial_matches: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            normalized_name = normalize_name(name)
            if normalized_name == normalized_keyword:
                exact_matches.append(item)
            elif not exact and normalized_keyword in normalized_name:
                partial_matches.append(item)
        for item in exact_matches + partial_matches:
            results.append(law_entry(item, rel, status, ["name"]))
            if len(results) >= limit:
                return results
    return results


def search_json_files(repo: Path, rel_files: list[str], keyword: str, limit: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for rel in rel_files:
        if len(results) >= limit:
            return results
        for item in iter_json_records(repo / rel):
            if contains(item, keyword):
                results.append(law_entry(item, rel, "reference", ["text"]))
                if len(results) >= limit:
                    return results
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search japanese-law-analysis/data_set law files")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Path to local data_set repository")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name", help="Search active law names")
    group.add_argument("--exact", help="Exact or normalized law-name lookup")
    group.add_argument("--abbr", help="Search law abbreviation datasets")
    group.add_argument("--yomikae", help="Search replacement-reading data")
    parser.add_argument("--include-repealed", action="store_true", help="Include law/repeal_list.json")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    repo = Path(args.repo)
    if not (repo / "law").exists():
        print(f"data_set/law not found: {repo}", file=sys.stderr)
        print("[]")
        return

    if args.name:
        results = search_law_names(repo, args.name, exact=False, include_repealed=args.include_repealed, limit=args.limit)
    elif args.exact:
        results = search_law_names(repo, args.exact, exact=True, include_repealed=args.include_repealed, limit=args.limit)
    elif args.abbr:
        results = search_json_files(repo, ["law/egov_abb.json", "law/law_abb.json", "law/ryakusyou.json"], args.abbr, args.limit)
    elif args.yomikae:
        results = search_json_files(repo, ["law/yomikae.json"], args.yomikae, args.limit)
    else:
        results = []

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run law tests and verify pass**

Run:

```bash
python3 -m unittest tests/test_search_law.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit law script**

Run:

```bash
git add .claude/skills/legal-jp/scripts/search_law.py tests/test_search_law.py
git commit -m "feat: add legal-jp law search"
```

Expected: commit succeeds.

---

### Task 3: Precedent Search Script

**Files:**
- Create: `.claude/skills/legal-jp/scripts/search_precedent.py`
- Create: `tests/test_search_precedent.py`

- [ ] **Step 1: Create failing tests for precedent search**

Create `tests/test_search_precedent.py`:

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "legal-jp" / "scripts" / "search_precedent.py"


class SearchPrecedentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        d2020 = self.repo / "precedent" / "2020"
        d2020.mkdir(parents=True)
        supreme_item = {
            "case_number": "令和2(受)123",
            "court_name": "最高裁判所第一小法廷",
            "date": {"era": "Reiwa", "year": 2, "month": 5, "day": 1},
            "trial_type": "SupremeCourt",
            "lawsuit_id": "1",
        }
        lower_item = {
            "case_number": "令和2(行ウ)999",
            "court_name": "東京地方裁判所",
            "date": {"era": "Reiwa", "year": 2, "month": 6, "day": 1},
            "trial_type": "LowerCourt",
            "lawsuit_id": "1",
        }
        (d2020 / "list.json").write_text(json.dumps([supreme_item, lower_item], ensure_ascii=False), encoding="utf-8")
        (d2020 / "令和2(受)123_最高裁判所第一小法廷_SupremeCourt_1.json").write_text(json.dumps({
            "case_name": "損害賠償請求事件",
            "case_number": "令和2(受)123",
            "court_name": "最高裁判所第一小法廷",
            "contents": "不法行為に基づく損害賠償について判断した。",
            "lawsuit_id": "1",
        }, ensure_ascii=False), encoding="utf-8")
        (d2020 / "令和2(行ウ)999_東京地方裁判所_LowerCourt_1.json").write_text(json.dumps({
            "case_name": "行政処分取消請求事件",
            "case_number": "令和2(行ウ)999",
            "court_name": "東京地方裁判所",
            "contents": "下級審の判断。",
            "lawsuit_id": "1",
        }, ensure_ascii=False), encoding="utf-8")
        (d2020 / "昭和27(オ)1250_最高裁判所第三小法廷_SupremeCourt_73986.json").write_text(json.dumps({
            "case_name": "所有権確認請求事件",
            "case_number": "昭和27(オ)1250",
            "court_name": "最高裁判所第三小法廷",
            "trial_type": "SupremeCourt",
            "lawsuit_id": "73986",
            "contents": "list.jsonにない判例。",
        }, ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(proc.stdout)

    def test_title_search_uses_decade_metadata(self):
        data = self.run_script("--title", "損害賠償", "--limit", "5")
        self.assertEqual(data[0]["title"], "損害賠償請求事件")
        self.assertEqual(data[0]["decade"], "2020")
        self.assertEqual(data[0]["date"], {"era": "Reiwa", "year": 2, "month": 5, "day": 1})

    def test_case_number_search(self):
        data = self.run_script("--case-number", "令和2", "--limit", "5")
        self.assertEqual(data[0]["case_number"], "令和2(受)123")

    def test_case_number_search_matches_lawsuit_id_or_json_path(self):
        data = self.run_script("--case-number", "1", "--limit", "5")
        self.assertEqual(data[0]["json_path"], "precedent/2020/令和2(受)123_最高裁判所第一小法廷_SupremeCourt_1.json")

    def test_duplicate_lawsuit_id_uses_matching_trial_type(self):
        data = self.run_script("--case-number", "令和2(行ウ)999", "--limit", "5")
        self.assertEqual(data[0]["json_path"], "precedent/2020/令和2(行ウ)999_東京地方裁判所_LowerCourt_1.json")

    def test_case_number_search_includes_detail_not_in_list(self):
        data = self.run_script("--case-number", "昭和27(オ)1250", "--limit", "5")
        self.assertEqual(data[0]["json_path"], "precedent/2020/昭和27(オ)1250_最高裁判所第三小法廷_SupremeCourt_73986.json")

    def test_text_search_returns_snippet(self):
        data = self.run_script("--text", "不法行為", "--decade", "2020", "--snippet", "--limit", "5")
        self.assertIn("不法行為", data[0]["snippet"])

    def test_court_filter_limits_results(self):
        data = self.run_script("--title", "損害賠償", "--court", "最高裁", "--limit", "5")
        self.assertEqual(len(data), 1)

    def test_title_search_does_not_match_court_only(self):
        data = self.run_script("--title", "最高裁", "--limit", "5")
        self.assertEqual(data, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run precedent tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_search_precedent.py -v
```

Expected: FAIL because `search_precedent.py` does not exist yet.

- [ ] **Step 3: Implement `search_precedent.py`**

Create `.claude/skills/legal-jp/scripts/search_precedent.py` with:

```python
#!/usr/bin/env python3
"""Search japanese-law-analysis/data_set precedent JSON files."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


DEFAULT_REPO = os.environ.get(
    "LEGAL_JP_DATA_SET_PATH",
    str(Path(__file__).resolve().parents[4] / "data_set"),
)


def load_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return None


def as_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def value_for(entry: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = entry.get(key)
        if value:
            return str(value)
    return ""


def raw_value_for(entry: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = entry.get(key)
        if value:
            return value
    return None


def make_snippet(text: str, keyword: str, context: int = 120) -> str:
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - context)
    end = min(len(text), idx + len(keyword) + context)
    return ("..." if start else "") + text[start:end] + ("..." if end < len(text) else "")


HEAVY_DETAIL_FIELDS = {"contents", "content", "本文", "full_text"}


def build_lawsuit_index(ddir: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in ddir.glob("*.json"):
        if path.name == "list.json":
            continue
        stem = path.stem
        lawsuit_id = stem.rsplit("_", 1)[-1]
        if lawsuit_id:
            index.setdefault(lawsuit_id, []).append(path)
    return index


def detail_matches_entry(path: Path, entry: dict[str, Any]) -> bool:
    detail = load_json(path)
    if not isinstance(detail, dict):
        return False
    for keys in (["case_number", "caseNo", "事件番号", "number"], ["court", "court_name", "裁判所", "courtName"], ["trial_type"]):
        expected = value_for(entry, keys)
        actual = value_for(detail, keys)
        if expected and actual and expected != actual:
            return False
    return True


def discover_json_path(ddir: Path, entry: dict[str, Any], lawsuit_index: dict[str, list[Path]]) -> Path | None:
    explicit = value_for(entry, ["file", "filename", "path"])
    if explicit:
        path = ddir / explicit
        return path if path.exists() else None
    lawsuit_id = value_for(entry, ["lawsuit_id", "id"])
    if not lawsuit_id:
        return None
    candidates = lawsuit_index.get(lawsuit_id, [])
    if not candidates:
        return None
    trial_type = value_for(entry, ["trial_type"])
    if trial_type:
        trial_matches = [path for path in candidates if f"_{trial_type}_{lawsuit_id}" in path.name]
        if len(trial_matches) == 1:
            return trial_matches[0]
    detail_matches = [path for path in candidates if detail_matches_entry(path, entry)]
    if len(detail_matches) == 1:
        return detail_matches[0]
    return candidates[0] if len(candidates) == 1 else None


def load_detail(repo: Path, entry: dict[str, Any]) -> dict[str, Any]:
    json_path = entry.get("json_path")
    if not json_path:
        return {}
    detail = load_json(repo / json_path)
    return detail if isinstance(detail, dict) else {}


def merged_entry(repo: Path, entry: dict[str, Any]) -> dict[str, Any]:
    detail = load_detail(repo, entry)
    merged = dict(detail)
    merged.update(entry)
    return merged


def light_raw(entry: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in entry.items() if k not in HEAVY_DETAIL_FIELDS}


def decade_dirs(repo: Path, decade: str | None) -> list[Path]:
    root = repo / "precedent"
    if decade:
        path = root / decade
        return [path] if path.exists() else []
    if not root.exists():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir())


def metadata_entries(repo: Path, decade: str | None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for ddir in decade_dirs(repo, decade):
        lawsuit_index = build_lawsuit_index(ddir)
        seen_paths: set[str] = set()
        data = load_json(ddir / "list.json")
        items = data if isinstance(data, list) else list(data.values()) if isinstance(data, dict) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            normalized["decade"] = ddir.name
            normalized["source_file"] = str((ddir / "list.json").relative_to(repo))
            json_path = discover_json_path(ddir, normalized, lawsuit_index)
            if json_path:
                normalized["json_path"] = str(json_path.relative_to(repo))
                seen_paths.add(normalized["json_path"])
            results.append(normalized)
        for path in sorted(ddir.glob("*.json")):
            if path.name == "list.json":
                continue
            rel = str(path.relative_to(repo))
            if rel in seen_paths:
                continue
            detail = load_json(path)
            if not isinstance(detail, dict):
                continue
            normalized = light_raw(detail)
            normalized["decade"] = ddir.name
            normalized["source_file"] = rel
            normalized["json_path"] = rel
            results.append(normalized)
    return results


def format_entry(repo: Path, entry: dict[str, Any], content: bool = False, snippet_keyword: str | None = None) -> dict[str, Any]:
    merged = merged_entry(repo, entry)
    title = value_for(merged, ["title", "case_name", "事件名", "name"])
    case_number = value_for(merged, ["case_number", "caseNo", "事件番号", "number"])
    court = value_for(merged, ["court", "court_name", "裁判所", "courtName"])
    item = {
        "title": title,
        "case_number": case_number,
        "court": court,
        "date": raw_value_for(merged, ["date", "judgement_date", "裁判年月日"]),
        "decade": entry.get("decade"),
        "source_file": entry.get("source_file"),
        "json_path": entry.get("json_path"),
        "raw": light_raw(entry),
    }
    detail = load_detail(repo, entry)
    if content and detail:
        item["content"] = detail
    if snippet_keyword and detail:
        snippet = make_snippet(as_text(detail), snippet_keyword)
        if snippet:
            item["snippet"] = snippet
    return item


def field_haystack(repo: Path, entry: dict[str, Any], fields: list[str]) -> str:
    merged = merged_entry(repo, entry)
    return " ".join(value_for(merged, [field]) for field in fields)


def metadata_search(repo: Path, args: argparse.Namespace, keyword: str, fields: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for entry in metadata_entries(repo, args.decade):
        merged = merged_entry(repo, entry)
        if args.court and args.court.lower() not in value_for(merged, ["court", "court_name", "裁判所", "courtName"]).lower():
            continue
        haystack = field_haystack(repo, entry, fields)
        if keyword.lower() in haystack.lower():
            results.append(format_entry(repo, entry, content=args.content, snippet_keyword=keyword if args.snippet else None))
            if len(results) >= args.limit:
                break
    return results


def text_search(repo: Path, args: argparse.Namespace, keyword: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    entries = metadata_entries(repo, args.decade)
    path_to_entry = {entry.get("json_path"): entry for entry in entries if entry.get("json_path")}
    for ddir in decade_dirs(repo, args.decade):
        for path in sorted(ddir.glob("*.json")):
            if path.name == "list.json":
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except (FileNotFoundError, PermissionError):
                continue
            if keyword.lower() not in text.lower():
                continue
            rel = str(path.relative_to(repo))
            entry = dict(path_to_entry.get(rel, {}))
            entry.setdefault("json_path", rel)
            entry.setdefault("source_file", rel)
            entry.setdefault("decade", path.parent.name)
            merged = merged_entry(repo, entry)
            if args.court and args.court.lower() not in value_for(merged, ["court", "court_name", "裁判所", "courtName"]).lower():
                continue
            results.append(format_entry(repo, entry, content=args.content, snippet_keyword=keyword if args.snippet else None))
            if len(results) >= args.limit:
                return results
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search japanese-law-analysis/data_set precedent files")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Path to local data_set repository")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--title", help="Search title/case-name metadata")
    group.add_argument("--case-number", help="Search case number metadata")
    group.add_argument("--text", help="Search individual precedent JSON files")
    parser.add_argument("--court", help="Filter by court name or court type")
    parser.add_argument("--decade", help="Restrict to one decade directory, e.g. 2020")
    parser.add_argument("--content", action="store_true", help="Include parsed JSON content")
    parser.add_argument("--snippet", action="store_true", help="Include keyword context")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    repo = Path(args.repo)
    if not (repo / "precedent").exists():
        print(f"data_set/precedent not found: {repo}", file=sys.stderr)
        print("[]")
        return

    if args.title:
        results = metadata_search(repo, args, args.title, ["title", "case_name", "事件名", "name"])
    elif args.case_number:
        results = metadata_search(repo, args, args.case_number, ["case_number", "caseNo", "事件番号", "number", "file", "filename", "path", "json_path", "lawsuit_id"])
    elif args.text:
        results = text_search(repo, args, args.text)
    else:
        results = []

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run precedent tests and verify pass**

Run:

```bash
python3 -m unittest tests/test_search_precedent.py -v
```

Expected: 8 tests pass.

- [ ] **Step 5: Commit precedent script**

Run:

```bash
git add .claude/skills/legal-jp/scripts/search_precedent.py tests/test_search_precedent.py
git commit -m "feat: add legal-jp precedent search"
```

Expected: commit succeeds.

---

### Task 4: Claude Skill Workflow

**Files:**
- Create: `.claude/skills/legal-jp/SKILL.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Create `.claude/skills/legal-jp/SKILL.md`**

Write:

````markdown
---
name: legal-jp
description: "Japanese legal information and precedent research skill for Japan law questions. Use for Japanese law lookup, precedent lookup, legal research, statute metadata, abbreviations, e-Gov law data, 裁判例, 判例, 法令, 法律相談, 日本法, 일본 법률, 일본 판례, 일본 법령, 법률 상담, 법령 검색, 판례 검색, 계약, 소송, 손해배상, 노동, 상속, 형사, 민사, 행정, 조문, 판결, legal, law, precedent. Activates when the user asks about Japanese legal issues or asks to search/analyze Japanese laws or cases using local data."
---

# Japanese Legal Information Skill

You research Japanese legal information using the local `japanese-law-analysis/data_set` snapshot.

## Core Rules

1. Use local source data before answering Japanese legal questions.
2. Separate source-backed facts from analysis or practical suggestions.
3. State the local dataset snapshot basis.
4. Do not present the answer as legal advice from a licensed Japanese lawyer.
5. Ask clarifying questions for fact-specific consultations when required facts are missing.

## Data Source

| Source | Path | Contents |
|--------|------|----------|
| data_set | `${SKILL_DIR}/../../../data_set` | Japanese law metadata, abbreviation data, replacement-reading data, and precedent JSON |

Primary source repository: `https://github.com/japanese-law-analysis/data_set`

## Dependencies

Python 3.10+ and Git. Search scripts use only the Python standard library.

## Workflow

### Step 1: Ensure Local Data

```bash
if [ -d "${SKILL_DIR}/../../../data_set/.git" ]; then
  git -C "${SKILL_DIR}/../../../data_set" pull --ff-only 2>/dev/null && echo "data_set updated" || echo "data_set update failed; using existing snapshot"
else
  git clone https://github.com/japanese-law-analysis/data_set.git "${SKILL_DIR}/../../../data_set"
fi
```

If clone or update fails, clearly state that local data is unavailable or stale.

### Step 2: Classify the Request

Direct lookup:
- Named law, statute metadata, abbreviation, replacement-reading data, precedent, or keyword search.
- Proceed directly to search.

Consultation:
- User describes a real situation and asks what to do or whether conduct is legal.
- Ask one concise clarifying question at a time if the legal field, parties, core facts, timing, amount, or desired outcome are missing.
- When enough facts are available, summarize the facts and ask whether to proceed with law and precedent research.

### Step 3: Search Law Data

Use:

```bash
python3 "${SKILL_DIR}/scripts/search_law.py" --name "民法" --limit 5
python3 "${SKILL_DIR}/scripts/search_law.py" --exact "民法" --include-repealed --limit 5
python3 "${SKILL_DIR}/scripts/search_law.py" --abbr "民法" --limit 5
python3 "${SKILL_DIR}/scripts/search_law.py" --yomikae "会社法" --limit 5
```

Search active laws first. Use `--include-repealed` only when history, old law, or repeal status matters.

### Step 4: Search Precedent Data

Use:

```bash
python3 "${SKILL_DIR}/scripts/search_precedent.py" --title "損害賠償" --decade 2020 --limit 5
python3 "${SKILL_DIR}/scripts/search_precedent.py" --case-number "令和2" --limit 5
python3 "${SKILL_DIR}/scripts/search_precedent.py" --text "損害賠償" --decade 2020 --snippet --limit 5
```

Prefer metadata/title search first. Use `--text` with `--decade` when possible to limit scanning.

### Step 5: Analyze

Structure the reasoning:

- Confirmed law data: names, IDs, numbers, status, source file.
- Confirmed precedent data: title, case number, court, date, source file or JSON path.
- Analysis: how the source data may relate to the user's issue.
- Limitations: missing full article text, stale local snapshot, or uncertain facts.

### Step 6: Output

Use this default answer structure for substantive analysis:

```markdown
## 일본 법률 정보

### 1. 쟁점
### 2. 확인한 법령 데이터
### 3. 확인한 판례 데이터
### 4. 분석
### 5. 실무상 확인할 점
### 6. 한계 및 면책
```

For direct lookup, a shorter answer is acceptable.

Always include:

> 이 답변은 로컬 `japanese-law-analysis/data_set` 스냅샷을 바탕으로 한 AI 법률 정보이며, 일본 변호사의 법률 자문을 대체하지 않습니다.

## Saving Outputs

Save a file only when the user asks for a report or saved output. Default path:

```text
outputs/{topic}_{work_type}_YYYYMMDD.md
```
````

- [ ] **Step 2: Align `AGENTS.md` with script names**

Append this exact section if it is not already present:

````markdown
## Script Reference

Law:

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py --name 民法 --limit 3
python3 .claude/skills/legal-jp/scripts/search_law.py --abbr 民法 --limit 3
```

Precedent:

```bash
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title 損害賠償 --decade 2020 --limit 3
python3 .claude/skills/legal-jp/scripts/search_precedent.py --text 損害賠償 --decade 2020 --snippet --limit 3
```
````

- [ ] **Step 3: Validate skill frontmatter manually**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
p = Path(".claude/skills/legal-jp/SKILL.md")
text = p.read_text(encoding="utf-8")
assert text.startswith("---\n")
assert "\nname: legal-jp\n" in text
assert "\ndescription: " in text
assert "\n---\n" in text[4:]
print("SKILL.md frontmatter ok")
PY
```

Expected: `SKILL.md frontmatter ok`

- [ ] **Step 4: Commit skill workflow**

Run:

```bash
git add .claude/skills/legal-jp/SKILL.md AGENTS.md
git commit -m "feat: add legal-jp agent workflows"
```

Expected: commit succeeds.

---

### Task 5: Data Clone and End-to-End Validation

**Files:**
- Runtime only: `data_set/`
- Modify only if validation exposes a defect: scripts or docs from earlier tasks.

- [ ] **Step 1: Clone or update data source**

Run:

```bash
if [ -d data_set/.git ]; then
  git -C data_set pull --ff-only
else
  git clone https://github.com/japanese-law-analysis/data_set.git data_set
fi
```

Expected: `data_set/` exists and contains `law/list.json` and `precedent/2020/`.

- [ ] **Step 2: Run unit tests**

Run:

```bash
python3 -m unittest tests/test_search_law.py tests/test_search_precedent.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Run law smoke commands**

Run:

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py --name 民法 --limit 3
python3 .claude/skills/legal-jp/scripts/search_law.py --abbr 民法 --limit 3
```

Expected: both commands return valid JSON and at least one of them returns a non-empty array.

- [ ] **Step 4: Run precedent smoke commands**

Run:

```bash
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title 損害賠償 --decade 2020 --limit 3
python3 .claude/skills/legal-jp/scripts/search_precedent.py --text 損害賠償 --decade 2020 --snippet --limit 3
```

Expected: both commands return valid JSON and at least one of them returns a non-empty array.

- [ ] **Step 5: Run real-data integration assertions**

Run:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

def run(args):
    proc = subprocess.run(args, check=True, capture_output=True, text=True, timeout=30)
    return json.loads(proc.stdout)

law = run(["python3", ".claude/skills/legal-jp/scripts/search_law.py", "--name", "民法", "--limit", "3"])
if not law:
    first_law = json.loads(Path("data_set/law/list.json").read_text(encoding="utf-8"))[0]["name"]
    law = run(["python3", ".claude/skills/legal-jp/scripts/search_law.py", "--exact", first_law, "--limit", "1"])
assert law, "law search returned no real-data result"
assert law[0].get("name") == "民法", law[0]
assert law[0].get("source_file"), law[0]
assert law[0].get("name"), law[0]

precedent = run([
    "python3", ".claude/skills/legal-jp/scripts/search_precedent.py",
    "--text", "損害賠償", "--decade", "2020", "--snippet", "--limit", "1"
])
if not precedent:
    first_meta = json.loads(Path("data_set/precedent/2020/list.json").read_text(encoding="utf-8"))[0]
    precedent = run([
        "python3", ".claude/skills/legal-jp/scripts/search_precedent.py",
        "--case-number", first_meta["case_number"], "--decade", "2020", "--limit", "1"
    ])
assert precedent, "precedent search returned no real-data result"
assert precedent[0].get("source_file") or precedent[0].get("json_path"), precedent[0]
if precedent[0].get("json_path"):
    assert (Path("data_set") / precedent[0]["json_path"]).exists(), precedent[0]["json_path"]

print("real-data integration assertions ok")
PY
```

Expected: `real-data integration assertions ok`; any individual command taking longer than 30 seconds fails the gate.

- [ ] **Step 6: Run a workflow smoke prompt**

Run this manual smoke check using the written `SKILL.md` and `AGENTS.md` workflow:

```text
Prompt: 일본 민법에 대해 확인 가능한 법령 데이터와 관련 손해배상 판례를 로컬 data_set 기준으로 요약해줘.
```

Expected answer properties:

- Uses `search_law.py` and `search_precedent.py` results from local `data_set/`.
- Cites at least one local law source such as `law/list.json` or `law/law_abb.json`.
- Cites at least one local precedent `source_file` or `json_path`.
- Separates confirmed source data from analysis.
- Includes the Japanese legal-advice disclaimer from `SKILL.md`.

- [ ] **Step 7: Final commit for validation fixes**

If validation required fixes, commit them:

```bash
git add .claude/skills/legal-jp/scripts tests README.md CLAUDE.md AGENTS.md .claude/skills/legal-jp/SKILL.md
git commit -m "fix: stabilize legal-jp search validation"
```

Expected: commit succeeds only if there are changes. If no changes, skip.

- [ ] **Step 8: Final status**

Run:

```bash
git status --short --branch
```

Expected: clean except ignored `data_set/` and `outputs/`.
