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
PROD_API_URL="${THORPE_API_URL:-https://api-thorpeworkforce.com}"
STAGING_FRONTEND_URL="${THORPE_STAGING_FRONTEND_URL:-https://staging.thorpeworkforce.ai}"
STAGING_API_URL="${THORPE_STAGING_API_URL:-https://staging-api.thorpeworkforce.ai}"
SUPPORT_EMAIL="${THORPE_SUPPORT_EMAIL:-support@thorpeworkforce.ai}"
DEFAULT_ENVIRONMENT="${THORPE_ENVIRONMENT:-production}"

RAILWAY_DASHBOARD_URL="${THORPE_RAILWAY_DASHBOARD_URL:-https://railway.app}"
VERCEL_DASHBOARD_URL="${THORPE_VERCEL_DASHBOARD_URL:-https://vercel.com/dashboard}"
STRIPE_DASHBOARD_URL="${THORPE_STRIPE_DASHBOARD_URL:-https://dashboard.stripe.com}"
GITHUB_REPO_URL="${THORPE_GITHUB_REPO_URL:-https://github.com/jonniethorpe45-max/Thorpe-Workforce}"
IONOS_ZONE_DOMAIN="${THORPE_IONOS_ZONE_DOMAIN:-}"
RAILWAY_API_CNAME_TARGET="${THORPE_RAILWAY_API_CNAME_TARGET:-REPLACE_WITH_PROD_RAILWAY_DOMAIN.up.railway.app}"
RAILWAY_STAGING_API_CNAME_TARGET="${THORPE_RAILWAY_STAGING_API_CNAME_TARGET:-REPLACE_WITH_STAGING_RAILWAY_DOMAIN.up.railway.app}"
VERCEL_CNAME_TARGET="${THORPE_VERCEL_CNAME_TARGET:-cname.vercel-dns.com}"
VERCEL_APEX_A_TARGET="${THORPE_VERCEL_APEX_A_TARGET:-76.76.21.21}"
DNS_DEFAULT_TTL="${THORPE_DNS_DEFAULT_TTL:-3600}"
STRIPE_MODE="${THORPE_STRIPE_MODE:-test}"
STRIPE_SECRET_KEY="${THORPE_STRIPE_SECRET_KEY:-}"
STRIPE_PUBLISHABLE_KEY="${THORPE_STRIPE_PUBLISHABLE_KEY:-}"
STRIPE_WEBHOOK_SECRET="${THORPE_STRIPE_WEBHOOK_SECRET:-}"
STRIPE_PRICE_ID_PRO_MONTHLY="${THORPE_STRIPE_PRICE_ID_PRO_MONTHLY:-}"
STRIPE_PRICE_ID_PRO_ANNUAL="${THORPE_STRIPE_PRICE_ID_PRO_ANNUAL:-}"
STRIPE_PRICE_ID_CREATOR_MONTHLY="${THORPE_STRIPE_PRICE_ID_CREATOR_MONTHLY:-}"
STRIPE_PRICE_ID_CREATOR_ANNUAL="${THORPE_STRIPE_PRICE_ID_CREATOR_ANNUAL:-}"
STRIPE_PRICE_ID_ENTERPRISE_MONTHLY="${THORPE_STRIPE_PRICE_ID_ENTERPRISE_MONTHLY:-}"
STRIPE_BILLING_PORTAL_RETURN_URL="${THORPE_STRIPE_BILLING_PORTAL_RETURN_URL:-}"

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

host_from_url() {
  local value
  value="$(normalize_url "${1:-}")"
  value="${value#*://}"
  value="${value%%/*}"
  printf "%s" "$value"
}

dns_label_for_host() {
  local host="$1"
  local zone="$2"
  if [[ -z "$host" || -z "$zone" ]]; then
    printf "%s" "$host"
    return 0
  fi
  if [[ "$host" == "$zone" ]]; then
    printf "@"
    return 0
  fi
  if [[ "$host" == *".${zone}" ]]; then
    printf "%s" "${host%.${zone}}"
    return 0
  fi
  printf "%s" "$host"
}

