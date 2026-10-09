"""Offline evaluation of the above-max agreement recording boundary."""

from __future__ import annotations

import json
from types import SimpleNamespace
from uuid import UUID
from unittest.mock import MagicMock, patch

import pytest

import call_helpers
from call_helpers import record_agreement
from evals.checks import check_above_max_recording


MAX_RATE = 2100.0
ABOVE_MAX_PRICE = 2200.0


def _agreement_context() -> SimpleNamespace:
    return SimpleNamespace(
        load_uuid="00000000-0000-0000-0000-000000000123",
        load_context={"load_id": "REF-1234", "maxRate": MAX_RATE},
        caller_mc="123456",
        caller_phone="+14155550100",
        call_id="00000000-0000-0000-0000-000000000099",
    )


@pytest.mark.asyncio
async def test_evaluator_flags_normal_above_max_agreement_and_accepts_follow_up():
    """The evaluator passes by detecting the first path's product failure."""
    context = _agreement_context()
    normal_results: list[dict] = []
    follow_up_results: list[dict] = []

    async def capture_normal_result(payload, *, properties=None):
        normal_results.append(json.loads(payload))

    async def capture_follow_up_result(payload, *, properties=None):
        follow_up_results.append(json.loads(payload))

    save_agreement = MagicMock(
        side_effect=[
            UUID("00000000-0000-0000-0000-000000000201"),
            UUID("00000000-0000-0000-0000-000000000202"),
        ]
    )
    notify_quote = MagicMock(return_value="quote-001")
    with (
        patch.object(call_helpers, "save_agreement", new=save_agreement),
        patch.object(
            call_helpers.NegotiationDBService,
            "notify_carrier_quote",
            new=notify_quote,
        ),
    ):
        await record_agreement(
            "record_agreement",
            "normal-above-max",
            {"agreed_price": ABOVE_MAX_PRICE, "above_max": False},
            None,
            context,
            capture_normal_result,
        )

        normal_evaluation = check_above_max_recording(
            max_rate=MAX_RATE,
            agreed_price=ABOVE_MAX_PRICE,
            above_max=False,
            database_recorded=save_agreement.call_count == 1,
            quote_sent=notify_quote.call_count == 1,
        )

        notify_quote.reset_mock()
        await record_agreement(
            "record_agreement",
            "follow-up-above-max",
            {
                "agreed_price": ABOVE_MAX_PRICE,
                "above_max": True,
                "carrier_contact_name": "Casey Carrier",
                "carrier_contact_phone": "+14155550101",
            },
            None,
            context,
            capture_follow_up_result,
        )

        follow_up_evaluation = check_above_max_recording(
            max_rate=MAX_RATE,
            agreed_price=ABOVE_MAX_PRICE,
            above_max=True,
            database_recorded=save_agreement.call_count == 2,
            quote_sent=notify_quote.called,
        )

    assert normal_results[0]["status"] == "success"
    assert normal_evaluation.passed is False
    assert "Database record: created." in normal_evaluation.evidence
    assert "Carrier quote: sent." in normal_evaluation.evidence

    assert follow_up_results[0]["status"] == "success"
    assert follow_up_evaluation.passed is True
    assert "Database record: created." in follow_up_evaluation.evidence
    assert "Carrier quote: not sent." in follow_up_evaluation.evidence

    assert save_agreement.call_args_list[0].args[3] is False
    assert save_agreement.call_args_list[1].args[3] is True
    notify_quote.assert_not_called()
