# ============================================================
#  R.S. - Red Shirt AI Assistant
#  skills.py — UPDATED with all new commands
#  Every skill RS knows — complete command library
# ============================================================

import os
import subprocess
import webbrowser
import datetime
import platform
import psutil
import config

import smtplib
from email.mime.text      import MIMEText
from email.mime.multipart import MIMEMultipart


# ============================================================
#  PART 1 — OPEN APPS & WEBSITES
# ============================================================

def open_website(url):
    """Opens a website in default browser"""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opening {url} in your browser."
    except Exception as e:
        return f"Error opening website: {str(e)}"


def open_app(app_name):
    """
    Opens any application.
    First tries known paths via app_controller,
    falls back to subprocess.
    """
    try:
        from app_controller import open_app as ac_open
        result = ac_open(app_name)
        if result:
            return f"Opening {app_name} for you."
    except:
        pass

    # Fallback — basic app map
    apps = {
        "notepad"    : "notepad.exe",
        "calculator" : "calc.exe",
        "paint"      : "mspaint.exe",
        "explorer"   : "explorer.exe",
        "cmd"        : "cmd.exe",
        "terminal"   : "cmd.exe",
        "chrome"     : "chrome.exe",
        "firefox"    : "firefox.exe",
        "edge"       : "msedge.exe",
        "vs code"    : "code",
        "vscode"     : "code",
        "spotify"    : "spotify.exe",
        "discord"    : "discord.exe",
        "whatsapp"   : "whatsapp.exe",
        "word"       : "winword.exe",
        "excel"      : "excel.exe",
        "powerpoint" : "powerpnt.exe",
        "vlc"        : "vlc.exe",
        "telegram"   : "telegram.exe",
        "zoom"       : "zoom.exe",
        "teams"      : "teams.exe",
        "slack"      : "slack.exe",
    }

    app_lower = app_name.lower()
    exe       = apps.get(app_lower, app_name)

    try:
        subprocess.Popen(exe, shell=True)
        return f"Opening {app_name} for you."
    except Exception as e:
        return f"Could not open {app_name}: {str(e)}"


def close_app(app_name):
    """Closes a running application"""
    try:
        from app_controller import close_app as ac_close
        result = ac_close(app_name)
        return f"Closed {app_name}." if result else f"{app_name} was not running."
    except Exception as e:
        return f"Could not close {app_name}: {str(e)}"


# ============================================================
#  PART 2 — WEB SEARCH
# ============================================================

def search_web(query):
    """Searches Google for a query"""
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching Google for: {query}"
    except Exception as e:
        return f"Search error: {str(e)}"


def search_youtube(query):
    """Searches YouTube — opens first result"""
    try:
        from media_player import play_youtube
        play_youtube(query)
        return f"Playing on YouTube: {query}"
    except Exception as e:
        url = f"https://www.youtube.com/results?search_query={query.replace(' ','+')}"
        webbrowser.open(url)
        return f"Searching YouTube for: {query}"


# ============================================================
#  PART 3 — SYSTEM INFO
# ============================================================

def get_time():
    """Returns current time"""
    now = datetime.datetime.now()
    return f"Current time is {now.strftime('%I:%M %p')}"


def get_date():
    """Returns current date"""
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}"


def get_system_info():
    """Returns full system info"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        ram         = psutil.virtual_memory()
        disk        = psutil.disk_usage('/')

        info = f"""
System    : {platform.system()} {platform.release()}
Machine   : {platform.machine()}
Python    : {platform.python_version()}
CPU Usage : {cpu_percent}%
RAM       : {ram.percent}% used ({_format_bytes(ram.used)} / {_format_bytes(ram.total)})
Disk      : {disk.percent}% used ({_format_bytes(disk.used)} / {_format_bytes(disk.total)})
"""
        return info.strip()
    except Exception as e:
        return f"System info error: {str(e)}"


def get_cpu_usage():
    """Returns current CPU usage"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        return f"CPU usage is {cpu}%"
    except:
        return "Could not get CPU usage"


