# legal-jp Dual Skill MVP Design

## Summary

Build `legal-jp` as a repo-local Japanese legal information skill project modeled after `/Users/sungmin/Dev/legal-kr`, with one shared local data/search layer and two agent-facing surfaces:

- Claude Code: `.claude/skills/legal-jp/SKILL.md`
- Codex: `AGENTS.md` plus the same scripts and repository conventions

The first milestone is a working MVP for Japanese law and precedent lookup from `japanese-law-analysis/data_set`, not a packaged Codex plugin.

## Goals

- Provide Japanese law and precedent lookup grounded in local source data.
- Support both Claude Code and Codex in the same repository.
- Keep the search layer deterministic and reusable through Python scripts.
- Mirror the operational style of `legal-kr`: update local data, search evidence, separate source-backed facts from legal analysis, and save requested outputs.

## Non-Goals

- Do not build a full Codex plugin package in the first milestone.
- Do not create a web app or UI.
- Do not transform the whole dataset into a new canonical format before the MVP works.
- Do not claim lawyer-grade advice or current-law completeness beyond the local dataset snapshot.

## Source Data

Use `https://github.com/japanese-law-analysis/data_set` as the primary data repository.

Relevant data paths:

- `law/list.json`: active e-Gov law data listing.
- `law/repeal_list.json`: repealed e-Gov law data listing.
- `law/egov_abb.json`: e-Gov abbreviation data.
- `law/law_abb.json`: law abbreviation data.
- `law/ryakusyou.json`: extracted abbreviation and definition clauses.
- `law/yomikae.json`: extracted replacement-reading clauses.
- `precedent/{decade}/list.json`: precedent metadata by decade.
- `precedent/{decade}/*.json`: individual precedent records.

The dataset README states that law and judgment data are not copyrightable under Japanese Copyright Act Article 13 and the generated dataset is released under CC0.

## Repository Layout

```text
legal-jp/
├── .claude/skills/legal-jp/
│   ├── SKILL.md
│   └── scripts/
│       ├── search_law.py
│       └── search_precedent.py
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── data_set/
├── outputs/
└── docs/superpowers/specs/
```

`data_set/` is a local clone of `japanese-law-analysis/data_set`. It should be updated with `git pull --ff-only` when available. If update fails, the skill should continue with the existing local snapshot and report that fallback.

## Claude Surface

Create `.claude/skills/legal-jp/SKILL.md` with:

- A Japanese-law-specific trigger description in Korean, Japanese, and English keywords.
- A role definition for Japanese legal information research.
- A workflow that checks/updates `data_set`, classifies the request, searches law and precedent data, analyzes evidence, and returns an answer.
- A consultation-style interview loop for fact-specific legal questions, similar to `legal-kr`.
- Explicit disclaimer language: AI-provided legal information, not a substitute for licensed Japanese legal advice.

The Claude skill should reference scripts with `${SKILL_DIR}/scripts/...` and data with `${SKILL_DIR}/../../../data_set`.

## Codex Surface

Create `AGENTS.md` with the same project contract:

- Always use the local `legal-jp` search scripts before answering Japanese legal questions.
- Use `data_set/` as the source of truth.
- Cite local evidence paths and source metadata where available.
- Save requested reports to `outputs/`.
- Preserve the same disclaimer and evidence-vs-analysis separation as the Claude skill.

`CLAUDE.md` should orient Claude Code at the project root and point to `.claude/skills/legal-jp/SKILL.md`. `README.md` should describe setup, data sources, example usage, and script commands.

## Search Scripts

### `search_law.py`

Implement law search against `data_set/law/*.json`.

Required modes:

- `--name KEYWORD`: search law names in `law/list.json` and optionally `law/repeal_list.json`.
- `--exact NAME`: exact or normalized law-name lookup.
- `--abbr KEYWORD`: search abbreviation sources such as `egov_abb.json`, `law_abb.json`, and `ryakusyou.json`.
- `--yomikae KEYWORD`: search replacement-reading data in `yomikae.json`.
- `--include-repealed`: include repealed laws.
- `--limit N`: limit result count.

