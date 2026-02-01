# 공통 Unit Test Workflow 구현 체크리스트

## Phase 1: Python Unit Test Workflow

### 1.1 Workflow 파일 생성
- [x] `actions/.github/workflows/unit-test-python.yml` 파일 생성
- [x] `workflow_call` 트리거 설정
- [x] inputs 파라미터 정의
  - [x] `python_version` (default: '3.12')
  - [x] `package_manager` (default: 'pip')
  - [x] `test_path` (default: '.')
  - [x] `run_unit_tests` (default: true)
  - [x] `run_integration_tests` (default: false)
  - [x] `unit_test_args` (default: '-m "not integration"')
  - [x] `integration_test_args` (default: '-m integration')
  - [x] `coverage_enabled` (default: true)
  - [x] `coverage_package` (default: '')
  - [x] `install_extras` (default: 'dev')
  - [x] `post_comment` (default: true)

### 1.2 Unit Tests Job 구현
- [x] Python 환경 설정 (`actions/setup-python@v5`)
- [x] pip/poetry 캐시 설정
- [x] 의존성 설치 (pip vs poetry 분기)
- [x] pytest 실행 및 결과 저장
- [x] Coverage 수집 (선택적)
- [x] 아티팩트 업로드 (junit-unit.xml, coverage.xml, test-output.txt)

### 1.3 Integration Tests Job 구현
- [x] 조건부 실행 (`if: inputs.run_integration_tests`)
- [x] Docker 환경 (testcontainers 지원)
- [x] pytest 실행 및 결과 저장
- [x] 아티팩트 업로드

### 1.4 Report Job 구현
- [x] 아티팩트 다운로드
- [x] 테스트 결과 파싱 (passed/failed/skipped/time)
- [x] Coverage 파싱
- [x] PR 코멘트 생성 (`actions/github-script@v7`)

### 1.5 테스트
- [x] korea-investment-stock에서 workflow 호출 테스트
- [x] stock-data-batch에서 Poetry 모드 테스트
- [ ] PR 코멘트 출력 확인

---

## Phase 2: Go Unit Test Workflow

### 2.1 Workflow 파일 생성
- [x] `actions/.github/workflows/unit-test-go.yml` 파일 생성
- [x] `workflow_call` 트리거 설정
- [x] inputs 파라미터 정의
  - [x] `go_version` (default: '1.24')
  - [x] `test_path` (default: './...')
  - [x] `run_unit_tests` (default: true)
  - [x] `run_integration_tests` (default: false)
  - [x] `unit_test_args` (default: '-v -short')
  - [x] `integration_test_args` (default: '-v -run Integration')
  - [x] `coverage_enabled` (default: true)
  - [x] `docker_compose_file` (default: 'docker-compose.yml')
  - [x] `post_comment` (default: true)

### 2.2 Unit Tests Job 구현
- [x] Go 환경 설정 (`actions/setup-go@v5`)
- [x] Go 모듈 캐시 설정
- [x] `go test` 실행 및 결과 저장
- [x] Coverage 수집 (`-coverprofile`)
- [x] 아티팩트 업로드

### 2.3 Integration Tests Job 구현
- [x] 조건부 실행 (`if: inputs.run_integration_tests`)
- [x] docker-compose up/down
- [x] `go test` 실행 및 결과 저장
- [x] 아티팩트 업로드

### 2.4 Report Job 구현
- [x] 아티팩트 다운로드
- [x] 테스트 결과 파싱 (ok/FAIL, time)
- [x] Coverage 파싱
- [x] PR 코멘트 생성

### 2.5 테스트
- [x] echo-server에서 workflow 호출 테스트
- [x] echo-http-cache에서 integration 테스트
- [ ] PR 코멘트 출력 확인

---

## Phase 3: 각 Repository 적용

### 3.1 korea-investment-stock
- [x] `.github/workflows/tests.yml` 생성 (또는 기존 파일 수정)
- [x] `unit-test-python.yml` 호출 설정
- [ ] PR 생성하여 테스트

### 3.2 stock-data-batch
- [x] `.github/workflows/tests.yml` 생성
- [x] `unit-test-python.yml` 호출 (poetry 모드)
- [ ] PR 생성하여 테스트

### 3.3 echo-server
- [x] `.github/workflows/tests.yml` 생성
- [x] `unit-test-go.yml` 호출
- [ ] PR 생성하여 테스트

### 3.4 echo-http-cache
- [x] `.github/workflows/tests.yml` 생성
- [x] `unit-test-go.yml` 호출 (integration + benchmarks)
- [ ] PR 생성하여 테스트

---

## 완료 기준

- [ ] Python workflow가 korea-investment-stock에서 정상 동작
- [ ] Go workflow가 echo-server에서 정상 동작
- [ ] PR 코멘트에 테스트 결과 테이블 정상 출력
- [ ] Coverage 정보 정상 표시
- [ ] 실패 시 적절한 상태 표시
