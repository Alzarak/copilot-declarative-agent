---
description: Scaffold a new Microsoft 365 Copilot Declarative Agent appPackage from scratch
allowed-tools: Read, Write, Bash, Glob, Grep
argument-hint: "[path] [--with-api] [--with-mcp] [--with-skills] [--typespec]"
---

# Create a New Copilot Declarative Agent

Scaffold a complete appPackage directory for a Microsoft 365 Copilot Declarative Agent.

## Steps

1. **Determine output path**: Use the argument if provided, otherwise default to `appPackage/` in the current project root. If the directory already exists, warn the user and ask before overwriting.

2. **Gather requirements** by asking the user:
   - Agent name (short, max 30 chars for manifest)
   - Agent purpose (1-2 sentences)
   - Which capabilities to enable (WebSearch, CodeInterpreter, GraphicArt, OneDriveAndSharePoint, Email, EmailActions, MeetingActions, Fabric, etc.). If the agent must act on mail (archive, send, rules), that is `EmailActions` — `Email` alone is read-only
   - Whether API actions are needed (`--with-api` flag or ask)
   - Whether a Remote MCP server action is needed (`--with-mcp` flag or ask) — get its https URL and auth type
   - Whether the agent needs agent skills (`--with-skills` flag or ask) — reusable SKILL.md playbooks, max 8
   - Whether to use TypeSpec (`--typespec` flag or ask)

3. **Generate UUID** for the manifest:
   ```bash
   uuidgen | tr '[:upper:]' '[:lower:]'
   ```

4. **Create the appPackage directory structure**:
   ```
   appPackage/
   ├── manifest.json
   ├── declarativeAgent.json
   ├── color.png          (placeholder - remind user to replace)
   ├── outline.png        (placeholder - remind user to replace)
   ├── apiPlugin.json     (if --with-api or --with-mcp)
   ├── apiDefinition.json (if --with-api)
   └── skills/            (if --with-skills)
       └── <skill-name>/SKILL.md
   ```

5. **Write manifest.json** following the schema in `references/file-schemas.md`:
   - Use manifestVersion "1.30" with the matching `$schema` URL
   - Fill in name, description from user input
   - Set placeholder developer info (ask user or use defaults)
   - Reference declarativeAgent.json

6. **Write declarativeAgent.json** with v1.9 schema:
   - Set version to "v1.9" and `$schema` to `https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.9/schema.json`
   - Write instructions using the Goal/Action/Transition pattern from `references/instruction-architecture.md`
   - Add selected capabilities
   - Add 3-6 conversation starters relevant to the agent purpose (max 12); use `depends_on` for starters that need a specific capability
   - Do not add properties outside the schema — any unknown property invalidates the file
   - If API actions: add actions array referencing apiPlugin.json

7. **If --with-api**: Write apiPlugin.json and apiDefinition.json scaffolds:
   - Use schema_version "v2.4"
   - Include one example function with states (reasoning/responding)
   - Include OAuthPluginVault auth scaffold
   - Write OpenAPI 3.0.0 spec with matching operationId

7a. **If --with-mcp**: Write an apiPlugin file with a `RemoteMCPServer` runtime (see `references/file-schemas.md` → RemoteMCPServer Runtime):
   - `spec.url` is the server's absolute https URL
   - Always include `auth` (`{ "type": "None" }`, `OAuthPluginVault` or `ApiKeyPluginVault` with `reference_id`)
   - Dynamic discovery: `"functions": []` and `"run_for_functions": ["*"]`; or pin tools in `functions` with definitions in `mcp_tool_description`
   - Add `{ "id": "<pluginId>", "file": "<plugin file>" }` to `actions`

7b. **If --with-skills**: For each skill (max 8):
   - Create `appPackage/skills/<skill-name>/SKILL.md` with YAML frontmatter `name` (lowercase-hyphen, same as the folder) and `description`, then the instructions (under 20,000 characters)
   - Put supporting files in `references/` or `scripts/` (allowed types only, max 3 levels deep; scripts run sandboxed with no network)
   - Add `{ "folder": "skills/<skill-name>" }` to `agent_skills` — relative, forward slashes, no `../`
   - Tell the user Agents Toolkit needs `TEAMSFX_AGENT_SKILLS=true`

8. **If --typespec**: Create main.tsp instead of manual JSON:
   - Reference `references/typespec.md` for decorator syntax

9. **Create placeholder icons**:
   - Generate minimal PNG files or remind user to add real icons
   - color.png: 192x192 px
   - outline.png: 32x32 px

10. **Run validation** on the generated package:
    ```bash
    python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_apppackage.py" [output_path]
    ```

11. **Present summary** of created files and next steps:
    - How to provision with Agents Toolkit
    - How to test in M365 Copilot
    - Remind about replacing placeholder icons
    - Remind about configuring Azure AD if using API actions

## Tips
- Read `references/file-schemas.md` for complete schema details
- Read `references/capabilities.md` before adding capabilities
- Read `references/instruction-architecture.md` for instruction best practices
- Read `references/file-schemas.md` → Agent Skills before writing SKILL.md folders
- Keep instructions focused — use Goal/Action/Transition pattern
- Start with fewer capabilities, add more as needed
