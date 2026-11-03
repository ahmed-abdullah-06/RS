# ============================================================
#  R.S. - Red Shirt AI Agent
#  agents.py — preset agents (OpenJarvis-style)
#
#  OpenJarvis ships built-in agents that each bundle a role, a tool
#  set and an execution mode. RS mirrors that:
#
#     chat             on-demand   54+ tools, local-first
#     simple           on-demand   no tools, pure conversation
#     code_assistant   on-demand   writes + RUNS code in workspace/
#     deep_research    on-demand   multi-hop web research w/ citations
#     morning_digest   scheduled   spoken daily briefing
#     monitor          continuous  stateful monitoring w/ memory
#
#  A preset is just configuration — the agent loop lives in brain.py.
# ============================================================

import os
import json
import datetime

import config
import brain
import traces


# ============================================================
#  PART 1 — PRESET OBJECT
# ============================================================

class Preset:
    """One agent preset: role, tools, engine policy, execution mode."""

    def __init__(self, name, description, system_prompt="",
                 tools=None, policy=None, max_steps=None,
                 runner="agent", schedule=None, params=None):
        self.name          = name
        self.description   = description
        self.system_prompt = system_prompt
        self.tools         = tools          # None = default belt (brain.default_tools())
        self.policy        = policy         # local_first | local | cloud
        self.max_steps     = max_steps
        self.runner        = runner         # agent | research | digest
        self.schedule      = schedule       # None = on demand
        self.params        = params or {}

    def to_dict(self):
        return {"name": self.name, "description": self.description,
                "system_prompt": self.system_prompt,
                "tool_names": _tool_names(self.tools),
                "policy": self.policy, "max_steps": self.max_steps,
                "runner": self.runner, "schedule": self.schedule,
                "params": self.params}


def _tool_names(tools):
    if tools is None:
        return ["*"]
    return [t["function"]["name"] for t in tools]


def _pick(names):
    """Filters brain.TOOLS down to a named subset (keeps order)."""
    wanted = set(names)
    return [t for t in brain.TOOLS if t["function"]["name"] in wanted]


# ============================================================
#  PART 2 — BUILT-IN PRESETS
# ============================================================

CODE_TOOLS = [
    "run_python", "run_python_file", "run_shell",
    "workspace_write", "workspace_read", "workspace_list",
    "read_file", "create_file", "list_files", "open_file",
]

# Everyday belt + heavy screen-driving belt live in brain.py (they are
# tool-selection concerns, and brain.think() needs the default one even
# when no preset is passed). See the comment block there for the
# measured token cost of each belt.

BUILTIN = {
    "chat": Preset(
        name="chat",
        description="Default RS — everyday tool belt, local model first, cloud when needed.",
        # None = the dynamic default belt (brain.default_tools()), which
        # is CHAT_TOOLS + whatever skills are installed right now.
        tools=None,
        policy="local_first",
        max_steps=config.MAX_AGENT_STEPS,
    ),

    "simple": Preset(
        name="simple",
        description="Lightweight conversation, no tools. Fastest and fully offline.",
        tools=[],
        policy="local",
        max_steps=1,
        system_prompt=("Answer conversationally in 1-3 sentences. No tools "
                       "exist for you. Never invent facts you cannot know — "
                       "the time, system stats, what is on screen. If a "
                       "question needs a tool, say so plainly instead of "
                       "guessing."),
    ),

    "code_assistant": Preset(
        name="code_assistant",
        description="Writes and executes Python/shell inside workspace/ (CodeAct-style).",
        tools=_pick(CODE_TOOLS),
        policy="local_first",
        max_steps=8,
        system_prompt=(
            "You are RS in CODE mode. You have a real Python and shell runner "
            "inside a sandbox folder called the workspace.\n"
            "- Write code, RUN it, read the output, then iterate.\n"
            "- Never assume an output — run it and report what happened.\n"
            "- Keep each run small and fast (under 60s).\n"
            "- Save scripts with workspace_write so the user can keep them.\n"
            "- Destructive commands are blocked by design; explain rather than retry."
        ),
    ),

    "deep_research": Preset(
        name="deep_research",
        description="Multi-hop research across the live web, answered with citations.",
        runner="research",
        policy="local_first",
        params={"depth": 2},
        system_prompt="You are a research agent. Cite every claim.",
    ),

    "morning_digest": Preset(
        name="morning_digest",
        description="Spoken daily briefing: weather, system, email, calendar, news.",
        runner="digest",
        policy="local",
        schedule=f"0 {config.BRIEFING_HOUR} * * *",
        system_prompt="You tighten a daily briefing into a spoken script.",
    ),

    "monitor": Preset(
        name="monitor",
        description="Continuous monitoring agent with compressed long-term memory.",
        tools=_pick(["monitor_cycle", "monitor_search", "get_monitor_status",
                     "get_system_info", "get_cpu_usage", "get_ram_usage",
                     "get_battery", "check_internet"]),
        policy="local",
        max_steps=3,
        system_prompt=(
            "You are RS in MONITOR mode. You watch the machine and report "
            "trends, not single readings. Retrieve your own past cycles with "
            "monitor_search before concluding anything."
        ),
    ),

    "screen": Preset(
        name="screen",
        description="Drives the screen and browser: look, click, type, complete tasks.",
        tools=_pick(brain.SCREEN_TOOLS),
        policy="local_first",
        max_steps=6,
        system_prompt=(
            "You are RS in SCREEN mode. You can see the screen and move the "
            "mouse/keyboard. Before every action, take a screenshot and read "
            "it so you act on what is really there. Prefer the dedicated "
            "tools (browser_go_to, find_and_click) over do_task_on_screen, "
            "which is the last resort. Report each action as you take it."
        ),
    ),
}


