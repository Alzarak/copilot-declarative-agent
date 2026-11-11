#!/usr/bin/env python3
"""
Validate Microsoft 365 Copilot Declarative Agent appPackage structure.

Checks file existence, JSON validity, schema versions, field limits,
cross-references, function sync, and declarative agent schema compliance
(v1.0 through v1.9, including v1.9 agent_skills).

Usage:
    python validate_apppackage.py [path_to_apppackage]

If no path is provided, looks for 'appPackage' in current directory.
"""

import fnmatch
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Known current schema versions
CURRENT_MANIFEST_VERSION = "1.30"
CURRENT_DA_VERSION = "v1.9"
CURRENT_PLUGIN_VERSION = "v2.4"
CURRENT_OPENAPI_VERSION = "3.0"

# Declarative agent schema versions this validator knows about. Older versions
# are accepted with a warning; features are checked against the declared version.
KNOWN_DA_VERSIONS = ["v1.0", "v1.2", "v1.3", "v1.4", "v1.5", "v1.6", "v1.7", "v1.8", "v1.9"]

# Valid capability names (v1.9) mapped to the schema version that introduced them
CAPABILITY_MIN_VERSION = {
    "WebSearch": "v1.0",
    "OneDriveAndSharePoint": "v1.0",
    "GraphConnectors": "v1.0",
    "GraphicArt": "v1.2",
    "CodeInterpreter": "v1.2",
    "Dataverse": "v1.3",
    "TeamsMessages": "v1.3",
    "Email": "v1.3",
    "People": "v1.3",
    "ScenarioModels": "v1.4",
    "Meetings": "v1.5",
    "EmbeddedKnowledge": "v1.6",
    "EmailActions": "v1.8",
    "MeetingActions": "v1.8",
    "Fabric": "v1.9",
}
VALID_CAPABILITIES = set(CAPABILITY_MIN_VERSION)

# Capabilities that take no properties other than "name"
NAME_ONLY_CAPABILITIES = {"GraphicArt", "CodeInterpreter", "EmailActions", "MeetingActions", "Fabric"}

# Top-level declarativeAgent.json properties mapped to the version that introduced them.
# Microsoft: "Any unrecognized property makes the whole document invalid."
DA_PROPERTY_MIN_VERSION = {
    "$schema": "v1.0",
    "version": "v1.0",
    "id": "v1.0",
    "name": "v1.0",
    "description": "v1.0",
    "instructions": "v1.0",
    "capabilities": "v1.0",
    "conversation_starters": "v1.0",
    "actions": "v1.0",
    "behavior_overrides": "v1.5",
    "disclaimer": "v1.5",
    "sensitivity_label": "v1.6",
    "worker_agents": "v1.6",
    "user_overrides": "v1.6",
    "editorial_answers": "v1.7",
    "agent_skills": "v1.9",
}

# Capability-specific array limits
CAPABILITY_LIMITS = {
    "WebSearch": {"sites": 4},
    "TeamsMessages": {"urls": 5},
    "Email": {"group_mailboxes": 25},
    "Meetings": {"items_by_id": 5},
    "EmbeddedKnowledge": {"files": 10},
}

# behavior_overrides.default_response_mode (v1.7+) — exact strings, spaces included
VALID_RESPONSE_MODES = {"Auto", "Quick response", "Think deeper"}

# Agent skills (v1.9) limits from learn.microsoft.com declarative-agent-skills
AGENT_SKILLS_MAX = 8
SKILL_MD_MAX_CHARS = 20_000
SKILL_MAX_DEPTH = 3
SKILLS_MAX_FILES = 350
APP_PACKAGE_MAX_BYTES = 10 * 1024 * 1024
SKILL_ALLOWED_EXTENSIONS = {
    # content
    ".json", ".xml", ".yaml", ".yml", ".ini", ".config", ".utf8", ".docx", ".doc",
    ".docm", ".pdf", ".txt", ".rtf", ".md", ".ppt", ".pptx", ".ppsm", ".xlsx",
    ".xls", ".xlsm", ".csv", ".tsv", ".html", ".htm", ".png", ".jpg", ".jpeg",
    ".gif", ".bmp", ".log",
    # scripts
    ".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".sh", ".bash",
}


def _version_tuple(version: str) -> tuple[int, ...] | None:
    """Parse 'v1.9' / '1.9' into (1, 9). Returns None if unparseable."""
    m = re.fullmatch(r"v?(\d+)\.(\d+)", str(version).strip())
    return (int(m.group(1)), int(m.group(2))) if m else None


