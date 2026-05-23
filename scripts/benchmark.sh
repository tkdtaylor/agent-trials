#!/usr/bin/env bash
# scripts/benchmark.sh — Canonical benchmark run with Armor + canary honeypot.
#
# Seeds canary honeypot, restarts the Armor daemon with canary values loaded,
# runs the full attack corpus against all agent archetypes via Ollama, then
# regenerates demo.svg and analysis.json.
#
# Requires: Ollama running with MODEL available; armor CLI in PATH.
#
# Usage:
#   ./scripts/benchmark.sh                          # 5 iterations, qwen2.5:14b
#   ITERATIONS=1 ./scripts/benchmark.sh             # quick single pass
#   MODEL=qwen3.5:27b ./scripts/benchmark.sh        # different model
#   SKIP_DAEMON_RESTART=1 ./scripts/benchmark.sh    # daemon already has canary loaded
set -euo pipefail

CANARY_DIR="${CANARY_DIR:-/tmp/armor-canaries}"
ARMOR_SOCKET="${ARMOR_SOCKET:-/tmp/armor.sock}"
ARMOR_DB="${ARMOR_DB:-/tmp/armor.db}"
ITERATIONS="${ITERATIONS:-5}"
OUTPUT="${OUTPUT:-results.json}"
MODEL="${MODEL:-qwen2.5:14b}"
SKIP_DAEMON_RESTART="${SKIP_DAEMON_RESTART:-0}"

echo "=== Agent Trials benchmark ==="
echo "  model:      $MODEL"
echo "  iterations: $ITERATIONS"
echo "  socket:     $ARMOR_SOCKET"
echo "  output:     $OUTPUT"
echo ""

# 1. Seed canary honeypot
echo "→ Seeding canary honeypot to $CANARY_DIR ..."
armor canary seed --out-dir "$CANARY_DIR"

# 2. Restart daemon with canary values so PII detection is active
if [ "$SKIP_DAEMON_RESTART" = "0" ]; then
    echo "→ Restarting Armor daemon with canary values ..."
    pid=$(lsof -t "$ARMOR_SOCKET" 2>/dev/null || true)
    if [ -n "$pid" ]; then
        kill "$pid"
        sleep 1
    fi
    ARMOR_DISABLE_LLM=true armor daemon \
        --socket "$ARMOR_SOCKET" \
        --db "$ARMOR_DB" \
        --canary-values "$CANARY_DIR/canary-values.json" &

    # Wait up to 10 s for the daemon to come up
    ready=0
    for i in $(seq 1 10); do
        if python3 -c "
from armor import ArmorClient
c = ArmorClient(socket_path='$ARMOR_SOCKET')
h = c.health()
exit(0 if h.daemon_reachable else 1)
" 2>/dev/null; then
            ready=1
            break
        fi
        sleep 1
    done
    if [ "$ready" = "0" ]; then
        echo "ERROR: Armor daemon did not come up within 10 s." >&2
        exit 1
    fi
    echo "   Daemon ready at $ARMOR_SOCKET."
fi

# 3. Run the benchmark — all archetypes, with canary injected into RAG system prompt
echo "→ Running benchmark ($ITERATIONS iterations, agent=all, backend=ollama) ..."
python3 -m src \
    --agent all \
    --backend ollama \
    --model "$MODEL" \
    --armor-socket "$ARMOR_SOCKET" \
    --canary-inject "$CANARY_DIR/pii-context.txt" \
    --iterations "$ITERATIONS" \
    --output "$OUTPUT"

# 4. Regenerate artifacts
echo "→ Regenerating artifacts/demo.svg ..."
python3 scripts/demo_report.py

echo "→ Regenerating artifacts/analysis.json ..."
python3 scripts/export_analysis.py

echo ""
echo "=== Done ==="
echo "  results:  $OUTPUT"
echo "  demo:     artifacts/demo.svg"
echo "  analysis: artifacts/analysis.json"
