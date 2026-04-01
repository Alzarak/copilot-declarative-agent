---
description: Test/preview a declarative agent using the M365 Agents Toolkit CLI (atk provision + deploy + preview)
allowed-tools: ["Bash", "Read", "Glob", "Grep", "Agent"]
argument-hint: "[--env local] [--host teams|outlook|office] [--browser chrome|edge]"
---

# Toolkit Test — Preview Declarative Agent

Test and preview a declarative agent using the `atk` CLI provision → deploy → preview pipeline.

## Steps

1. Dispatch the **toolkit-tester** agent to execute the pipeline:
   - Check prerequisites (`atk doctor`)
   - Validate before testing
   - Run `atk provision --env <env>`
   - Run `atk deploy --env <env>`
   - Run `atk preview --env <env> --m365-host <host>`
   - Report results and debugging tips

2. Pass environment, host, and browser preferences from arguments to the agent.

3. Default to `--env local` and `--m365-host teams` if not specified.

## CLI Reference

See `references/toolkit-cli.md` for full command syntax.
