# fix-post-date TODO

## Step 1: 새 워크플로우 파일 생성

- [x] `actions/.github/workflows/fix-post-date.yml` 생성
  - [x] 워크플로우 name → `Fix Post Date`
  - [x] 날짜 비교 조건 변경: `dateMatch[1] > today` → `dateMatch[1] !== today`
  - [x] 로그 메시지에 과거/미래 구분 추가
  - [x] 브랜치명 변경: `chore/fix-future-date-` → `chore/fix-post-date-`
  - [x] PR 제목 변경: `포스팅 날짜를 현재 날짜로 보정`
  - [x] PR 본문 변경: `오늘과 다른 날짜가 감지되어 자동 보정`
- [x] `blog-v2.advenoh.pe.kr/.github/workflows/fix-post-date.yml` 생성
  - [x] 워크플로우 name → `Fix Post Date`
  - [x] 재사용 워크플로우 참조 경로 → `fix-post-date.yml@main`

## Step 2: 기존 워크플로우 파일 삭제

- [x] `actions/.github/workflows/fix-future-date.yml` 삭제
- [x] `blog-v2.advenoh.pe.kr/.github/workflows/fix-future-date.yml` 삭제

## Step 3: 검증 (PR merge 후)

- [x] actions PR merge: https://github.com/kenshin579/actions/pull/35
- [x] blog-v2 PR merge: https://github.com/kenshin579/blog-v2.advenoh.pe.kr/pull/422
- [ ] GitHub Actions 탭에서 워크플로우 이름 `Fix Post Date` 표시 확인
- [ ] 과거 날짜 포스팅 merge → 보정 PR 생성 확인
- [ ] 오늘 날짜 포스팅 merge → 스킵 확인
