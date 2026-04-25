#!/usr/bin/env bash
# T13.128 — staging smoke checker.
#
# Curls every top-level route on the staging frontend + backend and
# asserts the documented expected HTTP status. Idempotent.
#
# Usage:
#   STAGING_FRONTEND_URL=https://staging.example STAGING_API_URL=https://api.staging.example \
#       scripts/staging-smoke.sh
# OR (positional):
#   scripts/staging-smoke.sh <frontend-url> <api-url>
#
# Exits non-zero if ANY route returns an unexpected status. Stdout is a
# tab-separated table: STATUS  METHOD  EXPECTED  ACTUAL  URL.
#
# This script intentionally has no dependencies beyond curl + bash 4.

set -u
set -o pipefail

FRONTEND_URL="${1:-${STAGING_FRONTEND_URL:-}}"
API_URL="${2:-${STAGING_API_URL:-${STAGING_BACKEND_URL:-}}}"

if [[ -z "${FRONTEND_URL}" || -z "${API_URL}" ]]; then
    echo "ERROR: STAGING_FRONTEND_URL and STAGING_API_URL must be set," >&2
    echo "       or passed as the first two positional arguments." >&2
    echo "" >&2
    echo "Usage: $0 <frontend-url> <api-url>" >&2
    exit 2
fi

# Strip trailing slashes so URL building is unambiguous.
FRONTEND_URL="${FRONTEND_URL%/}"
API_URL="${API_URL%/}"

# Per-request timeout. Fly.io cold-starts a stopped machine on first
# hit, so allow a generous connect timeout.
CURL_CONNECT_TIMEOUT=10
CURL_MAX_TIME=30

declare -i FAIL_COUNT=0
declare -i CHECK_COUNT=0

# Tab-separated header.
printf 'RESULT\tMETHOD\tEXPECTED\tACTUAL\tURL\n'

# check_either <method> <expected1> <expected2> <url>
# PASS if actual matches either expected status. Use when a route has
# legitimate alternate codes (e.g. /health/ready returning 503 when a
# dep is intentionally not loaded).
check_either() {
    local method="$1"
    local expected1="$2"
    local expected2="$3"
    local url="$4"
    CHECK_COUNT+=1
    local actual
    actual=$(
        curl -s -o /dev/null \
            --connect-timeout "${CURL_CONNECT_TIMEOUT}" \
            --max-time "${CURL_MAX_TIME}" \
            -w '%{http_code}' \
            -X "${method}" \
            "${url}" 2>/dev/null
    ) || true
    [[ -z "${actual}" ]] && actual="000"
    local result="PASS"
    if [[ "${actual}" != "${expected1}" && "${actual}" != "${expected2}" ]]; then
        result="FAIL"
        FAIL_COUNT+=1
    fi
    printf '%s\t%s\t%s|%s\t%s\t%s\n' "${result}" "${method}" "${expected1}" "${expected2}" "${actual}" "${url}"
}

# check <method> <expected-status> <url>
check() {
    local method="$1"
    local expected="$2"
    local url="$3"
    CHECK_COUNT+=1
    local actual
    # curl always writes %{http_code} to stdout — even on connect
    # failure (where it writes 000). Suppress the non-zero exit so we
    # don't append a fallback string to the captured code.
    actual=$(
        curl -s -o /dev/null \
            --connect-timeout "${CURL_CONNECT_TIMEOUT}" \
            --max-time "${CURL_MAX_TIME}" \
            -w '%{http_code}' \
            -X "${method}" \
            "${url}" 2>/dev/null
    ) || true
    [[ -z "${actual}" ]] && actual="000"
    local result="PASS"
    if [[ "${actual}" != "${expected}" ]]; then
        result="FAIL"
        FAIL_COUNT+=1
    fi
    printf '%s\t%s\t%s\t%s\t%s\n' "${result}" "${method}" "${expected}" "${actual}" "${url}"
}

# --- Backend health + root ---
check GET 200 "${API_URL}/"
check GET 200 "${API_URL}/health"
check GET 200 "${API_URL}/health/live"
# /health/ready returns 503 when sub-checks fail (e.g. RAG index not loaded).
# Smoke only asserts the route is alive, not that every dep is up — the
# component QC suites cover dep-up assertions.
check_either GET 200 503 "${API_URL}/health/ready"

# --- Backend public GET endpoints (no auth needed) ---
check GET 200 "${API_URL}/api/city"
check GET 200 "${API_URL}/api/jobs/"
check GET 200 "${API_URL}/api/dashboard/stats"
check GET 200 "${API_URL}/api/outcomes/aggregate"

# --- Backend admin endpoints — expect 401/403/422 without admin key.
# We assert the route is wired (not 404) by accepting any auth-rejection
# code. admin_flags only registers POST /{name}, so probe a POST.
admin_check() {
    local method="$1"
    local url="$2"
    CHECK_COUNT+=1
    local actual
    actual=$(
        curl -s -o /dev/null \
            --connect-timeout "${CURL_CONNECT_TIMEOUT}" \
            --max-time "${CURL_MAX_TIME}" \
            -w '%{http_code}' \
            -X "${method}" \
            "${url}" 2>/dev/null
    ) || true
    [[ -z "${actual}" ]] && actual="000"
    local result="PASS"
    case "${actual}" in
        401|403|422) ;;
        *) result="FAIL"; FAIL_COUNT+=1 ;;
    esac
    printf '%s\t%s\t%s\t%s\t%s\n' "${result}" "${method}" "401|403|422" "${actual}" "${url}"
}
admin_check POST "${API_URL}/api/admin/flags/_smoke"

# --- Frontend top-level pages (Next.js SSR returns 200 for the shell) ---
# Note: /documents has no parent page — NavBar links directly to
# /documents/resume. /feedback is token-gated (only /feedback/<token>
# is a real route); not part of the public smoke surface.
check GET 200 "${FRONTEND_URL}/"
check GET 200 "${FRONTEND_URL}/assess"
check GET 200 "${FRONTEND_URL}/daily"
check GET 200 "${FRONTEND_URL}/plan"
check GET 200 "${FRONTEND_URL}/jobs"
check GET 200 "${FRONTEND_URL}/documents/resume"
check GET 200 "${FRONTEND_URL}/documents/cover-letters"
check GET 200 "${FRONTEND_URL}/appointments"
check GET 200 "${FRONTEND_URL}/credit"
check GET 200 "${FRONTEND_URL}/case-manager"

# --- Summary ---
echo ""
if (( FAIL_COUNT == 0 )); then
    printf 'staging-smoke: PASS  (%d/%d checks)\n' "${CHECK_COUNT}" "${CHECK_COUNT}"
    exit 0
fi
printf 'staging-smoke: FAIL  (%d/%d checks failed)\n' "${FAIL_COUNT}" "${CHECK_COUNT}" >&2
exit 1
