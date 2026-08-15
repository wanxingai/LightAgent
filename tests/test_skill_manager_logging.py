import logging

import pytest

from LightAgent import LightAgent
from LightAgent.logger import LoggerManager
from LightAgent.skills import SkillManager


def write_skill(skills_dir, name="demo", description="Demo skill"):
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\nUse the demo skill.\n",
        encoding="utf-8",
    )
    return skill_dir


def test_discover_skills_uses_standard_logging_logger_without_type_error(tmp_path, caplog):
    skills_dir = tmp_path / "skills"
    write_skill(skills_dir)
    logger = logging.getLogger("lightagent.test.skillmanager")

    manager = SkillManager([str(skills_dir)], logger=logger)

    with caplog.at_level(logging.DEBUG, logger=logger.name):
        discovered = manager.discover_skills()

    assert [skill.name for skill in discovered] == ["demo"]
    assert "discover_skill" in caplog.text


def test_lightagent_init_auto_discovers_skills_with_default_logger(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills"
    write_skill(skills_dir)
    monkeypatch.chdir(tmp_path)

    agent = LightAgent(
        model="deepseek-v4-flash",
        api_key="sk-test",
        base_url="https://api.example.test/v1",
        skills_directories=[str(skills_dir)],
    )

    assert "demo" in agent.skill_manager.skills


def test_discover_skills_logs_errors_with_standard_logging_logger(tmp_path, caplog):
    skills_dir = tmp_path / "skills"
    bad_skill_dir = skills_dir / "bad"
    bad_skill_dir.mkdir(parents=True)
    bad_skill_dir.joinpath("SKILL.md").write_text(
        "---\nname: bad\n---\n\nMissing required description.\n",
        encoding="utf-8",
    )
    logger = logging.getLogger("lightagent.test.skillmanager.error")

    manager = SkillManager([str(skills_dir)], logger=logger)

    with caplog.at_level(logging.ERROR, logger=logger.name):
        discovered = manager.discover_skills()

    assert discovered == []
    assert "discover_skill_failed" in caplog.text
    assert "Skill missing required fields" in caplog.text


def test_log_keeps_logger_manager_signature():
    class CapturingLogger(LoggerManager):
        def __init__(self):
            self.calls = []

        def log(self, level, action, data):
            self.calls.append((level, action, data))

    logger = CapturingLogger()
    manager = SkillManager([], logger=logger)

    manager._log("DEBUG", "discover_skill", {"name": "demo"})

    assert logger.calls == [("DEBUG", "discover_skill", {"name": "demo"})]


def test_later_skill_directory_wins_and_conflict_is_reported(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_skill(first, description="First")
    winner = write_skill(second, description="Second")
    manager = SkillManager([str(first), str(second)])

    manager.discover_skills()

    assert manager.skills["demo"].description == "Second"
    assert manager.skills["demo"].path == str(winner)
    assert manager.list_conflicts() == [{
        "name": "demo",
        "winner": str(winner),
        "shadowed": str(first / "demo"),
        "rule": "later skills_directories entry wins",
    }]


def test_project_instructions_are_loaded_root_to_leaf_and_bounded(tmp_path):
    project = tmp_path / "project"
    nested = project / "src" / "feature"
    nested.mkdir(parents=True)
    project.joinpath("AGENTS.md").write_text("project rules", encoding="utf-8")
    nested.joinpath("AGENTS.md").write_text("feature rules", encoding="utf-8")
    manager = SkillManager([])

    instructions = manager.discover_project_instructions(nested)

    assert instructions.index("project rules") < instructions.index("feature rules")
    with pytest.raises(ValueError, match="exceed max_chars"):
        manager.discover_project_instructions(nested, max_chars=5)


def test_skill_reference_asset_and_script_paths_cannot_escape(tmp_path):
    skills_dir = tmp_path / "skills"
    skill_dir = write_skill(skills_dir)
    skill_dir.joinpath("references").mkdir()
    skill_dir.joinpath("references", "guide.md").write_text("safe", encoding="utf-8")
    skill_dir.joinpath("assets").mkdir()
    skill_dir.joinpath("assets", "data.bin").write_bytes(b"safe")
    skill_dir.joinpath("scripts").mkdir()
    manager = SkillManager([str(skills_dir)])
    manager.discover_skills()

    assert manager.read_reference("demo", "guide.md") == "safe"
    assert manager.read_asset("demo", "data.bin") == b"safe"
    assert "Security violation" in manager.read_reference("demo", "../../AGENTS.md")
    with pytest.raises(ValueError, match="Security violation"):
        manager.read_asset("demo", "../../outside.bin")
    assert "Security violation" in manager.execute_script("demo", "../../outside.py")
