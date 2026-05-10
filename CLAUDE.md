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