# ============================================================
#  PART 3 — USER PRESETS (saved overrides)
# ============================================================

def _load_user():
    try:
        with open(config.PRESETS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(preset):
    """Persists a preset (built-in or new) to presets.json."""
    data = _load_user()
    data[preset.name] = preset.to_dict()
    try:
        with open(config.PRESETS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        return True
    except Exception as e:
        print(f"Preset save error: {e}")
        return False


def get(name="chat"):
    """Returns a Preset by name (user overrides win over built-ins)."""
    data = _load_user()
    d = data.get(name)

    if d:
        tools = None if d.get("tool_names") == ["*"] else _pick(d.get("tool_names") or [])
        return Preset(name=d.get("name", name),
                      description=d.get("description", ""),
                      system_prompt=d.get("system_prompt", ""),
                      tools=tools, policy=d.get("policy"),
                      max_steps=d.get("max_steps"),
                      runner=d.get("runner", "agent"),
                      schedule=d.get("schedule"),
                      params=d.get("params", {}))

    if name in BUILTIN:
        return BUILTIN[name]

    return BUILTIN["chat"]


def all_presets():
    """Merged list for the CLI and the HUD."""
    out = {}
    for name, p in BUILTIN.items():
        out[name] = p.to_dict()
    for name, d in _load_user().items():
        out[name] = d
    return list(out.values())


def init_preset(name, force=False):
    """
    Writes a preset into presets.json so it survives and can be tuned.
    This is `rs init --preset <name>`.
    """
    if name not in BUILTIN:
        return (False, f"Unknown preset '{name}'. Available: "
                       f"{', '.join(BUILTIN)}")

    existing = _load_user()
    if name in existing and not force:
        return (False, f"Preset '{name}' is already saved. "
                       f"Use --force to overwrite it.")

    p = BUILTIN[name]
    save(p)
    return (True, f"Preset '{name}' saved to {config.PRESETS_PATH}\n"
                  f"  {p.description}")


# ============================================================
#  PART 4 — RUN
# ============================================================

def run(name, user_input, on_step=None, speak=False):
    """
    Executes one request under a preset. Returns {"response","type","preset"}.
    Delegates to the right runner:
       agent    → brain.think(preset=...)
       research → research.research(...)
       digest   → digest.build_digest(...)
    """
    preset = get(name)

    # ── Research runner ──
    if preset.runner == "research":
        import research
        result = research.research(user_input, on_step=on_step,
                                   depth=preset.params.get("depth", 2))
        return {"response": result["text"], "type": "research",
                "preset": preset.name, "sources": result.get("sources", [])}

    # ── Digest runner ──
    if preset.runner == "digest":
        import digest as digest_mod
        result = digest_mod.build_digest(speak=True, on_step=on_step)
        return {"response": result["spoken"], "type": "digest",
                "preset": preset.name}

    # ── Standard agent runner ──
    reply = brain.think(user_input, on_step=on_step, preset=preset)

    if speak:
        import voice
        import threading
        threading.Thread(target=voice.speak, args=(reply,),
                         daemon=True).start()

    return {"response": reply, "type": "agent", "preset": preset.name}


def preset_status():
    """Compact status line for the HUD/CLI."""
    lines = []
    for d in all_presets():
        mark = "●" if d["name"] == "chat" else "○"
        sched = f"  ⏱ {d['schedule']}" if d.get("schedule") else ""
        lines.append(f"  {mark} {d['name']:16s} [{d.get('policy') or 'local_first':11s}] "
                     f"{d['description']}{sched}")
    return "\n".join(lines)
