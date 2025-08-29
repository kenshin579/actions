# Weekly Todo Report - Docker 실행 가이드

이 문서는 Docker를 사용하여 주간 업무 보고서를 생성하는 방법을 설명합니다.

## 사전 요구사항

- Docker 설치
- GitHub Personal Access Token
- OpenAI API 키

## 환경변수 설정

환경변수를 직접 설정하거나 `.env` 파일을 생성하여 사용하세요:

```bash
# 필수 환경변수
OPENAI_BASE_URL=https://your-openai-compatible-endpoint.com/v1
OPENAI_API_KEY=your_openai_api_key
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token

# 선택 환경변수
GITHUB_TOOLSETS=repos,issues,pull_requests
GITHUB_READ_ONLY=1
REPOS=your-org/repo1,your-org/repo2
OPENAI_MODEL=gpt-4.1-mini
```

## Docker 실행

### 1. 이미지 빌드
```bash
docker build -t weekly-todo-report .
```

### 2. 컨테이너 실행
```bash
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e OPENAI_BASE_URL=$OPENAI_BASE_URL \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN \
  weekly-todo-report
```

### 3. 특정 옵션으로 실행
```bash
# 다른 프롬프트 파일 사용
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e OPENAI_BASE_URL=$OPENAI_BASE_URL \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN \
  weekly-todo-report --prompts-file custom_report.md

# 다른 출력 디렉토리 지정
docker run --rm \
  -v $(pwd)/custom_reports:/app/custom_reports \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e OPENAI_BASE_URL=$OPENAI_BASE_URL \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN \
  weekly-todo-report --output-dir /app/custom_reports
```

## 출력 파일

보고서는 `reports/` 디렉토리에 생성됩니다:

```
reports/
├── weekly_report_2025-01-22_2025-01-28.md
└── weekly_report_2025-01-22_2025-01-28_143052.md  # 중복 시 타임스탬프 추가
```

## 명령어 옵션

Docker 컨테이너에서 사용할 수 있는 옵션들:

```bash
# 기본 실행
docker run weekly-todo-report

# 다른 프롬프트 파일 사용
docker run weekly-todo-report --prompts-file custom_report.md

# 출력 디렉토리 지정
docker run weekly-todo-report --output-dir /app/custom_reports

# 도움말
docker run weekly-todo-report --help
```

## 문제 해결

### 1. Docker 권한 오류
```bash
sudo chmod 666 /var/run/docker.sock
```

### 2. MCP 연결 오류
- GitHub 토큰이 유효한지 확인하세요
- 네트워크 연결 상태를 확인하세요

### 3. OpenAI API 오류
- API 키와 엔드포인트 URL을 확인하세요
- API 할당량을 확인하세요

## 보안 고려사항

- 환경변수에 민감한 정보(API 키, 토큰)를 포함하지 마세요
- `.env` 파일을 Git에 커밋하지 마세요
- 프로덕션 환경에서는 시크릿 관리 도구를 사용하세요
