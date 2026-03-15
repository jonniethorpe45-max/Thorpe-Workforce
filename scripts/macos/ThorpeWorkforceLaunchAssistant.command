#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_PATH="$HOME/Thorpe-Workforce"
REPO_PATH="${THORPE_REPO_PATH:-$DEFAULT_REPO_PATH}"

GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

say() {
  printf "%b\n" "$1"
}

step() {
  say "${CYAN}==>${NC} $1"
}

ok() {
  say "${GREEN}✓${NC} $1"
}

warn() {
  say "${YELLOW}!${NC} $1"
}

err() {
  say "${RED}x${NC} $1"
}

prompt_repo_path() {
  say ""
  say "Current repo path: ${REPO_PATH}"
  read -r -p "Use this path? [Y/n] " keep_path
  if [[ "${keep_path:-Y}" =~ ^[Nn]$ ]]; then
    read -r -p "Enter full path to your Thorpe Workforce repo: " new_path
    if [[ -n "${new_path}" ]]; then
      REPO_PATH="${new_path}"
    fi
  fi
}

assert_repo() {
  if [[ ! -d "$REPO_PATH" ]]; then
    err "Repo path not found: $REPO_PATH"
    return 1
  fi
  if [[ ! -f "$REPO_PATH/README.md" || ! -d "$REPO_PATH/frontend" || ! -d "$REPO_PATH/backend" ]]; then
    err "Path does not look like the Thorpe Workforce repo: $REPO_PATH"
    return 1
  fi
  ok "Repo path verified: $REPO_PATH"
}

check_command() {
  local command_name="$1"
  if command -v "$command_name" >/dev/null 2>&1; then
    ok "$command_name installed"
  else
    warn "$command_name not found"
  fi
}

run_preflight() {
  step "Running preflight checks"
  check_command git
  check_command docker
  check_command node
  check_command npm
  check_command python3
  check_command curl
  check_command open
  check_command gh
  say ""
  warn "If docker/node/python are missing, install them before local startup."
}

copy_env_templates() {
  step "Ensuring env template files exist"
  if [[ ! -f "$REPO_PATH/.env.staging" ]]; then
    cp "$REPO_PATH/.env.staging.example" "$REPO_PATH/.env.staging"
    ok "Created .env.staging from template"
  else
    ok ".env.staging already exists"
  fi

  if [[ ! -f "$REPO_PATH/.env.production" ]]; then
    cp "$REPO_PATH/.env.production.example" "$REPO_PATH/.env.production"
    ok "Created .env.production from template"
  else
    ok ".env.production already exists"
  fi

  if [[ ! -f "$REPO_PATH/backend/.env" ]]; then
    cp "$REPO_PATH/backend/.env.example" "$REPO_PATH/backend/.env"
    ok "Created backend/.env from template"
  else
    ok "backend/.env already exists"
  fi

  if [[ ! -f "$REPO_PATH/frontend/.env.local" ]]; then
    cp "$REPO_PATH/frontend/.env.example" "$REPO_PATH/frontend/.env.local"
    ok "Created frontend/.env.local from template"
  else
    ok "frontend/.env.local already exists"
  fi

  say ""
  warn "Fill real keys and domains in env files before production deployment."
}

start_local_stack() {
  step "Starting local Docker stack"
  (cd "$REPO_PATH" && ./scripts/start_local.sh)
}

smoke_check_deployed_urls() {
  step "Deployment smoke checks"
  read -r -p "Frontend URL (e.g. https://thorpeworkforce.ai): " frontend_url
  read -r -p "Backend API URL (e.g. https://api.thorpeworkforce.ai): " api_url

  if [[ -z "${frontend_url}" || -z "${api_url}" ]]; then
    warn "Skipped: both frontend and api URLs are required."
    return 0
  fi

  local health_url="${api_url%/}/health"
  local live_url="${api_url%/}/health/live"
  local ready_url="${api_url%/}/health/ready"

  step "Checking API health endpoints"
  curl -fsS "$health_url" >/dev/null && ok "$health_url"
  curl -fsS "$live_url" >/dev/null && ok "$live_url"
  curl -fsS "$ready_url" >/dev/null && ok "$ready_url"

  step "Checking frontend homepage"
  curl -fsS "${frontend_url%/}/" >/dev/null && ok "${frontend_url%/}/"

  say ""
  ok "Smoke checks completed."
}

open_platform_dashboards() {
  step "Opening key dashboards in browser"
  open "https://railway.app"
  open "https://vercel.com/dashboard"
  open "https://dashboard.stripe.com"
  open "https://github.com"
  ok "Opened Railway, Vercel, Stripe, and GitHub dashboards"
}

print_manual_launch_checklist() {
  cat <<'CHECKLIST'

Manual launch checklist:

1) Railway
   - API service healthy at /health/ready
   - Worker service running
   - Postgres + Redis attached
   - DATABASE_URL / REDIS_URL set

2) Vercel
   - NEXT_PUBLIC_API_BASE_URL set to production API
   - NEXT_PUBLIC_APP_URL set to production frontend domain
   - Latest deploy is green

3) DNS
   - frontend domain points to Vercel
   - api subdomain points to Railway

4) Stripe (if enabled)
   - Correct test/live keys configured per environment
   - webhook endpoint set: /billing/webhooks/stripe
   - webhook secret set in backend env

5) Final smoke test
   - homepage
   - signup/login
   - onboarding
   - marketplace listing
   - worker install + run
   - founder OS page + chain run
   - admin pages
   - /health /health/live /health/ready

CHECKLIST
}

menu() {
  while true; do
    cat <<'MENU'

Thorpe Workforce Launch Assistant
--------------------------------
1) Set/verify repo path
2) Run preflight checks
3) Create env files from templates
4) Start local stack (docker compose)
5) Run deployed smoke checks (URLs)
6) Open Railway/Vercel/Stripe dashboards
7) Print manual launch checklist
8) Exit

MENU
    read -r -p "Choose an option [1-8]: " option
    case "$option" in
      1) prompt_repo_path; assert_repo ;;
      2) assert_repo && run_preflight ;;
      3) assert_repo && copy_env_templates ;;
      4) assert_repo && start_local_stack ;;
      5) smoke_check_deployed_urls ;;
      6) open_platform_dashboards ;;
      7) print_manual_launch_checklist ;;
      8) exit 0 ;;
      *) warn "Invalid option. Choose 1-8." ;;
    esac
  done
}

say "${CYAN}Thorpe Workforce macOS Launch Assistant${NC}"
prompt_repo_path
assert_repo
menu
