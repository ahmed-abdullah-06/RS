# RS — Red Shirt AI Agent

> **A local-first AI agent for Windows. Not a chatbot.**
> RS runs on **your machine** by default (Ollama), reaches for the cloud only when it must,
> controls your PC, speaks to you, watches your system, and learns from every run — like Jarvis.

<br>

## What RS Actually Does

Most AI assistants just chat. RS acts.

When you say *"open VS Code and play some lofi"*, RS doesn't reply with *"Sure, I can do that!"* —
it opens VS Code and starts playing lofi on YouTube. When your battery hits 12%, RS tells you
without being asked. When you say *"remind me at 6pm to call Ahmed"*, RS speaks the reminder at
exactly 6pm.

Everything runs through one agent loop: RS reads your message, **decides which of its tools to
call**, executes them, reads the results, and decides the next step — up to 5 rounds per request.
No keyword matching in the agent path.

<br>

## ✨ OpenJarvis-Style Architecture

RS borrows its architecture from Stanford's OpenJarvis: personal AI that lives on the device.

| Capability | What RS does |
|---|---|
| **🧠 Local-first routing** | Ollama (`llama3.2:3b`) answers first, GPT-4o only escalates. Auto-revives the Ollama daemon if it dies — never fails over to paid cloud just because the local server went to sleep. |
| **🤖 Preset agents** | 7 presets (`chat`, `simple`, `code_assistant`, `deep_research`, `morning_digest`, `monitor`, `screen`), each with its own tool belt, system prompt, engine policy and step budget. |
| **🧩 Skills marketplace** | Install skills from `github:owner/repo`, a git/zip URL or a local folder. Every installed skill registers **real tools** in the brain. 3 seeds ship with RS. |
| **💻 Code execution** | Sandboxed Python/shell runner + workspace with its own `code_assistant` preset. |
| **🔬 Deep research** | Multi-step research runner with citations and scraped sources. |
| **☀ Morning digest** | Daily briefing (weather, system, mail, headlines, reminders) at `BRIEFING_HOUR`. |
| **◉ Monitor agent** | Background watcher that snapshots CPU/RAM/disk/net on an interval and keeps compressed long-term memory of trends. |
| **📈 Trace-based learning** | Every run is traced (engine, latency, tokens, tools, cost). `GET /traces?learn=1` runs a learning pass and reports what works and what to fix. |
| **⌨️ `rs` CLI** | `rs chat`, `rs ask`, `rs research`, `rs skill install …`, `rs doctor`, `rs serve` and more. |

<br>

## 🚀 Quick Start

### 1. Install Ollama (the free local brain)
```powershell
winget install Ollama.Ollama
ollama pull llama3.2:3b
```
> RS works without Ollama (it falls back to cloud), but local-first is the whole point.
> If the Ollama app isn't running, **RS starts it for you** — see `engines.py`.

### 2. Install Python packages
```bash
pip install -r requirement.txt
playwright install chromium
```

