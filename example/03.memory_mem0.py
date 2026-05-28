# Enable Memory Module

# Or use a custom memory module, here is an example with mem0 https://github.com/mem0ai/mem0/
from mem0 import Memory
from LightAgent import LightAgent
import os
from loguru import logger

class CustomMemory:
    def __init__(self):
        self.memories = []
        os.environ["OPENAI_API_KEY"] = "your_api_key"
        os.environ["OPENAI_BASE_URL"] = "http://your_base_url/v1"
        # Initialize Mem0
        config = {
            "version": "v1.1"
        }
        # Use qdrant as a vector database for storing memories in mem0, change config to the code below
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
        """Store memory. Developers can modify the internal implementation of the storage method; the current example is the mem0 method for adding memory."""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """Retrieve related memory. Developers can modify the internal implementation of the retrieval method; the current example is the mem0 method for searching memory."""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="Please remember that you are LightAgent, a useful assistant to help users use multiple tools.",  # system role description
        model="deepseek-chat",  # Supported models: openai, chatglm, deepseek, qwen, etc.
        api_key="your_api_key",  # Replace with your large model provider API Key
        base_url="your_base_url",  # Replace with your large model provider api url
        memory=CustomMemory(),  # Enable memory function
        tree_of_thought=False,  # Enable Chain of Thought
    )

# Memory-enabled test & if tools need to be added, you can add tools to the agent for memory-enabled tool calls

user_id = "user_01"
logger.info("\n=========== next conversation ===========")
query = "Introduce me to the attractions in Sanya. Many of my friends have traveled to Sanya, and I want to visit too."
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== next conversation ===========")
query = "Where should I travel?"
print(agent.run(query, stream=False, user_id=user_id))