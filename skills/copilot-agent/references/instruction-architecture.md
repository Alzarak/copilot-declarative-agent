# Instruction Architecture

## Runtime Constraints

| Limit | Value | Notes |
|-------|-------|-------|
| Total token budget | 4,096 tokens | ALL context: instructions + context + tools + prompt + response |
| Plugin response limit | 25 items | Max items from external API responses |
| Grounding record limit | 50 items | Contextual data available |
| Timeout | 45 seconds | Including network latency and processing |
| Plugin API execution | 10 seconds | Optimize for under 9 seconds |

Optimize for ~66% utilization due to external overhead.

## The Five Layers

### Layer 1: Agent Instructions (declarativeAgent.json -> instructions)
- **Purpose**: Agent-wide behavior, loaded every turn
- **Limit**: 8,000 characters
- **What goes here**: Role definition, tone, multi-tool orchestration workflows, status definitions, output formatting rules, few-shot examples
- **Format**: Markdown with headers and lists

**Microsoft-recommended structure** (Goal/Action/Transition pattern):

```markdown
# OBJECTIVE
Guide users through [process] by [method].

# RESPONSE RULES
- Ask one clarifying question at a time, only when needed.
- Present information as concise bullet points or tables.
- Use tools only if data is sufficient; otherwise, ask for missing info.

# WORKFLOW

## Step 1: Gather Basic Details
- **Goal:** Identify the user's issue.
- **Action:** Proceed if clear; ask one focused clarifying question if not.
- **Transition:** Once clear, proceed to Step 2.

## Step 2: Check External Data
- **Goal:** Rule out known issues.
- **Action:** Query `DataSource` for relevant information.
- **Transition:** If match found, present solution. If not, proceed to Step 3.

## Step 3: Search Knowledge Base
- **Goal:** Find best-fit solutions.
- **Action:** Search knowledge sources, use iterative narrowing.
- **Transition:** Present top matches. If unresolved, proceed to Step 4.

## Step 4: Escalate or Create Record
- **Goal:** Log unresolved issues.
- **Action:** Gather required fields, confirm with user, create record.

# OUTPUT FORMATTING RULES
- Use bullets for actions, tables for structured data.
- Always confirm before ending or submitting.

# EXAMPLES

## Valid Example
User: "I can't access my email"
Agent: "I'll check for any ongoing email outages. One moment..."
[Queries service status]
Agent: "There's a known outage affecting Exchange Online. It's expected to be resolved by 3 PM EST."

## Invalid Example
- "Here are 15 articles that might help..." (overwhelms user)
- "I'm raising a ticket now." (without confirming details first)
```

**Explicit capability references** (Microsoft recommends calling out capability names):
- Actions: "Use `Jira` to fetch tickets"
- Connectors: "Use `ServiceNow KB` for help articles"
- SharePoint: "Reference SharePoint internal documents"
- Email: "Check user emails for relevant information"
- Teams: "Search Teams chat history for context"
- Code Interpreter: "Use code interpreter to generate charts"
- People: "Use people knowledge to fetch user contact details"

**Writing patterns**:
- Use positive instructions ("do X") rather than negative ("don't do Y")
- Use precise verbs: "query", "fetch", "present", "confirm"
- Include 2+ few-shot examples for complex behaviors
- Break workflows into numbered steps with Goal/Action/Transition

### Layer 2: Plugin Description (apiPlugin.json -> description_for_model)
- **Purpose**: Plugin selection -- helps orchestrator decide when to use this plugin
- **Limit**: **2,048 characters** (CRITICAL -- content beyond this MAY be silently ignored)
- **What goes here**: 2-3 sentences describing when to use this plugin
- **What does NOT go here**: Parameter mapping, terminology glossaries, orchestration logic, defaults, formatting rules

**Good example** (under 200 chars):
```
Use this plugin when the user wants to search, create, or manage support tickets. Supports filtering by status, priority, assignee, and date range.
```

**Bad example** (overloaded, 3000+ chars of parameter guidance that should be in reasoning states).

### Layer 3: Function Description (apiPlugin.json -> functions[].description)
- **Purpose**: Function selection -- helps orchestrator pick the right function
- **Limit**: ~4,000 characters
- **What goes here**: 1-2 sentences describing what this specific function does
- Keep concise and semantically clear

### Layer 4: Reasoning Instructions (functions[].states.reasoning.instructions)
- **Purpose**: Per-function call guidance, loaded only when orchestrator is considering this function
- **Format**: Array of strings
- **What goes here**: Parameter mapping, when to call, defaults, terminology, chaining rules

```json
{
  "states": {
    "reasoning": {
      "description": "Searches for support tickets matching criteria.",
      "instructions": [
        "Use this function when the user asks to find, list, or search tickets.",
        "Map 'high priority' to priority=1, 'medium' to priority=2, 'low' to priority=4.",
        "Map 'my tickets' or 'assigned to me' to assigned_to='me'.",
        "Default max_results to 10 unless user specifies otherwise.",
        "If user asks about a specific ticket by number, use the ticket ID directly."
      ]
    }
  }
}
```

