# RS — Red Shirt AI Agent

> **A real AI agent for Windows. Not a chatbot.**
> RS controls your PC, speaks to you, listens for your voice, and acts autonomously — like Jarvis.

<br>

## What RS Actually Does

Most AI assistants just chat. RS acts.

When you say *"open VS Code and play some lofi"*, RS doesn't reply with *"Sure, I can do that!"* — it opens VS Code and starts playing lofi on YouTube. When your battery hits 12%, RS tells you without being asked. When you say *"remind me at 6pm to call Ahmed"*, RS speaks the reminder at exactly 6pm.

RS is a local Windows AI agent built in Python, powered by GPT-4o function calling, with a full hacker-themed desktop GUI.

<br>

## Features

### 🧠 Real AI Agent — 54 Tools
RS uses GPT-4o function calling. The AI reads your message, decides which tools to call, executes them, sees the results, and decides the next step — all automatically. No keyword matching.

### 👁️ Screen Vision
RS can take a screenshot and use AI to read and understand what's on your screen — error messages, open apps, UI elements. It can find and click buttons autonomously.

### 🎙️ Always-On Voice
Say **"Hey RS"** at any time — no clicking, no buttons. RS wakes up, listens for your command, executes it, and speaks the response back. Voice is always running in the background.

### 🔔 Proactive Alerts
RS monitors your PC in the background and tells you things without being asked:
- Battery low / fully charged
- CPU or RAM overloaded
- Internet went down / came back
- Morning briefing at 8 AM
- Custom reminders you set

### 🌐 Browser Automation
RS can open Chrome, navigate websites, read page content, click buttons, fill forms, send WhatsApp messages, and read Gmail — all through Playwright browser automation.

### 💾 Long-Term Memory
RS remembers every conversation. It tracks what topics you ask about most, learns from feedback you give it, and uses past interactions to personalize future responses.

### 🖥️ Hacker OS Interface
Full desktop GUI with matrix rain animation, rotating 3D neural core, live step-by-step display as RS works, real-time system stats, task manager, memory browser, and settings panel.

<br>

## Project Structure

```
RS/
├── config.py           — Identity, paths, API keys, settings
├── memory.py           — Long-term memory, logs, feedback, patterns
├── brain.py            — AI agent core with 54 function-calling tools
├── voice.py            — TTS (speak) + STT (listen) + wake word
├── proactive.py        — Background monitor & proactive alerts
│
├── app_controller.py   — Open/close apps, Spotify, Discord, volume
├── skills.py           — File management, web, email, system info
├── computer_use.py     — Mouse, keyboard, screenshot, screen control
├── mouse_keyboard.py   — Human-like input simulation
├── browser_agent.py    — Chrome automation via Playwright
├── vision.py           — Screen vision via GPT-4o
├── media_player.py     — YouTube, Spotify, VLC, media keys
├── downloader.py       — yt-dlp video/audio downloader
│
├── server.py           — Flask API server (all requests go here)
├── boot_tasks.py       — Scheduled tasks, boot routines
├── startup.py          — Register RS to auto-start on Windows boot
├── tray.py             — System tray icon
├── tunnel.py           — Cloudflare/ngrok tunnel for mobile access
│
├── gui2.py             — Hacker OS desktop GUI (CustomTkinter)
├── main.py             — CLI entry point
├── launch.py           — Silent master launcher (no terminal)
├── RS.vbs              — Windows entry point (double-click to start)
│
├── app/
│   ├── index.html      — Electron web dashboard
│   ├── style.css       — Hacker theme styles
│   ├── renderer.js     — Dashboard JavaScript logic
│   └── mobile.html     — Mobile control page
│
├── main.js             — Electron shell
├── memory_store/       — JSON memory files (auto-created)
├── logs/               — Activity logs (auto-created)
├── downloads/          — Downloaded files (auto-created)
└── .env                — API keys (you create this)
```

<br>

## Requirements

### Python
```
Python 3.11 or higher
```

### Install all packages
```bash
pip install customtkinter flask flask-cors psutil pyautogui
pip install pygame pyngrok pynput pystray requests schedule
pip install SpeechRecognition pillow python-dotenv yt-dlp
pip install playwright && playwright install chromium
```

### Node.js (optional — only for Electron desktop shell)
```
Node.js 18+
npm install
```

<br>

## Setup

### 1. Create your `.env` file
Create a file called `.env` in the RS project folder:

```env
OPENROUTER_API_KEY=your_openrouter_key_here
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
NGROK_TOKEN=your_ngrok_token_here
```

