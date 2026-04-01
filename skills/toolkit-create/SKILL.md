---
name: toolkit-create
description: |
  This skill should be used when the user asks to "scaffold a new agent with the toolkit", "create a declarative agent project", "atk new", "initialize a new copilot project", "set up a new M365 agent", "create agent with toolkit CLI", or wants to use the Microsoft 365 Agents Toolkit CLI to generate a new declarative agent project. Dispatches a subagent to handle the full creation workflow.
---

# Toolkit Create — Scaffold Declarative Agent Project

Scaffold a new Microsoft 365 Copilot Declarative Agent project using the `atk` CLI from the Microsoft 365 Agents Toolkit.

## Prerequisites

- `atk` CLI installed: `npm install -g @microsoft/m365agentstoolkit-cli`
- Authenticated: `atk auth login`

## Workflow

1. **Check prerequisites** — Verify `atk` is installed and the user is authenticated.
2. **Gather requirements** — Determine agent name, capabilities, language preference, and whether API actions are needed.
3. **Dispatch the toolkit-creator agent** to execute the scaffolding workflow.
4. **Post-creation** — Run the plugin's validation script on the generated appPackage to catch issues early.

## Agent Dispatch

Dispatch the `toolkit-creator` agent with context about:
- Agent name and purpose
- Programming language (typescript recommended)
- Whether to include API actions (`--openapi-spec-location` if provided)
- Target folder path
- Any capabilities to add after creation (`atk add capability`)

## CLI Reference

For full `atk new` syntax and parameters, consult `references/toolkit-cli.md`.

## Post-Creation Steps

After the agent completes scaffolding:
1. Validate the generated appPackage with the plugin's validation script
2. Suggest next steps: edit instructions, add capabilities, add API tools
3. Remind about icon replacement (color.png 192x192, outline.png 32x32)
