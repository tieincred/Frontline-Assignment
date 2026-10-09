"""One end-to-end offline replay of the greeting-to-load-context transition."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

import call_helpers
from call_helpers import get_load_context
from evals.replay import build_greeting_context


FAKE_LOAD = {
    "id": "00000000-0000-0000-0000-000000000123",
    "load_id": "REF-1234",
    "origin_city": "Atlanta",
    "origin_state": "GA",
    "destination_city": "Chicago",
    "destination_state": "IL",
    "pickup_time": "June 10 at 9 AM",
    "dropoff_time": "June 11 at 4 PM",
    "equipment": "Dry van",
    "commodity": "Paper goods",
    "special_instructions": "Driver must check in on arrival",
    "start_rate": 1800,
    "book_now_rate": 1950,
    "max_rate": 2100,
}


@pytest.mark.asyncio
async def test_successful_load_lookup_replaces_greeting_prompt_and_preserves_history(
):
    """A fake successful lookup exercises the production prompt transition."""
    context = build_greeting_context(org_name="Northstar Freight")
    original_history = context.messages[1:].copy()
    greeting_prompt = context.messages[0]["content"]
    tool_results: list[dict] = []

    async def capture_result(payload, *, properties=None):
        tool_results.append(json.loads(payload))

    lookup = MagicMock(return_value=FAKE_LOAD)
    update_call_load = MagicMock()
    with (
        patch.object(
            call_helpers.NegotiationDBService,
            "get_load_by_reference",
            new=lookup,
        ),
        patch.object(call_helpers, "update_call_load", new=update_call_load),
    ):
        await get_load_context(
            "get_load_context",
            "replay-load-lookup",
            {"load_id": "REF-1234"},
            None,
            context,
            capture_result,
        )

    lookup.assert_called_once_with("REF-1234", context.org_id)
    update_call_load.assert_called_once_with(context.call_id, FAKE_LOAD["id"])
    assert tool_results == [
        {
            "status": "success",
            "message": "Load REF-1234 information retrieved successfully",
            "load_data": context.load_context,
            "call_id": context.call_id,
        }
    ]
    assert context.messages[1:] == original_history
    assert context.messages[0]["role"] == "system"
    assert context.messages[0]["content"] != greeting_prompt
    assert (
        "We just found the load context for reference number: REF-1234."
        in context.messages[0]["content"]
    )
    assert "Opening Offer: $1800.0" in context.messages[0]["content"]


@pytest.mark.asyncio
async def test_invalid_reference_never_reaches_database_or_changes_context():
    """Transcript junk must not trigger a load read or discard the greeting."""
    context = build_greeting_context(org_name="Northstar Freight")
    original_messages = context.messages.copy()
    tool_results: list[dict] = []

    async def capture_result(payload, *, properties=None):
        tool_results.append(json.loads(payload))

    lookup = MagicMock()
    update_call_load = MagicMock()
    with (
        patch.object(
            call_helpers.NegotiationDBService,
            "get_load_by_reference",
            new=lookup,
        ),
        patch.object(call_helpers, "update_call_load", new=update_call_load),
    ):
        await get_load_context(
            "get_load_context",
            "replay-invalid-reference",
            {"load_id": "Noted down"},
            None,
            context,
            capture_result,
        )

    lookup.assert_not_called()
    update_call_load.assert_not_called()
    assert tool_results == [
        {
            "status": "error",
            "message": (
                "A reference number is required to look up the load. "
                "Please ask the caller to provide their reference number first."
            ),
        }
    ]
    assert context.messages == original_messages


@pytest.mark.asyncio
async def test_missing_org_load_preserves_greeting_and_does_not_update_call():
    """A plausible reference that is absent for this org cannot switch prompts."""
    context = build_greeting_context(org_name="Northstar Freight")
    original_messages = context.messages.copy()
    tool_results: list[dict] = []

    async def capture_result(payload, *, properties=None):
        tool_results.append(json.loads(payload))

    lookup = MagicMock(return_value=None)
    update_call_load = MagicMock()
    with (
        patch.object(
            call_helpers.NegotiationDBService,
            "get_load_by_reference",
            new=lookup,
        ),
        patch.object(call_helpers, "update_call_load", new=update_call_load),
    ):
        await get_load_context(
            "get_load_context",
            "replay-missing-org-load",
            {"load_id": "REF-9999"},
            None,
            context,
            capture_result,
        )

    lookup.assert_called_once_with("REF-9999", context.org_id)
    update_call_load.assert_not_called()
    assert tool_results == [
        {"status": "error", "message": "No load found with ID: REF-9999"}
    ]
    assert context.messages == original_messages
