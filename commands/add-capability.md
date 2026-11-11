---
description: Add a capability (WebSearch, CodeInterpreter, EmailActions, Fabric, etc.) to an existing Copilot Declarative Agent
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: "[capability_name] [--path appPackage/]"
---

# Add Capability to Copilot Declarative Agent

Add one or more capabilities to an existing declarativeAgent.json, keeping the configuration valid.

## Available Capabilities (v1.9 Schema)

| # | Name | Config Required? | License Required? | Description |
|---|------|-----------------|-------------------|-------------|
| 1 | `WebSearch` | Optional (sites) | No | Web search grounding; optionally scope to 4 sites |
| 2 | `CodeInterpreter` | None | No | Python code execution for data analysis, charts, file generation |
| 3 | `GraphicArt` | None | No | Image/art generation from text descriptions |
| 4 | `OneDriveAndSharePoint` | Optional (URLs/IDs) | Yes | Search SharePoint/OneDrive files as knowledge |
| 5 | `GraphConnectors` | Required (connection_id) | Yes | Search org data via Copilot connectors |
| 6 | `Dataverse` | Required (host, skill, tables) | Yes | Query Dynamics 365/Dataverse tables |
| 7 | `TeamsMessages` | Optional (URLs) | Yes (license only) | Search Teams channels, chats, group chats |
| 8 | `Email` | Optional (mailbox, folders) | Yes (license only) | **Read-only** search of personal/shared mailboxes |
| 9 | `EmailActions` | None | Yes (license only) | Act on the mailbox: triage, send, delete, rules, auto-reply (v1.8) |
| 10 | `People` | Optional (include_related_content) | Yes (license only) | Org profiles, reporting chains, collaborators |
| 11 | `Meetings` | Optional (items_by_id) | Yes (license only) | Meeting transcripts, metadata, chat |
| 12 | `MeetingActions` | None | Yes (license only) | Schedule meetings, time-finding polls (v1.8) |
| 13 | `ScenarioModels` | Required (model id) | Yes | Task-specific fine-tuned models |
| 14 | `Fabric` | None | Yes | Microsoft Fabric grounding (v1.9) |

`EmbeddedKnowledge` is in the schema but not yet available. Max one of each capability per agent.

## Steps

1. **Locate the appPackage**: Find `declarativeAgent.json` using the argument path, or search for it:
   ```
   Glob for **/declarativeAgent.json
   ```
   If multiple found (e.g., `appPackage/` and `appPackage.dev/`), ask user which to update, or offer to update both.

2. **Read the current declarativeAgent.json** to understand:
   - Current schema version (v1.2+ for most capabilities, v1.5+ for Meetings, v1.6 for scoping, v1.8 for EmailActions/MeetingActions, v1.9 for Fabric)
   - Existing capabilities array
   - Whether the requested capability is already present

3. **Parse the requested capability** from the argument or ask the user:
   - If argument provided (e.g., `CodeInterpreter`), use it directly
   - If no argument, present the capabilities table above and ask which to add
   - Support adding multiple capabilities at once (comma-separated)

4. **EmailActions vs Email**: If the user wants the agent to archive, flag, move, send, delete or create rules, that is `EmailActions`, not `Email`. `Email` is read-only search. If `Email` is scoped (`shared_mailbox`, `group_mailboxes`, `folders`), tell the user that scoping does **not** limit `EmailActions`, and offer an instruction line that constrains write actions (for example: "Only act on messages in the Support folder. Confirm before sending or deleting.").

5. **Check for duplicates**: If the capability already exists in the `capabilities` array, inform the user and ask if they want to update its configuration instead.

6. **Check schema version**: If the current schema version is too old for the requested capability:
   - `Meetings` requires v1.5+
   - `People.include_related_content`, `GraphConnectors` filtering, `Email.group_mailboxes` require v1.6
   - `EmailActions`, `MeetingActions` require v1.8
   - `Fabric` requires v1.9
   - Offer to upgrade the schema version (reference the `update-schema` command)

