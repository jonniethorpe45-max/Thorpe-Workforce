#!/usr/bin/env bash
set -euo pipefail

exec celery -A app.tasks.celery_app.celery_app worker -l "${CELERY_LOG_LEVEL:-info}"