**Getting your keys:**
- `OPENROUTER_API_KEY` → Sign up free at [openrouter.ai](https://openrouter.ai) → API Keys
- `EMAIL_PASSWORD` → Gmail → Google Account → Security → 2-Step Verification → App Passwords → Generate
- `NGROK_TOKEN` → Sign up free at [ngrok.com](https://ngrok.com) → Your Authtoken (optional — only needed for mobile access)

### 2. Test the installation
```bash
python server.py
```
Open `http://localhost:5000/ping` in your browser. You should see `{"status": "online"}`.

### 3. Launch RS
```bash
# Option A — Full GUI launch
python gui2.py

# Option B — CLI only (no GUI)
python main.py

# Option C — Server only (for mobile/API use)
python server.py
```

<br>

## Auto-Start on Windows Boot

Run this once to install RS as a Windows startup app:

```bash
python startup.py
# Choose option 1 → INSTALL
```

From now on RS starts silently in the background every time you turn on your PC. No terminal window. No popup. Just a green icon in your system tray.

To start RS manually without rebooting: **double-click `RS.vbs`**

<br>

## How to Use RS

### Text — type in the GUI
Just type anything naturally. RS understands intent, not keywords.

```
You:  open chrome and search for Python tutorials
RS:   [opens Chrome] [searches Google]
      Done sir. Chrome is open with Python tutorials.

You:  what's my battery and RAM?
RS:   [checks battery] [checks RAM]
      Battery: 78% on battery power.
      RAM: 62% used (9.9GB of 16GB).

You:  remind me in 30 minutes to take a break
RS:   [sets reminder]
      I'll remind you in 30 minutes, sir.

You:  send a WhatsApp to Ahmed saying I'll be 10 minutes late
RS:   [opens WhatsApp Web] [finds Ahmed] [sends message]
      WhatsApp message sent to Ahmed, sir.

You:  download shape of you as mp3
RS:   [calls yt-dlp] 
      Downloaded: downloads/audio/Shape of You - Ed Sheeran.mp3
```

### Voice — say "Hey RS"
Say **"Hey RS"** out loud. RS wakes up and listens. Then say your command naturally. RS acts and speaks back.

Click **[MIC]** in the GUI to activate voice mode.

### Tray Icon
Right-click the green tray icon in your taskbar for quick actions:
- 🖥️ Open RS — restore the GUI
- ⚡ Quick: Time
- 🌐 Quick: Open Browser
- 🔄 Restart Server
- ❌ Quit RS

<br>

## All 54 Agent Tools

RS's brain can call any of these tools automatically based on what you ask:

| Category | Tools |
|---|---|
| **System Info** | get_time, get_date, get_system_info, get_battery, get_cpu_usage, get_ram_usage, check_internet, get_ip_address |
| **App Control** | open_app, close_app, open_website, search_web |
| **Volume** | volume_up, volume_down, mute_volume, set_volume |
| **Media** | play_youtube, open_spotify, media_play_pause, media_next, media_previous, download_youtube_audio |
| **Files** | create_file, read_file, delete_file, list_files, create_folder, open_file, open_folder |
| **Email** | send_email |
| **PC Control** | take_screenshot, lock_pc, shutdown_pc, restart_pc, sleep_pc, show_notification |
| **Clipboard** | copy_to_clipboard, get_clipboard |
| **Vision** | analyze_screen, find_and_click, do_task_on_screen |
| **Browser** | browser_go_to, browser_search_google, send_whatsapp, read_whatsapp, read_emails, browser_task |
| **Scheduling** | schedule_task, list_scheduled_tasks |
| **Reminders** | remind_in_minutes, remind_at_time |
| **Memory** | get_recent_memories, get_evolution_stats, get_monitor_status |

<br>

## Proactive Alerts

RS monitors your PC every 30 seconds and will alert you (voice + GUI bubble) when:

| Condition | Alert |
|---|---|
| Battery ≤ 10% | "Sir, battery is critically low at X%." |
| Battery ≤ 20% | "Sir, battery is at X%. You may want to charge." |
| Battery = 100% | "Battery fully charged, sir." |
| CPU > 90% | "Sir, CPU usage is very high at X%." |
| RAM > 90% | "Sir, RAM is at X%. Close some applications." |
| Disk C: > 90% | "Sir, C: drive is X% full." |
| Internet down | "Sir, internet connection appears to be down." |
| 8:00 AM | Morning briefing |
| Your reminders | Spoken at the exact time you set |

<br>

## GUI Overview

```
┌─────────────────────────────────────────────────────────────┐
│  [RS]  RED SHIRT HACKER OS    [TERMINAL][TASKS][MEMORY][CONFIG]  00:00:00 │
├──────────────┬───────────────────────────────┬──────────────┤
│              │                               │  TELEMETRY   │
│  NEURAL CORE │   MATRIX RAIN BACKGROUND     │  Uptime      │
│  [3D Cube]   │                               │  Tasks Done  │
│              │   CHAT MESSAGES               │  Memories    │
│  CPU  ████░  │   [ RS ] >> Good morning sir │  Storage     │
│  MEM  ██░░░  │   [ YOU ] open chrome        │              │
│  NET  ███░░  │   [ RS ] ⚙ open_app(chrome)  │  ACTIVITY    │
│              │          ✓ Opened chrome      │  TOP TOPICS  │
│  ACTIVITY    │          Done sir.            │              │
│  LOG         │                               │  FEEDBACK    │
│              │  ──────────────────────────── │  SCORE       │
│  MODULES     │  TEXT MODE > [input box] SEND │              │
└──────────────┴───────────────────────────────┴──────────────┘
│ SYS LOG  >> NEURAL CORE ACTIVE | RS v3.0 RUNNING | ...        00:00:00 │
└─────────────────────────────────────────────────────────────┘
```

<br>

## Architecture — How It Works

```
User speaks or types
        ↓
voice.py (wake word) OR gui2.py (text input)
        ↓
server.py /chat endpoint
        ↓
brain.py — sends to GPT-4o with 54 tool definitions
        ↓
GPT-4o decides which tool(s) to call
        ↓
brain.py executes tool → result sent back to GPT-4o
        ↓
GPT-4o sees result, decides next step
        ↓  (repeats up to 5 times)
GPT-4o gives final response
        ↓
voice.py speaks response
gui2.py shows response + step log
memory.py saves the interaction
```

Meanwhile, in the background:
```
proactive.py → monitors battery/CPU/RAM/disk/internet every 30s
boot_tasks.py → runs scheduled tasks (daily briefing, reminders)
voice.py → always listening for "Hey RS"
tray.py → green icon in system tray
```

<br>

## Memory & Evolution

RS stores every conversation in `memory_store/experiences.json`. Over time it:
- Tracks which topics you ask about most (patterns)
- Uses recent conversations to personalize responses
- Learns from feedback you give (good/ok/bad ratings)
- Calculates a version number that grows with experience

Every 10 conversations = minor version bump.
Every 5 good feedback ratings = patch bump.

<br>

## Mobile Access

To control RS from your phone:

```bash
python tunnel.py
# Choose option 1 → Start tunnel
```

RS will print a public URL like `https://abc123.ngrok.io`. Open `https://abc123.ngrok.io/mobile` on your phone — full mobile control panel, works from anywhere in the world.

<br>

## Troubleshooting

**RS doesn't speak (no voice)**
- Make sure `VOICE_ENABLED = True` in `config.py`
- PowerShell must be allowed: run `Set-ExecutionPolicy RemoteSigned` in PowerShell as admin

**Wake word not working**
```bash
pip install SpeechRecognition pyaudio
```
Also check that your microphone is set as the default recording device in Windows Sound settings.

**OpenRouter API errors**
- Check your `OPENROUTER_API_KEY` in `.env`
- Model `openai/gpt-4o` requires credits — use `mistralai/mistral-7b-instruct` for free tier (change `MODEL` in `brain.py`)

**Browser automation not working**
```bash
playwright install chromium
```

**GUI doesn't open**
```bash
pip install customtkinter
```

**Email sending fails**
- Use a Gmail App Password, not your regular Gmail password
- Gmail → Account → Security → 2-Step Verification → App Passwords

<br>

## Configuration

Edit `config.py` to customize RS:

```python
ASSISTANT_NAME    = "RS"          # Change RS's name
VOICE_ENABLED     = True          # Turn voice on/off
MEMORY_ENABLED    = True          # Turn memory on/off
MAX_MEMORY_ENTRIES = 365          # How many memories to keep
```

Edit `brain.py` to change the AI model:
```python
MODEL = "openai/gpt-4o"                    # Best, costs credits
MODEL = "mistralai/mistral-7b-instruct"    # Free tier
MODEL = "anthropic/claude-3-haiku"         # Fast and affordable
```

<br>

## Project Info

| | |
|---|---|
| **Name** | RS — Red Shirt AI Agent |
| **Version** | 3.0 |
| **Creator** | MR NOTE |
| **Platform** | Windows 10/11 |
| **Python** | 3.11+ |
| **AI Model** | GPT-4o via OpenRouter |
| **GUI** | CustomTkinter (hacker theme) |
| **Voice** | Windows Speech Synthesis + Google STT |
| **Browser** | Playwright + Chromium |
| **GitHub** | [ahmed-abdullah-06](https://github.com/ahmed-abdullah-06) |

<br>

---

*RS is a personal AI agent project. It is not affiliated with any company. The browser automation features are for personal use only.*