# Evaluation decisions

## Scope

- Preserve the existing single-prompt architecture and production code.
- Run handlers offline with mocked persistence, quote, telephony, and network
  boundaries. Use placeholder configuration only.
- Do not claim coverage of live LLM behavior, audio, speech recognition,
  telephony, provider authentication, or real service writes.

## Chosen risks

1. A strictly above-max price recorded as a normal agreement is the highest
   current financial risk because it can also trigger quote submission.
2. An above-max follow-up is legitimate only when explicitly marked, supplied
   with contact details, and not submitted as a quote.
3. Failed load lookup must not replace the greeting prompt or update a call.
4. The lookup service currently ignores its `org_id` argument. This is recorded
   as an ownership-boundary limitation rather than misrepresented as tested
   tenant isolation.
5. Transfer currently proves a loaded reference/routing but not confirmed
   carrier identity; evaluate and report the gap without silently changing
   production behavior.
6. Internal-rate confidentiality applies to carrier-facing Room1. Room2 is
   explicitly broker-facing and may discuss those rates when asked.

## Trade-offs

- Handler checks are deterministic and safe, but do not show that a model will
  choose the right tool call from arbitrary speech.
- Synthetic text/tool-trace graders test grader calibration, not model quality.
- Existing functional tests remain the source for lower-level phone persistence,
  lookup, and transfer-routing behavior; evaluation scenarios add cross-boundary
  product evidence instead of duplicating them.
- Exact-ceiling behavior remains a product ambiguity. The current prompt's rate
  bands suggest a firm-at-ceiling result should be `no_agreement`, while another
  prompt phrase can be read more broadly. Record it until product direction is
  supplied rather than silently treating it as above-max.

## Current finding

The offline runner intentionally exits 1 because a price above the fixture
maximum, passed to `record_agreement` with `above_max=false`, is observed as a
normal saved agreement and a quote notification. The test passes because it
detects this real product behavior; the product safety outcome does not pass.
