# Evaluation decisions

## Implemented scope

- Preserve production code and the existing single-prompt architecture.
- Run handler probes with dummy configuration, mocked side-effect boundaries,
  and a socket-level no-network tripwire.
- Keep real handler results separate from synthetic grader calibration.
- Make no claim about live model choice, audio, speech recognition, Daily,
  real persistence, provider authentication, or concurrent tool calls.

## Actual findings

1. An above-max price submitted with `above_max=false` issues mocked normal-save
   and quote-notification calls. The runner exits 1 for this observed handler
   behavior; the mocks do not prove completed persistence or delivery.
2. An above-max follow-up with contact details issues a mocked save call and no
   quote-notification call; its full mocked save payload is checked.
3. A below-ceiling agreement checks the complete mocked save call (load UUID,
   price, call ID, and contacts) and quote payload. A mocked `None` save result
   returns the database error and issues no quote-notification call.
4. A direct transfer fixture with a routable loaded reference and
   `carrier_identity_confirmed=false` still sets transfer metadata and schedules
   transfer. This proves that `handle_transfer_to_human` does not inspect that
   field in this fixture. It does not prove the field is an authoritative
   requirement in every configuration: the phone-first producer of identity
   state is gated by `HIGHWAY_PHONE_LOOKUP_ENABLED` upstream.
5. Invalid and missing load lookups preserve the greeting/history and avoid a
   call-record update. A successful lookup replaces the system prompt and sets
   load state.
6. `get_load_by_reference` ignores `org_id`; record this as a known limitation,
   not a passing tenant-isolation test.

## Calibration decision

The Room1 disclosure grader uses planted controls only. Its bad control is not
an observed product failure; it proves the grader rejects a trace containing
internal goal/ceiling values and labels. Its good control proves an opening-rate
response can pass. Room2 is excluded because its broker-facing prompt permits
internal-rate discussion.

## Deferred work

Close-ordering evaluation is deliberately deferred. Exact-ceiling behavior also
remains a product ambiguity: the prompt's rate bands suggest `no_agreement` for
a firm-at-ceiling bid, while another phrase can be read more broadly. Neither is
claimed as implemented coverage.
