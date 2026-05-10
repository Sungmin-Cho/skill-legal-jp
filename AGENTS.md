# AGENTS.md - legal-jp

This file is the Codex project guide for `legal-jp`.

Use the `$legal-jp` project skill for Japanese legal information, law lookup, precedent lookup, and fact-specific Japanese legal research. The Codex project skill body is `.agents/skills/legal-jp/SKILL.md`.

## Project Overview

`legal-jp` is a repo-local Japanese legal information skill modeled after `/Users/sungmin/Dev/legal-kr`.

- Source data: `japanese-law-analysis/data_set`
- Local data path: `data_set/`
- Claude skill: `.claude/skills/legal-jp/SKILL.md`
- Codex project skill: `.agents/skills/legal-jp/SKILL.md`
- Shared search scripts: `.claude/skills/legal-jp/scripts/`
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

If either command fails, explicitly state that dataset commit/date provenance could not be determined.

5. Use the local scripts before answering:

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py --name "民法" --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title "損害賠償" --decade 2020 --limit 5
```

6. Separate source-backed facts from analysis or practical suggestions.
7. Include dataset commit/date provenance in every substantive answer or saved report.
8. State that the answer is AI-assisted legal information based on a local Japanese dataset snapshot and is not a substitute for licensed Japanese legal advice.

## Data Source

| Source | Local path | Contents |
|--------|------------|----------|
| `japanese-law-analysis/data_set` | `data_set/` | Japanese law metadata, abbreviation data, replacement-reading data, and precedent JSON |

`data_set/` is ignored by git and should remain local. Do not commit downloaded source data or generated `outputs/` reports unless the user explicitly changes the repository policy.

## Script Reference

Law:

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py --name "民法" --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --exact "民法" --include-repealed --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --abbr "敷金" --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --yomikae "会社法" --limit 5
```

Precedent:

```bash
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title "損害賠償" --decade 2020 --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --case-number "令和2" --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --text "損害賠償" --decade 2020 --snippet --limit 5
```

## Evidence Rules

- Treat `data_set/` as the local source of truth.
- Cite local paths, law metadata, case metadata, and script output when available.
- If the dataset cannot be cloned, updated, or inspected, say so explicitly.
- Do not invent article text, court holdings, dates, case numbers, or data counts.
- Ask a concise clarifying question when key facts are missing for a consultation.

## Answer Shape

For substantive analysis, prefer:

```markdown
## 일본 법률 정보

### 1. 쟁점
### 2. 데이터셋 출처
### 3. 확인한 법령 데이터
### 4. 확인한 판례 데이터
### 5. 분석
### 6. 실무상 확인할 점
### 7. 한계 및 면책
```

For direct lookup, a shorter answer is acceptable, but it still needs dataset provenance and a disclaimer when it is a substantive legal answer.

## Output Rules

Save a file only when the user asks for a report or saved output. Create `outputs/` if needed.

Default path:

```text
outputs/{topic}_{work_type}_YYYYMMDD.md
```

Use `.docx`, `.xlsx`, `.pptx`, or `.pdf` only when the user explicitly requests that format.

After saving, provide a file link and a brief summary of what was saved.

## Guardrails

- Do not present outputs as advice from a licensed Japanese lawyer.
- Do not invent statutes, holdings, dates, court names, or case numbers.
- Do not omit uncertainty when the local dataset is stale, missing, or incomplete.
- Do not broaden the task into unrelated legal systems unless the user asks.
