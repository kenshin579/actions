# Auto Merge PR 구현 TODO

## 1단계: 기본 구조 수정

- [x] `auto-merge-pr.yml` 파일 백업 (선택)
- [x] `getPostDateFromPR` 헬퍼 함수 추가
  - [x] `pulls.listFiles` API로 PR 파일 목록 조회
  - [x] `.md` 파일 필터링 로직 구현
  - [x] `repos.getContent` API로 파일 내용 조회
  - [x] Base64 디코딩 및 frontmatter date 파싱

## 2단계: merge 대상 선정 로직 수정

- [x] 각 PR에 `postDate` 속성 추가
- [x] 미래 날짜 PR 필터링 로직 구현
  - [x] 오늘 날짜와 비교 (`date <= today`)
  - [x] date 없는 PR은 기존 로직 유지
- [x] 정렬 기준 변경
  - [x] `created_at` → `postDate` 기준
  - [x] date 없으면 `created_at` fallback

## 3단계: 예외 처리

- [x] MD 파일 없는 PR 처리
- [x] date 필드 없는 PR 처리
- [x] API 호출 실패 시 try-catch 처리
- [x] 디버그 로그 추가

## 4단계: 테스트

- [ ] 로컬에서 스크립트 로직 검증
- [ ] 테스트 시나리오 확인
  - [ ] 과거 날짜 PR → merge 대상 ✅
  - [ ] 오늘 날짜 PR → merge 대상 ✅
  - [ ] 미래 날짜 PR → merge 대상 아님 ❌
  - [ ] date 없는 PR → 기존 로직 적용

## 5단계: 배포

- [x] 워크플로우 파일 커밋
- [ ] 실제 PR로 동작 확인
