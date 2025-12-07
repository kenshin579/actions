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

### Release (`release.yml`)

수동으로 Tag 생성 및 GitHub Release를 생성합니다.

**특징:**
- Semantic Versioning (major/minor/patch)
- 변경사항 없으면 자동 스킵
- GitHub Release 자동 생성 (release notes 포함)

**입력:**
- `version_type`: 버전 증가 타입 (`patch`, `minor`, `major`)
- `tag_prefix`: 태그 접두사 (기본값: `v`)
- `create_release`: GitHub Release 생성 여부 (기본값: `true`)

**출력:**
- `new_version`: 생성된 새 버전
- `previous_version`: 이전 버전
- `has_changes`: 변경사항 존재 여부

**사용법:**
```yaml
name: Create Release
on:
  workflow_dispatch:
    inputs:
      version_type:
        type: choice
        options: [patch, minor, major]
        default: 'minor'

jobs:
  release:
    uses: kenshin579/actions/.github/workflows/release.yml@main
    with:
      version_type: ${{ inputs.version_type }}
    secrets: inherit
```

### Docker Publish (`docker-publish.yml`)

Tag push 시 Docker 이미지를 빌드하고 레지스트리에 push합니다.

**특징:**
- Multi-platform 빌드 지원 (amd64, arm64)
- Semantic versioning 태그 자동 생성
- GHA 캐시 활용

**입력:**
- `image_name`: Docker 이미지 이름 (필수)
- `platforms`: 빌드 플랫폼 (기본값: `linux/amd64,linux/arm64`)
- `registry`: Docker 레지스트리 (기본값: `docker.io`)

**필요한 Secrets:**
- `DOCKER_USERNAME`: Docker 레지스트리 사용자명
- `DOCKER_PASSWORD`: Docker 레지스트리 비밀번호

**사용법:**
```yaml
name: Docker Build & Push
on:
  push:
    tags: ['v*']

jobs:
  docker:
    uses: kenshin579/actions/.github/workflows/docker-publish.yml@main
    with:
      image_name: my-app
      platforms: linux/arm64
    secrets:
      DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
      DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
```

### PyPI Publish (`pypi-publish.yml`)

Tag push 시 Python 패키지를 PyPI에 publish합니다.

**특징:**
- 테스트 실행 후 publish (선택)
- setuptools-scm 버전 관리
- GitHub Release에 dist 파일 첨부

**입력:**
- `python_version`: Python 버전 (기본값: `3.12`)
- `run_tests`: 테스트 실행 여부 (기본값: `true`)
- `test_command`: 테스트 명령어 (기본값: `pytest`)
- `create_release`: GitHub Release 생성 여부 (기본값: `true`)

**필요한 Secrets:**
- `PYPI_API_TOKEN`: PyPI API 토큰

**사용법:**
```yaml
name: Publish to PyPI
on:
  push:
    tags: ['v*.*.*']

jobs:
  publish:
    uses: kenshin579/actions/.github/workflows/pypi-publish.yml@main
    with:
      python_version: '3.12'
      run_tests: true
      test_command: 'pytest -v'
    secrets:
      PYPI_API_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
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
