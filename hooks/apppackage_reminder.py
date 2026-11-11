#!/usr/bin/env python3
"""PostToolUse hook: remind Claude to validate after an appPackage file changes.

Reads the hook payload on stdin. When the edited file is inside an appPackage
folder or is one of the package's JSON/SKILL.md files, prints a JSON
`additionalContext` reminder (plain stdout is not shown to Claude for
PostToolUse). Never blocks and never fails the tool call.
"""
import json
import re
import sys

PATTERN = re.compile(
    r"(^|/)appPackage(\.[\w-]+)?(/|$)"
    r"|(^|/)(manifest|declarativeAgent|apiPlugin[\w-]*|apiDefinition[\w-]*)\.json$",
    re.IGNORECASE,
)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    tool_input = payload.get("tool_input") or {}
    path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if not path:
        return
    normalized = path.replace("\\", "/")
    if not PATTERN.search(normalized):
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"{path} is part of a Copilot declarative agent appPackage. "
                "Run /copilot-declarative-agent:validate (or "
                "scripts/validate_apppackage.py) before finishing."
            ),
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
