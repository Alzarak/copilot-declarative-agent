# File Schemas and Limits

## Schema Versions

| File | Field | Current Version | Schema URL |
|------|-------|-----------------|------------|
| manifest.json | `manifestVersion` | `1.30` | `https://developer.microsoft.com/json-schemas/teams/v1.30/MicrosoftTeams.schema.json` |
| declarativeAgent.json | `version` | `v1.9` | `https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.9/schema.json` |
| apiPlugin.json | `schema_version` | `v2.4` | `https://aka.ms/json-schemas/copilot/plugin/v2.4/schema.json` |
| apiDefinition.json | `openapi` | `3.0.0` | OpenAPI specification |

Older declarative agent versions (v1.0–v1.8) are still accepted; the validator warns and flags any feature newer than the declared version. Root-level `agentSkills` in manifest.json needs manifestVersion 1.28+.

### Declarative agent version history

| Version | Added |
|---------|-------|
| v1.9 | `agent_skills` (max 8), `Fabric` capability |
| v1.8 | `EmailActions` and `MeetingActions` capabilities |
| v1.7 | `editorial_answers`, `behavior_overrides.default_response_mode`, `conversation_starters[].depends_on`; conversation starters max 12 |
| v1.6 | `sensitivity_label`, `worker_agents`, `user_overrides`, `EmbeddedKnowledge`, `Meetings.items_by_id`, `People.include_related_content`, `Email.group_mailboxes` |

## Runtime Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Total token budget | 4,096 tokens | Includes instructions + context + tools + prompt + response |
| Plugin response limit | 25 items | Max items from external API responses |
| Grounding record limit | 50 items | Contextual data available |
| Timeout | 45 seconds | Including network latency and processing |
| Plugin API execution | 10 seconds | Optimize for under 9s |
| `description_for_model` | 2,048 chars | Content beyond this MAY be ignored |
| `instructions` | 8,000 chars | Agent-wide behavior |

Optimize for ~66% of technical limits due to external overhead.

---

## manifest.json (Microsoft 365 App Manifest v1.30)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.30/MicrosoftTeams.schema.json",
  "manifestVersion": "1.30",
  "id": "00000000-0000-0000-0000-000000000000",
  "version": "1.0.0",
  "developer": {
    "name": "Company Name",
    "websiteUrl": "https://example.com",
    "privacyUrl": "https://example.com/privacy",
    "termsOfUseUrl": "https://example.com/terms"
  },
  "name": {
    "short": "Agent Name",
    "full": "Full Agent Name with More Detail"
  },
  "description": {
    "short": "Brief description of what the agent does",
    "full": "Detailed description explaining the agent's purpose, capabilities, and target audience."
  },
  "icons": {
    "color": "color.png",
    "outline": "outline.png"
  },
  "copilotAgents": {
    "declarativeAgents": [
      {
        "id": "declarativeAgent",
        "file": "declarativeAgent.json"
      }
    ]
  },
  "webApplicationInfo": {
    "id": "00000000-0000-0000-0000-000000000000",
    "resource": "api://example.com/00000000-0000-0000-0000-000000000000"
  }
}
```

### Field Limits

| Field | Limit | Required |
|-------|-------|----------|
| `id` | UUID format | Yes |
| `name.short` | 30 chars | Yes |
| `name.full` | 100 chars | No |
| `description.short` | 80 chars | Yes |
| `description.full` | 4000 chars | Yes |
| `developer.name` | — | Yes |
| `developer.websiteUrl` | — | Yes |
| `developer.privacyUrl` | — | Yes |
| `developer.termsOfUseUrl` | — | Yes |
| `copilotAgents.declarativeAgents` | Array | Yes |
| `webApplicationInfo.id` | Azure AD App ID | For auth |

---

## declarativeAgent.json (v1.9)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.9/schema.json",
  "version": "v1.9",
  "id": "agentIdentifier",
  "name": "My Agent",
  "description": "What this agent does and when to use it.",
  "instructions": "# Role\nYou are a helpful assistant.\n\n# Workflow\n## Step 1\n...",
  "capabilities": [
    { "name": "WebSearch" },
    { "name": "CodeInterpreter" },
    { "name": "EmailActions" }
  ],
  "conversation_starters": [
    { "title": "Get started", "text": "How can you help me?" },
    { "title": "Search", "text": "Find information about..." },
    {
      "title": "Tidy inbox",
      "text": "Archive the resolved threads in my inbox",
      "depends_on": [{ "name": "capabilities", "id": "EmailActions" }]
    }
  ],
  "actions": [
    { "id": "myApiPlugin", "file": "apiPlugin.json" }
  ],
  "agent_skills": [
    { "folder": "skills/ticket-triage" }
  ],
  "behavior_overrides": {
    "suggestions": { "disabled": false },
    "special_instructions": { "discourage_model_knowledge": false },
    "default_response_mode": "Auto"
  },
  "editorial_answers": {
    "answers": [
      {
        "question": "What are support hours?",
        "answer": "8am-6pm ET, Monday to Friday.",
        "similarity_thresholds": { "min": 6, "max": 10 }
      }
    ]
  },
  "disclaimer": {
    "text": "This agent provides estimates only. Verify important information independently."
  },
  "worker_agents": [
    { "id": "P_00000000-0000-0000-0000-000000000000" }
  ],
  "user_overrides": [
    {
      "path": "$.capabilities[?(@.name == 'OneDriveAndSharePoint')]",
      "allowed_actions": ["remove"]
    }
  ],
  "sensitivity_label": {
    "id": "00000000-0000-0000-0000-000000000000"
  }
}
```