7. **Gather configuration** based on capability type:

   **No config needed** (just add the object):
   - `CodeInterpreter` → `{ "name": "CodeInterpreter" }`
   - `GraphicArt` → `{ "name": "GraphicArt" }`
   - `People` → `{ "name": "People" }` (optionally ask about `include_related_content`)
   - `Meetings` → `{ "name": "Meetings" }` (optionally ask about scoping to specific meetings)
   - `EmailActions` → `{ "name": "EmailActions" }` — no properties allowed
   - `MeetingActions` → `{ "name": "MeetingActions" }` — no properties allowed
   - `Fabric` → `{ "name": "Fabric" }` — no properties allowed

   **Optional config** (works without, better with):
   - `WebSearch` → Ask if they want to scope to specific sites (max 4 URLs, max 2 path segments, no query params)
   - `OneDriveAndSharePoint` → Ask for SharePoint/OneDrive URLs or IDs (omit for all accessible content)
   - `TeamsMessages` → Ask for specific Teams channel/chat URLs (max 5, omit for all)
   - `Email` → Ask for shared mailbox SMTP, folder scoping

   **Required config** (must provide details):
   - `GraphConnectors` → Need `connection_id` at minimum
   - `Dataverse` → Need `host_name`, `skill` value, and table names
   - `ScenarioModels` → Need model `id`

8. **Add the capability** to the `capabilities` array in declarativeAgent.json:
   - Insert as a new object in the array
   - Preserve existing capabilities
   - Maintain JSON formatting consistency

9. **Update both environments** if applicable:
   - If both `appPackage/` and `appPackage.dev/` exist, ask if user wants to update both
   - Dev environment often gets capabilities first for testing

10. **Suggest instruction updates**: Some capabilities work better when referenced in the agent's `instructions` field:
   - `CodeInterpreter`: "Use code interpreter to analyze data, generate charts, or create files when needed."
   - `GraphicArt`: "Use the image generator to create visuals when the user requests diagrams or images."
   - `OneDriveAndSharePoint`: "Search SharePoint/OneDrive for relevant documents before answering."
   - `People`: "Use people knowledge to look up contact details and org structure."
   - `EmailActions`: "Confirm with the user before sending, deleting or creating inbox rules."
   - `MeetingActions`: "Propose times and confirm before sending a meeting invite."
   - Offer a `conversation_starters` entry with `depends_on` (v1.7+) so it only shows when the capability is enabled
   - Offer to add a relevant instruction line (but don't force it — not always needed)

11. **Run validation** to verify the change:
    ```bash
    python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_apppackage.py" [path]
    ```

12. **Present summary**:
    - What was added
    - Whether license is required for users
    - Remind to re-provision/redeploy the agent for changes to take effect
    - Note any instruction updates that were made

## Examples

### Simple (no-config capability)
```
/copilot-declarative-agent:add-capability CodeInterpreter
```
Adds `{ "name": "CodeInterpreter" }` to capabilities array.

### With configuration
```
/copilot-declarative-agent:add-capability WebSearch
```
Asks if user wants to scope to specific sites, then adds:
```json
{
  "name": "WebSearch",
  "sites": [
    { "url": "https://learn.microsoft.com" }
  ]
}
```

### Multiple capabilities
```
/copilot-declarative-agent:add-capability CodeInterpreter,GraphicArt,People
```
Adds all three to the capabilities array.

## Tips
- Read `references/capabilities.md` for full configuration details of each capability
- Read `references/knowledge-sources.md` for knowledge source best practices
- Less is more — focused agents with fewer capabilities perform better
- Microsoft's v1.9 reference says every capability except `WebSearch` needs a Microsoft 365 Copilot license or metered usage on the tenant
- When adding `OneDriveAndSharePoint`, permissions and sensitivity labels are respected — the agent only retrieves content the user can access
