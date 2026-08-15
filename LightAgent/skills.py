#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-22
"""

import os
import yaml
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
import logging


@dataclass
class Skill:
    """技能数据类"""
    name: str
    description: str
    path: str
    instructions: str = ""
    has_scripts: bool = False
    has_references: bool = False
    has_assets: bool = False
    source_directory: str | None = None
    precedence: int = 0


class SkillManager:
    """技能管理器：发现、加载和执行技能"""

    def __init__(self, skills_directories: List[str] = None, logger=None):
        self.skills_directories = skills_directories or ["skills"]
        self.skills: Dict[str, Skill] = {}
        self.skill_conflicts: List[Dict[str, Any]] = []
        self.logger = logger or logging.getLogger(__name__)

    def discover_skills(self) -> List[Skill]:
        """发现所有可用技能（仅加载元数据）"""
        discovered = []
        self.skills = {}
        self.skill_conflicts = []

        for precedence, base_dir in enumerate(self.skills_directories):
            if not os.path.exists(base_dir):
                continue

            for item in sorted(os.listdir(base_dir)):
                skill_path = os.path.join(base_dir, item)
                skill_file = os.path.join(skill_path, "SKILL.md")

                if os.path.isdir(skill_path) and os.path.exists(skill_file):
                    try:
                        skill = self._load_skill_metadata(skill_path)
                        if skill:
                            skill.source_directory = str(Path(base_dir).resolve())
                            skill.precedence = precedence
                            previous = self.skills.get(skill.name)
                            if previous is not None:
                                conflict = {
                                    "name": skill.name,
                                    "winner": skill.path,
                                    "shadowed": previous.path,
                                    "rule": "later skills_directories entry wins",
                                }
                                self.skill_conflicts.append(conflict)
                                self._log("WARNING", "skill_conflict", conflict)
                            self.skills[skill.name] = skill
                            discovered.append(skill)
                            self._log("DEBUG", "discover_skill",
                                      {"name": skill.name, "path": skill_path})
                    except Exception as e:
                        self._log("ERROR", "discover_skill_failed",
                                  {"path": skill_path, "error": str(e)})

        return discovered

    def list_conflicts(self) -> List[Dict[str, Any]]:
        """Return deterministic diagnostics for shadowed Skill names."""
        return [dict(item) for item in self.skill_conflicts]

    def discover_project_instructions(
            self,
            start_directory: str | os.PathLike[str] | None = None,
            *,
            filename: str = "AGENTS.md",
            max_chars: int = 100_000,
    ) -> str:
        """Load project instructions from filesystem root to the working directory."""
        current = Path(start_directory or os.getcwd()).resolve()
        candidates = [current, *current.parents]
        contents: List[str] = []
        total = 0
        for directory in reversed(candidates):
            instruction_file = directory / filename
            if not instruction_file.is_file():
                continue
            content = instruction_file.read_text(encoding="utf-8")
            total += len(content)
            if total > max_chars:
                raise ValueError(f"project instructions exceed max_chars={max_chars}")
            contents.append(f"# {instruction_file}\n{content.strip()}")
        return "\n\n".join(contents)

    def _load_skill_metadata(self, skill_path: str) -> Optional[Skill]:
        """从SKILL.md加载技能元数据（仅frontmatter）"""
        skill_file = os.path.join(skill_path, "SKILL.md")

        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            raise ValueError(f"Missing frontmatter in {skill_file}")

        frontmatter = yaml.safe_load(frontmatter_match.group(1))

        # 验证必需字段
        if 'name' not in frontmatter or 'description' not in frontmatter:
            raise ValueError(f"Skill missing required fields (name, description)")

        # 检查可选目录
        has_scripts = os.path.exists(os.path.join(skill_path, "scripts"))
        has_references = os.path.exists(os.path.join(skill_path, "references"))
        has_assets = os.path.exists(os.path.join(skill_path, "assets"))

        return Skill(
            name=frontmatter['name'],
            description=frontmatter['description'],
            path=skill_path,
            has_scripts=has_scripts,
            has_references=has_references,
            has_assets=has_assets
        )

    def activate_skill(self, skill_name: str) -> str:
        """激活技能：加载完整指令到上下文"""
        if skill_name not in self.skills:
            raise ValueError(f"Skill '{skill_name}' not found")

        skill = self.skills[skill_name]
        skill_file = os.path.join(skill.path, "SKILL.md")

        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 移除frontmatter，只保留指令部分
        content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
        skill.instructions = content.strip()

        self._log("INFO", "activate_skill", {"name": skill_name})
        return skill.instructions

    def get_skills_xml(self) -> str:
        """生成技能元数据的XML格式（用于系统提示）"""
        if not self.skills:
            return ""

        xml_parts = ['<available_skills>']

        for skill in self.skills.values():
            xml_parts.append(f'  <skill>')
            xml_parts.append(f'    <name>{skill.name}</name>')
            xml_parts.append(f'    <description>{skill.description}</description>')
            xml_parts.append(f'    <location>{os.path.join(skill.path, "SKILL.md")}</location>')
            xml_parts.append(f'  </skill>')

        xml_parts.append('</available_skills>')
        return '\n'.join(xml_parts)

    def execute_script(self, skill_name: str, script_name: str, args: List[str] = None) -> str:
        """执行技能中的脚本（带沙箱）"""
        if skill_name not in self.skills:
            return f"Error: Skill '{skill_name}' not found"

        skill = self.skills[skill_name]
        scripts_root = Path(skill.path, "scripts").resolve()
        script_path = (scripts_root / script_name).resolve()

        # 安全检查：只允许执行scripts目录下的文件
        if not script_path.is_relative_to(scripts_root):
            return "Error: Security violation - cannot execute outside scripts directory"

        if not script_path.exists():
            return f"Error: Script '{script_path}' not found in skill '{skill_name}'"

        try:
            # 在临时目录中执行以提供隔离
            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run(
                    [str(script_path)] + (args or []),
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=tmpdir
                )

                output = result.stdout
                if result.stderr:
                    output += f"\nSTDERR:\n{result.stderr}"

                self._log("DEBUG", "execute_script",
                          {"skill": skill_name, "script": script_name, "output": output[:200]})
                return output

        except subprocess.TimeoutExpired:
            return "Error: Script execution timeout (30s)"
        except Exception as e:
            return f"Error executing script: {str(e)}"

    def read_reference(self, skill_name: str, ref_path: str) -> str:
        """读取技能中的参考文档"""
        if skill_name not in self.skills:
            return f"Error: Skill '{skill_name}' not found"

        skill = self.skills[skill_name]
        references_root = Path(skill.path, "references").resolve()
        full_path = (references_root / ref_path).resolve()

        # 安全检查：防止目录遍历
        if not full_path.is_relative_to(references_root):
            return "Error: Security violation - invalid reference path"

        if not full_path.exists():
            return f"Error: Reference '{ref_path}' not found"

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading reference: {str(e)}"

    def read_asset(self, skill_name: str, asset_path: str) -> bytes:
        """读取技能中的资源文件（返回二进制数据）"""
        if skill_name not in self.skills:
            raise ValueError(f"Skill '{skill_name}' not found")

        skill = self.skills[skill_name]
        assets_root = Path(skill.path, "assets").resolve()
        full_path = (assets_root / asset_path).resolve()

        # 安全检查
        if not full_path.is_relative_to(assets_root):
            raise ValueError("Security violation: invalid asset path")

        with open(full_path, 'rb') as f:
            return f.read()

    def _log(self, level: str, action: str, data: Any):
        """统一的日志方法，兼容LightAgent的LoggerManager和标准logging"""
        if not self.logger:
            return

        from .logger import LoggerManager

        if isinstance(self.logger, LoggerManager):
            self.logger.log(level, action, data)
        elif hasattr(self.logger, 'debug') and hasattr(self.logger, 'info') and hasattr(self.logger, 'error'):
            log_msg = f"[SkillManager] {action}: {data}"
            level_map = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
            }
            self.logger.log(level_map.get(level, logging.INFO), log_msg)
        # 如果没有合适的logger，忽略日志