### Field Limits

| Field | Limit | Required |
|-------|-------|----------|
| `$schema` | Must point at the same version as `version` | Yes (atk validate) |
| `version` | Schema version string with `v` prefix | Yes |
| `name` | 100 chars | Yes |
| `description` | 1,000 chars | Yes |
| `instructions` | 8,000 chars | Yes |
| `capabilities` | Array of capability objects | No |
| `conversation_starters` | Max **12** items (v1.7+; v1.6 docs conflict between 6 and 12) | No |
| `conversation_starters[].depends_on` | `[{ "name": "capabilities", "id": "<Capability>" }]` | No (v1.7) |
| `actions` | 1–10 items; each `{id, file}` or an inline plugin manifest | No |
| `agent_skills` | Max **8** `{ "folder" }` items — see Agent Skills below | No (v1.9) |
| `behavior_overrides` | Object | No |
| `behavior_overrides.default_response_mode` | `Auto` \| `Quick response` \| `Think deeper` | No (v1.7) |
| `editorial_answers` | `url` **or** `answers` (max 300; `question`, `answer`, `similarity_thresholds` 0–10) | No (v1.7) |
| `disclaimer.text` | 500 chars, min 1 non-whitespace | No (v1.6) |
| `worker_agents` | Array of {id} objects | No (v1.6, preview; v1.8+ docs call `id` optional but define no alternative — keep it) |
| `user_overrides` | Array, only "remove" action | No (v1.6) |
| `sensitivity_label.id` | GUID | No (v1.6, not yet enabled) |

**Any property not in the schema makes the whole document invalid** — the validator errors on unknown top-level keys.

### 15 Capability Types (max one of each)

WebSearch, OneDriveAndSharePoint, GraphConnectors, GraphicArt, CodeInterpreter, Dataverse, TeamsMessages, Email, EmailActions (v1.8), People, ScenarioModels, Meetings, MeetingActions (v1.8), Fabric (v1.9), EmbeddedKnowledge

See `capabilities.md` for full configuration details.

### String Localization

Localizable strings support `[[key_name]]` syntax resolved from localization files:
```json
{ "name": "[[agent_name]]", "description": "[[agent_description]]" }
```

---

## Agent Skills (v1.9)

Agent skills package reusable instructions, reference files and scripts that the agent loads only when a task needs them. Declare them with the top-level `agent_skills` array in declarativeAgent.json (schema **v1.9 required**).

```json
"agent_skills": [
  { "folder": "./skills/ticket-triage" },
  { "folder": "skills/escalation-policy" }
]
```

### `agent_skills` rules

| Rule | Value |
|------|-------|
| Max skills per agent | **8** |
| Item properties | `folder` only (string, required, non-empty) |
| `folder` path | Relative to declarativeAgent.json, forward slashes only, no `../`, must resolve to a directory **inside** the app package |
| `SKILL.md` | Required in every skill folder |
| `SKILL.md` frontmatter | YAML with `name` and `description` |
| `SKILL.md` length | Under **20,000** characters |
| Directory depth inside a skill | Max **3** |
| Files across all skills | Max **350** |
| App package size (Agents Toolkit) | 10 MB total; skills ship as folders, not .zip |
| Reuse across agents | Not supported — each agent carries its own copy |

### Folder layout

