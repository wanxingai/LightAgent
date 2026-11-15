import asyncio

from LightAgent import AgentRuntime, JobStatus
from LightAgent.cancellation import accepts_keyword


def test_accepts_keyword_positional_only_parameter() -> None:
    def operation(cancellation_token: object = None, /) -> object:
        return cancellation_token

    assert not accepts_keyword(operation, "cancellation_token")


def test_accepts_keyword_variadic_positional_parameter() -> None:
    def operation(*cancellation_token: object) -> tuple[object, ...]:
        return cancellation_token

    assert not accepts_keyword(operation, "cancellation_token")


def test_accepts_keyword_positional_only_with_keyword_arguments() -> None:
    def operation(cancellation_token: object = None, /, **kwargs: object) -> object:
        return kwargs.get("cancellation_token")

    assert accepts_keyword(operation, "cancellation_token")


def test_job_start_positional_only_default() -> None:
    async def scenario() -> None:
        runtime = AgentRuntime()
        runtime.open_session()

        async def operation(cancellation_token: object = None, /) -> str:
            return "done"

        record = runtime.jobs.start("work", operation)
        completed = await runtime.jobs.wait(record.job_id)

        assert completed.status == JobStatus.SUCCESS
        assert completed.result == "done"

    asyncio.run(scenario())
