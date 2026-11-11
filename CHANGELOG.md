# Changelog

## 1.4.0 — 2026-11-10

Declarative agent schema **v1.6 → v1.9**.

### Validator (`scripts/validate_apppackage.py`)
- Current versions: declarative agent `v1.9`, app manifest `1.30`, plugin manifest `v2.4` (unchanged — still Microsoft's latest).
- Older declarative agent versions (v1.0–v1.8) pass with a warning. Features newer than the declared version are flagged (errors for v1.7+ features, warnings for older ones).
- `$schema` URL must name the same version as `version`; `version` needs the `v` prefix.
- Unknown top-level properties are errors (Microsoft rejects the whole document).
- Capabilities: added `EmailActions`, `MeetingActions` (v1.8) and `Fabric` (v1.9). Unknown capabilities are now errors, duplicates are errors, and name-only capabilities reject extra properties. Warns when `Email` is scoped alongside `EmailActions`, since the scoping does not apply to it.
- Conversation starters: max 12 (v1.7+). v1.6 packages over 6 get a warning because Microsoft's v1.6 page says both 6 and 12.
- New `agent_skills` checks: max 8; `folder` only; relative, forward slashes, no `../`, inside the package, a directory, contains `SKILL.md`; SKILL.md frontmatter `name`/`description`, under 20,000 chars; allowed file types, depth ≤ 3, ≤ 350 files. Same checks for root `agentSkills` in manifest.json (1.28+).
- New v1.7 checks: `editorial_answers`, `behavior_overrides.default_response_mode`, `conversation_starters[].depends_on`.
- `RemoteMCPServer` runtimes are no longer treated as local OpenAPI files. Checks absolute `spec.url`, `mcp_tool_description` (`file` xor `tools`, tool shape), missing `auth`, and dynamic discovery (`functions: []` + `run_for_functions: ["*"]`). Wildcards in `run_for_functions` are honored.
- Plugin `$schema` accepts both the developer.microsoft.com and aka.ms URLs.
- UTF-8 console output on Windows.

### Tests
- `tests/fixtures/v1.6-basic` and `tests/fixtures/v1.9-skills-mcp` (agent skills, EmailActions, MeetingActions, Fabric, RemoteMCPServer with dynamic discovery).
- `tests/test_validate_apppackage.py`: 24 cases that mutate the v1.9 fixture and assert each check fires.

### Docs and commands
- `file-schemas.md`, `capabilities.md`, `validation.md`, `SKILL.md`, `common-tasks.md` and the complete reference updated to v1.9, with a new Agent Skills section, version history table, and EmailActions vs Email comparison.
- `update-schema`, `add-capability` and `create` commands target v1.9; `create` gains `--with-mcp` and `--with-skills`.

### Plugin format
- Hook now emits JSON `additionalContext` (plain stdout from a PostToolUse hook never reached Claude), runs via Python instead of `jq`, and matches Windows paths.
- Removed the unrecognized `whenToUse` agent field (folded into `description`).
- Removed `AskUserQuestion` from subagent tools (not available to subagents); the toolkit-create and toolkit-deploy commands now collect answers and publish confirmation before dispatching.
- `allowed-tools` uses the documented comma-separated form.
- `plugin.json`: added `homepage` and `repository`.
