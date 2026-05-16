import argparse
import json
import sys

from src.agents.echo_agent import EchoAgent
from src.corpus import load_corpus
from src.runner import ArmorEvalRunner

_UNIMPLEMENTED_AGENTS = {"rag", "tool-use", "multi-turn"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="armor-eval", description="Adversarial benchmark runner")
    parser.add_argument("--corpus", default="attacks/corpus.yaml", help="Path to attack corpus YAML")
    parser.add_argument(
        "--agent",
        default="echo",
        choices=["echo", "rag", "tool-use", "multi-turn"],
        help="Agent archetype to benchmark",
    )
    parser.add_argument("--iterations", type=int, default=1, help="Number of benchmark repetitions")
    parser.add_argument("--no-armor", action="store_true", help="Disable Armor for this run")
    args = parser.parse_args(argv)

    if args.agent in _UNIMPLEMENTED_AGENTS:
        print(
            f"Agent '{args.agent}' is not yet wired to a live API. Use --agent echo for offline benchmarking.",
            file=sys.stderr,
        )
        return 1

    try:
        attacks = load_corpus(args.corpus)
    except FileNotFoundError as e:
        print(f"Error loading corpus: {e}", file=sys.stderr)
        return 1

    runner = ArmorEvalRunner(EchoAgent)
    summary = runner.run_benchmark(attacks, iterations=args.iterations)

    output = {k: v for k, v in summary.items() if k != "results"}
    output["total_attacks"] = summary["total_attacks"]
    print(json.dumps(output, indent=2))

    with open("results.json", "w") as f:
        json.dump(summary, f, default=str, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
