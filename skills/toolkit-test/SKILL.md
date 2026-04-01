---
name: toolkit-test
description: |
  This skill should be used when the user asks to "test my agent", "preview the agent", "run atk preview", "test in Teams", "test in Outlook", "preview locally", "provision and preview", "test agent in M365", or wants to use the Microsoft 365 Agents Toolkit CLI to test/preview their declarative agent. Dispatches a subagent for the provision-deploy-preview pipeline.
---

# Toolkit Test — Preview Declarative Agent

Test and preview a declarative agent using the `atk` CLI provision → deploy → preview pipeline.

## Prerequisites

- `atk` CLI installed: `npm install -g @microsoft/m365agentstoolkit-cli`
- Authenticated: `atk auth login`
- Project created and validated
- For local: Node.js, .NET SDK, Azure Functions Core Tools (run `atk doctor` to check)

## Workflow

1. **Check prerequisites** — Verify `atk` is installed, user is authenticated, and `atk doctor` passes.
2. **Determine environment** — Local testing or remote (cloud) testing.
3. **Dispatch the toolkit-tester agent** to execute the provision → deploy → preview pipeline.
4. **Report results** — Surface any errors and provide debugging guidance.

## Agent Dispatch

Dispatch the `toolkit-tester` agent with context about:
- Project root path
- Environment: `local` or named environment (e.g., `dev`)
- M365 host target: `teams` (default), `outlook`, or `office`
- Browser preference: `chrome`, `edge`, or `default`
- Whether to use desktop client (`--desktop`)

## Testing Pipeline

The agent executes these steps sequentially:

1. `atk provision --env <env>` — Provision cloud resources / local setup
2. `atk deploy --env <env>` — Deploy the application
3. `atk preview --env <env>` — Launch preview in browser/client

Each step must succeed before the next runs. On failure, the agent reports the error and suggests fixes.

## Debugging

After preview launches, suggest:
- Enable developer mode in M365 Copilot: `-developer on`
- Check Copilot orchestrator logs for function invocation issues
- Reference `references/debugging.md` for troubleshooting patterns

## CLI Reference

For full command syntax, consult `references/toolkit-cli.md`.