def get_ram_usage():
    """Returns current RAM usage"""
    try:
        ram = psutil.virtual_memory()
        return f"RAM usage: {ram.percent}% ({_format_bytes(ram.used)} used of {_format_bytes(ram.total)})"
    except:
        return "Could not get RAM usage"


def get_battery():
    """Returns battery status"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "on battery"
            return f"Battery: {battery.percent:.0f}% — {status}"
        return "No battery detected (desktop PC)"
    except:
        return "Could not get battery info"


def get_running_processes():
    """Returns list of top running processes"""
    try:
        procs = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(proc.info)
            except:
                pass

        # Sort by CPU usage
        procs = sorted(procs, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
        lines = [f"{p['name']}: CPU {p['cpu_percent']}% | RAM {p['memory_percent']:.1f}%"
                 for p in procs]
        return "Top processes:\n" + "\n".join(lines)
    except Exception as e:
        return f"Process list error: {str(e)}"


def _format_bytes(b):
    """Converts bytes to human-readable"""
    if b < 1024**2:  return f"{b/1024:.0f}KB"
    if b < 1024**3:  return f"{b/1024**2:.1f}MB"
    return f"{b/1024**3:.1f}GB"


# ============================================================
#  PART 4 — FILE MANAGEMENT
# ============================================================

def create_file(filename, content=""):
    """Creates a new file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filename}' created successfully."
    except Exception as e:
        return f"Error creating file: {str(e)}"


def read_file(filename):
    """Reads and returns file content"""
    try:
        if not os.path.exists(filename):
            return f"File '{filename}' not found."
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        return f"Content of '{filename}':\n{content}" if content else f"File '{filename}' is empty."
    except Exception as e:
        return f"Error reading file: {str(e)}"


def delete_file(filename):
    """Deletes a file"""
    try:
        if not os.path.exists(filename):
            return f"File '{filename}' not found."
        os.remove(filename)
        return f"File '{filename}' deleted successfully."
    except Exception as e:
        return f"Error deleting file: {str(e)}"


def list_files(folder="."):
    """Lists all files in a folder"""
    try:
        files = os.listdir(folder)
        if not files:
            return "No files found."
        return f"Files in '{folder}':\n" + "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


def create_folder(folder_name):
    """Creates a new folder"""
    try:
        os.makedirs(folder_name, exist_ok=True)
        return f"Folder '{folder_name}' created successfully."
    except Exception as e:
        return f"Error creating folder: {str(e)}"


def delete_folder(folder_name):
    """Deletes a folder and all contents"""
    try:
        import shutil
        if not os.path.exists(folder_name):
            return f"Folder '{folder_name}' not found."
        shutil.rmtree(folder_name)
        return f"Folder '{folder_name}' deleted successfully."
    except Exception as e:
        return f"Error deleting folder: {str(e)}"


def move_file(source, destination):
    """Moves a file from source to destination"""
    try:
        import shutil
        shutil.move(source, destination)
        return f"Moved '{source}' to '{destination}'"
    except Exception as e:
        return f"Error moving file: {str(e)}"


def copy_file(source, destination):
    """Copies a file"""
    try:
        import shutil
        shutil.copy2(source, destination)
        return f"Copied '{source}' to '{destination}'"
    except Exception as e:
        return f"Error copying file: {str(e)}"


def open_file(filepath):
    """Opens a file with default app"""
    try:
        os.startfile(filepath)
        return f"Opening '{filepath}'"
    except Exception as e:
        return f"Error opening file: {str(e)}"


def open_folder(folder_path="."):
    """Opens a folder in Windows Explorer"""
    try:
        abs_path = os.path.abspath(folder_path)
        subprocess.Popen(['explorer', abs_path])
        return f"Opened folder: {abs_path}"
    except Exception as e:
        return f"Error opening folder: {str(e)}"


