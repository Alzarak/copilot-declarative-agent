"""Validator regression tests.

Mutates the v1.9 fixture (tests/fixtures/v1.9-skills-mcp) and confirms each
schema check fires. Run from the repo root:

    python tests/test_validate_apppackage.py
"""
import copy, importlib.util, json, shutil, sys, tempfile
from pathlib import Path

repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("v", repo / "scripts" / "validate_apppackage.py")
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
src = repo / "tests" / "fixtures" / "v1.9-skills-mcp" / "appPackage"
base = json.loads((src / "declarativeAgent.json").read_text(encoding="utf-8"))
plugin = json.loads((src / "apiPlugin-tickets.json").read_text(encoding="utf-8"))


def run(mutate_da=None, mutate_plugin=None, files=None):
    tmp = Path(tempfile.mkdtemp()) / "appPackage"
    shutil.copytree(src, tmp)
    da = copy.deepcopy(base); pl = copy.deepcopy(plugin)
    if mutate_da: mutate_da(da)
    if mutate_plugin: mutate_plugin(pl)
    (tmp / "declarativeAgent.json").write_text(json.dumps(da), encoding="utf-8")
    (tmp / "apiPlugin-tickets.json").write_text(json.dumps(pl), encoding="utf-8")
    for rel, body in (files or {}).items():
        p = tmp / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body, encoding="utf-8")
    val = v.AppPackageValidator(str(tmp))
    for step in ("_check_required_files", "_validate_manifest", "_validate_declarative_agent",
                 "_validate_api_plugin", "_validate_security_info", "_validate_api_definition",
                 "_check_cross_references", "_check_function_sync"):
        getattr(val, step)()
    return val


cases = {
    "9 skills": (lambda d: d.update(agent_skills=[{"folder": f"skills/s{i}"} for i in range(9)]), None, None, "max 8"),
    "../ folder": (lambda d: d.update(agent_skills=[{"folder": "../outside"}]), None, None, "../"),
    "absolute folder": (lambda d: d.update(agent_skills=[{"folder": "/skills/x"}]), None, None, "relative"),
    "backslash": (lambda d: d.update(agent_skills=[{"folder": "skills\\ticket-triage"}]), None, None, "forward slashes"),
    "no SKILL.md": (lambda d: d.update(agent_skills=[{"folder": "skills/empty"}]), None, {"skills/empty/readme.txt": "x"}, "no SKILL.md"),
    "missing dir": (lambda d: d.update(agent_skills=[{"folder": "skills/nope"}]), None, None, "not a directory"),
    "no frontmatter desc": (lambda d: d.update(agent_skills=[{"folder": "skills/bad"}]), None, {"skills/bad/SKILL.md": "---\nname: bad\n---\nbody"}, "missing 'description'"),
    "bad file type": (None, None, {"skills/ticket-triage/tool.exe": "x"}, "not allowed"),
    "extra skill prop": (lambda d: d.update(agent_skills=[{"folder": "skills/ticket-triage", "name": "x"}]), None, None, "only 'folder'"),
    "v1.8 with agent_skills": (lambda d: d.update(version="v1.8", **{"$schema": d["$schema"].replace("v1.9", "v1.8")}), None, None, "requires schema v1.9"),
    "v1.6 with EmailActions": (lambda d: (d.update(version="v1.6", **{"$schema": d["$schema"].replace("v1.9", "v1.6")}), d.pop("agent_skills"), d.pop("editorial_answers"), d["behavior_overrides"].pop("default_response_mode"), [s.pop("depends_on", None) for s in d["conversation_starters"]]), None, None, "capability 'EmailActions', which requires schema v1.8"),
    "13 starters": (lambda d: d.update(conversation_starters=[{"text": str(i)} for i in range(13)]), None, None, "max 12"),
    "unknown capability": (lambda d: d["capabilities"].append({"name": "Calendar"}), None, None, "unknown capability"),
    "duplicate capability": (lambda d: d["capabilities"].append({"name": "Fabric"}), None, None, "more than once"),
    "EmailActions props": (lambda d: d["capabilities"].__setitem__(1, {"name": "EmailActions", "folders": []}), None, None, "no properties besides"),
    "bad response mode": (lambda d: d["behavior_overrides"].update(default_response_mode="Fast"), None, None, "default_response_mode 'Fast'"),
    "unknown top-level": (lambda d: d.update(skills=[]), None, None, "unrecognized top-level property 'skills'"),
    "schema/version mismatch": (lambda d: d.update(version="v1.8"), None, None, "must match"),
    "no v prefix": (lambda d: d.update(version="1.9"), None, None, "'v' prefix"),
    "relative MCP url": (None, lambda p: p["runtimes"][0]["spec"].update(url="mcp.json"), None, "absolute URL"),
    "MCP file+tools": (None, lambda p: p["runtimes"][0]["spec"].update(mcp_tool_description={"file": "t.json", "tools": []}), None, "exactly one"),
    "MCP missing tool file": (None, lambda p: p["runtimes"][0]["spec"].update(mcp_tool_description={"file": "t.json"}), None, "file missing"),
    "pinned fn not in run_for": (None, lambda p: (p.update(functions=[{"name": "getTicket", "description": "d"}]), p["runtimes"][0].update(run_for_functions=["other"])), None, "not in any run_for_functions"),
}

failed = 0
for name, (md, mp, files, expect) in cases.items():
    val = run(md, mp, files)
    hit = [e for e in val.errors if expect in e]
    status = "ok  " if hit else "FAIL"
    if not hit:
        failed += 1
    print(f"{status} {name:28} -> {hit[0] if hit else val.errors}")

# Wildcard function names should be accepted
val = run(None, lambda p: (p.update(functions=[{"name": "getTicket", "description": "d"}]), p["runtimes"][0].update(run_for_functions=["get*"])))
ok = not val.errors
failed += 0 if ok else 1
print(f"{'ok  ' if ok else 'FAIL'} {'wildcard run_for_functions':28} -> errors={val.errors}")
print(f"\n{len(cases) + 1 - failed}/{len(cases) + 1} negative/positive cases behaved as expected")
sys.exit(1 if failed else 0)
