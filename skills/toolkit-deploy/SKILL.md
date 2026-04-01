---
name: toolkit-deploy
description: |
  This skill should be used when the user asks to "deploy my agent", "publish the agent", "deploy to production", "run atk deploy", "atk publish", "publish to org catalog", "package and deploy", "ship the agent", or wants to use the Microsoft 365 Agents Toolkit CLI to deploy/publish their declarative agent to an environment or the org app catalog. Dispatches a subagent for the full deployment pipeline.
---

# Toolkit Deploy — Deploy & Publish Declarative Agent

Deploy a declarative agent to a target environment and optionally publish to the organization app catalog using the `atk` CLI.

## Prerequisites

- `atk` CLI installed: `npm install -g @microsoft/m365agentstoolkit-cli`
- Authenticated: `atk auth login` (both M365 and Azure if deploying to cloud)
- Project validated (recommend running toolkit-validate first)
- Azure subscription configured (for cloud deployments)

## Workflow

1. **Pre-flight checks** — Verify authentication, validate the project, confirm target environment.
2. **Dispatch the toolkit-deployer agent** to execute the deployment pipeline.
3. **Report results** — Confirm successful deployment or surface errors with remediation steps.

## Agent Dispatch

Dispatch the `toolkit-deployer` agent with context about:
- Project root path
- Target environment name (e.g., `dev`, `staging`, `production`)
- Whether to also publish to org catalog after deployment
- Whether to run validation before deploying
- Any custom config file path

## Deployment Pipeline

The agent executes these steps:

1. **Validate** (optional) — `atk validate --env <env>` to catch issues pre-deploy
2. **Provision** — `atk provision --env <env>` to ensure cloud resources exist
3. **Deploy** — `atk deploy --env <env>` to deploy the application
4. **Package** — `atk package --env <env>` to build the distributable package
5. **Publish** (optional) — `atk publish --env <env>` to submit to org app catalog

Each step must succeed before the next. On failure, the agent reports the error and suggests fixes.

## Environment Management

Before deploying, verify the target environment exists:
```bash
atk env list
atk env add production --env dev  # Create from existing
```

## Post-Deployment

After successful deployment:
- Verify with `atk preview --env <env>` to confirm the agent works
- Check `atk launchinfo --manifest-id <id>` for launch URLs
- Share the app with collaborators: `atk collaborator grant --email <email> --env <env>`

## Rollback

To clean up a failed deployment:
```bash
atk uninstall -i false --mode env --env <env> --options 'm365-app,app-registration,bot-framework-registration'
```

## CLI Reference

For full command syntax, consult `references/toolkit-cli.md`.
