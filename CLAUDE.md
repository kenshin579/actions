# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

GitHub Actions 및 자동화 스크립트 모음 저장소. 재사용 가능한 GitHub 워크플로우와 주간 보고서 생성 도구를 포함.

## Architecture

### GitHub Workflows (`.github/workflows/`)

재사용 가능한 워크플로우 (`workflow_call` 트리거):

**PR 자동화**:
- **auto-merge-pr.yml**: `MergeReady` 라벨이 있는 PR 자동 머지 (주간 제한 적용)
- **label-merge-conflict.yml**: PR 충돌 감지 시 자동 라벨링
- **code-review.yml**: Qodo PR Agent를 활용한 자동 코드 리뷰 (DeepSeek 모델 사용)

**릴리스 자동화**:
- **release.yml**: Semantic versioning 기반 태그 생성 및 GitHub Release
- **docker-publish.yml**: Multi-platform Docker 이미지 빌드 및 레지스트리 푸시
- **pypi-publish.yml**: Python 패키지 PyPI 배포 (테스트 실행 옵션 포함)

### Weekly Report Script (`scripts/weekly-todo-report/`)

OpenAI Agents SDK + GitHub MCP를 활용한 주간 보고서 자동 생성 도구.

**핵심 컴포넌트**:
- `main.py`: 에이전트 빌드 및 보고서 생성 진입점
- `.prompts/*.md`: YAML 헤더에 GitHub 정보(owner, repos)를 포함한 프롬프트 템플릿
- `run.sh`: 환경변수 설정 및 실행 스크립트

**주요 특징**:
- 토요일~금요일 주간 범위 자동 계산 (KST 기준)
- GitHub MCP 서버를 Docker로 read-only 모드 실행
- 프롬프트 파일에서 대상 저장소 목록 자동 추출

## Commands

### Weekly Report Script

```bash
# 디렉토리 이동
cd scripts/weekly-todo-report

# 가상환경 설정
python -m venv .venv
source .venv/bin/activate
pip install -e .

# 실행 (환경변수 필요)
export OPENAI_BASE_URL=<your-endpoint>
export OPENAI_API_KEY=<your-key>
export GITHUB_PERSONAL_ACCESS_TOKEN=<your-token>
python main.py

# 또는 run.sh 사용 (환경변수 자동 설정)
./run.sh
```

### 테스트

```bash
cd scripts/weekly-todo-report
pytest test_this_week_range.py -v
```

## Commit Message Convention

커밋 메시지는 한국어로 작성. 형식: `[이슈번호 또는 브랜치]: <설명>`

```
[#3000] 주식 가격 조회 API 구현
[chores] 의존성 업데이트
```

타입: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

브랜치 명명: `feat/#이슈번호-간략한설명`, `fix/#이슈번호-간략한설명`
