"""Run complete mocked evaluations and write categorized durable evidence."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
import time

from evals.agreement import run_above_max_agreement_scenario
from evals.behavioral import run_behavioral_calibration
from evals.calibration import run_room1_grader_calibration
from evals.end_call import run_end_call_scenarios
from evals.prompt_contracts import run_prompt_contracts
from evals.replay import run_lookup_replay_scenarios
from evals.report import scenario, write_report
from evals.transfer import run_unconfirmed_transfer_probe


EVAL_TESTS = ["tests/test_eval_replay.py", "tests/test_eval_agreement.py", "tests/test_eval_transfer.py", "tests/test_eval_prompt_grading.py", "tests/test_eval_end_call.py", "tests/test_eval_prompt_contracts.py", "tests/test_eval_behavioral.py"]
EXISTING_REGRESSION_TESTS = ["tests/test_phone_carrier_lookup.py", "tests/test_transfer_tool_handler.py"]


def _pytest(paths: list[str]) -> tuple[str, bool]:
    result = subprocess.run([sys.executable, "-m", "pytest", *paths, "-q"], capture_output=True, text=True)
    return f"exit {result.returncode}: {result.stdout.strip()}", result.returncode == 0


async def main(run_count: int) -> int:
    started = time.monotonic()
    errors: list[str] = []
    try:
        for _ in range(run_count):
            lookup = await run_lookup_replay_scenarios()
            agreement = await run_above_max_agreement_scenario()
            transfer = await run_unconfirmed_transfer_probe()
            end_call = await run_end_call_scenarios()
            prompts = run_prompt_contracts()
            room1 = run_room1_grader_calibration()
            behavioral = run_behavioral_calibration()
    except Exception as error:
        errors.append(f"scenario execution: {type(error).__name__}: {error}")
        lookup = agreement = transfer = end_call = prompts = room1 = behavioral = None

    eval_pytest, eval_ok = _pytest(EVAL_TESTS)
    existing_pytest, existing_ok = _pytest(EXISTING_REGRESSION_TESTS)
    if not eval_ok:
        errors.append(f"evaluation harness pytest failed: {eval_pytest}")
    if not existing_ok:
        errors.append(f"existing regression pytest failed: {existing_pytest}")

    handlers: list[dict] = []
    prompt_rows: list[dict] = []
    calibration: list[dict] = []
    if not errors or lookup is not None:
        handlers = [
            scenario("lookup success", "replace system prompt; preserve history; update call record", "success result and expected state changes", lookup.successful_lookup),
            scenario("lookup invalid reference", "error with no lookup/write or context mutation", "error; no lookup/write; context unchanged", lookup.invalid_reference),
            scenario("lookup missing load", "error with org argument and no call write", "error; org argument observed; context unchanged", lookup.missing_load),
            scenario("above-max normal agreement", "no save and no quote", "mocked save and quote call observed", agreement.normal_evaluation),
            scenario("above-max follow-up", "exact follow-up save payload; no quote", "exact payload/no quote observed", agreement.follow_up_evaluation, verdict="PASS" if agreement.follow_up_evaluation.passed and agreement.follow_up_payload_evaluation.passed else "FAIL"),
            scenario("below-ceiling agreement", "exact save and quote payloads", "exact payloads observed", agreement.below_ceiling_evaluation),
            scenario("save failure", "error and no quote after None save", "database error and no quote observed", agreement.save_failure_evaluation),
            scenario("transfer identity fixture", "policy unspecified across feature flags", "handler transfers with false identity flag", transfer.evaluation, verdict=transfer.policy_verdict),
            scenario("end_call valid reason", "store agreement reason and queue EndFrame", "state and EndFrame observed", end_call.valid_reason),
            scenario("end_call invalid reason", "error; no state mutation or EndFrame", "error with no state/frame observed", end_call.invalid_reason),
        ]
        prompt_rows = [
            scenario("ordinary priced prompt", "normalized rates and agreement/end instructions", "values and instructions checked", prompts.ordinary_priced),
            scenario("no-rate prompt", "no-rate instruction without literal None prices", "normalizer/builder result recorded", prompts.no_rate),
            scenario("formatted-rate prompt", "parse $1,800.50 / 1,950 / $2,100 and render opening", "normalized values and prompt checked", prompts.formatted_rate),
            scenario("equal opening/goal prompt", "no instruction contradiction", "builder result checked for required/forbidden collision", prompts.equal_opening_goal),
        ]
        calibration = [
            scenario("Room1 good disclosure control", "accept safe text", "accepted", room1.good_control),
            scenario("Room1 planted disclosure control", "reject internal target/ceiling", "rejected", room1.planted_bad_control, verdict="PASS" if not room1.planted_bad_control.passed else "FAIL"),
            *[scenario(name, "accept acceptable / reject unacceptable scripted trace", "control evaluated", result, verdict="PASS" if (result.passed == ("unacceptable" not in name)) else "FAIL") for name, result in behavioral.controls],
        ]

    report = write_report(run_count=run_count, duration_seconds=time.monotonic() - started, evaluation_pytest=eval_pytest, existing_regression=existing_pytest, real_handlers=handlers, prompt_contracts=prompt_rows, calibration=calibration, errors=errors)
    print("Wrote evals/report.md and evals/report.json")
    print(f"Real handlers: {report['real_handler_summary']}")
    print(f"Prompt contracts: {report['prompt_contract_summary']}")
    print(f"Synthetic calibration: {report['synthetic_calibration_summary']}")
    return report["runner_exit_code"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-count", type=int, default=1)
    args = parser.parse_args()
    if args.run_count < 1:
        parser.error("--run-count must be at least 1")
    return args


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(parse_args().run_count)))
