import logging

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
