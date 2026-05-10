---
name: legal-jp
description: "Use when the user asks about Japanese law, Japanese precedent, legal research, statute metadata, abbreviations, e-Gov law data, 裁判例, 判例, 法令, 法律相談, 日本法, 일본 법률, 일본 판례, 일본 법령, 법률 상담, 법령 검색, 판례 검색, 계약, 소송, 손해배상, 노동, 상속, 형사, 민사, 행정, 조문, 판결, legal, law, or precedent."
---

# Legal JP

Use this Codex project skill for Japanese legal information. It mirrors the Claude Code skill in `.claude/skills/legal-jp/SKILL.md`, but is exposed through the Codex project plugin surface.

## Core Rules

1. Use local source data before answering Japanese legal questions.
2. Separate source-backed facts from legal analysis or practical suggestions.
3. State the local dataset commit/date provenance.
4. Do not present the answer as legal advice from a licensed Japanese lawyer.
5. Ask concise clarifying questions when key facts are missing.

## Paths

Assume this skill lives at `.agents/skills/legal-jp`.

```bash
DATA_DIR="${SKILL_DIR}/../../../data_set"
SCRIPT_DIR="${SKILL_DIR}/../../../.claude/skills/legal-jp/scripts"
```

`data_set/` and `outputs/` are local-only directories ignored by git.

## Workflow

### 1. Ensure Local Data

```bash
if [ -d "${DATA_DIR}/.git" ]; then
  git -C "${DATA_DIR}" pull --ff-only 2>/dev/null && echo "data_set updated" || echo "data_set update failed; using existing snapshot"
else
  git clone https://github.com/japanese-law-analysis/data_set.git "${DATA_DIR}"
fi
```

If clone or update fails, clearly state that local data is unavailable or stale.

### 2. Record Dataset Provenance

Before every substantive legal answer or saved report, run:

```bash
git -C "${DATA_DIR}" rev-parse --short HEAD
git -C "${DATA_DIR}" log -1 --format=%cs
```

Report the dataset commit and last commit date. If either command fails, explicitly state that dataset commit/date provenance could not be determined.

### 3. Search Law Data

Use the shared scripts:

```bash
python3 "${SCRIPT_DIR}/search_law.py" --name "民法" --limit 5
python3 "${SCRIPT_DIR}/search_law.py" --exact "民法" --include-repealed --limit 5
python3 "${SCRIPT_DIR}/search_law.py" --abbr "敷金" --limit 5
python3 "${SCRIPT_DIR}/search_law.py" --yomikae "会社法" --limit 5
```

Search active laws first. Use `--include-repealed` only when history, old law, or repeal status matters.

### 4. Search Precedent Data

```bash
python3 "${SCRIPT_DIR}/search_precedent.py" --title "損害賠償" --decade 2020 --limit 5
python3 "${SCRIPT_DIR}/search_precedent.py" --case-number "令和2" --limit 5
python3 "${SCRIPT_DIR}/search_precedent.py" --text "敷金" --snippet --limit 5
```

Prefer metadata/title search first. Use `--text` with `--decade` when possible to limit scanning.

### 5. Analyze and Answer

For substantive analysis, structure the answer as:

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

Always include:

- `data_set` commit: `<short sha>` or `unknown`
- `data_set` date: `<YYYY-MM-DD>` or `unknown`
- Disclaimer: this is AI-assisted legal information based on a local Japanese dataset snapshot, not a substitute for licensed Japanese legal advice.

## Saving Outputs

Save a file only when the user asks for a report or saved output. Default path:

```text
outputs/{topic}_{work_type}_YYYYMMDD.md
```
