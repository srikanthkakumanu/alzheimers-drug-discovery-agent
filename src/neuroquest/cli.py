"""`neuroquest` command-line interface (ADR-011; docs/architecture/application-design.md#cli).

Exit codes: 0 ok · 1 internal error · 3 partial result · 4 invalid input or configuration ·
5 decision conflict.
"""

from __future__ import annotations

import getpass
import subprocess
import sys
from pathlib import Path
from typing import Annotated, get_args

import typer

from neuroquest.errors import (
    ConfigurationError,
    DecisionError,
    NeuroQuestError,
    RecordFormatError,
    UnknownRecordError,
)
from neuroquest.llm.base import LLMClient
from neuroquest.models.runs import HumanDisposition, RunStatus
from neuroquest.service import ReviewService
from neuroquest.settings import Settings

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Evidence-grounded review of SYNTHETIC DEMONSTRATION Alzheimer's candidates.",
)

EXIT_PARTIAL, EXIT_INPUT, EXIT_CONFLICT = 3, 4, 5


def make_llm(settings: Settings) -> LLMClient:
    """Factory seam: tests replace this to avoid network calls."""
    from neuroquest.llm.openai_client import OpenAIClient

    return OpenAIClient(settings)


def _service() -> ReviewService:
    settings = Settings()
    settings.export_tracing_env()
    return ReviewService(settings, lambda: make_llm(settings))


def _fail(message: str, code: int) -> typer.Exit:
    typer.secho(f"Error: {message}", err=True, fg=typer.colors.RED)
    return typer.Exit(code)


def _parse_dispositions(values: list[str]) -> dict[str, HumanDisposition]:
    allowed = get_args(HumanDisposition)
    parsed: dict[str, HumanDisposition] = {}
    for value in values:
        ref, sep, disposition = value.partition("=")
        if not sep or disposition not in allowed:
            raise DecisionError(f"Use CANDIDATE=DISPOSITION with one of {', '.join(allowed)}; got {value!r}.")
        parsed[ref] = disposition  # type: ignore[assignment]  # checked against allowed above
    return parsed


@app.command()
def review(
    ids: Annotated[list[str], typer.Argument(help="Candidate IDs, e.g. A G N")],
    question: Annotated[str | None, typer.Option(help="Research question for the packet")] = None,
    budget_usd: Annotated[float | None, typer.Option(min=0.001, help="Override the per-run cap")] = None,
    out: Annotated[Path | None, typer.Option(help="Also write the packet to this file")] = None,
) -> None:
    """Run reviewer and portfolio steps, then pause for a human decision."""
    try:
        service = _service()
        try:
            outcome = service.review(ids, question, budget_usd)
        finally:
            service.close()
    except (UnknownRecordError, ConfigurationError, RecordFormatError) as exc:
        raise _fail(str(exc), EXIT_INPUT) from exc
    except NeuroQuestError as exc:
        raise _fail(str(exc), 1) from exc
    typer.echo(outcome.packet_markdown)
    if out:
        out.write_text(outcome.packet_markdown, encoding="utf-8")
    typer.echo(f"run_id: {outcome.run_id} · status: {outcome.status} · cost: ${outcome.cost_usd:.4f}", err=True)
    if outcome.status == "partial":
        raise typer.Exit(EXIT_PARTIAL)


@app.command()
def decide(
    run_id: Annotated[str, typer.Argument(help="Run awaiting a human decision")],
    disposition: Annotated[list[str], typer.Option("--disposition", "-d", help="CANDIDATE=DISPOSITION")],
    reason: Annotated[str, typer.Option(help="Why you decided this")],
) -> None:
    """Record your decision for one or more candidates and close the run."""
    try:
        parsed = _parse_dispositions(disposition)
        service = _service_without_model()
        try:
            outcome = service.decide(run_id, parsed, reason, getpass.getuser())
        finally:
            service.close()
    except DecisionError as exc:
        raise _fail(str(exc), EXIT_CONFLICT) from exc
    except (UnknownRecordError, ConfigurationError) as exc:
        raise _fail(str(exc), EXIT_INPUT) from exc
    typer.echo(outcome.packet_markdown)


def _service_without_model() -> ReviewService:
    def unavailable() -> LLMClient:
        raise ConfigurationError("Recording a decision does not use a model.")

    return ReviewService(Settings(), unavailable)


@app.command()
def runs(
    status: Annotated[str | None, typer.Option(help="Filter by status")] = None,
    limit: Annotated[int, typer.Option(min=1, max=200)] = 20,
) -> None:
    """List recent runs."""
    if status is not None and status not in get_args(RunStatus):
        raise _fail(f"Unknown status {status!r}.", EXIT_INPUT)
    service = _service_without_model()
    try:
        records = service.runs(status, limit)  # type: ignore[arg-type]  # validated above
    finally:
        service.close()
    for r in records:
        typer.echo(
            f"{r.run_id}  {r.status:<15} ${r.cost_usd:.4f}  "
            f"{' '.join(c.removeprefix('candidate-') for c in r.candidate_ids)}  {r.question[:60]}"
        )


@app.command()
def show(run_id: str) -> None:
    """Print a run's decision packet."""
    service = _service_without_model()
    try:
        record = service.run(run_id)
    except UnknownRecordError as exc:
        raise _fail(str(exc), EXIT_INPUT) from exc
    finally:
        service.close()
    typer.echo(record.packet_markdown or f"Run {run_id} has no packet (status {record.status}).")


@app.command()
def validate() -> None:
    """Run the offline repository validator."""
    root = Settings().resolved_repo_root()
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "validate_repository.py"), "--root", str(root)], check=False
    )
    raise typer.Exit(result.returncode)
