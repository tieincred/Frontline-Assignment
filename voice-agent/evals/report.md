# Offline evaluation report

- Commit: `5a98a66274322954a0a6255f54650eec6e50c41d`
- Timestamp (UTC): `2026-10-09T20:24:27.705441+00:00`
- Completed run count: 1
- Duration: 2.886 seconds
- Unique scenario count: 26 (handler, prompt-contract, and synthetic-control scenarios; assertions are not counted separately)
- Evaluation-harness pytest: exit 0: .......                                                                  [100%]
7 passed in 0.93s
- Existing mocked regression pytest: exit 0: .....................................                   [100%]
37 passed, 17 subtests passed in 0.95s
- Complete runner exit code: 1

## Existing regression coverage (pre-existing tests)

`tests/test_phone_carrier_lookup.py` supplies mocked carrier-verification and phone-first persistence coverage. `tests/test_transfer_tool_handler.py` supplies mocked transfer load/routing guard coverage. They are run and reported above as existing regressions, not re-counted as new scenarios.

## Real-handler evaluations

| Scenario | Expected outcome | Observed outcome | Verdict | Evidence |
| --- | --- | --- | --- | --- |
| lookup success | replace system prompt; preserve history; update call record | success result and expected state changes | PASS | Tool result: {'status': 'success', 'message': 'Load REF-1234 information retrieved successfully', 'load_data': {'id': 'REF-1234', 'load_id': 'REF-1234', 'origin': {'city': 'Atlanta', 'state': 'GA', 'country': None, 'timezone': None}, 'destination': {'city': 'Chicago', 'state': 'IL', 'country': None, 'timezone': None}, 'pickupTime': 'June 10 at 9 AM', 'dropoffTime': 'June 11 at 4 PM', 'equipment': 'Dry van', 'commodity': 'Paper goods', 'isHazmat': None, 'specialInstructions': 'Driver must check in on arrival', 'trackerRequired': False, 'startRate': 1800.0, 'bookNowRate': 1950.0, 'maxRate': 2100.0, 'bookedRate': None, 'customerName': None, 'weight': None, 'transfer_call_to': None, 'transfer_country_code': None}, 'call_id': '00000000-0000-0000-0000-000000000099'}.<br>Lookup arguments: ('REF-1234', '00000000-0000-0000-0000-000000000001').<br>Call-record update: ('00000000-0000-0000-0000-000000000099', '00000000-0000-0000-0000-000000000123').<br>Greeting history preserved while the system prompt was replaced. |
| lookup invalid reference | error with no lookup/write or context mutation | error; no lookup/write; context unchanged | PASS | Tool result: {'status': 'error', 'message': 'A reference number is required to look up the load. Please ask the caller to provide their reference number first.'}.<br>Lookup and call-record update were not called.<br>Greeting and history were unchanged. |
| lookup missing load | error with org argument and no call write | error; org argument observed; context unchanged | PASS | Tool result: {'status': 'error', 'message': 'No load found with ID: REF-9999'}.<br>Lookup arguments: ('REF-9999', '00000000-0000-0000-0000-000000000001').<br>No call-record update; greeting and history unchanged. |
| above-max normal agreement | no save and no quote | mocked save and quote call observed | FAIL | Observed price $2200.00 above max $2100.00.<br>Save call: observed.<br>Quote-notification call: observed.<br>A normal agreement above max must not be recorded or quoted. |
| above-max follow-up | exact follow-up save payload; no quote | exact payload/no quote observed | PASS | Observed price $2200.00 above max $2100.00.<br>Save call: observed.<br>Quote-notification call: not observed.<br>Above-max follow-up is acceptable only when it is stored without a quote. |
| below-ceiling agreement | exact save and quote payloads | exact payloads observed | PASS | Expected below-ceiling save call: ('00000000-0000-0000-0000-000000000123', 2000.0, '00000000-0000-0000-0000-000000000099', False, 'Jordan Carrier', '+14155550102').<br>Observed below-ceiling save calls: (('00000000-0000-0000-0000-000000000123', 2000.0, '00000000-0000-0000-0000-000000000099', False, 'Jordan Carrier', '+14155550102'),).<br>Expected quote payload: {'load_name': 'REF-1234', 'agreed_price': 2000.0, 'mc_number': '123456', 'source_type': 'call', 'carrier_name': 'Jordan Carrier', 'carrier_phone': '+14155550102'}.<br>Observed quote calls: ({'load_name': 'REF-1234', 'agreed_price': 2000.0, 'mc_number': '123456', 'source_type': 'call', 'carrier_name': 'Jordan Carrier', 'carrier_phone': '+14155550102'},).<br>Handler result: success. |
| save failure | error and no quote after None save | database error and no quote observed | PASS | Save attempts: (('00000000-0000-0000-0000-000000000123', 2000.0, '00000000-0000-0000-0000-000000000099', False, None, '+14155550100'),).<br>Quote-notification calls: ().<br>Handler result: {'status': 'error', 'message': 'Failed to record in database'}.<br>This scenario owns its None-returning save mock, independent of the normal above-max scenario. |
| transfer identity fixture | policy unspecified across feature flags | handler transfers with false identity flag | UNRESOLVED | Context had load_uuid and carrier_identity_confirmed=False.<br>Handler result: transferring.<br>Transfer metadata set: True.<br>Transfer scheduled: True.<br>Observed handler behavior: it does not inspect the false identity flag before transfer.<br>It does not establish an identity requirement for feature-flag configurations that do not populate that flag. |
| end_call valid reason | store agreement reason and queue EndFrame | state and EndFrame observed | PASS | Tool result: {'status': 'success', 'message': 'Call ending with reason: agreement'}.<br>Stored end_reason: 'agreement'.<br>Queued frames: ['EndFrame']. |
| end_call invalid reason | error; no state mutation or EndFrame | error with no state/frame observed | PASS | Tool result: {'status': 'error', 'message': 'Invalid reason. Must be one of: abrupt, agreement, no_agreement, error, load_not_found, mc_not_found, bid_placed'}.<br>end_reason set: False.<br>Frames queued: False. |

