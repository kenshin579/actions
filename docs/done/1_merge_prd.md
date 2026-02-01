# PR Merge 후 미래 날짜 보정 워크플로우

## 개요

PR이 merge 될 때, 포함된 `index.md`의 frontmatter `date` 필드가 미래 날짜인 경우 현재 날짜(오늘)로 자동 변경하는 GitHub Action을 생성한다.

## 배경

- `auto-merge-pr.yml`은 `date > 오늘`인 PR을 merge 대상에서 제외한다
- 하지만 수동으로 PR을 미리 merge하는 경우, 미래 날짜가 그대로 게시된다
- 이 경우 블로그에 아직 오지 않은 날짜의 포스트가 노출되는 문제가 발생한다

## 현재 콘텐츠 구조

### Frontmatter 형식 (blog-v2, investment 공통)

```yaml
---
title: "포스트 제목"
description: "설명"
date: 2026-01-15
update: 2026-01-15
tags:
  - tag1
---
```

- 날짜 형식: `YYYY-MM-DD` (따옴표 없음)
- `date`와 `update` 필드 모두 존재
- 파일 경로: `contents/{category}/{slug}/index.md`

## 요구사항

### 1. 재사용 워크플로우 (actions 레포)

**파일**: `actions/.github/workflows/fix-future-date.yml`

**트리거**: `workflow_call` (재사용 가능)

**동작 흐름**:

1. merge된 PR에서 변경된 파일 목록 조회
2. `index.md` 파일 필터링
3. 각 `index.md`의 frontmatter `date` 필드 파싱
4. `date > 오늘`이면 → `date`를 오늘 날짜로 변경
5. `update` 필드도 함께 오늘 날짜로 변경
6. 변경 사항이 있으면 별도 브랜치 생성 → PR 자동 생성

### 2. Caller 워크플로우 (blog-v2, investment 레포)

**파일**: 각 레포의 `.github/workflows/fix-future-date.yml`

**트리거**: `pull_request`의 `closed` 이벤트 (merge된 경우만 실행)

**호출 방식**:
```yaml
uses: kenshin579/actions/.github/workflows/fix-future-date.yml@main
```

## 상세 요구사항

### 날짜 비교 로직

| 시나리오 | date 값 | 오늘 날짜 | 동작 |
|---------|---------|-----------|------|
| 과거 날짜 | 2026-01-10 | 2026-01-15 | 변경 없음 |
| 오늘 날짜 | 2026-01-15 | 2026-01-15 | 변경 없음 |
| 미래 날짜 | 2026-01-20 | 2026-01-15 | `date: 2026-01-15`로 변경 |
| date 없음 | - | 2026-01-15 | 변경 없음 (스킵) |

### Frontmatter 수정 범위

- `date` 필드: 미래 날짜 → 오늘 날짜로 변경
- `update` 필드: `date`를 변경하는 경우 함께 오늘 날짜로 변경

### 커밋 & PR 생성

- 브랜치명: `chore/fix-future-date-{pr_number}`
- 커밋 메시지: `[chore] 미래 날짜를 현재 날짜로 보정`
- PR 제목: `[chore] 미래 날짜를 현재 날짜로 보정`
- PR 본문: 원본 PR 번호 및 변경 파일 목록 포함
- main 브랜치에 직접 push하지 않고, 별도 PR을 생성한다

### 예외 처리

- merge가 아닌 close인 경우: 실행하지 않음
- `index.md`가 없는 PR: 아무 동작 없이 종료
- frontmatter 파싱 실패: 해당 파일 스킵, 로그 출력
- 변경 사항 없음: 브랜치/PR 생성하지 않음

## 파일 구조

```
# actions 레포 (재사용 워크플로우)
actions/.github/workflows/fix-future-date.yml

# blog-v2 레포 (caller)
blog-v2.advenoh.pe.kr/.github/workflows/fix-future-date.yml

# investment 레포 (caller)
investment.advenoh.pe.kr/.github/workflows/fix-future-date.yml
```

## 기술 참고

### 기존 패턴 참조

- `auto-merge-pr.yml`: frontmatter date 파싱 로직 재활용 가능
  - 정규식: `/^---[\s\S]*?date:\s*(\d{4}-\d{2}-\d{2})[\s\S]*?---/`
- caller 워크플로우 패턴: `blog-v2/.github/workflows/auto-merge-pr.yml` 참조

### 필요 권한

- `contents: write` (브랜치 생성 및 파일 수정을 위해)
- `pull-requests: write` (PR 생성을 위해)
