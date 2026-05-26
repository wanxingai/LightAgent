#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

import json
from typing import Dict, Any, List


def create_skill_tools(skill_manager):
    """创建与技能交互的工具函数"""

    def list_skills() -> str:
        """
        列出所有可用的技能

        Returns:
            技能列表的JSON字符串
        """
        skills = []
        for skill in skill_manager.skills.values():
            skills.append({
                "name": skill.name,
                "description": skill.description,
                "has_scripts": skill.has_scripts,
                "has_references": skill.has_references,
                "has_assets": skill.has_assets
            })
        return json.dumps({"skills": skills}, ensure_ascii=False, indent=2)

    # 为函数添加tool_info属性
    list_skills.tool_info = {
        "tool_name": "list_skills",
        "tool_title": "列出可用技能",
        "tool_description": "获取所有已加载技能的列表及其描述",
        "tool_params": []
    }

    def activate_skill(skill_name: str) -> str:
        """
        激活指定技能，获取完整指令

        Args:
            skill_name: 技能名称

        Returns:
            技能的完整指令
        """
        try:
            instructions = skill_manager.activate_skill(skill_name)
            return instructions
        except Exception as e:
            return f"激活技能失败: {str(e)}"

    activate_skill.tool_info = {
        "tool_name": "activate_skill",
        "tool_title": "激活技能",
        "tool_description": "加载指定技能的完整指令到上下文",
        "tool_params": [
            {"name": "skill_name", "description": "要激活的技能名称", "type": "string", "required": True}
        ]
    }

    def execute_skill_script(skill_name: str, script_name: str, args: List[str] = None) -> str:
        """
        执行技能中的脚本

        Args:
            skill_name: 技能名称
            script_name: 脚本文件名
            args: 脚本参数列表

        Returns:
            脚本执行结果
        """
        return skill_manager.execute_script(skill_name, script_name, args)

    execute_skill_script.tool_info = {
        "tool_name": "execute_skill_script",
        "tool_title": "执行技能脚本",
        "tool_description": "执行技能目录scripts/下的脚本文件",
        "tool_params": [
            {"name": "skill_name", "description": "技能名称", "type": "string", "required": True},
            {"name": "script_name", "description": "脚本文件名", "type": "string", "required": True},
            {"name": "args", "description": "脚本参数列表", "type": "array", "required": False}
        ]
    }

    def read_skill_reference(skill_name: str, ref_path: str) -> str:
        """
        读取技能中的参考文档

        Args:
            skill_name: 技能名称
            ref_path: 参考文档路径（相对于references目录）

        Returns:
            文档内容
        """
        return skill_manager.read_reference(skill_name, ref_path)

    read_skill_reference.tool_info = {
        "tool_name": "read_skill_reference",
        "tool_title": "读取技能参考文档",
        "tool_description": "读取技能目录references/下的文档内容",
        "tool_params": [
            {"name": "skill_name", "description": "技能名称", "type": "string", "required": True},
            {"name": "ref_path", "description": "参考文档路径", "type": "string", "required": True}
        ]
    }

    return [list_skills, activate_skill, execute_skill_script, read_skill_reference]