# Common Tasks

This reference covers all common agent creation/modification workflows.

## Three Approaches to Building

### Agent Builder (No-Code UI)
Available in the Microsoft 365 Copilot app via left pane > "Create agent". Two modes:
- **Describe Tab**: Natural language — auto-generates name, description, instructions. Changes saved per conversation turn. Only available in supported languages.
- **Configure Tab**: Manual control over Name (30 chars), Icon, Description (1,000 chars), Instructions (8,000 chars), Knowledge, Capabilities, Starter Prompts.
- **Test Pane**: Ephemeral agent for testing (available after name+description+instructions set). Cannot share prompts or @mention other agents.
- **Templates**: Pre-configured templates that can be customized.
- **Limitations**: No API actions, no behavior_overrides/disclaimer/worker_agents/user_overrides, no Adaptive Cards, no sensitivity labels, no MCP server integration.

### Microsoft 365 Agents Toolkit (Code-First, VS Code)
**Prerequisites**: VS Code, M365 Agents Toolkit extension v6.0+, Copilot license or developer sandbox.
**Steps**:
1. Open VS Code
2. Select "Microsoft 365 Agents Toolkit" > "Create a New Agent/App"
3. Select "Declarative Agent"
4. Choose "No Action" (basic) or "Start with TypeSpec" (TypeSpec-based)
5. Select default folder, enter application name
6. In the Lifecycle pane, select "Provision" to deploy
**Testing**: Go to `https://m365.cloud.microsoft/chat`, click conversation drawer, select your agent.
**F5 Preview**: Select "Preview your app (F5)" for browser-based Copilot Chat with developer mode debugging.
**Note**: Government tenants (GCC) do NOT support publishing via Agents Toolkit.

### Manual JSON (Hand-Crafted)
Most flexible, requires full schema knowledge. Best for CI/CD integration and version control.

## Creating a New Agent (Manual JSON)

1. Create `appPackage/` directory
2. Generate UUID for `manifest.json` `id` field
3. Write `manifest.json` with developer info, name, description, icons, copilotAgents reference
4. Write `declarativeAgent.json` with name, description, instructions (use Markdown), capabilities, conversation_starters
5. If API actions needed: create `apiPlugin.json` + `apiDefinition.json` + add action reference in declarativeAgent.json
6. Add `color.png` (192x192) and `outline.png` (32x32)
7. Bump version, provision/deploy

**Icon requirements**: PNG format, transparent background recommended. Color icon 192x192 px, outline icon 32x32 px. Max 1 MB file size.

## Adding a New API Tool (4-File Sync)

Update four files in sync — this is the most error-prone task:

### Step 1: Add function to apiPlugin.json
```json
{
  "name": "newFunction",
  "description": "What this function does.",
  "states": {
    "reasoning": {
      "instructions": [
        "When to call this function.",
        "How to map user language to parameters."
      ]
    },
    "responding": {
      "instructions": [
        "How to format the response."
      ]
    }
  }
}
```

### Step 2: Add to run_for_functions in runtime
```json
"run_for_functions": ["existingFunction", "newFunction"]
```

### Step 3: Add OpenAPI path to apiDefinition.json
```json
"/api/v1/resource/newFunction": {
  "post": {
    "operationId": "newFunction",
    "summary": "Description",
    "x-openai-isConsequential": false,
    "requestBody": { ... },
    "responses": { ... }
  }
}
```

### Step 4: Bump version in manifest.json
```json
"version": "1.0.1"
```

**Critical sync rules**:
- `operationId` must match function `name` exactly
- Function must be in `run_for_functions`
- `x-openai-isConsequential`: `false` for read-only, `true` for create/update/delete
- Run validation after changes

## Adding Conversation Starters

```json
"conversation_starters": [
  { "title": "Find tickets", "text": "Show me all open high-priority tickets" },
  { "title": "Create report", "text": "Generate a monthly summary report" },
  { "title": "Check status", "text": "What's the status of ticket #12345?" }
]
```

- Max **6** items (v1.6 limit, reduced from 12)
- Include minimum 3 sample prompts reflecting core capabilities
- Show realistic, useful examples covering different capabilities
- Keep titles 2-3 words

## Configuring Behavior Overrides (v1.6)

```json
{
  "behavior_overrides": {
    "suggestions": { "disabled": true },
    "special_instructions": { "discourage_model_knowledge": true }
  }
}
```

- `suggestions.disabled`: Disables follow-up suggestion feature
- `discourage_model_knowledge`: Agent does not use general model knowledge when generating responses

## Adding Worker Agents (v1.6, Preview)

```json
{ "worker_agents": [{ "id": "P_2c27ae89-1f78-4ef7-824c-7d83f77eda28" }] }
```

The `id` is the title ID of the other agent's application (from publishing or developer mode metadata).

## Adding User Overrides (v1.6)

```json
{
  "user_overrides": [{
    "path": "$.capabilities[?(@.name == 'OneDriveAndSharePoint')]",
    "allowed_actions": ["remove"]
  }]
}
```

Lets end users toggle off specific capabilities via UI. Only `"remove"` action supported. For GraphConnectors, the system displays friendly names for Microsoft connectors.

## Adding a Disclaimer (v1.6)

```json
{ "disclaimer": { "text": "This agent provides estimates only. Verify important information." } }
```

Max 500 characters. Displayed at the start of every conversation.

## Configuring Adaptive Card Templates

Add `response_semantics` to a function in apiPlugin.json:

```json
{
  "capabilities": {
    "response_semantics": {
      "data_path": "$.results",
      "properties": {
        "title": "$.name",
        "subtitle": "$.status"
      },
      "static_template": { "file": "./adaptive-cards/result.json" }
    }
  }
}
```

See `adaptive-cards.md` for full details.

## After Modifying Agent Files

1. Bump `version` in manifest.json
2. Re-provision via Agents Toolkit or re-upload
3. Changes may take a few minutes to propagate
4. Run `/copilot:validate` to catch issues
5. Test in Copilot with developer mode (`-developer on`)
