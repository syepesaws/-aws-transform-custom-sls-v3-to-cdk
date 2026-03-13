#!/usr/bin/env bash
# Run ATX transformation on each repo in config.yaml, capture telemetry, write per-repo JSON results.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$PROJECT_DIR/benchmark-results"
CONFIG="$PROJECT_DIR/config.yaml"
WORK_DIR="$PROJECT_DIR/.workdir"

# Require yq and jq
for cmd in yq jq git atx; do
  command -v "$cmd" >/dev/null || { echo "Error: $cmd not found"; exit 1; }
done

[ -f "$CONFIG" ] || { echo "Error: $CONFIG not found. Run scrape_repos.py first."; exit 1; }

TRANSFORMATION=$(yq -r '.transformation_name' "$CONFIG")
BUILD_CMD=$(yq -r '.build_command // "npx cdk synth"' "$CONFIG")
REPO_COUNT=$(yq -r '.repos | length' "$CONFIG")

mkdir -p "$RESULTS_DIR" "$WORK_DIR"

echo "=== ATX Benchmark: $TRANSFORMATION ==="
echo "Repos: $REPO_COUNT | Build: $BUILD_CMD"
echo ""

for i in $(seq 0 $((REPO_COUNT - 1))); do
  REPO_URL=$(yq -r ".repos[$i].url" "$CONFIG")
  REPO_NAME=$(yq -r ".repos[$i].name" "$CONFIG")
  REPO_DIR="$WORK_DIR/$REPO_NAME"
  RESULT_FILE="$RESULTS_DIR/${REPO_NAME}.json"

  echo "--- [$((i+1))/$REPO_COUNT] $REPO_NAME ---"

  # Clone
  if [ -d "$REPO_DIR" ]; then
    echo "  Using cached clone"
  else
    git clone --depth 1 "$REPO_URL" "$REPO_DIR" 2>/dev/null
  fi

  # Run ATX (non-interactive, trust all tools)
  ATX_LOG="$RESULTS_DIR/${REPO_NAME}_atx.log"
  START_TS=$(date +%s)

  atx custom def exec \
    -n "$TRANSFORMATION" \
    -p "$REPO_DIR" \
    -c "$BUILD_CMD" \
    -x -t 2>&1 | tee "$ATX_LOG"

  ATX_EXIT=$?
  END_TS=$(date +%s)
  DURATION=$(( END_TS - START_TS ))

  # Extract agent minutes from ATX output (last line pattern: "Agent minutes used: X.XX")
  AGENT_MINUTES=$(grep -oE 'Agent minutes used: [0-9.]+' "$ATX_LOG" | tail -1 | grep -oE '[0-9.]+' || echo "N/A")

  # Extract conversation ID for knowledge item lookup
  CONV_ID=$(grep -oE 'conversation-id [a-f0-9-]+' "$ATX_LOG" | tail -1 | awk '{print $2}' || echo "")

  # Check build result
  BUILD_STATUS="skipped"
  if [ -d "$REPO_DIR" ]; then
    cd "$REPO_DIR"
    if eval "$BUILD_CMD" > "$RESULTS_DIR/${REPO_NAME}_build.log" 2>&1; then
      BUILD_STATUS="pass"
    else
      BUILD_STATUS="fail"
    fi
    cd "$PROJECT_DIR"
  fi

  # Count knowledge items if conversation ID available
  KI_COUNT="N/A"
  if [ -n "$CONV_ID" ]; then
    KI_COUNT=$(atx custom def list-ki -n "$TRANSFORMATION" --json 2>/dev/null | jq 'length' || echo "N/A")
  fi

  # Write result JSON
  jq -n \
    --arg name "$REPO_NAME" \
    --arg url "$REPO_URL" \
    --arg status "$([ $ATX_EXIT -eq 0 ] && echo success || echo failure)" \
    --arg build "$BUILD_STATUS" \
    --arg duration "$DURATION" \
    --arg agent_min "$AGENT_MINUTES" \
    --arg ki "$KI_COUNT" \
    --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{
      repo: $name,
      url: $url,
      transformation_status: $status,
      build_status: $build,
      duration_seconds: ($duration | tonumber),
      agent_minutes: $agent_min,
      knowledge_items: $ki,
      timestamp: $timestamp
    }' > "$RESULT_FILE"

  echo "  Status: $([ $ATX_EXIT -eq 0 ] && echo ✅ || echo ❌) | Build: $BUILD_STATUS | Time: ${DURATION}s | Agent min: $AGENT_MINUTES"
  echo ""
done

echo "=== Done. Results in $RESULTS_DIR ==="
