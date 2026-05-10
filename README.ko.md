# legal-jp

Claude Code와 Codex에서 사용하는 일본 법률 정보 검색 스킬입니다. 로컬
`japanese-law-analysis/data_set` 스냅샷을 검색해 일본 법령 메타데이터, 법령 약칭,
읽기 대체 데이터, 판례 JSON을 근거로 일본 법률 리서치를 지원합니다.

[日本語 README](README.md)

## 개요

일본 법령, 판례, 법률 리서치, 사실관계 기반 법률 검토 요청이 들어왔을 때 AI의 일반 지식만으로 답하지 않고, 로컬 데이터셋을 먼저 검색해 근거를 확인하도록 만든 저장소입니다.

**스킬 없이 질문할 때:**

- 일반적인 법률 지식 기반 답변이 되기 쉽습니다.
- 사용한 데이터의 commit/date provenance가 빠지기 쉽습니다.
- 법령 약칭, 읽기 대체 데이터, 판례 메타데이터를 체계적으로 확인하기 어렵습니다.

**스킬 적용 시:**

- `data_set/` 로컬 스냅샷을 먼저 검색합니다.
- 법령명, 법령번호, 상태, 약칭, 읽기 대체 정보, 판례 메타데이터를 근거와 함께 확인합니다.
- 데이터셋 commit/date provenance를 답변이나 저장 리포트에 명시합니다.
- 확인된 데이터, 분석, 한계, 면책을 분리해 제시합니다.

## 데이터 소스

| 저장소 | 내용 | 라이선스 |
|--------|------|----------|
| [japanese-law-analysis/data_set](https://github.com/japanese-law-analysis/data_set) | 일본 법령 메타데이터, 법령 약칭, 읽기 대체 데이터, 판례 JSON | CC0-1.0 |

이 저장소는 데이터 본문을 포함하지 않습니다. `data_set/`은 로컬 작업용으로 clone하는 디렉터리이며 `.gitignore` 대상입니다.

## 설치

```bash
# 1. 스킬 저장소 클론
git clone https://github.com/Sungmin-Cho/skill-legal-jp.git
cd skill-legal-jp

# 2. 일본 법률 데이터셋 클론
git clone https://github.com/japanese-law-analysis/data_set.git data_set

# 3. Claude Code 또는 Codex에서 이 디렉터리 열기
claude
```

로컬 데이터를 갱신할 때:

```bash
git -C data_set pull --ff-only
```

답변 전에 데이터셋 provenance를 확인합니다.

```bash
git -C data_set rev-parse --short HEAD
git -C data_set log -1 --format=%cs
```

## 사용 예시

### 법령 검색

```bash
python3 .claude/skills/legal-jp/scripts/search_law.py --name "民法" --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --exact "民法" --include-repealed --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --abbr "民法" --limit 5
python3 .claude/skills/legal-jp/scripts/search_law.py --yomikae "会社法" --limit 5
```

주요 옵션:

- `--name`: 법령명 부분 일치 검색
- `--exact`: 정확한 법령명 검색
- `--abbr`: 법령 약칭 데이터 검색
- `--yomikae`: 읽기 대체 데이터 검색
- `--include-repealed`: 폐지 법령 포함
- `--limit`: 표시 건수 제한

### 판례 검색

```bash
python3 .claude/skills/legal-jp/scripts/search_precedent.py --title "損害賠償" --decade 2020 --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --case-number "令和2" --limit 5
python3 .claude/skills/legal-jp/scripts/search_precedent.py --text "損害賠償" --decade 2020 --snippet --limit 5
```

주요 옵션:

- `--title`: 판례 제목 검색
- `--case-number`: 사건번호 검색
- `--text`: 판례 JSON 본문 검색
- `--court`: 법원명 필터
- `--decade`: 연대 필터
- `--content`: 판시사항, 판결요지 등 포함
- `--snippet`: 키워드 주변 텍스트만 표시
- `--limit`: 표시 건수 제한

## 프로젝트 구조

```text
legal-jp/
├── .claude/skills/legal-jp/
│   ├── SKILL.md                    # Claude Code용 스킬 정의
│   └── scripts/
│       ├── search_law.py           # 법령 메타데이터, 약칭, 읽기 대체 검색
│       └── search_precedent.py     # 판례 메타데이터, 본문 검색
├── tests/                          # 스크립트와 문서 계약 테스트
├── AGENTS.md                       # Codex용 작업 계약
├── CLAUDE.md                       # Claude Code용 프로젝트 안내
├── README.md                       # 일본어 README
├── README.ko.md                    # 한국어 README
├── data_set/                       # 로컬 데이터셋. git 관리 대상 아님
└── outputs/                        # 저장 리포트. git 관리 대상 아님
```

## 에이전트 진입점

- Claude Code: `.claude/skills/legal-jp/SKILL.md`와 `CLAUDE.md`
- Codex: `AGENTS.md`

두 진입점 모두 실질적인 일본 법률 답변에서는 다음을 지킵니다.

1. `data_set/`을 준비하고 가능하면 `git pull --ff-only`로 갱신합니다.
2. `rev-parse --short HEAD`와 `log -1 --format=%cs`로 dataset provenance를 기록합니다.
3. 검색 스크립트로 로컬 근거를 확인합니다.
4. 확인된 데이터, 분석, 실무상 확인할 점, 한계를 분리합니다.
5. 일본 변호사의 법률 자문이 아니라는 점을 명시합니다.

## 출력 저장

사용자가 리포트나 저장 결과물을 요청한 경우에만 `outputs/`에 저장합니다. 별도 지정이 없으면 Markdown을 사용합니다.

```text
outputs/{topic}_{work_type}_YYYYMMDD.md
```

`.docx`, `.xlsx`, `.pptx`, `.pdf`는 사용자가 명시한 경우에만 사용합니다.

## 데이터 출처 및 라이선스

- 데이터셋: [japanese-law-analysis/data_set](https://github.com/japanese-law-analysis/data_set)
- 데이터셋 라이선스: CC0-1.0
- 스킬 코드: 이 저장소에 별도 `LICENSE`가 추가되기 전까지는 개별 라이선스가 지정되지 않았습니다.

## 면책 조항

이 프로젝트가 제공하는 정보는 로컬 `japanese-law-analysis/data_set` 스냅샷에 기반한 AI 지원 법률 정보입니다. 일본 변호사의 법률 자문을 대체하지 않습니다. 구체적인 사건, 계약, 소송, 행정 대응은 자격을 갖춘 일본법 전문가에게 확인해야 합니다.