mask_secret() {
  local value="${1:-}"
  local len=0
  if [[ -z "$value" ]]; then
    printf "%s" "(not set)"
    return 0
  fi
  len="${#value}"
  if ((len <= 8)); then
    printf "***"
    return 0
  fi
  printf "%s***%s" "${value:0:4}" "${value:len-4:4}"
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
  read -r -p "Environment mode [${DEFAULT_ENVIRONMENT}] (production/staging): " input
  if [[ -n "${input}" ]]; then DEFAULT_ENVIRONMENT="${input}"; fi

  read -r -p "Support email [${SUPPORT_EMAIL}]: " input
  if [[ -n "${input}" ]]; then SUPPORT_EMAIL="${input}"; fi

  read -r -p "Production frontend URL [${PROD_FRONTEND_URL}]: " input
  if [[ -n "${input}" ]]; then PROD_FRONTEND_URL="$(normalize_url "$input")"; fi

  read -r -p "Production API URL [${PROD_API_URL}]: " input
  if [[ -n "${input}" ]]; then PROD_API_URL="$(normalize_url "$input")"; fi

  read -r -p "Staging frontend URL [${STAGING_FRONTEND_URL}]: " input
  if [[ -n "${input}" ]]; then STAGING_FRONTEND_URL="$(normalize_url "$input")"; fi

  read -r -p "Staging API URL [${STAGING_API_URL}]: " input
  if [[ -n "${input}" ]]; then STAGING_API_URL="$(normalize_url "$input")"; fi

  if [[ -z "$IONOS_ZONE_DOMAIN" ]]; then
    IONOS_ZONE_DOMAIN="$(host_from_url "$PROD_FRONTEND_URL")"
  fi
  read -r -p "IONOS DNS zone domain [${IONOS_ZONE_DOMAIN}]: " input
  if [[ -n "${input}" ]]; then IONOS_ZONE_DOMAIN="${input}"; fi

  read -r -p "Railway production API CNAME target [${RAILWAY_API_CNAME_TARGET}]: " input
  if [[ -n "${input}" ]]; then RAILWAY_API_CNAME_TARGET="${input}"; fi

  read -r -p "Railway staging API CNAME target [${RAILWAY_STAGING_API_CNAME_TARGET}]: " input
  if [[ -n "${input}" ]]; then RAILWAY_STAGING_API_CNAME_TARGET="${input}"; fi

  say ""
  ok "Domain defaults updated for this session."
}

