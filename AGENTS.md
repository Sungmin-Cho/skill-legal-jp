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
