# 공통 Release Workflow PRD

## 개요

여러 repository에서 수동으로 tag 생성 및 release를 진행하고 있어, `actions` repo에 재사용 가능한 공통 workflow를 만들어 중복 코드를 줄이고 일관성을 유지한다.

## 현재 상황 분석

### Repository별 Release 파이프라인 현황

| Repository | Tag 생성 | 후속 작업 | 트리거 | 플랫폼 |
|------------|---------|----------|--------|--------|
| stock-data-batch | `release.yml` (수동) | Docker push | `on: push tags: v*` | arm64 |
| korea-investment-stock | 수동 | PyPI publish + GitHub Release | `on: push tags: v*.*.*` | - |
| echo-server | 수동 | Docker push | `on: push tags: v*` | amd64, arm64 |
| inspireme.advenoh.pe.kr | 수동 | Docker push | `on: push tags: v*` | amd64, arm64 |
| toolbox | 수동 | Docker push | `on: push tags: v*.*.*` | amd64, arm64 |
| echo-http-cache | 수동 | 없음 (Go 라이브러리) | - | - |

### 후속 작업 유형

#### Type A: Docker Push
- **대상**: stock-data-batch, echo-server, inspireme, toolbox
- **공통점**: tag push 시 Docker 이미지 빌드 및 push
- **차이점**:
  - 플랫폼: arm64 only vs amd64+arm64
  - Registry: docker.io (공통)
  - Secrets 이름: `DOCKER_USERNAME/PASSWORD` vs `DOCKER_REGISTRY_USERNAME/PASSWORD`
  - Cache: registry 기반 vs GHA 기반

#### Type B: PyPI Publish
- **대상**: korea-investment-stock
- **특징**:
  - 테스트 실행 후 publish
  - setuptools-scm으로 버전 관리
  - GitHub Release에 dist 파일 첨부

#### Type C: 없음 (라이브러리)
- **대상**: echo-http-cache
- **특징**: Go 모듈로 tag만 생성하면 됨

### 현재 Workflow 상세 분석

#### stock-data-batch/release.yml (Tag 생성)
```yaml
on: workflow_dispatch
inputs: version_type (patch/minor/major)

Steps:
1. 마지막 태그 조회
2. 변경사항 확인 (없으면 스킵)
3. 새 버전 계산
4. 태그 생성 및 푸시
5. GitHub Release 생성 (auto release notes)
```

#### stock-data-batch/docker-publish.yml (Docker Push)
```yaml
on: push tags: v*

Steps:
1. docker/metadata-action (태그 추출)
2. docker/login-action
3. docker/build-push-action (arm64, registry cache)
```

#### korea-investment-stock/publish-pypi.yml
```yaml
on: push tags: v*.*.*

Jobs:
1. test: pytest 실행
2. build-and-publish:
   - python -m build
   - twine upload
   - GitHub Release 생성 (dist 파일 첨부)
```

## 요구사항

### 1. 공통 Release Workflow (Tag 생성)

**파일:** `actions/.github/workflows/release.yml`

**목적:** 수동으로 tag 생성 및 GitHub Release 생성

```yaml
on:
  workflow_call:
    inputs:
      version_type:
        description: 'Version bump type'
        type: string
        default: 'minor'
      tag_prefix:
        description: 'Tag prefix (v, 빈문자열)'
        type: string
        default: 'v'
      create_release:
        description: 'GitHub Release 생성 여부'
        type: boolean
        default: true
    outputs:
      new_version:
        description: '생성된 새 버전 (예: v1.2.0)'
      previous_version:
        description: '이전 버전'
      has_changes:
        description: '변경사항 존재 여부'
```

### 2. 공통 Docker Publish Workflow

**파일:** `actions/.github/workflows/docker-publish.yml`

**목적:** Tag push 시 Docker 이미지 빌드 및 push

