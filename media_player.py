# ============================================================
#  R.S. - Red Shirt AI Assistant
#  media_player.py — Media player control
#  RS plays music, videos, audio — local files & online
# ============================================================

import subprocess
import os
import time
import threading
import pyautogui
from computer_use import search_and_open

# ── Downloads folder ─────────────────────────────────────────
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# ── Global state ─────────────────────────────────────────────
_current_media  = None
_vlc_process    = None
_pygame_playing = False


# ============================================================
#  PART 1 — PLAY WITH VLC (local files & streams)
# ============================================================

def play_with_vlc(path_or_url, fullscreen=False):
    """
    Plays any media file or URL with VLC.
    Supports: MP3, MP4, AVI, MKV, WAV, FLAC, YouTube URLs etc.

    path_or_url: local file path OR online URL
    fullscreen:  True = plays in fullscreen
    """
    global _vlc_process, _current_media

    try:
        print(f"▶️  Playing with VLC: {path_or_url}")

        # Find VLC
        vlc_paths = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        ]

        vlc_exe = None
        for p in vlc_paths:
            if os.path.exists(p):
                vlc_exe = p
                break

        if not vlc_exe:
            print("⚠️  VLC not found — trying Windows default player")
            return play_with_default(path_or_url)

        # Build VLC command
        args = [vlc_exe, path_or_url]
        if fullscreen:
            args.append('--fullscreen')

        # Kill existing VLC
        stop_media()
        time.sleep(0.5)

        # Start VLC
        _vlc_process   = subprocess.Popen(args)
        _current_media = path_or_url

        print(f"✅ Playing: {path_or_url}")
        return True

    except Exception as e:
        print(f"❌ VLC error: {e}")
        return False


def stop_media():
    """Stops currently playing media"""
    global _vlc_process, _current_media

    try:
        # Stop VLC
        if _vlc_process:
            _vlc_process.terminate()
            _vlc_process = None

        # Kill any VLC processes
        subprocess.run(
            ['taskkill', '/f', '/im', 'vlc.exe'],
            capture_output=True
        )

        _current_media = None
        print("⏹️  Media stopped")
        return True

    except Exception as e:
        print(f"❌ Stop error: {e}")
        return False


def play_with_default(path):
    """Opens file with Windows default app"""
    try:
        os.startfile(path)
        print(f"▶️  Opened with default player: {path}")
        return True
    except Exception as e:
        print(f"❌ Default player error: {e}")
        return False


# ============================================================
#  PART 2 — PYGAME AUDIO (simple MP3/WAV)
# ============================================================

def play_audio(file_path, loop=False):
    """
    Plays audio file using pygame.
    Lighter than VLC for simple audio files.
    Supports: MP3, WAV, OGG
    """
    global _pygame_playing

    try:
        import pygame
        pygame.mixer.init()

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        print(f"🎵 Playing audio: {file_path}")
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(-1 if loop else 0)
        _pygame_playing = True

        print(f"✅ Playing: {os.path.basename(file_path)}")
        return True

    except Exception as e:
        print(f"❌ Audio error: {e}")
        return False


def stop_audio():
    """Stops pygame audio"""
    global _pygame_playing
    try:
        import pygame
        pygame.mixer.music.stop()
        _pygame_playing = False
        print("⏹️  Audio stopped")
        return True
    except:
        return False


def pause_audio():
    """Pauses pygame audio"""
    try:
        import pygame
        pygame.mixer.music.pause()
        print("⏸️  Audio paused")
        return True
    except:
        return False


def resume_audio():
    """Resumes pygame audio"""
    try:
        import pygame
        pygame.mixer.music.unpause()
        print("▶️  Audio resumed")
        return True
    except:
        return False


def set_audio_volume(level):
    """
    Sets pygame audio volume.
    level: 0.0 to 1.0
    """
    try:
        import pygame
        pygame.mixer.music.set_volume(level)
        print(f"🔊 Volume set to {int(level*100)}%")
        return True
    except:
        return False


# ============================================================
#  PART 3 — YOUTUBE PLAYBACK
# ============================================================

