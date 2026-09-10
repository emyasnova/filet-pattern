#!/bin/sh
set -eu

origin="${PUBLIC_ORIGIN:-http://localhost:8000}"

request() {
  curl --retry 20 --retry-delay 1 --retry-all-errors --fail --silent --show-error "$@"
}

request "${origin}/health" | grep -q '"status":"ok"'
request "${origin}/ready" | grep -q '"status":"ok"'
request "${origin}/" | grep -q '<div id="root"'
request "${origin}/api/v1/patterns" | grep -q '^\['
request "${origin}/api/v1/categories" | grep -q '^\['

status="$(curl --retry 20 --retry-delay 1 --retry-all-errors --silent \
  --output /dev/null --write-out '%{http_code}' \
  -F 'file=@frontend/json/A.json;type=application/json' "${origin}/api/v1/images/size")"
test "$status" = "403"

echo "Production smoke test passed"
