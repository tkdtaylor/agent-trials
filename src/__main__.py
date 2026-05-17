import argparse
import json
import sys

from src.agents.echo_agent import EchoAgent
from src.corpus import load_corpus
from src.runner import ArmorEvalRunner


def _build_backend(args):
    if args.backend == "ollama":
        from src.backends.ollama import OllamaBackend

        return OllamaBackend(model=args.model)
    if args.backend == "llamacpp":
        from src.backends.llamacpp import LlamaCppBackend

        return LlamaCppBackend(model_path=args.model_path)
    return None


def _build_agent_factory(args, backend):
    if args.agent == "echo":
        return EchoAgent
    if args.agent == "rag":
        from src.agents.rag_agent import RAGAgent
        from src.backends.adapters import rag_generate, rag_retrieve

        retrieve = rag_retrieve([])
        generate = rag_generate(backend)
        return lambda: RAGAgent(retrieve=retrieve, generate=generate)
    if args.agent == "tool-use":
        from src.agents.tool_use_agent import ToolUseAgent
        from src.backends.adapters import simulated_execute_tool, tool_use_decide, tool_use_generate

        decide = tool_use_decide(backend, [])
        if getattr(args, "sandbox", False):
            from src.backends.sandbox import SandboxedToolExecutor

            execute = SandboxedToolExecutor({})
        else:
            execute = simulated_execute_tool()
        generate = tool_use_generate(backend)
        return lambda: ToolUseAgent(decide_tools=decide, execute_tool=execute, generate=generate)
    if args.agent == "multi-turn":
        from src.agents.multi_turn_agent import MultiTurnAgent
        from src.backends.adapters import multi_turn_generate

        generate = multi_turn_generate(backend)
        return lambda: MultiTurnAgent(generate=generate)
    return None


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
    parser.add_argument(
        "--backend",
        choices=["ollama", "llamacpp"],
        default=None,
        help="Local LLM backend for real agent archetypes",
    )
    parser.add_argument("--model", default="qwen2.5:14b", help="Model name (Ollama backend)")
    parser.add_argument("--model-path", default=None, help="GGUF model file path (LlamaCpp backend)")
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Use Docker-sandboxed tool execution for tool-use agent (requires Docker)",
    )
    args = parser.parse_args(argv)

    if args.backend == "llamacpp" and not args.model_path:
        print("Error: --model-path is required when --backend llamacpp", file=sys.stderr)
        return 1

    _unimplemented = {"rag", "tool-use", "multi-turn"}
    if args.agent in _unimplemented and args.backend is None:
        print(
            f"Agent '{args.agent}' is not yet wired to a live API. "
            "Use --agent echo for offline benchmarking, or provide --backend.",
            file=sys.stderr,
        )
        return 1

    try:
        attacks = load_corpus(args.corpus)
    except FileNotFoundError as e:
        print(f"Error loading corpus: {e}", file=sys.stderr)
        return 1

    backend = _build_backend(args)
    agent_factory = _build_agent_factory(args, backend)

    runner = ArmorEvalRunner(agent_factory)
    summary = runner.run_benchmark(attacks, iterations=args.iterations)

    output = {k: v for k, v in summary.items() if k != "results"}
    output["total_attacks"] = summary["total_attacks"]
    print(json.dumps(output, indent=2))

    with open("results.json", "w") as f:
        json.dump(summary, f, default=str, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
