#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from typing import List, Optional

from agents import (
    Agent,
    Runner,
    ModelSettings,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_default_openai_client,
    set_tracing_disabled,
)
from agents.mcp import MCPServerStdio

# ---------- 설정 ----------

KST = ZoneInfo("Asia/Seoul")

@dataclass
class Repo:
    owner: str
    name: str

def parse_repos(env: str) -> List[Repo]:
    # "owner1/repo1,owner2/repo2" 형식
    items = [x.strip() for x in env.split(",") if x.strip()]
    repos: List[Repo] = []
    for it in items:
        if "/" not in it:
            raise ValueError(f"REPOS 형식 오류: {it} (owner/repo 필요)")
        owner, name = it.split("/", 1)
        repos.append(Repo(owner=owner, name=name))
    return repos

def this_week_range_kst(now: Optional[datetime] = None):
    """
    전 토요일 00:00 (KST) ~ 이번주 금요일 23:59:59 (KST)
    """
    now = now or datetime.now(tz=KST)

    # 전 토요일 계산 (weekday: 월=0, 화=1, 수=2, 목=3, 금=4, 토=5, 일=6)
    if now.weekday() == 5:  # 토요일
        start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=KST)
    elif now.weekday() == 6:  # 일요일
        yesterday = now - timedelta(days=1)
        start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, tzinfo=KST)
    else:  # 월~금 (0-4)
        # 전 토요일 = 이번주 토요일 (weekday=5)
        days_to_saturday = (now.weekday() - 5) % 7
        saturday = now - timedelta(days=days_to_saturday)
        start = datetime(saturday.year, saturday.month, saturday.day, 0, 0, 0, tzinfo=KST)

    # 이번주 금요일 계산 (토요일부터 6일 후)
    friday = start + timedelta(days=6)
    end = datetime(friday.year, friday.month, friday.day, 23, 59, 59, tzinfo=KST)

    return start, end

def iso_utc(dt_kst: datetime) -> str:
    return dt_kst.astimezone(ZoneInfo("UTC")).isoformat()

# ---------- 메인 에이전트 ----------

