# ============================================================
#  R.S. - Red Shirt AI Assistant
#  app_controller.py — Desktop app controller
#  RS opens and controls any app on your PC
# ============================================================

import subprocess
import os
import time
import psutil
import pyautogui
from mouse_keyboard import human_click, human_type, human_hotkey, human_press
from computer_use  import take_screenshot, search_and_open

# ── Common app paths (Windows) ────────────────────────────────
APP_PATHS = {
    # Browsers
    "chrome"        : r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox"       : r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge"          : r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    # Communication
    "discord"       : os.path.join(os.environ.get("LOCALAPPDATA",""),
                        r"Discord\app-*\Discord.exe"),
    "telegram"      : os.path.join(os.environ.get("APPDATA",""),
                        r"Telegram Desktop\Telegram.exe"),
    "whatsapp"      : os.path.join(os.environ.get("LOCALAPPDATA",""),
                        r"WhatsApp\WhatsApp.exe"),
    "slack"         : os.path.join(os.environ.get("LOCALAPPDATA",""),
                        r"slack\slack.exe"),
    "zoom"          : os.path.join(os.environ.get("APPDATA",""),
                        r"Zoom\bin\Zoom.exe"),
    "teams"         : os.path.join(os.environ.get("LOCALAPPDATA",""),
                        r"Microsoft\Teams\current\Teams.exe"),

    # Media
    "spotify"       : os.path.join(os.environ.get("APPDATA",""),
                        r"Spotify\Spotify.exe"),
    "vlc"           : r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "itunes"        : r"C:\Program Files\iTunes\iTunes.exe",

    # Productivity
    "notepad"       : r"C:\Windows\notepad.exe",
    "wordpad"       : r"C:\Program Files\Windows NT\Accessories\wordpad.exe",
    "calculator"    : r"C:\Windows\System32\calc.exe",
    "paint"         : r"C:\Windows\System32\mspaint.exe",
    "word"          : r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel"         : r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint"    : r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",

    # Dev tools
    "vscode"        : os.path.join(os.environ.get("LOCALAPPDATA",""),
                        r"Programs\Microsoft VS Code\Code.exe"),
    "cmd"           : r"C:\Windows\System32\cmd.exe",
    "powershell"    : r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",

    # System
    "explorer"      : r"C:\Windows\explorer.exe",
    "taskmanager"   : r"C:\Windows\System32\Taskmgr.exe",
    "controlpanel"  : "control",
    "settings"      : "ms-settings:",
}


# ============================================================
#  PART 1 — OPEN ANY APP
# ============================================================

def open_app(app_name):
    """
    Opens any app by name.
    Tries known paths first, then uses Windows search.

    Examples:
        open_app("chrome")
        open_app("spotify")
        open_app("discord")
        open_app("notepad")
    """
    app_name_lower = app_name.lower().strip()

    print(f"🚀 Opening: {app_name}")

    # Method 1 — Try known path
    if app_name_lower in APP_PATHS:
        path = APP_PATHS[app_name_lower]

        # Handle wildcard paths (like Discord)
        if '*' in path:
            import glob
            matches = glob.glob(path)
            if matches:
                path = matches[-1]  # Use latest version

        try:
            if os.path.exists(path):
                subprocess.Popen([path])
                time.sleep(2)
                print(f"✅ Opened {app_name} from path")
                return True
        except:
            pass

        # Handle special commands (settings, control panel)
        try:
            os.startfile(path)
            time.sleep(2)
            print(f"✅ Opened {app_name} via startfile")
            return True
        except:
            pass

    # Method 2 — Use Windows search
    print(f"   Trying Windows search for {app_name}...")
    result = search_and_open(app_name)
    time.sleep(2)
    return result


def open_app_with_file(app_name, file_path):
    """Opens an app with a specific file"""
    try:
        if app_name.lower() in APP_PATHS:
            path = APP_PATHS[app_name.lower()]
            subprocess.Popen([path, file_path])
        else:
            os.startfile(file_path)
        time.sleep(2)
        print(f"✅ Opened {file_path} with {app_name}")
        return True
    except Exception as e:
        print(f"❌ Open with file error: {e}")
        return False


# ============================================================
#  PART 2 — CLOSE APPS
# ============================================================

def close_app(app_name):
    """
    Closes an app by name.
    Finds the running process and kills it.
    """
    try:
        app_name_lower = app_name.lower()

        # Process name mapping
        process_names = {
            "chrome"    : "chrome.exe",
            "firefox"   : "firefox.exe",
            "edge"      : "msedge.exe",
            "discord"   : "Discord.exe",
            "telegram"  : "Telegram.exe",
            "spotify"   : "Spotify.exe",
            "notepad"   : "notepad.exe",
            "vlc"       : "vlc.exe",
            "vscode"    : "Code.exe",
            "whatsapp"  : "WhatsApp.exe",
            "zoom"      : "Zoom.exe",
            "teams"     : "Teams.exe",
        }

        proc_name = process_names.get(app_name_lower, app_name)

        killed = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and \
               app_name_lower in proc.info['name'].lower():
                proc.kill()
                killed = True

        if killed:
            print(f"✅ Closed {app_name}")
        else:
            print(f"⚠️  {app_name} was not running")

        return killed

    except Exception as e:
        print(f"❌ Close app error: {e}")
        return False


