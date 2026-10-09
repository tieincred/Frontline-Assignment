"""Shared offline scenario for the above-max agreement safety check."""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID

import call_helpers
from call_helpers import record_agreement
from evals.checks import EvaluationResult, check_above_max_recording
from evals.safety import offline_guard


MAX_RATE = 2100.0
ABOVE_MAX_PRICE = 2200.0
@dataclass(frozen=True)
class AgreementScenarioReport:
    """Observed side effects and evaluations for both above-max tool calls."""

    normal_result: dict
    follow_up_result: dict
    normal_evaluation: EvaluationResult
    follow_up_evaluation: EvaluationResult
    save_calls: tuple[tuple, ...]
    quote_calls: tuple[dict[str, object], ...]


def _agreement_context() -> SimpleNamespace:
    return SimpleNamespace(
        load_uuid="00000000-0000-0000-0000-000000000123",
        load_context={"load_id": "REF-1234", "maxRate": MAX_RATE},
        caller_mc="123456",
        caller_phone="+14155550100",
        call_id="00000000-0000-0000-0000-000000000099",
    )


async def run_above_max_agreement_scenario() -> AgreementScenarioReport:
    """Run both existing above-max paths without persistence or network access."""
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
        offline_guard(),
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
        normal_quote_calls = tuple(
            dict(call.kwargs) for call in notify_quote.call_args_list
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

    return AgreementScenarioReport(
        normal_result=normal_results[0],
        follow_up_result=follow_up_results[0],
        normal_evaluation=normal_evaluation,
        follow_up_evaluation=follow_up_evaluation,
        save_calls=tuple(call.args for call in save_agreement.call_args_list),
        quote_calls=normal_quote_calls,
    )
