import os
from loguru import logger
from LightAgent import LightAgent, LightSwarm


# 或者使用自定义记忆模块，下面以mem0为例 https://github.com/mem0ai/mem0/
from mem0 import Memory

class CustomMemory:
    def __init__(self):
        self.memories = []
        os.environ["OPENAI_API_KEY"] = "your_api_key"
        os.environ["OPENAI_BASE_URL"] = "http://your_base_url/v1"
        # Initialize Mem0
        config = {
            "version": "v1.1"
        }
        # mem0中 如需使用qdrant作为向量数据库存储记忆，请将config改为下面代码
        # config = {
        #     "vector_store": {
        #         "provider": "qdrant",
        #         "config": {
        #             "host": "localhost",
        #             "port": 6333,
        #         }
        #     },
        #     "version": "v1.1"
        # }
        self.m = Memory.from_config(config_dict=config)

    def store(self, data: str, user_id):
        """存储记忆 开发者可以自行修改存储方法的内部实现"""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """检索相关记忆 开发者可以自行修改检索方法的内部实现"""
        result = self.m.search(query, user_id=user_id)
        return result


agent = LightAgent(
        name="Agent A",  # 代理名称
        instructions="You are a helpful agent.",  # 角色描述
        role="Please remember that you are LightAgent, a useful assistant to help users use multiple tools.",  # system role description
        model="gpt-4o-mini",  # 支持的模型：openai, chatglm, deepseek, qwen 等 qwen-turbo-2024-11-01 \ step-1-flash
        api_key="your_api_key",  # 替换为你的 API Key
        base_url="http://your_base_url/v1",  # api url
        memory=CustomMemory(),  # 启用记忆功能
        tree_of_thought=False,  # 启用思维链
        self_learning=True,  #启用agent自我学习
        debug=True,
        log_level="DEBUG",
        log_file="example.log"
    )

def run_conversation(query: str, stream=False, max_retry=5, user_id="user1"):
    logger.info(f"\n开始思考问题: {query}")
    response = agent.run(query, stream=stream, max_retry=max_retry, user_id=user_id)  # 使用 agent 运行查询
    # 处理响应
    if stream:
        for chunk in response:
            print(chunk, end="\n", flush=True)
            # content = chunk.choices[0].delta.content or ""
            # print(content, end="", flush=True)
    else:
        logger.info(f"Final Reply: \n{response}")
    return response

# agent自我学习的测试1
logger.info("\n=========== next conversation ===========")
user_id = "test_user_1"
query = "我现在有一个采购货款需要转账，我的审批流程是怎么样的？"
run_conversation(query, stream=True, user_id=user_id)
logger.info("\n=========== next conversation ===========")
query = "请记住：本公司新规定，2025年1月起，公司所有采购货款的转账需要先找负责采购的丁总签字，再交给财务经历审批，财务经历审批后，还需要公司总经理审批，出纳才能打款转过去。"
run_conversation(query, stream=True, user_id=user_id)

user_id = "test_user_2"
query = "你好，我有一笔采购款要转给对方，我要怎么申请转账？"
run_conversation(query, stream=True, user_id=user_id)