configure_stripe_settings() {
  local input=""
  local default_portal_url="$STRIPE_BILLING_PORTAL_RETURN_URL"
  if [[ -z "$default_portal_url" ]]; then
    default_portal_url="$(normalize_url "$PROD_FRONTEND_URL")/app/settings/billing"
  fi

  say ""
  step "Configure Stripe settings"
  read -r -p "Stripe mode [${STRIPE_MODE}] (test/live): " input
  if [[ -n "${input}" ]]; then STRIPE_MODE="${input}"; fi

  read -r -p "STRIPE_SECRET_KEY [$(mask_secret "$STRIPE_SECRET_KEY")]: " input
  if [[ -n "${input}" ]]; then STRIPE_SECRET_KEY="${input}"; fi

  read -r -p "STRIPE_PUBLISHABLE_KEY [$(mask_secret "$STRIPE_PUBLISHABLE_KEY")]: " input
  if [[ -n "${input}" ]]; then STRIPE_PUBLISHABLE_KEY="${input}"; fi

  read -r -p "STRIPE_WEBHOOK_SECRET [$(mask_secret "$STRIPE_WEBHOOK_SECRET")]: " input
  if [[ -n "${input}" ]]; then STRIPE_WEBHOOK_SECRET="${input}"; fi

  read -r -p "STRIPE_PRICE_ID_PRO_MONTHLY [${STRIPE_PRICE_ID_PRO_MONTHLY:-unset}]: " input
  if [[ -n "${input}" ]]; then STRIPE_PRICE_ID_PRO_MONTHLY="${input}"; fi

  read -r -p "STRIPE_PRICE_ID_PRO_ANNUAL [${STRIPE_PRICE_ID_PRO_ANNUAL:-unset}]: " input
  if [[ -n "${input}" ]]; then STRIPE_PRICE_ID_PRO_ANNUAL="${input}"; fi

  read -r -p "STRIPE_PRICE_ID_CREATOR_MONTHLY [${STRIPE_PRICE_ID_CREATOR_MONTHLY:-unset}]: " input
  if [[ -n "${input}" ]]; then STRIPE_PRICE_ID_CREATOR_MONTHLY="${input}"; fi

  read -r -p "STRIPE_PRICE_ID_CREATOR_ANNUAL [${STRIPE_PRICE_ID_CREATOR_ANNUAL:-unset}]: " input
  if [[ -n "${input}" ]]; then STRIPE_PRICE_ID_CREATOR_ANNUAL="${input}"; fi

  read -r -p "STRIPE_PRICE_ID_ENTERPRISE_MONTHLY [${STRIPE_PRICE_ID_ENTERPRISE_MONTHLY:-unset}]: " input
  if [[ -n "${input}" ]]; then STRIPE_PRICE_ID_ENTERPRISE_MONTHLY="${input}"; fi

  read -r -p "STRIPE_BILLING_PORTAL_RETURN_URL [${default_portal_url}]: " input
  if [[ -n "${input}" ]]; then
    STRIPE_BILLING_PORTAL_RETURN_URL="$(normalize_url "$input")"
  else
    STRIPE_BILLING_PORTAL_RETURN_URL="$default_portal_url"
  fi

  say ""
  ok "Stripe settings updated for this session."
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
  check_command stripe
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
   - use menu option 17 to print IONOS DNS record plan

4) Stripe (if enabled)
   - Correct test/live keys configured per environment
   - webhook endpoint set: /billing/webhooks/stripe
   - webhook secret set in backend env
   - use menu options 13-16 for Stripe helper flow

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
  local zone_display="$IONOS_ZONE_DOMAIN"
  if [[ -z "$zone_display" ]]; then
    zone_display="$(host_from_url "$PROD_FRONTEND_URL")"
  fi
  cat <<CONFIG

Current Launch Assistant config:
- Repo path:            ${REPO_PATH}
- Environment mode:     ${DEFAULT_ENVIRONMENT}
- Support email:        ${SUPPORT_EMAIL}
- Prod frontend URL:    ${PROD_FRONTEND_URL}
- Prod API URL:         ${PROD_API_URL}
- Staging frontend URL: ${STAGING_FRONTEND_URL}
- Staging API URL:      ${STAGING_API_URL}
- IONOS zone domain:    ${zone_display}
- Railway API target:   ${RAILWAY_API_CNAME_TARGET}
- Railway stg API tgt:  ${RAILWAY_STAGING_API_CNAME_TARGET}
- Stripe mode:          ${STRIPE_MODE}
- Stripe secret key:    $(mask_secret "$STRIPE_SECRET_KEY")
- Stripe publishable:   $(mask_secret "$STRIPE_PUBLISHABLE_KEY")
- Stripe webhook:       $(mask_secret "$STRIPE_WEBHOOK_SECRET")
- Stripe Pro monthly:   ${STRIPE_PRICE_ID_PRO_MONTHLY:-unset}
- Stripe portal return: ${STRIPE_BILLING_PORTAL_RETURN_URL:-unset}
- Profile file:         ${PROFILE_FILE}

CONFIG
}

