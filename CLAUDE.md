# CLAUDE.md - legal-jp

This file is the Claude Code project guide for `legal-jp`.

Use `.claude/skills/legal-jp/SKILL.md` for Japanese legal information, law lookup, precedent lookup, and fact-specific Japanese legal research.

## Project Overview

`legal-jp` is a repo-local Japanese legal information skill modeled after `/Users/sungmin/Dev/legal-kr`.

- Source data: `japanese-law-analysis/data_set`
- Local data path: `data_set/`
- Claude skill: `.claude/skills/legal-jp/SKILL.md`
- Codex project skill: `.agents/skills/legal-jp/SKILL.md`
- Codex plugin manifest: `.codex-plugin/plugin.json`
- Search scripts: `.claude/skills/legal-jp/scripts/`
- Saved outputs: `outputs/`

The repository does not track `data_set/`, `docs/`, or `outputs/`.

## Required Workflow

For Japanese law, precedent, legal research, or fact-specific legal questions:

1. Use the `legal-jp` skill before answering.
2. Ensure `data_set/` exists. Clone `https://github.com/japanese-law-analysis/data_set.git` if missing.
3. If `data_set/` exists, try `git -C data_set pull --ff-only`; continue with the existing snapshot if update fails and state that limitation.
4. Record dataset provenance before every substantive legal answer or saved report:

```bash
git -C data_set rev-parse --short HEAD
git -C data_set log -1 --format=%cs
```

5. Use the local scripts before answering:

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py --name "民法" --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title "損害賠償" --decade 2020 --limit 5
```

6. Separate source-backed facts from analysis or practical suggestions.
7. Include dataset commit/date provenance in every substantive answer or saved report.
8. State that the answer is AI-assisted legal information based on a local Japanese dataset snapshot and is not a substitute for licensed Japanese legal advice.

## Repository Structure

```text
legal-jp/
├── .claude/skills/legal-jp/
│   ├── SKILL.md
│   └── scripts/
│       ├── search_law.py
│       └── search_precedent.py
├── tests/
├── .agents/skills/legal-jp/
├── .codex-plugin/plugin.json
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── README.ko.md
├── data_set/
└── outputs/
```

## Evidence Rules

- Treat `data_set/` as the local source of truth.
- Cite local paths, law metadata, case metadata, and script output when available.
- If the dataset cannot be cloned, updated, or inspected, say so explicitly.
- Do not invent article text, court holdings, dates, case numbers, or data counts.
- Ask a concise clarifying question when key facts are missing for a consultation.

## Output Rules

Save a file only when the user asks for a report or saved output. Create `outputs/` if needed.

Default path:

```text
outputs/{topic}_{work_type}_YYYYMMDD.md
```

Use `.docx`, `.xlsx`, `.pptx`, or `.pdf` only when the user explicitly requests that format.

After saving, provide a file link and a brief summary of what was saved.
