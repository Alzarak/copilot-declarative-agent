# Copilot Declarative Agent — Complete Reference Guide

> **Last updated**: February 2026 | **Schema**: declarativeAgent v1.6, apiPlugin v2.2+ | **Model**: GPT 5.1+
> **Source**: Microsoft Learn official documentation + community best practices

---

## Table of Contents

1. [What Are Declarative Agents](#1-what-are-declarative-agents)
2. [Architecture & Data Flow](#2-architecture--data-flow)
3. [App Package Structure](#3-app-package-structure)
4. [Declarative Agent Manifest (v1.6)](#4-declarative-agent-manifest-v16)
5. [Writing Effective Instructions](#5-writing-effective-instructions)
6. [Instruction Patterns & Templates](#6-instruction-patterns--templates)
7. [GPT 5.1+ Model Migration](#7-gpt-51-model-migration)
8. [Capabilities (Knowledge Sources)](#8-capabilities-knowledge-sources)
9. [API Plugins & Tool Calling](#9-api-plugins--tool-calling)
10. [API Plugin Manifest (v2.2+)](#10-api-plugin-manifest-v22)
11. [OpenAPI Document Best Practices](#11-openapi-document-best-practices)
12. [Function States & Instruction Layers](#12-function-states--instruction-layers)
13. [Adaptive Cards & Response Rendering](#13-adaptive-cards--response-rendering)
14. [Chaining & Multi-Step Workflows](#14-chaining--multi-step-workflows)
15. [Testing & Debugging](#15-testing--debugging)
16. [Runtime Limits & Optimization](#16-runtime-limits--optimization)
17. [Security & Compliance](#17-security--compliance)
18. [Building Tools](#18-building-tools)
19. [Common Pitfalls & Troubleshooting](#19-common-pitfalls--troubleshooting)
20. [Quick Reference Tables](#20-quick-reference-tables)

---

## 1. What Are Declarative Agents

Declarative agents are customized versions of Microsoft 365 Copilot created through **configuration, not code**. They run on the same orchestrator, foundation models, and trusted AI services that power M365 Copilot.

### Core Components

| Component | Purpose | Limit |
|-----------|---------|-------|
| **Name** | Display name for discovery | 30 chars (M365 Copilot) / 100 chars (Agents Toolkit) |
| **Description** | What the agent does | 1,000 characters |
| **Instructions** | Behavioral guidelines & workflows | 8,000 characters |
| **Capabilities** | Built-in AI capabilities (knowledge sources) | 12 types available |
| **Actions** | API plugins for external data/actions | 1–10 plugins |
| **Conversation Starters** | Example prompts shown to users | Max 6 (v1.6) / 12 (v1.5) |

### Optimal Use Cases

- Information retrieval from Microsoft 365 or external sources
- Simple, single-step workflows
- Productivity enhancement within existing M365 workflows
- Employee self-help with enhanced knowledge
- Real-time customer support with system integrations

### Poor Fit

- Complex decision trees requiring iterative processing
- Large data processing or full document contexts
- Custom AI models or specialized training data
- Workflows requiring looped operation plans
- Streaming API workloads or on-premises data sources

---

## 2. Architecture & Data Flow

```
User Prompt
    ↓
Microsoft 365 Copilot Client (Teams, Word, PowerPoint, Outlook)
    ↓
Orchestrator (developer has NO control)
    ↓
┌─────────────────────────────────────────┐
│ 1. Agent instructions injected          │
│ 2. Capabilities/knowledge grounded      │  ← Sequential processing
│ 3. Plugin functions matched & called    │    (no chained grounding
│ 4. Response generated                   │     or looped operations)
└─────────────────────────────────────────┘
    ↓
User Response
```

### Key Architecture Constraints

| Limit | Value | Notes |
|-------|-------|-------|
| Grounding record limit | 50 items | Affects contextual data available |
| Plugin response limit | 25 items | Constrains external API response sizes |
| Token limit | 4,096* | Includes ALL context + response data |
| Timeout limit | 45 seconds* | Includes network latency + processing |

*\* Optimize for ~66% of technical limit due to external overhead.*

### Plugin Injection Rules

- **≤5 plugins**: Always injected into prompt
- **>5 plugins**: Semantic matching based on plugin `description`, not individual functions
- **Functions per plugin**: Unlimited, but quality degrades >10 functions due to token limits

---

## 3. App Package Structure

Every declarative agent is packaged as a Microsoft 365 app:

```
appPackage/
├── manifest.json              # App manifest (references declarativeAgent.json)
├── declarativeAgent.json      # Agent manifest (v1.6) — instructions, capabilities, actions
├── apiPlugin.json             # Plugin manifest (v2.2+) — functions, runtimes
├── apiDefinition.json         # OpenAPI 3.0 spec (or .yaml)
├── color.png                  # Color icon (192x192)
└── outline.png                # Outline icon (32x32)
```

### File References

```
manifest.json
  └── "copilotAgents.declarativeAgents[0].file" → "declarativeAgent.json"

declarativeAgent.json
  └── "actions[0].file" → "apiPlugin.json"

apiPlugin.json
  └── "runtimes[0].spec.url" → "apiDefinition.json"
```

---

## 4. Declarative Agent Manifest (v1.6)

### Schema URL
```
https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.6/schema.json
```

### Root Object Properties

| Property | Type | Required | Limit | Description |
|----------|------|----------|-------|-------------|
| `version` | String | Yes | — | Set to `"v1.6"` |
| `name` | String | Yes | 100 chars | Agent display name (localizable) |
| `description` | String | Yes | 1,000 chars | Agent purpose (localizable) |
| `instructions` | String | Yes | 8,000 chars | Behavioral guidelines (Markdown) |
| `capabilities` | Array | No | 1 per type | Knowledge sources & AI capabilities |
| `conversation_starters` | Array | No | **6** (v1.6) | Example prompts for users |
| `actions` | Array | No | **1–10** | API plugin references |
| `behavior_overrides` | Object | No | — | Modify default agent behavior |
| `disclaimer` | Object | No | 500 chars | Text shown at conversation start |
| `sensitivity_label` | Object | No | — | Microsoft Purview label (for embedded files) |
| `worker_agents` | Array | No | — | Other agents this agent can use (preview) |
| `user_overrides` | Array | No | — | Capabilities users can modify |

### v1.6 Changes from v1.5

- `sensitivity_label` — Purview sensitivity labels (for embedded files)
- `worker_agents` — Multi-agent composition (preview)
- `user_overrides` — User-modifiable capabilities via UI
- `EmbeddedKnowledge` capability — Local files in app package (not yet available)
- `items_by_id` on Meetings — Scope to specific meetings
- `include_related_content` on People — Include related docs/emails/Teams messages
- `group_mailboxes` on Email — Up to 25 group mailboxes
- `conversation_starters` limit changed to **6** (was 12 in v1.5)
- `actions` limit formalized as **1–10**

### Minimal Example

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.6/schema.json",
  "version": "v1.6",
  "name": "IT Help Desk Agent",
  "description": "Helps employees resolve common IT problems and create support tickets.",
  "instructions": "# OBJECTIVE\nGuide users through IT issue resolution...",
  "conversation_starters": [
    { "title": "VPN Issues", "text": "I can't connect to VPN" },
    { "title": "Password Reset", "text": "How do I reset my password?" }
  ],
  "capabilities": [
    { "name": "WebSearch" },
    { "name": "People" }
  ],
  "actions": [
    { "id": "serviceNowPlugin", "file": "apiPlugin.json" }
  ]
}
```

### behavior_overrides

```json
{
  "behavior_overrides": {
    "suggestions": { "disabled": true },
    "special_instructions": { "discourage_model_knowledge": true }
  }
}
```

- `suggestions.disabled: true` — Disables follow-up suggestion chips
- `discourage_model_knowledge: true` — Agent only uses provided knowledge, not model training data

### worker_agents (Preview)

```json
{
  "worker_agents": [
    { "id": "P_2c27ae89-1f78-4ef7-824c-7d83f77eda28" }
  ]
}
```

The `id` is the title ID from the application containing the worker agent.

### user_overrides

```json
{
  "user_overrides": [
    {
      "path": "$.capabilities[?(@.name == 'OneDriveAndSharePoint')]",
      "allowed_actions": ["remove"]
    }
  ]
}
```

Allows users to remove specific capabilities via UI controls.

---

## 5. Writing Effective Instructions

### The Microsoft-Recommended Structure

```markdown
# OBJECTIVE
[Agent's role, goals, and purpose — 1-3 sentences]

# RESPONSE RULES
- [Behavioral constraints as bullet points]
- Ask one clarifying question at a time
- Present information as concise bullet points or tables
- Always confirm before moving to the next step
- Use tools only if data is sufficient; otherwise, ask the user

# WORKFLOW

## Step 1: [Step Name]
- **Goal:** [Purpose of this step]
- **Action:**
  - [What the agent should do]
  - [Which tools to use]
- **Transition:** [Criteria for moving to next step]

## Step 2: [Step Name]
...

# OUTPUT FORMATTING RULES
- Use bullets for actions, lists, next steps
- Use tables for structured data
- Avoid long paragraphs; keep responses skimmable
- Always confirm before ending or submitting

# EXAMPLES

## Valid Example
**User:** "[example query]"
**Assistant:**
- "[step 1 response]"
- "[step 2 response]"

## Invalid Example
- "[what NOT to do]" *(explanation)*
```

### Core Principles

1. **Focus on what Copilot SHOULD do**, not what to avoid
2. **Use precise, specific verbs**: ask, search, send, check, use
3. **Supplement with examples** to minimize ambiguity
4. **Define nonstandard terms** unique to the organization
5. **Structure in Markdown** with `#`, `##`, `-`, `1.` formatting

### Goal/Action/Transition Pattern

Every workflow step MUST include:

- **Goal**: The purpose of the step
- **Action**: What the agent should do and which tools to use
- **Transition**: Clear criteria for moving to the next step or ending

### Atomic Tasks

Break multi-action instructions into clearly separated units:

**Bad**: "Extract metrics and summarize findings."

**Good**:
1. Extract metrics from the document.
2. Summarize findings based on extracted metrics.

### Explicitly Reference Capabilities

Always call out names of actions, capabilities, and knowledge sources:

| Type | Example Reference |
|------|------------------|
| Actions | "Use `Jira` to fetch tickets." |
| Copilot connectors | "Use `ServiceNow KB` for help articles." |
| SharePoint | "Reference SharePoint internal documents." |
| Email | "Check user emails for relevant information." |
| Teams | "Search Teams chat history." |
| Code interpreter | "Use code interpreter to generate charts." |
| People | "Use people knowledge to fetch user email." |

### Few-Shot Examples

- **Simple scenarios**: No examples needed
- **Complex scenarios**: Use few-shot prompting (multiple examples)
- Always include both **Valid** and **Invalid** examples
- Use multi-turn dialogue format (User/Assistant exchanges)
- Show the agent's reasoning process in examples

### Tone, Verbosity & Output Format

**Always specify these explicitly** — if omitted, the model infers them inconsistently:

```markdown
- Tone: professional and concise
- Output: Three bullet points per section
- Return only the requested format; no explanations
```

### Self-Evaluation Step

Add a final self-check:

```markdown
Before finalizing, confirm that all items from Section A appear in the summary.
```

---

## 6. Instruction Patterns & Templates

### Pattern 1: Deterministic Workflows

Convert ambiguous multi-task requests into explicit, sequential steps:

```markdown
## Task: Metrics and ROI (Deterministic)

### Definitions (Do not invent)
- Metrics to compute: [Metric1], [Metric2], [Metric3]
- ROI definition: ROI = (Benefit - Cost) / Cost
- Source of truth: Use ONLY the provided document(s)

### Steps (Sequential — do not reorder)
Step 1: Locate inputs for [Metric1-3]. Quote the section/table name.
Step 2: Compute [Metric1-3] exactly as defined. If missing, stop and ask.
Step 3: Compute ROI using the definition above. Do not substitute formulas.
Step 4: Output ONLY the table below.

### Output format
Return a single Markdown table: Metric | Value | Source | Notes

### Final check
Confirm every metric has (a) a value, (b) a source, and (c) no assumptions.
```

### Pattern 2: Parallel vs Sequential Structure

```markdown
Section A — Extract Data (Non-Sequential)
- Extract pricing changes.
- Extract margin changes.
- Extract sentiment themes.

Section B — Build the Summary (Sequential)
Step 1: Integrate all findings from Section A.
Step 2: Produce the 2-page call prep summary.
```

### Pattern 3: Explicit Decision Rules

```markdown
Read the product report.
Check category performance.
If performance is stable or improving, write the summary section.
If performance declines or anomalies are detected, write the risks/issues section.
```

### Pattern 4: Output Contract

```markdown
## Output Contract (Mandatory)
Goal: [one sentence]
Format: [bullet list | table | 2 pages | JSON]
Detail level: [short | medium | detailed] — do not exceed [X] bullets per section
Tone: [Professional | Friendly | Efficient]
Include: [A, B, C]
Exclude: No extra recommendations, no extra context, no "helpful tips"
```

### Pattern 5: Reasoning Control

**Deep reasoning:**
```markdown
Use deep reasoning. Break the problem into steps, analyze each step,
evaluate alternatives, and justify the final decision. Reflect before answering.
```

**Fast/minimal reasoning:**
```markdown
Short answer only. No reasoning or explanation. Provide the final result only.
```

### Pattern 6: Literal-Execution Header (GPT 5.1 Stability)

```markdown
Always interpret instructions literally.
Never infer intent or fill in missing steps.
Never add context, recommendations, or assumptions.
Follow step order exactly with no optimization.
Respond concisely and only in the requested format.
Do not call tools unless a step explicitly instructs you to do so.
```

### Pattern 7: Instruction Audit Prompt

```markdown
You are reviewing agent instructions for 5.1 stability.

INPUT
<instructions>[PASTE CURRENT INSTRUCTIONS]</instructions>

CHECKS
- Step order: identify ambiguity, missing/merged steps → propose atomic steps
- Tool use: identify auto-calls, retries → add "use only in step X; no auto-retry"
- Grounding: detect inference, blending → add "cite only retrieved; no inference"
- Missing-data handling: → add "stop and ask the user"
- Verbosity: → replace with "return only the requested format"
- Contradictions: resolve; prefer explicit over implied
- Vague verbs ("verify", "process", "handle"): replace with precise actions
- Safety: prohibit step reordering, optimization, or reinterpretation

OUTPUT
- Header patch (3–6 lines)
- Top 5 changes (bullet: "Issue → Fix")
- Example rewrite (≤10 lines) for the riskiest step
```

---

## 7. GPT 5.1+ Model Migration

### What Changed

| GPT 5.0 | GPT 5.1+ |
|----------|----------|
| **Literal-first**: follows instructions step-by-step | **Intent-first**: interprets what instructions *intended* |
| Honors numbering, structure exactly | May reorganize plans to fix/optimize them |
| Won't fill in missing information | Fills gaps and infers missing steps |
| Consistent professional tone | Dynamically selects tone and verbosity |
| Fixed reasoning depth | Adaptive reasoning per request/sub-task |

### 8 Output Profiles in GPT 5.1

Default, Professional, Friendly, Candid, Quirky, Efficient, Nerdy, Cynical

You can explicitly prompt for these or let the model infer them.

### Common Symptoms After Migration

- Steps become reordered
- Parallel tasks become sequential
- Model blends steps ("extract and summarize")
- Tone drifts toward "educational" or "chatty"
- Model creates or removes steps based on inferred context

### Migration Strategy

| Scenario | Approach |
|----------|----------|
| Fixed workflow/format required | Use strict step-by-step instructions + literal-execution header |
| Goals clear, tools well-defined | Use goal-focused prompts with guardrails, let model plan |
| Existing agent drifting | Add stabilizing header as interim fix, then restructure |

### When to Use Strict Instructions

- Fixed business processes
- Specific formatting rules
- Required reasoning/retrieval sequences
- Compliance or audit requirements

### When to Embrace Adaptive Reasoning

- Tools and knowledge sources are well-defined
- Output format is flexible
- Goal is more important than exact path
- Simple, routine tasks

---

## 8. Capabilities (Knowledge Sources)

### All 12 Capability Types (v1.6)

| Capability | `name` Value | Key Properties | Limits |
|------------|-------------|----------------|--------|
| Web Search | `WebSearch` | `sites[].url` | 4 sites; URLs ≤2 path segments, no query params |
| OneDrive & SharePoint | `OneDriveAndSharePoint` | `items_by_url`, `items_by_sharepoint_ids` | Omit both = all sources |
| Copilot Connectors | `GraphConnectors` | `connections[].connection_id` | KQL filtering, path/container scoping |
| Image Generator | `GraphicArt` | — | — |
| Code Interpreter | `CodeInterpreter` | — | Python code execution |
| Dataverse | `Dataverse` | `knowledge_sources[].host_name`, `skill`, `tables` | — |
| Teams Messages | `TeamsMessages` | `urls[].url` | 5 URLs; omit = all channels/chats |
| Email | `Email` | `shared_mailbox`, `group_mailboxes`, `folders` | 25 group mailboxes |
| People | `People` | `include_related_content` | Related content = docs/emails/Teams |
| Scenario Models | `ScenarioModels` | `models[].id` | — |
| Meetings | `Meetings` | `items_by_id[].id`, `is_series` | 5 meeting IDs |
| Embedded Knowledge | `EmbeddedKnowledge` | `files[].file` | 10 files, 1MB each (not yet available) |

### Knowledge Source Best Practices

- **Relevance over quantity** — Only add what helps answer expected questions
- **Less is more** — Copilot performs best with focused, reasonably-sized documents
- **Scope team chats** — Specific channels > all chats
- **Test with and without** — Verify the agent actually uses added knowledge
- **Refresh periodically** — Keep content current and accurate
- **Permissions matter** — Agent can only retrieve content the user has access to

### Embedded Knowledge File Types

`.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`, `.txt`, `.pdf` — max 1MB each, max 10 files

### WebSearch URL Rules

- Max 2 path segments: `https://contoso.com/projects/mark-8` (valid)
- 3+ segments invalid: `https://contoso.com/projects/mark-8/beta` (invalid)
- No query parameters allowed
- Max 4 URLs

---

## 9. API Plugins & Tool Calling

### How API Plugins Work

1. User asks a question
2. Orchestrator matches intent to plugin functions
3. Agent asks user to confirm data sharing (first time)
4. Plugin authenticates (if needed)
5. Agent sends API request
6. API returns response
7. Agent generates natural language response

### Plugin Types

| Type | Described By |
|------|-------------|
| API plugins | OpenAPI description |
| Copilot Studio actions | Copilot Studio conversation map |
| Message extension plugins | App manifest |

### Confirmation Rules

- **First connection**: Always asks user to confirm
- **Read-only operations**: No subsequent confirmation needed
- **Write operations**: Always require confirmation
- Override with `x-openai-isConsequential` in OpenAPI spec

### Plugin Injection

- ≤5 plugins → Always injected into prompt
- >5 plugins → Semantic matching on plugin `description` (not individual functions)
- All functions returned even if only one matched

---

## 10. API Plugin Manifest (v2.2+)

### Schema URL (Latest: v2.4)
```
https://aka.ms/json-schemas/copilot/plugin/v2.2/schema.json
```

### Root Object

| Property | Type | Required | Limit | Description |
|----------|------|----------|-------|-------------|
| `schema_version` | String | Yes | — | `"v2.2"` or later |
| `name_for_human` | String | Yes | 20 chars | Plugin display name |
| `namespace` | String | Yes | — | Unique identifier (`^[A-Za-z0-9]+`) |
| `description_for_human` | String | Yes | 100 chars | User-facing description |
| `description_for_model` | String | No | **2,048 chars** | Model-facing description (CRITICAL) |
| `functions` | Array | No | — | Available functions |
| `runtimes` | Array | No | — | Runtime configurations |
| `capabilities` | Object | No | — | Plugin-level capabilities |

### Function Object

| Property | Type | Description |
|----------|------|-------------|
| `name` | String | Must match `operationId` in OpenAPI spec |
| `description` | String | Model-facing function description |
| `parameters` | Object | JSON Schema subset for function params |
| `returns` | Object | Return value description |
| `states` | Object | `reasoning` and `responding` state configs |
| `capabilities` | Object | `confirmation`, `response_semantics`, `security_info` |

### Runtime Types

```json
// OpenAPI Runtime
{
  "type": "OpenApi",
  "auth": { "type": "OAuthPluginVault", "reference_id": "..." },
  "spec": { "url": "apiDefinition.json" },
  "run_for_functions": ["getItems", "createItem"]
}
```

### Authentication Types

| Type | Use Case |
|------|----------|
| `None` | Public APIs, no auth required |
| `OAuthPluginVault` | OAuth 2.0 (reference_id from registration) |
| `ApiKeyPluginVault` | API key-based auth (reference_id from registration) |

### security_info (v2.2+)

```json
{
  "capabilities": {
    "security_info": {
      "data_handling": ["GetPrivateData", "ResourceStateUpdate"]
    }
  }
}
```

| Value | Meaning |
|-------|---------|
| `GetPublicData` | Retrieves from unauthenticated external source |
| `GetPrivateData` | Retrieves from authenticated source or current app |
| `DataTransform` | Returns output based on input only |
| `DataExport` | Writes data to external location |
| `ResourceStateUpdate` | Changes state requiring user confirmation |

### progress_style (OpenAPI spec object)

Controls how function execution progress is shown:

| Value | Behavior |
|-------|----------|
| `None` | No progress indicator |
| `ShowUsage` | Shows the function is being called |
| `ShowUsageWithInput` | Shows function + input parameters |
| `ShowUsageWithInputAndOutput` | Shows function + input + output |

---

## 11. OpenAPI Document Best Practices

### Essential Elements

1. **info.description** — Brief, clear description of what the API does. This becomes the plugin description.

2. **operationId** — Unique identifier per operation. Shows in debugger output. Must match function `name` in plugin manifest.

3. **Operation descriptions** — Clear, semantic descriptions for each endpoint. Copilot uses these to match user intent to API operations.

4. **Parameter descriptions** — Include description, type, and examples for every parameter.

5. **Response definitions** — Define all possible responses (success + error) with schemas and examples.

### Example

```yaml
info:
  title: Repair Service
  description: A simple service to manage repairs for various items
  version: 1.0.0

paths:
  /repairs:
    get:
      operationId: listRepairs
      summary: List all repairs
      description: Returns a list of repairs with their details and images
      parameters:
        - name: assignedTo
          in: query
          description: The name or ID of the person assigned to the repair
          schema:
            type: string
          required: false
      responses:
        '200':
          description: A list of repairs
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Repair'
              examples:
                example1:
                  value:
                    - id: "1"
                      item: "Laptop"
                      status: "In Progress"
                      assignedTo: "John Doe"
        '404':
          description: No repairs found
```

### Validation

Use [Hidi](https://github.com/microsoft/OpenAPI.NET/tree/main/src/Microsoft.OpenApi.Hidi) or similar tools to validate against the OpenAPI Specification.

---

## 12. Function States & Instruction Layers

### The 5-Layer Instruction Architecture

```
Layer 1: declarativeAgent.instructions (8,000 chars)
  └── Agent-level behavior, workflows, response rules

Layer 2: apiPlugin.description_for_model (2,048 chars — CRITICAL)
  └── Plugin-level orchestration guidance

Layer 3: function.description (~4,000 chars)
  └── Per-function purpose and parameter guidance

Layer 4: function.states.reasoning.instructions (Array)
  └── Instructions for when the model is planning/calling functions

Layer 5: function.states.responding.instructions (Array)
  └── Instructions for when the model is generating user-visible text
```

### States Object

```json
{
  "states": {
    "reasoning": {
      "description": "Describes function purpose during planning",
      "instructions": [
        "If user mentions a city, use the city parameter.",
        "Only use amenities from the enum list.",
        "Find closest match or ignore if no match."
      ],
      "examples": ["Example invocation..."]
    },
    "responding": {
      "description": "Describes function purpose during response generation",
      "instructions": [
        "Examine the output of the function.",
        "Do not include information not in JSON results.",
        "If error field present, provide error code and message.",
        "Extract and include as much relevant information as possible."
      ],
      "examples": []
    }
  }
}
```

### Key Rules

- **reasoning.instructions** (array) = augments built-in prompts
- **reasoning.instructions** (string) = overrides built-in prompts entirely
- **responding** state = model generates text, **cannot invoke functions**
- Functions without states rely on description and OpenAPI spec alone

### description_for_model Best Practices

- Keep under 2,048 characters (truncated beyond)
- Focus on **when** to use the plugin, not individual function details
- Avoid duplicating function-specific guidance (that goes in function descriptions and states)
- Detect bloat: if >50% is function-specific, redistribute to states

---

## 13. Adaptive Cards & Response Rendering

### response_semantics Object

```json
{
  "capabilities": {
    "response_semantics": {
      "data_path": "$.results",
      "properties": {
        "title": "$.name",
        "subtitle": "$.description",
        "url": "$.link",
        "thumbnail_url": "$.imageUrl",
        "information_protection_label": "$.ipLabel"
      },
      "static_template": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
          { "type": "TextBlock", "text": "${name}", "weight": "Bolder" },
          { "type": "TextBlock", "text": "${description}" }
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "View", "url": "${link}" }
        ]
      }
    }
  }
}
```

### Three Template Modes

| Mode | Property | Description |
|------|----------|-------------|
| **Inline/Static** | `static_template` | Adaptive Card JSON embedded in manifest |
| **File Reference** | `static_template` with `$ref` | Card in separate file |
| **Dynamic** | `template_selector` | JSONPath to card in API response |

### Semantic Properties

| Property | Purpose |
|----------|---------|
| `title` | Citation title |
| `subtitle` | Citation subtitle |
| `url` | Citation link |
| `thumbnail_url` | Thumbnail image |
| `information_protection_label` | Sensitivity indicator |
| `template_selector` | Dynamic card selector (JSONPath) |

---

## 14. Chaining & Multi-Step Workflows

### Pattern: Output as Input

Use one function's result as input for another:

```
Instructions: Get the weather, then create a task with the temperature.
Flow: getWeather(location="Prague") → createTask(title="{weather output}")
```

### Pattern: Conversation History

Use prior responses for follow-up actions:

```
Instructions:
1. When user asks to list to-dos, call getTasks.
2. After listing, if user asks to delete, use the ID from the response.

Flow: getTasks() → displays list → deleteTask(id=from_history)
```

### Pattern: SharePoint + API

Combine knowledge sources and actions:

```
Instructions: Get project statuses from SharePoint, create a to-do for each.
Flow: SharePoint knowledge → createTask() for each project
```

### Pattern: API + Code Interpreter

```
Instructions: List all to-dos, then plot a chart of the output.
Flow: getTasks() → Code Interpreter generates chart
```

### Multi-Turn Conversation Design

When functions require multiple parameters:

```markdown
If user asks about the weather:
- Ask the user for location.
- Ask the user for forecast day.
- Ask the user for unit system.
- Only call **getWeather** when you collect all the values.
```

---

## 15. Testing & Debugging

### Testing Strategies

1. **Built-in test chat** — Agent Builder right pane. Test frequently.
2. **Conversation starters** — Verify all work as expected.
3. **Edge cases** — Test long questions, irrelevant questions, ambiguous requests.
4. **Cross-app testing** — Test in Teams, Word, Excel, Outlook.
5. **Confirmation flows** — Test Allow and Cancel/Deny for consequential actions.
6. **Peer testing** — Have colleagues test to find gaps.
7. **Output validation** — Spot-check answers against source material.
8. **Compare against base Copilot** — Verify agent adds value over default.

### Developer Mode

Enable with `-developer on` in Copilot Chat to see debug cards showing:

- Agent metadata
- Selected functions
- Plugin execution details
- Grounding sources used

### Testing Checklist

- [ ] All conversation starters produce expected results
- [ ] Agent acts according to instructions
- [ ] Prompts outside conversation starters are handled appropriately
- [ ] Actions requiring confirmation work correctly
- [ ] Knowledge sources are being used correctly
- [ ] Agent handles "I don't know" scenarios gracefully
- [ ] Multi-turn conversations maintain context
- [ ] Cross-app behavior is consistent

---

## 16. Runtime Limits & Optimization

### Hard Limits

| Resource | Limit |
|----------|-------|
| Instructions | 8,000 characters |
| Description (agent) | 1,000 characters |
| description_for_model (plugin) | 2,048 characters |
| Token budget (runtime) | 4,096 tokens |
| Conversation starters | 6 (v1.6) |
| Actions (plugins) | 1–10 |
| WebSearch sites | 4 |
| TeamsMessages URLs | 5 |
| Meetings items | 5 |
| Group mailboxes | 25 |
| Embedded files | 10 (max 1MB each) |
| Functions per plugin | Unlimited (quality degrades >10) |
| Grounding records | 50 items |
| Plugin response items | 25 items |
| Timeout | 45 seconds |
| URL path segments (WebSearch) | 2 max |
| Disclaimer text | 500 characters |

### Optimization Targets

- **Token budget**: Optimize for ~66% utilization (~2,700 tokens of 4,096)
- **Instructions**: Aim for 200–7,200 characters (warn if <200 or >90% of 8,000)
- **Plugin responses**: Keep payloads small; truncate large content
- **Preprocessing**: Use Copilot connectors or plugin preprocessing to reduce data
- **Post-processing**: Leverage Code Interpreter for data analysis after retrieval

### Performance Tips

- Use `progress_style: "ShowUsage"` for better UX during API calls
- Keep function count per plugin ≤10
- Use scoped knowledge sources (specific SharePoint sites, not all)
- Optimize OpenAPI response schemas to return only needed fields

---

## 17. Security & Compliance

### Built-in Protections

- Inherits Microsoft 365 security, compliance, and governance frameworks
- Content filtering and inline disengagement for XPIA (cross-prompt injection attacks)
- RAI (Responsible AI) validation required before publishing
- User permissions enforced — agent can only access content user has access to
- Requires M365 Copilot license for capabilities beyond WebSearch

### isConsequential Actions

Mark write operations in OpenAPI spec:

```yaml
paths:
  /tasks:
    post:
      x-openai-isConsequential: true
      operationId: createTask
```

- `true` = Always requires user confirmation
- `false` = May not require confirmation after first connection
- Omitted = Default behavior based on HTTP method

### Data Handling Attestation (v2.2+)

Declare function behavior via `security_info.data_handling`:

```json
{
  "security_info": {
    "data_handling": ["GetPrivateData", "ResourceStateUpdate"]
  }
}
```

Without `security_info`, the function **cannot interact with other plugins or capabilities**.

### Sensitivity Labels (v1.6)

For embedded files, specify the highest protection label:

```json
{
  "sensitivity_label": { "id": "<purview-label-guid>" }
}
```

---

## 18. Building Tools

| Tool | Best For |
|------|----------|
| **Microsoft 365 Copilot (Agent Builder)** | No-code; quick prototyping in the browser |
| **Microsoft 365 Agents Toolkit** | Pro-code; VS Code/Visual Studio integration |
| **Copilot Studio** | Low-code; Power Platform integration |
| **SharePoint** | Document-grounded agents directly from SharePoint |
| **Kiota** | CLI tool for generating plugin packages from OpenAPI |

### TypeSpec Support

TypeSpec provides strongly-typed agent definitions:

```typescript
@agent("Repairs Agent", "Helps track tickets and repairs")
@instructions("Look at ServiceNow and Jira tickets...")
namespace MyAgent {
  op webSearch is AgentCapabilities.WebSearch<Sites = [
    { url: "https://contoso.com" }
  ]>;

  @conversationStarter(#{ title: "My Repairs", text: "What repairs are assigned to me?" })
}
```

Requires Agents Toolkit v6.0+.

---

## 19. Common Pitfalls & Troubleshooting

### Instruction Failures

| Problem | Cause | Fix |
|---------|-------|-----|
| Overeager tool use | Model calls tools without needed inputs | Add "Only call if inputs are available; otherwise, ask" |
| Repetitive phrasing | Model reuses example phrasing verbatim | Add multiple examples (few-shot); try removing examples |
| Verbose explanations | No output constraints | Add concise examples and format constraints |
| Steps reordered | Ambiguous step structure | Use explicit numbering + "Do not reorder" |
| Blended steps | Fused multi-action instructions | Make tasks atomic (one action per step) |
| Tone drift | No explicit tone specification | Always specify tone, verbosity, and format |

### Common Issues

| Symptom | Root Cause | Solution |
|---------|-----------|----------|
| Agent not appearing | Manifest validation failed | Check all required fields, icon sizes |
| Functions not triggering | description_for_model doesn't describe use cases | Improve plugin/function descriptions |
| Instructions ignored | Too vague or conflicting | Use strict Markdown structure, remove ambiguity |
| Wrong function called | Operation descriptions too similar | Make operationId and descriptions distinct |
| Agent uses wrong knowledge | Too many unscoped sources | Scope to specific SharePoint sites/channels |
| Slow responses | Large plugin responses | Reduce payload size, use progress_style |
| First-time user confusion | No conversation starters | Add 3–6 focused conversation starters |

### Debug Checklist

1. Enable developer mode (`-developer on`)
2. Check which functions were selected in debug card
3. Verify function parameters match expected values
4. Check if grounding sources returned relevant data
5. Review instruction compliance in response
6. Test without plugins to isolate instruction vs. plugin issues

---

## 20. Quick Reference Tables

### Character Limits

| Field | Max Length |
|-------|-----------|
| Agent name | 100 chars |
| Agent description | 1,000 chars |
| Agent instructions | 8,000 chars |
| Plugin name_for_human | 20 chars |
| Plugin description_for_human | 100 chars |
| Plugin description_for_model | 2,048 chars |
| Disclaimer text | 500 chars |
| All string properties (default) | 4,000 chars |

### Array Limits (v1.6)

| Array | Max Items |
|-------|-----------|
| conversation_starters | 6 |
| actions | 10 |
| WebSearch sites | 4 |
| TeamsMessages urls | 5 |
| Meetings items_by_id | 5 |
| Email group_mailboxes | 25 |
| EmbeddedKnowledge files | 10 |
| capabilities (per type) | 1 each |

### Schema Versions

| File | Latest Version | Schema URL |
|------|---------------|------------|
| declarativeAgent.json | v1.6 | `https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.6/schema.json` |
| apiPlugin.json | v2.4 (recommended v2.2+) | `https://aka.ms/json-schemas/copilot/plugin/v2.2/schema.json` |
| manifest.json | v1.24 | `https://developer.microsoft.com/json-schemas/teams/vDevPreview/MicrosoftTeams.schema.json` |

### Capability Name Values

```
WebSearch, OneDriveAndSharePoint, GraphConnectors, GraphicArt,
CodeInterpreter, Dataverse, TeamsMessages, Email, People,
ScenarioModels, Meetings, EmbeddedKnowledge
```

### HTTP Method → isConsequential Default

| Method | Default Behavior |
|--------|-----------------|
| GET | Non-consequential (no confirmation after first) |
| POST, PUT, PATCH, DELETE | Consequential (always confirms) |

### GPT 5.1 Output Profiles

```
Default, Professional, Friendly, Candid, Quirky,
Efficient, Nerdy, Cynical
```

---

## Sources

- [Write effective instructions for declarative agents](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-instructions)
- [Best practices for building declarative agents](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-best-practices)
- [Write Instructions for Declarative Agents with API plugins](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/instructions-api-plugins)
- [Declarative Agents overview](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-declarative-agent)
- [Declarative agent schema v1.6](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-manifest-1.6)
- [Declarative agent schema v1.5](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-manifest-1.5)
- [Declarative agent architecture](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-architecture)
- [API plugins overview](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-api-plugins)
- [API plugin manifest schema v2.2](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api-plugin-manifest-2.2)
- [OpenAPI document guidance](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/openapi-document-guidance)
- [Model changes in GPT 5.1+](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-model-migration-overview)
