---
description: Scaffold a new declarative agent project using the M365 Agents Toolkit CLI (atk new)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Agent
argument-hint: "[agent-name] [--lang typescript|javascript|csharp]"
---

# Toolkit Create — Scaffold Declarative Agent Project

Scaffold a new Microsoft 365 Copilot Declarative Agent project using the `atk` CLI.

## Steps

1. Gather the agent name, language, output folder and whether API actions are needed from the arguments; ask the user (AskUserQuestion) for anything missing. Subagents cannot ask the user, so collect this before dispatching.

2. Dispatch the **toolkit-creator** agent with those details to handle the full workflow:
   - Check prerequisites (`atk` installed, authenticated)
   - Run `atk new -c declarative-agent` with provided options
   - Add capabilities if requested via `atk add capability`
   - Run post-creation validation with the plugin's validation script
   - Report created files and next steps

3. Pass the gathered details and any arguments to the agent as context. If it returns open questions, ask the user and dispatch it again.

4. After the agent completes, suggest:
   - Edit `appPackage/declarativeAgent.json` to customize instructions
   - Add capabilities with `/copilot-declarative-agent:add-capability`
   - Add API tools with `/copilot-declarative-agent:add-tool`
   - Validate with `/copilot-declarative-agent:toolkit-validate`

## CLI Reference

See `references/toolkit-cli.md` for full `atk new` syntax.
