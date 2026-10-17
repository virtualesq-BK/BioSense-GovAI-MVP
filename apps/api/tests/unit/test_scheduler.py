"""Unit tests for scheduler job registration logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from biosense.config import settings


@pytest.fixture(autouse=True)
def _fresh_scheduler(monkeypatch):
    """Each test gets a clean scheduler with .start() stubbed out (no event loop needed)."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    fresh = AsyncIOScheduler()
    # Stub start() so synchronous tests don't need a running event loop.
    monkeypatch.setattr(fresh, "start", MagicMock())
    monkeypatch.setattr("biosense.jobs.scheduler.scheduler", fresh)
    yield fresh
    if fresh.running:
        fresh.shutdown(wait=False)


def _job_ids(sched) -> set[str]:
    return {j.id for j in sched.get_jobs()}


# ---------------------------------------------------------------------------
# start_scheduler — job registration
# ---------------------------------------------------------------------------


def test_both_jobs_registered_by_default(_fresh_scheduler) -> None:
    from biosense.jobs.scheduler import start_scheduler

    start_scheduler()

    assert "public_data_full_sync" in _job_ids(_fresh_scheduler)
    assert "literature_harvest" in _job_ids(_fresh_scheduler)


def test_literature_job_absent_when_disabled(monkeypatch, _fresh_scheduler) -> None:
    monkeypatch.setattr(settings, "literature_harvest_scheduler_enabled", False)
    from biosense.jobs.scheduler import start_scheduler

    start_scheduler()

    assert "public_data_full_sync" in _job_ids(_fresh_scheduler)
    assert "literature_harvest" not in _job_ids(_fresh_scheduler)


def test_public_data_job_absent_when_disabled(monkeypatch, _fresh_scheduler) -> None:
    monkeypatch.setattr(settings, "ingestion_scheduler_enabled", False)
    from biosense.jobs.scheduler import start_scheduler

    start_scheduler()

    assert "public_data_full_sync" not in _job_ids(_fresh_scheduler)
    assert "literature_harvest" in _job_ids(_fresh_scheduler)


def test_scheduler_not_started_when_both_disabled(monkeypatch, _fresh_scheduler) -> None:
    monkeypatch.setattr(settings, "ingestion_scheduler_enabled", False)
    monkeypatch.setattr(settings, "literature_harvest_scheduler_enabled", False)
    from biosense.jobs.scheduler import start_scheduler

    start_scheduler()

    assert not _fresh_scheduler.running


def test_literature_job_uses_configured_cron(monkeypatch, _fresh_scheduler) -> None:
    monkeypatch.setattr(settings, "literature_harvest_cron_day_of_week", "wed")
    monkeypatch.setattr(settings, "literature_harvest_cron_hour", 4)
    from biosense.jobs.scheduler import start_scheduler

    start_scheduler()

    job = _fresh_scheduler.get_job("literature_harvest")
    assert job is not None
    fields = {f.name: f for f in job.trigger.fields}
    assert str(fields["day_of_week"]) == "wed"
    assert str(fields["hour"]) == "4"


# ---------------------------------------------------------------------------
# scheduled_literature_harvest — happy path and error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scheduled_literature_harvest_calls_service() -> None:
    mock_result = {"harvested": 5, "skipped": 2, "failed": 0, "paper_ids": [], "message": "ok"}

    with (
        patch(
            "biosense.jobs.scheduler.async_session_factory"
        ) as mock_factory,
        patch(
            "biosense.jobs.scheduler.PubmedHarvestService.harvest",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_harvest,
    ):
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from biosense.jobs.scheduler import scheduled_literature_harvest

        await scheduled_literature_harvest()

    mock_harvest.assert_awaited_once_with(
        max_results_per_query=settings.literature_harvest_max_results_per_query,
    )


@pytest.mark.asyncio
async def test_scheduled_literature_harvest_logs_error_and_does_not_raise() -> None:
    """A harvest failure must not propagate and crash the scheduler."""
    with (
        patch("biosense.jobs.scheduler.async_session_factory") as mock_factory,
        patch(
            "biosense.jobs.scheduler.PubmedHarvestService.harvest",
            new_callable=AsyncMock,
            side_effect=RuntimeError("PubMed unreachable"),
        ),
    ):
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from biosense.jobs.scheduler import scheduled_literature_harvest

        # Must not raise
        await scheduled_literature_harvest()
