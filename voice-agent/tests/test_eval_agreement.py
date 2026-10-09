"""Offline evaluation of the above-max agreement recording boundary."""

from __future__ import annotations

import pytest

from evals.agreement import run_above_max_agreement_scenario


@pytest.mark.asyncio
async def test_evaluator_flags_normal_above_max_agreement_and_accepts_follow_up():
    """The evaluator passes by detecting the first path's product failure."""
    report = await run_above_max_agreement_scenario()

    assert report.normal_result["status"] == "success"
    assert report.normal_evaluation.passed is False
    assert "Database record: created." in report.normal_evaluation.evidence
    assert "Carrier quote: sent." in report.normal_evaluation.evidence

    assert report.follow_up_result["status"] == "success"
    assert report.follow_up_evaluation.passed is True
    assert "Database record: created." in report.follow_up_evaluation.evidence
    assert "Carrier quote: not sent." in report.follow_up_evaluation.evidence

    assert report.save_calls[0][3] is False
    assert report.save_calls[1][3] is True
    assert len(report.quote_calls) == 1
