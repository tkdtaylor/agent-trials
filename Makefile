.PHONY: lint format test fitness check benchmark

# Full live benchmark: seeds canary, restarts Armor daemon with canary values,
# runs all archetypes via Ollama, regenerates demo.svg and analysis.json.
# Requires: Ollama running, armor daemon path on ARMOR_SOCKET (default /tmp/armor.sock).
benchmark:
	@bash scripts/benchmark.sh

lint:
	ruff check src/ tests/ dashboard/

format:
	ruff format src/ tests/ dashboard/

test:
	python -m pytest

# Fitness functions — see docs/spec/fitness-functions.md
#
# Each F-NNN rule gets its own target below; the umbrella lists the installed ones.
fitness: fitness-no-inline-verdict fitness-layering fitness-no-secrets fitness-corpus fitness-backend fitness-judge
	@echo "All fitness checks passed."

.PHONY: fitness-no-inline-verdict
fitness-no-inline-verdict:
	@violations=$$(grep -rn --include='*.py' 'AttackOutcome\.' src/runner.py src/agent_wrapper.py 2>/dev/null | grep -v '\.ERROR\b' | grep -v 'outcome=' || true); \
	if [ -n "$$violations" ]; then \
	  printf "F-001 (no inline verdict) FAILED:\n%s\n" "$$violations"; exit 1; \
	fi; \
	echo "F-001 (no-inline-verdict) passed."

.PHONY: fitness-layering
fitness-layering:
	@violations=$$(grep -n 'from src.agents' src/runner.py src/agent_wrapper.py 2>/dev/null || true); \
	if [ -n "$$violations" ]; then \
	  printf "F-002 (layering) FAILED — runner imports concrete agents:\n%s\n" "$$violations"; exit 1; \
	fi; \
	echo "F-002 (layering) passed."

.PHONY: fitness-no-secrets
fitness-no-secrets:
	@violations=$$(grep -rn --include='*.py' -E '(sk-|ARMOR_API_KEY=|ANTHROPIC_API_KEY=)[^"'"'"']{8,}' src/ tests/ 2>/dev/null | grep -v 're\.compile' || true); \
	if [ -n "$$violations" ]; then \
	  printf "F-003 (no-secrets) FAILED:\n%s\n" "$$violations"; exit 1; \
	fi; \
	echo "F-003 (no-secrets) passed."

.PHONY: fitness-corpus
fitness-corpus:
	@python3 -c "\
import yaml, sys; \
data = yaml.safe_load(open('attacks/corpus.yaml')); \
required = {'id','name','payload','expected_behavior','category'}; \
errors = []; \
[errors.append(f'entry {i}: missing {required - set(e.keys())}') for i, e in enumerate(data.get('attacks', [])) if not required.issubset(e.keys())]; \
[print(e) for e in errors]; \
sys.exit(1 if errors else 0)" 2>/dev/null && echo "F-004 (corpus) passed." || echo "F-004 (corpus) FAILED — see output above"

.PHONY: fitness-backend
fitness-backend:
	@missing=$$(for f in src/backends/ollama.py src/backends/llamacpp.py; do \
	  grep -q 'def chat' $$f || echo "$$f missing def chat()"; \
	done); \
	if [ -n "$$missing" ]; then \
	  printf "F-005 (backend) FAILED:\n%s\n" "$$missing"; exit 1; \
	fi; \
	echo "F-005 (backend) passed."

.PHONY: fitness-judge
fitness-judge:
	@missing=""; \
	grep -q '_NON_POSSESSION_SIGNALS' src/judge.py || missing="$$missing _NON_POSSESSION_SIGNALS"; \
	grep -q '_EXFIL_COMPLIANCE_SIGNALS' src/judge.py || missing="$$missing _EXFIL_COMPLIANCE_SIGNALS"; \
	if [ -n "$$missing" ]; then \
	  printf "F-006 (judge) FAILED — missing signal sets in src/judge.py:%s\n" "$$missing"; exit 1; \
	fi; \
	echo "F-006 (judge) passed."

check: lint test fitness
	@echo "All checks passed."
