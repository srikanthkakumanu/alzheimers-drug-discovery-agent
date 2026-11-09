# Claude Code setup

How this repository uses Claude Code as an authoring and review assistant. This is tooling for the design package, not the future application. Official references: [memory](https://code.claude.com/docs/en/memory), [skills](https://code.claude.com/docs/en/skills), [hooks](https://code.claude.com/docs/en/hooks), [settings](https://code.claude.com/docs/en/settings), [subagents](https://code.claude.com/docs/en/sub-agents) (last checked 2026-11-09).

## Surfaces in use
| Surface | Location | When it loads |
| --- | --- | --- |
| Root instructions | [CLAUDE.md](../CLAUDE.md) | Session start |
| Directory rules | `molecules/`, `experiments/`, `literature/` `CLAUDE.md` | When Claude reads files in that directory |
| Role contracts | `roles/<role>/CLAUDE.md` | When a role file is read (by a skill or on request) |
| Skills | `.claude/skills/<name>/SKILL.md` | Description always; body when invoked or selected |
| Commands | `.claude/commands/<name>.md` | On explicit `/name` |
| Stop hook | [.claude/settings.json](../.claude/settings.json) → [validate_on_stop.py](../.claude/hooks/validate_on_stop.py) | When Claude finishes a turn |

## Workflows
| Invocation | Purpose | Starts from |
| --- | --- | --- |
| `/research-status` | Phase, task, open decisions, next action | STATUS, TASK |
| `/neuroquest-review A G N` | Candidate comparison and gate check | Reviewer role, candidate index |
| `/neuroquest-evidence <claim>` | Sources, counterevidence, limits | Researcher role, literature index |
| `/neuroquest-plan <candidate> <gap>` | Proposed study concept | Planner role, candidate |
| `/validate-research` | Offline validator and tests | Local Python |

Skill frontmatter is JSON (valid YAML) with only `name` and `description`: no model override, tool pre-approval, or forked context. Arguments are treated as IDs or questions, never as shell code.

## Stop hook
Runs the dependency-free validator once when Claude stops. Silent on success. On failure it returns a bounded reason (≤1,600 characters, only `ERROR` lines) asking Claude to fix in-scope issues or report them. On the follow-up stop (`stop_hook_active: true`) it skips, preventing loops; so it is best-effort feedback, not an unbypassable gate. It makes no network or model calls and never reads `.env` or transcripts. The validator’s 15-second limit sits inside the 20-second hook timeout. Disabled hooks, untrusted projects, managed settings, or missing Python stop it from running.

To disable: remove the `Stop` entry from `.claude/settings.json`; CI and manual checks still work.

## Deliberately not used yet
| Feature | Reason |
| --- | --- |
| Native subagents (`.claude/agents/`) | Roles are design contracts until orchestration is decided ([ADR-004](../adr/ADR-004.md)) |
| MCP servers (`.mcp.json`) | No connector selected ([ADR-008](../adr/ADR-008.md)) |
| Always-loaded `.claude/rules/` | Directory `CLAUDE.md` files already scope rules to where they apply |
| Permission pre-approvals, model overrides | Not needed for document work |

## Verify locally
Start Claude Code at the repository root and trust the project. Use `/hooks` to see the Stop hook and `/` to list the five workflows; `/research-status` is a cheap first check. Outside Claude: `python3 scripts/validate_repository.py` and `python3 -m unittest discover -s tests -v`. The validator also checks that the three skills and two commands exist with minimal metadata; renaming or removing one requires an intentional validator change.
