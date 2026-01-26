# Auto Merge PR 개선 요구사항

## 개요

`auto-merge-pr.yml` 워크플로우를 개선하여, MD 파일의 YAML frontmatter에 있는 `date:` 필드를 기준으로 PR merge 여부를 결정한다.

## 현재 동작 방식

- `MergeReady` 라벨이 있는 PR 목록 조회
- `created_at` (PR 생성일) 기준으로 정렬
- 가장 오래된 PR부터 merge
- 주간 merge 제한 적용 (PR 개수에 따라 1~4개)

## 변경 요구사항

### 핵심 변경 사항

MD 파일의 frontmatter `date:` 필드가 **오늘 날짜와 같거나 지난 경우**에만 해당 PR을 merge 대상으로 선택한다.

### Frontmatter 예시

```yaml
---
title: "블로그 포스트 제목"
description: "설명"
date: 2026-01-15
update: 2026-01-15
tags:
  - tag1
---
```

### 상세 요구사항

1. **PR에서 MD 파일 조회**
   - PR에 포함된 변경 파일 목록에서 `.md` 파일 찾기
   - 주로 `contents/` 디렉토리 내 `index.md` 파일

2. **Frontmatter date 필드 파싱**
   - MD 파일 상단의 YAML frontmatter에서 `date:` 필드 추출
   - 날짜 형식: `YYYY-MM-DD` (예: `2026-01-15`)

3. **날짜 비교 로직**
   - `date <= 오늘` 인 경우: merge 대상 ✅
   - `date > 오늘` 인 경우: merge 대상 아님 ❌

4. **정렬 기준 변경**
   - 기존: `created_at` (PR 생성일)
   - 변경: frontmatter `date` 필드 (오래된 날짜 우선)

5. **예외 처리**
   - MD 파일이 없는 PR: 기존 로직 유지 (created_at 기준)
   - frontmatter에 date 필드가 없는 경우: 기존 로직 유지
   - date 파싱 실패 시: 해당 PR 스킵 또는 기존 로직 적용

## 테스트 시나리오

| 시나리오 | date 값 | 오늘 날짜 | 예상 결과 |
|---------|---------|-----------|----------|
| 과거 날짜 | 2026-01-10 | 2026-01-15 | Merge ✅ |
| 오늘 날짜 | 2026-01-15 | 2026-01-15 | Merge ✅ |
| 미래 날짜 | 2026-01-20 | 2026-01-15 | 대기 ❌ |
| date 없음 | - | 2026-01-15 | 기존 로직 적용 |

## 영향 범위

- 파일: `actions/.github/workflows/auto-merge-pr.yml`
- 관련 레포: 이 워크플로우를 호출하는 모든 레포지토리

## 참고

- 기존 주간 merge 제한 로직은 유지
- `MergeReady` 라벨 기반 필터링은 유지
