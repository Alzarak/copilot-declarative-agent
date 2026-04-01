---
description: Deploy and publish a declarative agent using the M365 Agents Toolkit CLI (atk provision + deploy + publish)
allowed-tools: ["Bash", "Read", "Glob", "Grep", "AskUserQuestion", "Agent"]
argument-hint: "[--env dev] [--publish]"
---

# Toolkit Deploy — Deploy & Publish Declarative Agent

Deploy a declarative agent to a target environment and optionally publish to the org app catalog.

## Steps

1. Dispatch the **toolkit-deployer** agent to execute the deployment pipeline:
   - Pre-flight checks (auth, environment exists, validation)
   - Run `atk provision --env <env>`
   - Run `atk deploy --env <env>`
   - Run `atk package --env <env>`
   - Run `atk publish --env <env>` (only if `--publish` flag or user confirms)
   - Post-deployment verification
   - Report results with rollback instructions if needed

2. Pass environment and publish preference from arguments to the agent.

3. **Always confirm with the user before publishing** — it submits to the org catalog.

## CLI Reference

See `references/toolkit-cli.md` for full command syntax.
