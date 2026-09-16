import asyncio

import pytest

from LightAgent import AgentRuntime, JobStatus


def test_expired_job_lease_prevents_result_publication():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()

        async def work():
            await asyncio.sleep(0.03)
            return "must not publish"

        started = runtime.jobs.start("leased", work, lease_seconds=0.005)
        return runtime, started, await runtime.jobs.wait(started.job_id)

    runtime, started, completed = asyncio.run(scenario())

    assert completed.status == JobStatus.INTERRUPTED
    assert completed.result is None
    assert completed.lease_epoch == 1
    assert any(event.type == "job.interrupted" for event in runtime.session.events)


def test_job_lease_renewal_and_resume_are_epoch_fenced():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()

        async def slow_work():
            await asyncio.sleep(0.02)
            return "first"

        started = runtime.jobs.start("leased", slow_work, lease_seconds=0.005)
        interrupted = await runtime.jobs.wait(started.job_id)
        resumed = runtime.jobs.resume(started.job_id, lambda: "recovered", lease_seconds=1)
        with pytest.raises(RuntimeError, match="stale"):
            runtime.jobs.renew_lease(
                resumed.job_id,
                1,
                expected_epoch=resumed.lease_epoch - 1,
            )
        renewed = runtime.jobs.renew_lease(
            resumed.job_id,
            1,
            expected_epoch=resumed.lease_epoch,
        )
        completed = await runtime.jobs.wait(resumed.job_id)
        return interrupted, resumed, renewed, completed

    interrupted, resumed, renewed, completed = asyncio.run(scenario())

    assert interrupted.status == JobStatus.INTERRUPTED
    assert resumed.lease_epoch == 2
    assert renewed.lease_epoch == 2
    assert completed.status == JobStatus.SUCCESS
    assert completed.result == "recovered"