def play_youtube(query, use_browser=True):
    """
    Plays YouTube video.
    Searches and directly opens the first video result.
    """
    try:
        import webbrowser
        import requests
        import re

        print(f"▶️  Searching YouTube for: {query}")

        if query.startswith("http"):
            # Direct URL — open it straight away
            webbrowser.open(query)
            return True

        # Search YouTube and get first video URL
        search_query = query.replace(" ", "+")
        search_url   = f"https://www.youtube.com/results?search_query={search_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        # Extract first video ID from YouTube search results
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)

        if video_ids:
            first_video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            print(f"✅ Opening video: {first_video_url}")
            webbrowser.open(first_video_url)
            return True
        else:
            # Fallback — just open search results
            print("⚠️  Could not find video ID — opening search results")
            webbrowser.open(search_url)
            return True

    except Exception as e:
        print(f"❌ YouTube play error: {e}")
        import webbrowser
        webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ','+')}")
        return False


def download_youtube_audio(query_or_url):
    """
    Downloads YouTube audio as MP3.
    Returns file path when done.
    """
    try:
        import yt_dlp

        # Configure yt-dlp
        ydl_opts = {
            'format'          : 'bestaudio/best',
            'outtmpl'         : os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
            'postprocessors'  : [{
                'key'            : 'FFmpegExtractAudio',
                'preferredcodec' : 'mp3',
            }],
            'quiet'           : True,
            'no_warnings'     : True,
        }

        # If not a URL, search YouTube first
        if not query_or_url.startswith('http'):
            query_or_url = f"ytsearch1:{query_or_url}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info      = ydl.extract_info(query_or_url, download=True)
            if 'entries' in info:
                info  = info['entries'][0]
            title     = info.get('title', 'audio')
            file_path = os.path.join(DOWNLOADS_DIR, f"{title}.mp3")

        print(f"✅ Downloaded: {file_path}")
        return file_path

    except Exception as e:
        print(f"❌ Download audio error: {e}")
        return None


def download_youtube_video(query_or_url, quality='720p'):
    """
    Downloads YouTube video.
    Returns file path when done.
    """
    try:
        import yt_dlp

        quality_map = {
            '360p' : 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            '480p' : 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '720p' : 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        }

        ydl_opts = {
            'format' : quality_map.get(quality, 'bestvideo+bestaudio/best'),
            'outtmpl': os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
            'quiet'  : True,
        }

        if not query_or_url.startswith('http'):
            query_or_url = f"ytsearch1:{query_or_url}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info      = ydl.extract_info(query_or_url, download=True)
            if 'entries' in info:
                info  = info['entries'][0]
            title     = info.get('title', 'video')

        print(f"✅ Video downloaded: {title}")
        return os.path.join(DOWNLOADS_DIR, f"{title}.mp4")

    except Exception as e:
        print(f"❌ Download video error: {e}")
        return None


# ============================================================
#  PART 4 — SYSTEM MEDIA KEYS
# ============================================================

def media_play_pause():
    """Press system media play/pause key"""
    pyautogui.press('playpause')
    print("⏯️  Play/Pause")


def media_next():
    """Press system next track key"""
    pyautogui.press('nexttrack')
    print("⏭️  Next track")


def media_previous():
    """Press system previous track key"""
    pyautogui.press('prevtrack')
    print("⏮️  Previous track")


def media_stop():
    """Press system stop key"""
    pyautogui.press('stop')
    print("⏹️  Stop")


def system_volume_up(steps=5):
    """Increases system volume"""
    for _ in range(steps):
        pyautogui.press('volumeup')
        time.sleep(0.03)
    print(f"🔊 Volume up x{steps}")


def system_volume_down(steps=5):
    """Decreases system volume"""
    for _ in range(steps):
        pyautogui.press('volumedown')
        time.sleep(0.03)
    print(f"🔉 Volume down x{steps}")


def system_mute():
    """Mutes/unmutes system audio"""
    pyautogui.press('volumemute')
    print("🔇 Mute toggled")


# ============================================================
#  PART 5 — OPEN MEDIA APPS
# ============================================================

