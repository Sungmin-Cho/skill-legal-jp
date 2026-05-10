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