```
appPackage/
├── declarativeAgent.json
└── skills/
    └── ticket-triage/
        ├── SKILL.md
        ├── references/priority-matrix.md
        └── scripts/sla.py
```

### SKILL.md

```markdown
---
name: ticket-triage
description: Classify an incoming service desk email by priority and queue, then suggest a first reply.
---

# Ticket triage
1. Read the email and identify the affected user, device and symptom.
2. Assign a priority using `references/priority-matrix.md`.
3. Draft a short first reply.
```

Microsoft only states that the frontmatter needs "name and description". The Agent Skills convention (lowercase-hyphen `name` matching the folder, max 64 chars; `description` max 1,024 chars) is a good default; the validator warns, not errors, when `name` departs from it.

### Allowed file types

- **Content:** .json .xml .yaml .yml .ini .config .utf8 .docx .doc .docm .pdf .txt .rtf .md .ppt .pptx .ppsm .xlsx .xls .xlsm .csv .tsv .html .htm .png .jpg .jpeg .gif .bmp .log
- **Scripts:** .py .js .mjs .cjs .ts .mts .sh .bash

### Script sandbox

Scripts run with no network access, no package installs and no authenticated calls. They can only use packages already in the sandbox and cannot call connectors, plugins or MCP servers — put live data access in an action, not a skill.

### Agents Toolkit

- Set `TEAMSFX_AGENT_SKILLS=true`.
- `atk add skill --name <name> --description "<text>"` or `atk add skill --from <path>`; default location is `./appPackage/skills/<name>/SKILL.md`.
- The Microsoft 365 app manifest also has a root-level `agentSkills` array (manifest **1.28+**, same `{ "folder" }` shape, max 256 chars). Use `agent_skills` in declarativeAgent.json for skills scoped to one agent.

### Other notes

- Sensitivity labels on skill files are honored; user-defined permissions and Double Key Encryption are not supported.
- In tenants using Purview Information Barriers, admins can deploy agents with skills but end users cannot add skills to agents they build.

---

