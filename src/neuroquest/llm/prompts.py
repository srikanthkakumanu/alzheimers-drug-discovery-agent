"""Compose system prompts from shared rules + role contracts (docs/architecture/prompt-design.md).

Role contracts in roles/<role>/CLAUDE.md are the single source of truth for both
Claude Code and the application. Order is stable-first to benefit prefix caching.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from neuroquest.models.records import Candidate, Experiment

Role = Literal["researcher", "reviewer", "planner", "regulatory", "portfolio"]
TEMPLATE_VERSION = "1"
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


@dataclass(frozen=True, slots=True)
class ComposedPrompt:
    text: str
    version: str


def shared_rules() -> str:
    return resources.files("neuroquest.prompts").joinpath("shared.md").read_text(encoding="utf-8")


def role_contract(repo_root: Path, role: Role) -> str:
    """Role contract with repository navigation links reduced to their labels."""
    text = (repo_root / "roles" / role / "CLAUDE.md").read_text(encoding="utf-8")
    return _LINK.sub(r"\1", text)


def system_prompt(repo_root: Path, role: Role, output_model: type[BaseModel]) -> ComposedPrompt:
    schema = json.dumps(output_model.model_json_schema(), sort_keys=True)
    parts = [
        shared_rules(),
        f"# Your role contract\n\n{role_contract(repo_root, role)}",
        f"# Output\n\nReturn a {output_model.__name__} object. Every field is required; use empty lists "
        "when nothing applies.",
    ]
    digest = hashlib.sha256("\n".join([*parts, schema]).encode()).hexdigest()[:12]
    return ComposedPrompt(text="\n\n".join(parts), version=f"{role}-v{TEMPLATE_VERSION}-{digest}")


def _neutralize(body: str) -> str:
    """Record text cannot open or close an evidence block, so it cannot escape the data wrapper (EV-11)."""
    return re.sub(r"<\s*(/?)\s*evidence", r"&lt;\1evidence", body, flags=re.IGNORECASE)


def evidence_block(candidates: list[Candidate], experiments: list[Experiment]) -> str:
    """Untrusted record text wrapped in explicit delimiters."""
    blocks = [f'<evidence id="{c.id}" provenance="synthetic">\n{_neutralize(c.body)}\n</evidence>' for c in candidates]
    blocks += [
        f'<evidence id="{e.id}" provenance="synthetic">\n{_neutralize(e.body)}\n</evidence>' for e in experiments
    ]
    return "\n\n".join(blocks)
