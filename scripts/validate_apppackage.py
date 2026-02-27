#!/usr/bin/env python3
"""
Validate Microsoft 365 Copilot Declarative Agent appPackage structure.

Checks file existence, JSON validity, schema versions, field limits,
cross-references, function sync, and v1.6 property compliance.

Usage:
    python validate_apppackage.py [path_to_apppackage]

If no path is provided, looks for 'appPackage' in current directory.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Known current schema versions
CURRENT_MANIFEST_VERSION = "1.24"
CURRENT_DA_VERSION = "v1.6"
CURRENT_PLUGIN_VERSION = "v2.4"
CURRENT_OPENAPI_VERSION = "3.0"

# All valid capability names in v1.6
VALID_CAPABILITIES = {
    "WebSearch", "OneDriveAndSharePoint", "GraphConnectors",
    "GraphicArt", "CodeInterpreter", "Dataverse", "TeamsMessages",
    "Email", "People", "ScenarioModels", "Meetings", "EmbeddedKnowledge",
}

# Capability-specific array limits
CAPABILITY_LIMITS = {
    "WebSearch": {"sites": 4},
    "TeamsMessages": {"urls": 5},
    "Email": {"group_mailboxes": 25},
    "Meetings": {"items_by_id": 5},
    "EmbeddedKnowledge": {"files": 10},
}

# Valid security_info.data_handling values
VALID_DATA_HANDLING_VALUES = {
    "GetPublicData", "GetPrivateData", "DataTransform",
    "DataExport", "ResourceStateUpdate",
}


class AppPackageValidator:
    def __init__(self, package_path: str):
        self.package_path = Path(package_path)
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passed: list[str] = []
        self._json_cache: dict[str, Any] = {}

    def validate(self) -> bool:
        """Run all validations and return True if package is valid."""
        print(f"\nValidating appPackage: {self.package_path}\n")
        print("=" * 60)

        self._check_required_files()
        self._validate_manifest()
        self._validate_declarative_agent()
        self._validate_api_plugin()
        self._validate_security_info()
        self._validate_api_definition()
        self._validate_icons()
        self._check_cross_references()
        self._check_function_sync()

        self._print_results()

        return len(self.errors) == 0

    def _check_required_files(self):
        """Check that required files exist."""
        required = ["manifest.json", "declarativeAgent.json", "color.png", "outline.png"]

        for file in required:
            path = self.package_path / file
            if path.exists():
                self.passed.append(f"File exists: {file}")
            else:
                self.errors.append(f"Missing required file: {file}")

    def _validate_manifest(self):
        """Validate manifest.json structure."""
        path = self.package_path / "manifest.json"
        if not path.exists():
            return

        data = self._load_json(path)
        if not data:
            return

        # Check required fields
        required_fields = ["manifestVersion", "id", "version", "developer", "name", "description", "icons"]
        for field in required_fields:
            if field in data:
                self.passed.append(f"manifest.json has '{field}'")
            else:
                self.errors.append(f"manifest.json missing required field: '{field}'")

        # Check schema version currency
        if "manifestVersion" in data:
            if data["manifestVersion"] == CURRENT_MANIFEST_VERSION:
                self.passed.append(f"manifest.json manifestVersion is current ({CURRENT_MANIFEST_VERSION})")
            else:
                self.warnings.append(
                    f"manifest.json manifestVersion '{data['manifestVersion']}' differs from "
                    f"known current version '{CURRENT_MANIFEST_VERSION}'"
                )

        # Validate UUID format
        if "id" in data:
            uuid_pattern = re.compile(
                r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I
            )
            if uuid_pattern.match(data["id"]):
                self.passed.append("manifest.json 'id' is valid UUID")
            else:
                self.errors.append(f"manifest.json 'id' is not valid UUID: {data['id']}")

        # Check developer fields
        if "developer" in data:
            dev = data["developer"]
            for field in ["name", "websiteUrl", "privacyUrl", "termsOfUseUrl"]:
                if field in dev:
                    self.passed.append(f"manifest.json developer has '{field}'")
                else:
                    self.errors.append(f"manifest.json developer missing: '{field}'")

        # Check name/description lengths
        if "name" in data and "short" in data["name"]:
            name_len = len(data["name"]["short"])
            if name_len <= 30:
                self.passed.append(f"manifest.json name.short <= 30 chars ({name_len})")
            else:
                self.errors.append(f"manifest.json name.short too long ({name_len} chars, max 30)")

        if "description" in data and "short" in data["description"]:
            desc_len = len(data["description"]["short"])
            if desc_len <= 80:
                self.passed.append(f"manifest.json description.short <= 80 chars ({desc_len})")
            else:
                self.warnings.append(f"manifest.json description.short is {desc_len} chars (max 80)")

        # Check copilotAgents
        if "copilotAgents" in data and "declarativeAgents" in data["copilotAgents"]:
            agents = data["copilotAgents"]["declarativeAgents"]
            if len(agents) > 0:
                self.passed.append(f"manifest.json has {len(agents)} declarativeAgent(s)")
                for i, agent in enumerate(agents):
                    if "id" in agent and "file" in agent:
                        self.passed.append(f"manifest.json declarativeAgent[{i}] has id and file")
                    else:
                        self.errors.append(f"manifest.json declarativeAgent[{i}] missing id or file")
            else:
                self.errors.append("manifest.json copilotAgents.declarativeAgents is empty")
        else:
            self.errors.append("manifest.json missing copilotAgents.declarativeAgents")

    def _validate_declarative_agent(self):
        """Validate declarativeAgent.json structure including v1.6 properties."""
        path = self.package_path / "declarativeAgent.json"
        if not path.exists():
            return

        data = self._load_json(path)
        if not data:
            return

        # Check required fields
        required = ["name", "description", "instructions"]
        for field in required:
            if field in data:
                self.passed.append(f"declarativeAgent.json has '{field}'")
            else:
                self.errors.append(f"declarativeAgent.json missing required field: '{field}'")

        # Check schema version currency
        if "version" in data:
            if data["version"] == CURRENT_DA_VERSION:
                self.passed.append(f"declarativeAgent.json version is current ({CURRENT_DA_VERSION})")
            else:
                self.warnings.append(
                    f"declarativeAgent.json version '{data['version']}' differs from "
                    f"known current version '{CURRENT_DA_VERSION}'"
                )

        # Validate field lengths
        if "name" in data:
            name_len = len(data["name"])
            if name_len <= 100:
                self.passed.append(f"declarativeAgent.json 'name' <= 100 chars ({name_len})")
            else:
                self.errors.append(f"declarativeAgent.json 'name' too long ({name_len} chars, max 100)")

        if "description" in data:
            desc_len = len(data["description"])
            if desc_len <= 1000:
                self.passed.append(f"declarativeAgent.json 'description' <= 1000 chars ({desc_len})")
            else:
                self.errors.append(
                    f"declarativeAgent.json 'description' too long ({desc_len} chars, max 1000)"
                )

        if "instructions" in data:
            instr = data["instructions"]
            instr_len = len(instr)
            if instr_len <= 8000:
                self.passed.append(
                    f"declarativeAgent.json 'instructions' <= 8000 chars ({instr_len} used)"
                )
            else:
                self.errors.append(
                    f"declarativeAgent.json 'instructions' too long ({instr_len} chars, max 8000)"
                )

            # Instruction quality checks
            self._check_instruction_quality(instr)

        # Validate capabilities
        if "capabilities" in data:
            for i, cap in enumerate(data["capabilities"]):
                if "name" not in cap:
                    self.errors.append(f"declarativeAgent.json capabilities[{i}] missing 'name'")
                    continue
                cap_name = cap["name"]
                if cap_name in VALID_CAPABILITIES:
                    self.passed.append(f"declarativeAgent.json has valid capability: {cap_name}")
                else:
                    self.warnings.append(
                        f"declarativeAgent.json has unknown capability: {cap_name}"
                    )

                # Check capability-specific limits
                if cap_name in CAPABILITY_LIMITS:
                    for field, limit in CAPABILITY_LIMITS[cap_name].items():
                        if field in cap and len(cap[field]) > limit:
                            self.errors.append(
                                f"declarativeAgent.json {cap_name}.{field} has "
                                f"{len(cap[field])} items (max {limit})"
                            )

                # WebSearch URL validation
                if cap_name == "WebSearch" and "sites" in cap:
                    for j, site in enumerate(cap["sites"]):
                        url = site.get("url", "")
                        if "?" in url:
                            self.errors.append(
                                f"WebSearch sites[{j}] URL contains query parameters (not allowed)"
                            )
                        path_segments = [s for s in url.split("//", 1)[-1].split("/")[1:] if s]
                        if len(path_segments) > 2:
                            self.errors.append(
                                f"WebSearch sites[{j}] URL has {len(path_segments)} path segments "
                                f"(max 2)"
                            )

        # Validate conversation_starters (v1.6 limit: 6)
        if "conversation_starters" in data:
            starters = data["conversation_starters"]
            if len(starters) > 6:
                self.errors.append(
                    f"declarativeAgent.json conversation_starters has {len(starters)} items "
                    f"(max 6 in v1.6)"
                )
            else:
                self.passed.append(
                    f"declarativeAgent.json conversation_starters count OK ({len(starters)}/6)"
                )
            for i, starter in enumerate(starters):
                if "text" in starter:
                    self.passed.append(f"declarativeAgent.json conversation_starter[{i}] has 'text'")
                else:
                    self.errors.append(
                        f"declarativeAgent.json conversation_starter[{i}] missing 'text'"
                    )

        # Validate actions (v1.6 limit: 1-10)
        if "actions" in data:
            actions = data["actions"]
            if len(actions) > 10:
                self.errors.append(
                    f"declarativeAgent.json actions has {len(actions)} items (max 10)"
                )
            for i, action in enumerate(actions):
                if "id" in action and "file" in action:
                    self.passed.append(f"declarativeAgent.json action[{i}] has id and file")
                else:
                    self.errors.append(f"declarativeAgent.json action[{i}] missing id or file")

        # Validate behavior_overrides (v1.6)
        if "behavior_overrides" in data:
            bo = data["behavior_overrides"]
            if "suggestions" in bo:
                if "disabled" not in bo["suggestions"]:
                    self.errors.append(
                        "behavior_overrides.suggestions missing required 'disabled' field"
                    )
                else:
                    self.passed.append("behavior_overrides.suggestions is valid")
            if "special_instructions" in bo:
                if "discourage_model_knowledge" not in bo["special_instructions"]:
                    self.errors.append(
                        "behavior_overrides.special_instructions missing "
                        "'discourage_model_knowledge' field"
                    )
                else:
                    self.passed.append("behavior_overrides.special_instructions is valid")

        # Validate disclaimer (v1.6)
        if "disclaimer" in data:
            disclaimer = data["disclaimer"]
            if "text" in disclaimer:
                text_len = len(disclaimer["text"])
                if text_len <= 500:
                    self.passed.append(f"disclaimer.text <= 500 chars ({text_len})")
                else:
                    self.errors.append(f"disclaimer.text too long ({text_len} chars, max 500)")
                if not disclaimer["text"].strip():
                    self.errors.append("disclaimer.text must contain at least one non-whitespace char")
            else:
                self.errors.append("disclaimer missing required 'text' field")

        # Validate worker_agents (v1.6 preview)
        if "worker_agents" in data:
            for i, wa in enumerate(data["worker_agents"]):
                if "id" in wa:
                    self.passed.append(f"worker_agents[{i}] has 'id'")
                else:
                    self.errors.append(f"worker_agents[{i}] missing required 'id'")

        # Validate user_overrides (v1.6)
        if "user_overrides" in data:
            for i, uo in enumerate(data["user_overrides"]):
                if "path" not in uo:
                    self.errors.append(f"user_overrides[{i}] missing required 'path'")
                if "allowed_actions" not in uo:
                    self.errors.append(f"user_overrides[{i}] missing required 'allowed_actions'")
                elif uo["allowed_actions"] != ["remove"]:
                    self.warnings.append(
                        f"user_overrides[{i}] allowed_actions only supports ['remove']"
                    )
                if "path" in uo and "allowed_actions" in uo:
                    self.passed.append(f"user_overrides[{i}] is valid")

    def _check_instruction_quality(self, instructions: str):
        """Check instruction formatting against Microsoft best practices.

        Microsoft's recommended structure:
          # OBJECTIVE          — role and goals
          # RESPONSE RULES     — behavioral constraints
          # WORKFLOW            — step-by-step with Goal/Action/Transition
          # OUTPUT FORMATTING   — how to present results
          # EXAMPLES            — valid and invalid few-shot examples

        Reference: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/
        declarative-agent-instructions
        """
        instr_len = len(instructions)
        utilization = instr_len / 8000 * 100

        # ── Section 1: Structural formatting ──────────────────────────

        # Check for Markdown headers (# or ##)
        headers = re.findall(r'^(#{1,3})\s+(.+)', instructions, re.MULTILINE)
        if headers:
            self.passed.append(
                f"instructions use Markdown headers ({len(headers)} found)"
            )
        else:
            self.warnings.append(
                "instructions lack Markdown headers. Microsoft recommends structuring "
                "instructions with top-level sections: # OBJECTIVE, # RESPONSE RULES, "
                "# WORKFLOW, # OUTPUT FORMATTING RULES, # EXAMPLES"
            )

        # Check for Markdown lists (bullets or numbered)
        has_lists = bool(re.search(
            r'^\s*[-*]\s+\S|^\s*\d+\.\s+\S', instructions, re.MULTILINE
        ))
        if has_lists:
            self.passed.append("instructions use Markdown lists")
        else:
            self.warnings.append(
                "instructions lack Markdown lists. Use bullet points or numbered "
                "lists for rules, workflows, and examples"
            )

        # ── Section 2: Recommended sections ───────────────────────────

        # OBJECTIVE / ROLE section
        has_objective = bool(re.search(
            r'^#{1,2}\s*(objective|role|purpose|overview)\b',
            instructions, re.IGNORECASE | re.MULTILINE
        ))
        if has_objective:
            self.passed.append(
                "instructions have an OBJECTIVE/ROLE section (defines agent purpose)"
            )
        else:
            self.warnings.append(
                "instructions missing # OBJECTIVE or # ROLE section. Start with a "
                "clear statement of the agent's purpose and goals"
            )

        # RESPONSE RULES section
        has_rules = bool(re.search(
            r'^#{1,2}\s*(response\s+rules?|rules?|constraints?|guidelines?)\b',
            instructions, re.IGNORECASE | re.MULTILINE
        ))
        if has_rules:
            self.passed.append(
                "instructions have a RESPONSE RULES section (behavioral constraints)"
            )
        else:
            self.warnings.append(
                "instructions missing # RESPONSE RULES section. Add behavioral "
                "constraints like: ask one question at a time, use bullets, confirm "
                "before submitting"
            )

        # WORKFLOW section with Goal/Action/Transition pattern
        has_workflow_header = bool(re.search(
            r'^#{1,2}\s*(workflow|steps?|process)\b',
            instructions, re.IGNORECASE | re.MULTILINE
        ))
        has_goal = bool(re.search(
            r'\*\*goal\b', instructions, re.IGNORECASE
        ))
        has_action = bool(re.search(
            r'\*\*action\b', instructions, re.IGNORECASE
        ))
        has_transition = bool(re.search(
            r'\*\*transition\b', instructions, re.IGNORECASE
        ))
        has_steps = bool(re.search(
            r'##\s*step\s+\d', instructions, re.IGNORECASE
        ))

        if has_workflow_header:
            self.passed.append(
                "instructions have a WORKFLOW section"
            )
        else:
            self.warnings.append(
                "instructions missing # WORKFLOW section. Define multi-step "
                "processes with ## Step N subsections"
            )

        gat_count = sum([has_goal, has_action, has_transition])
        if gat_count == 3:
            self.passed.append(
                "instructions use the full Goal/Action/Transition pattern "
                "(Microsoft best practice for workflow steps)"
            )
        elif gat_count > 0:
            missing = []
            if not has_goal:
                missing.append("**Goal:**")
            if not has_action:
                missing.append("**Action:**")
            if not has_transition:
                missing.append("**Transition:**")
            self.warnings.append(
                f"instructions partially use Goal/Action/Transition pattern "
                f"(missing: {', '.join(missing)}). Each workflow step should have all "
                f"three to clearly define what to achieve, what to do, and when to "
                f"move to the next step"
            )
        elif has_steps:
            self.warnings.append(
                "instructions have numbered steps but don't use the "
                "Goal/Action/Transition pattern. Microsoft recommends each step include: "
                "**Goal:** (what to achieve), **Action:** (what to do), "
                "**Transition:** (when to move to the next step)"
            )

        # OUTPUT FORMATTING section
        has_formatting = bool(re.search(
            r'^#{1,2}\s*(output\s+format|formatting\s+rules?|response\s+format)',
            instructions, re.IGNORECASE | re.MULTILINE
        ))
        if has_formatting:
            self.passed.append(
                "instructions have an OUTPUT FORMATTING section"
            )
        else:
            self.warnings.append(
                "instructions missing # OUTPUT FORMATTING RULES section. Add guidance "
                "like: use bullets for actions, tables for structured data, keep "
                "responses skimmable, always confirm before submitting"
            )

        # ── Section 3: Few-shot examples ──────────────────────────────

        # Check for EXAMPLES section header
        has_examples_header = bool(re.search(
            r'^#{1,2}\s*examples?\b', instructions, re.IGNORECASE | re.MULTILINE
        ))

        # Check for valid/invalid example subsections
        has_valid_example = bool(re.search(
            r'(valid\s+example|correct\s+example|good\s+example)',
            instructions, re.IGNORECASE
        ))
        has_invalid_example = bool(re.search(
            r'(invalid\s+example|incorrect\s+example|bad\s+example)',
            instructions, re.IGNORECASE
        ))

        # Check for multi-turn dialogue patterns (User/Assistant/Agent)
        dialogue_turns = re.findall(
            r'(\*\*user\b|\*\*assistant\b|\*\*agent\b|'
            r'user:\s*["\']|assistant:\s*["\']|agent:\s*["\'])',
            instructions, re.IGNORECASE
        )
        has_dialogue = len(dialogue_turns) >= 2

        if has_examples_header:
            self.passed.append("instructions have an # EXAMPLES section")

            if has_valid_example and has_invalid_example:
                self.passed.append(
                    "instructions include both Valid and Invalid examples "
                    "(Microsoft best practice — shows desired AND undesired behavior)"
                )
            elif has_valid_example:
                self.warnings.append(
                    "instructions have Valid examples but no Invalid examples. "
                    "Microsoft recommends including ## Invalid Example showing common "
                    "mistakes like: overwhelming the user with too many results, "
                    "taking action without confirmation, or being overly verbose"
                )
            elif has_invalid_example:
                self.warnings.append(
                    "instructions have Invalid examples but no Valid examples. "
                    "Add ## Valid Example showing a multi-turn dialogue with correct "
                    "agent behavior"
                )
            else:
                self.warnings.append(
                    "instructions have an EXAMPLES section but no Valid/Invalid "
                    "subsections. Microsoft recommends: ## Valid Example (multi-turn "
                    "dialogue) and ## Invalid Example (common mistakes to avoid)"
                )

            if has_dialogue:
                self.passed.append(
                    f"examples include multi-turn dialogue ({len(dialogue_turns)} turns) "
                    f"— shows realistic agent interaction flow"
                )
            else:
                self.warnings.append(
                    "examples lack multi-turn dialogue. Microsoft recommends showing "
                    "realistic User/Assistant exchanges that demonstrate the full "
                    "workflow: User: \"problem\" → Agent: clarifying question → "
                    "User: answer → Agent: resolution"
                )
        else:
            self.warnings.append(
                "instructions missing # EXAMPLES section. Microsoft strongly recommends "
                "including few-shot examples with:\n"
                "  - ## Valid Example: Multi-turn dialogue showing correct behavior\n"
                "  - ## Invalid Example: Common mistakes to avoid\n"
                "This reduces repetitive phrasing and verbose explanations. See: "
                "https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/"
                "declarative-agent-instructions"
            )

        # ── Section 4: Instruction style ──────────────────────────────

        # Check for explicit capability/tool references
        has_capability_refs = bool(re.search(
            r'(use\s+`[^`]+`|query\s+`[^`]+`|search\s+`[^`]+`|'
            r'use\s+the\s+\w+\s+capability)',
            instructions, re.IGNORECASE
        ))
        if has_capability_refs:
            self.passed.append(
                "instructions reference capabilities/tools explicitly "
                "(e.g., 'Query `ServiceNow` for...')"
            )
        else:
            self.warnings.append(
                "instructions don't reference capabilities/tools by name. "
                "Microsoft recommends explicit references like: "
                "'Query `ServiceNow` for outages', 'Search `SharePoint` for policies', "
                "'Use code interpreter to generate charts'"
            )

        # Check positive vs negative instruction style
        negative_patterns = re.findall(
            r"(?:^|\.\s+)(?:do\s+not|don't|never|avoid|must\s+not|should\s+not)\s+",
            instructions, re.IGNORECASE | re.MULTILINE
        )
        positive_patterns = re.findall(
            r'(?:^|\.\s+)(?:always|use|present|confirm|ask|query|search|fetch)\s+',
            instructions, re.IGNORECASE | re.MULTILINE
        )
        if len(negative_patterns) > len(positive_patterns) and len(negative_patterns) > 3:
            self.warnings.append(
                f"instructions lean heavily on negative phrasing "
                f"({len(negative_patterns)} negative vs {len(positive_patterns)} positive). "
                f"Microsoft recommends focusing on what the agent SHOULD do. "
                f"Example: instead of 'Don't list all results', use "
                f"'Use iterative narrowing to find the best match'"
            )

        # Check for confirmation patterns (important for consequential actions)
        has_confirmation = bool(re.search(
            r'(confirm|verify|ask\s+.*before|check\s+with)',
            instructions, re.IGNORECASE
        ))
        if has_confirmation:
            self.passed.append(
                "instructions include confirmation/verification patterns "
                "(important for consequential actions)"
            )

        # ── Section 5: Budget utilization ─────────────────────────────

        if instr_len < 200:
            self.warnings.append(
                f"instructions are very short ({instr_len} chars, {utilization:.0f}% "
                f"of 8000 budget). Add: # OBJECTIVE, # RESPONSE RULES, # WORKFLOW "
                f"(with Goal/Action/Transition), # OUTPUT FORMATTING RULES, # EXAMPLES"
            )
        elif utilization > 90:
            self.warnings.append(
                f"instructions are near capacity ({instr_len} chars, {utilization:.0f}% "
                f"of 8000). Consider moving function-specific guidance to "
                f"states.reasoning.instructions to free up space"
            )

    def _validate_api_plugin(self):
        """Validate apiPlugin.json structure."""
        path = self.package_path / "apiPlugin.json"
        if not path.exists():
            return

        data = self._load_json(path)
        if not data:
            return

        # Check required fields
        required = ["schema_version", "name_for_human", "functions"]
        for field in required:
            if field in data:
                self.passed.append(f"apiPlugin.json has '{field}'")
            else:
                self.errors.append(f"apiPlugin.json missing required field: '{field}'")

        # Check schema version currency
        if "schema_version" in data:
            if data["schema_version"] == CURRENT_PLUGIN_VERSION:
                self.passed.append(
                    f"apiPlugin.json schema_version is current ({CURRENT_PLUGIN_VERSION})"
                )
            else:
                self.warnings.append(
                    f"apiPlugin.json schema_version '{data['schema_version']}' differs from "
                    f"known current version '{CURRENT_PLUGIN_VERSION}'"
                )

        # Check description_for_model length (CRITICAL: 2048 chars)
        if "description_for_model" in data:
            dfm_len = len(data["description_for_model"])
            if dfm_len <= 2048:
                self.passed.append(
                    f"apiPlugin.json description_for_model <= 2048 chars ({dfm_len})"
                )
            else:
                self.errors.append(
                    f"apiPlugin.json description_for_model is {dfm_len} chars "
                    f"(max 2048 — content beyond this MAY be ignored by Copilot)"
                )

        # Check description_for_model content quality
        if "description_for_model" in data:
            dfm = data["description_for_model"]
            dfm_len = len(dfm)

            # Warn if it looks like function-specific guidance is crammed in
            func_specific_patterns = re.findall(
                r'(parameter|map\s+["\']|default\s+to|when\s+the\s+user\s+asks\s+for)',
                dfm, re.IGNORECASE
            )
            if len(func_specific_patterns) >= 3:
                self.warnings.append(
                    f"description_for_model appears to contain function-specific guidance "
                    f"({len(func_specific_patterns)} matches). Consider moving parameter mappings "
                    f"and per-function rules to functions[].states.reasoning.instructions instead"
                )

            # Warn if very long even under limit
            if 1500 < dfm_len <= 2048:
                self.warnings.append(
                    f"description_for_model is {dfm_len} chars — approaching 2,048 limit. "
                    f"Keep to 2-3 sentences about when to use this plugin; move details to "
                    f"function states"
                )

        # Validate functions
        funcs_without_reasoning = []
        funcs_without_responding = []
        if "functions" in data:
            for i, func in enumerate(data["functions"]):
                fname = func.get("name", f"unnamed[{i}]")
                if "name" in func and "description" in func:
                    self.passed.append(f"apiPlugin.json function '{fname}' has name and description")
                else:
                    self.errors.append(f"apiPlugin.json function[{i}] missing name or description")

                # Check for reasoning/responding states
                if "states" in func:
                    if "reasoning" in func["states"]:
                        reasoning = func["states"]["reasoning"]
                        self.passed.append(
                            f"apiPlugin.json function '{fname}' has reasoning state"
                        )
                        # Check reasoning has instructions array
                        if "instructions" in reasoning:
                            instr = reasoning["instructions"]
                            if isinstance(instr, list) and len(instr) > 0:
                                self.passed.append(
                                    f"apiPlugin.json function '{fname}' reasoning has "
                                    f"{len(instr)} instruction(s)"
                                )
                            else:
                                self.warnings.append(
                                    f"apiPlugin.json function '{fname}' reasoning.instructions "
                                    f"is empty — add parameter mapping and usage guidance"
                                )
                    else:
                        funcs_without_reasoning.append(fname)

                    if "responding" in func["states"]:
                        responding = func["states"]["responding"]
                        self.passed.append(
                            f"apiPlugin.json function '{fname}' has responding state"
                        )
                        if "instructions" in responding:
                            instr = responding["instructions"]
                            if isinstance(instr, list) and len(instr) > 0:
                                self.passed.append(
                                    f"apiPlugin.json function '{fname}' responding has "
                                    f"{len(instr)} instruction(s)"
                                )
                            else:
                                self.warnings.append(
                                    f"apiPlugin.json function '{fname}' responding.instructions "
                                    f"is empty — add result formatting guidance"
                                )
                    else:
                        funcs_without_responding.append(fname)
                else:
                    funcs_without_reasoning.append(fname)
                    funcs_without_responding.append(fname)

            if funcs_without_reasoning:
                self.warnings.append(
                    f"apiPlugin.json functions missing states.reasoning: "
                    f"{funcs_without_reasoning}. Add reasoning.instructions with parameter "
                    f"mapping and usage guidance for better function selection"
                )
            if funcs_without_responding:
                self.warnings.append(
                    f"apiPlugin.json functions missing states.responding: "
                    f"{funcs_without_responding}. Add responding.instructions with result "
                    f"formatting and error handling guidance"
                )

        # Validate runtimes
        valid_runtime_types = {"OpenApi", "RemoteMCPServer", "LocalPlugin"}
        if "runtimes" in data:
            for i, runtime in enumerate(data["runtimes"]):
                rt_type = runtime.get("type", "unknown")
                if "type" in runtime:
                    if rt_type in valid_runtime_types:
                        self.passed.append(f"apiPlugin.json runtime[{i}] type '{rt_type}' is valid")
                    else:
                        self.warnings.append(
                            f"apiPlugin.json runtime[{i}] has unknown type: {rt_type}"
                        )
                else:
                    self.errors.append(f"apiPlugin.json runtime[{i}] missing type")

                if "spec" in runtime and "url" in runtime["spec"]:
                    self.passed.append(f"apiPlugin.json runtime[{i}] has spec.url")
                elif rt_type == "OpenApi":
                    self.warnings.append(f"apiPlugin.json runtime[{i}] missing spec.url")

        # Cross-check functions vs run_for_functions
        func_names = {f["name"] for f in data.get("functions", []) if "name" in f}
        runtime_funcs: set[str] = set()
        for rt in data.get("runtimes", []):
            runtime_funcs.update(rt.get("run_for_functions", []))

        orphaned = func_names - runtime_funcs
        if orphaned:
            self.errors.append(
                f"apiPlugin.json functions not in any run_for_functions: {sorted(orphaned)}"
            )
        elif func_names:
            self.passed.append("apiPlugin.json all functions are in run_for_functions")

        extra = runtime_funcs - func_names
        if extra:
            self.errors.append(
                f"apiPlugin.json run_for_functions references undefined functions: {sorted(extra)}"
            )
        elif runtime_funcs:
            self.passed.append(
                "apiPlugin.json all run_for_functions entries have matching function definitions"
            )

    def _validate_security_info(self):
        """Validate security_info.data_handling on apiPlugin functions."""
        plugin_path = self.package_path / "apiPlugin.json"
        api_path = self.package_path / "apiDefinition.json"

        if not plugin_path.exists():
            return

        plugin_data = self._load_json(plugin_path)
        if not plugin_data:
            return

        # Build a set of consequential operationIds from apiDefinition
        consequential_ops: set[str] = set()
        if api_path.exists():
            api_data = self._load_json(api_path)
            if api_data and "paths" in api_data:
                for path_obj in api_data["paths"].values():
                    for method_obj in path_obj.values():
                        if not isinstance(method_obj, dict):
                            continue
                        if method_obj.get("x-openai-isConsequential") is True:
                            op_id = method_obj.get("operationId")
                            if op_id:
                                consequential_ops.add(op_id)

        for func in plugin_data.get("functions", []):
            fname = func.get("name", "unnamed")
            caps = func.get("capabilities", {})
            security_info = caps.get("security_info") if isinstance(caps, dict) else None

            if security_info is None:
                self.warnings.append(
                    f"Function '{fname}' has no security_info — it cannot interact "
                    f"with other plugins or capabilities"
                )
                # Still check consequential mismatch even without security_info
                if fname in consequential_ops:
                    self.warnings.append(
                        f"Function '{fname}' is x-openai-isConsequential but has no "
                        f"security_info.data_handling with 'ResourceStateUpdate'"
                    )
                continue

            data_handling = security_info.get("data_handling")
            if data_handling is None:
                # security_info exists but no data_handling — check consequential
                if fname in consequential_ops:
                    self.warnings.append(
                        f"Function '{fname}' is x-openai-isConsequential but has no "
                        f"security_info.data_handling with 'ResourceStateUpdate'"
                    )
                continue

            if not isinstance(data_handling, list):
                self.errors.append(
                    f"Function '{fname}' security_info.data_handling must be an array"
                )
                continue

            # Validate each value
            invalid_values = [v for v in data_handling if v not in VALID_DATA_HANDLING_VALUES]
            if invalid_values:
                self.errors.append(
                    f"Function '{fname}' security_info.data_handling has invalid values: "
                    f"{invalid_values}. Valid values: {sorted(VALID_DATA_HANDLING_VALUES)}"
                )
            else:
                self.passed.append(
                    f"Function '{fname}' security_info.data_handling values are valid"
                )

            # Consequential check: isConsequential but no ResourceStateUpdate
            if fname in consequential_ops and "ResourceStateUpdate" not in data_handling:
                self.warnings.append(
                    f"Function '{fname}' is x-openai-isConsequential but "
                    f"security_info.data_handling does not include 'ResourceStateUpdate'"
                )

    def _validate_api_definition(self):
        """Validate apiDefinition.json structure if it exists."""
        path = self.package_path / "apiDefinition.json"
        if not path.exists():
            return

        data = self._load_json(path)
        if not data:
            return

        # Check OpenAPI version
        if "openapi" in data:
            if data["openapi"].startswith(CURRENT_OPENAPI_VERSION):
                self.passed.append(f"apiDefinition.json has OpenAPI version {data['openapi']}")
            else:
                self.warnings.append(
                    f"apiDefinition.json OpenAPI version '{data['openapi']}' may not be compatible "
                    f"(expected {CURRENT_OPENAPI_VERSION}.x)"
                )

        # Check paths exist
        if "paths" in data and len(data["paths"]) > 0:
            self.passed.append(f"apiDefinition.json has {len(data['paths'])} path(s)")
        else:
            self.warnings.append("apiDefinition.json has no paths defined")

        # Check isConsequential on operations
        if "paths" in data:
            for path_name, path_obj in data["paths"].items():
                for method, method_obj in path_obj.items():
                    if not isinstance(method_obj, dict):
                        continue
                    op_id = method_obj.get("operationId", "unknown")
                    if "x-openai-isConsequential" not in method_obj:
                        self.warnings.append(
                            f"apiDefinition.json {method.upper()} {path_name} ({op_id}) "
                            f"missing x-openai-isConsequential"
                        )

    def _validate_icons(self):
        """Validate icon files exist and are valid PNG."""
        for icon in ["color.png", "outline.png"]:
            path = self.package_path / icon
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        header = f.read(8)
                        if header[:4] == b'\x89PNG':
                            self.passed.append(f"{icon} is valid PNG")
                        else:
                            self.errors.append(f"{icon} is not a valid PNG file")
                except Exception as e:
                    self.errors.append(f"{icon} could not be read: {e}")

    def _check_cross_references(self):
        """Check that file references between manifests are valid."""
        # manifest -> declarativeAgent
        manifest_path = self.package_path / "manifest.json"
        if manifest_path.exists():
            data = self._load_json(manifest_path)
            if data and "copilotAgents" in data and "declarativeAgents" in data["copilotAgents"]:
                for agent in data["copilotAgents"]["declarativeAgents"]:
                    if "file" in agent:
                        agent_path = self.package_path / agent["file"]
                        if agent_path.exists():
                            self.passed.append(
                                f"manifest.json references existing file: {agent['file']}"
                            )
                        else:
                            self.errors.append(
                                f"manifest.json references missing file: {agent['file']}"
                            )

        # declarativeAgent -> apiPlugin
        da_path = self.package_path / "declarativeAgent.json"
        if da_path.exists():
            data = self._load_json(da_path)
            if data and "actions" in data:
                for action in data["actions"]:
                    if "file" in action:
                        action_path = self.package_path / action["file"]
                        if action_path.exists():
                            self.passed.append(
                                f"declarativeAgent.json references existing file: {action['file']}"
                            )
                        else:
                            self.errors.append(
                                f"declarativeAgent.json references missing file: {action['file']}"
                            )

        # apiPlugin -> apiDefinition
        plugin_path = self.package_path / "apiPlugin.json"
        if plugin_path.exists():
            data = self._load_json(plugin_path)
            if data and "runtimes" in data:
                for runtime in data["runtimes"]:
                    if "spec" in runtime and "url" in runtime["spec"]:
                        spec_path = self.package_path / runtime["spec"]["url"]
                        if spec_path.exists():
                            self.passed.append(
                                f"apiPlugin.json references existing file: "
                                f"{runtime['spec']['url']}"
                            )
                        else:
                            self.errors.append(
                                f"apiPlugin.json references missing file: "
                                f"{runtime['spec']['url']}"
                            )

    def _check_function_sync(self):
        """Check that apiPlugin function names match apiDefinition operationIds."""
        plugin_path = self.package_path / "apiPlugin.json"
        api_path = self.package_path / "apiDefinition.json"

        if not plugin_path.exists() or not api_path.exists():
            return

        plugin_data = self._load_json(plugin_path)
        api_data = self._load_json(api_path)

        if not plugin_data or not api_data:
            return

        plugin_funcs = {f["name"] for f in plugin_data.get("functions", []) if "name" in f}

        api_operation_ids: set[str] = set()
        for path_obj in api_data.get("paths", {}).values():
            for method_obj in path_obj.values():
                if isinstance(method_obj, dict) and "operationId" in method_obj:
                    api_operation_ids.add(method_obj["operationId"])

        missing_ops = plugin_funcs - api_operation_ids
        if missing_ops:
            self.errors.append(
                f"apiPlugin functions missing from apiDefinition operationIds: "
                f"{sorted(missing_ops)}"
            )

        extra_ops = api_operation_ids - plugin_funcs
        if extra_ops:
            self.warnings.append(
                f"apiDefinition operationIds not in apiPlugin functions: {sorted(extra_ops)}"
            )

        if not missing_ops and not extra_ops and plugin_funcs:
            self.passed.append(
                f"apiPlugin functions and apiDefinition operationIds are in sync "
                f"({len(plugin_funcs)} functions)"
            )

    def _load_json(self, path: Path) -> Any | None:
        """Load and parse JSON file, with caching."""
        cache_key = str(path)
        if cache_key in self._json_cache:
            return self._json_cache[cache_key]

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._json_cache[cache_key] = data
                return data
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in {path.name}: {e}")
            self._json_cache[cache_key] = None
            return None
        except Exception as e:
            self.errors.append(f"Could not read {path.name}: {e}")
            self._json_cache[cache_key] = None
            return None

    def _print_results(self):
        """Print validation results."""
        print("\n## PASSED CHECKS")
        print("-" * 40)
        for msg in self.passed:
            print(f"  [PASS] {msg}")

        if self.warnings:
            print("\n## WARNINGS")
            print("-" * 40)
            for msg in self.warnings:
                print(f"  [WARN] {msg}")

        if self.errors:
            print("\n## ERRORS")
            print("-" * 40)
            for msg in self.errors:
                print(f"  [FAIL] {msg}")

        print("\n" + "=" * 60)
        print(
            f"Summary: {len(self.passed)} passed, "
            f"{len(self.warnings)} warnings, {len(self.errors)} errors"
        )

        if len(self.errors) == 0:
            print("\nappPackage validation PASSED")
        else:
            print("\nappPackage validation FAILED")


def main():
    if len(sys.argv) > 1:
        package_path = sys.argv[1]
    else:
        package_path = "appPackage"

    if not os.path.exists(package_path):
        print(f"Error: appPackage not found at {package_path}")
        print("Usage: python validate_apppackage.py [path_to_apppackage]")
        sys.exit(1)

    validator = AppPackageValidator(package_path)
    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
