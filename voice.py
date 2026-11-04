# ============================================================
#  R.S. - Red Shirt AI Agent
#  voice.py — TTS (speak) + STT (listen) + wake word
# ============================================================

import os
import subprocess
import threading
import config


# ============================================================
#  PART 1 — SPEAK (TTS via Windows Speech Synthesis)
# ============================================================

def _clean_for_speech(text):
    """
    Prepares text for the Windows speech engine.
    The text is written to a UTF-8 file and read by PowerShell,
    so we no longer inject it into a script string (safe from
    quotes, $, parentheses, newlines etc).
    """
    clean = str(text)

    # Smart quotes / dashes / ellipsis
    clean = clean.replace('\u2019', "'").replace('\u2018', "'")
    clean = clean.replace('\u201c', '"').replace('\u201d', '"')
    clean = clean.replace('\u2014', '-').replace('\u2013', '-')
    clean = clean.replace('\u2026', '...')

    # Expand common contractions so they are spoken properly
    fixes = {
        "i'm": "i am",   "i'll": "i will",  "i've": "i have",
        "i'd": "i would", "we'll": "we will", "we're": "we are",
        "we've": "we have", "you'll": "you will", "you're": "you are",
        "you've": "you've", "don't": "do not", "didn't": "did not",
        "can't": "cannot", "won't": "will not", "isn't": "is not",
        "aren't": "are not", "wasn't": "was not", "it's": "it is",
        "that's": "that is", "there's": "there is", "let's": "let us",
    }
    # Only expand whole words (case-insensitive)
    words = []
    for w in clean.split(" "):
        low = w.lower()
        if low in fixes:
            words.append(fixes[low])
        else:
            words.append(w)
    clean = " ".join(words)

    # Strip characters the speech engine chokes on
    for ch in ["`", "*", "#", "_", "<", ">", "{", "}"]:
        clean = clean.replace(ch, "")

    # Collapse newlines into pauses
    clean = clean.replace("\n", ". ")
    return clean


def speak(text, block=True):
    """
    RS speaks using the Windows built-in speech engine.
    block=True waits until speech finishes (used by the CLI).
    block=False returns immediately (used by the GUI/server).
    """
    if not config.VOICE_ENABLED or not str(text).strip():
        return

    def _speak():
        try:
            clean_text = _clean_for_speech(text)

            # Write the text to a file — PowerShell reads it (injection-safe)
            with open(config.SPEAK_TEXT, "w", encoding="utf-8") as f:
                f.write(clean_text)

            # Build a tiny script that reads that file and speaks it
            script = f"""
$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Speech
$t = Get-Content -Raw -Encoding UTF8 '{config.SPEAK_TEXT}'
if ($t) {{
    $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $s.Rate  = 1
    $s.Volume = 100
    $s.Speak($t)
    $s.Dispose()
}}
"""
            with open(config.SPEAK_SCRIPT, "w", encoding="utf-8") as f:
                f.write(script)

            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", config.SPEAK_SCRIPT],
                shell=False,
                capture_output=True,
                timeout=60,
            )

        except Exception as e:
            print(f"Voice error: {e}")

    if block:
        _speak()
    else:
        threading.Thread(target=_speak, daemon=True).start()


def stop_speaking():
    """Kills any speech currently playing."""
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", "powershell.exe"],
            capture_output=True
        )
    except Exception:
        pass


# ============================================================
#  PART 2 — LISTEN (STT)
# ============================================================

def listen(timeout=6, phrase_limit=8):
    """
    Listen to the microphone and return text.
    Returns: transcript string, or one of:
      "timeout"  — heard nothing
      "unclear"  — could not understand audio
      "error"    — microphone/network problem
    """
    try:
        import speech_recognition as sr
    except Exception:
        return "error"

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            print(f"{config.ASSISTANT_NAME}: Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_limit)

        text = recognizer.recognize_google(audio)
        print(f"You (voice): {text}")
        return text

    except Exception as e:
        import speech_recognition as sr
        if isinstance(e, sr.WaitTimeoutError):
            return "timeout"
        if isinstance(e, sr.UnknownValueError):
            return "unclear"
        # sr.RequestError (API down) or mic failure
        return "error"


# ============================================================
#  PART 3 — ALWAYS-ON WAKE WORD ("Hey RS")
# ============================================================

_wake_active = False
_wake_thread = None


def is_wake_active():
    return _wake_active


def start_wake_word(on_wake=None, energy_threshold=300):
    """
    Starts the always-on background listener.
    When the user says the wake word (config.WAKE_WORD, e.g. "hey rs"):
      - calls on_wake() if given
      - otherwise listens once for a command and returns it via the callback
    Safe to call more than once — only one listener runs.
    """
    global _wake_active, _wake_thread
    if _wake_active:
        return True

    def _loop():
        global _wake_active
        try:
            import speech_recognition as sr
        except Exception:
            return

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = energy_threshold
        recognizer.dynamic_energy_threshold = True
        wake_words = [w.strip() for w in config.WAKE_WORD.split("/") if w.strip()]

        try:
            mic = sr.Microphone()
        except Exception:
            return

        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.75)

        _wake_active = True
        print(f"🎙️  Wake word active — say '{config.WAKE_WORD.upper()}'")

        while _wake_active:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=4,
                                              phrase_time_limit=4)
                heard = recognizer.recognize_google(audio).lower()

                # Did the user call us?
                if any(w in heard for w in wake_words):
                    print("🎙️  Wake word detected!")
                    if on_wake:
                        on_wake()
                    else:
                        # Default behaviour: listen for the real command
                        command = listen()
                        if command not in ("timeout", "unclear", "error"):
                            print(f"🎙️  Wake command: {command}")
                            return command
            except Exception:
                continue

    _wake_thread = threading.Thread(target=_loop, daemon=True)
    _wake_thread.start()
    return True


def stop_wake_word():
    """Stops the always-on listener."""
    global _wake_active
    _wake_active = False


# ============================================================
#  MAIN — Test voice
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  RS Voice — Test Mode")
    print("=" * 50)
    print()
    print("  1 → Test speaking")
    print("  2 → Test listening")
    print()

    choice = input("Enter choice: ").strip()

    if choice == "1":
        text = input("What should RS say: ")
        speak(text)
    elif choice == "2":
        print("Say something...")
        result = listen()
        print(f"Result: {result}")
