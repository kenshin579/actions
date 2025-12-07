# My Actions

GitHub Actions 및 자동화 스크립트 모음 저장소입니다.

## 개요

이 저장소는 다른 저장소에서 재사용 가능한 GitHub 워크플로우와 자동화 도구를 제공합니다.

## 워크플로우

### Auto Merge PR (`auto-merge-pr.yml`)

`MergeReady` 라벨이 있는 PR을 자동으로 머지합니다.

**특징:**
- 주간 머지 제한 (대기 PR 수에 따라 1~4개)
- 가장 오래된 PR부터 순차 처리
- Squash 머지 방식

**사용법:**
```yaml
jobs:
  auto-merge:
    uses: kenshin579/actions/.github/workflows/auto-merge-pr.yml@main
    secrets: inherit
```

### Label Merge Conflict (`label-merge-conflict.yml`)

PR에 충돌이 발생하면 자동으로 라벨을 추가합니다.

**라벨:**
- 충돌 발생 시: `PR: needs rebase`
- 충돌 해결 시: `PR: ready to ship`

**사용법:**
```yaml
jobs:
  label-conflict:
    uses: kenshin579/actions/.github/workflows/label-merge-conflict.yml@main
    secrets: inherit
```

### Code Review (`code-review.yml`)

Qodo PR Agent를 활용한 자동 코드 리뷰를 수행합니다.

**특징:**
- 자동 PR 설명 생성
- 자동 코드 리뷰
- 자동 개선 제안
- DeepSeek 모델 사용

**사용법:**
```yaml
jobs:
  code-review:
    uses: kenshin579/actions/.github/workflows/code-review.yml@main
    secrets: inherit
    with:
      ignore_glob: "['**/mocks/**', 'swagdocs/**']"
```

## 스크립트

### Weekly Todo Report (`scripts/weekly-todo-report/`)

OpenAI Agents SDK와 GitHub MCP를 활용한 주간 업무 보고서 자동 생성 도구입니다.

**특징:**
- GitHub PR/이슈 데이터 자동 수집
- 토요일~금요일 주간 범위 (KST 기준)
- 마크다운 보고서 생성
- Docker 지원

**필수 환경변수:**
- `OPENAI_BASE_URL`: OpenAI 호환 API 엔드포인트
- `OPENAI_API_KEY`: API 키
- `GITHUB_PERSONAL_ACCESS_TOKEN`: GitHub 토큰

**실행:**
```bash
cd scripts/weekly-todo-report
source .venv/bin/activate
python main.py
```

자세한 내용은 [DOCKER_README.md](scripts/weekly-todo-report/DOCKER_README.md)를 참조하세요.

## 라이선스

MIT License
