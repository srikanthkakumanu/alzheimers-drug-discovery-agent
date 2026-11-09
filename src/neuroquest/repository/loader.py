"""Load evidence records (JSON frontmatter + Markdown body) into typed models."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from neuroquest.errors import RecordFormatError, UnknownRecordError
from neuroquest.models.records import (
    DIMENSIONS,
    Candidate,
    CandidateId,
    Experiment,
    ExperimentId,
    Paper,
    PaperId,
)
from neuroquest.models.scoring import ScoringModel

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^# (.+)$", re.M)


def split_record(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter, body). Frontmatter is JSON, a YAML subset."""
    match = FRONTMATTER.match(text)
    if not match:
        raise RecordFormatError("missing JSON frontmatter")
    meta = json.loads(match.group(1))
    if not isinstance(meta, dict):
        raise RecordFormatError("frontmatter must be a JSON object")
    return meta, text[match.end() :].strip()


def _load[M: BaseModel](path: Path, model: type[M]) -> M:
    meta, body = split_record(path.read_text(encoding="utf-8"))
    heading = HEADING.search(body)
    try:
        return model.model_validate({**meta, "title": heading.group(1) if heading else "", "body": body})
    except ValidationError as exc:
        raise RecordFormatError(f"{path.name}: {exc.error_count()} contract violation(s): {exc}") from exc


class Repository:
    """Immutable snapshot of candidates, experiments, papers, and the scoring model."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.scoring = ScoringModel.model_validate_json(
            (root / "config" / "scoring-model.json").read_text(encoding="utf-8")
        )
        self.candidates: dict[CandidateId, Candidate] = {
            c.id: c for c in self._load_all("molecules", "candidate-*.md", Candidate)
        }
        self.experiments: dict[ExperimentId, Experiment] = {
            e.id: e for e in self._load_all("experiments", "EXP-*.md", Experiment)
        }
        self.papers: dict[PaperId, Paper] = {p.id: p for p in self._load_all("literature", "paper-*.md", Paper)}

    def _load_all[M: BaseModel](self, folder: str, pattern: str, model: type[M]) -> Iterable[M]:
        return [_load(path, model) for path in sorted((self.root / folder).glob(pattern))]

    def resolve_candidate(self, ref: str) -> CandidateId:
        """Accept 'A', 'a', or 'candidate-A'; never guess a similar ID."""
        cleaned = ref.strip()
        key = CandidateId(cleaned if cleaned.startswith("candidate-") else f"candidate-{cleaned.upper()}")
        if key not in self.candidates:
            raise UnknownRecordError(
                f"Unknown candidate {ref!r}. Known: " + ", ".join(c.letter for c in self.candidates.values())
            )
        return key

    def candidate(self, candidate_id: CandidateId) -> Candidate:
        try:
            return self.candidates[candidate_id]
        except KeyError as exc:
            raise UnknownRecordError(f"Unknown candidate {candidate_id!r}") from exc

    def evidence_for(self, candidate_ids: Iterable[CandidateId], limit: int) -> list[Experiment]:
        """Most decision-relevant experiments first: challengers, then efficacy, then other ratings."""
        ordered: list[ExperimentId] = []
        candidates = [self.candidate(cid) for cid in candidate_ids]
        for candidate in candidates:
            ordered += [h.challenged_by for h in candidate.score_history]
        for dimension in DIMENSIONS:
            for candidate in candidates:
                ordered += candidate.rating_evidence.for_dimension(dimension)
        unique = list(dict.fromkeys(ordered))
        return [self.experiments[e] for e in unique[:limit] if e in self.experiments]
