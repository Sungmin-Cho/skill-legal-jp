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

Claude Code または Codex でこのリポジトリを開いた状態で、普段どおり自然文で質問します。スキルは内部でローカルデータセットを更新・検索し、確認した根拠と dataset provenance を回答に含めます。

### 個別相談

```text
日本で賃貸借契約が終了したのに、貸主が敷金を返してくれません。
退去時の原状回復費用として高額な請求もされています。
どの法律と裁判例を確認すべきか、実務上の対応順序も教えてください。
```

→ 関係し得る法令・裁判例データを検索し、確認済みの根拠、分析、追加で確認すべき事実、免責を分けて回答します。

### 法令リサーチ

```text
会社法における取締役の競業避止義務について、
関連する法令データと読み替え情報を確認して要点を整理してください。
根拠ファイルとデータセットの commit/date provenance も付けてください。
```

→ 法令名、法令番号、状態、略称、読み替え情報などをローカルデータに基づいて整理します。

### 裁判例リサーチ

```text
2020年代の損害賠償に関する裁判例を探して、
事件番号、裁判所、判決日、要旨が分かる範囲で表にしてください。
```

→ 裁判例タイトル、事件番号、裁判所、日付、JSON パスなどのメタデータを確認し、必要に応じて本文スニペットも使って整理します。

### 保存レポート

```text
民法上の不法行為責任について、確認できる法令データと裁判例を使って
日本語の調査メモを作成し、Markdown ファイルとして保存してください。
```

→ `outputs/{topic}_{work_type}_YYYYMMDD.md` に保存し、保存先リンクを返します。

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
- Codex: `$legal-jp:legal-jp` project skill, `.agents/skills/legal-jp/SKILL.md`, `.codex-plugin/plugin.json`, and `AGENTS.md`

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