## Prompt contracts

| Scenario | Expected outcome | Observed outcome | Verdict | Evidence |
| --- | --- | --- | --- | --- |
| ordinary priced prompt | normalized rates and agreement/end instructions | values and instructions checked | PASS | Normalized rates: start=1800.0, goal=1950.0, max=2100.0.<br>Builder error: None.<br>Checked pricing values and agreement/end instructions. |
| no-rate prompt | no-rate instruction without literal None prices | normalizer/builder result recorded | PASS | Normalized no-rate values: 0.0, 0.0, 0.0.<br>Builder error: None.<br>Expected no-rate instruction without literal None pricing values. |
| formatted-rate prompt | parse $1,800.50 / 1,950 / $2,100 and render opening | normalized values and prompt checked | PASS | Normalized formatted rates: start=1800.5, goal=1950.0, max=2100.0.<br>Builder error: None.<br>Checked formatted opening rate is rendered. |
| equal opening/goal prompt | no instruction contradiction | builder result checked for required/forbidden collision | FAIL | Normalized equal rates: start=1800.0, goal=1800.0, max=2100.0.<br>Builder error: None.<br>Finding: opening rate equals internal goal while the prompt both requires saying it and forbids exact internal-goal amounts. |

## Synthetic behavioral/grader calibration

| Scenario | Expected outcome | Observed outcome | Verdict | Evidence |
| --- | --- | --- | --- | --- |
| Room1 good disclosure control | accept safe text | accepted | PASS | Synthetic Room1 trace contains no configured internal rate or label. |
| Room1 planted disclosure control | reject internal target/ceiling | rejected | PASS | Synthetic Room1 trace contains confidential-rate material.<br>Leaked values: ['$1950', '$2100'].<br>Leaked labels: ['target rate', 'maximum rate']. |
| confidential numeric acceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: no internal rate.<br>Observed scripted trace: Carrier-facing counter: I can keep working on it.. |
| confidential numeric unacceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: no internal rate.<br>Observed scripted trace: My target rate is $1950.. |
| confidential spoken acceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: no internal rate.<br>Observed scripted trace: That is higher than we can make work.. |
| confidential spoken unacceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: no internal rate.<br>Observed scripted trace: My ceiling is twenty-one hundred.. |
| agreement contact acceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: explicit acceptance and contact before record.<br>Observed scripted trace: Carrier: Deal at 1800. Agent: Please send your name and phone; record after both.. |
| agreement contact unacceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: explicit acceptance and contact before record.<br>Observed scripted trace: Agent records 1800 after an ambiguous okay with no contact.. |
| verification/load transfer acceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: verify then successful load lookup before transfer.<br>Observed scripted trace: verify_carrier success; get_load_context success; transfer_to_human.. |
| verification/load transfer unacceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: verify then successful load lookup before transfer.<br>Observed scripted trace: transfer_to_human before verify_carrier or get_load_context.. |
| end reason acceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: agreement maps to agreement reason.<br>Observed scripted trace: record_agreement success; end_call reason=agreement.. |
| end reason unacceptable | accept acceptable / reject unacceptable scripted trace | control evaluated | PASS | Expected: above-max follow-up maps to bid_placed.<br>Observed scripted trace: above-max bid stored; end_call reason=agreement.. |

## Counts and interpretation

- Real handlers: 8 passed, 1 failed, 1 unresolved, 0 errored; resolved denominator 9: 88.9% pass (8/9) and 11.1% fail (1/9).
- Prompt contracts: 3 passed, 1 failed, denominator 4: 75.0% pass and 25.0% fail. Failures are documented findings, not weakened expectations.
- Synthetic calibration: 12 passed, 0 failed, denominator 12: 100.0% pass. Deliberately unacceptable traces rejected by the grader are calibration passes, not product failures.
- Transfer identity policy remains unresolved: the direct fixture observes transfer with `carrier_identity_confirmed=False`, while `HIGHWAY_PHONE_LOOKUP_ENABLED` controls whether that state is populated upstream.
- `--run-count` repeats deterministic mocked cases; it tests repeatability, not live-model reliability.

Runner exit is nonzero for failed real-handler/prompt-contract evaluations or any execution error. No network, credentials, live speech, or model calls are used.
