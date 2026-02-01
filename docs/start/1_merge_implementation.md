# PR Merge 후 미래 날짜 보정 - 구현 문서

## 수정/생성 대상 파일

| 파일 | 레포 | 작업 |
|-----|------|------|
| `.github/workflows/fix-future-date.yml` | actions | 신규 (재사용 워크플로우) |
| `.github/workflows/fix-future-date.yml` | blog-v2 | 신규 (caller) |
| `.github/workflows/fix-future-date.yml` | investment | 신규 (caller) |

## 핵심 구현 사항

### 1. 재사용 워크플로우 (`actions/.github/workflows/fix-future-date.yml`)

`workflow_call` 트리거로 호출되며, caller에서 PR 번호를 입력으로 받는다.

```yaml
name: Fix Future Date

on:
  workflow_call:
    inputs:
      pr_number:
        required: true
        type: number
```

### 2. PR에서 변경된 index.md 파일 조회

`actions/github-script@v7`을 사용하여 merge된 PR의 변경 파일 중 `index.md`를 찾는다.

```javascript
// merge된 PR에서 변경된 파일 목록 조회
const { data: files } = await github.rest.pulls.listFiles({
  owner, repo,
  pull_number: prNumber
});

// index.md 파일만 필터링
const indexFiles = files.filter(f => f.filename.endsWith('index.md'));
```

### 3. Frontmatter date 파싱 및 미래 날짜 판별

기존 `auto-merge-pr.yml`의 정규식 패턴을 재활용한다.

```javascript
const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

for (const file of indexFiles) {
  const { data: content } = await github.rest.repos.getContent({
    owner, repo, path: file.filename
  });
  const fileContent = Buffer.from(content.content, 'base64').toString('utf-8');
  const dateMatch = fileContent.match(/^---[\s\S]*?date:\s*(\d{4}-\d{2}-\d{2})[\s\S]*?---/);

  if (dateMatch && dateMatch[1] > today) {
    // 미래 날짜 → 보정 대상
  }
}
```

### 4. date/update 필드 치환

`sed` 명령으로 frontmatter 내 `date`와 `update` 필드를 오늘 날짜로 치환한다.

```bash
sed -i "s/^date: ${OLD_DATE}/date: ${TODAY}/" "${FILE_PATH}"
sed -i "s/^update: ${OLD_DATE}/update: ${TODAY}/" "${FILE_PATH}"
```

### 5. 보정 브랜치 생성 및 PR 생성

변경 사항이 있는 경우, 별도 브랜치를 만들어 PR을 생성한다.

```bash
# 보정 브랜치 생성
BRANCH_NAME="chore/fix-future-date-$(date +%Y%m%d)"
git checkout -b "${BRANCH_NAME}"

git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add -A
git diff --cached --quiet || git commit -m "[chore] 미래 날짜를 현재 날짜로 보정"
git push origin "${BRANCH_NAME}"
```

PR 생성은 `actions/github-script@v7`에서 GitHub API로 처리한다.

```javascript
await github.rest.pulls.create({
  owner, repo,
  title: '[chore] 미래 날짜를 현재 날짜로 보정',
  head: branchName,
  base: 'main',
  body: `PR #${prNumber} merge 시 미래 날짜가 감지되어 자동 보정합니다.\n\n변경 파일:\n${changedFiles.join('\n')}`
});
```

### 6. Caller 워크플로우 (blog-v2, investment 공통)

```yaml
name: Fix Future Date

on:
  pull_request:
    types: [closed]

jobs:
  fix-date:
    if: github.event.pull_request.merged == true
    uses: kenshin579/actions/.github/workflows/fix-future-date.yml@main
    with:
      pr_number: ${{ github.event.pull_request.number }}
    secrets: inherit
```

## 동작 흐름

```
1. PR이 merge됨 (caller에서 pull_request closed 이벤트 감지)
2. merge 여부 확인 (github.event.pull_request.merged == true)
3. PR 번호를 재사용 워크플로우에 전달
4. 재사용 워크플로우에서:
   a. 레포 checkout (main 브랜치)
   b. PR 변경 파일에서 index.md 필터링
   c. 각 index.md의 frontmatter date 파싱
   d. 미래 날짜인 경우 date/update를 오늘 날짜로 변경
   e. 변경 사항이 있으면:
      - chore/fix-future-date-YYYYMMDD 브랜치 생성
      - 커밋 & 푸시
      - main 대상 PR 자동 생성
```

## 예외 처리

| 상황 | 처리 방법 |
|-----|---------|
| merge가 아닌 close | caller에서 `if: merged == true`로 필터 |
| index.md 없는 PR | 아무 동작 없이 종료 |
| date 필드 없음 | 해당 파일 스킵 |
| frontmatter 파싱 실패 | 해당 파일 스킵, 로그 출력 |
| 변경 사항 없음 | 브랜치/PR 생성하지 않음 |
| 동일 날짜 보정 브랜치 이미 존재 | 브랜치명에 PR 번호 포함하여 충돌 방지 (`chore/fix-future-date-{pr_number}`) |
