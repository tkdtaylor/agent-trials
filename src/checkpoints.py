"""Checkpoint management for grouped benchmark runs.

Provides pure-function helpers for splitting attacks into groups, writing/loading
checkpoint files, and merging results across groups.
"""

import dataclasses
import json
import pathlib
from enum import Enum

from src.types import AttackOutcome, AttackVector, RunResult


def split_into_groups(attacks: list[AttackVector], group_size: int) -> list[list[AttackVector]]:
    """Partition attacks into sequential groups of at most group_size.

    Args:
        attacks: List of attack vectors to split.
        group_size: Maximum attacks per group.

    Returns:
        List of groups, where each group is a list of attacks.
    """
    groups = []
    for i in range(0, len(attacks), group_size):
        groups.append(attacks[i : i + group_size])
    return groups


def checkpoint_path(output: pathlib.Path, group_index: int) -> pathlib.Path:
    """Return the checkpoint file path for a given group.

    Format: {output.stem}_group_{NNN}.json in output's parent directory.

    Args:
        output: Path to the final results.json file.
        group_index: Zero-based group number.

    Returns:
        Path to the checkpoint file for this group.
    """
    parent = output.parent
    stem = output.stem
    name = f"{stem}_group_{group_index:03d}.json"
    return parent / name


def is_checkpointed(output: pathlib.Path, group_index: int) -> bool:
    """Return True if the checkpoint file for group_index already exists.

    Args:
        output: Path to the final results.json file.
        group_index: Zero-based group number.

    Returns:
        True if the checkpoint file exists, False otherwise.
    """
    return checkpoint_path(output, group_index).exists()


def write_checkpoint(path: pathlib.Path, results: list[RunResult]) -> None:
    """Serialize results to JSON at path (atomic: write to .tmp then rename).

    Each RunResult is written as a plain dict via dataclasses.asdict.
    AttackOutcome enum is stored as its .value string.

    Args:
        path: Path to write the checkpoint file.
        results: List of RunResult objects to serialize.
    """
    def _default(obj):
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        if isinstance(obj, Enum):
            return obj.value
        return str(obj)

    # Write to temporary file first
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w") as f:
        json.dump(results, f, default=_default, indent=2)

    # Atomic rename
    tmp_path.replace(path)


def load_checkpoint(path: pathlib.Path) -> list[RunResult]:
    """Deserialize a checkpoint file back into RunResult objects.

    The string outcome values are converted back to AttackOutcome enum members.

    Args:
        path: Path to the checkpoint file.

    Returns:
        List of RunResult objects.
    """
    from src.types import AgentTrace

    with open(path) as f:
        data = json.load(f)

    results = []
    for item in data:
        # Reconstruct nested AgentTrace first
        trace_data = item.pop("trace")
        trace = AgentTrace(**trace_data)

        # Convert outcome string back to enum
        outcome_str = item.pop("outcome")
        outcome = AttackOutcome(outcome_str)

        # Reconstruct RunResult
        result = RunResult(
            outcome=outcome,
            trace=trace,
            **item
        )
        results.append(result)

    return results


def merge_group_results(groups: list[list[RunResult]]) -> list[RunResult]:
    """Flatten a list of per-group result lists into a single list.

    Args:
        groups: List of result lists, one per group.

    Returns:
        Flattened list of all results.
    """
    all_results = []
    for group in groups:
        all_results.extend(group)
    return all_results
