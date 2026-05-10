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