async def build_agent(repos: List[Repo], start_kst: datetime, end_kst: datetime) -> Agent:
    """
    Agents SDK + GitHub MCP (Docker, stdio) 연동 에이전트 구성
    - MCP 서버는 read-only 로 띄워 안전하게 조회만 수행
    """
    # 사내 OpenAI-호환 엔드포인트 설정
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("OPENAI_BASE_URL / OPENAI_API_KEY 환경변수를 설정하세요.")
    set_default_openai_client(AsyncOpenAI(base_url=base_url, api_key=api_key))

    # 사내/폐쇄망 등에서 OpenAI 트레이싱을 쓰지 않도록 비활성화
    set_tracing_disabled(True)

    # GitHub MCP 서버(docker) 연결 파라미터
    # - 공식 이미지: ghcr.io/github/github-mcp-server  (read-only/툴셋 제한 지원)
    # - github.com 사용 (Enterprise Server 미사용)
    mcp_env = {
        "GITHUB_PERSONAL_ACCESS_TOKEN": os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN") or "",
        "GITHUB_TOOLSETS": os.environ.get("GITHUB_TOOLSETS", "repos,issues,pull_requests"),
        "GITHUB_READ_ONLY": os.environ.get("GITHUB_READ_ONLY", "1"),
    }

    if not mcp_env["GITHUB_PERSONAL_ACCESS_TOKEN"]:
        raise RuntimeError("GITHUB_PERSONAL_ACCESS_TOKEN (또는 GITHUB_TOKEN) 환경변수를 설정하세요.")

    github_mcp = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                "-e", "GITHUB_TOOLSETS",
                "-e", "GITHUB_READ_ONLY",
                "ghcr.io/github/github-mcp-server",
            ],
            "env": mcp_env,  # 환경변수를 params 안에 포함
        },
        cache_tools_list=True,   # 툴 목록 캐시
    )

    # MCP 서버 연결
    await github_mcp.connect()

    # 보고서 생성 지시문 (한국어)
    start_iso_kst = start_kst.isoformat()
    end_iso_kst = end_kst.isoformat()
    start_iso_utc = iso_utc(start_kst)
    end_iso_utc = iso_utc(end_kst)

    repo_text = "\n".join([f"- {r.owner}/{r.name}" for r in repos])

    # GitHub MCP가 제공하는 검색/이슈/PR 관련 툴을 사용하여 데이터 수집하도록 지시
    # (서버가 노출하는 툴 이름은 버전에 따라 다를 수 있으나, MCP 툴 설명을 기반으로 LLM이 선택함)
    instructions = f"""
당신은 '주간업무 보고서 봇'입니다. 반드시 GitHub MCP 툴만 사용해 데이터를 수집한 뒤 한국어 Markdown 보고서를 작성하세요.

[타임프레임]
- 기준 타임존: KST(Asia/Seoul)
- KST: {start_iso_kst} ~ {end_iso_kst}
- UTC: {start_iso_utc} ~ {end_iso_utc}

[대상 저장소]
{repo_text}

[수집 지침]
1) '이번주' 범위({start_iso_utc}..{end_iso_utc}, UTC)로 다음을 각 repo별로 수집:
   - 머지된 PR (is:pr is:merged merged:범위)
   - 닫힌 이슈 (is:issue is:closed closed:범위)
   - (가능하면) 커밋/릴리즈 노트/Actions 실패율 등도 조회
2) 각 항목에 대해: 제목, 링크, 작성자, 라벨, 머지/클로즈 일시, (가능하면) 변경 파일 수/추가/삭제 라인.
3) 개인별 성과 집계: PR/이슈 수, 주요 기여 요약.
4) '리스크/차주 계획' 섹션은 수집된 이슈/PR 라벨과 설명, 코멘트를 참고해 간결히 작성.

[출력 포맷: Markdown]
# {end_kst.date().isoformat()} 주간업무 보고서
- 보고 범위: {start_iso_kst} ~ {end_iso_kst} (KST)

## 하이라이트 (3~6줄)
- ...

## 개인별 요약
- PR/이슈 수와 핵심 성과 bullet

## 레포지토리별 상세
### owner/repo
- PR: ...
- 이슈: ...

## 메트릭 (가능하면)
- PR 머지 수, 평균 리드타임, 라벨 분포 등

## 리스크 & 차주 계획
- ...

[중요] 반드시 MCP 툴을 호출해서 실제 데이터로 작성. 임의로 지어내지 말 것.
    """.strip()

    agent = Agent(
        name="Weekly Reporter",
        instructions=instructions,
        # Responses API 미지원 엔드포인트 대비: Chat Completions 형태로 강제
        model=OpenAIChatCompletionsModel(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            openai_client=AsyncOpenAI(base_url=base_url, api_key=api_key),
        ),
        model_settings=ModelSettings(temperature=0.2),
        mcp_servers=[github_mcp],
    )
    return agent

async def main():
    # 환경변수
    repos_env = os.getenv("REPOS")  # 예: "your-org/app, your-org/data-pipeline"
    if not repos_env:
        raise RuntimeError("REPOS 환경변수에 'owner/repo' 콤마리스트를 지정하세요.")
    repos = parse_repos(repos_env)

    start_kst, end_kst = this_week_range_kst()

    agent = await build_agent(repos, start_kst, end_kst)

    # 프롬프트는 간단히. 상세 지시는 instructions에 있음.
    user_input = "이번주 주간업무 보고서를 작성해줘. 모든 수치는 MCP로 확인해."
    result = await Runner.run(agent, input=user_input, max_turns=3)

    md = result.final_output or "(결과가 비어있습니다)"
    out_name = f"weekly_report_{end_kst.date().isoformat()}.md"
    with open(out_name, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\n✅ 저장됨: {out_name}\n")

if __name__ == "__main__":
    asyncio.run(main())