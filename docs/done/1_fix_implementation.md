# fix-post-date 구현 문서

## 개요

`fix-future-date.yml` → `fix-post-date.yml`로 이름 변경하고, 과거 날짜도 보정하도록 개선한다.

## 수정 대상 파일

| 변경 유형 | 파일 경로 |
|-----------|-----------|
| 신규 생성 | `actions/.github/workflows/fix-post-date.yml` |
| 신규 생성 | `blog-v2.advenoh.pe.kr/.github/workflows/fix-post-date.yml` |
| 삭제 | `actions/.github/workflows/fix-future-date.yml` |
| 삭제 | `blog-v2.advenoh.pe.kr/.github/workflows/fix-future-date.yml` |

## 구현 상세

### 1. `actions/.github/workflows/fix-post-date.yml` (재사용 워크플로우)

기존 `fix-future-date.yml`을 복사 후 아래 4가지 변경 적용.

#### 1-1. 워크플로우 이름 변경

```yaml
name: Fix Post Date
```

#### 1-2. 날짜 비교 조건 변경 (Step 2: Check and fix dates)

```javascript
// Before
if (dateMatch && dateMatch[1] > today) {
  console.log(`미래 날짜 감지: ${file.filename} (date: ${dateMatch[1]})`);
  filesToFix.push({ path: file.filename, oldDate: dateMatch[1] });
}

// After
if (dateMatch && dateMatch[1] !== today) {
  const label = dateMatch[1] > today ? '미래' : '과거';
  console.log(`${label} 날짜 감지: ${file.filename} (date: ${dateMatch[1]})`);
  filesToFix.push({ path: file.filename, oldDate: dateMatch[1] });
}
```

#### 1-3. 브랜치명 변경 (Step 3: Fix dates and create PR)

```javascript
// Before
const branchName = `chore/fix-future-date-${prNumber}`;

// After
const branchName = `chore/fix-post-date-${prNumber}`;
```

#### 1-4. PR 제목/본문 변경 (Step 3: Fix dates and create PR)

```javascript
// Before
title: '[chore] 미래 날짜를 현재 날짜로 보정'
body: `PR #${prNumber} merge 시 미래 날짜가 감지되어 자동 보정합니다.\n\n...`

// After
title: '[chore] 포스팅 날짜를 현재 날짜로 보정'
body: `PR #${prNumber} merge 시 오늘과 다른 날짜가 감지되어 자동 보정합니다.\n\n...`
```

### 2. `blog-v2.advenoh.pe.kr/.github/workflows/fix-post-date.yml` (트리거 워크플로우)

기존 `fix-future-date.yml`을 복사 후 아래 변경 적용.

```yaml
name: Fix Post Date

on:
  pull_request:
    types: [closed]

permissions:
  contents: write
  pull-requests: write

jobs:
  fix-date:
    if: github.event.pull_request.merged == true
    uses: kenshin579/actions/.github/workflows/fix-post-date.yml@main  # 변경
    with:
      pr_number: ${{ github.event.pull_request.number }}
      content_dir: contents
    secrets: inherit
```

### 3. 기존 파일 삭제

- `actions/.github/workflows/fix-future-date.yml`
- `blog-v2.advenoh.pe.kr/.github/workflows/fix-future-date.yml`
