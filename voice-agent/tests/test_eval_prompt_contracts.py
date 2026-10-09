"""Real normalizer/prompt-builder contract harness."""

from evals.prompt_contracts import run_prompt_contracts


def test_prompt_contracts_surface_findings_without_masking_them():
    report = run_prompt_contracts()
    assert report.ordinary_priced.passed is True
    assert report.formatted_rate.passed is True
    assert report.no_rate.passed is True
    # The equal-rate contradiction is intentionally represented in the CLI,
    # not asserted away as passing behavior here.
    assert report.equal_opening_goal.passed is False