save_profile_file() {
  cat >"$PROFILE_FILE" <<PROFILE
# Auto-generated by ThorpeWorkforceLaunchAssistant.command
# Update values as needed.

export THORPE_REPO_PATH="$REPO_PATH"
export THORPE_ENVIRONMENT="$DEFAULT_ENVIRONMENT"
export THORPE_SUPPORT_EMAIL="$SUPPORT_EMAIL"
export THORPE_FRONTEND_URL="$PROD_FRONTEND_URL"
export THORPE_API_URL="$PROD_API_URL"
export THORPE_STAGING_FRONTEND_URL="$STAGING_FRONTEND_URL"
export THORPE_STAGING_API_URL="$STAGING_API_URL"
export THORPE_RAILWAY_DASHBOARD_URL="$RAILWAY_DASHBOARD_URL"
export THORPE_VERCEL_DASHBOARD_URL="$VERCEL_DASHBOARD_URL"
export THORPE_STRIPE_DASHBOARD_URL="$STRIPE_DASHBOARD_URL"
export THORPE_GITHUB_REPO_URL="$GITHUB_REPO_URL"
export THORPE_IONOS_ZONE_DOMAIN="$IONOS_ZONE_DOMAIN"
export THORPE_RAILWAY_API_CNAME_TARGET="$RAILWAY_API_CNAME_TARGET"
export THORPE_RAILWAY_STAGING_API_CNAME_TARGET="$RAILWAY_STAGING_API_CNAME_TARGET"
export THORPE_VERCEL_CNAME_TARGET="$VERCEL_CNAME_TARGET"
export THORPE_VERCEL_APEX_A_TARGET="$VERCEL_APEX_A_TARGET"
export THORPE_DNS_DEFAULT_TTL="$DNS_DEFAULT_TTL"
export THORPE_STRIPE_MODE="$STRIPE_MODE"
export THORPE_STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY"
export THORPE_STRIPE_PUBLISHABLE_KEY="$STRIPE_PUBLISHABLE_KEY"
export THORPE_STRIPE_WEBHOOK_SECRET="$STRIPE_WEBHOOK_SECRET"
export THORPE_STRIPE_PRICE_ID_PRO_MONTHLY="$STRIPE_PRICE_ID_PRO_MONTHLY"
export THORPE_STRIPE_PRICE_ID_PRO_ANNUAL="$STRIPE_PRICE_ID_PRO_ANNUAL"
export THORPE_STRIPE_PRICE_ID_CREATOR_MONTHLY="$STRIPE_PRICE_ID_CREATOR_MONTHLY"
export THORPE_STRIPE_PRICE_ID_CREATOR_ANNUAL="$STRIPE_PRICE_ID_CREATOR_ANNUAL"
export THORPE_STRIPE_PRICE_ID_ENTERPRISE_MONTHLY="$STRIPE_PRICE_ID_ENTERPRISE_MONTHLY"
export THORPE_STRIPE_BILLING_PORTAL_RETURN_URL="$STRIPE_BILLING_PORTAL_RETURN_URL"
PROFILE
  ok "Saved profile: $PROFILE_FILE"
}

build_stripe_backend_env_block() {
  local portal_url="$STRIPE_BILLING_PORTAL_RETURN_URL"
  if [[ -z "$portal_url" ]]; then
    portal_url="$(normalize_url "$PROD_FRONTEND_URL")/app/settings/billing"
  fi
  cat <<EOF
BILLING_PROVIDER=stripe
STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY:-REPLACE_WITH_SK_${STRIPE_MODE}}
STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY:-REPLACE_WITH_PK_${STRIPE_MODE}}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-REPLACE_WITH_WHSEC_${STRIPE_MODE}}
STRIPE_PRICE_ID_PRO_MONTHLY=${STRIPE_PRICE_ID_PRO_MONTHLY:-REPLACE_WITH_PRICE_ID}
STRIPE_PRICE_ID_PRO_ANNUAL=${STRIPE_PRICE_ID_PRO_ANNUAL:-REPLACE_WITH_PRICE_ID}
STRIPE_PRICE_ID_CREATOR_MONTHLY=${STRIPE_PRICE_ID_CREATOR_MONTHLY:-REPLACE_WITH_PRICE_ID}
STRIPE_PRICE_ID_CREATOR_ANNUAL=${STRIPE_PRICE_ID_CREATOR_ANNUAL:-REPLACE_WITH_PRICE_ID}
STRIPE_PRICE_ID_ENTERPRISE_MONTHLY=${STRIPE_PRICE_ID_ENTERPRISE_MONTHLY:-REPLACE_WITH_PRICE_ID}
STRIPE_BILLING_PORTAL_RETURN_URL=${portal_url}
EOF
}

build_stripe_frontend_env_block() {
  cat <<EOF
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY:-REPLACE_WITH_PK_${STRIPE_MODE}}
EOF
}

print_stripe_env_blocks() {
  say ""
  say "Stripe backend env vars (Railway API service):"
  say "-----------------------------------------------"
  build_stripe_backend_env_block
  say ""
  say "Stripe frontend env vars (Vercel):"
  say "-----------------------------------"
  build_stripe_frontend_env_block
  say ""
  warn "Keep Stripe keys secret; do not commit env files."
}

