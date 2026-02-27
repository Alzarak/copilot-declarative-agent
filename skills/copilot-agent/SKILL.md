---
name: copilot-agent
description: |
  Create, validate, and manage Microsoft 365 Copilot Declarative Agents. Use this skill whenever the user mentions Copilot agents, declarative agents, appPackage folders, Teams Toolkit, Microsoft 365 Agents Toolkit, TypeSpec agents, or wants to create/validate/update Copilot agent configurations. Trigger on phrases like "create a Copilot agent", "validate my appPackage", "update declarative agent", "check agent manifest", "verify appPackage folder", "add an API tool", "optimize instructions", "add capability", or any work related to Copilot extensibility.
---

# Microsoft 365 Copilot Declarative Agent Skill

Customizable AI agents that run on the Microsoft 365 Copilot orchestrator, scoped to specific business needs.

## Task Routing

Read the appropriate reference file based on the task:

| Task | Reference File |
|------|---------------|
| Writing/updating agent instructions, `description_for_model`, or per-function guidance | `references/instruction-architecture.md` |
| Validating an appPackage, troubleshooting issues | `references/validation.md` |
| Adding a new API tool, creating an agent, modifying files, configuring behavior_overrides/worker_agents | `references/common-tasks.md` |
| Looking up JSON schemas, field limits, schema versions, runtime limits | `references/file-schemas.md` |
| Configuring capabilities (WebSearch, CodeInterpreter, Email, etc.) | `references/capabilities.md` |
| Configuring knowledge sources (SharePoint, Teams, Email, connectors) | `references/knowledge-sources.md` |
| Building agents with TypeSpec | `references/typespec.md` |
| Configuring Adaptive Card response templates | `references/adaptive-cards.md` |
| Configuring security (auth types, isConsequential, security_info, data_handling, sensitivity labels) | `references/security-compliance.md` |
| Migrating instructions for GPT 5.1+, fixing tone drift, stabilizing step order, instruction audit | `references/gpt51-migration.md` |
| Testing, debugging, developer mode, deployment | `references/debugging.md` |

## App Package Structure

```
appPackage/
├── manifest.json           # Teams app manifest (required)
├── declarativeAgent.json   # Declarative agent definition (required)
├── apiPlugin.json          # API plugin configuration (optional, for actions)
├── apiDefinition.json      # OpenAPI specification (optional, with apiPlugin)
├── color.png               # Color icon 192x192 (required)
└── outline.png             # Outline icon 32x32 (required)
```

## Three Building Approaches

| Approach | Tool | Best For |
|----------|------|----------|
| No-code | Agent Builder (M365 Copilot app) | Quick in-browser creation, no API actions |
| Code-first | M365 Agents Toolkit (VS Code) | Full control, JSON or TypeSpec |
| Manual | Hand-crafted JSON | Maximum flexibility |

## Instruction Architecture (Summary)

Copilot provides **five layers** for guiding behavior. Distribute guidance to the narrowest applicable layer.

| Layer | Location | Purpose | Limit |
|-------|----------|---------|-------|
| Agent instructions | `declarativeAgent.json` → `instructions` | Overall behavior, workflows | **8,000 chars** |
| Plugin description | `apiPlugin.json` → `description_for_model` | When to use this plugin | **2,048 chars** |
| Function description | `apiPlugin.json` → `functions[].description` | What this function does | ~4,000 chars |
| Reasoning instructions | `functions[].states.reasoning.instructions` | How to call — parameters, chaining | Array of strings |
| Responding instructions | `functions[].states.responding.instructions` | How to present results | Array of strings |

**Runtime budget**: 4,096 tokens total. Optimize for ~66% utilization.

## Quick Reference

| Field | Limit |
|-------|-------|
| manifest `name.short` | 30 chars |
| manifest `description.short` | 80 chars |
| agent `name` | 100 chars |
| agent `description` | 1000 chars |
| agent `instructions` | 8000 chars |
| agent `conversation_starters` | 6 items max |
| agent `actions` | 1–10 items |
| `description_for_model` | 2048 chars |
| `disclaimer.text` | 500 chars |
| color.png | 192x192 px |
| outline.png | 32x32 px |

## 12 Capability Types (v1.6)

WebSearch, OneDriveAndSharePoint, GraphConnectors, GraphicArt, CodeInterpreter, Dataverse, TeamsMessages, Email, People, ScenarioModels, Meetings, EmbeddedKnowledge (not yet available)

See `references/capabilities.md` for configuration details.

## Schema Versions

| File | Current Version | Schema URL |
|------|-----------------|------------|
| manifest.json | `1.24` | `https://developer.microsoft.com/json-schemas/teams/v1.24/MicrosoftTeams.schema.json` |
| declarativeAgent.json | `v1.6` | `https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.6/schema.json` |
| apiPlugin.json | `v2.4` | `https://aka.ms/json-schemas/copilot/plugin/v2.4/schema.json` |
| apiDefinition.json | `3.0.0` | OpenAPI specification |

## Validation Script

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_apppackage.py [path_to_apppackage]
```