def open_spotify(search=None):
    """Opens Spotify, optionally searches for a song"""
    from app_controller import open_app, is_app_running, spotify_search_play

    if not is_app_running("Spotify"):
        open_app("spotify")
        time.sleep(5)

    if search:
        spotify_search_play(search)

    print("✅ Spotify opened")
    return True


def open_netflix():
    """Opens Netflix in system default browser"""
    import webbrowser
    webbrowser.open("https://www.netflix.com")
    print("✅ Netflix opened")


def open_youtube():
    """Opens YouTube in system default browser"""
    import webbrowser
    webbrowser.open("https://www.youtube.com")
    print("✅ YouTube opened")


def open_media_file(file_path):
    """Opens any media file with best available player"""
    ext = os.path.splitext(file_path)[1].lower()

    # Audio files — use pygame for simplicity
    if ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac']:
        return play_audio(file_path)

    # Video files — use VLC
    elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
        return play_with_vlc(file_path)

    # Unknown — use default app
    else:
        return play_with_default(file_path)


# ============================================================
#  PART 6 — MASTER MEDIA COMMAND HANDLER
# ============================================================

def handle_media_command(command):
    """
    Master handler for all media commands.
    RS calls this with natural language.

    Examples:
        handle_media_command("play shape of you")
        handle_media_command("pause music")
        handle_media_command("next song")
        handle_media_command("volume up")
        handle_media_command("open netflix")
        handle_media_command("open youtube")
    """
    command = command.lower().strip()

    # Play commands
    if command.startswith("play "):
        query = command.replace("play ", "").strip()
        if "youtube" in query:
            query = query.replace("youtube", "").strip()
            return play_youtube(query)
        elif "spotify" in query:
            query = query.replace("spotify", "").strip()
            return open_spotify(search=query)
        else:
            # Default — search YouTube in browser
            return play_youtube(query)

    # Control commands
    elif "pause"    in command: return media_play_pause()
    elif "resume"   in command: return media_play_pause()
    elif "next"     in command: return media_next()
    elif "previous" in command: return media_previous()
    elif "stop"     in command: return stop_media()

    # Volume commands
    elif "volume up"   in command: return system_volume_up()
    elif "volume down" in command: return system_volume_down()
    elif "mute"        in command: return system_mute()

    # Open streaming apps
    elif "netflix"  in command: return open_netflix()
    elif "youtube"  in command: return open_youtube()
    elif "spotify"  in command: return open_spotify()

    # Download commands
    elif command.startswith("download "):
        query = command.replace("download ", "").strip()
        if "video" in query:
            query = query.replace("video", "").strip()
            return download_youtube_video(query)
        else:
            return download_youtube_audio(query)

    else:
        print(f"❌ Unknown media command: {command}")
        return False


# ============================================================
#  MAIN — Test when run directly
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  RS Media Player — Test Mode")
    print("=" * 50)
    print()
    print("  1 → Play YouTube video in browser")
    print("  2 → Download YouTube audio (MP3)")
    print("  3 → Play local audio file")
    print("  4 → System media key test")
    print("  5 → Open Spotify")
    print()

    choice = input("Enter choice: ").strip()

    if choice == "1":
        query = input("What to play on YouTube: ")
        play_youtube(query, use_browser=True)

    elif choice == "2":
        query = input("Song/video to download: ")
        path  = download_youtube_audio(query)
        if path:
            print(f"Downloaded to: {path}")
            play = input("Play now? (yes/no): ")
            if play.lower() == 'yes':
                play_audio(path)
                input("Press Enter to stop...")
                stop_audio()

    elif choice == "3":
        path = input("File path: ")
        play_audio(path)
        input("Press Enter to stop...")
        stop_audio()

    elif choice == "4":
        print("Testing media keys...")
        print("Make sure some media is playing first!")
        time.sleep(2)
        media_play_pause()
        time.sleep(1)
        media_next()
        time.sleep(1)
        media_previous()

    elif choice == "5":
        song = input("Search Spotify for: ")
        open_spotify(search=song)