**Why this matters**: Putting function-specific guidance here instead of in `description_for_model` saves tokens and keeps it scoped to when it is needed.

### Layer 5: Responding Instructions (functions[].states.responding.instructions)
- **Purpose**: Result presentation guidance
- **Format**: Array of strings
- **What goes here**: Error handling, formatting, data extraction, link generation

```json
{
  "states": {
    "responding": {
      "instructions": [
        "Present results as a numbered list with ticket number, title, status, and priority.",
        "If no results found, suggest broadening the search or trying different keywords.",
        "For error responses, explain the issue and suggest what the user can try.",
        "Always include the total count of matching results.",
        "If results exceed max_results, mention that more results are available."
      ]
    }
  }
}
```

## Multi-Tool Orchestration Patterns

Declarative agents support sequential processing only -- no loops or conditional branches.

### Pattern 1: Output-as-Input
Result of one function call feeds into another:
- Search for a ticket -> Get ticket details -> Search related notes
- Reference in instructions: "After finding the ticket, use `getTicketNotes` to retrieve discussion history."

### Pattern 2: Conversation-History
Use prior responses for follow-up calls:
- "Show my tickets" -> "Now filter those by high priority"
- Previous results inform the next query parameters.

### Pattern 3: Knowledge + Action
Combine grounding knowledge with API actions:
- SharePoint knowledge provides context -> API function takes action
- "Reference the escalation policy in SharePoint, then create a ticket using the API."

### Pattern 4: Action + Capability
Combine API calls with built-in capabilities:
- API returns data -> Code Interpreter analyzes it
- "Fetch sales data, then use code interpreter to create a trend chart."

**Important**: Processing is sequential, not looped. You cannot create iterative reasoning loops or complex decision trees.

## Instruction Patterns

### Pattern 1: Deterministic Workflows

Convert ambiguous multi-task requests into explicit, sequential steps:

```markdown
## Task: Metrics and ROI (Deterministic)

### Definitions (Do not invent)
- Metrics to compute: [Metric1], [Metric2], [Metric3]
- ROI definition: ROI = (Benefit - Cost) / Cost
- Source of truth: Use ONLY the provided document(s)

### Steps (Sequential -- do not reorder)
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
Section A -- Extract Data (Non-Sequential)
- Extract pricing changes.
- Extract margin changes.
- Extract sentiment themes.

Section B -- Build the Summary (Sequential)
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
Detail level: [short | medium | detailed] -- do not exceed [X] bullets per section
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

### Pattern 6: Self-Evaluation Step

Add a final self-check to instructions:

```markdown
Before finalizing, confirm that all items from Section A appear in the summary.
```

## Multi-Turn Conversation Design

When functions require multiple parameters, collect them before calling:

```markdown
If user asks about the weather:
- Ask the user for location.
- Ask the user for forecast day.
- Ask the user for unit system.
- Only call **getWeather** when you collect all the values.
```

Design guidelines:
- Ask one clarifying question at a time
- Confirm all details before executing write operations
- Use conversation history for follow-up queries (don't re-ask known values)
- Provide defaults where possible to reduce friction

## Common Prompt Failures and Fixes

| Problem | Fix |
|---------|-----|
| Over-eager tool use | "Only call the tool if necessary inputs are available; otherwise, ask the user" |
| Repetitive phrasing | Use 2+ few-shot examples instead of 1 |
| Verbose explanations | Add constraints and concise example responses |
| Wrong function selected | Improve function `description` semantic clarity |
| Parameters mapped incorrectly | Add explicit mapping in `reasoning.instructions` |
| Results poorly formatted | Add formatting rules in `responding.instructions` |

## Migration Guide: Monolithic to Layered

If you have a bloated `description_for_model` (over 2,048 chars), migrate to layered approach:

1. **Identify content types**: Separate parameter guidance, orchestration logic, formatting rules, and plugin description
2. **Keep in description_for_model**: Only 2-3 sentences about WHEN to use this plugin
3. **Move to instructions**: Orchestration workflows, multi-tool chaining, status definitions
4. **Move to reasoning.instructions**: Per-function parameter mapping, terminology, defaults
5. **Move to responding.instructions**: Output formatting, error handling, link generation
6. **Verify**: Check total character counts are within limits, test behavior

## Instruction Focus Areas (Microsoft Framework)

| Focus Area | Purpose |
|------------|---------|
| Instruction strategy | Define role/goals, plan for edge cases, set boundaries |
| Contextual intelligence | Adjust for deployment context (Word vs Teams vs Outlook) |
| Collaborative iteration | Cross-functional review with PMs, writers, engineers |
| Instruction diagnostics | Use logs and feedback to find non-helpful patterns |
| Instruction architecture | Break into reusable parts, use tags and templates |
