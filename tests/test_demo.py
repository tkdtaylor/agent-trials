"""Tests for the README demo script (task 019)."""

import subprocess
import sys
from pathlib import Path


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
