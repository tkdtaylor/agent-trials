import time
from collections.abc import Callable
from datetime import UTC, datetime

from src.agent_wrapper import AgentProtocol
from src.judge import judge_outcome
from src.types import AgentTrace, AttackOutcome, AttackVector, RunResult


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


class ArmorEvalRunner:
    def __init__(self, agent_factory: Callable[[], AgentProtocol], armor_client=None):
        self._agent_factory = agent_factory
        self._armor_client = armor_client

    def run_single_attack(self, attack: AttackVector, enable_armor: bool = True) -> RunResult:
        start = time.monotonic()

        try:
            agent = self._agent_factory()
        except Exception as e:
            return RunResult(
                attack_id=attack.id,
                attack_name=attack.name,
                outcome=AttackOutcome.ERROR,
                trace=AgentTrace(
                    input_received=attack.payload,
                    final_output=str(e),
                    latency_ms=(time.monotonic() - start) * 1000,
                    timestamp=_now(),
                ),
                armor_active=enable_armor,
                verdict_reasoning=f"agent factory error: {e}",
            )

        armor = self._armor_client if enable_armor else None

        try:
            if armor is not None:
                input_check = armor.check_input(attack.payload, agent.session_id)
                if input_check.blocked:
                    return RunResult(
                        attack_id=attack.id,
                        attack_name=attack.name,
                        outcome=AttackOutcome.BLOCKED,
                        trace=AgentTrace(
                            input_received=attack.payload,
                            final_output="BLOCKED_BY_ARMOR_INPUT",
                            latency_ms=(time.monotonic() - start) * 1000,
                            timestamp=_now(),
                            armor_blocks=[{"stage": "input", "reason": getattr(input_check, "reason", "blocked")}],
                        ),
                        armor_active=True,
                        verdict_reasoning="Armor blocked input",
                    )

            response = agent.process_request(attack.payload)

            armor_blocks: list[dict] = []
            if armor is not None:
                output_check = armor.check_output(response.text, agent.session_id)
                if output_check.blocked:
                    armor_blocks = [{"stage": "output", "reason": getattr(output_check, "reason", "blocked")}]
                    return RunResult(
                        attack_id=attack.id,
                        attack_name=attack.name,
                        outcome=AttackOutcome.BLOCKED,
                        trace=AgentTrace(
                            input_received=attack.payload,
                            final_output=response.text,
                            latency_ms=(time.monotonic() - start) * 1000,
                            timestamp=_now(),
                            context_retrieved=agent.retrieved_context,
                            tool_calls_attempted=agent.tool_calls,
                            armor_blocks=armor_blocks,
                        ),
                        armor_active=True,
                        verdict_reasoning="Armor blocked output",
                    )

            outcome, reasoning = judge_outcome(attack, response.text, agent.tool_calls)
            return RunResult(
                attack_id=attack.id,
                attack_name=attack.name,
                outcome=outcome,
                trace=AgentTrace(
                    input_received=attack.payload,
                    final_output=response.text,
                    latency_ms=(time.monotonic() - start) * 1000,
                    timestamp=_now(),
                    context_retrieved=agent.retrieved_context,
                    tool_calls_attempted=agent.tool_calls,
                    armor_blocks=armor_blocks,
                ),
                armor_active=enable_armor,
                verdict_reasoning=reasoning,
            )

        except Exception as e:
            return RunResult(
                attack_id=attack.id,
                attack_name=attack.name,
                outcome=AttackOutcome.ERROR,
                trace=AgentTrace(
                    input_received=attack.payload,
                    final_output=str(e),
                    latency_ms=(time.monotonic() - start) * 1000,
                    timestamp=_now(),
                ),
                armor_active=enable_armor,
                verdict_reasoning=f"agent error: {e}",
            )

    def run_benchmark(self, attacks: list[AttackVector], iterations: int = 1) -> dict:
        results: list[RunResult] = []
        for _ in range(iterations):
            for attack in attacks:
                results.append(self.run_single_attack(attack, enable_armor=False))
                results.append(self.run_single_attack(attack, enable_armor=True))
        return self._aggregate_results(attacks, results)

    def _aggregate_results(self, attacks: list[AttackVector], results: list[RunResult]) -> dict:
        without_armor = [r for r in results if not r.armor_active]
        with_armor = [r for r in results if r.armor_active]
        with_summary = _summarize(with_armor)
        without_summary = _summarize(without_armor)
        return {
            "total_attacks": len(attacks),
            "with_armor": with_summary,
            "without_armor": without_summary,
            "latency_overhead_ms": with_summary["avg_latency_ms"] - without_summary["avg_latency_ms"],
            "results": results,
        }


def _summarize(results: list[RunResult]) -> dict:
    total = len(results)
    blocked = sum(1 for r in results if r.outcome.value == "blocked")
    success = sum(1 for r in results if r.outcome.value == "success")
    false_positive = sum(1 for r in results if r.outcome.value == "false_positive")
    error = sum(1 for r in results if r.outcome.value == "error")
    denominator = blocked + success + error
    return {
        "blocked": blocked,
        "success": success,
        "false_positive": false_positive,
        "error": error,
        "detection_rate": blocked / denominator if denominator > 0 else 0.0,
        "false_positive_rate": false_positive / total if total > 0 else 0.0,
        "avg_latency_ms": sum(r.trace.latency_ms for r in results) / total if total > 0 else 0.0,
    }
