---
description: Add a new API tool/function to an existing Copilot Declarative Agent (4-file sync)
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
argument-hint: "[function_name]"
---

# Add API Tool to Copilot Declarative Agent

Add a new API function to an existing appPackage, keeping all four files in sync.

## Steps

1. **Locate the appPackage**: Find `appPackage/` or ask the user for the path.

2. **Read existing files** to understand current configuration:
   - `apiPlugin.json` — existing functions, runtimes, naming patterns
   - `apiDefinition.json` — existing paths, server URL, auth scheme
   - `declarativeAgent.json` — verify actions reference exists
   - `manifest.json` — current version number

3. **Gather function details** from the user (or argument):
   - Function name (snake_case, must match operationId)
   - What the function does (1-2 sentences)
   - Parameters (name, type, description, required)
   - Whether it's consequential (creates/updates/deletes data)
   - Reasoning instructions (parameter mappings, when to use)
   - Responding instructions (how to present results)

4. **Update apiPlugin.json** — Add to `functions` array:
   ```json
   {
     "name": "function_name",
     "description": "Brief description",
     "states": {
       "reasoning": {
         "description": "What this function returns",
         "instructions": ["Parameter and usage guidance"]
       },
       "responding": {
         "instructions": ["How to present results"]
       }
     }
   }
   ```
   Also add the function name to the appropriate `run_for_functions` array.

5. **Update apiDefinition.json** — Add OpenAPI path:
   - Match the existing path pattern (e.g., `/mcp/v1/autotask/{operationId}`)
   - Set `operationId` to exactly match the function name
   - Set `x-openai-isConsequential` appropriately (false for reads, true for writes)
   - Define requestBody schema with parameters
   - Define response schema

6. **Bump manifest.json version** (e.g., "1.0.8" → "1.0.9")

7. **Run validation** to verify sync:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_apppackage.py [path]
   ```

8. **Present summary** of changes and remind user to re-provision.

## Critical Sync Points
- `operationId` in apiDefinition.json **must exactly match** `name` in apiPlugin.json
- Function name **must appear** in `run_for_functions` of at least one runtime
- Missing any of the four file updates causes **silent failures**

## Tips
- Read `references/common-tasks.md` for the full 4-file sync workflow
- Read `references/instruction-architecture.md` for writing effective states
- Follow existing patterns in the appPackage for consistency
- Use `x-openai-isConsequential: false` for read-only queries
