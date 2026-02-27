# Validation and Troubleshooting

## Finding the App Package

1. Check user-provided path first (if specified)
2. Look for `appPackage/` in current directory
3. Search for `**/appPackage/` using glob patterns

## Full Validation Workflow

When asked to validate an appPackage:

1. **Locate the folder**
2. **Check required files exist**
3. **Validate each JSON file** for syntax and schema compliance
4. **Verify cross-references** between files (file paths, function names, operationIds)
5. **Check schema version currency** against known current versions
6. **Check field limits** (character counts, array sizes)
7. **Validate new v1.6 properties** (behavior_overrides, disclaimer, worker_agents, user_overrides)
8. **Report findings** with specific issues and recommendations

Or run the validation script:
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_apppackage.py [path_to_apppackage]
```

## Validation Checklist

### File Existence
- [ ] manifest.json exists
- [ ] declarativeAgent.json exists
- [ ] color.png exists (192x192)
- [ ] outline.png exists (32x32)
- [ ] apiPlugin.json exists (if actions defined)
- [ ] apiDefinition.json exists (if apiPlugin exists)

### manifest.json
- [ ] Valid JSON syntax
- [ ] `manifestVersion` is "1.24" or compatible
- [ ] `id` is valid UUID format
- [ ] `version` follows semantic versioning
- [ ] `developer` has all required fields (name, websiteUrl, privacyUrl, termsOfUseUrl)
- [ ] `name.short` <= 30 characters
- [ ] `description.short` <= 80 characters
- [ ] `copilotAgents.declarativeAgents` array exists
- [ ] Each declarativeAgent has `id` and `file`
- [ ] Referenced files exist

### declarativeAgent.json
- [ ] Valid JSON syntax
- [ ] `version` is valid schema version (e.g., "v1.6")
- [ ] `name` exists and <= 100 characters
- [ ] `description` exists and <= 1000 characters
- [ ] `instructions` exists and <= 8000 characters
- [ ] `instructions` uses Markdown formatting (headers, lists)
- [ ] `capabilities` items have valid `name` (one of 12 known types)
- [ ] `conversation_starters` max 6 items (v1.6 limit, reduced from 12)
- [ ] `conversation_starters` items have `text` field
- [ ] `actions` array: 1–10 items, each with `id` and `file`
- [ ] Referenced action files exist
- [ ] `behavior_overrides` structure is valid (if present)
- [ ] `disclaimer.text` <= 500 characters (if present)
- [ ] `worker_agents` items have `id` (if present)
- [ ] `user_overrides` items have `path` and `allowed_actions` (if present)

### apiPlugin.json
- [ ] Valid JSON syntax
- [ ] `schema_version` is valid (e.g., "v2.4")
- [ ] `name_for_human` exists and <= 20 characters
- [ ] `description_for_model` is under 2,048 characters
- [ ] `functions` array items have `name` and `description`
- [ ] Functions with complex behavior have `states.reasoning.instructions`
- [ ] `runtimes` array items have required fields (type, auth, spec)
- [ ] `spec.url` references existing file
- [ ] Every function name appears in at least one `run_for_functions` array
- [ ] Every `run_for_functions` entry has a matching function definition
- [ ] Runtime type is valid: OpenApi, RemoteMCPServer, or LocalPlugin
- [ ] For RemoteMCPServer: spec has url and optionally mcp_tool_description
- [ ] `security_info` present if cross-plugin interaction needed
- [ ] `response_semantics` data_path uses valid JSONPath (if present)

### apiDefinition.json
- [ ] Valid JSON syntax
- [ ] OpenAPI version is 3.0.x
- [ ] Every `operationId` matches a function `name` in apiPlugin.json
- [ ] Every apiPlugin function has a matching `operationId` path
- [ ] Authentication schemes properly defined
- [ ] `x-openai-isConsequential` set appropriately (false for reads, true for writes)

### Capability-Specific Validation
- [ ] WebSearch `sites` array max 4 URLs, max 2 path segments, no query params
- [ ] OneDriveAndSharePoint has valid `items_by_url` or `items_by_sharepoint_ids`
- [ ] GraphConnectors `connections` have `connection_id`
- [ ] TeamsMessages `urls` max 5 items
- [ ] Email `group_mailboxes` max 25 items
- [ ] Meetings `items_by_id` max 5 items
- [ ] EmbeddedKnowledge `files` max 10 items, max 1 MB each

## Troubleshooting

### Agent Not Appearing in Copilot
1. Check manifest.json `copilotAgents` configuration exists
2. Verify Azure AD app registration matches `webApplicationInfo.id`
3. Ensure app is properly published/installed in Teams
4. Check tenant admin has enabled Copilot extensibility
5. Government tenants (GCC) have limited support

### API Functions Not Working
1. Verify `operationId` in OpenAPI matches function `name` exactly
2. Check authentication configuration in runtime
3. Validate OpenAPI paths use correct HTTP methods (POST for actions)
4. Ensure server URLs are accessible from Copilot service
5. Check `run_for_functions` includes all function names
6. Run validation script to catch sync issues
7. Check Plugin API execution timeout (10 seconds)

### Agent Ignoring Instructions
1. Check `description_for_model` is under 2,048 characters — content beyond this may be silently ignored
2. Move function-specific guidance from `description_for_model` to `functions[].states.reasoning.instructions`
3. Verify `instructions` in declarativeAgent.json uses Markdown formatting
4. Check total token usage — 4,096 token runtime budget includes everything
5. Use developer mode (`-developer on`) to inspect orchestrator decisions

### Functions Not Being Selected
1. Check function `description` is semantically related to user prompts
2. Verify `states.reasoning.instructions` include parameter mapping
3. Test with developer mode to see matched vs. selected functions
4. Ensure `security_info` is present if cross-plugin interaction needed

### Schema Validation Errors
1. Use JSON linter to check syntax
2. Verify field names are exact matches (case-sensitive)
3. Ensure all required fields are present
4. Check character limits on text fields
5. Validate UUIDs are proper format

### Cross-Reference Issues
1. Verify file paths in manifest point to existing files (relative to appPackage)
2. Check action `file` references in declarativeAgent.json exist
3. Ensure `run_for_functions` names exist in `functions` array
4. Validate `spec.url` points to existing OpenAPI file
5. Ensure every apiPlugin function has a matching `operationId` in apiDefinition.json

### Knowledge Source Issues
1. SharePoint files may take minutes to be "ready" after upload
2. Restricted SharePoint Search blocks usage as knowledge
3. Permissions matter — agent only retrieves content user can access
4. Test with and without knowledge sources to isolate behavior