Output JSON should include stable fields where available:

- `name`
- `num`
- `id`
- `date`
- `source_file`
- `status`
- `patch`
- `matches`

The script should use only the Python standard library.

### `search_precedent.py`

Implement precedent search against `data_set/precedent/{decade}/list.json` and individual JSON files.

Required modes:

- `--title KEYWORD`: search metadata/title fields.
- `--case-number KEYWORD`: search case number or filename.
- `--court KEYWORD`: filter by court name or court type.
- `--text KEYWORD`: search individual precedent JSON text.
- `--decade 2020`: limit search to one decade directory.
- `--content`: include selected detail fields or text snippets.
- `--snippet`: include a short keyword context.
- `--limit N`: limit result count.

The script should build metadata from decade `list.json` files when present and join individual JSON paths where possible. Full-text search can use subprocess `grep` or Python scanning, but should avoid loading all large JSON files into memory when a narrower search is possible.

## Workflow

1. Ensure `data_set/` exists. If absent, clone `https://github.com/japanese-law-analysis/data_set.git`.
2. Update `data_set/` with `git pull --ff-only`; on failure, warn and continue with the existing snapshot.
3. Classify request:
   - Direct lookup: named law, article, abbreviation, precedent, or dataset search.
   - Consultation: fact-specific legal situation requiring targeted questions.
4. Search law data with `search_law.py`.
5. Search precedent data with `search_precedent.py` when case law is relevant.
6. Present source-backed findings separately from legal analysis.
7. Include a disclaimer and the dataset snapshot basis.
8. Save reports only when requested, using `outputs/{topic}_{work_type}_YYYYMMDD.md` by default.

## Output Contract

Default answer sections:

```markdown
## 일본 법률 정보

### 1. 쟁점
### 2. 확인한 법령 데이터
### 3. 확인한 판례 데이터
### 4. 분석
### 5. 실무상 확인할 점
### 6. 한계 및 면책
```

For direct lookup requests, a shorter answer is acceptable as long as it includes source data and limitations.

## Validation

Minimum validation before considering the MVP complete:

- `python3 .claude/skills/legal-jp/scripts/search_law.py --name 民法 --limit 3`
- `python3 .claude/skills/legal-jp/scripts/search_law.py --abbr 民法 --limit 3`
- `python3 .claude/skills/legal-jp/scripts/search_precedent.py --title 損害賠償 --limit 3`
- `python3 .claude/skills/legal-jp/scripts/search_precedent.py --text 損害賠償 --decade 2020 --snippet --limit 3`
- Read one returned law result and one returned precedent result to verify paths and fields.
- Run a smoke prompt through the written workflow and confirm the answer cites actual local data.

## Risks

- `data_set` is not shaped like `legalize-kr`; law text may require e-Gov XML retrieval or separate source links for full article extraction. The MVP should be honest when only metadata or extracted analysis JSON is available.
- Precedent JSON schemas may vary by decade or court source. Scripts should be schema-tolerant and surface raw keys when necessary.
- `ryakusyou.json` is large, so abbreviation searches should stream or short-circuit rather than loading unnecessary content when practical.
- Japanese legal advice can depend on current statutes, amendments, and professional interpretation. Answers must state the local dataset snapshot basis.

## Implementation Order

1. Initialize repository support files: `README.md`, `CLAUDE.md`, `AGENTS.md`, `.gitignore`.
2. Create the Claude skill skeleton and scripts directory.
3. Implement `search_law.py`.
4. Implement `search_precedent.py`.
5. Write `SKILL.md` workflow and align `AGENTS.md`.
6. Clone or update `data_set/`.
7. Run script validation and one workflow smoke test.
