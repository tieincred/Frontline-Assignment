# Offline evaluation plan

This suite evaluates the voice agent's highest-risk handler and state
contracts without production credentials, provider calls, audio, or a live
model. It preserves the existing single-prompt architecture and observes the
production prompt transition rather than changing it.

## System map

`bot.py` creates an LLM context with a greeting/MC-verification/reference
prompt. `verify_carrier` stages carrier identity on context; confirmation may
persist the phone-to-carrier mapping. On a valid reference,
`get_load_context` reads and normalizes a load, replaces `messages[0]` with the
full negotiation prompt, stores `load_uuid`, `load_context`, and transfer
routing, then updates the call record.

`record_agreement` does not compare the agreed price to `load_context.maxRate`.
With `above_max=false` it saves a normal negotiation and attempts KCH quote
notification. With `above_max=true` it requires contact details, stores an
above-max follow-up, and skips the quote notification.

`transfer_to_human` requires a loaded reference and transfer routing, but does
not require `carrier_identity_confirmed`. Room2 is broker-only: its prompt
explicitly permits sharing internal rates with the human broker. Carrier-facing
Room1 confidentiality checks must not be applied to Room2.

`get_load_context` passes `context.org_id` to `get_load_by_reference`, but the
current service ignores it because KCH load rows have no tenant ownership
field. This is an ownership-boundary limitation, not tenant-isolation coverage.

## Prioritized cases

| Priority | Case | Evidence and threshold | Boundary |
| --- | --- | --- | --- |
| P0 | Above-max normal agreement | Price above fixture max must produce neither normal save nor quote. | Release block; currently fails product behavior. |
| P0 | Above-max follow-up | `above_max=true`, contact details, saved record, no quote. | Release block. |
| P0 | Load prompt transition | Successful lookup replaces only system prompt and preserves history; failed lookup changes neither prompt/history nor call record. | Release block. |
| P0 | Ownership-boundary limitation | Record that reference lookup ignores org ID. | Informational until source schema has ownership. |
| P1 | Transfer before identity confirmation | Loaded-but-unconfirmed context must not start orchestration. | Known current enforcement gap. |
| P1 | Carrier-facing internal-rate leak | Synthetic Room1 response must not reveal goal/ceiling values or labels. | Release block when grader is calibrated. |
| P2 | Close/transfer ordering | Synthetic tool traces must honor prerequisites and outcome-specific end reasons. | Release block for unsafe ordering. |

## Evaluation layers

Handler checks call production handlers with mocked external boundaries. They
are evidence about actual code paths: lookup, prompt replacement, persistence,
quote notification, transfer guards, and Room2 context construction.

Synthetic graders inspect fixed assistant text and tool traces only. They
calibrate grader rules: known carrier-facing leaks fail, opening-rate-only text
passes, and Room2 broker discussion of internal rates passes. They do not prove
live-model, speech-to-text, TTS, Daily, transfer, or audio behavior.

Existing functional tests already cover carrier persistence, reference
plausibility, transfer routing, and database lookup mechanics. New evaluation
tests should compose those boundaries into the product risks above rather than
duplicate their unit coverage.

## Run

The suite runs with placeholder values only:

```bash
cd voice-agent
SUPABASE_URL=http://test-suite.local SUPABASE_SERVICE_ROLE_KEY=test-key \
  /tmp/e3-voice-agent-eval-venv/bin/python -m pytest \
  tests/test_eval_replay.py tests/test_eval_agreement.py -q

SUPABASE_URL=http://test-suite.local SUPABASE_SERVICE_ROLE_KEY=test-key \
  /tmp/e3-voice-agent-eval-venv/bin/python -m evals
```

The runner intentionally exits non-zero while it observes the current unsafe
above-max normal-agreement behavior. A passing test that detects this finding is
not a passing product behavior.
