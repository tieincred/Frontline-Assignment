"""Run the currently implemented offline agreement evaluation."""

from __future__ import annotations

import asyncio

from evals.agreement import run_above_max_agreement_scenario
from evals.calibration import run_room1_grader_calibration
from evals.transfer import run_unconfirmed_transfer_probe


def _print_evaluation(label, evaluation) -> None:
    status = "PASS" if evaluation.passed else "FAIL"
    print(f"{label}: {status}")
    for item in evaluation.evidence:
        print(f"  - {item}")


async def main() -> int:
    agreement = await run_above_max_agreement_scenario()
    transfer = await run_unconfirmed_transfer_probe()
    calibration = run_room1_grader_calibration()

    print("Real handler probes")
    print("Above-max agreement")
    print(f"normal save calls: {agreement.normal_save_calls}")
    print(f"normal quote calls: {agreement.normal_quote_calls}")
    print(f"follow-up save calls: {agreement.follow_up_save_calls}")
    print(f"follow-up quote calls: {agreement.follow_up_quote_calls}")
    _print_evaluation("normal agreement path", agreement.normal_evaluation)
    _print_evaluation("above-max follow-up path", agreement.follow_up_evaluation)
    print("Unconfirmed transfer")
    _print_evaluation("transfer identity guard", transfer.evaluation)

    print("Synthetic grader calibration (planted controls, not product observations)")
    _print_evaluation("Room1 good control", calibration.good_control)
    _print_evaluation("Room1 planted bad control", calibration.planted_bad_control)

    handler_failures = (
        not agreement.normal_evaluation.passed
        or not agreement.follow_up_evaluation.passed
        or not transfer.evaluation.passed
    )
    calibration_failed = (
        not calibration.good_control.passed or calibration.planted_bad_control.passed
    )
    if handler_failures:
        print("Unsafe real handler behavior observed.")
    if calibration_failed:
        print("Synthetic grader calibration failed.")
    return int(handler_failures or calibration_failed)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