save_stripe_env_files() {
  assert_repo
  local output_dir="$REPO_PATH/.launch-assistant-output"
  mkdir -p "$output_dir"
  build_stripe_backend_env_block >"$output_dir/stripe-backend.env"
  build_stripe_frontend_env_block >"$output_dir/stripe-frontend.env"
  cat >"$output_dir/stripe-webhook-events.txt" <<'EVENTS'
checkout.session.completed
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
invoice.paid
invoice.payment_failed
payment_intent.succeeded
EVENTS
  ok "Saved:"
  ok "  $output_dir/stripe-backend.env"
  ok "  $output_dir/stripe-frontend.env"
  ok "  $output_dir/stripe-webhook-events.txt"
}

print_stripe_connect_guide() {
  local api_url webhook_url
  api_url="$(normalize_url "$PROD_API_URL")"
  webhook_url="${api_url}/billing/webhooks/stripe"
  step "Stripe connection guide (${STRIPE_MODE} mode)"
  cat <<GUIDE
1) In Stripe Dashboard, switch to the ${STRIPE_MODE} workspace/mode.
2) Copy API keys:
   - Secret key (sk_...)
   - Publishable key (pk_...)
3) Create or identify prices used by Thorpe Workforce plans:
   - Pro monthly
   - Pro annual
   - Creator monthly
   - Creator annual
   - Enterprise monthly
4) In Stripe Webhooks, add endpoint:
   ${webhook_url}
5) Subscribe endpoint to these events:
   - checkout.session.completed
   - customer.subscription.created
   - customer.subscription.updated
   - customer.subscription.deleted
   - invoice.paid
   - invoice.payment_failed
   - payment_intent.succeeded
6) Copy the webhook signing secret (whsec_...).
7) Use menu option 15 (or 16) to generate env vars and paste:
   - Railway API service: stripe-backend.env values
   - Vercel project: stripe-frontend.env values
8) Redeploy backend + frontend, then test:
   - GET ${api_url}/billing/plans
   - In app: Settings > Billing checkout flow
   - Billing webhook delivery succeeds in Stripe logs
GUIDE
  say ""
  warn "Use test keys in staging and live keys only in production."
}

build_ionos_dns_records() {
  local mode="${1:-production}"
  local frontend_url="$PROD_FRONTEND_URL"
  local api_url="$PROD_API_URL"
  local api_target="$RAILWAY_API_CNAME_TARGET"
  local zone="$IONOS_ZONE_DOMAIN"
  local frontend_host api_host frontend_label api_label

  if [[ "$mode" == "staging" ]]; then
    frontend_url="$STAGING_FRONTEND_URL"
    api_url="$STAGING_API_URL"
    api_target="$RAILWAY_STAGING_API_CNAME_TARGET"
  fi

  frontend_host="$(host_from_url "$frontend_url")"
  api_host="$(host_from_url "$api_url")"
  if [[ -z "$zone" ]]; then
    zone="$frontend_host"
  fi
  frontend_label="$(dns_label_for_host "$frontend_host" "$zone")"
  api_label="$(dns_label_for_host "$api_host" "$zone")"

  if [[ "$frontend_label" == "@" ]]; then
    printf "%s|%s|%s|%s|%s\n" "@" "A" "$VERCEL_APEX_A_TARGET" "$DNS_DEFAULT_TTL" "${mode} frontend apex -> Vercel"
    printf "%s|%s|%s|%s|%s\n" "www" "CNAME" "$VERCEL_CNAME_TARGET" "$DNS_DEFAULT_TTL" "${mode} frontend www alias -> Vercel"
  else
    printf "%s|%s|%s|%s|%s\n" "$frontend_label" "CNAME" "$VERCEL_CNAME_TARGET" "$DNS_DEFAULT_TTL" "${mode} frontend host -> Vercel"
  fi

  printf "%s|%s|%s|%s|%s\n" "$api_label" "CNAME" "$api_target" "$DNS_DEFAULT_TTL" "${mode} api host -> Railway"
}