# ============================================================
#  PART 5 — EMAIL
# ============================================================

def send_email(to_address, subject, body):
    """Sends an email via Gmail"""
    try:
        msg            = MIMEMultipart()
        msg['From']    = config.EMAIL_ADDRESS
        msg['To']      = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        server.sendmail(config.EMAIL_ADDRESS, to_address, msg.as_string())
        server.quit()

        return f"Email sent to {to_address} successfully."

    except smtplib.SMTPAuthenticationError:
        return "Email authentication failed. Check your Gmail App Password in .env"
    except Exception as e:
        return f"Email error: {str(e)}"


# ============================================================
#  PART 6 — MEDIA SHORTCUTS
# ============================================================

def play_music(query):
    """Plays music on YouTube"""
    try:
        from media_player import play_youtube
        play_youtube(query)
        return f"Playing: {query}"
    except Exception as e:
        return f"Could not play music: {str(e)}"


def pause_music():
    """Pauses/resumes current media"""
    try:
        from media_player import media_play_pause
        media_play_pause()
        return "Music paused/resumed"
    except Exception as e:
        return f"Could not pause: {str(e)}"


def next_song():
    """Skips to next track"""
    try:
        from media_player import media_next
        media_next()
        return "Skipped to next track"
    except Exception as e:
        return f"Could not skip: {str(e)}"


def volume_up():
    """Increases volume"""
    try:
        from app_controller import volume_up as vu
        vu()
        return "Volume increased"
    except Exception as e:
        return f"Volume error: {str(e)}"


def volume_down():
    """Decreases volume"""
    try:
        from app_controller import volume_down as vd
        vd()
        return "Volume decreased"
    except Exception as e:
        return f"Volume error: {str(e)}"


# ============================================================
#  PART 7 — PC CONTROL SHORTCUTS
# ============================================================

def take_screenshot():
    """Takes a screenshot"""
    try:
        from computer_use import take_screenshot as ts
        path = ts()
        return f"Screenshot saved: {path}"
    except Exception as e:
        return f"Screenshot error: {str(e)}"


def lock_pc():
    """Locks the Windows screen"""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "PC locked"
    except Exception as e:
        return f"Lock error: {str(e)}"


def shutdown_pc(delay=60):
    """Schedules PC shutdown"""
    try:
        subprocess.run(['shutdown', '/s', '/t', str(delay)])
        return f"PC will shut down in {delay} seconds. Type 'cancel shutdown' to cancel."
    except Exception as e:
        return f"Shutdown error: {str(e)}"


def cancel_shutdown():
    """Cancels scheduled shutdown"""
    try:
        subprocess.run(['shutdown', '/a'])
        return "Shutdown cancelled"
    except Exception as e:
        return f"Cancel error: {str(e)}"


def restart_pc(delay=60):
    """Schedules PC restart"""
    try:
        subprocess.run(['shutdown', '/r', '/t', str(delay)])
        return f"PC will restart in {delay} seconds."
    except Exception as e:
        return f"Restart error: {str(e)}"


def sleep_pc():
    """Puts PC to sleep"""
    try:
        subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
        return "Going to sleep..."
    except Exception as e:
        return f"Sleep error: {str(e)}"


def show_notification(title, message):
    """Shows Windows notification"""
    try:
        from app_controller import show_notification as sn
        sn(title, message)
        return f"Notification shown: {title}"
    except Exception as e:
        return f"Notification error: {str(e)}"


# ============================================================
#  PART 8 — CLIPBOARD
# ============================================================

def copy_to_clipboard(text):
    """Copies text to clipboard"""
    try:
        subprocess.run(
            ['powershell', '-command', f'Set-Clipboard -Value "{text}"'],
            capture_output=True
        )
        return f"Copied to clipboard: {text[:30]}..."
    except Exception as e:
        return f"Clipboard error: {str(e)}"


