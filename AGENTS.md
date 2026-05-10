# AGENTS.md - legal-jp

This file is the Codex project contract for `legal-jp`.

Use the `$legal-jp:legal-jp` project skill whenever the task involves Japanese law, precedent, statute metadata, legal research, or fact-specific legal questions. The project plugin manifest is `.codex-plugin/plugin.json`, and the Codex skill body is `.agents/skills/legal-jp/SKILL.md`.

## Required Workflow

For Japanese law, precedent, legal research, or fact-specific legal questions:

1. Ensure `data_set/` exists. Clone `https://github.com/japanese-law-analysis/data_set.git` if missing.
2. Try `git -C data_set pull --ff-only`; if it fails, mention that the existing snapshot is being used.
3. Record dataset provenance before answering:

```bash
git -C data_set rev-parse --short HEAD
git -C data_set log -1 --format=%cs
```

If either command fails, explicitly state that dataset commit/date provenance could not be determined.

4. Search local evidence with:

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py
python3 .claude/skills/legal-jp/scripts/search_precedent.py
```

5. Cite evidence using local paths and metadata returned by the scripts.
6. Separate confirmed source data from legal analysis or practical suggestions.
7. Include the dataset commit/date provenance in every substantive legal answer or saved report.
8. Include the disclaimer that this is AI-assisted legal information, not a substitute for licensed Japanese legal advice.

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
python3 .claude/skills/legal-jp/scripts/search_law.py --abbr "民法" --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --yomikae "会社法" --limit 5
```

Precedent:

```bash
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title "損害賠償" --decade 2020 --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --case-number "令和2" --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --text "損害賠償" --decade 2020 --snippet --limit 5
```

## Output Files

When the user asks for a report or saved output, create `outputs/` and save Markdown by default:

```text
outputs/{topic}_{work_type}_YYYYMMDD.md
```

Use `.docx`, `.xlsx`, `.pptx`, or `.pdf` only when explicitly requested.

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

## Guardrails

- Do not present outputs as advice from a licensed Japanese lawyer.
- Do not invent statutes, holdings, dates, court names, or case numbers.
- Do not omit uncertainty when the local dataset is stale, missing, or incomplete.
- Do not broaden the task into unrelated legal systems unless the user asks.