## apiPlugin.json (v2.4)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/copilot/plugin/v2.4/schema.json",
  "schema_version": "v2.4",
  "name_for_human": "My API Tools",
  "namespace": "myApi",
  "description_for_human": "Tools for managing resources.",
  "description_for_model": "Use this plugin when the user wants to search, create, or manage resources. Supports filtering by status, type, and date.",
  "functions": [
    {
      "name": "searchResources",
      "description": "Search for resources by various criteria.",
      "capabilities": {
        "response_semantics": {
          "data_path": "$.results",
          "properties": {
            "title": "$.name",
            "subtitle": "$.status",
            "url": "$.href"
          },
          "static_template": { "file": "./adaptive-cards/search-result.json" }
        }
      },
      "states": {
        "reasoning": {
          "description": "Searches resources matching filters.",
          "instructions": [
            "Use this function when the user asks to find or list resources.",
            "Map 'high priority' to priority=1, 'low priority' to priority=4.",
            "Default max_results to 10 unless the user specifies otherwise."
          ]
        },
        "responding": {
          "instructions": [
            "Present results as a numbered list with name, status, and link.",
            "If no results found, suggest broadening the search criteria.",
            "Always show the total count of matching results."
          ]
        }
      }
    }
  ],
  "runtimes": [
    {
      "type": "OpenApi",
      "auth": {
        "type": "OAuthPluginVault",
        "reference_id": "00000000-0000-0000-0000-000000000000"
      },
      "spec": {
        "url": "apiDefinition.json",
        "progress_style": "ShowUsageWithInputAndOutput"
      },
      "run_for_functions": ["searchResources"]
    }
  ]
}
```

### Field Limits

| Field | Limit | Required |
|-------|-------|----------|
| `schema_version` | Version string | Yes |
| `name_for_human` | 20 chars | Yes |
| `description_for_human` | 100 chars | No |
| `description_for_model` | **2,048 chars** (CRITICAL) | No |
| `namespace` | String | No |
| `functions` | Array (may be `[]` for MCP dynamic discovery) | Yes |
| `functions[].name` | Must match operationId | Yes |
| `functions[].description` | ~4,000 chars | Yes |
| `runtimes` | Array | Yes |

### Runtime Types

| Type | Purpose |
|------|---------|
| `OpenApi` | Standard OpenAPI-based API calls |
| `RemoteMCPServer` | Remote Model Context Protocol server (v2.4) — `spec.url` is the server's absolute URL, not a package file |
| `LocalPlugin` | Office Add-in integration |

### RemoteMCPServer Runtime

```json
{
  "type": "RemoteMCPServer",
  "auth": { "type": "None" },
  "run_for_functions": ["getWeather"],
  "spec": {
    "url": "https://weather.contoso.com/mcp",
    "mcp_tool_description": {
      "tools": [
        {
          "name": "getWeather",
          "description": "Get current weather for a location",
          "inputSchema": {
            "type": "object",
            "properties": { "location": { "type": "string" } },
            "required": ["location"]
          }
        }
      ]
    }
  }
}
```

Three MCP modes:
1. **Inline tools**: Define `tools` array in `mcp_tool_description`
2. **File reference**: `"file": "mcp-tools.json"` in `mcp_tool_description`
3. **Dynamic discovery**: Omit `mcp_tool_description`, set `"functions": []` and `"run_for_functions": ["*"]`; Copilot calls `tools/list` at runtime

Rules: `spec.url` must be absolute; `file` and `tools` are mutually exclusive; each tool needs `name`, `description` and `inputSchema`; `run_for_functions` accepts wildcards. The v2.4 runtime table marks `auth` required while Microsoft's MCP examples omit it — always include it (`{ "type": "None" }` for open servers).

Dynamic discovery (no tool list in the package):

```json
{
  "schema_version": "v2.4",
  "name_for_human": "Tickets",
  "functions": [],
  "runtimes": [{
    "type": "RemoteMCPServer",
    "auth": { "type": "OAuthPluginVault", "reference_id": "${{MCP_AUTH_ID}}" },
    "spec": { "url": "https://mcp.contoso.com/mcp" },
    "run_for_functions": ["*"]
  }]
}
```

### Auth Types

| Type | Usage |
|------|-------|
| `OAuthPluginVault` | Azure AD with `reference_id` |
| `ApiKeyPluginVault` | API key-based auth (reference_id from Teams Developer Portal registration) |
| `None` | No authentication |

### Function States

```json
{
  "states": {
    "reasoning": {
      "description": "What this function does",
      "instructions": [
        "When to call this function",
        "How to map user language to parameters"
      ]
    },
    "responding": {
      "instructions": [
        "How to format the response",
        "Error handling guidance"
      ]
    }
  }
}
```

### reasoning.instructions Format

- **Array of strings** (recommended): Augments built-in prompts
- **Single string**: Overrides built-in prompts entirely

Always use array format unless you need to completely replace the orchestrator's default reasoning behavior.

### response_semantics (Adaptive Cards)

See `adaptive-cards.md` for full details.

### progress_style

Controls what the user sees during function execution:
- `None` — no progress indicator
- `ShowUsage` — shows function is being called
- `ShowUsageWithInput` — shows function + input parameters
- `ShowUsageWithInputAndOutput` — shows function + input + output

### security_info

**Without `security_info`, the function cannot interact with other plugins or agent capabilities.** Required for cross-plugin orchestration.

### security_info Configuration

```json
{
  "capabilities": {
    "security_info": {
      "data_handling": ["GetPrivateData", "ResourceStateUpdate"]
    }
  }
}
```

| Value | Meaning |
|-------|---------|
| `GetPublicData` | Retrieves from unauthenticated external source |
| `GetPrivateData` | Retrieves from authenticated source or current app |
| `DataTransform` | Returns output based on input only |
| `DataExport` | Writes data to external location |
| `ResourceStateUpdate` | Changes state requiring user confirmation |

---

## apiDefinition.json (OpenAPI 3.0.0)

### Size Limits

| Constraint | Limit | Notes |
|------------|-------|-------|
| **File size** | **100 KB max** | Hard limit — files over 100 KB will fail validation or be rejected |
| Functions per plugin | Unlimited, but **quality degrades >10** | Due to 4,096 token budget; aim for ≤25 per plugin |
| Plugin response | 25 items max | Per API call response |

### Slimming Strategies

When approaching the 100 KB limit:

1. **Use `$ref` components** — Define reusable schemas in `components/schemas` and reference them:
   ```json
   "components": {
     "schemas": {
       "ApiResponse": { "type": "object" },
       "CommonFilters": {
         "type": "object",
         "properties": {
           "status": { "type": "string" },
           "created_within": { "type": "string" }
         }
       }
     }
   }
   ```
   Then reference with `{"$ref": "#/components/schemas/CommonFilters"}` in request bodies.

2. **Use `allOf` to compose schemas** — Combine a `$ref` with operation-specific properties:
   ```json
   "schema": {
     "allOf": [
       { "$ref": "#/components/schemas/CommonFilters" },
       { "type": "object", "properties": { "group_by": { "type": "string" } }, "required": ["group_by"] }
     ]
   }
   ```

3. **Remove redundant fields** — Push `description` text to apiPlugin.json reasoning instructions instead of duplicating in the OpenAPI spec. Keep only `summary` on operations.

4. **Simplify response schemas** — Use a single `$ref` to a generic response component instead of inlining response schemas on every operation.

5. **Remove internal-only parameters** — Don't expose server-side defaults (e.g., `cache`, `fields`, `max_results`) in the OpenAPI spec if the server handles defaults.

6. **Split into multiple plugins** — When a single plugin exceeds 25 functions or its apiDefinition exceeds 100 KB, split by domain (see Plugin Splitting below).

### Example (Slim)

```json
{
  "openapi": "3.0.0",
  "info": { "title": "My API", "version": "1.0.0" },
  "servers": [{ "url": "https://api.example.com" }],
  "paths": {
    "/api/v1/search": {
      "post": {
        "operationId": "searchResources",
        "summary": "Search resources",
        "x-openai-isConsequential": false,
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/CommonFilters" }
            }
          }
        },
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ApiResponse" }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "ApiResponse": { "type": "object" },
      "CommonFilters": {
        "type": "object",
        "properties": {
          "query": { "type": "string", "description": "Search query" },
          "status": { "type": "string", "description": "Status filter" }
        }
      }
    }
  }
}
```

## Plugin Injection Rules

How the orchestrator decides which plugins to load:

| Plugin Count | Behavior |
|-------------|----------|
| 1-5 plugins | Always injected into prompt |
| 6+ plugins | Semantic matching on plugin `description_for_model` (not individual functions) |

When >5 plugins are registered, only plugins whose `description_for_model` semantically matches the user's prompt are loaded. **All functions from a matched plugin are included**, even if only one function matched.

A plugin can include an unlimited number of functions. However, **quality degrades if more than 10 functions are included** in a single plugin due to token window limits.

### Plugin Splitting

When to split into multiple plugins:
- apiDefinition.json exceeds **100 KB**
- Plugin has **more than 25 functions** (conservative) or **more than 10** (Microsoft recommendation)
- Functions naturally group into distinct domains

**Architecture**: Each plugin is a separate `apiPlugin-{domain}.json` + `apiDefinition-{domain}.json` pair, referenced as separate actions in `declarativeAgent.json`:

```json
"actions": [
  { "id": "corePlugin", "file": "apiPlugin-core.json" },
  { "id": "projectsPlugin", "file": "apiPlugin-projects.json" }
]
```

Each apiPlugin file has its own `runtimes` array pointing to its own apiDefinition file:
```json
"runtimes": [{
  "type": "OpenApi",
  "auth": { "type": "OAuthPluginVault", "reference_id": "..." },
  "spec": { "url": "apiDefinition-core.json" },
  "run_for_functions": ["func1", "func2"]
}]
```

**Planning for future plugins**: Keep total plugin count ≤5 so all are always injected. Example with 4 plugins:
| Plugin | Functions | apiDefinition size |
|--------|-----------|-------------------|
| `apiPlugin-autotask.json` | 25 | ~31 KB |
| `apiPlugin-autotask-projects.json` | 25 | ~35 KB |
| `apiPlugin-passportal.json` | ~15 | ~20 KB |
| `apiPlugin-lionguard.json` | ~10 | ~15 KB |

**Best practice**: Write `description_for_model` to cover the full range of scenarios each plugin handles, not just one function. Keep it under 2,048 chars.

## Function Capabilities Object

Each function can have these capabilities:

```json
{
  "capabilities": {
    "confirmation": {
      "type": "AdaptiveCard",
      "title": "Confirm Action",
      "body": "Please confirm this operation."
    },
    "response_semantics": { ... },
    "security_info": {
      "data_handling": ["GetPrivateData"]
    }
  }
}
```

| Capability | Purpose |
|-----------|---------|
| `confirmation` | Custom confirmation dialog for consequential actions |
| `response_semantics` | Adaptive Card rendering (see adaptive-cards.md) |
| `security_info` | Cross-plugin interaction permissions |

### Key Rules

- `operationId` **must** match function `name` in apiPlugin.json exactly
- `x-openai-isConsequential`: `false` for read-only (GET), `true` for create/update/delete
- When `isConsequential` is true, Copilot shows confirmation dialog
- When false, enables "Always Allow" option during confirmation
