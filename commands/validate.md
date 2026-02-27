---
description: Validate a Microsoft 365 Copilot Declarative Agent appPackage for correctness
allowed-tools: ["Read", "Bash", "Glob", "Grep"]
argument-hint: "[path_to_apppackage]"
---

# Validate Copilot Declarative Agent appPackage

Run comprehensive validation on an appPackage directory.

## Steps

1. **Locate the appPackage**:
   - Use the argument path if provided
   - Otherwise look for `appPackage/` in the current directory
   - Search for `**/appPackage/` if not found
   - If still not found, ask the user for the path

2. **Run the validation script**:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_apppackage.py [path]
   ```

3. **Review the output** and present findings organized by severity:
   - **Errors**: Must be fixed (missing files, invalid JSON, broken cross-references, sync issues)
   - **Warnings**: Should be reviewed (outdated schema versions, approaching limits)
   - **Passed**: Confirmation of correct configuration

4. **For any errors found**, read the relevant reference file and provide specific fix instructions:
   - Schema issues → `references/file-schemas.md`
   - Instruction issues → `references/instruction-architecture.md`
   - Capability issues → `references/capabilities.md`
   - Cross-reference issues → `references/validation.md`

5. **Check instruction quality** (beyond what the script validates):
   - Is `description_for_model` under 2,048 chars?
   - Are function-specific details in `states.reasoning` instead of `description_for_model`?
   - Do instructions use Markdown formatting with headers and lists?
   - Are there 2+ few-shot examples for complex behaviors?

6. **Offer to fix** any issues found automatically.

## Tips
- Read `references/validation.md` for the full validation checklist
- The script checks structure, cross-references, function sync, and schema versions
- Manual review of instruction quality is also important
- Use developer mode (`-developer on` in Copilot) to test behavior after fixes
