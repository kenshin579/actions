# PR Merge 후 미래 날짜 보정 - TODO

## 1단계: 재사용 워크플로우 생성 (actions 레포)

- [x] `actions/.github/workflows/fix-future-date.yml` 생성
  - [x] `workflow_call` 트리거 + `pr_number` input 정의
  - [x] `actions/checkout@v4`로 레포 체크아웃
  - [x] `actions/github-script@v7`로 PR 변경 파일 조회
  - [x] `index.md` 필터링 및 frontmatter date 파싱
  - [x] 미래 날짜 판별 로직 구현
  - [x] `date`, `update` 필드를 오늘 날짜로 치환
  - [x] 변경 사항 있을 때만 별도 브랜치 생성 → 커밋 & 푸시
  - [x] GitHub API로 main 대상 PR 자동 생성

## 2단계: Caller 워크플로우 생성

- [x] `blog-v2.advenoh.pe.kr/.github/workflows/fix-future-date.yml` 생성
  - [x] `pull_request: closed` 트리거
  - [x] `if: merged == true` 조건
  - [x] actions 레포의 재사용 워크플로우 호출
- [x] `investment.advenoh.pe.kr/.github/workflows/fix-future-date.yml` 생성
  - [x] blog-v2와 동일한 구조

## 3단계: 테스트

- [ ] actions 레포에 워크플로우 push
- [ ] blog-v2에서 미래 날짜 index.md PR 생성 후 수동 merge → date 보정 확인
- [ ] investment에서 동일 테스트
