#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_FILE="${THORPE_LAUNCH_PROFILE:-$SCRIPT_DIR/launch-assistant.profile}"

if [[ -f "$PROFILE_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$PROFILE_FILE"
fi

DEFAULT_REPO_PATH="$HOME/Thorpe-Workforce"
REPO_PATH="${THORPE_REPO_PATH:-$DEFAULT_REPO_PATH}"

PROD_FRONTEND_URL="${THORPE_FRONTEND_URL:-https://thorpeworkforce.ai}"
PROD_API_URL="${THORPE_API_URL:-https://api-thorpeworkforce.ai}"
STAGING_FRONTEND_URL="${THORPE_STAGING_FRONTEND_URL:-https://staging.thorpeworkforce.ai}"
STAGING_API_URL="${THORPE_STAGING_API_URL:-https://staging-api.thorpeworkforce.ai}"

RAILWAY_DASHBOARD_URL="${THORPE_RAILWAY_DASHBOARD_URL:-https://railway.app}"
VERCEL_DASHBOARD_URL="${THORPE_VERCEL_DASHBOARD_URL:-https://vercel.com/dashboard}"
STRIPE_DASHBOARD_URL="${THORPE_STRIPE_DASHBOARD_URL:-https://dashboard.stripe.com}"
GITHUB_REPO_URL="${THORPE_GITHUB_REPO_URL:-https://github.com/jonniethorpe45-max/Thorpe-Workforce}"

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

normalize_url() {
  local value="${1:-}"
  value="${value%"${value##*[![:space:]]}"}"
  value="${value#"${value%%[![:space:]]*}"}"
  printf "%s" "${value%/}"
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

configure_domain_defaults() {
  local input=""
  say ""
  read -r -p "Production frontend URL [${PROD_FRONTEND_URL}]: " input
  if [[ -n "${input}" ]]; then PROD_FRONTEND_URL="$(normalize_url "$input")"; fi

  read -r -p "Production API URL [${PROD_API_URL}]: " input
  if [[ -n "${input}" ]]; then PROD_API_URL="$(normalize_url "$input")"; fi

  read -r -p "Staging frontend URL [${STAGING_FRONTEND_URL}]: " input
  if [[ -n "${input}" ]]; then STAGING_FRONTEND_URL="$(normalize_url "$input")"; fi

  read -r -p "Staging API URL [${STAGING_API_URL}]: " input
  if [[ -n "${input}" ]]; then STAGING_API_URL="$(normalize_url "$input")"; fi

  say ""
  ok "Domain defaults updated for this session."
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

check_url() {
  local label="$1"
  local url="$2"
  if curl -fsS --max-time 15 "$url" >/dev/null 2>&1; then
    ok "$label: $url"
    return 0
  fi
  err "$label failed: $url"
  return 1
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

  if [[ ! -f "$SCRIPT_DIR/launch-assistant.profile" && -f "$SCRIPT_DIR/launch-assistant.profile.example" ]]; then
    cp "$SCRIPT_DIR/launch-assistant.profile.example" "$SCRIPT_DIR/launch-assistant.profile"
    ok "Created scripts/macos/launch-assistant.profile from example"
  else
    ok "scripts/macos/launch-assistant.profile already exists"
  fi

  say ""
  warn "Fill real keys and domains in env/profile files before production deployment."
}

start_local_stack() {
  step "Starting local Docker stack"
  (cd "$REPO_PATH" && ./scripts/start_local.sh)
}

smoke_check_deployed_urls() {
  local mode="${1:-production}"
  local frontend_url="$PROD_FRONTEND_URL"
  local api_url="$PROD_API_URL"
  local input=""

  if [[ "$mode" == "staging" ]]; then
    frontend_url="$STAGING_FRONTEND_URL"
    api_url="$STAGING_API_URL"
  fi

  frontend_url="$(normalize_url "$frontend_url")"
  api_url="$(normalize_url "$api_url")"

  step "Deployment smoke checks (${mode})"
  read -r -p "Frontend URL [${frontend_url}]: " input
  if [[ -n "${input}" ]]; then frontend_url="$(normalize_url "$input")"; fi
  read -r -p "API URL [${api_url}]: " input
  if [[ -n "${input}" ]]; then api_url="$(normalize_url "$input")"; fi

  if [[ -z "${frontend_url}" || -z "${api_url}" ]]; then
    warn "Skipped: both frontend and api URLs are required."
    return 0
  fi

  local success_count=0
  local total_count=0

  run_check() {
    local label="$1"
    local url="$2"
    total_count=$((total_count + 1))
    if check_url "$label" "$url"; then
      success_count=$((success_count + 1))
    fi
  }

  run_check "API health" "${api_url}/health"
  run_check "API live" "${api_url}/health/live"
  run_check "API ready" "${api_url}/health/ready"
  run_check "API public workers" "${api_url}/public-workers"
  run_check "API pricing plans" "${api_url}/billing/plans"

  run_check "Frontend home" "${frontend_url}/"
  run_check "Frontend pricing" "${frontend_url}/pricing"
  run_check "Frontend marketplace" "${frontend_url}/marketplace"
  run_check "Frontend login" "${frontend_url}/login"
  run_check "Frontend signup" "${frontend_url}/signup"

  say ""
  if [[ "$success_count" -eq "$total_count" ]]; then
    ok "Smoke checks passed (${success_count}/${total_count})."
  else
    warn "Smoke checks completed with issues (${success_count}/${total_count} passed)."
  fi
}

open_platform_dashboards() {
  step "Opening key dashboards in browser"
  open "$RAILWAY_DASHBOARD_URL"
  open "$VERCEL_DASHBOARD_URL"
  open "$STRIPE_DASHBOARD_URL"
  open "$GITHUB_REPO_URL"
  ok "Opened Railway, Vercel, Stripe, and GitHub dashboards"
}

print_manual_launch_checklist() {
  cat <<CHECKLIST

Manual launch checklist:

Production URLs configured:
- Frontend: ${PROD_FRONTEND_URL}
- API:      ${PROD_API_URL}

Staging URLs configured:
- Frontend: ${STAGING_FRONTEND_URL}
- API:      ${STAGING_API_URL}

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

show_current_config() {
  cat <<CONFIG

Current Launch Assistant config:
- Repo path:            ${REPO_PATH}
- Prod frontend URL:    ${PROD_FRONTEND_URL}
- Prod API URL:         ${PROD_API_URL}
- Staging frontend URL: ${STAGING_FRONTEND_URL}
- Staging API URL:      ${STAGING_API_URL}
- Profile file:         ${PROFILE_FILE}

CONFIG
}

save_profile_file() {
  cat >"$PROFILE_FILE" <<PROFILE
# Auto-generated by ThorpeWorkforceLaunchAssistant.command
# Update values as needed.

export THORPE_REPO_PATH="$REPO_PATH"
export THORPE_FRONTEND_URL="$PROD_FRONTEND_URL"
export THORPE_API_URL="$PROD_API_URL"
export THORPE_STAGING_FRONTEND_URL="$STAGING_FRONTEND_URL"
export THORPE_STAGING_API_URL="$STAGING_API_URL"
export THORPE_RAILWAY_DASHBOARD_URL="$RAILWAY_DASHBOARD_URL"
export THORPE_VERCEL_DASHBOARD_URL="$VERCEL_DASHBOARD_URL"
export THORPE_STRIPE_DASHBOARD_URL="$STRIPE_DASHBOARD_URL"
export THORPE_GITHUB_REPO_URL="$GITHUB_REPO_URL"
PROFILE
  ok "Saved profile: $PROFILE_FILE"
}

menu() {
  while true; do
    cat <<'MENU'

Thorpe Workforce Launch Assistant
--------------------------------
1) Set/verify repo path
2) Show current config
3) Configure production/staging URLs
4) Run preflight checks
5) Create env/profile files from templates
6) Save current config to profile file
7) Start local stack (docker compose)
8) Run production smoke checks
9) Run staging smoke checks
10) Open Railway/Vercel/Stripe dashboards
11) Print manual launch checklist
12) Exit

MENU
    read -r -p "Choose an option [1-12]: " option
    case "$option" in
      1) prompt_repo_path; assert_repo ;;
      2) show_current_config ;;
      3) configure_domain_defaults ;;
      4) assert_repo && run_preflight ;;
      5) assert_repo && copy_env_templates ;;
      6) save_profile_file ;;
      7) assert_repo && start_local_stack ;;
      8) smoke_check_deployed_urls "production" ;;
      9) smoke_check_deployed_urls "staging" ;;
      10) open_platform_dashboards ;;
      11) print_manual_launch_checklist ;;
      12) exit 0 ;;
      *) warn "Invalid option. Choose 1-12." ;;
    esac
  done
}

say "${CYAN}Thorpe Workforce macOS Launch Assistant${NC}"
show_current_config
prompt_repo_path
assert_repo
menu