def _is_absolute_url(value: str) -> bool:
    return bool(re.match(r"^https?://", str(value), re.I))

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

        # Check $schema property (required by atk validate)
        expected_schema = f"https://developer.microsoft.com/json-schemas/teams/v{CURRENT_MANIFEST_VERSION}/MicrosoftTeams.schema.json"
        if "$schema" in data:
            self.passed.append(f"manifest.json has $schema property")
        else:
            self.errors.append(
                f"manifest.json missing '$schema' property — required by atk validate. "
                f"Add: \"$schema\": \"{expected_schema}\""
            )

        # Check schema version currency
        if "manifestVersion" in data:
            if data["manifestVersion"] == CURRENT_MANIFEST_VERSION:
                self.passed.append(f"manifest.json manifestVersion is current ({CURRENT_MANIFEST_VERSION})")
            else:
                self.warnings.append(
                    f"manifest.json manifestVersion '{data['manifestVersion']}' differs from "
                    f"known current version '{CURRENT_MANIFEST_VERSION}' (still accepted; "
                    f"root-level agentSkills needs 1.28+)"
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

        # Root-level agentSkills (app manifest 1.28+), same {folder} shape as agent_skills
        if "agentSkills" in data:
            mv = _version_tuple(data.get("manifestVersion", ""))
            if mv and mv < (1, 28):
                self.errors.append(
                    f"manifest.json uses 'agentSkills', which requires manifestVersion 1.28 or later"
                )
            self._validate_agent_skills(data["agentSkills"], "manifest.json agentSkills")

    # Features whose minimum version is v1.7 or later come from Microsoft's
    # published change lists and are enforced as errors. Older minimums are
    # reported as warnings because Microsoft no longer documents them precisely.
    _STRICT_GATE_FROM = (1, 7)

    def _gate(self, feature: str, min_version: str, declared: tuple[int, ...] | None):
        """Report a feature used with a declared schema version older than it requires."""
        if declared is None:
            return
        needed = _version_tuple(min_version)
        if needed and declared < needed:
            msg = (
                f"declarativeAgent.json uses {feature}, which requires schema {min_version} "
                f"or later (declared v{declared[0]}.{declared[1]}). Run update-schema."
            )
            if needed >= self._STRICT_GATE_FROM:
                self.errors.append(msg)
            else:
                self.warnings.append(msg)

    def _validate_declarative_agent(self):
        """Validate declarativeAgent.json structure (schema v1.0–v1.9)."""
        path = self.package_path / "declarativeAgent.json"
        if not path.exists():
            return

        data = self._load_json(path)
        if not data:
            return
        if not isinstance(data, dict):
            self.errors.append("declarativeAgent.json root must be a JSON object")
            return

        # Check required fields
        required = ["version", "name", "description", "instructions"]
        for field in required:
            if field in data:
                self.passed.append(f"declarativeAgent.json has '{field}'")
            else:
                self.errors.append(f"declarativeAgent.json missing required field: '{field}'")

        # Check $schema property (required by atk validate)
        declared_str = str(data.get("version", ""))
        declared = _version_tuple(declared_str)
        schema_version = declared_str if declared else CURRENT_DA_VERSION
        expected_schema = (
            f"https://developer.microsoft.com/json-schemas/copilot/declarative-agent/"
            f"{schema_version}/schema.json"
        )
        if "$schema" in data:
            self.passed.append("declarativeAgent.json has $schema property")
            schema_url = str(data["$schema"])
            m = re.search(r"/declarative-agent/(v\d+\.\d+)/", schema_url)
            if m and declared_str and m.group(1) != declared_str:
                self.errors.append(
                    f"declarativeAgent.json $schema points to {m.group(1)} but version is "
                    f"'{declared_str}' — they must match"
                )
        else:
            self.errors.append(
                f"declarativeAgent.json missing '$schema' property — required by atk validate. "
                f"Add: \"$schema\": \"{expected_schema}\""
            )

        # Schema version: current passes, older warns, unknown/newer warns, malformed errors
        if "version" in data:
            current = _version_tuple(CURRENT_DA_VERSION)
            if declared is None:
                self.errors.append(
                    f"declarativeAgent.json version '{declared_str}' is not a valid schema "
                    f"version (expected e.g. '{CURRENT_DA_VERSION}')"
                )
            elif not declared_str.startswith("v"):
                self.errors.append(
                    f"declarativeAgent.json version '{declared_str}' must include the 'v' "
                    f"prefix (e.g. 'v{declared[0]}.{declared[1]}')"
                )
            elif declared == current:
                self.passed.append(f"declarativeAgent.json version is current ({CURRENT_DA_VERSION})")
            elif declared < current:
                self.warnings.append(
                    f"declarativeAgent.json version '{declared_str}' is older than the current "
                    f"'{CURRENT_DA_VERSION}'. Still accepted; run update-schema to use newer features "
                    f"(agent_skills, EmailActions, MeetingActions, Fabric, editorial_answers)"
                )
            else:
                self.warnings.append(
                    f"declarativeAgent.json version '{declared_str}' is newer than this validator "
                    f"knows ('{CURRENT_DA_VERSION}'); newer properties are not checked"
                )
            if declared_str and declared_str not in KNOWN_DA_VERSIONS and declared and declared <= current:
                self.warnings.append(
                    f"declarativeAgent.json version '{declared_str}' is not a published schema version"
                )

        # Unknown top-level properties invalidate the whole document
        newer_than_known = declared is not None and declared > _version_tuple(CURRENT_DA_VERSION)
        for key in data:
            if key in DA_PROPERTY_MIN_VERSION:
                self._gate(f"'{key}'", DA_PROPERTY_MIN_VERSION[key], declared)
            elif not newer_than_known:
                self.errors.append(
                    f"declarativeAgent.json has unrecognized top-level property '{key}' "
                    f"(Microsoft rejects documents with unknown properties)"
                )

        # Validate field lengths
        for field, limit in (("name", 100), ("description", 1000)):
            if field in data:
                value = str(data[field])
                if not value.strip():
                    self.errors.append(f"declarativeAgent.json '{field}' must not be empty")
                elif len(value) <= limit:
                    self.passed.append(f"declarativeAgent.json '{field}' <= {limit} chars ({len(value)})")
                else:
                    self.errors.append(
                        f"declarativeAgent.json '{field}' too long ({len(value)} chars, max {limit})"
                    )

        if "instructions" in data:
            instr = str(data["instructions"])
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
        cap_names_present: set[str] = set()
        if "capabilities" in data:
            seen: set[str] = set()
            for i, cap in enumerate(data["capabilities"]):
                if not isinstance(cap, dict) or "name" not in cap:
                    self.errors.append(f"declarativeAgent.json capabilities[{i}] missing 'name'")
                    continue
                cap_name = cap["name"]
                if cap_name in seen:
                    self.errors.append(
                        f"declarativeAgent.json lists capability '{cap_name}' more than once "
                        f"(max one of each type)"
                    )
                seen.add(cap_name)
                cap_names_present.add(cap_name)
                if cap_name in VALID_CAPABILITIES:
                    self.passed.append(f"declarativeAgent.json has valid capability: {cap_name}")
                    self._gate(f"capability '{cap_name}'", CAPABILITY_MIN_VERSION[cap_name], declared)
                else:
                    self.errors.append(
                        f"declarativeAgent.json has unknown capability: {cap_name}. "
                        f"Valid ({CURRENT_DA_VERSION}): {sorted(VALID_CAPABILITIES)}"
                    )

                if cap_name in NAME_ONLY_CAPABILITIES:
                    extra = sorted(k for k in cap if k != "name")
                    if extra:
                        self.errors.append(
                            f"capability '{cap_name}' takes no properties besides 'name' "
                            f"(found {extra})"
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

                if cap_name == "ScenarioModels" and "models" not in cap:
                    self.errors.append("capability 'ScenarioModels' missing required 'models'")

                if cap_name == "EmbeddedKnowledge" and "files" not in cap and declared and declared >= (1, 8):
                    self.errors.append("capability 'EmbeddedKnowledge' missing required 'files' (v1.8+)")

            # EmailActions is independent of Email: Email scoping does not apply to it
            if "EmailActions" in cap_names_present:
                email_cap = next(
                    (c for c in data["capabilities"] if isinstance(c, dict) and c.get("name") == "Email"),
                    None,
                )
                if email_cap and any(k in email_cap for k in ("shared_mailbox", "group_mailboxes", "folders")):
                    self.warnings.append(
                        "Email is scoped (shared_mailbox/group_mailboxes/folders) but that scoping "
                        "does NOT apply to EmailActions — EmailActions can act on the user's whole "
                        "mailbox. Constrain write actions in instructions if needed"
                    )

        # Validate conversation_starters (12 in v1.7+; v1.6 docs conflict — 6 vs 12)
        if "conversation_starters" in data:
            starters = data["conversation_starters"]
            if declared == (1, 6):
                limit, hard = 6, False
            else:
                limit, hard = 12, True
            if len(starters) > 12:
                self.errors.append(
                    f"declarativeAgent.json conversation_starters has {len(starters)} items (max 12)"
                )
            elif len(starters) > limit:
                msg = (
                    f"declarativeAgent.json conversation_starters has {len(starters)} items; the "
                    f"v1.6 docs say max {limit} in one place and 12 in another. Upgrade to "
                    f"{CURRENT_DA_VERSION} (max 12) or trim to {limit}"
                )
                (self.errors if hard else self.warnings).append(msg)
            else:
                self.passed.append(
                    f"declarativeAgent.json conversation_starters count OK ({len(starters)}/{limit})"
                )
            for i, starter in enumerate(starters):
                if "text" in starter:
                    self.passed.append(f"declarativeAgent.json conversation_starter[{i}] has 'text'")
                else:
                    self.errors.append(
                        f"declarativeAgent.json conversation_starter[{i}] missing 'text'"
                    )
                if "depends_on" in starter:
                    self._gate(f"conversation_starters[{i}].depends_on", "v1.7", declared)
                    for dep in starter["depends_on"]:
                        if dep.get("name") != "capabilities" or "id" not in dep:
                            self.errors.append(
                                f"conversation_starter[{i}].depends_on items need "
                                f"{{\"name\": \"capabilities\", \"id\": \"<CapabilityName>\"}}"
                            )
                        elif dep["id"] not in cap_names_present:
                            self.warnings.append(
                                f"conversation_starter[{i}] depends on capability '{dep['id']}', "
                                f"which this agent does not declare — the starter will never show"
                            )

        # Validate actions (1-10)
        if "actions" in data:
            actions = data["actions"]
            if len(actions) == 0:
                self.errors.append("declarativeAgent.json actions is empty (min 1 if present)")
            if len(actions) > 10:
                self.errors.append(
                    f"declarativeAgent.json actions has {len(actions)} items (max 10)"
                )
            for i, action in enumerate(actions):
                if "id" in action and "file" in action:
                    self.passed.append(f"declarativeAgent.json action[{i}] has id and file")
                elif "schema_version" in action or "functions" in action:
                    self.passed.append(f"declarativeAgent.json action[{i}] is an inline plugin manifest")
                else:
                    self.errors.append(f"declarativeAgent.json action[{i}] missing id or file")

        # Validate agent_skills (v1.9)
        if "agent_skills" in data:
            self._validate_agent_skills(data["agent_skills"], "declarativeAgent.json agent_skills")

        # Validate behavior_overrides
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
            if "default_response_mode" in bo:
                self._gate("behavior_overrides.default_response_mode", "v1.7", declared)
                if bo["default_response_mode"] in VALID_RESPONSE_MODES:
                    self.passed.append("behavior_overrides.default_response_mode is valid")
                else:
                    self.errors.append(
                        f"behavior_overrides.default_response_mode '{bo['default_response_mode']}' "
                        f"is invalid. Valid: {sorted(VALID_RESPONSE_MODES)}"
                    )

        # Validate disclaimer
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

        # Validate editorial_answers (v1.7)
        if "editorial_answers" in data:
            ea = data["editorial_answers"]
            has_url, has_answers = "url" in ea, "answers" in ea
            if has_url == has_answers:
                self.errors.append("editorial_answers must have exactly one of 'url' or 'answers'")
            if has_answers:
                answers = ea["answers"]
                if len(answers) > 300:
                    self.errors.append(f"editorial_answers.answers has {len(answers)} items (max 300)")
                for i, ans in enumerate(answers):
                    if "question" not in ans or "answer" not in ans:
                        self.errors.append(
                            f"editorial_answers.answers[{i}] needs both 'question' and 'answer'"
                        )
                    thr = ans.get("similarity_thresholds", {})
                    for k in ("min", "max"):
                        if k in thr and not (isinstance(thr[k], int) and 0 <= thr[k] <= 10):
                            self.errors.append(
                                f"editorial_answers.answers[{i}].similarity_thresholds.{k} "
                                f"must be an integer 0–10"
                            )
                if answers and not any("question" not in a or "answer" not in a for a in answers):
                    self.passed.append(f"editorial_answers has {len(answers)} valid answer(s)")

        # Validate worker_agents (preview). id is required in v1.6; v1.8+ docs are ambiguous.
        if "worker_agents" in data:
            for i, wa in enumerate(data["worker_agents"]):
                if "id" in wa:
                    self.passed.append(f"worker_agents[{i}] has 'id'")
                elif declared and declared >= (1, 8):
                    self.warnings.append(
                        f"worker_agents[{i}] has no 'id' — v1.8+ docs mark it optional but "
                        f"define no alternative property; include 'id'"
                    )
                else:
                    self.errors.append(f"worker_agents[{i}] missing required 'id'")

        # Validate user_overrides
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

    def _validate_agent_skills(self, skills: Any, label: str):
        """Validate an agent_skills / agentSkills array (each item: {"folder": "<relative dir>"})."""
        if not isinstance(skills, list):
            self.errors.append(f"{label} must be an array")
            return
        if len(skills) > AGENT_SKILLS_MAX:
            self.errors.append(f"{label} has {len(skills)} items (max {AGENT_SKILLS_MAX})")
        else:
            self.passed.append(f"{label} count OK ({len(skills)}/{AGENT_SKILLS_MAX})")

        root = self.package_path.resolve()
        seen: set[str] = set()
        total_files = 0
        for i, skill in enumerate(skills):
            where = f"{label}[{i}]"
            if not isinstance(skill, dict) or "folder" not in skill:
                self.errors.append(f"{where} missing required 'folder'")
                continue
            extra = sorted(k for k in skill if k != "folder")
            if extra:
                self.errors.append(f"{where} has unrecognized properties {extra} (only 'folder' allowed)")
            folder = skill["folder"]
            if not isinstance(folder, str) or not folder.strip():
                self.errors.append(f"{where}.folder must be a non-empty string")
                continue
            if len(folder) > 256:
                self.errors.append(f"{where}.folder is {len(folder)} chars (max 256)")
            if "\\" in folder:
                self.errors.append(f"{where}.folder '{folder}' must use forward slashes only")
                continue
            if folder.startswith("/") or re.match(r"^[A-Za-z]:", folder) or _is_absolute_url(folder):
                self.errors.append(f"{where}.folder '{folder}' must be relative to the manifest")
                continue
            if ".." in folder.split("/"):
                self.errors.append(f"{where}.folder '{folder}' must not contain '../'")
                continue

            target = (self.package_path / folder).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                self.errors.append(f"{where}.folder '{folder}' resolves outside the app package")
                continue
            key = str(target).lower()
            if key in seen:
                self.errors.append(f"{where}.folder '{folder}' is listed more than once")
            seen.add(key)
            if not target.is_dir():
                self.errors.append(f"{where}.folder '{folder}' is not a directory in the app package")
                continue

            skill_md = target / "SKILL.md"
            if not skill_md.is_file():
                self.errors.append(f"{where}.folder '{folder}' has no SKILL.md")
                continue
            self.passed.append(f"{where} '{folder}' contains SKILL.md")
            self._validate_skill_md(skill_md, f"{folder}/SKILL.md", target.name)

            for f in target.rglob("*"):
                if not f.is_file():
                    continue
                total_files += 1
                rel = f.relative_to(target)
                if len(rel.parts) - 1 > SKILL_MAX_DEPTH:
                    self.errors.append(
                        f"{folder}/{rel.as_posix()} is nested deeper than {SKILL_MAX_DEPTH} directories"
                    )
                if f.suffix.lower() not in SKILL_ALLOWED_EXTENSIONS:
                    self.errors.append(
                        f"{folder}/{rel.as_posix()} has a file type not allowed in agent skills "
                        f"('{f.suffix or '(none)'}')"
                    )

        if total_files > SKILLS_MAX_FILES:
            self.errors.append(f"agent skills contain {total_files} files (max {SKILLS_MAX_FILES} across all skills)")

    def _validate_skill_md(self, path: Path, label: str, folder_name: str):
        """Check SKILL.md YAML frontmatter (name, description) and the 20,000-char limit."""
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            self.errors.append(f"{label} could not be read: {e}")
            return
        if len(text) >= SKILL_MD_MAX_CHARS:
            self.errors.append(f"{label} is {len(text)} chars (must be under {SKILL_MD_MAX_CHARS})")
        m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
        if not m:
            self.errors.append(f"{label} has no YAML frontmatter (--- name/description ---)")
            return
        front: dict[str, str] = {}
        for line in m.group(1).splitlines():
            km = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if km:
                front[km.group(1)] = km.group(2).strip().strip("'\"")
        for key in ("name", "description"):
            if key not in front:
                self.errors.append(f"{label} frontmatter missing '{key}'")
        name = front.get("name", "")
        if name:
            # Agent Skills standard conventions — not confirmed by Microsoft for Copilot, so warn only
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
                self.warnings.append(
                    f"{label} name '{name}' does not follow the Agent Skills convention "
                    f"(lowercase letters, digits, hyphens; max 64)"
                )
            elif name != folder_name:
                self.warnings.append(
                    f"{label} name '{name}' does not match its folder name '{folder_name}'"
                )
            else:
                self.passed.append(f"{label} frontmatter has name '{name}' and description")

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
        """Validate apiPlugin JSON files. Supports both single apiPlugin.json
        and multiple apiPlugin-*.json files referenced from declarativeAgent.json."""
        # Discover plugin files from declarativeAgent.json actions
        plugin_files = []
        da_path = self.package_path / "declarativeAgent.json"
        if da_path.exists():
            da_data = self._load_json(da_path)
            if da_data and "actions" in da_data:
                for action in da_data["actions"]:
                    pfile = action.get("file", "")
                    if (self.package_path / pfile).exists():
                        plugin_files.append(pfile)
        # Fallback to legacy single file
        if not plugin_files and (self.package_path / "apiPlugin.json").exists():
            plugin_files.append("apiPlugin.json")

        for pfile in plugin_files:
            self._validate_single_api_plugin(pfile)

    def _validate_single_api_plugin(self, plugin_filename: str):
        """Validate a single apiPlugin JSON file."""
        path = self.package_path / plugin_filename

        data = self._load_json(path)
        if not data:
            return

        # Check required fields
        required = ["schema_version", "name_for_human", "functions"]
        for field in required:
            if field in data:
                self.passed.append(f"{plugin_filename} has '{field}'")
            else:
                self.errors.append(f"{plugin_filename} missing required field: '{field}'")

        # Check $schema property (required by atk validate)
        expected_schema = f"https://developer.microsoft.com/json-schemas/copilot/plugin/{CURRENT_PLUGIN_VERSION}/schema.json"
        if "$schema" in data:
            if data["$schema"] in (
                expected_schema,
                f"https://aka.ms/json-schemas/copilot/plugin/{CURRENT_PLUGIN_VERSION}/schema.json",
            ):
                self.passed.append(f"{plugin_filename} has correct $schema URL")
            else:
                self.warnings.append(
                    f"{plugin_filename} $schema URL '{data['$schema']}' differs from expected '{expected_schema}'"
                )
        else:
            self.errors.append(
                f"{plugin_filename} missing '$schema' property — required by atk validate. "
                f"Add: \"$schema\": \"{expected_schema}\""
            )

        # Check schema version currency
        if "schema_version" in data:
            if data["schema_version"] == CURRENT_PLUGIN_VERSION:
                self.passed.append(
                    f"{plugin_filename} schema_version is current ({CURRENT_PLUGIN_VERSION})"
                )
            else:
                self.warnings.append(
                    f"{plugin_filename} schema_version '{data['schema_version']}' differs from "
                    f"known current version '{CURRENT_PLUGIN_VERSION}'"
                )

        # Check description_for_model length (CRITICAL: 2048 chars)
        if "description_for_model" in data:
            dfm_len = len(data["description_for_model"])
            if dfm_len <= 2048:
                self.passed.append(
                    f"{plugin_filename} description_for_model <= 2048 chars ({dfm_len})"
                )
            else:
                self.errors.append(
                    f"{plugin_filename} description_for_model is {dfm_len} chars "
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
                    self.passed.append(f"{plugin_filename} function '{fname}' has name and description")
                else:
                    self.errors.append(f"{plugin_filename} function[{i}] missing name or description")

                # Check for reasoning/responding states
                if "states" in func:
                    if "reasoning" in func["states"]:
                        reasoning = func["states"]["reasoning"]
                        self.passed.append(
                            f"{plugin_filename} function '{fname}' has reasoning state"
                        )
                        # Check reasoning has instructions array
                        if "instructions" in reasoning:
                            instr = reasoning["instructions"]
                            if isinstance(instr, list) and len(instr) > 0:
                                self.passed.append(
                                    f"{plugin_filename} function '{fname}' reasoning has "
                                    f"{len(instr)} instruction(s)"
                                )
                            else:
                                self.warnings.append(
                                    f"{plugin_filename} function '{fname}' reasoning.instructions "
                                    f"is empty — add parameter mapping and usage guidance"
                                )
                    else:
                        funcs_without_reasoning.append(fname)

                    if "responding" in func["states"]:
                        responding = func["states"]["responding"]
                        self.passed.append(
                            f"{plugin_filename} function '{fname}' has responding state"
                        )
                        if "instructions" in responding:
                            instr = responding["instructions"]
                            if isinstance(instr, list) and len(instr) > 0:
                                self.passed.append(
                                    f"{plugin_filename} function '{fname}' responding has "
                                    f"{len(instr)} instruction(s)"
                                )
                            else:
                                self.warnings.append(
                                    f"{plugin_filename} function '{fname}' responding.instructions "
                                    f"is empty — add result formatting guidance"
                                )
                    else:
                        funcs_without_responding.append(fname)
                else:
                    funcs_without_reasoning.append(fname)
                    funcs_without_responding.append(fname)

            if funcs_without_reasoning:
                self.warnings.append(
                    f"{plugin_filename} functions missing states.reasoning: "
                    f"{funcs_without_reasoning}. Add reasoning.instructions with parameter "
                    f"mapping and usage guidance for better function selection"
                )
            if funcs_without_responding:
                self.warnings.append(
                    f"{plugin_filename} functions missing states.responding: "
                    f"{funcs_without_responding}. Add responding.instructions with result "
                    f"formatting and error handling guidance"
                )

        # Validate runtimes
        valid_runtime_types = {"OpenApi", "RemoteMCPServer", "LocalPlugin"}
        for i, runtime in enumerate(data.get("runtimes", [])):
            rt_type = runtime.get("type", "unknown")
            if "type" in runtime:
                if rt_type in valid_runtime_types:
                    self.passed.append(f"{plugin_filename} runtime[{i}] type '{rt_type}' is valid")
                else:
                    self.warnings.append(
                        f"{plugin_filename} runtime[{i}] has unknown type: {rt_type}"
                    )
            else:
                self.errors.append(f"{plugin_filename} runtime[{i}] missing type")

            spec = runtime.get("spec", {}) or {}
            if rt_type == "RemoteMCPServer":
                self._validate_mcp_runtime(plugin_filename, i, runtime)
            elif "url" in spec:
                self.passed.append(f"{plugin_filename} runtime[{i}] has spec.url")
            elif rt_type == "OpenApi":
                self.warnings.append(f"{plugin_filename} runtime[{i}] missing spec.url")

        # Cross-check functions vs run_for_functions (wildcards such as "*" are allowed)
        func_names = {f["name"] for f in data.get("functions", []) if "name" in f}
        patterns: set[str] = set()
        for rt in data.get("runtimes", []):
            patterns.update(rt.get("run_for_functions", []))
        wildcards = {p for p in patterns if any(c in p for c in "*?[")}
        literals = patterns - wildcards

        orphaned = {
            f for f in func_names
            if f not in literals and not any(fnmatch.fnmatchcase(f, w) for w in wildcards)
        }
        if orphaned:
            self.errors.append(
                f"{plugin_filename} functions not in any run_for_functions: {sorted(orphaned)}"
            )
        elif func_names:
            self.passed.append(f"{plugin_filename} all functions are in run_for_functions")

        extra = literals - func_names
        if extra:
            self.errors.append(
                f"{plugin_filename} run_for_functions references undefined functions: {sorted(extra)}"
            )
        elif literals:
            self.passed.append(
                f"{plugin_filename} all run_for_functions entries have matching function definitions"
            )
        if wildcards and not func_names:
            self.passed.append(
                f"{plugin_filename} uses dynamic tool discovery (functions: [], "
                f"run_for_functions: {sorted(wildcards)})"
            )

    def _validate_mcp_runtime(self, plugin_filename: str, i: int, runtime: dict):
        """Validate a RemoteMCPServer runtime (plugin manifest v2.4)."""
        where = f"{plugin_filename} runtime[{i}] (RemoteMCPServer)"
        spec = runtime.get("spec", {}) or {}
        url = spec.get("url", "")
        if not url:
            self.errors.append(f"{where} missing required spec.url")
        elif not _is_absolute_url(url):
            self.errors.append(f"{where} spec.url '{url}' must be an absolute URL to the MCP server")
        elif not url.lower().startswith("https://"):
            self.warnings.append(f"{where} spec.url '{url}' is not https")
        else:
            self.passed.append(f"{where} has absolute spec.url")

        if "auth" not in runtime:
            self.warnings.append(
                f"{where} has no 'auth' — the v2.4 runtime table marks it required; "
                f"add {{\"type\": \"None\"}} if the server is unauthenticated"
            )

        desc = spec.get("mcp_tool_description")
        if desc is None:
            if "*" not in runtime.get("run_for_functions", []):
                self.warnings.append(
                    f"{where} has no mcp_tool_description (dynamic discovery) — pair it with "
                    f"\"functions\": [] and \"run_for_functions\": [\"*\"]"
                )
            return
        has_file, has_tools = "file" in desc, "tools" in desc
        if has_file == has_tools:
            self.errors.append(f"{where} mcp_tool_description needs exactly one of 'file' or 'tools'")
            return
        if has_file:
            tool_path = self.package_path / desc["file"]
            if not tool_path.exists():
                self.errors.append(f"{where} mcp_tool_description.file missing: {desc['file']}")
                return
            tools_doc = self._load_json(tool_path)
            tools = tools_doc.get("tools", []) if isinstance(tools_doc, dict) else []
            self.passed.append(f"{where} references existing tool file: {desc['file']}")
        else:
            tools = desc["tools"]
        for j, tool in enumerate(tools):
            missing = [k for k in ("name", "description", "inputSchema") if k not in tool]
            if missing:
                self.errors.append(f"{where} tool[{j}] missing {missing}")
        if tools and all(all(k in t for k in ("name", "description", "inputSchema")) for t in tools):
            self.passed.append(f"{where} declares {len(tools)} MCP tool(s)")

    @staticmethod
    def _openapi_spec_file(runtime: dict) -> str:
        """Return the local OpenAPI file for an OpenApi runtime, or '' for other runtimes."""
        if runtime.get("type", "OpenApi") != "OpenApi":
            return ""
        url = (runtime.get("spec", {}) or {}).get("url", "")
        return "" if _is_absolute_url(url) else url

    def _validate_security_info(self):
        """Validate security_info.data_handling on apiPlugin functions.
        Supports multiple plugin files referenced from declarativeAgent.json."""
        # Discover all plugin files
        plugin_files = []
        da_path = self.package_path / "declarativeAgent.json"
        if da_path.exists():
            da_data = self._load_json(da_path)
            if da_data and "actions" in da_data:
                for action in da_data["actions"]:
                    pfile = action.get("file", "")
                    if (self.package_path / pfile).exists():
                        plugin_files.append(pfile)
        # Fallback to legacy single file
        if not plugin_files and (self.package_path / "apiPlugin.json").exists():
            plugin_files.append("apiPlugin.json")

        for pfile in plugin_files:
            self._validate_plugin_security_info(pfile)

    def _validate_plugin_security_info(self, plugin_filename: str):
        """Validate security_info for a single apiPlugin file."""
        plugin_path = self.package_path / plugin_filename

        plugin_data = self._load_json(plugin_path)
        if not plugin_data:
            return

        # Build a set of consequential operationIds from referenced apiDefinition(s)
        consequential_ops: set[str] = set()
        for rt in plugin_data.get("runtimes", []):
            api_file = self._openapi_spec_file(rt)
            api_path = self.package_path / api_file if api_file else None
            if api_path and api_path.exists():
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
        """Validate apiDefinition JSON files. Supports both single apiDefinition.json and
        multiple apiDefinition-*.json files referenced from apiPlugin files."""
        # Discover all apiDefinition files referenced from plugin manifests
        api_def_files = set()
        da_path = self.package_path / "declarativeAgent.json"
        if da_path.exists():
            da_data = self._load_json(da_path)
            if da_data and "actions" in da_data:
                for action in da_data["actions"]:
                    plugin_file = action.get("file", "")
                    plugin_path = self.package_path / plugin_file
                    if plugin_path.exists():
                        pdata = self._load_json(plugin_path)
                        if pdata and "runtimes" in pdata:
                            for rt in pdata["runtimes"]:
                                spec_url = self._openapi_spec_file(rt)
                                if spec_url:
                                    api_def_files.add(spec_url)

        # Fallback to legacy single file
        if not api_def_files:
            legacy = self.package_path / "apiDefinition.json"
            if legacy.exists():
                api_def_files.add("apiDefinition.json")

        for api_file in sorted(api_def_files):
            self._validate_single_api_definition(api_file)

    def _validate_single_api_definition(self, filename: str):
        """Validate a single apiDefinition JSON file."""
        path = self.package_path / filename
        if not path.exists():
            return

        # File size check
        file_size = path.stat().st_size
        file_size_kb = file_size / 1024
        if file_size > 100_000:
            self.errors.append(
                f"{filename} is {file_size_kb:.0f} KB — exceeds the 100 KB limit. "
                f"Split into multiple plugins or use $ref components to reduce size."
            )
        elif file_size > 80_000:
            self.warnings.append(
                f"{filename} is {file_size_kb:.0f} KB — approaching the 100 KB limit. "
                f"Consider using $ref components or splitting into multiple plugins."
            )

        data = self._load_json(path)
        if not data:
            return

        # Check OpenAPI version
        if "openapi" in data:
            if data["openapi"].startswith(CURRENT_OPENAPI_VERSION):
                self.passed.append(f"{filename} has OpenAPI version {data['openapi']}")
            else:
                self.warnings.append(
                    f"{filename} OpenAPI version '{data['openapi']}' may not be compatible "
                    f"(expected {CURRENT_OPENAPI_VERSION}.x)"
                )

        # Check paths exist
        if "paths" in data and len(data["paths"]) > 0:
            num_paths = len(data["paths"])
            self.passed.append(f"{filename} has {num_paths} path(s)")
            if num_paths > 25:
                self.warnings.append(
                    f"{filename} has {num_paths} operations — quality may degrade above 25. "
                    f"Consider splitting into multiple plugins."
                )
        else:
            self.warnings.append(f"{filename} has no paths defined")

        # Check isConsequential on operations
        if "paths" in data:
            for path_name, path_obj in data["paths"].items():
                for method, method_obj in path_obj.items():
                    if not isinstance(method_obj, dict):
                        continue
                    op_id = method_obj.get("operationId", "unknown")
                    if "x-openai-isConsequential" not in method_obj:
                        self.warnings.append(
                            f"{filename} {method.upper()} {path_name} ({op_id}) "
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

        # apiPlugin -> apiDefinition (supports multiple plugin files)
        plugin_files = set()
        if da_path.exists():
            da_data = self._load_json(da_path)
            if da_data and "actions" in da_data:
                for action in da_data["actions"]:
                    pfile = action.get("file", "")
                    if (self.package_path / pfile).exists():
                        plugin_files.add(pfile)
        # Fallback to legacy single file
        if not plugin_files and (self.package_path / "apiPlugin.json").exists():
            plugin_files.add("apiPlugin.json")

        for pfile in sorted(plugin_files):
            plugin_path = self.package_path / pfile
            data = self._load_json(plugin_path)
            if data and "runtimes" in data:
                for runtime in data["runtimes"]:
                    if self._openapi_spec_file(runtime):
                        spec_path = self.package_path / runtime["spec"]["url"]
                        if spec_path.exists():
                            self.passed.append(
                                f"{pfile} references existing file: "
                                f"{runtime['spec']['url']}"
                            )
                        else:
                            self.errors.append(
                                f"{pfile} references missing file: "
                                f"{runtime['spec']['url']}"
                            )

    def _check_function_sync(self):
        """Check that apiPlugin function names match apiDefinition operationIds.
        Supports multiple plugin files referenced from declarativeAgent.json."""
        # Discover all plugin files from declarativeAgent.json actions
        plugin_pairs = []  # list of (plugin_file, api_def_file)
        da_path = self.package_path / "declarativeAgent.json"
        if da_path.exists():
            da_data = self._load_json(da_path)
            if da_data and "actions" in da_data:
                for action in da_data["actions"]:
                    pfile = action.get("file", "")
                    ppath = self.package_path / pfile
                    if ppath.exists():
                        pdata = self._load_json(ppath)
                        if pdata and "runtimes" in pdata:
                            for rt in pdata["runtimes"]:
                                api_file = self._openapi_spec_file(rt)
                                if api_file and (self.package_path / api_file).exists():
                                    plugin_pairs.append((pfile, api_file))

        # Fallback to legacy single-file pattern
        if not plugin_pairs:
            legacy_plugin = self.package_path / "apiPlugin.json"
            legacy_api = self.package_path / "apiDefinition.json"
            if legacy_plugin.exists() and legacy_api.exists():
                plugin_pairs.append(("apiPlugin.json", "apiDefinition.json"))

        all_funcs_across_plugins = []
        for plugin_file, api_file in plugin_pairs:
            plugin_data = self._load_json(self.package_path / plugin_file)
            api_data = self._load_json(self.package_path / api_file)
            if not plugin_data or not api_data:
                continue

            plugin_funcs = {f["name"] for f in plugin_data.get("functions", []) if "name" in f}
            run_for = set()
            for rt in plugin_data.get("runtimes", []):
                run_for.update(rt.get("run_for_functions", []))

            api_operation_ids: set[str] = set()
            for path_obj in api_data.get("paths", {}).values():
                for method_obj in path_obj.values():
                    if isinstance(method_obj, dict) and "operationId" in method_obj:
                        api_operation_ids.add(method_obj["operationId"])

            # Check functions match run_for_functions
            funcs_not_in_run = plugin_funcs - run_for
            if funcs_not_in_run:
                self.errors.append(
                    f"{plugin_file} functions not in run_for_functions: "
                    f"{sorted(funcs_not_in_run)}"
                )
            run_not_in_funcs = run_for - plugin_funcs
            if run_not_in_funcs:
                self.warnings.append(
                    f"{plugin_file} run_for_functions entries without function definitions: "
                    f"{sorted(run_not_in_funcs)}"
                )

            # Check functions match apiDefinition operationIds
            missing_ops = plugin_funcs - api_operation_ids
            if missing_ops:
                self.errors.append(
                    f"{plugin_file} functions missing from {api_file} operationIds: "
                    f"{sorted(missing_ops)}"
                )

            extra_ops = api_operation_ids - plugin_funcs
            if extra_ops:
                self.warnings.append(
                    f"{api_file} operationIds not in {plugin_file} functions: "
                    f"{sorted(extra_ops)}"
                )

            if not missing_ops and not extra_ops and plugin_funcs:
                self.passed.append(
                    f"{plugin_file} functions and {api_file} operationIds are in sync "
                    f"({len(plugin_funcs)} functions)"
                )

            all_funcs_across_plugins.append((plugin_file, plugin_funcs))

        # Check for function overlap between plugins
        if len(all_funcs_across_plugins) > 1:
            for i, (pfile_a, funcs_a) in enumerate(all_funcs_across_plugins):
                for pfile_b, funcs_b in all_funcs_across_plugins[i + 1:]:
                    overlap = funcs_a & funcs_b
                    if overlap:
                        self.errors.append(
                            f"Function overlap between {pfile_a} and {pfile_b}: "
                            f"{sorted(overlap)}"
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
    # Windows consoles default to a legacy code page; keep em dashes and arrows readable
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

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
