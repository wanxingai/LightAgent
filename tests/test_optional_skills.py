import builtins
from types import SimpleNamespace

import pytest

from LightAgent import LightAgent, Skill, SkillManager, create_skill_tools
from LightAgent.skills import Skill as LegacySkill, SkillManager as LegacyManager
from LightAgent.skill_tools import create_skill_tools as legacy_create_skill_tools


def write_skill(directory):
    directory.mkdir(parents=True)
    path = directory / "SKILL.md"
    path.write_text(
        "---\nname: fixture\ndescription: >-\n  An example\n  Skill.\n---\n\nUse the fixture.\n",
        encoding="utf-8",
    )
    return path


def block_yaml(monkeypatch, error):
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "yaml":
            raise error
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


def test_no_skills_does_not_try_to_load_pyyaml(tmp_path, monkeypatch):
    assert Skill is LegacySkill and SkillManager is LegacyManager
    assert create_skill_tools is legacy_create_skill_tools
    monkeypatch.chdir(tmp_path)
    (tmp_path / "skills" / "not-a-skill").mkdir(parents=True)
    block_yaml(monkeypatch, AssertionError("PyYAML imported without a Skill"))
    agent = LightAgent(model="fixture", api_key="fixture")
    message = SimpleNamespace(content="local", tool_calls=None)
    agent.client.chat.completions.create = lambda **kwargs: SimpleNamespace(
        choices=[SimpleNamespace(message=message)]
    )
    assert agent.run("hello") == "local"
    assert agent.skill_manager.skills == {}
    assert "activate_skill" not in agent.tool_registry.function_mappings


@pytest.mark.parametrize("custom", [False, True])
def test_discovered_skill_explicitly_reports_missing_pyyaml(tmp_path, monkeypatch, custom):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / ("custom-skills" if custom else "skills")
    path = write_skill(root / "fixture")
    options = {"skills_directories": [str(root)]} if custom else {}
    missing = ModuleNotFoundError("no PyYAML", name="yaml")
    block_yaml(monkeypatch, missing)

    with pytest.raises(ImportError, match="pip install 'PyYAML>=6.0.1'") as exc:
        LightAgent(model="fixture", api_key="fixture", **options)
    assert "PyYAML" in str(exc.value)
    assert path.name in str(exc.value)
    assert exc.value.__cause__ is missing

    agent = LightAgent(model="fixture", api_key="fixture", auto_discover_skills=False, **options)
    assert agent.skill_manager.skills == {}
    with pytest.raises(ImportError, match="pip install 'PyYAML>=6.0.1'"):
        agent.skill_manager.discover_skills()


def test_skills_does_not_hide_broken_pyyaml_import(tmp_path, monkeypatch):
    write_skill(tmp_path / "fixture")
    broken = ModuleNotFoundError("missing YAML runtime dependency", name="fixture_transitive")
    block_yaml(monkeypatch, broken)
    with pytest.raises(ModuleNotFoundError) as exc:
        SkillManager([str(tmp_path)]).discover_skills()
    assert exc.value is broken


def test_default_discovery_and_activation_skills_with_pyyaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_skill(tmp_path / "skills" / "fixture")
    agent = LightAgent(model="fixture", api_key="fixture")
    assert agent.skill_manager.skills["fixture"].description == "An example Skill."
    assert "activate_skill" in agent.tool_registry.function_mappings
    assert agent.skill_manager.activate_skill("fixture") == "Use the fixture."
