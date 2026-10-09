"""Run the currently implemented offline agreement evaluation."""

from __future__ import annotations

import asyncio

from evals.agreement import run_above_max_agreement_scenario


def _print_evaluation(label, evaluation) -> None:
    status = "PASS" if evaluation.passed else "FAIL"
    print(f"{label}: {status}")
    for item in evaluation.evidence:
        print(f"  - {item}")


async def main() -> int:
    report = await run_above_max_agreement_scenario()
    print("Above-max agreement evaluation")
    print(f"save_agreement calls: {report.save_calls}")
    print(f"notify_carrier_quote calls: {report.quote_calls}")
    _print_evaluation("normal agreement path", report.normal_evaluation)
    _print_evaluation("above-max follow-up path", report.follow_up_evaluation)

    if not report.normal_evaluation.passed:
        print("Unsafe above-max normal-agreement behavior observed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
