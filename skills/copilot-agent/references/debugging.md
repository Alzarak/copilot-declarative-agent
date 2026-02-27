# Testing and Debugging

## Testing Approaches

### Agent Builder Test Pane
- Ephemeral agent instance in a side-by-side pane
- Available after name + description + instructions are provided
- Cannot share prompts, provide feedback, or @mention other agents
- Shows suggested starter prompts; use "New Chat" to reset
- Good for quick iteration on instructions

### Agents Toolkit F5 Preview
- Select "Preview your app (F5)" in Agents Toolkit pane
- Launches browser-based Copilot Chat with developer mode debugging
- Automatic developer mode for inspecting orchestrator behavior
- Best for debugging API plugin issues

### Manual Testing
1. Deploy/provision agent
2. Go to `https://m365.cloud.microsoft/chat`
3. Click conversation drawer icon next to "New Chat"
4. Select your declarative agent from the list
5. Test with conversation starters and edge cases

## Developer Mode

Enable: type `-developer on` in any Copilot Chat session with your agent selected.
Disable: `-developer off`

Shows debug information after each response.

### Debug Card Sections

**Agent Metadata:**
- Agent ID (title ID + manifest ID)
- Agent version
- Conversation ID
- Request ID
- Knowledge source usage summary

**Agent Capabilities:**
- Per-capability execution status
- Downloadable diagnostic .txt file with detailed results
- Shows which knowledge sources were queried and what was returned

**Agent Actions:**
- Action ID and version
- Matched functions (semantic match -- what the orchestrator considered)
- Selected functions (orchestrator decision -- what was actually called)
- Execution details: status, latency, request endpoint, HTTP method, headers, response

## Troubleshooting

| Issue | Likely Cause |
|-------|-------------|
| No debug info appears | Browser connection failed; restart F5 preview |
| No debug info despite connection | Orchestrator didn't need enterprise data for that prompt |
| "No functions selected for execution" | Function description not semantically related to the prompt |
| Empty or failed execution details | Unclear descriptions, invalid host URLs, or OpenAPI spec problems |
| Agent not appearing in Copilot | App not provisioned, admin hasn't enabled extensibility, or manifest misconfigured |
| Functions timing out | Plugin API execution limit is 10 seconds; optimize API response time |
| Instructions seem ignored | `description_for_model` over 2,048 chars (content beyond may be silently ignored) |
| Wrong function selected | Improve function `description` for better semantic matching |

## Testing Best Practices

1. **Test in multiple apps**: Word, Excel, Teams, Outlook, PowerPoint -- behavior may differ
2. **Check confirmation flows**: For consequential actions (`isConsequential: true`), test both Allow and Cancel
3. **Load testing**: Consider concurrent users and rapid queries if deploying broadly
4. **Peer/user testing**: Fresh eyes find gaps in instructions that the author misses
5. **Validate outputs**: Spot-check responses against source material for accuracy
6. **Test edge cases**: Long prompts, irrelevant questions, boundary scenarios
7. **Test with and without knowledge**: Isolate whether knowledge sources help or hinder
8. **Check token budget**: Use developer mode to verify responses aren't being truncated

## Deployment

### Agent Builder
Automatic -- agents are available immediately after creation.

### Agents Toolkit
Select "Provision" in the Lifecycle pane. Changes propagate in a few minutes after bumping `manifest.json` version.

### Publishing to Organization
Publish through Teams Admin Center for org-wide distribution. Requires admin approval.

### Government Tenants (GCC)
Limited support. Publishing via Agents Toolkit is NOT supported. Currently available for GCC only (not GCC High or DoD).

## Where Agents Are Available
- Microsoft 365 Copilot Chat (primary)
- Copilot in Teams
- Copilot in Word
- Copilot in PowerPoint
- Copilot in Outlook (limited)