def is_app_running(app_name):
    """Checks if an app is currently running"""
    app_name_lower = app_name.lower()
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and \
           app_name_lower in proc.info['name'].lower():
            return True
    return False


# ============================================================
#  PART 3 — BRING APP TO FRONT
# ============================================================

def focus_app(app_name):
    """
    Brings an app window to the front.
    Uses Alt+Tab style window switching.
    """
    try:
        import subprocess
        script = f'''
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinAPI {{
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
}}
"@
$proc = Get-Process | Where-Object {{$_.MainWindowTitle -like "*{app_name}*"}} | Select-Object -First 1
if ($proc) {{ [WinAPI]::SetForegroundWindow($proc.MainWindowHandle) }}
'''
        subprocess.run(['powershell', '-command', script], capture_output=True)
        time.sleep(0.5)
        print(f"✅ Focused: {app_name}")
        return True
    except Exception as e:
        print(f"❌ Focus error: {e}")
        return False


def get_running_apps():
    """Returns list of all currently running apps with windows"""
    apps = []
    for proc in psutil.process_iter(['name', 'pid', 'status']):
        try:
            if proc.info['status'] == 'running':
                apps.append({
                    'name': proc.info['name'],
                    'pid' : proc.info['pid']
                })
        except:
            pass
    return apps


# ============================================================
#  PART 4 — SPOTIFY CONTROL
# ============================================================

def spotify_play_pause():
    """Play or pause Spotify"""
    if not is_app_running("Spotify"):
        open_app("spotify")
        time.sleep(4)
    focus_app("Spotify")
    time.sleep(0.5)
    pyautogui.hotkey('space')
    print("🎵 Spotify play/pause toggled")


def spotify_next():
    """Skip to next track"""
    focus_app("Spotify")
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'right')
    print("⏭️  Spotify next track")


def spotify_previous():
    """Go to previous track"""
    focus_app("Spotify")
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'left')
    print("⏮️  Spotify previous track")


def spotify_volume_up():
    """Increase Spotify volume"""
    focus_app("Spotify")
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'up')
    print("🔊 Spotify volume up")


def spotify_volume_down():
    """Decrease Spotify volume"""
    focus_app("Spotify")
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'down')
    print("🔉 Spotify volume down")


def spotify_search_play(song_name):
    """Opens Spotify and searches for a song"""
    try:
        if not is_app_running("Spotify"):
            open_app("spotify")
            time.sleep(4)

        focus_app("Spotify")
        time.sleep(1)

        # Open search with Ctrl+L
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.8)

        # Type song name
        human_type(song_name, speed='fast')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(2)

        print(f"🎵 Spotify searching: {song_name}")
        return True
    except Exception as e:
        print(f"❌ Spotify search error: {e}")
        return False


# ============================================================
#  PART 5 — DISCORD CONTROL
# ============================================================

def discord_send_message(server=None, channel=None, message=None):
    """
    Sends a message in Discord.
    If server/channel given, navigates there first.
    """
    try:
        if not is_app_running("Discord"):
            open_app("discord")
            time.sleep(5)

        focus_app("Discord")
        time.sleep(1)

        # Use Ctrl+K to quick-switch channel
        if channel:
            pyautogui.hotkey('ctrl', 'k')
            time.sleep(0.8)
            human_type(channel, speed='fast')
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(0.5)

        # Type and send message
        if message:
            # Click message box
            pyautogui.hotkey('alt', 'shift', 'down')
            time.sleep(0.3)
            human_type(message, speed='normal')
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(0.5)

        print(f"✅ Discord message sent: {message[:30] if message else ''}")
        return True

    except Exception as e:
        print(f"❌ Discord error: {e}")
        return False


# ============================================================
#  PART 6 — VOLUME & SYSTEM CONTROLS
# ============================================================

def set_volume(level):
    """
    Sets system volume (0-100).
    Uses Windows PowerShell.
    """
    try:
        script = f"""
$obj = New-Object -ComObject WScript.Shell
$current = [int]([Math]::Round((([math]::Round(([System.Math]::Log(100/{level}+1)/[System.Math]::Log(1.1)),0))*(-1)+65535)*100/65535))
"""
        # Simpler approach — use nircmd if available, else use key presses
        # Set volume using audio endpoint
        ps_script = f"""
$vol = {level / 100}
$obj = New-Object -ComObject WScript.Shell
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {{
    int f(); int g(); int h(); int i();
    int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
    int j();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int k(); int l(); int m(); int n();
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, System.Guid pguidEventContext);
    int GetMute(out bool pbMute);
}}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {{
    int Activate(ref System.Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
}}
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {{
    int f();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
}}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject {{ }}
public class Audio {{
    static IAudioEndpointVolume Vol() {{
        var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
        IMMDevice dev = null;
        Marshal.ThrowExceptionForHR(enumerator.GetDefaultAudioEndpoint(0, 1, out dev));
        IAudioEndpointVolume epv = null;
        var epvid = typeof(IAudioEndpointVolume).GUID;
        Marshal.ThrowExceptionForHR(dev.Activate(ref epvid, 23, 0, out epv));
        return epv;
    }}
    public static float Volume {{
        get {{ float v = -1; Marshal.ThrowExceptionForHR(Vol().GetMasterVolumeLevelScalar(out v)); return v; }}
        set {{ Marshal.ThrowExceptionForHR(Vol().SetMasterVolumeLevelScalar(value, System.Guid.Empty)); }}
    }}
}}
'@
[Audio]::Volume = {level/100}
"""
        subprocess.run(
            ['powershell', '-command', ps_script],
            capture_output=True, timeout=5
        )
        print(f"🔊 Volume set to {level}%")
        return True
    except Exception as e:
        print(f"❌ Volume error: {e}")
        return False


