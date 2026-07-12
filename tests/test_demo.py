"""Tests for the README demo script (task 019)."""

import json
import re
import subprocess
import sys
from pathlib import Path

_RESULTS_PATH = Path("results.json")
_DEMO_SVG_PATH = Path("artifacts/demo.svg")


def test_demo_script_exists():
    # T-019-01
    assert Path("scripts/demo_report.py").exists()


def test_demo_script_runs_and_produces_svg():
    # T-019-02
    result = subprocess.run(
        [sys.executable, "scripts/demo_report.py"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"demo_report.py failed:\n{result.stderr}"
    assert Path("artifacts/demo.svg").exists()


def test_demo_svg_is_valid_svg():
    # T-019-03
    content = Path("artifacts/demo.svg").read_text()
    assert "<svg" in content[:500], "artifacts/demo.svg does not look like a valid SVG"


def test_readme_references_demo_image():
    # T-019-04
    readme = Path("README.md").read_text()
    assert "demo.svg" in readme, "README.md does not reference artifacts/demo.svg"


# TC-020-07
def test_demo_report_shows_block_rates_for_multi_iteration_data():
    """When results.json carries multi-iteration consistency data, demo_report.py
    renders N/M block-rate fractions in the Bare/Armor columns instead of a single
    binary outcome glyph."""
    backup = _RESULTS_PATH.read_text() if _RESULTS_PATH.exists() else None
    svg_backup = _DEMO_SVG_PATH.read_text() if _DEMO_SVG_PATH.exists() else None
    payload = {
        "total_attacks": 1,
        "with_armor": {"detection_rate": 1.0, "false_positive_rate": 0.0},
        "without_armor": {"detection_rate": 1 / 3},
        "latency_overhead_ms": -5.0,
        "consistency": {
            "inj-001": {
                "bare_blocked": 1,
                "bare_total": 3,
                "armored_blocked": 3,
                "armored_total": 3,
                "bare_block_rate": 1 / 3,
                "armored_block_rate": 1.0,
                "verdict": "armor_adds_protection",
            }
        },
        "results": [
            {"attack_id": "inj-001", "outcome": "success", "armor_active": False},
            {"attack_id": "inj-001", "outcome": "blocked", "armor_active": True},
        ],
    }
    try:
        _RESULTS_PATH.write_text(json.dumps(payload))
        result = subprocess.run(
            [sys.executable, "scripts/demo_report.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"demo_report.py failed:\n{result.stderr}"
        svg = Path("artifacts/demo.svg").read_text()
        assert re.search(r"1/3", svg), "expected a 1/3 bare block-rate fraction in demo.svg"
        assert re.search(r"3/3", svg), "expected a 3/3 armored block-rate fraction in demo.svg"
    finally:
        if backup is not None:
            _RESULTS_PATH.write_text(backup)
        else:
            _RESULTS_PATH.unlink(missing_ok=True)
        if svg_backup is not None:
            _DEMO_SVG_PATH.write_text(svg_backup)
