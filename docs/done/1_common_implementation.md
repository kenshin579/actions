# 공통 Release Workflow 구현 가이드

## 1. release.yml (Tag 생성)

**파일:** `actions/.github/workflows/release.yml`

```yaml
name: Create Release

on:
  workflow_call:
    inputs:
      version_type:
        description: 'Version bump type (patch, minor, major)'
        type: string
        required: false
        default: 'minor'
      tag_prefix:
        description: 'Tag prefix'
        type: string
        required: false
        default: 'v'
      create_release:
        description: 'Create GitHub Release'
        type: boolean
        required: false
        default: true
    outputs:
      new_version:
        description: '생성된 새 버전'
        value: ${{ jobs.release.outputs.new_version }}
      previous_version:
        description: '이전 버전'
        value: ${{ jobs.release.outputs.previous_version }}
      has_changes:
        description: '변경사항 존재 여부'
        value: ${{ jobs.release.outputs.has_changes }}

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    outputs:
      new_version: ${{ steps.calc_version.outputs.new_version }}
      previous_version: ${{ steps.get_tag.outputs.latest_tag }}
      has_changes: ${{ steps.check_changes.outputs.has_changes }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get latest tag
        id: get_tag
        run: |
          PREFIX="${{ inputs.tag_prefix }}"
          LATEST_TAG=$(git describe --tags --abbrev=0 --match "${PREFIX}*" 2>/dev/null || echo "${PREFIX}0.0.0")
          echo "latest_tag=$LATEST_TAG" >> $GITHUB_OUTPUT

      - name: Check for changes since last tag
        id: check_changes
        run: |
          LAST_TAG="${{ steps.get_tag.outputs.latest_tag }}"
          PREFIX="${{ inputs.tag_prefix }}"
          if [ "$LAST_TAG" = "${PREFIX}0.0.0" ]; then
            echo "has_changes=true" >> $GITHUB_OUTPUT
          else
            COMMIT_COUNT=$(git rev-list --count ${LAST_TAG}..HEAD)
            if [ "$COMMIT_COUNT" -eq 0 ]; then
              echo "has_changes=false" >> $GITHUB_OUTPUT
              echo "::warning::No changes since $LAST_TAG"
            else
              echo "has_changes=true" >> $GITHUB_OUTPUT
            fi
          fi

      - name: Calculate new version
        id: calc_version
        if: steps.check_changes.outputs.has_changes == 'true'
        run: |
          CURRENT="${{ steps.get_tag.outputs.latest_tag }}"
          PREFIX="${{ inputs.tag_prefix }}"
          VERSION_TYPE="${{ inputs.version_type }}"

          VERSION=${CURRENT#$PREFIX}
          IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"

          case $VERSION_TYPE in
            major) NEW_VERSION="${PREFIX}$((MAJOR + 1)).0.0" ;;
            minor) NEW_VERSION="${PREFIX}${MAJOR}.$((MINOR + 1)).0" ;;
            patch) NEW_VERSION="${PREFIX}${MAJOR}.${MINOR}.$((PATCH + 1))" ;;
          esac

          echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT

      - name: Create tag
        if: steps.check_changes.outputs.has_changes == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag ${{ steps.calc_version.outputs.new_version }}
          git push origin ${{ steps.calc_version.outputs.new_version }}

      - name: Create GitHub Release
        if: steps.check_changes.outputs.has_changes == 'true' && inputs.create_release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.calc_version.outputs.new_version }}
          name: ${{ steps.calc_version.outputs.new_version }}
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 2. docker-publish.yml (Docker Push)

**파일:** `actions/.github/workflows/docker-publish.yml`

```yaml
name: Docker Build & Push

on:
  workflow_call:
    inputs:
      image_name:
        description: 'Docker image name'
        type: string
        required: true
      platforms:
        description: 'Build platforms'
        type: string
        required: false
        default: 'linux/amd64,linux/arm64'
      registry:
        description: 'Docker registry'
        type: string
        required: false
        default: 'docker.io'
    secrets:
      DOCKER_USERNAME:
        required: true
      DOCKER_PASSWORD:
        required: true

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ inputs.registry }}/${{ secrets.DOCKER_USERNAME }}/${{ inputs.image_name }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ inputs.registry }}
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: ${{ inputs.platforms }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## 3. pypi-publish.yml (PyPI Publish)

**파일:** `actions/.github/workflows/pypi-publish.yml`

```yaml
name: Publish to PyPI

on:
  workflow_call:
    inputs:
      python_version:
        description: 'Python version'
        type: string
        required: false
        default: '3.12'
      run_tests:
        description: 'Run tests before publish'
        type: boolean
        required: false
        default: true
      test_command:
        description: 'Test command'
        type: string
        required: false
        default: 'pytest'
      create_release:
        description: 'Create GitHub Release with dist files'
        type: boolean
        required: false
        default: true
    secrets:
      PYPI_API_TOKEN:
        required: true

jobs:
  test:
    if: inputs.run_tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python_version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: ${{ inputs.test_command }}

  build-and-publish:
    needs: [test]
    if: always() && (needs.test.result == 'success' || needs.test.result == 'skipped')
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python_version }}

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine setuptools-scm

      - name: Build package
        run: |
          rm -rf dist/ build/ *.egg-info
          python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: python -m twine upload dist/*

      - name: Create GitHub Release
        if: inputs.create_release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 4. 각 Repository에서 호출하는 방식

### stock-data-batch

**release.yml:**
```yaml
name: Create Release
on:
  workflow_dispatch:
    inputs:
      version_type:
        description: 'Version bump type'
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

**docker-publish.yml:**
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
    secrets:
      DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
      DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
```

### korea-investment-stock

**release.yml:** (stock-data-batch와 동일)

**publish-pypi.yml:**
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
      test_command: |
        pytest korea_investment_stock/ -v \
          --ignore=korea_investment_stock/test_korea_investment_stock.py \
          --ignore=korea_investment_stock/test_integration_us_stocks.py \
          -k "not (Redis or redis_storage)"
    secrets:
      PYPI_API_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
```

### echo-http-cache (Tag만)

**release.yml:**
```yaml
name: Create Release
on:
  workflow_dispatch:
    inputs:
      version_type:
        description: 'Version bump type'
        type: choice
        options: [patch, minor, major]
        default: 'minor'

jobs:
  release:
    uses: kenshin579/actions/.github/workflows/release.yml@main
    with:
      version_type: ${{ inputs.version_type }}
      create_release: true
    secrets: inherit
```

## 5. Secrets 설정

각 repository에서 필요한 secrets:

| Repository | 필요한 Secrets |
|------------|---------------|
| stock-data-batch | `DOCKER_USERNAME`, `DOCKER_PASSWORD` |
| korea-investment-stock | `PYPI_API_TOKEN` |
| echo-server | `DOCKER_USERNAME`, `DOCKER_PASSWORD` |
| inspireme.advenoh.pe.kr | `DOCKER_USERNAME`, `DOCKER_PASSWORD` |
| toolbox | `DOCKER_USERNAME`, `DOCKER_PASSWORD` |
| echo-http-cache | 없음 (GITHUB_TOKEN 자동 제공) |

**주의:** 기존에 `DOCKER_REGISTRY_USERNAME/PASSWORD` 사용하던 repo는 `DOCKER_USERNAME/PASSWORD`로 변경 필요.
