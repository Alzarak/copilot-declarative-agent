---
description: Update appPackage schema versions to the latest supported versions
allowed-tools: ["Read", "Edit", "Bash", "Glob"]
argument-hint: "[path_to_apppackage]"
---

# Update Schema Versions

Check and update all schema versions in an appPackage to the latest supported versions.

## Current Versions

| File | Field | Current Version | Schema URL |
|------|-------|-----------------|------------|
| manifest.json | `manifestVersion` | `1.24` | `https://developer.microsoft.com/json-schemas/teams/v1.24/MicrosoftTeams.schema.json` |
| manifest.json | `$schema` | (same URL) | |
| declarativeAgent.json | `version` | `v1.6` | `https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.6/schema.json` |
| declarativeAgent.json | `$schema` | (same URL) | |
| apiPlugin.json | `schema_version` | `v2.4` | `https://aka.ms/json-schemas/copilot/plugin/v2.4/schema.json` |
| apiDefinition.json | `openapi` | `3.0.0` | OpenAPI specification |

## Steps

1. **Locate the appPackage** and read all JSON files.

2. **Check each file** for outdated schema versions.

3. **Present findings**:
   - Which files need updates
   - Current version → target version
   - Any new features available in the new version

4. **Update versions** (after user confirmation):
   - Update `manifestVersion` and `$schema` in manifest.json
   - Update `version` and `$schema` in declarativeAgent.json
   - Update `schema_version` in apiPlugin.json

5. **Check for new v1.6 features** the user might want to adopt:
   - `behavior_overrides` (suggestions, discourage_model_knowledge)
   - `disclaimer` (conversation start text)
   - `worker_agents` (multi-agent orchestration, preview)
   - `user_overrides` (let users toggle capabilities)
   - New capabilities (CodeInterpreter, GraphicArt, Email, People, etc.)
   - Conversation starters limit reduced to 6 (check compliance)

6. **Bump manifest.json version** number.

7. **Run validation** to confirm everything is correct.

## Tips
- Read `references/file-schemas.md` for complete schema details
- Updating schema versions may enable new features but shouldn't break existing ones
- Always test after updating — re-provision and verify in Copilot
- Check conversation_starters count (v1.6 limit is 6, down from 12)
