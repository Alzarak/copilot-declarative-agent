---
description: Validate a declarative agent project using the M365 Agents Toolkit CLI (atk validate)
allowed-tools: ["Bash", "Read", "Glob", "Grep", "Agent"]
argument-hint: "[--env dev] [--method validation-rules|test-cases]"
---

# Toolkit Validate — Validate Agent with ATK CLI

Run comprehensive validation using both the `atk validate` CLI and the plugin's built-in validation script.

## Steps

1. Dispatch the **toolkit-validator** agent to run the full validation pipeline:
   - Locate the project root
   - Run `atk validate` (schema validation)
   - Run `atk validate --validate-method validation-rules`
   - Run `atk validate --validate-method test-cases` (if requested)
   - Run the plugin's Python validation script for cross-reference checks
   - Manual quality checks on instruction limits and field compliance
   - Report findings by severity with fix recommendations

2. Pass environment and method preferences from arguments to the agent.

## CLI Reference

See `references/toolkit-cli.md` for full `atk validate` syntax.