### 3. Create your `.env` (never hardcode secrets)
```env
OPENROUTER_API_KEY=your_openrouter_key_here
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
NGROK_TOKEN=your_ngrok_token_here
```
- `OPENROUTER_API_KEY` → free at [openrouter.ai](https://openrouter.ai) → API Keys (cloud fallback)
- `EMAIL_PASSWORD` → Gmail → Security → 2-Step Verification → **App Passwords**
- `NGROK_TOKEN` → only needed for mobile access

### 4. Launch
```bash
# A — JARVIS HUD (browser) — start the server, then open /hud
python rs.py serve            # → http://localhost:5000/hud

# B — Desktop window (pywebview shell around the HUD)
python gui2.py                # or: double-click RS.vbs

# C — Terminal chat
python rs.py chat

# D — One-shot
python rs.py ask "what's my RAM usage?"
```

<br>

## 🖥️ The JARVIS HUD

`http://localhost:5000/hud` — an ice-blue holographic interface: arc-reactor core, live
telemetry, agent activity feed, alerts, voice/wake toggles.

- **Header preset selector** — switch the active agent (`chat` → `screen` → `code_assistant` …)
  and every message you send routes through it.
- **⬡ LAB drawer** — three tabs:
  - **SKILLS** — installed skills, install from URL/GitHub/folder, sync, remove
  - **LEARNING** — trace stats (runs, latency, tokens, cost, per-engine/per-preset) + *RUN LEARNING PASS*
  - **SYSTEM** — engine doctor, build digest, start/stop the monitor agent

<br>

## 🤖 The 7 Presets

| Preset | Tools | Policy | What it's for |
|---|---|---|---|
| `chat` | dynamic default belt | local_first | Everyday conversation + actions |
| `simple` | none | local | Fast, fully offline replies (no tool calls) |
| `code_assistant` | 10 code tools | local_first | Run/inspect code in the workspace |
| `deep_research` | research runner | local_first | Multi-source research with citations |
| `morning_digest` | digest runner | local | The daily briefing |
| `monitor` | 8 monitor tools | local | Trend reporting from monitor memory |
| `screen` | 8 vision/browser tools | local_first | Look at the screen, click, type, drive the browser |

User presets saved with `rs init` override the built-ins.

<br>

## 🧰 Tool Belts — why RS doesn't show all 72 tools at once

Measured on a CPU-only laptop: the **full 72-tool schema needs ~4423 tokens**. Ollama silently
cuts anything that doesn't fit `num_ctx`, so a too-large schema gets truncated mid-JSON and the
model starts **hallucinating tool names**. And every tool costs ~50 tokens of prefill on *every*
step.

So the brain carries belts (`brain.py`):

| Belt | Tools | Prompt size | Used by |
|---|---|---|---|
| Default (`CHAT_TOOLS` + installed skills) | ~34+ | ~2450 tokens | `chat`, plain `brain.think()` |
| `SCREEN_TOOLS` | 8 | — | `screen` preset |
| `CODE_TOOLS` | 10 | — | `code_assistant` |
| Tool-free | 0 | ~700 tokens | `simple` |

Heavy/dangerous tools (`shutdown_pc`, `delete_file`, autonomous mouse/keyboard) live in their
own presets — a trivial *"open notepad"* can never hijack the autonomous screen-driving mode.

**All 72 tools by category:**

| Category | Tools |
|---|---|
| **System Info** | get_time, get_date, get_system_info, get_battery, get_cpu_usage, get_ram_usage, check_internet, get_ip_address |
| **App Control** | open_app, close_app, open_website, search_web |
| **Volume** | volume_up, volume_down, mute_volume, set_volume |
| **Media** | play_youtube, open_spotify, media_play_pause, media_next, media_previous, download_youtube_audio |
| **Files** | create_file, read_file, delete_file, list_files, create_folder, open_file, open_folder |
| **Email** | send_email, read_emails |
| **PC Control** | take_screenshot, lock_pc, shutdown_pc, restart_pc, sleep_pc, show_notification |
| **Clipboard** | copy_to_clipboard, get_clipboard |
| **Vision / Screen** | analyze_screen, find_and_click, do_task_on_screen |
| **Browser** | browser_go_to, browser_search_google, browser_task |
| **Reminders** | remind_in_minutes, remind_at_time |
| **Code** | run_python, run_python_file, run_shell, workspace_write, workspace_read, workspace_list |
| **Memory / Monitor** | get_recent_memories, get_evolution_stats, get_monitor_status, monitor_cycle, monitor_search |
| **Skills** | system_report, top_processes, git_status, git_log, git_diff, text_stats, text_transform, text_replace |

<br>

## ⚙️ Engines — local-first routing

```python
engines.py:
   OllamaEngine  (local, private, free, offline)   ← primary
        │  unavailable / failed
        ▼
   OpenRouterEngine (GPT-4o)                       ← fallback only
```

| Env var | Default | Meaning |
|---|---|---|
| `RS_ENGINE_POLICY` | `local_first` | `local_first` \| `local` \| `cloud` |
| `RS_LOCAL_MODEL` | `llama3.2:3b` | Ollama model name |
| `RS_OLLAMA_URL` | `http://localhost:11434` | Ollama API |
| `RS_LOCAL_NUM_CTX` | `6144` | Context — **must fit the tool schema** (full 72 = ~4423 tok) |
| `RS_LOCAL_MAX_TOKENS` | `384` | Generation cap per step (CPU is slow) |
| `RS_TOOL_RESULT_CHARS` | `1600` | Tool output truncation (latency knob) |
| `RS_MONITOR_ENABLED` / `RS_MONITOR_INTERVAL` | `1` / `300` | Background monitor agent |
| `PORT` | `5000` | Web server |

**Model notes (measured, CPU-only i5):**
- `llama3.2:3b` — the default. Only model that reliably picks correct tools *and* tells the truth
  (~14–45s per agent turn on CPU).
- `qwen2.5:0.5b/1.5b`, `llama3.2:1b` — faster but fabricate facts or leak raw schema JSON.
- `qwen3:4b` — accurate but 100s+ per turn on CPU.

<br>

## 🧩 Skills Marketplace

```bash
# CLI
rs skill list
rs skill install github:owner/repo
rs skill install https://github.com/owner/repo/archive/refs/heads/main.zip
rs skill install D:\path\to\skill-folder
rs skill sync          # re-register tools after editing a skill
rs skill uninstall system_reporter
```

Seeds shipped with RS: `system_reporter`, `text_tools`, `git_helper`.
Installed skills are advertised in the system prompt **and** added to the default tool belt
(recomputed per call — install a skill while the server runs and it's usable immediately).

<br>

## 📈 Trace-Based Learning Loop

Every agent run writes a trace: engine, model, latency, tokens, tools used, success, preset.

```bash
rs traces              # stats
rs traces --learn      # learning pass → improvement notes
curl http://localhost:5000/traces?learn=1
```

The HUD **LEARNING** tab shows the same data: runs, success %, local vs cloud split, p95 latency,
per-tool call counts, cost.

<br>

## ⏰ Background Agents

```bash
rs monitor start --interval 300     # or POST /monitor {"action":"start"}
rs monitor status                   # or GET  /monitor
rs digest                           # or POST /digest {"speak":false}
```
> `rs monitor status` reports **this process's** state — when the server owns the agent,
> ask the server: `GET /monitor` (the HUD SYSTEM tab does this for you).

On `rs serve` boot both are armed automatically:
```
  ◉ monitor agent: every 300s
  ⏰ digest scheduler: armed
```

<br>

## ⌨️ `rs` CLI Reference

```
rs chat                 interactive chat (default)
rs ask "question"       one-shot question
rs research "topic"     deep research with citations
rs digest               build the morning briefing
rs agents               list preset agents
rs init                 save a preset for tuning
rs doctor               health check (engines, ffmpeg, disk, skills)
rs traces [--learn]     trace stats / learning loop
rs skill list|install|uninstall|sync|add
rs monitor start|stop|status
rs gui                  open the JARVIS HUD desktop window
rs serve                start the web server
```

<br>

## 🌐 HTTP API

| Route | Method | Purpose |
|---|---|---|
| `/hud` · `/mobile` · `/dashboard` | GET | Front-ends |
| `/chat` | POST | Chat — `{"message","source","preset"}` |
| `/agent/run` | POST | Run a preset directly |
| `/agents` | GET | Preset list |
| `/skills` | GET/POST | List / install / uninstall / sync |
| `/traces` · `/traces?learn=1` | GET | Trace stats / learning pass |
| `/doctor` | GET | Engine + system health |
| `/monitor` | GET/POST | Monitor agent status / start / stop |
| `/digest` | POST | Build the morning briefing |
| `/ping` · `/stats` · `/telemetry` · `/alerts` | GET | Health, counters, live gauges, alert feed |
| `/steps?since=0` | GET | Live agent step feed |

<br>

## 📁 Project Structure

```
RS/
├── config.py           — Identity, paths, settings, env knobs
├── memory.py           — Long-term memory, logs, feedback, patterns
├── brain.py            — Agent loop, 72 tools, tool belts, system prompt
├── agents.py           — 7 preset agents (belt, policy, prompt, runner)
├── engines.py          — local-first router: Ollama → GPT-4o (self-healing)
├── voice.py            — TTS (speak) + STT (listen) + wake word
├── proactive.py        — Background alerts & reminders
│
├── app_controller.py   — Open/close apps, Spotify, Discord, volume
├── skills.py           — File management, web, email, system info
├── computer_use.py     — Mouse, keyboard, screenshot, screen control
├── mouse_keyboard.py   — Human-like input simulation
├── browser_agent.py    — Chrome automation via Playwright
├── vision.py           — Screen vision
├── media_player.py     — YouTube, Spotify, VLC, media keys
├── downloader.py       — yt-dlp video/audio downloader
│
├── code_runner.py      — Sandboxed Python/shell execution + workspace
├── research.py         — Deep research runner (sources + citations)
├── digest.py           — Morning briefing builder
├── monitor.py          — Continuous monitoring agent (long-term memory)
├── traces.py           — Run traces + learning pass
├── skills_catalog.py   — Skills marketplace (install → tools)
│
├── server.py           — Flask API server (all requests go here)
├── rs.py               — CLI entry point
├── boot_tasks.py       — Scheduled tasks, boot routines
├── startup.py          — Register RS to auto-start on Windows boot
├── tray.py             — System tray icon
├── tunnel.py           — Cloudflare/ngrok tunnel for mobile access
│
├── gui2.py             — JARVIS HUD desktop shell (pywebview)
├── main.py             — Legacy CLI entry point
├── launch.py           — Silent master launcher (no terminal)
├── RS.vbs              — Windows entry point (double-click to start)
│
├── app/                — HUD (hud.html/css/js), mobile, dashboard
├── skills_seed/        — Bundled skills (system_reporter, text_tools, git_helper)
├── skills_store/       — Installed skills (auto-created)
├── workspace/          — code_assistant sandbox (auto-created)
├── memory_store/       — JSON memory files (auto-created)
├── logs/ · digests/ · downloads/ · screenshots/   (auto-created)
└── .env                — API keys (you create this)
```

<br>

## 🔧 Troubleshooting

**Local model unavailable / Ollama not running**
- RS auto-starts it (`engines.py` → `_start_server()`, rate-limited to once per minute).
- Manual: `ollama serve` or launch the Ollama app. Then `rs doctor`.

**Local replies are slow**
- CPU-only inference ≈ 15–45s per agent turn with a tool round. That's the trade for free/private.
- Speed knobs: `RS_LOCAL_MAX_TOKENS`, `RS_TOOL_RESULT_CHARS`, fewer tools in `brain.CHAT_TOOLS`.
- Do **not** lower `RS_LOCAL_NUM_CTX` below the schema size — Ollama truncates silently and the
  model starts inventing tools.

**MP3 downloads fail**
- `winget install Gyan.FFmpeg` (yt-dlp needs FFmpeg on PATH).

**Wake word / microphone not working**
```bash
pip install SpeechRecognition pyaudio
```
Set the mic as the default recording device in Windows Sound settings.

**Email sending fails**
- Use a Gmail **App Password**, never your real password. Keep it in `.env` only.

**Browser automation not working**
```bash
playwright install chromium
```

**Cloud escalation errors**
- `OPENROUTER_API_KEY` in `.env`, and GPT-4o needs credits. Local-first means RS still works.

<br>

## 📋 Configuration

Edit `config.py` (or set env vars) to customize RS:

```python
ASSISTANT_NAME     = "RS"        # Change RS's name
VOICE_ENABLED      = True        # Turn voice on/off
MEMORY_ENABLED     = True        # Turn memory on/off
ENGINE_POLICY      = "local_first"
LOCAL_MODEL        = "llama3.2:3b"
BRIEFING_HOUR      = 8           # morning digest at 08:00
MAX_AGENT_STEPS    = 5           # tool rounds per request
```

<br>

## 📌 Project Info

| | |
|---|---|
| **Name** | RS — Red Shirt AI Agent |
| **Version** | 3.0 |
| **Creator** | MR NOTE |
| **Platform** | Windows 10/11 |
| **Python** | 3.11+ (tested on 3.13) |
| **Primary AI** | `llama3.2:3b` via Ollama (local, free) |
| **Fallback AI** | GPT-4o via OpenRouter |
| **Interface** | JARVIS HUD (web) + pywebview desktop shell + `rs` CLI |
| **Browser** | Playwright + Chromium |
| **GitHub** | [ahmed-abdullah-06](https://github.com/ahmed-abdullah-06) |

<br>

---

*RS is a personal AI agent project. It is not affiliated with any company. The browser automation features are for personal use only.*
