from LightAgent import LightAgent, LightFlow


api_key = "your_api_key"
base_url = "http://your_base_url/v1"
model = "deepseek-v4-flash"


research_agent = LightAgent(
    name="Research Agent",
    model=model,
    api_key=api_key,
    base_url=base_url,
    role="You research the user's request and return concise facts and constraints.",
)

writer_agent = LightAgent(
    name="Writer Agent",
    model=model,
    api_key=api_key,
    base_url=base_url,
    role="You write a clear final answer based only on the provided research output.",
)

review_agent = LightAgent(
    name="Review Agent",
    model=model,
    api_key=api_key,
    base_url=base_url,
    role="You review the answer for clarity, missing context, and actionability.",
)


flow = (
    LightFlow()
    .step(
        "research",
        agent=research_agent,
        query="Research the core value of LightFlow for multi-agent workflows.",
    )
    .step(
        "write",
        agent=writer_agent,
        depends_on=["research"],
        query=lambda context: (
            "Write a short developer-facing introduction based on this research:\n\n"
            f"{context['outputs']['research']}"
        ),
        max_retry=2,
    )
    .step(
        "review",
        agent=review_agent,
        depends_on=["write"],
        query=lambda context: (
            "Review and improve this draft. Keep the answer concise:\n\n"
            f"{context['outputs']['write']}"
        ),
    )
)


result = flow.run(
    "Explain LightFlow in LightAgent v0.8.0.",
    user_id="lightflow_example_user",
    trace=True,
)

print("Final answer:")
print(result.content)

print("\nStep outputs:")
for step in result.steps:
    print(f"- {step.name}: success={step.error is None}, attempts={step.attempts}")
    print(step.content)

print("\nTrace events:")
for event in result.trace:
    print(event["type"], event.get("data", {}))
