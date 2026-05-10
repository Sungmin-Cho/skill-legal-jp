# legal-jp

Claude Code と Codex で使う日本法情報検索スキルです。ローカルの
`japanese-law-analysis/data_set` スナップショットを検索し、法令メタデータ、
法令略称、読み替えデータ、裁判例 JSON を根拠として日本法に関する調査を支援します。

[한국어 문서](README.ko.md)

## 概要

ユーザーが日本法の法令・判例・実務上の確認事項を質問したとき、AI の一般知識だけで答えるのではなく、ローカルデータセットを先に検索して根拠を確認するためのリポジトリです。

**このスキルなしで質問した場合:**

- 一般的な法律知識だけに基づく回答になりやすい
- データセットの更新日時や根拠ファイルが不明になりやすい
- 法令略称や裁判例メタデータを体系的に確認しにくい

**このスキルを使う場合:**

- `data_set/` のローカルスナップショットを先に検索
- 法令名、法令番号、状態、略称、読み替え情報、裁判例メタデータを根拠付きで確認
- データセット commit/date provenance を回答または保存レポートに明記
- 確認済みデータ、分析、限界、免責を分けて提示

## データソース

| 保存先 | 内容 | ライセンス |
|--------|------|------------|
| [japanese-law-analysis/data_set](https://github.com/japanese-law-analysis/data_set) | 日本の法令メタデータ、法令略称、読み替えデータ、裁判例 JSON | CC0-1.0 |

このリポジトリではデータ本体を同梱しません。`data_set/` はローカル作業用に clone するディレクトリで、`.gitignore` の対象です。

## セットアップ

```bash
# 1. スキルリポジトリを取得
git clone https://github.com/Sungmin-Cho/skill-legal-jp.git
cd skill-legal-jp

# 2. 日本法データセットを取得
git clone https://github.com/japanese-law-analysis/data_set.git data_set

# 3. Claude Code または Codex でこのディレクトリを開く
claude
```

ローカルデータを更新する場合:

```bash
git -C data_set pull --ff-only
```

回答前にデータセットの provenance を確認します。

```bash
git -C data_set rev-parse --short HEAD
git -C data_set log -1 --format=%cs
```

## 使用例

### 法令検索

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py --name "民法" --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --exact "民法" --include-repealed --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --abbr "民法" --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --yomikae "会社法" --limit 5
```

主なオプション:

- `--name`: 法令名の部分一致検索
- `--exact`: 正確な法令名で検索
- `--abbr`: 法令略称データを検索
- `--yomikae`: 読み替えデータを検索
- `--include-repealed`: 廃止法令も含める
- `--limit`: 表示件数を制限

### 裁判例検索

```bash
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title "損害賠償" --decade 2020 --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --case-number "令和2" --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --text "損害賠償" --decade 2020 --snippet --limit 5
```

主なオプション:

- `--title`: 裁判例タイトル検索
- `--case-number`: 事件番号検索
- `--text`: 裁判例 JSON 本文検索
- `--court`: 裁判所名フィルタ
- `--decade`: 年代フィルタ
- `--content`: 判示事項・裁判要旨などを含める
- `--snippet`: キーワード周辺だけを表示
- `--limit`: 表示件数を制限

## プロジェクト構成

```text
legal-jp/
├── .claude/skills/legal-jp/
│   ├── SKILL.md                    # Claude Code 用スキル定義
│   └── scripts/
│       ├── search_law.py           # 法令メタデータ・略称・読み替え検索
│       └── search_precedent.py     # 裁判例メタデータ・本文検索
├── tests/                          # スクリプトと文書契約のテスト
├── AGENTS.md                       # Codex 用の作業契約
├── CLAUDE.md                       # Claude Code 用のプロジェクト案内
├── README.md                       # 日本語 README
├── README.ko.md                    # 한국어 README
├── data_set/                       # ローカルデータセット。git 管理対象外
└── outputs/                        # 保存レポート。git 管理対象外
```

## エージェントの入口

- Claude Code: `.claude/skills/legal-jp/SKILL.md` と `CLAUDE.md`
- Codex: `AGENTS.md`

どちらの入口でも、実質的な日本法回答では次を守ります。

1. `data_set/` を用意し、可能なら `git pull --ff-only` で更新する。
2. `rev-parse --short HEAD` と `log -1 --format=%cs` で dataset provenance を記録する。
3. 検索スクリプトでローカル根拠を確認する。
4. 確認済みデータ、分析、実務上の確認事項、限界を分ける。
5. 日本の弁護士による法的助言ではないことを明記する。

## 出力保存

ユーザーがレポートや保存成果物を求めた場合だけ、`outputs/` に保存します。指定がない場合は Markdown を使います。

```text
outputs/{topic}_{work_type}_YYYYMMDD.md
```

`.docx`、`.xlsx`、`.pptx`、`.pdf` はユーザーが明示した場合にだけ使います。

## データの出典とライセンス

- データセット: [japanese-law-analysis/data_set](https://github.com/japanese-law-analysis/data_set)
- データセットライセンス: CC0-1.0
- スキルコード: このリポジトリに別途 `LICENSE` が追加されるまでは、個別ライセンスは未指定です。

## 免責

このプロジェクトが提供する情報は、ローカル `japanese-law-analysis/data_set` スナップショットに基づく AI 支援の法律情報です。日本の弁護士による法的助言を代替するものではありません。具体的な事件、契約、訴訟、行政対応については、資格を有する日本法専門家に確認してください。