```yaml
on:
  workflow_call:
    inputs:
      image_name:
        description: 'Docker 이미지 이름'
        type: string
        required: true
      platforms:
        description: '빌드 플랫폼'
        type: string
        default: 'linux/amd64,linux/arm64'
      registry:
        description: 'Docker registry'
        type: string
        default: 'docker.io'
    secrets:
      DOCKER_USERNAME:
        required: true
      DOCKER_PASSWORD:
        required: true
```

### 3. 공통 PyPI Publish Workflow

**파일:** `actions/.github/workflows/pypi-publish.yml`

**목적:** Tag push 시 PyPI에 패키지 publish

```yaml
on:
  workflow_call:
    inputs:
      python_version:
        description: 'Python 버전'
        type: string
        default: '3.12'
      run_tests:
        description: '테스트 실행 여부'
        type: boolean
        default: true
      test_command:
        description: '테스트 명령어'
        type: string
        default: 'pytest'
    secrets:
      PYPI_API_TOKEN:
        required: true
```

## 사용 예시

### 예시 1: stock-data-batch (Tag + Docker)

**release.yml** (Tag 생성)
```yaml
name: Create Release
on:
  workflow_dispatch:
    inputs:
      version_type:
        type: choice
        options: [patch, minor, major]

jobs:
  release:
    uses: kenshin579/actions/.github/workflows/release.yml@main
    with:
      version_type: ${{ inputs.version_type }}
    secrets: inherit
```

**docker-publish.yml** (Docker Push - 기존 유지 또는 공통화)
```yaml
name: Docker Build & Push
on:
  push:
    tags: ['v*']

jobs:
  docker:
    uses: kenshin579/actions/.github/workflows/docker-publish.yml@main
    with:
      image_name: stock-data-batch
      platforms: linux/arm64
    secrets: inherit
```

### 예시 2: korea-investment-stock (Tag + PyPI)

**release.yml**
```yaml
name: Create Release
on:
  workflow_dispatch:
    inputs:
      version_type:
        type: choice
        options: [patch, minor, major]

jobs:
  release:
    uses: kenshin579/actions/.github/workflows/release.yml@main
    with:
      version_type: ${{ inputs.version_type }}
    secrets: inherit
```

**publish-pypi.yml**
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
      test_command: 'pytest korea_investment_stock/ -v --ignore=...'
    secrets: inherit
```

### 예시 3: echo-http-cache (Tag만)

```yaml
name: Create Release
on:
  workflow_dispatch:
    inputs:
      version_type:
        type: choice
        options: [patch, minor, major]

jobs:
  release:
    uses: kenshin579/actions/.github/workflows/release.yml@main
    with:
      version_type: ${{ inputs.version_type }}
      create_release: true  # Go 모듈은 GitHub Release만 생성
    secrets: inherit
```

## 관련 문서

- **구현 가이드:** `1_common_implementation.md`
- **체크리스트:** `1_common_todo.md`

## Secrets 통일

현재 각 repo에서 다른 이름의 secrets 사용:

| 현재 | 통일안 |
|------|--------|
| `DOCKER_USERNAME` | `DOCKER_USERNAME` |
| `DOCKER_PASSWORD` | `DOCKER_PASSWORD` |
| `DOCKER_REGISTRY_USERNAME` | → `DOCKER_USERNAME` |
| `DOCKER_REGISTRY_PASSWORD` | → `DOCKER_PASSWORD` |
| `DOCKER_REGISTRY_URL` | 삭제 (기본값 docker.io) |

## 참고

### workflow_call 제약사항

- secrets는 명시적 전달 또는 `secrets: inherit` 사용
- 중첩 호출 깊이 제한: 4단계
- reusable workflow는 같은 org 내 public repo 또는 같은 repo에서만 호출 가능

### Docker 플랫폼별 고려사항

| 플랫폼 | 용도 |
|--------|------|
| `linux/amd64` | 일반 서버, CI/CD |
| `linux/arm64` | Apple Silicon Mac, AWS Graviton |
| 둘 다 | 범용 배포 |
