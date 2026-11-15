"""Shared clean-environment acceptance entry point for Docker and CI."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import xml.etree.ElementTree as ET

ALLOWED_SKIPS = {
    "opt in to real Worker/Docker integration",
    "real Mem0 Graph security matrix is opt-in",
    "set LIGHTAGENT_CODEX_INTEGRATION=1 with a logged-in local Codex CLI",
}


def junit_summary(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    totals = {key: sum(int(s.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    totals["passed"] = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    totals["skip_reasons"] = sorted({case.find("skipped").get("message", "")
        for suite in suites for case in suite.findall("testcase") if case.find("skipped") is not None})
    return totals


def run(command, log, *, cwd=None, env=None):
    with log.open("w") as stream:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}); see {log.name}")


def require_complete(summary):
    if (not summary["tests"] or summary["failures"] or summary["errors"] or
            set(summary["skip_reasons"]) - ALLOWED_SKIPS):
        raise RuntimeError("incomplete acceptance suite or unexpected skips")


def resolve_wheel(path):
    path = Path(path).resolve()
    if path.is_dir():
        wheels = sorted(path.glob("*.whl"))
        if len(wheels) != 1:
            raise ValueError(f"expected exactly one wheel in {path}; found {len(wheels)}")
        path = wheels[0]
    if not path.is_file() or path.suffix != ".whl":
        raise ValueError(f"expected a wheel file: {path}")
    return path


def build_research(source, output):
    if __package__:
        from .clean_matrix import copy_research_source
    else:
        from clean_matrix import copy_research_source

    wheels = output / "research-wheels"
    wheels.mkdir()
    with TemporaryDirectory(prefix="lightresearch-build-") as directory:
        staged = Path(directory) / "source"
        copy_research_source(source, staged)
        run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(wheels), str(staged)],
            output / "research-build.log", cwd=directory)
    return resolve_wheel(wheels)


def validate(output, *, core_wheel, research_wheel=None, research_source=None):
    if research_wheel is not None and research_source is not None:
        raise ValueError("choose either a research source or a research wheel")
    joint = research_wheel is not None or research_source is not None
    core_wheel = resolve_wheel(core_wheel)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    config = Path(sys.prefix) / "pyvenv.cfg"
    if sys.prefix == sys.base_prefix or not config.exists() or "include-system-site-packages = false" not in config.read_text().lower():
        raise RuntimeError("acceptance requires a venv without inherited site-packages")
    node = shutil.which("node")
    if joint and not node:
        raise RuntimeError("Node.js is required; do not silently skip console behavior tests")
    report = dict(schema_version=1, status="running", python=sys.version, platform=platform.platform(),
                  prefix=sys.prefix, base_prefix=sys.base_prefix, inherited_site_packages=False,
                  mode="joint" if joint else "core",
                  node=subprocess.check_output([node, "--version"], text=True).strip() if node else None,
                  wheels={core_wheel.name: hashlib.sha256(core_wheel.read_bytes()).hexdigest()})
    try:
        run([sys.executable, "-m", "pip", "check"], output / "pip-check.log")
        run([sys.executable, "-m", "pip", "freeze", "--all"], output / "freeze.txt")
        run([sys.executable, "-m", "pip", "inspect"], output / "installed.json")
        report["dependencies"] = {name: importlib.metadata.version(name) for name in
                                  ("openai", "mcp", "pydantic", "pydantic-settings", "PyYAML", "cryptography", "pytest")}
        for name in ("mem0ai", "langfuse"):
            try:
                report["dependencies"][name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                report["dependencies"][name] = None
        environment = {**os.environ, "PYTHONPATH": str(Path.cwd()), "PYTHONNOUSERSITE": "1"}
        suite = [sys.executable, "-m", "pytest", "-q", "tests", "-rs", "-o", "faulthandler_timeout=60",
                 "--junitxml=" + str(output / "full.xml")]
        if joint:
            research_wheel = (build_research(research_source, output) if research_source is not None
                              else resolve_wheel(research_wheel))
            report["wheels"][research_wheel.name] = hashlib.sha256(research_wheel.read_bytes()).hexdigest()
            with TemporaryDirectory(prefix="lightresearch-test-") as directory:
                run([sys.executable, "-m", "pip", "install", "--no-index", "--no-deps", "--target",
                     directory, str(research_wheel)], output / "research-install.log")
                joint_env = dict(environment, PYTHONPATH=os.pathsep.join((directory, environment["PYTHONPATH"])))
                run([sys.executable, "-c", "from importlib.util import find_spec; from pathlib import Path; import sys; "
                     "assert Path(find_spec('LightResearch').origin).resolve().is_relative_to(Path(sys.argv[1]).resolve())",
                     directory], output / "research-isolation.log", cwd=directory, env=joint_env)
                run(suite, output / "full.log", env=joint_env)
        else:
            run([sys.executable, "-c", "from importlib.util import find_spec; "
                 "assert find_spec('LightResearch') is None, 'core acceptance requires no LightResearch'"],
                output / "core-isolation.log", env=environment)
            run(suite + ["--ignore=tests/research", "-m", "not requires_lightresearch"],
                output / "full.log", env=environment)
        run([sys.executable, "tests/wheel_smoke.py", str(core_wheel)],
            output / "wheel.log", env=environment)
        if joint:
            run([sys.executable, "tests/extension_wheel_smoke.py", str(core_wheel), str(research_wheel)],
                output / "extension.log", env=environment)
        report["tests"] = junit_summary(output / "full.xml")
        require_complete(report["tests"])
        if (Path("upstream-tests")).is_dir():
            run([sys.executable, "-m", "pytest", "-q", "upstream-tests", "--junitxml=" + str(output / "upstream.xml")],
                output / "upstream.log", env=environment)
            report["upstream_tests"] = junit_summary(output / "upstream.xml")
        report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", error=str(error))
        raise
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--core-wheel", type=Path)
    research = parser.add_mutually_exclusive_group()
    research.add_argument("--research-wheel", type=Path, help="wheel file or directory containing exactly one wheel")
    research.add_argument("--research-source", type=Path, help="explicit LightResearch checkout (builds a wheel)")
    args = parser.parse_args()
    validate(args.output, core_wheel=args.core_wheel or Path("/opt/wheels/core"),
             research_wheel=args.research_wheel, research_source=args.research_source)