print_ionos_dns_record_table() {
  local mode="$1"
  local zone="$IONOS_ZONE_DOMAIN"
  if [[ -z "$zone" ]]; then
    zone="$(host_from_url "$PROD_FRONTEND_URL")"
  fi
  say ""
  say "${mode^} DNS records (IONOS zone: ${zone})"
  say "---------------------------------------------"
  printf "%-16s %-8s %-58s %-6s %s\n" "Name" "Type" "Value" "TTL" "Purpose"
  while IFS='|' read -r name type value ttl note; do
    printf "%-16s %-8s %-58s %-6s %s\n" "$name" "$type" "$value" "$ttl" "$note"
  done < <(build_ionos_dns_records "$mode")
}

print_ionos_dns_setup_plan() {
  step "IONOS DNS setup plan"
  say "1) Open IONOS: Domains & SSL -> your domain -> DNS"
  say "2) Add/update the records below (replace Railway targets if still placeholders)."
  say "3) Remove conflicting records for same host/type where needed."
  say "4) Save changes, then run menu option 15 to check DNS propagation."
  print_ionos_dns_record_table "production"
  print_ionos_dns_record_table "staging"
  say ""
  warn "For custom Vercel DNS, adjust VERCEL_CNAME_TARGET / VERCEL_APEX_A_TARGET in profile if needed."
}

save_ionos_dns_plan_file() {
  assert_repo
  local output_dir="$REPO_PATH/.launch-assistant-output"
  local output_file="$output_dir/ionos-dns-records.txt"
  mkdir -p "$output_dir"
  {
    echo "Thorpe Workforce IONOS DNS plan"
    echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo
    echo "Production records"
    echo "Name|Type|Value|TTL|Purpose"
    build_ionos_dns_records "production"
    echo
    echo "Staging records"
    echo "Name|Type|Value|TTL|Purpose"
    build_ionos_dns_records "staging"
  } >"$output_file"
  ok "Saved DNS plan: $output_file"
}

check_dns_resolution() {
  local host="$1"
  local result=""
  if [[ -z "$host" ]]; then
    return 0
  fi
  if command -v dig >/dev/null 2>&1; then
    result="$(dig +short "$host" | tr '\n' ' ' | sed 's/[[:space:]]\+$//')"
  elif command -v nslookup >/dev/null 2>&1; then
    result="$(nslookup "$host" 2>/dev/null | awk '/^Address: / {print $2}' | tr '\n' ' ' | sed 's/[[:space:]]\+$//')"
  fi

  if [[ -n "$result" ]]; then
    ok "DNS ${host} -> ${result}"
  else
    warn "DNS unresolved or no local resolver output for: ${host}"
  fi
}

run_dns_quick_checks() {
  step "DNS quick checks"
  check_dns_resolution "$(host_from_url "$PROD_FRONTEND_URL")"
  check_dns_resolution "$(host_from_url "$PROD_API_URL")"
  check_dns_resolution "$(host_from_url "$STAGING_FRONTEND_URL")"
  check_dns_resolution "$(host_from_url "$STAGING_API_URL")"
  say ""
  warn "If DNS was updated recently, propagation can take several minutes."
}

build_env_block_railway_api() {
  local frontend_url api_url api_host
  frontend_url="$(normalize_url "$PROD_FRONTEND_URL")"
  api_url="$(normalize_url "$PROD_API_URL")"
  api_host="$(host_from_url "$api_url")"
  cat <<EOF
ENVIRONMENT=${DEFAULT_ENVIRONMENT}
SECRET_KEY=REPLACE_WITH_LONG_RANDOM_SECRET
DATABASE_URL=REPLACE_WITH_RAILWAY_POSTGRES_URL
REDIS_URL=REPLACE_WITH_RAILWAY_REDIS_URL
APP_BASE_URL=${frontend_url}
SUPPORT_EMAIL=${SUPPORT_EMAIL}
CORS_ORIGINS=${frontend_url}
TRUSTED_HOSTS=${api_host},*.up.railway.app
BILLING_PROVIDER=placeholder
EMAIL_PROVIDER=mock
AI_PROVIDER=mock
RUN_MIGRATIONS_ON_BOOT=false
PASSWORD_RESET_TOKEN_TTL_MINUTES=30
EOF
}

