"""Offline evaluation of the transfer identity-confirmation boundary."""

import pytest

from evals.transfer import run_unconfirmed_transfer_probe


@pytest.mark.asyncio
async def test_evaluator_reports_transfer_started_for_unconfirmed_carrier():
    """The test passes because it detects the real missing identity guard."""
    report = await run_unconfirmed_transfer_probe()

    assert report.result["status"] == "transferring"
    assert report.orchestration_started is True
    assert report.transfer_scheduled is True
    assert report.evaluation.passed is False
    assert "Context had load_uuid and carrier_identity_confirmed=False." in report.evaluation.evidence
