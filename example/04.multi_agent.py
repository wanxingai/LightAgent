import os

from LightAgent import LightAgent, LightSwarm
# Set Environment Variables OPENAI_API_KEY and OPENAI_BASE_URL
# The default model uses gpt-4o-mini
model = "gpt-4o-mini"
os.environ["OPENAI_API_KEY"] = "your_api_key"
os.environ["OPENAI_BASE_URL"] = "http://your_base_url/v1"
# Create an instance of LightSwarm
light_swarm = LightSwarm()

# Create multiple agents
agent_a = LightAgent(
    name="Agent A",
    model=model,
    instructions="I am Agent A, the front desk receptionist.",
    role="Receptionist responsible for welcoming visitors and providing basic information guidance. Before each reply, please state your identity and that you can only guide users to other roles, not directly answer business questions. If you cannot help the user, please respond: Sorry, I am currently unable to assist!"
)

agent_b = LightAgent(
    name="Agent B",
    model=model,
    instructions="I am Agent B, responsible for the reservation of meeting rooms.",
    role="Meeting room reservation administrator in charge of handling reservations, cancellations, and inquiries for meeting rooms 1, 2, and 3."
)

agent_c = LightAgent(
    name="Agent C",
    model=model,
    instructions="I am Agent C, a technical support specialist, responsible for handling technical issues. Please state your identity before each reply, offering detailed responses to technical inquiries, and guide users to contact higher-level technical support for issues beyond your capability."
)

agent_d = LightAgent(
    name="Agent D",
    model=model,
    instructions="I am Agent D, an HR specialist, responsible for handling HR-related questions.",
    role="HR specialist managing inquiries and processes related to employee onboarding, offboarding, leave, and benefits."
)

# Automatically register agents to the LightSwarm instance
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# Run Agent A
res = light_swarm.run(agent=agent_a, query="Hello, I am Alice. I need to check if Wang Xiaoming has completed onboarding.", stream=False)
print(res)