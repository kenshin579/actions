#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import argparse
import re
import signal
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

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

def load_prompt_template(template_name: str) -> str:
    """Load prompt template from .prompts directory"""
    template_path = os.path.join(".prompts", template_name)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(f"Prompt template not found: {template_path}")

def format_prompt_template(template: str, **kwargs) -> str:
    """Format prompt template with provided variables"""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise RuntimeError(f"Missing template variable: {e}")

def parse_yaml_header(content: str) -> Dict[str, Any]:
    """Parse YAML header from markdown content"""
    yaml_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.search(yaml_pattern, content, re.DOTALL)

    if not match:
        return {}

    yaml_content = match.group(1)

    # Simple YAML parsing for github section
    result = {}
    lines = yaml_content.strip().split('\n')

    current_section = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('github:'):
            current_section = 'github'
            result['github'] = {}
        elif current_section == 'github':
            if line.startswith('owner:'):
                owner = line.split(':', 1)[1].strip()
                result['github']['owner'] = owner
            elif line.startswith('repos:'):
                result['github']['repos'] = []
            elif line.startswith('- ') and 'repos' in result['github']:
                repo = line[2:].strip()
                result['github']['repos'].append(repo)

    return result

def extract_github_info_from_prompt(prompts_file: str) -> tuple[str, List[str]]:
    """Extract github owner and repos from prompt file"""
    template_content = load_prompt_template(prompts_file)
    yaml_data = parse_yaml_header(template_content)

    if 'github' not in yaml_data:
        raise RuntimeError(f"GitHub 정보가 {prompts_file} 파일에 없습니다.")

    github_info = yaml_data['github']
    owner = github_info.get('owner')
    repos = github_info.get('repos', [])

    if not owner:
        raise RuntimeError(f"GitHub owner가 {prompts_file} 파일에 없습니다.")

    if not repos:
        raise RuntimeError(f"GitHub repos가 {prompts_file} 파일에 없습니다.")

    return owner, repos

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="주간업무 보고서 생성 봇",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py
  python main.py --prompts-file custom_report.md --output-dir ./reports

주의: 대상 저장소와 GitHub 정보는 프롬프트 파일의 YAML 헤더에서 자동으로 읽어옵니다.
        """
    )

    parser.add_argument(
        '--prompts-file',
        type=str,
        default='weekly_report.md',
        help='사용할 프롬프트 템플릿 파일 (.prompts 폴더 내 파일명) (기본값: weekly_report.md)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='보고서 파일을 생성할 디렉토리 (기본값: 현재 디렉토리)'
    )

    return parser.parse_args()

# ---------- 메인 에이전트 ----------

async def build_agent(repos: List[Repo], start_kst: datetime, end_kst: datetime, prompts_file: str = "weekly_report.md") -> tuple[Agent, MCPServerStdio]:
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

    # 보고서 생성 지시문 (한국어) - 외부 템플릿 파일에서 로드
    start_iso_kst = start_kst.isoformat()
    end_iso_kst = end_kst.isoformat()
    start_iso_utc = iso_utc(start_kst)
    end_iso_utc = iso_utc(end_kst)

    repo_text = "\n".join([f"- {r.owner}/{r.name}" for r in repos])

    # 템플릿 파일에서 프롬프트 로드 및 변수 치환
    template = load_prompt_template(prompts_file)
    instructions = format_prompt_template(
        template,
        start_iso_kst=start_iso_kst,
        end_iso_kst=end_iso_kst,
        start_iso_utc=start_iso_utc,
        end_iso_utc=end_iso_utc,
        repo_text=repo_text,
        start_date=start_kst.date().isoformat(),
        end_date=end_kst.date().isoformat()
    )

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
    return agent, github_mcp

async def main():
    # 명령어 인자 파싱
    args = parse_arguments()
    github_mcp = None

    try:
        # 프롬프트 파일에서 GitHub 정보 추출
        owner, repo_names = extract_github_info_from_prompt(args.prompts_file)
        print(f"✅ 프롬프트 파일에서 GitHub 정보 로드: {owner} (레포지토리 {len(repo_names)}개)")

        # Repo 객체 생성
        repos = [Repo(owner=owner, name=repo_name) for repo_name in repo_names]

        start_kst, end_kst = this_week_range_kst()

        # 에이전트 생성 (MCP 클라이언트 포함)
        agent, github_mcp = await build_agent(repos, start_kst, end_kst, args.prompts_file)

        # 프롬프트는 간단히. 상세 지시는 instructions에 있음.
        user_input = "이번주 주간업무 보고서를 작성해줘. 모든 수치는 MCP로 확인해."

        print("🔄 보고서 생성 중...")
        result = await Runner.run(agent, input=user_input, max_turns=3)

        md = result.final_output or "(결과가 비어있습니다)"

        # 출력 디렉토리 생성 및 파일 저장
        output_dir = os.path.abspath(args.output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # 파일명 생성: 파일이름_startdate_enddate.md (또는 _HHMMSS.md)
        prompt_basename = os.path.splitext(args.prompts_file)[0]  # 확장자 제거
        start_date = start_kst.date().isoformat()
        end_date = end_kst.date().isoformat()

        # 기본 파일명 생성
        base_name = f"{prompt_basename}_{start_date}_{end_date}"
        out_name = f"{base_name}.md"
        out_path = os.path.join(output_dir, out_name)

        # 파일이 이미 존재하는 경우 타임스탬프 추가
        if os.path.exists(out_path):
            current_time = datetime.now().strftime("%H%M%S")
            out_name = f"{base_name}_{current_time}.md"
            out_path = os.path.join(output_dir, out_name)
            print(f"📁 기존 파일이 존재하여 타임스탬프 추가: {out_name}")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"\n✅ 보고서 생성 완료!")
        print(f"📁 저장 위치: {out_path}")
        print(f"📊 보고서 기간: {start_date} ~ {end_date}")

    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        raise
    finally:
        # MCP 클라이언트 정리
        if github_mcp:
            try:
                print("🔄 MCP 클라이언트 연결 해제 중...")
                await github_mcp.disconnect()
                print("✅ MCP 클라이언트 연결 해제 완료")
            except Exception as e:
                print(f"⚠️  MCP 클라이언트 연결 해제 중 오류 (무시됨): {e}")
                # MCP 연결 해제 오류는 무시하고 계속 진행

async def run_main():
    """메인 함수를 시그널 핸들링과 함께 실행"""
    # 시그널 핸들러 설정
    def signal_handler(signum, frame):
        print(f"\n⚠️  시그널 {signum} 수신. 안전하게 종료합니다...")
        raise KeyboardInterrupt("사용자 시그널로 인한 중단")

    # SIGINT (Ctrl+C) 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)

    try:
        await main()
    except KeyboardInterrupt:
        print("\n⚠️  프로그램이 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\n❌ 치명적 오류: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(run_main())
    exit(exit_code)