# Auto Merge PR 구현 문서

## 개요

MD 파일의 YAML frontmatter `date:` 필드를 기준으로 PR merge 여부를 결정하도록 `auto-merge-pr.yml` 워크플로우를 수정한다.

## 수정 대상 파일

- `actions/.github/workflows/auto-merge-pr.yml`

## 핵심 구현 사항

### 1. PR별 date 필드 추출 함수 추가

각 PR에서 변경된 MD 파일의 frontmatter `date:` 필드를 추출하는 헬퍼 함수를 구현한다.

```javascript
async function getPostDateFromPR(github, owner, repo, pr) {
  // 1. PR에서 변경된 파일 목록 조회
  const { data: files } = await github.rest.pulls.listFiles({
    owner,
    repo,
    pull_number: pr.number
  });

  // 2. MD 파일 필터링 (contents/ 디렉토리 내 index.md 우선)
  const mdFiles = files.filter(f => f.filename.endsWith('.md'));
  if (mdFiles.length === 0) return null;

  // 3. 첫 번째 MD 파일 내용 조회
  const targetFile = mdFiles.find(f => f.filename.includes('index.md')) || mdFiles[0];
  const { data: content } = await github.rest.repos.getContent({
    owner,
    repo,
    path: targetFile.filename,
    ref: pr.head.ref
  });

  // 4. Base64 디코딩 및 frontmatter date 파싱
  const fileContent = Buffer.from(content.content, 'base64').toString('utf-8');
  const dateMatch = fileContent.match(/^---[\s\S]*?date:\s*(\d{4}-\d{2}-\d{2})[\s\S]*?---/);

  return dateMatch ? dateMatch[1] : null;
}
```

### 2. merge 대상 필터링 로직 수정

기존 `created_at` 기반 정렬을 `date` 필드 기반으로 변경하고, 미래 날짜 PR은 제외한다.

```javascript
// 오늘 날짜 (시간 제외)
const today = new Date();
today.setHours(0, 0, 0, 0);

// 각 PR에 postDate 추가
for (const pr of mergeReadyPRs) {
  pr.postDate = await getPostDateFromPR(github, owner, repo, pr);
}

// 미래 날짜 PR 제외 (date가 없으면 포함)
const eligiblePRs = mergeReadyPRs.filter(pr => {
  if (!pr.postDate) return true; // date 없으면 기존 로직 적용
  const postDate = new Date(pr.postDate);
  return postDate <= today;
});

// postDate 기준 정렬 (오래된 날짜 우선, date 없으면 created_at 사용)
eligiblePRs.sort((a, b) => {
  const dateA = a.postDate ? new Date(a.postDate) : new Date(a.created_at);
  const dateB = b.postDate ? new Date(b.postDate) : new Date(b.created_at);
  return dateA - dateB;
});
```

### 3. 로그 출력 개선

디버깅을 위해 각 PR의 postDate와 merge 대상 여부를 로그로 출력한다.

```javascript
console.log(`PR #${pr.number}: postDate=${pr.postDate || 'N/A'}, eligible=${postDate <= today}`);
```

## 동작 흐름

```
1. MergeReady 라벨이 있는 PR 목록 조회
2. 각 PR에서 MD 파일의 frontmatter date 추출
3. date <= 오늘인 PR만 필터링
4. date 기준 정렬 (오래된 날짜 우선)
5. 주간 merge 제한 확인
6. 가장 오래된 eligible PR 선택 및 merge
```

## 예외 처리

| 상황 | 처리 방법 |
|-----|---------|
| MD 파일 없음 | `created_at` 기준 정렬에 포함 |
| date 필드 없음 | `created_at` 기준 정렬에 포함 |
| date 파싱 실패 | `created_at` 기준 정렬에 포함 |
| API 호출 실패 | try-catch로 감싸고 `created_at` 사용 |
