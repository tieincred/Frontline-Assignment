"""Small, dependency-free building blocks for offline call replays.

The replay intentionally uses the same initial-prompt builder as the bot while
keeping the context lightweight, as the handler tests do.  Tool handlers can
therefore mutate it exactly as they do during a call without starting a voice
pipeline or contacting external services.
"""

from __future__ import annotations

from types import SimpleNamespace

from load_context_utils import get_initial_system_prompt


def build_greeting_context(org_name: str | None = None) -> SimpleNamespace:
    """Return an LLMContext-shaped object seeded with the production greeting.

    The fixed history represents a carrier who has been greeted, supplied an
    MC number, confirmed the returned carrier identity, and supplied a load
    reference.  It is deliberately plain data so tests can inspect prompt
    replacement directly.
    """
    greeting_prompt = get_initial_system_prompt(org_name=org_name)
    return SimpleNamespace(
        messages=[
            {"role": "system", "content": greeting_prompt},
            {
                "role": "assistant",
                "content": "Hi, this is Northstar Freight, can I get your MC number?",
            },
            {"role": "user", "content": "My MC is 123456."},
            {"role": "assistant", "content": "Is this Acme Trucking?"},
            {"role": "user", "content": "Yes. The reference is REF-1234."},
        ],
        org_id="00000000-0000-0000-0000-000000000001",
        call_id="00000000-0000-0000-0000-000000000099",
        caller_phone="+14155550100",
    )
