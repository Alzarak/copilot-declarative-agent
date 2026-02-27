---
description: Scaffold a new Microsoft 365 Copilot Declarative Agent appPackage from scratch
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep"]
argument-hint: "[path] [--with-api] [--typespec]"
---

# Create a New Copilot Declarative Agent

Scaffold a complete appPackage directory for a Microsoft 365 Copilot Declarative Agent.

## Steps

1. **Determine output path**: Use the argument if provided, otherwise default to `appPackage/` in the current project root. If the directory already exists, warn the user and ask before overwriting.

2. **Gather requirements** by asking the user:
   - Agent name (short, max 30 chars for manifest)
   - Agent purpose (1-2 sentences)
   - Which capabilities to enable (WebSearch, CodeInterpreter, GraphicArt, OneDriveAndSharePoint, etc.)
   - Whether API actions are needed (`--with-api` flag or ask)
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
   ├── apiPlugin.json     (if --with-api)
   └── apiDefinition.json (if --with-api)
   ```

5. **Write manifest.json** following the schema in `references/file-schemas.md`:
   - Use manifestVersion "1.24"
   - Fill in name, description from user input
   - Set placeholder developer info (ask user or use defaults)
   - Reference declarativeAgent.json

6. **Write declarativeAgent.json** with v1.6 schema:
   - Set version to "v1.6"
   - Write instructions using the Goal/Action/Transition pattern from `references/instruction-architecture.md`
   - Add selected capabilities
   - Add 3-6 conversation starters relevant to the agent purpose
   - If API actions: add actions array referencing apiPlugin.json

7. **If --with-api**: Write apiPlugin.json and apiDefinition.json scaffolds:
   - Use schema_version "v2.4"
   - Include one example function with states (reasoning/responding)
   - Include OAuthPluginVault auth scaffold
   - Write OpenAPI 3.0.0 spec with matching operationId

8. **If --typespec**: Create main.tsp instead of manual JSON:
   - Reference `references/typespec.md` for decorator syntax

9. **Create placeholder icons**:
   - Generate minimal PNG files or remind user to add real icons
   - color.png: 192x192 px
   - outline.png: 32x32 px

10. **Run validation** on the generated package:
    ```bash
    python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_apppackage.py [output_path]
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
- Keep instructions focused — use Goal/Action/Transition pattern
- Start with fewer capabilities, add more as needed