def get_clipboard():
    """Gets text from clipboard"""
    try:
        result = subprocess.run(
            ['powershell', '-command', 'Get-Clipboard'],
            capture_output=True, text=True
        )
        text = result.stdout.strip()
        return f"Clipboard: {text}" if text else "Clipboard is empty"
    except Exception as e:
        return f"Clipboard error: {str(e)}"


# ============================================================
#  PART 9 — INTERNET & NETWORK
# ============================================================

def check_internet():
    """Checks internet connection"""
    try:
        import requests
        r = requests.get("https://www.google.com", timeout=5)
        return "Internet connection: Online"
    except:
        return "Internet connection: Offline"


def get_ip_address():
    """Gets public IP address"""
    try:
        import requests
        r = requests.get("https://api.ipify.org", timeout=5)
        return f"Your public IP: {r.text}"
    except:
        return "Could not get IP address"


def ping_website(url):
    """Pings a website to check if it's up"""
    try:
        import requests
        r = requests.get(url, timeout=5)
        return f"{url} is UP (status: {r.status_code})"
    except:
        return f"{url} is DOWN or unreachable"


# ============================================================
#  PART 10 — MASTER SKILL HANDLER
# ============================================================

def handle_skill(command):
    """
    Master skill handler.
    RS calls this with any command to find the right skill.
    Returns response string.
    """
    cmd = command.lower().strip()

    # Time & Date
    if "time"              in cmd: return get_time()
    if "date"              in cmd: return get_date()

    # System info
    if "system info"       in cmd: return get_system_info()
    if "cpu"               in cmd: return get_cpu_usage()
    if "ram" or "memory usage" in cmd: return get_ram_usage()
    if "battery"           in cmd: return get_battery()
    if "processes"         in cmd: return get_running_processes()
    if "ip address"        in cmd: return get_ip_address()
    if "internet"          in cmd: return check_internet()

    # Apps
    if cmd.startswith("open "):
        app = cmd.replace("open ", "").strip()
        return open_app(app)
    if cmd.startswith("close "):
        app = cmd.replace("close ", "").strip()
        return close_app(app)

    # Media
    if cmd.startswith("play "):
        return play_music(cmd.replace("play ", "").strip())
    if "pause"             in cmd: return pause_music()
    if "next song"         in cmd: return next_song()
    if "volume up"         in cmd: return volume_up()
    if "volume down"       in cmd: return volume_down()

    # Files
    if cmd.startswith("create file "): return create_file(cmd[12:])
    if cmd.startswith("read file "):   return read_file(cmd[10:])
    if cmd.startswith("delete file "): return delete_file(cmd[12:])
    if cmd.startswith("open file "):   return open_file(cmd[10:])
    if cmd.startswith("open folder "): return open_folder(cmd[12:])
    if cmd.startswith("list files"):
        parts  = cmd.split(" ", 2)
        folder = parts[2] if len(parts) > 2 else "."
        return list_files(folder)

    # PC Control
    if "screenshot"        in cmd: return take_screenshot()
    if "lock"              in cmd: return lock_pc()
    if "shutdown"          in cmd: return shutdown_pc()
    if "cancel shutdown"   in cmd: return cancel_shutdown()
    if "restart"           in cmd: return restart_pc()
    if "sleep"             in cmd: return sleep_pc()

    # Clipboard
    if "clipboard"         in cmd: return get_clipboard()

    # Notification
    if cmd.startswith("notify "):
        msg = cmd.replace("notify ", "").strip()
        return show_notification("RS", msg)

    # Email
    if cmd.startswith("send email "):
        parts = cmd[11:].split("|")
        if len(parts) >= 3:
            return send_email(parts[0].strip(),
                              parts[1].strip(),
                              parts[2].strip())
        return "Format: send email [to] | [subject] | [body]"

    # Search
    if cmd.startswith("search "):
        return search_web(cmd[7:])
    if cmd.startswith("youtube "):
        return search_youtube(cmd[8:])

    return None  # Not handled — AI will respond