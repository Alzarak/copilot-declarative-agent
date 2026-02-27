---
description: Migrate a monolithic description_for_model to the layered instruction architecture
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
argument-hint: "[path_to_apppackage]"
---

# Migrate to Layered Instruction Architecture

Analyze and redistribute instructions from an overloaded `description_for_model` to the correct layers.

## Steps

1. **Locate the appPackage** and read all JSON files.

2. **Analyze current state**:
   - Measure `description_for_model` length (warn if >2,048 chars)
   - Measure `instructions` length in declarativeAgent.json
   - Check which functions have `states` defined
   - Identify content types in `description_for_model`

3. **Classify content** in the current `description_for_model`:

   | Content Type | Target Layer |
   |-------------|-------------|
   | Terminology mappings ("customer" = company_name) | → `states.reasoning.instructions` on relevant functions |
   | Parameter defaults | → `states.reasoning.instructions` on relevant functions |
   | When-to-use guidance per function | → `states.reasoning.instructions` on relevant functions |
   | Result formatting rules | → `states.responding.instructions` on relevant functions |
   | Error handling patterns | → `states.responding.instructions` on relevant functions |
   | Multi-tool workflows | → `instructions` in declarativeAgent.json |
   | Status definitions | → `instructions` in declarativeAgent.json |
   | Role/tone definition | → `instructions` in declarativeAgent.json |

4. **Present migration plan** to user before making changes:
   - Show what moves where
   - Show projected sizes after migration
   - Highlight any content that doesn't clearly fit one layer

5. **Execute migration** (after user approval):
   - Move function-specific content to `states.reasoning.instructions`
   - Move formatting content to `states.responding.instructions`
   - Move orchestration content to `instructions`
   - Trim `description_for_model` to 2-3 sentences (<2,048 chars)

6. **Bump manifest.json version**

7. **Run validation** to verify everything is correct.

8. **Present before/after** comparison:
   - description_for_model: X chars → Y chars
   - instructions: X chars → Y chars
   - Functions with states: X → Y

## Tips
- Read `references/instruction-architecture.md` for the full 5-layer architecture
- The key insight: per-function guidance in `states` only loads when that function is being considered, saving tokens on every other turn
- Keep `description_for_model` to 2-3 sentences about what the plugin does and when to use it
- Use Goal/Action/Transition pattern in declarativeAgent.json instructions
