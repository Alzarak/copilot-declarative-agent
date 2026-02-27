# GPT 5.1+ Model Migration

How to adapt declarative agent instructions for the GPT 5.1+ model changes in Microsoft 365 Copilot.

## What Changed

| GPT 5.0 | GPT 5.1+ |
|----------|----------|
| **Literal-first**: follows instructions step-by-step | **Intent-first**: interprets what instructions *intended* |
| Honors numbering and structure exactly | May reorganize plans to fix/optimize them |
| Won't fill in missing information | Fills gaps and infers missing steps |
| Consistent professional tone | Dynamically selects tone and verbosity |
| Fixed reasoning depth | Adaptive reasoning per request/sub-task |

## 8 Output Profiles

GPT 5.1 can dynamically select from these profiles. You can explicitly prompt for one or let the model infer:

```
Default, Professional, Friendly, Candid, Quirky, Efficient, Nerdy, Cynical
```

**Best practice**: Always specify tone and verbosity explicitly in instructions to prevent drift:
```markdown
- Tone: professional and concise
- Output: three bullet points per section
- Return only the requested format; no explanations
```

## Common Symptoms After Migration

| Symptom | Cause |
|---------|-------|
| Steps become reordered | Model "optimizes" step order based on inferred intent |
| Parallel tasks become sequential | Model serializes for safety |
| Steps get blended ("extract and summarize") | Model fuses multi-action instructions |
| Tone drifts toward "educational" or "chatty" | Adaptive tone selection without explicit constraints |
| Model creates or removes steps | Gap-filling based on inferred context |
| Verbose explanations added | No output constraints specified |

## Migration Strategy

| Scenario | Approach |
|----------|----------|
| Fixed workflow/format required | Use strict step-by-step instructions + literal-execution header |
| Goals clear, tools well-defined | Use goal-focused prompts with guardrails, let model plan |
| Existing agent drifting | Add stabilizing header as interim fix, then restructure |

## When to Use Strict Instructions

- Fixed business processes (approval workflows, compliance steps)
- Specific formatting rules (reports, templates)
- Required reasoning/retrieval sequences (search before create)
- Compliance or audit requirements
- Multi-tool orchestration with specific order

## When to Embrace Adaptive Reasoning

- Tools and knowledge sources are well-defined
- Output format is flexible
- Goal is more important than exact path
- Simple, routine tasks (lookups, searches)

## Pattern: Literal-Execution Header

Add this block at the top of `instructions` to stabilize behavior for strict workflows:

```markdown
Always interpret instructions literally.
Never infer intent or fill in missing steps.
Never add context, recommendations, or assumptions.
Follow step order exactly with no optimization.
Respond concisely and only in the requested format.
Do not call tools unless a step explicitly instructs you to do so.
```

**Use this when**: Business processes must execute in exact order with no creative interpretation.

**Avoid this when**: You want the model to flexibly handle varied user requests.

## Pattern: Instruction Audit Prompt

Use this template to review and stabilize existing instructions:

```markdown
You are reviewing agent instructions for 5.1 stability.

INPUT
<instructions>[PASTE CURRENT INSTRUCTIONS]</instructions>

CHECKS
- Step order: identify ambiguity, missing/merged steps -> propose atomic steps
- Tool use: identify auto-calls, retries -> add "use only in step X; no auto-retry"
- Grounding: detect inference, blending -> add "cite only retrieved; no inference"
- Missing-data handling: -> add "stop and ask the user"
- Verbosity: -> replace with "return only the requested format"
- Contradictions: resolve; prefer explicit over implied
- Vague verbs ("verify", "process", "handle"): replace with precise actions
- Safety: prohibit step reordering, optimization, or reinterpretation

OUTPUT
- Header patch (3-6 lines)
- Top 5 changes (bullet: "Issue -> Fix")
- Example rewrite (<=10 lines) for the riskiest step
```

## Combining Strict and Adaptive

For agents with both strict workflows and flexible queries, use a hybrid approach:

```markdown
# OBJECTIVE
Help users manage support tickets.

# STRICT WORKFLOW (Follow exactly, do not reorder)
## Creating Tickets
Step 1: Collect title and description. Do NOT proceed without both.
Step 2: Ask for priority (1=Critical, 2=High, 3=Medium, 4=Low).
Step 3: Confirm all details with the user before calling `createTicket`.
Step 4: Present the created ticket ID and link.

# FLEXIBLE QUERIES (Adapt as needed)
For searches, lookups, and status checks, use the best approach
based on the user's question. Prioritize relevant results.

# OUTPUT RULES (Always apply)
- Tone: professional and concise
- Use bullets for lists, tables for structured data
- Never add unsolicited recommendations
```

## Testing After Migration

1. Test all conversation starters -- verify responses match expected behavior
2. Check multi-step workflows execute in correct order
3. Verify tone consistency across different query types
4. Test edge cases (ambiguous queries, missing data)
5. Use developer mode (`-developer on`) to inspect orchestrator decisions
6. Compare against pre-migration behavior if possible
