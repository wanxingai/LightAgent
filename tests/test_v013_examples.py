import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("name", ["15.durable_execution.py", "16.jobs_and_history.py"])
def test_offline_execution_examples(name, tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / "example" / name)], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(root)}, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_offline_signed_provider_example(tmp_path):
    pytest.importorskip("cryptography")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / "example" / "17.signed_providers.py")], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(root)}, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "Changed bundle rejected" in result.stdout