build_env_block_railway_worker() {
  local frontend_url
  frontend_url="$(normalize_url "$PROD_FRONTEND_URL")"
  cat <<EOF
ENVIRONMENT=${DEFAULT_ENVIRONMENT}
SECRET_KEY=REPLACE_WITH_LONG_RANDOM_SECRET
DATABASE_URL=REPLACE_WITH_RAILWAY_POSTGRES_URL
REDIS_URL=REPLACE_WITH_RAILWAY_REDIS_URL
APP_BASE_URL=${frontend_url}
SUPPORT_EMAIL=${SUPPORT_EMAIL}
BILLING_PROVIDER=placeholder
EMAIL_PROVIDER=mock
AI_PROVIDER=mock
RUN_MIGRATIONS=false
SEED_WORKER_SYSTEM=false
SEED_DEMO_DATA=false
SEED_FOUNDER_OS_CHAINS=false
EOF
}

build_env_block_vercel() {
  local frontend_url api_url
  frontend_url="$(normalize_url "$PROD_FRONTEND_URL")"
  api_url="$(normalize_url "$PROD_API_URL")"
  cat <<EOF
NEXT_PUBLIC_API_BASE_URL=${api_url}
NEXT_PUBLIC_APP_URL=${frontend_url}
NEXT_PUBLIC_INTERNAL_WORKER_BUILDER_ENABLED=true
NEXT_PUBLIC_WORKER_CREATOR_ENABLED=true
EOF
}

print_deployment_env_blocks() {
  say ""
  say "Railway API service env vars:"
  say "-----------------------------"
  build_env_block_railway_api
  say ""
  say "Railway Worker service env vars:"
  say "--------------------------------"
  build_env_block_railway_worker
  say ""
  say "Vercel frontend env vars:"
  say "-------------------------"
  build_env_block_vercel
  say ""
  warn "Optional Stripe/SendGrid blocks are in README/DEPLOYMENT docs."
}

save_deployment_env_files() {
  assert_repo
  local output_dir="$REPO_PATH/.launch-assistant-output"
  mkdir -p "$output_dir"
  build_env_block_railway_api >"$output_dir/railway-api.env"
  build_env_block_railway_worker >"$output_dir/railway-worker.env"
  build_env_block_vercel >"$output_dir/vercel.env"
  ok "Saved:"
  ok "  $output_dir/railway-api.env"
  ok "  $output_dir/railway-worker.env"
  ok "  $output_dir/vercel.env"
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
7) Print deployment env var blocks
8) Save deployment env var files
9) Start local stack (docker compose)
10) Run production smoke checks
11) Run staging smoke checks
12) Open Railway/Vercel/Stripe dashboards
13) Configure Stripe settings
14) Print Stripe connection guide
15) Print Stripe env var blocks
16) Save Stripe env var files
17) Print IONOS DNS setup plan
18) Save IONOS DNS plan to file
19) Run DNS quick checks
20) Print manual launch checklist
21) Exit

MENU
    read -r -p "Choose an option [1-21]: " option
    case "$option" in
      1) prompt_repo_path; assert_repo ;;
      2) show_current_config ;;
      3) configure_domain_defaults ;;
      4) assert_repo && run_preflight ;;
      5) assert_repo && copy_env_templates ;;
      6) save_profile_file ;;
      7) print_deployment_env_blocks ;;
      8) save_deployment_env_files ;;
      9) assert_repo && start_local_stack ;;
      10) smoke_check_deployed_urls "production" ;;
      11) smoke_check_deployed_urls "staging" ;;
      12) open_platform_dashboards ;;
      13) configure_stripe_settings ;;
      14) print_stripe_connect_guide ;;
      15) print_stripe_env_blocks ;;
      16) save_stripe_env_files ;;
      17) print_ionos_dns_setup_plan ;;
      18) save_ionos_dns_plan_file ;;
      19) run_dns_quick_checks ;;
      20) print_manual_launch_checklist ;;
      21) exit 0 ;;
      *) warn "Invalid option. Choose 1-21." ;;
    esac
  done
}

say "${CYAN}Thorpe Workforce macOS Launch Assistant${NC}"
show_current_config
prompt_repo_path
assert_repo
menu