def mute_volume():
    """Mutes system volume"""
    pyautogui.press('volumemute')
    print("🔇 Volume muted")


def volume_up(steps=5):
    """Increases volume"""
    for _ in range(steps):
        pyautogui.press('volumeup')
        time.sleep(0.05)
    print(f"🔊 Volume up x{steps}")


def volume_down(steps=5):
    """Decreases volume"""
    for _ in range(steps):
        pyautogui.press('volumedown')
        time.sleep(0.05)
    print(f"🔉 Volume down x{steps}")


# ============================================================
#  PART 7 — CLIPBOARD & NOTIFICATIONS
# ============================================================

def show_notification(title, message):
    """Shows a Windows toast notification"""
    try:
        script = f"""
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipTitle = "{title}"
$notify.BalloonTipText = "{message}"
$notify.Visible = $True
$notify.ShowBalloonTip(5000)
Start-Sleep -Seconds 6
$notify.Dispose()
"""
        subprocess.Popen(
            ['powershell', '-command', script],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print(f"🔔 Notification: {title} — {message}")
        return True
    except Exception as e:
        print(f"❌ Notification error: {e}")
        return False


def take_system_screenshot():
    """Takes screenshot using Windows Snipping tool"""
    pyautogui.hotkey('win', 'shift', 's')
    time.sleep(0.5)
    print("📸 Snipping tool opened")


# ============================================================
#  PART 8 — MASTER APP COMMAND HANDLER
# ============================================================

def handle_app_command(command):
    """
    Master handler — RS calls this with natural language commands.
    Figures out what app action to take.

    Examples:
        handle_app_command("open spotify")
        handle_app_command("play next song")
        handle_app_command("close chrome")
        handle_app_command("volume up")
        handle_app_command("send discord message hello")
    """
    command = command.lower().strip()

    # Open commands
    if command.startswith("open "):
        app = command.replace("open ", "").strip()
        return open_app(app)

    # Close commands
    elif command.startswith("close "):
        app = command.replace("close ", "").strip()
        return close_app(app)

    # Spotify commands
    elif "next song"    in command: return spotify_next()
    elif "previous song" in command: return spotify_previous()
    elif "pause music"  in command: return spotify_play_pause()
    elif "play music"   in command: return spotify_play_pause()
    elif command.startswith("play "):
        song = command.replace("play ", "").strip()
        return spotify_search_play(song)

    # Volume commands
    elif "volume up"    in command: return volume_up()
    elif "volume down"  in command: return volume_down()
    elif "mute"         in command: return mute_volume()

    # Discord commands
    elif command.startswith("discord "):
        msg = command.replace("discord ", "").strip()
        return discord_send_message(message=msg)

    # Notification
    elif command.startswith("notify "):
        msg = command.replace("notify ", "").strip()
        return show_notification("RS Alert", msg)

    else:
        print(f"❌ Unknown app command: {command}")
        return False


# ============================================================
#  MAIN — Test when run directly
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  RS App Controller — Test Mode")
    print("=" * 50)
    print()
    print("  1 → Open an app")
    print("  2 → Close an app")
    print("  3 → Check if app is running")
    print("  4 → Control Spotify")
    print("  5 → Show notification")
    print()

    choice = input("Enter choice: ").strip()

    if choice == "1":
        app = input("App name (e.g. notepad, chrome, spotify): ")
        open_app(app)

    elif choice == "2":
        app = input("App name to close: ")
        close_app(app)

    elif choice == "3":
        app = input("App name to check: ")
        running = is_app_running(app)
        print(f"{'✅ Running' if running else '❌ Not running'}: {app}")

    elif choice == "4":
        print("Spotify controls:")
        print("  1 → Play/Pause  2 → Next  3 → Previous")
        print("  4 → Volume Up   5 → Volume Down")
        sc = input("Choice: ")
        if sc == "1": spotify_play_pause()
        elif sc == "2": spotify_next()
        elif sc == "3": spotify_previous()
        elif sc == "4": spotify_volume_up()
        elif sc == "5": spotify_volume_down()

    elif choice == "5":
        title = input("Notification title: ")
        msg   = input("Notification message: ")
        show_notification(title, msg)