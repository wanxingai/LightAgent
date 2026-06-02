#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manual LightFlow demo.

Run from the repository root:

    LIGHTAGENT_API_KEY="your_api_key" python tests/lightflow_demo.py
"""

import json
import os

from LightAgent import LightAgent, LightFlow


API_KEY = os.getenv("LIGHTAGENT_API_KEY") or os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("LIGHTAGENT_BASE_URL", "http://newapi.wanxingai.cn/v1/")
MODEL = os.getenv("LIGHTAGENT_MODEL", "deepseek-v3.2")


def build_agent(name: str, role: str) -> LightAgent:
    if not API_KEY:
        raise RuntimeError("Set LIGHTAGENT_API_KEY or OPENAI_API_KEY before running this demo.")

    return LightAgent(
        name=name,
        role=role,
        model=MODEL,
        api_key=API_KEY,
        base_url=BASE_URL,
        tree_of_thought=False,
        filter_tools=False,
        self_learning=False,
        debug=True,
        log_level="DEBUG",
        log_file="lightflow_demo.log",
    )


def main():
    research_agent = build_agent(
        "researcher",
        "你是一个研究助手。请提炼用户问题中的关键事实、背景和需要进一步说明的要点。",
    )
    writer_agent = build_agent(
        "writer",
        "你是一个写作助手。请根据研究结果输出结构清晰、简洁可执行的中文回答。",
    )

    flow = (
        LightFlow()
        .step(
            "research",
            agent=research_agent,
            query="请分析 LightFlow 在多 Agent 工作流中的核心价值。",
        )
        .step(
            "write",
            agent=writer_agent,
            depends_on=["research"],
            query=lambda context: (
                "请基于下面的研究结果，写一段面向开发者的 LightFlow 介绍：\n\n"
                f"{context['outputs']['research']}"
            ),
            max_retry=2,
        )
    )

    result = flow.run("LightFlow demo", user_id="lightflow_demo_user", trace=True)

    print("Final answer:")
    print(result.content)
    print("\nStep summary:")
    print(json.dumps(
        [
            {
                "name": step.name,
                "success": step.error is None,
                "attempts": step.attempts,
                "content": step.content,
            }
            for step in result.steps
        ],
        ensure_ascii=False,
        indent=2,
    ))
    print("\nTrace events:")
    print(json.dumps(result.trace, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
