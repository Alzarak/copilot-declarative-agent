# File Schemas and Limits

## Schema Versions

| File | Field | Current Version | Schema URL |
|------|-------|-----------------|------------|
| manifest.json | `manifestVersion` | `1.24` | `https://developer.microsoft.com/json-schemas/teams/v1.24/MicrosoftTeams.schema.json` |
| declarativeAgent.json | `version` | `v1.6` | `https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.6/schema.json` |
| apiPlugin.json | `schema_version` | `v2.4` | `https://aka.ms/json-schemas/copilot/plugin/v2.4/schema.json` |
| apiDefinition.json | `openapi` | `3.0.0` | OpenAPI specification |

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

## manifest.json (Teams App Manifest v1.24)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.24/MicrosoftTeams.schema.json",
  "manifestVersion": "1.24",
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

## declarativeAgent.json (v1.6)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.6/schema.json",
  "version": "v1.6",
  "id": "agentIdentifier",
  "name": "My Agent",
  "description": "What this agent does and when to use it.",
  "instructions": "# Role\nYou are a helpful assistant.\n\n# Workflow\n## Step 1\n...",
  "capabilities": [
    { "name": "WebSearch" },
    { "name": "CodeInterpreter" }
  ],
  "conversation_starters": [
    { "title": "Get started", "text": "How can you help me?" },
    { "title": "Search", "text": "Find information about..." }
  ],
  "actions": [
    { "id": "myApiPlugin", "file": "apiPlugin.json" }
  ],
  "behavior_overrides": {
    "suggestions": { "disabled": false },
    "special_instructions": { "discourage_model_knowledge": false }
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
| `version` | Schema version string | Yes |
| `name` | 100 chars | Yes |
| `description` | 1,000 chars | Yes |
| `instructions` | 8,000 chars | Yes |
| `capabilities` | Array of capability objects | No |
| `conversation_starters` | Max **6** items (reduced from 12 in v1.2) | No |
| `actions` | 1–10 items | No |
| `behavior_overrides` | Object | No (v1.6) |
| `disclaimer.text` | 500 chars, min 1 non-whitespace | No (v1.6) |
| `worker_agents` | Array of {id} objects | No (v1.6, preview) |
| `user_overrides` | Array, only "remove" action | No (v1.6) |
| `sensitivity_label.id` | GUID | No (v1.6, not yet enabled) |

### 12 Capability Types

WebSearch, OneDriveAndSharePoint, GraphConnectors, GraphicArt, CodeInterpreter, Dataverse, TeamsMessages, Email, People, ScenarioModels, Meetings, EmbeddedKnowledge

See `capabilities.md` for full configuration details.

### String Localization

Localizable strings support `[[key_name]]` syntax resolved from localization files:
```json
{ "name": "[[agent_name]]", "description": "[[agent_description]]" }
```

---

## apiPlugin.json (v2.4)

```json
{
  "$schema": "https://aka.ms/json-schemas/copilot/plugin/v2.4/schema.json",
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
| `functions` | Array | Yes |
| `functions[].name` | Must match operationId | Yes |
| `functions[].description` | ~4,000 chars | Yes |
| `runtimes` | Array | Yes |

### Runtime Types

| Type | Purpose |
|------|---------|
| `OpenApi` | Standard OpenAPI-based API calls |
| `RemoteMCPServer` | Model Context Protocol server (v2.4) |
| `LocalPlugin` | Office Add-in integration |

### RemoteMCPServer Runtime

```json
{
  "type": "RemoteMCPServer",
  "auth": { "type": "none" },
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
3. **Dynamic discovery**: Omit `mcp_tool_description`; server calls `tools/list`

### Auth Types

| Type | Usage |
|------|-------|
| `OAuthPluginVault` | Azure AD with `reference_id` |
| `ApiKeyPluginVault` | API key-based auth (reference_id from Teams Developer Portal registration) |
| `none` | No authentication |

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

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "My API",
    "version": "1.0.0",
    "description": "API for managing resources"
  },
  "servers": [
    { "url": "https://api.example.com" }
  ],
  "paths": {
    "/api/v1/resources/searchResources": {
      "post": {
        "operationId": "searchResources",
        "summary": "Search for resources",
        "x-openai-isConsequential": false,
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": { "type": "string", "description": "Search query" },
                  "max_results": { "type": "integer", "description": "Max results (default 10)" }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Search results",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "results": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "name": { "type": "string" },
                          "status": { "type": "string" }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "securitySchemes": {
      "oauth2": {
        "type": "oauth2",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
            "tokenUrl": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            "scopes": {
              "api://{client-id}/access_as_user": "Access API"
            }
          }
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

When >5 plugins are registered, only plugins whose `description_for_model` semantically matches the user's prompt are loaded. All functions from a matched plugin are included.

**Best practice**: Write `description_for_model` to cover the full range of scenarios the plugin handles, not just one function.

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
