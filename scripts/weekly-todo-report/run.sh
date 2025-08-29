# 1) 환경변수 설정
export OPENAI_BASE_URL=$MODEL_CONNECT_API_URL
export OPENAI_API_KEY=$MODEL_CONNECT_API_KEY

export GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_API_KEY
export GITHUB_TOOLSETS="repos,issues,pull_requests"
export GITHUB_READ_ONLY="1"                        # 안전하게 조회 전용

echo "OPENAI_BASE_URL: $OPENAI_BASE_URL"
echo "OPENAI_API_KEY: $OPENAI_API_KEY"


export REPOS="kenshin579/tutorials-python, kenshin579/actions, kenshin579/inspireme.advenoh.pe.kr, kenshin579/stock.advenoh.pe.kr"
export TEAM_YAML="./team.yml"
export OPENAI_MODEL="gpt-4.1-mini"                 # 내부 모델명으로 교체 가능

# 2) 실행 (로컬 가상환경 활성화 후, 편의상 개발 모드 설치 및 실행)
# 사용자가 요청한 명령: source ../../.venv/bin/activate && pip install -e scripts/weekly-todo-report
# - 프로젝트 루트에 .venv 가 있다고 가정합니다.
# - pyproject.toml 은 scripts/weekly-todo-report 디렉토리에 존재합니다.
set -euo pipefail

# pip install -e .

# 스크립트 실행
#source .venv/bin/activate && python main.py