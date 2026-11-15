"""Create credential-free snapshots and run isolated, offline test containers."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4


VERSIONS = ("3.10", "3.11", "3.12", "3.13")


def image_metadata(reference):
    result = subprocess.run(["docker", "image", "inspect", reference], capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)[0]
    # Some daemon/tag combinations list a tag but only resolve its image ID.
    ids = subprocess.check_output(["docker", "image", "ls", "--no-trunc", "--filter",
                                   "reference=" + reference, "--format", "{{.ID}}"], text=True).splitlines()
    matches = [json.loads(subprocess.check_output(["docker", "image", "inspect", identity]))[0] for identity in set(ids)]
    matches = [item for item in matches if reference in item.get("RepoTags", [])]
    if len(matches) != 1:
        raise RuntimeError("cannot resolve an unambiguous image identity: " + reference)
    return matches[0]


def copy_research_source(source, destination):
    """Stage only the sibling package's build inputs, never its local data."""
    source = Path(source).resolve(strict=True)
    if not (source / "pyproject.toml").is_file() or not (source / "__init__.py").is_file():
        raise ValueError("research source must contain LightResearch's pyproject.toml and __init__.py")
    destination.mkdir(parents=True)
    paths = [source / "pyproject.toml", *sorted(source.glob("*.py"))]
    if (source / "README.md").is_file():
        paths.append(source / "README.md")
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError("research input must be a regular file: " + path.name)
        shutil.copyfile(path, destination / path.name)


def snapshot(source, destination, *, research_source=None, research_wheel=None):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists() or source == destination or source in destination.parents:
        raise ValueError("snapshot destination must be new and outside the checkout")
    names = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=source).decode().split("\0"))
    if research_source is not None and research_wheel is not None:
        raise ValueError("choose either a research source or a research wheel")
    names.update(str(p.relative_to(source)) for p in (source / "LightAgent").rglob("*") if p.is_file())
    names.update(str(p.relative_to(source)) for p in (source / "tests").rglob("test_*.py"))
    for folder in ("tests/research", "tests/fixtures", "tests/acceptance"):
        names.update(str(p.relative_to(source)) for p in (source / folder).rglob("*") if p.is_file())
    names.update("example/" + name for name in ("15.durable_execution.py", "16.jobs_and_history.py", "17.signed_providers.py"))
    names.update(("tests/__init__.py", "tests/wheel_smoke.py", "tests/extension_wheel_smoke.py"))
    files = {}
    destination.mkdir(parents=True, mode=0o700)
    for name in sorted(names):
        relative = Path(name)
        if (not name or relative.parts[0] == "LightResearch" or relative.is_absolute() or ".." in relative.parts or
                any(part in {".git", ".github", ".DS_Store", "__pycache__", "dist", "build"} or part.endswith(".egg-info") for part in relative.parts)
                or relative.suffix in {".bak", ".pyc", ".log", ".pem", ".key"} or relative.name.startswith(".env")):
            continue
        path = source / relative
        if not path.is_file():
            continue
        if path.is_symlink():
            raise ValueError("snapshot contains a symlink: " + name)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        files[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    if research_source is not None:
        copy_research_source(research_source, destination / "research-input" / "source")
    if research_wheel is not None:
        wheel = Path(research_wheel).resolve(strict=True)
        if not wheel.is_file() or wheel.suffix != ".whl":
            raise ValueError("research wheel must be a .whl file")
        target = destination / "research-input" / "wheel" / wheel.name
        target.parent.mkdir(parents=True)
        shutil.copyfile(wheel, target)
    for path in (destination / "research-input").rglob("*"):
        if path.is_file():
            files[path.relative_to(destination).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    upstream = destination / "upstream-tests"
    upstream.mkdir()
    for name in ("test_mcp_client_manager.py", "test_tool_schema_validation.py"):
        target = upstream / name
        target.write_bytes(subprocess.check_output(["git", "show", "HEAD:tests/" + name], cwd=source))
        files["upstream-tests/" + name] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = dict(schema_version=1, files=files)
    (destination.parent / "snapshot.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()


def execute(command, log):
    print("Running: " + " ".join(command[:6]), flush=True)
    with log.open("w") as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"exit {result.returncode}; see {log}")


def one(version, output, digest, *, build_only=False, with_research=False):
    target = output / ("python-" + version)
    target.mkdir(exist_ok=True)
    image = "lightagent-v1-acceptance:py" + version.replace(".", "") + "-" + digest[:10]
    report = dict(python=version, image=image, status="preparing")
    try:
        reference = "python:" + version + "-slim-bookworm"
        base = image_metadata(reference)
        report.update(base_image_id=base["Id"], base_digest=base["RepoDigests"][0])
        execute(["docker", "build", "--pull=false", "--build-arg", "BASE_IMAGE=" + report["base_digest"],
                 "--file", str(output / "source/tests/acceptance/Dockerfile"), "--tag", image, str(output / "source")],
                target / "build.log")
        report["image_id"] = image_metadata(image)["Id"]
        report["status"] = "built"
        if not build_only:
            command = ["python", "tests/acceptance/verify.py", "--output", "/reports"]
            if with_research:
                command.extend(("--research-wheel", "/opt/wheels/research"))
            execute(["docker", "run", "--rm", "--name", "la-acceptance-" + uuid4().hex[:12], "--network", "none",
                     "--cpus", "2", "--memory", "2500m", "--pids-limit", "512",
                     "--volume", str(target) + ":/reports", report["image_id"], *command], target / "container.log")
            report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", error=str(error))
    finally:
        (target / "container.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--versions", nargs="+", choices=VERSIONS, default=list(VERSIONS))
    parser.add_argument("--jobs", type=int, choices=(1, 2), default=1)
    parser.add_argument("--build-only", action="store_true")
    research = parser.add_mutually_exclusive_group()
    research.add_argument("--research-source", type=Path, help="explicit LightResearch checkout")
    research.add_argument("--research-wheel", type=Path, help="explicit LightResearch wheel")
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    digest = snapshot(args.source, args.output / "source",
                      research_source=args.research_source, research_wheel=args.research_wheel)
    with_research = args.research_source is not None or args.research_wheel is not None
    with ThreadPoolExecutor(args.jobs) as pool:
        reports = list(pool.map(lambda version: one(version, args.output, digest, build_only=args.build_only,
                                                    with_research=with_research), args.versions))
    (args.output / "matrix.json").write_text(json.dumps(
        dict(snapshot_digest=digest, with_research=with_research, results=reports), indent=2) + "\n")
    sys.exit(1 if any(r["status"] == "failed" for r in reports) else 0)
