# ============================================================
#  R.S. - Red Shirt AI Agent
#  brain.py — AI agent core (64 function-calling tools)
#
#  How it works:
#    user message -> engines.chat_with_fallback() (LOCAL model first,
#                    GPT-4o when it must — see engines.py)
#    model picks tool(s) -> RS executes them -> results go back
#    model sees results  -> picks next tool or gives final answer
#    (repeats up to MAX_AGENT_STEPS times)
#
#  presets (agents.py) can narrow the tool list, swap the system
#  prompt and pin an engine policy — the loop itself never changes.
#  Every run is recorded in traces.py for the learning loop.
# ============================================================

import json
import time
import datetime
import threading
import requests

import config
import memory
import skills
import engines
import traces

# Action modules (imported lazily-safe: no side effects at import time)
import app_controller
import media_player
import downloader
import computer_use
import mouse_keyboard
import vision
import browser_agent
import boot_tasks
import proactive
import code_runner
import research
import digest
import monitor


# ============================================================
#  PART 1 — TOOL DEFINITIONS (54 tools)
# ============================================================

def _t(name, description, properties=None, required=None):
    """Builds one OpenAI-style tool definition."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties or {},
                "required": required or [],
            },
        },
    }


_STR = {"type": "string"}
_INT  = {"type": "integer"}
_NUM  = {"type": "number"}

TOOLS = [
    # ── System Info (8) ───────────────────────────────────────
    _t("get_time", "Get the current time."),
    _t("get_date", "Get today's date."),
    _t("get_system_info", "Get full system info: OS, CPU, RAM, disk usage."),
    _t("get_battery", "Get battery percentage and charging status."),
    _t("get_cpu_usage", "Get current CPU usage percentage."),
    _t("get_ram_usage", "Get current RAM usage percentage and amounts."),
    _t("check_internet", "Check if the internet connection is online."),
    _t("get_ip_address", "Get the public IP address."),

    # ── App Control (4) ───────────────────────────────────────
    _t("open_app", "Open a desktop application by name (e.g. chrome, vscode, spotify, notepad).",
       {"app_name": _STR}, ["app_name"]),
    _t("close_app", "Close a running application by name.",
       {"app_name": _STR}, ["app_name"]),
    _t("open_website", "Open a website URL in the default browser.",
       {"url": _STR}, ["url"]),
    _t("search_web", "Search Google for a query in the default browser.",
       {"query": _STR}, ["query"]),

    # ── Volume (4) ────────────────────────────────────────────
    _t("volume_up", "Increase the system volume."),
    _t("volume_down", "Decrease the system volume."),
    _t("mute_volume", "Mute or unmute the system volume."),
    _t("set_volume", "Set system volume to an exact level.",
       {"level": _INT}, ["level"]),

    # ── Media (6) ─────────────────────────────────────────────
    _t("play_youtube", "Play a video/song on YouTube in the browser. Use a song or video name.",
       {"query": _STR}, ["query"]),
    _t("open_spotify", "Open Spotify, optionally searching for a song.",
       {"search": _STR}),
    _t("media_play_pause", "Toggle play/pause of the current media (system media key)."),
    _t("media_next", "Skip to the next track (system media key)."),
    _t("media_previous", "Go to the previous track (system media key)."),
    _t("download_youtube_audio", "Download a YouTube video's audio as MP3 into the downloads folder.",
       {"query_or_url": _STR}, ["query_or_url"]),

    # ── Files (7) ─────────────────────────────────────────────
    _t("create_file", "Create a new file with optional content.",
       {"filename": _STR, "content": _STR}, ["filename"]),
    _t("read_file", "Read and return the contents of a file.",
       {"filename": _STR}, ["filename"]),
    _t("delete_file", "Delete a file.",
       {"filename": _STR}, ["filename"]),
    _t("list_files", "List all files in a folder.", {"folder": _STR}),
    _t("create_folder", "Create a new folder.",
       {"folder_name": _STR}, ["folder_name"]),
    _t("open_file", "Open a file with its default application.",
       {"filepath": _STR}, ["filepath"]),
    _t("open_folder", "Open a folder in Windows Explorer.",
       {"folder_path": _STR}),

    # ── Email (1) ─────────────────────────────────────────────
    _t("send_email", "Send an email via Gmail SMTP.",
       {"to": _STR, "subject": _STR, "body": _STR}, ["to", "subject", "body"]),

    # ── PC Control (6) ────────────────────────────────────────
    _t("take_screenshot", "Take a screenshot of the entire screen and save it."),
    _t("lock_pc", "Lock the Windows session."),
    _t("shutdown_pc", "Shut down the PC after a delay in seconds (default 60).",
       {"delay": _INT}),
    _t("restart_pc", "Restart the PC after a delay in seconds (default 60).",
       {"delay": _INT}),
    _t("sleep_pc", "Put the PC to sleep."),
    _t("show_notification", "Show a Windows toast notification.",
       {"title": _STR, "message": _STR}, ["title", "message"]),

    # ── Clipboard (2) ─────────────────────────────────────────
    _t("copy_to_clipboard", "Copy text to the clipboard.",
       {"text": _STR}, ["text"]),
    _t("get_clipboard", "Get the current clipboard text."),

    # ── Vision (3) ────────────────────────────────────────────
    _t("analyze_screen", "Take a screenshot and have AI read/understand what is on screen.",
       {"question": _STR}),
    _t("find_and_click", "Find an element on screen by description and click it (uses AI vision).",
       {"element": _STR}, ["element"]),
    _t("do_task_on_screen", "LAST RESORT only: autonomously complete a task by looking at "
                            "the screen and moving the mouse/keyboard. Only when NO dedicated "
                            "tool exists for the request (runs in background).",
       {"task": _STR}, ["task"]),

    # ── Browser (6) ───────────────────────────────────────────
    _t("browser_go_to", "Open a URL in the Playwright-controlled browser.",
       {"url": _STR}, ["url"]),
    _t("browser_search_google", "Search Google in the controlled browser and return the top results.",
       {"query": _STR}, ["query"]),
    _t("send_whatsapp", "Send a WhatsApp message to a contact through WhatsApp Web.",
       {"contact": _STR, "message": _STR}, ["contact", "message"]),
    _t("read_whatsapp", "Read the latest messages from a WhatsApp contact.",
       {"contact": _STR}, ["contact"]),
    _t("read_emails", "Read the latest emails from the Gmail inbox.", {"count": _INT}),
    _t("browser_task", "LAST RESORT only: multi-step task in the controlled browser, "
                       "when browser_go_to / browser_search_google are not enough.",
       {"task": _STR}, ["task"]),

    # ── Scheduling (2) ────────────────────────────────────────
    _t("schedule_task", "Schedule a recurring RS task. trigger: 'boot', 'daily' (HH:MM), "
                        "'hourly' or 'interval' (minutes).",
       {"name": _STR, "command": _STR, "trigger": _STR, "trigger_value": _STR},
       ["name", "command", "trigger"]),
    _t("list_scheduled_tasks", "List all scheduled RS tasks."),

    # ── Reminders (2) ─────────────────────────────────────────
    _t("remind_in_minutes", "Set a reminder that fires after N minutes.",
       {"minutes": _NUM, "message": _STR}, ["minutes", "message"]),
    _t("remind_at_time", "Set a reminder at a specific 24h time today/tomorrow (e.g. '18:30').",
       {"time": _STR, "message": _STR}, ["time", "message"]),

    # ── Memory (3) ────────────────────────────────────────────
    _t("get_recent_memories", "Recall recent past conversations from long-term memory.",
       {"count": _INT}),
    _t("get_evolution_stats", "Get RS evolution stats: memories, feedback, top topics."),
    _t("get_monitor_status", "Get current PC monitor status (battery, CPU, RAM, disk, internet)."),

    # ── Code Execution (6) — code_assistant preset ────────────
    _t("run_python", "Run a Python snippet in the sandboxed workspace; returns its output.",
       {"code": _STR, "timeout": _INT}, ["code"]),
    _t("run_python_file", "Run an existing .py file in the workspace.",
       {"filename": _STR}, ["filename"]),
    _t("run_shell", "Run a shell command (PowerShell) in the workspace.",
       {"command": _STR, "timeout": _INT}, ["command"]),
    _t("workspace_write", "Write a file in the code workspace.",
       {"filename": _STR, "content": _STR}, ["filename", "content"]),
    _t("workspace_read", "Read a file from the code workspace.",
       {"filename": _STR}, ["filename"]),
    _t("workspace_list", "List the code workspace folder."),

    # ── Research (1) — deep_research preset ───────────────────
    _t("research_deep", "Multi-hop web research; returns a cited answer with sources.",
       {"question": _STR}, ["question"]),

    # ── Digest (1) — morning_digest preset ────────────────────
    _t("build_digest", "Build and speak the daily briefing.",
       {"speak": _STR}),

    # ── Monitor agent (2) — monitor preset ────────────────────
    _t("monitor_cycle", "Run one monitoring cycle now."),
    _t("monitor_search", "Search the monitor agent's long-term memory.",
       {"query": _STR}, ["query"]),
]

TOOL_NAMES = [t["function"]["name"] for t in TOOLS]


# ── Installed skills become real tools (skills_catalog.py) ──────
# Bundled seed skills are planted on first run, then every skill in
# skills_store/ registers its own tool definitions here. A skill that
# fails to load is skipped, never fatal.
def _load_skill_tools():
    """
    Syncs TOOLS with what is actually installed — adds new skill tools
    and prunes the ones whose skill was uninstalled. Safe to call again.
    """
    global TOOL_NAMES
    try:
        import skills_catalog
        skills_catalog.seed_builtins()
        skill_defs = skills_catalog.tool_definitions()
    except Exception as e:
        print(f"Skills load error: {e}")
        return 0

    skill_names = {d["function"]["name"] for d in skill_defs}

    # ── prune: drop skill tools that are no longer installed ──
    # Built-in tools carry no "[skill:" marker, so they are never touched.
    def _is_skill_tool(definition):
        return "[skill:" in (definition["function"].get("description") or "")

    removed = 0
    for i in range(len(TOOLS) - 1, -1, -1):
        definition = TOOLS[i]
        name = definition["function"]["name"]
        if _is_skill_tool(definition) and name not in skill_names:
            del TOOLS[i]
            if name in TOOL_NAMES:
                TOOL_NAMES.remove(name)
            removed += 1

    # ── add: append whatever is new ──
    known = set(TOOL_NAMES)
    added = 0
    for definition in skill_defs:
        name = definition["function"]["name"]
        if name in known:
            continue
        TOOLS.append(definition)
        TOOL_NAMES.append(name)
        known.add(name)
        added += 1
    if added or removed:
        return f"+{added} -{removed} skill tool(s)"
    return "skills in sync"


_load_skill_tools()


# ============================================================
#  TOOL BELTS — a small model should not see 72 tools
# ============================================================
#
# Measured on this machine (CPU-only, llama3.2:3b, num_ctx=4096):
#   72 tools  → schema alone is ~3700 tokens and does NOT fit in the
#               context, so Ollama silently cuts the JSON in half. The
#               model then sees a half-written schema and hallucinates
#               tool names/arguments (root cause of the "get_evolution_
#               stats" nonsense).
#   34 tools  → ~1750 tokens of schema, fits complete with room for a
#               full tool round, and tool selection became correct.
# Every tool also costs ~50 tokens of prefill on EVERY step, so the
# default belt stays lean and the heavy tools live in their own preset.

CHAT_TOOLS = [
    # ── time & machine state ──
    "get_time", "get_date", "get_system_info", "get_cpu_usage",
    "get_ram_usage", "check_internet", "get_ip_address",
    # ── apps & files ──
    "open_app", "close_app", "create_file", "read_file", "list_files",
    "open_file", "open_folder",
    # ── web ──
    "search_web", "open_website",
    # ── desktop niceties ──
    "take_screenshot", "show_notification", "copy_to_clipboard",
    "get_clipboard",
    # ── reminders & mail ──
    "remind_in_minutes", "remind_at_time", "read_emails", "send_email",
    # ── memory & quick code ──
    "get_recent_memories", "run_python",
    # ── bundled skills (advertised in the system prompt) ──
    "system_report", "top_processes",
    "git_status", "git_log", "git_diff",
    "text_stats", "text_transform", "text_replace",
]

# Screen-driving tools — their own preset so `chat` stays lean and a
# trivial "open notepad" never hijacks the autonomous mouse/keyboard mode.
SCREEN_TOOLS = [
    "analyze_screen", "find_and_click", "do_task_on_screen",
    "browser_go_to", "browser_search_google", "browser_task",
    "take_screenshot", "get_clipboard",
]


def subset(names):
    """Filters TOOLS down to a named subset (keeps order, skips unknown)."""
    wanted = set(names)
    return [t for t in TOOLS if t["function"]["name"] in wanted]


def default_tools():
    """
    The default belt: CHAT_TOOLS plus every installed skill tool.

    Recomputed on each call so a skill installed while the server is
    running is immediately usable — a static list would advertise the
    skill in the system prompt while withholding it from the schema,
    and the model would call a tool that doesn't exist.
    """
    belt = subset(CHAT_TOOLS)
    have = {t["function"]["name"] for t in belt}
    for t in TOOLS:
        name = t["function"]["name"]
        if name in have:
            continue
        if "[skill:" in (t["function"].get("description") or ""):
            belt.append(t)
            have.add(name)
    return belt


# What an agent gets when it declares no belt of its own.
DEFAULT_TOOLS = default_tools()


# ============================================================
#  PART 2 — TOOL EXECUTOR
# ============================================================

def _run_browser_task(task, max_steps=6):
    """
    Simple browser agent: read the page, let GPT-4o decide the next
    browser action (click/type/goto/done), execute, repeat.
    """
    page = browser_agent.get_page()
    for step in range(max_steps):
        try:
            text = browser_agent.get_page_text()[:4000]
        except Exception:
            text = ""
        try:
            links = browser_agent.get_all_links()[:25]
        except Exception:
            links = []

        prompt = (
            f"You are controlling a browser to do: \"{task}\"\n"
            f"Current page: {browser_agent.get_current_url()}\n"
            f"Visible text:\n{text}\n"
            f"Top links: {json.dumps(links)[:1500]}\n\n"
            "Reply with ONLY JSON — the single next action:\n"
            '{"action":"goto","url":"https://..."}\n'
            '{"action":"click_text","text":"link/button text"}\n'
            '{"action":"type","text":"text to type here"}\n'
            '{"action":"press","key":"enter"}\n'
            '{"action":"scroll","direction":"down"}\n'
            '{"action":"done","summary":"what happened"}'
        )
        try:
            r = requests.post(config.API_URL, headers={
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"},
                json={"model": config.MODEL,
                      "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 200}, timeout=45)
            raw = r.json()["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].replace("json", "", 1)
            action = json.loads(raw)
        except Exception as e:
            return f"Browser task failed at step {step + 1}: {e}"

        a = action.get("action")
        if a == "done":
            return f"Browser task complete: {action.get('summary', 'done')}"
        if a == "goto":
            browser_agent.go_to(action.get("url", ""))
        elif a == "click_text":
            browser_agent.click_element(text=action.get("text", ""))
        elif a == "type":
            page.keyboard.type(action.get("text", ""))
        elif a == "press":
            browser_agent.press_key(action.get("key", "enter"))
        elif a == "scroll":
            browser_agent.scroll_page(action.get("direction", "down"))

    return "Browser task reached its step limit."


def execute_tool(name, args):
    """
    Executes one tool call and always returns a string result
    (sent back to the model as the tool's output).
    """
    args = args or {}
    try:
        # ── System Info (8) ──
        if name == "get_time":            return skills.get_time()
        if name == "get_date":            return skills.get_date()
        if name == "get_system_info":     return skills.get_system_info()
        if name == "get_battery":         return skills.get_battery()
        if name == "get_cpu_usage":       return skills.get_cpu_usage()
        if name == "get_ram_usage":       return skills.get_ram_usage()
        if name == "check_internet":      return skills.check_internet()
        if name == "get_ip_address":      return skills.get_ip_address()

        # ── App Control (4) ──
        if name == "open_app":
            ok = app_controller.open_app(args.get("app_name", ""))
            return f"Opened {args.get('app_name')}." if ok else \
                   f"Could not open {args.get('app_name')}."
        if name == "close_app":
            ok = app_controller.close_app(args.get("app_name", ""))
            return f"Closed {args.get('app_name')}." if ok else \
                   f"{args.get('app_name')} was not running."
        if name == "open_website": return skills.open_website(args.get("url", ""))
        if name == "search_web":   return skills.search_web(args.get("query", ""))

        # ── Volume (4) ──
        if name == "volume_up":    app_controller.volume_up();    return "Volume increased."
        if name == "volume_down":  app_controller.volume_down();  return "Volume decreased."
        if name == "mute_volume":  app_controller.mute_volume();  return "Volume muted/unmuted."
        if name == "set_volume":
            level = max(0, min(100, int(args.get("level", 50))))
            ok = app_controller.set_volume(level)
            return f"Volume set to {level}%." if ok else "Could not set volume."

        # ── Media (6) ──
        if name == "play_youtube":
            ok = media_player.play_youtube(args.get("query", ""))
            return f"Playing on YouTube: {args.get('query')}" if ok else "YouTube play failed."
        if name == "open_spotify":
            media_player.open_spotify(search=args.get("search"))
            return "Spotify opened." + \
                   (f" Searching for {args.get('search')}." if args.get("search") else "")
        if name == "media_play_pause":  media_player.media_play_pause();  return "Toggled play/pause."
        if name == "media_next":        media_player.media_next();        return "Skipped to next track."
        if name == "media_previous":    media_player.media_previous();    return "Went to previous track."
        if name == "download_youtube_audio":
            path = downloader.download_youtube(args.get("query_or_url", ""), mode="audio")
            return f"Downloaded: {path}" if path else "Download failed."

        # ── Files (7) ──
        if name == "create_file":
            return skills.create_file(args.get("filename", ""),
                                      args.get("content", ""))
        if name == "read_file":     return skills.read_file(args.get("filename", ""))
        if name == "delete_file":   return skills.delete_file(args.get("filename", ""))
        if name == "list_files":    return skills.list_files(args.get("folder", "."))
        if name == "create_folder": return skills.create_folder(args.get("folder_name", ""))
        if name == "open_file":     return skills.open_file(args.get("filepath", ""))
        if name == "open_folder":   return skills.open_folder(args.get("folder_path", "."))

        # ── Email (1) ──
        if name == "send_email":
            return skills.send_email(args.get("to", ""),
                                     args.get("subject", ""),
                                     args.get("body", ""))

        # ── PC Control (6) ──
        if name == "take_screenshot":
            path = computer_use.take_screenshot()
            return f"Screenshot saved: {path}" if path else "Screenshot failed."
        if name == "lock_pc":     return skills.lock_pc()
        if name == "shutdown_pc": return skills.shutdown_pc(int(args.get("delay", 60)))
        if name == "restart_pc":  return skills.restart_pc(int(args.get("delay", 60)))
        if name == "sleep_pc":    return skills.sleep_pc()
        if name == "show_notification":
            app_controller.show_notification(args.get("title", "RS"),
                                             args.get("message", ""))
            return "Notification shown."

        # ── Clipboard (2) ──
        if name == "copy_to_clipboard": return skills.copy_to_clipboard(args.get("text", ""))
        if name == "get_clipboard":     return skills.get_clipboard()

        # ── Vision (3) ──
        if name == "analyze_screen":
            return vision.analyze_screen(
                args.get("question", "What do you see on this screen?"))
        if name == "find_and_click":
            pos = vision.find_element(args.get("element", ""))
            if pos:
                mouse_keyboard.human_click(pos[0], pos[1])
                return f"Clicked '{args.get('element')}' at ({pos[0]}, {pos[1]})."
            return f"Could not find '{args.get('element')}' on screen."
        if name == "do_task_on_screen":
            task = args.get("task", "")
            threading.Thread(target=vision.run_task_autonomously,
                             args=(task,), daemon=True).start()
            return f"Autonomous task started in background: {task}"

        # ── Browser (6) ──
        if name == "browser_go_to":
            ok = browser_agent.go_to(args.get("url", ""))
            return f"Opened {args.get('url')}." if ok else "Navigation failed."
        if name == "browser_search_google":
            results = browser_agent.google_search(args.get("query", ""))
            if not results:
                return "No results found."
            lines = [f"{i + 1}. {r.get('title', '')} — {r.get('url', '')}"
                     for i, r in enumerate(results[:5])]
            return "Top Google results:\n" + "\n".join(lines)
        if name == "send_whatsapp":
            ok = browser_agent.send_whatsapp_message(args.get("contact", ""),
                                                     args.get("message", ""))
            return f"WhatsApp sent to {args.get('contact')}." if ok else "WhatsApp send failed."
        if name == "read_whatsapp":
            msgs = browser_agent.read_whatsapp_messages(args.get("contact", ""))
            if not msgs:
                return "No messages found."
            return "Latest messages:\n" + "\n".join(
                f"- {m.get('text', '')}" for m in msgs)
        if name == "read_emails":
            count = int(args.get("count", 5))
            emails = browser_agent.read_emails(count)
            if not emails:
                return "No emails found."
            return "Latest emails:\n" + "\n".join(
                f"- From {e.get('sender', '?')}: {e.get('subject', '')} "
                f"({e.get('time', '')})" for e in emails)
        if name == "browser_task":
            threading.Thread(target=lambda: browser_agent.start_browser(
                headless=False, save_session=True), daemon=True).start()
            return _run_browser_task(args.get("task", ""))

        # ── Scheduling (2) ──
        if name == "schedule_task":
            task = boot_tasks.add_task(
                args.get("name", "Task"),
                args.get("command", ""),
                args.get("trigger", "daily"),
                args.get("trigger_value"))
            boot_tasks.setup_scheduler()
            return (f"Task '{task['name']}' scheduled "
                    f"({task['trigger']} {task.get('trigger_value') or ''}).")
        if name == "list_scheduled_tasks":
            tasks = boot_tasks.load_tasks()
            if not tasks:
                return "No scheduled tasks."
            return "Scheduled tasks:\n" + "\n".join(
                f"- {t['name']} [{t['trigger']} {t.get('trigger_value') or ''}] "
                f"({t.get('run_count', 0)} runs)" for t in tasks)

        # ── Reminders (2) ──
        if name == "remind_in_minutes":
            r = proactive.add_reminder(args.get("message", "Reminder"),
                                       minutes=float(args.get("minutes", 5)))
            return r
        if name == "remind_at_time":
            r = proactive.add_reminder(args.get("message", "Reminder"),
                                       at_time=args.get("time", ""))
            return r

        # ── Memory (3) ──
        if name == "get_recent_memories":
            return memory.get_recent_memories(int(args.get("count", 5)))
        if name == "get_evolution_stats":  return memory.get_evolution_stats()
        if name == "get_monitor_status":   return proactive.get_monitor_status()

        # ── Code Execution (6) ──
        if name == "run_python":
            return code_runner.run_python(args.get("code", ""),
                                          args.get("timeout", 60))
        if name == "run_python_file":
            return code_runner.run_python_file(args.get("filename", ""),
                                               args.get("timeout", 60))
        if name == "run_shell":
            return code_runner.run_shell(args.get("command", ""),
                                         args.get("timeout", 60))
        if name == "workspace_write":
            return code_runner.write_file(args.get("filename", ""),
                                          args.get("content", ""))
        if name == "workspace_read":
            return code_runner.read_file(args.get("filename", ""))
        if name == "workspace_list":
            return code_runner.list_workspace()

        # ── Research (1) ──
        if name == "research_deep":
            return research.research_summary(args.get("question", ""))

        # ── Digest (1) ──
        if name == "build_digest":
            speak = str(args.get("speak", "yes")).lower() not in ("no", "false", "0")
            d = digest.build_digest(speak=speak)
            return f"Digest ready:\n{d['text']}"

        # ── Monitor agent (2) ──
        if name == "monitor_cycle":
            entry = monitor.cycle(force=True)
            return json.dumps({k: entry.get(k) for k in
                               ("time", "alert", "message",
                                "cpu", "ram", "disk", "battery")},
                              ensure_ascii=False)
        if name == "monitor_search":
            hits = monitor.retrieval(args.get("query", ""))
            if not hits:
                return "No matching cycles in monitor memory."
            return json.dumps(hits[:5], ensure_ascii=False)[:2000]

        # ── Installed skills (skills_catalog.py) ──
        import skills_catalog
        if skills_catalog.has_tool(name):
            return skills_catalog.run(name, args)

        return f"Unknown tool: {name}"

    except Exception as e:
        return f"Tool '{name}' failed: {e}"


# ============================================================
#  PART 3 — AGENT LOOP (the actual thinking)
# ============================================================

conversation_history = []


def _trim_history():
    """Keeps session context bounded."""
    if len(conversation_history) > config.MAX_HISTORY * 2:
        del conversation_history[:len(conversation_history) - config.MAX_HISTORY * 2]


def _system_prompt(extra=""):
    past_memories = memory.get_recent_memories(5)
    interests     = memory.get_interests_summary()
    bad_responses = memory.get_bad_responses()

    # Installed skills teach RS how to use them (skills_catalog.py).
    try:
        import skills_catalog
        skill_block = skills_catalog.skills_prompt_block()
    except Exception:
        skill_block = ""

    preset_block = f"""
--- ACTIVE AGENT MODE ---
{extra.strip()}
--- END AGENT MODE ---
""" if extra else ""

    # A tool-less preset has no get_time, so the model INVENTS the clock
    # (observed: "12:12 PM" at 06:32). Give it the real one — a handful
    # of tokens, and every answer that mentions "now" becomes honest.
    now = datetime.datetime.now()

    return config.PERSONALITY + preset_block + f"""
Current model: {engines.get_engine().model}
Current date & time: {now.strftime('%A, %d %B %Y · %H:%M:%S')} (local)
{skill_block}
--- PAST MEMORIES ---
{past_memories}
--- END OF MEMORIES ---

--- USER INTERESTS ---
{interests}
--- END OF INTERESTS ---

--- LEARN FROM MISTAKES ---
{bad_responses}
--- END OF MISTAKES ---

Use memories to personalize responses. Use interests to tailor your tone.
Avoid repeating mistakes from bad responses.
"""


def _fallback_skills(user_input):
    """
    Offline path (no API key / API down): try the keyword skill router.
    Returns a string, or None if nothing matched.
    """
    cmd = user_input.lower().strip()

    router = {
        "time": skills.get_time, "date": skills.get_date,
        "system info": skills.get_system_info, "battery": skills.get_battery,
        "cpu": skills.get_cpu_usage, "ram": skills.get_ram_usage,
        "screenshot": lambda: f"Screenshot saved: {computer_use.take_screenshot()}",
        "clipboard": skills.get_clipboard,
        "evolve": memory.get_evolution_stats, "stats": memory.get_evolution_stats,
    }
    if cmd in router:
        return router[cmd]()

    for prefix, fn in [("open ", skills.open_app),
                       ("search ", skills.search_web),
                       ("youtube ", skills.search_youtube),
                       ("open website ", skills.open_website)]:
        if cmd.startswith(prefix):
            return fn(user_input[len(prefix):].strip())

    return None


def _assistant_msg(engine_name, content, calls):
    """Formats the assistant turn that carried tool calls — per engine."""
    if engine_name == "ollama":
        return {"role": "assistant", "content": content or "",
                "tool_calls": [{"function": {"name":     c["name"],
                                             "arguments": c["args"]}}
                               for c in calls]}
    return {"role": "assistant", "content": content or "",
            "tool_calls": [{"id": c["id"], "type": "function",
                            "function": {"name":      c["name"],
                                         "arguments": json.dumps(c["args"])}}
                           for c in calls]}


def _tool_msg(engine_name, call, result):
    """Formats one tool result — per engine."""
    if engine_name == "ollama":
        return {"role": "tool", "tool_name": call["name"], "content": result}
    return {"role": "tool", "tool_call_id": call["id"], "content": result}


def think(user_input, on_step=None, speak_steps=False, preset=None):
    """
    Main agent entry point.
      user_input : what the user said
      on_step    : optional callback(dict) — receives live step events:
                   {"type":"tool",  "name":..., "args":...}
                   {"type":"result","name":..., "result":...}
                   {"type":"final", "text":...}
      speak_steps: unused placeholder (kept for API compatibility)
      preset     : optional agents.Preset — narrows the tool list, swaps
                   the system prompt and sets the engine policy.

    Engine routing is local-first (engines.py): the Ollama model answers
    when it can, GPT-4o escalates when it must. Every run is traced.
    """
    def step(event):
        if on_step:
            try:
                on_step(event)
            except Exception:
                pass

    # ── Preset (agent mode) or default chat ──
    preset_name = getattr(preset, "name", "chat")
    policy      = getattr(preset, "policy", None)
    # None = no belt declared → the default lean belt. NOT `or TOOLS`:
    # that expression also turned `tools=[]` (the tool-free `simple`
    # preset) into all 72 tools, because [] is falsy.
    preset_tools = getattr(preset, "tools", None)
    tool_set     = default_tools() if preset_tools is None else preset_tools
    max_steps   = getattr(preset, "max_steps", None) or config.MAX_AGENT_STEPS
    mode_prompt = getattr(preset, "system_prompt", "")

    t0           = time.time()
    steps_log    = []
    usage_total  = {"prompt_tokens": 0, "completion_tokens": 0}
    engine_used  = None
    model_used   = ""
    escalated    = None

    def log(event):
        steps_log.append(event)
        step(event)

    # ── No engine at all? Fall back to keyword skills ──
    cloud_ready = bool(config.OPENROUTER_API_KEY)
    local_ready = engines.local_engine().available()[0]
    if not cloud_ready and not local_ready:
        result = _fallback_skills(user_input)
        return result or ("No model engine available, sir. Install Ollama "
                          "(winget install Ollama.Ollama) or add "
                          "OPENROUTER_API_KEY to .env.")

    conversation_history.append({"role": "user", "content": user_input})
    _trim_history()

    messages = ([{"role": "system", "content": _system_prompt(mode_prompt)}]
                + list(conversation_history))

    final_reply = None

    # ── Agent loop: up to max_steps tool rounds ──
    for _ in range(max_steps):
        try:
            reply = engines.chat_with_fallback(messages, tools=tool_set,
                                               policy=policy, max_tokens=1500)
        except engines.EngineError as e:
            traces.record(preset_name, "?", "?", user_input, steps_log,
                          final=f"engine error: {e}",
                          latency_ms=int((time.time() - t0) * 1000), ok=False)
            return f"Brain error: {e}"

        engine_used = reply["engine"]
        model_used  = reply["model"]
        escalated   = escalated or reply.get("escalated_from")
        for k in usage_total:
            usage_total[k] += reply["usage"].get(k, 0)

        calls = reply["tool_calls"]

        # ── No tool calls → final answer ──
        if not calls:
            final_reply = (reply.get("content") or "").strip() or "..."
            conversation_history.append({"role": "assistant",
                                         "content": final_reply})
            break

        # ── Execute every requested tool, feed results back ──
        messages.append(_assistant_msg(engine_used, reply.get("content"), calls))

        for call in calls:
            name, args = call["name"], call["args"]
            log({"type": "tool", "name": name, "args": args})
            result = str(execute_tool(name, args))[:config.TOOL_RESULT_CHARS]
            log({"type": "result", "name": name, "result": result})
            messages.append(_tool_msg(engine_used, call, result))

    # ── Step limit reached — ask model to wrap up without tools ──
    if final_reply is None:
        try:
            messages.append({"role": "user",
                             "content": "Give your final answer now, without tools."})
            wrap = engines.chat_with_fallback(messages, tools=None,
                                              policy=policy, max_tokens=800)
            final_reply = (wrap.get("content") or "").strip() or \
                          "I ran out of steps before finishing that, sir."
        except engines.EngineError:
            final_reply = ("I ran out of steps before finishing that, sir. "
                           "Ask me again?")
        conversation_history.append({"role": "assistant", "content": final_reply})

    step({"type": "final", "text": final_reply})

    # ── Trace it (the learning loop) ──
    traces.record(
        preset=preset_name, engine=engine_used or "?", model=model_used or "?",
        user_input=user_input, steps=steps_log, final=final_reply,
        usage=usage_total, latency_ms=int((time.time() - t0) * 1000),
        ok=True, escalated=escalated,
        extra={"tool_count": sum(1 for s in steps_log if s["type"] == "tool")},
    )

    return final_reply


def clear_history():
    """Clears conversation history — fresh start."""
    conversation_history.clear()
    return "Memory cleared."
