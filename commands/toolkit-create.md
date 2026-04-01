---
description: Scaffold a new declarative agent project using the M365 Agents Toolkit CLI (atk new)
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "AskUserQuestion", "Agent"]
argument-hint: "[agent-name] [--lang typescript|javascript|csharp]"
---

# Toolkit Create — Scaffold Declarative Agent Project

Scaffold a new Microsoft 365 Copilot Declarative Agent project using the `atk` CLI.

## Steps

1. Dispatch the **toolkit-creator** agent to handle the full workflow:
   - Check prerequisites (`atk` installed, authenticated)
   - Gather agent name, language, and options from user or arguments
   - Run `atk new -c declarative-agent` with provided options
   - Add capabilities if requested via `atk add capability`
   - Run post-creation validation with the plugin's validation script
   - Report created files and next steps

2. Pass any arguments from this command to the agent as context.

3. After the agent completes, suggest:
   - Edit `appPackage/declarativeAgent.json` to customize instructions
   - Add capabilities with `/copilot-declarative-agent:add-capability`
   - Add API tools with `/copilot-declarative-agent:add-tool`
   - Validate with `/copilot-declarative-agent:toolkit-validate`

## CLI Reference

See `references/toolkit-cli.md` for full `atk new` syntax.
