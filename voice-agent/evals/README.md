# Offline evaluation suite

The implemented suite evaluates selected handler/state contracts without
production credentials, provider calls, audio, or a live model. It preserves
the single-prompt architecture and observes the production prompt transition.

## Implemented real-handler probes

| Check | Input | Evidence | Current result |
| --- | --- | --- | --- |
| Successful load lookup | Fixture load after greeting history | System prompt replacement, preserved history, `load_uuid`/`load_context`, call-record update | Pass |
| Invalid reference | Transcript junk reference | No lookup/write, error result, unchanged context | Pass |
| Missing load | Plausible reference returning no result | Lookup gets supplied org ID, no call-record update, unchanged context | Pass; not tenant-isolation coverage |
| Above-max normal agreement | `$2200 > $2100`, `above_max=false` | Mocked save and quote-notification calls | Product behavior fails; evaluator detects it |
| Above-max follow-up | Same price, `above_max=true`, contacts | Exact mocked save payload; no quote-notification call | Pass |
| Below-ceiling agreement | `$2000 < $2100`, contacts | Exact mocked save payload and quote payload | Pass |
| Save failure | Same valid agreement, mocked save returns `None` | Error result; no quote-notification call | Pass |
| Transfer fixture | Routed loaded reference, `carrier_identity_confirmed=false` | Transfer metadata and scheduling calls | Handler does not inspect that flag in this fixture |

`get_load_by_reference` ignores its `org_id` parameter because current KCH load
rows have no tenant ownership field. This is a known limitation, not a passing
tenant-isolation case.

## Synthetic grader calibration

The Room1 disclosure grader evaluates planted text controls, not observed model
behavior. It accepts an opening-rate-only control and rejects a planted trace
containing the internal goal, ceiling, and labels. It is intentionally limited
to carrier-facing Room1 text: Room2 legitimately permits internal-rate
discussion with the human broker.

## Offline safety and limits

Every implemented handler probe applies dummy configuration and a socket
tripwire that fails any unexpected network connection. Database, quote, and
transfer boundaries are mocks: a recorded mock call does not claim completed
persistence or quote delivery.

The suite does not verify live model choice, speech recognition, TTS, Daily
rooms, real provider authentication, real persistence, audio timing, or
concurrent tool-call behavior. Close-ordering evaluation is deferred.

The transfer fixture is deliberately narrower than an all-configuration
identity policy claim. `HIGHWAY_PHONE_LOOKUP_ENABLED` controls phone-first
identity behavior upstream, while this direct handler fixture supplies a false
`carrier_identity_confirmed` value plus a routable loaded reference. It proves
that `handle_transfer_to_human` does not read that value before it starts a
transfer; it does not prove that the flag is authoritative when phone-first is
disabled or absent.

## Portable setup and run

The suite requires Python 3.11 plus the repository requirement files. From a
fresh checkout at the repository root, use this complete sequence. `--seed`
installs pip into the new environment, so the install command is available:

```bash
cd voice-agent
uv venv --seed --python 3.11 .venv
.venv/bin/python -m pip install -r requirements.txt -r tests/requirements-test.txt
```

Run with placeholders only:

```bash
cd voice-agent
SUPABASE_URL=http://test-suite.local SUPABASE_SERVICE_ROLE_KEY=test-key \
  .venv/bin/python -m pytest \
  tests/test_eval_replay.py tests/test_eval_agreement.py \
  tests/test_eval_transfer.py tests/test_eval_prompt_grading.py -q

SUPABASE_URL=http://test-suite.local SUPABASE_SERVICE_ROLE_KEY=test-key \
  .venv/bin/python -m evals
```

Pytest covers the load-lookup replay and harness contracts. The CLI reports the
real agreement and transfer handler probes separately from synthetic grader
calibration. It intentionally exits non-zero while it observes the current
unsafe normal-agreement and unconfirmed-transfer handler behavior. A passing
pytest test that detects either finding is not a passing product behavior.

## Completed run excerpt

```text
6 passed
normal agreement path: FAIL
above-max follow-up: PASS
below-ceiling agreement: PASS
save failure: PASS
transfer identity guard: FAIL
runner exit code: 1
```
