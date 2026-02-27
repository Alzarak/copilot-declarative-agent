# Security & Compliance

Enterprise-grade security configuration for declarative agents with API plugins.

## Built-in Protections

Declarative agents inherit Microsoft 365 security, compliance, and governance:

- Content filtering and inline disengagement for XPIA (cross-prompt injection attacks)
- RAI (Responsible AI) validation required before publishing
- User permissions enforced -- agent can only access content the user has access to
- Requires M365 Copilot license for capabilities beyond WebSearch

## Authentication Types

Configure authentication in the `runtimes` section of `apiPlugin.json`.

### OAuthPluginVault (Azure AD OAuth 2.0)

```json
{
  "type": "OpenApi",
  "auth": {
    "type": "OAuthPluginVault",
    "reference_id": "00000000-0000-0000-0000-000000000000"
  },
  "spec": { "url": "apiDefinition.json" },
  "run_for_functions": ["searchResources"]
}
```

- `reference_id`: Obtained from Azure AD app registration in the Teams Developer Portal
- Supports delegated and application permissions
- Token exchange handled by the Copilot orchestrator

### ApiKeyPluginVault (API Key)

```json
{
  "type": "OpenApi",
  "auth": {
    "type": "ApiKeyPluginVault",
    "reference_id": "00000000-0000-0000-0000-000000000000"
  },
  "spec": { "url": "apiDefinition.json" },
  "run_for_functions": ["getPublicData"]
}
```

- `reference_id`: Registered API key from the Teams Developer Portal
- Suitable for third-party APIs that use API key authentication
- Key is securely stored in Plugin Vault

### None (No Authentication)

```json
{
  "type": "OpenApi",
  "auth": { "type": "none" },
  "spec": { "url": "apiDefinition.json" },
  "run_for_functions": ["getPublicInfo"]
}
```

- For public APIs that require no authentication
- Use sparingly -- most enterprise APIs should require auth

## isConsequential Actions

Mark write operations in your OpenAPI spec to control user confirmation behavior:

```yaml
paths:
  /tasks:
    post:
      x-openai-isConsequential: true
      operationId: createTask
```

| Value | Behavior |
|-------|----------|
| `true` | Always requires user confirmation before executing |
| `false` | May not require confirmation after first connection (enables "Always Allow") |
| Omitted | Default based on HTTP method (see below) |

### HTTP Method Defaults

| Method | Default Behavior |
|--------|-----------------|
| GET | Non-consequential (no confirmation after first) |
| POST, PUT, PATCH, DELETE | Consequential (always confirms) |

### Confirmation Flow

1. **First connection**: Always asks user to confirm data sharing with the plugin
2. **Read-only (non-consequential)**: No subsequent confirmation needed
3. **Write operations (consequential)**: Always requires confirmation
4. Override behavior explicitly with `x-openai-isConsequential`

**Best practice**: Always set `x-openai-isConsequential` explicitly on every operation rather than relying on HTTP method defaults.

## security_info (v2.2+)

**Without `security_info`, a function cannot interact with other plugins or agent capabilities.** This is required for cross-plugin orchestration.

### Configuration

Add `security_info` to a function's `capabilities`:

```json
{
  "name": "searchResources",
  "description": "Search for resources.",
  "capabilities": {
    "security_info": {
      "data_handling": ["GetPrivateData"]
    }
  }
}
```

### data_handling Values

| Value | Meaning | Use When |
|-------|---------|----------|
| `GetPublicData` | Retrieves data from unauthenticated external source | Public API calls, no user credentials |
| `GetPrivateData` | Retrieves data from authenticated source or current app | User-scoped queries, tenant data |
| `DataTransform` | Returns output based on input only, no external calls | Computation, formatting, conversion |
| `DataExport` | Writes data to an external location | File uploads, data export operations |
| `ResourceStateUpdate` | Changes state requiring user confirmation | Create, update, delete operations |

### Common Combinations

| Function Type | data_handling |
|--------------|--------------|
| Read-only search with auth | `["GetPrivateData"]` |
| Create/update resource | `["GetPrivateData", "ResourceStateUpdate"]` |
| Export data to file | `["GetPrivateData", "DataExport"]` |
| Public data retrieval | `["GetPublicData"]` |
| Data transformation | `["DataTransform"]` |
| Read + modify + export | `["GetPrivateData", "ResourceStateUpdate", "DataExport"]` |

### Example: Full Function with Security

```json
{
  "name": "createTicket",
  "description": "Creates a new support ticket.",
  "capabilities": {
    "security_info": {
      "data_handling": ["GetPrivateData", "ResourceStateUpdate"]
    },
    "confirmation": {
      "type": "AdaptiveCard",
      "title": "Create Ticket",
      "body": "Are you sure you want to create this ticket?"
    }
  },
  "states": {
    "reasoning": {
      "instructions": [
        "Use this function when the user wants to create a new ticket.",
        "Require title and description before calling."
      ]
    },
    "responding": {
      "instructions": [
        "Confirm the ticket was created with its ID and link.",
        "If error, show the error message and suggest corrective action."
      ]
    }
  }
}
```

## Sensitivity Labels (v1.6)

For agents with embedded files, specify the highest protection label:

```json
{
  "sensitivity_label": { "id": "<purview-label-guid>" }
}
```

- Applied to the agent when embedded knowledge files are present
- Uses Microsoft Purview Information Protection labels
- The label GUID comes from your organization's Purview configuration
- Unsupported: Double key encryption, user-defined permissions, cross-tenant encrypted files, password-protected files

## Enterprise Security Checklist

### Authentication

- [ ] All API endpoints use `OAuthPluginVault` or `ApiKeyPluginVault` (not `none`) for sensitive data
- [ ] Azure AD app registration has minimal required scopes
- [ ] OAuth flow uses delegated permissions (user context) where possible
- [ ] API keys are registered through Teams Developer Portal (not hardcoded)

### Data Protection

- [ ] `x-openai-isConsequential: true` on all write operations (POST/PUT/PATCH/DELETE)
- [ ] `security_info.data_handling` configured on every function
- [ ] `sensitivity_label` set when using embedded knowledge files
- [ ] API responses don't expose sensitive fields unnecessarily

### Access Control

- [ ] SharePoint/OneDrive knowledge respects user permissions (automatic)
- [ ] Agent only accesses content the authenticated user can access
- [ ] Shared mailboxes and group mailboxes are explicitly scoped
- [ ] Teams channels are scoped to specific threads (not all chats)

### Knowledge Sources

- [ ] `behavior_overrides.special_instructions.discourage_model_knowledge: true` if agent should only use provided sources
- [ ] Knowledge sources are scoped to specific sites/channels (not "all")
- [ ] Embedded files reviewed for sensitive content before bundling

### Compliance

- [ ] RAI validation passed before publishing
- [ ] Privacy URL and Terms of Use URL set in `manifest.json` developer section
- [ ] Agent description clearly states what data it accesses
- [ ] Disclaimer configured for any agent providing estimates or advice

### Plugin Interaction

- [ ] Functions that need cross-plugin interaction have `security_info` configured
- [ ] `data_handling` values accurately reflect function behavior
- [ ] Write operations have both `isConsequential: true` and `ResourceStateUpdate` in data_handling
