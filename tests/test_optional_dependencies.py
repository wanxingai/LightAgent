import builtins
import subprocess
import sys

from LightAgent.builtin_tools.nos import upload_file_to_oss


def test_lightagent_import_does_not_require_boto3():
    script = """
import builtins

real_import = builtins.__import__

def guarded_import(name, *args, **kwargs):
    if name == "boto3" or name.startswith("botocore"):
        raise ImportError(f"blocked optional dependency: {name}")
    return real_import(name, *args, **kwargs)

builtins.__import__ = guarded_import
import LightAgent
assert LightAgent.LightAgent is not None
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_upload_file_to_oss_reports_missing_optional_boto3(monkeypatch, tmp_path):
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "boto3" or name.startswith("botocore"):
            raise ImportError(f"blocked optional dependency: {name}")
        return real_import(name, *args, **kwargs)

    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    result = upload_file_to_oss(str(sample))

    assert "缺少可选依赖库" in result
    assert "LightAgent[oss]" in result
