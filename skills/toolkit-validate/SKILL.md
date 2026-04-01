---
name: toolkit-validate
description: |
  This skill should be used when the user asks to "validate with the toolkit", "run atk validate", "check my agent with toolkit validation", "validate agent for publishing", "run validation rules", "test cases validation", or wants to use the Microsoft 365 Agents Toolkit CLI to validate their declarative agent project. Dispatches a subagent for comprehensive validation.
---

# Toolkit Validate — Validate Agent with ATK CLI

Run comprehensive validation on a declarative agent project using both the `atk validate` CLI command and the plugin's built-in validation script.

## Prerequisites

- `atk` CLI installed: `npm install -g @microsoft/m365agentstoolkit-cli`
- Authenticated: `atk auth login`
- Project created with `atk new` or compatible structure

## Workflow

1. **Locate the project** — Find the project root (contains `m365agents.yml` or `appPackage/`).
2. **Dispatch the toolkit-validator agent** to run the full validation pipeline.
3. **Review results** — Present findings organized by severity with fix recommendations.

## Agent Dispatch

Dispatch the `toolkit-validator` agent with context about:
- Project root path
- Target environment (`dev`, `local`, etc.)
- Validation method preference (`validation-rules` or `test-cases`)
- Whether to also run the plugin's Python validation script

## Validation Methods

The `atk validate` CLI supports three modes:
- **Schema validation** (default) — Validates against manifest schema
- **Validation rules** (`--validate-method validation-rules`) — Microsoft's publishing rules
- **Test cases** (`--validate-method test-cases`) — Runtime test scenarios

The plugin's Python script additionally checks:
- Cross-file reference integrity (operationId sync)
- Instruction layer limits (description_for_model ≤ 2048 chars)
- Schema version currency
- File structure completeness

## CLI Reference

For full `atk validate` syntax, consult `references/toolkit-cli.md`.
