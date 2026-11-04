# ============================================================
#  R.S. - Red Shirt AI Assistant
#  startup.py — Auto-start RS on Windows boot
# ============================================================

import os
import sys
import winreg
import subprocess

# ── The name RS will register under in Windows startup ──────
APP_NAME = "RS_RedShirt"

# ── Path to the RS launcher ────────────────────────────────
# This is the file that actually starts RS (server + tray + GUI)
if getattr(sys, 'frozen', False):
    # If running as compiled .exe
    RS_PATH = sys.executable
    PYTHON  = sys.executable
else:
    # If running as Python script — launch.py starts the full stack
    RS_PATH  = os.path.abspath("launch.py")
    PYTHON   = sys.executable


# ============================================================
#  ADD RS TO WINDOWS STARTUP
# ============================================================

def add_to_startup():
    """
    Adds RS to Windows Registry startup.
    This means RS starts automatically every time PC boots.
    """
    try:
        # Open Windows Registry startup key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        # Build the command that will run on startup
        if getattr(sys, 'frozen', False):
            # Running as .exe
            command = f'"{RS_PATH}"'
        else:
            # Running as Python script — prefer pythonw (silent, no console)
            python_exe = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(python_exe):
                python_exe = PYTHON
            command = f'"{python_exe}" "{RS_PATH}"'

        # Write to registry
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)

        print(f"✅ RS added to startup successfully!")
        print(f"   Command: {command}")
        print(f"   RS will now start automatically on every boot.")
        return True

    except Exception as e:
        print(f"❌ Failed to add to startup: {str(e)}")
        return False


# ============================================================
#  REMOVE RS FROM WINDOWS STARTUP
# ============================================================

def remove_from_startup():
    """
    Removes RS from Windows startup.
    RS will no longer auto-start on boot.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)

        print(f"✅ RS removed from startup.")
        return True

    except FileNotFoundError:
        print("RS was not in startup.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


# ============================================================
#  CHECK IF RS IS IN STARTUP
# ============================================================

def is_in_startup():
    """
    Checks if RS is already registered in Windows startup.
    Returns True or False.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )

        value, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)

        print(f"✅ RS is in startup: {value}")
        return True

    except FileNotFoundError:
        print("RS is NOT in startup.")
        return False
    except Exception as e:
        print(f"Error checking startup: {str(e)}")
        return False


# ============================================================
#  CREATE STARTUP BATCH FILE (BACKUP METHOD)
# ============================================================

def create_startup_batch():
    """
    Creates a .bat file in Windows Startup folder.
    This is a backup method if Registry method fails.
    """
    try:
        # Windows startup folder path
        startup_folder = os.path.join(
            os.environ["APPDATA"],
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )

        bat_path = os.path.join(startup_folder, "RS_AutoStart.bat")

        # Get current directory (RS folder)
        rs_dir = os.path.dirname(os.path.abspath(__file__))

        # Build batch file content
        bat_content = f"""@echo off
title RS - Red Shirt AI Assistant
cd /d "{rs_dir}"
start /min "" "{PYTHON}" "{RS_PATH}"
exit
"""
        with open(bat_path, "w") as f:
            f.write(bat_content)

        print(f"✅ Startup batch file created at:")
        print(f"   {bat_path}")
        return True

    except Exception as e:
        print(f"❌ Batch file error: {str(e)}")
        return False


# ============================================================
#  REMOVE STARTUP BATCH FILE
# ============================================================

def remove_startup_batch():
    """Removes the startup batch file"""
    try:
        startup_folder = os.path.join(
            os.environ["APPDATA"],
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        bat_path = os.path.join(startup_folder, "RS_AutoStart.bat")

        if os.path.exists(bat_path):
            os.remove(bat_path)
            print("✅ Startup batch file removed.")
        else:
            print("No startup batch file found.")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


# ============================================================
#  MAIN — Run directly to install/uninstall startup
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  RS - Red Shirt  |  Startup Manager")
    print("=" * 50)
    print()
    print("What do you want to do?")
    print("  1 → Add RS to startup (auto-start on boot)")
    print("  2 → Remove RS from startup")
    print("  3 → Check if RS is in startup")
    print("  4 → Create startup batch file (backup method)")
    print()

    choice = input("Enter choice (1/2/3/4): ").strip()

    if choice == "1":
        add_to_startup()
        create_startup_batch()  # Do both methods for reliability
    elif choice == "2":
        remove_from_startup()
        remove_startup_batch()
    elif choice == "3":
        is_in_startup()
    elif choice == "4":
        create_startup_batch()
    else:
        print("Invalid choice.")