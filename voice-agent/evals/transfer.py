"""Real-handler probe for transfer before carrier identity confirmation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import transfer_tool_handler
from transfer_tool_handler import TransferToolHandler

from evals.checks import EvaluationResult
from evals.safety import offline_guard


@dataclass(frozen=True)
class TransferProbeReport:
    """Observed transfer-handler outcome for an unconfirmed carrier."""

    result: dict
    orchestration_started: bool
    transfer_scheduled: bool
    evaluation: EvaluationResult


async def run_unconfirmed_transfer_probe() -> TransferProbeReport:
    """Probe the real handler with a load but no confirmed carrier identity."""
    orchestrator = MagicMock()
    speech_sync = MagicMock()
    speech_sync.schedule_after_speech = AsyncMock()
    handler = TransferToolHandler(
        orchestrator=orchestrator,
        http_session=MagicMock(),
        stt=MagicMock(),
        tts=MagicMock(),
        llm=MagicMock(),
        skip_tts_processor=MagicMock(),
        transcript=MagicMock(),
        speech_sync=speech_sync,
        audiobuffer=MagicMock(),
        context_aggregator=MagicMock(),
    )
    context = SimpleNamespace(
        load_uuid="00000000-0000-0000-0000-000000000123",
        carrier_identity_confirmed=False,
    )
    results: list[dict] = []

    async def capture_result(payload, *, properties=None):
        results.append(json.loads(payload))

    with (
        offline_guard(),
        patch.object(
            transfer_tool_handler.NegotiationDBService,
            "get_load",
            return_value={"carrier_sales_rep_phone": "+12058752486"},
        ),
    ):
        await handler.handle_transfer_to_human(
            "transfer_to_human",
            "unconfirmed-transfer",
            {"reason": "carrier requested a person", "load_number": "REF-1234"},
            None,
            context,
            capture_result,
        )

    orchestration_started = orchestrator.set_transfer_metadata.called
    transfer_scheduled = speech_sync.schedule_after_speech.await_count == 1
    evaluation = EvaluationResult(
        passed=not orchestration_started and not transfer_scheduled,
        evidence=(
            "Context had load_uuid and carrier_identity_confirmed=False.",
            f"Handler result: {results[0]['status']}.",
            f"Transfer metadata set: {orchestration_started}.",
            f"Transfer scheduled: {transfer_scheduled}.",
            "Expected safe behavior: reject before orchestration when identity is unconfirmed.",
        ),
    )
    return TransferProbeReport(
        result=results[0],
        orchestration_started=orchestration_started,
        transfer_scheduled=transfer_scheduled,
        evaluation=evaluation,
    )
