---
description: Update appPackage schema versions to the latest supported versions (declarative agent v1.9)
allowed-tools: Read, Edit, Bash, Glob
argument-hint: "[path_to_apppackage]"
---

# Update Schema Versions

Check and update all schema versions in an appPackage to the latest supported versions.

## Current Versions

| File | Field | Current Version | Schema URL |
|------|-------|-----------------|------------|
| manifest.json | `manifestVersion` | `1.30` | `https://developer.microsoft.com/json-schemas/teams/v1.30/MicrosoftTeams.schema.json` |
| manifest.json | `$schema` | (same URL) | |
| declarativeAgent.json | `version` | `v1.9` | `https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.9/schema.json` |
| declarativeAgent.json | `$schema` | (same URL — must match `version`) | |
| apiPlugin.json | `schema_version` | `v2.4` | `https://developer.microsoft.com/json-schemas/copilot/plugin/v2.4/schema.json` |
| apiDefinition.json | `openapi` | `3.0.0` | OpenAPI specification |

Older versions still validate (with a warning). Upgrading is only required to use a newer feature.

## What Each Declarative Agent Version Adds

| Version | New features |
|---------|--------------|
| v1.9 | `agent_skills` (max 8 SKILL.md folders), `Fabric` capability |
| v1.8 | `EmailActions`, `MeetingActions` capabilities |
| v1.7 | `editorial_answers`, `behavior_overrides.default_response_mode`, `conversation_starters[].depends_on`, conversation starters max 12 |
| v1.6 | `sensitivity_label`, `worker_agents`, `user_overrides`, `EmbeddedKnowledge`, scoping for Meetings/People/Email |

## Steps

1. **Locate the appPackage** and read all JSON files.

2. **Check each file** for outdated schema versions. Note that `$schema` and `version` in declarativeAgent.json must name the same version.

3. **Present findings**:
   - Which files need updates
   - Current version → target version
   - New features available between the two versions (table above)

4. **Update versions** (after user confirmation):
   - Update `manifestVersion` and `$schema` in manifest.json
   - Update `version` and `$schema` in declarativeAgent.json — keep the `v` prefix (`"v1.9"`)
   - Update `schema_version` and `$schema` in each apiPlugin file (already v2.4 is current)

5. **Check compatibility after the bump** — upgrading never removes properties, but confirm:
   - No unrecognized top-level properties (v1.9 rejects any property not in the schema)
   - `worker_agents` items still have `id`
   - `EmbeddedKnowledge` has `files` (required from v1.8)

6. **Offer the features the new version unlocks**:
   - `agent_skills` — reusable SKILL.md folders inside the package (see `references/file-schemas.md` → Agent Skills). Agents Toolkit needs `TEAMSFX_AGENT_SKILLS=true`.
   - `EmailActions` — mailbox write actions. Separate from the read-only `Email` capability, and `Email` scoping does not apply to it.
   - `MeetingActions` — scheduling and time-finding.
   - `Fabric` — Microsoft Fabric grounding.
   - `editorial_answers`, `default_response_mode`, `conversation_starters[].depends_on`
   - Conversation starters can go up to 12.

7. **Bump manifest.json version** number.

8. **Run validation** to confirm everything is correct:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_apppackage.py" [path]
   ```

## Tips
- Read `references/file-schemas.md` for complete schema details
- Updating schema versions may enable new features but shouldn't break existing ones
- Always test after updating — re-provision and verify in Copilot
- Root-level `agentSkills` in manifest.json needs manifestVersion 1.28+; prefer `agent_skills` in declarativeAgent.json
