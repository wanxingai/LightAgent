import os
from LightAgent import LightAgent, LightSwarm

agent = LightAgent(
        name="Agent A",  # 代理名称
        instructions="You are a helpful agent.",  # 角色描述
        role="Please remember that you are LightAgent, a useful assistant to help users use multiple tools.",  # system role description
        model="gpt-4o-mini",  # 支持的模型：openai, chatglm, deepseek, qwen 等 qwen-turbo-2024-11-01 \ step-1-flash
        api_key="your_api_key",  # 替换为你的 API Key
        base_url="http://your_base_url/v1",  # api url
        debug=True,
        log_level="DEBUG",
        log_file="example.log"
    )


# 模拟历史对话
history = [
    {"role": "user", "content": "今天天气怎么样？"},
    {"role": "assistant", "content": "今天天气晴朗，温度在25度左右。"},
]


user_id = "test_user_2"
query = "你好，请总结上面的信息"
response = agent.run(query, history=history, stream=True, user_id=user_id)  # 使用 agent 运行查询
for chunk in response:
    print(chunk, end="\n", flush=True)
