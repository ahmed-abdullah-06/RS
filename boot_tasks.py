# ============================================================
#  R.S. - Red Shirt AI Assistant
#  boot_tasks.py — Auto-run tasks on PC startup
#  RS reads previous memory and executes scheduled tasks
#  automatically when PC boots
# ============================================================

import os
import json
import time
import threading
import schedule
import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Files ────────────────────────────────────────────────────
TASKS_FILE    = "memory_store/scheduled_tasks.json"
BOOT_LOG_FILE = "memory_store/boot_log.json"
os.makedirs("memory_store", exist_ok=True)


# ============================================================
#  PART 1 — TASK STORAGE
# ============================================================

def load_tasks():
    """Loads all scheduled tasks from file"""
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
        return []
    except:
        return []


def save_tasks(tasks):
    """Saves tasks to file"""
    try:
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save tasks: {e}")
        return False


def add_task(name, command, trigger, trigger_value=None, enabled=True):
    """
    Adds a new scheduled task.
    trigger: 'boot', 'daily', 'hourly', 'interval'
    trigger_value: for daily -> "08:00", for interval -> 30 (minutes)
    """
    tasks = load_tasks()
    task  = {
        "id"           : int(time.time()),
        "name"         : name,
        "command"      : command,
        "trigger"      : trigger,
        "trigger_value": trigger_value,
        "enabled"      : enabled,
        "created"      : datetime.datetime.now().isoformat(),
        "last_run"     : None,
        "run_count"    : 0
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Task added: {name} | {trigger} {trigger_value or ''}")
    return task


def remove_task(task_id):
    tasks = [t for t in load_tasks() if t.get("id") != task_id]
    save_tasks(tasks)
    print(f"Task {task_id} removed")


def toggle_task(task_id, enabled):
    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id:
            task["enabled"] = enabled
    save_tasks(tasks)
    print(f"Task {task_id} {'enabled' if enabled else 'disabled'}")


def list_tasks():
    tasks = load_tasks()
    if not tasks:
        print("No scheduled tasks")
        return []
    print(f"\nScheduled Tasks ({len(tasks)} total):")
    print("-" * 50)
    for t in tasks:
        status = "ON " if t.get("enabled") else "OFF"
        print(f"[{status}] [{t['id']}] {t['name']}")
        print(f"      Command : {t['command']}")
        print(f"      Trigger : {t['trigger']} {t.get('trigger_value','')}")
        print(f"      Ran     : {t.get('run_count',0)} times")
        print()
    return tasks


# ============================================================
#  PART 2 — EXECUTE A TASK
# ============================================================

def execute_task(task):
    """Executes a task by sending command to RS server"""
    try:
        import requests as req
        task_name = task.get("name", "Unknown")
        command   = task.get("command", "")
        print(f"\nRunning task: {task_name} | {command}")

        response = req.post(
            "http://localhost:5000/chat",
            json    = {"message": command, "source": "boot_task"},
            timeout = 30
        )

        if response.status_code == 200:
            reply = response.json().get("response", "")
            print(f"   RS: {reply[:100]}...")

            tasks = load_tasks()
            for t in tasks:
                if t.get("id") == task.get("id"):
                    t["last_run"]  = datetime.datetime.now().isoformat()
                    t["run_count"] = t.get("run_count", 0) + 1
            save_tasks(tasks)
            return reply

    except Exception as e:
        print(f"Task error: {e}")
        return None


# ============================================================
#  PART 3 — BOOT TASKS
# ============================================================

def _wait_for_server(max_wait=60):
    """Waits until Flask server is online"""
    import requests as req
    print("   Waiting for RS server...")
    for _ in range(max_wait // 2):
        try:
            r = req.get("http://localhost:5000/ping", timeout=2)
            if r.status_code == 200:
                print("   Server ready!")
                return True
        except:
            pass
        time.sleep(2)
    print("   Server did not start in time")
    return False


def _log_boot(tasks_run):
    try:
        logs = []
        if os.path.exists(BOOT_LOG_FILE):
            with open(BOOT_LOG_FILE, "r") as f:
                logs = json.load(f)
        logs.append({"time": datetime.datetime.now().isoformat(), "tasks_run": tasks_run})
        logs = logs[-50:]
        with open(BOOT_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
    except:
        pass


def run_boot_tasks():
    """Runs all boot-triggered tasks on startup"""
    print("\nRunning boot tasks...")
    _wait_for_server()

    tasks      = load_tasks()
    boot_tasks = [t for t in tasks if t.get("trigger") == "boot" and t.get("enabled")]

    if not boot_tasks:
        print("   No boot tasks configured")
        return

    print(f"   Found {len(boot_tasks)} boot tasks")
    time.sleep(2)

    for task in boot_tasks:
        execute_task(task)
        time.sleep(3)

    _log_boot(len(boot_tasks))
    print("Boot tasks complete!")


# ============================================================
#  PART 4 — SCHEDULER
# ============================================================

def setup_scheduler():
    """Schedules all daily/hourly/interval tasks"""
    tasks = load_tasks()
    count = 0

    for task in tasks:
        if not task.get("enabled"):
            continue
        trigger = task.get("trigger")
        value   = task.get("trigger_value")
        try:
            if trigger == "daily" and value:
                schedule.every().day.at(value).do(execute_task, task)
                print(f"Scheduled daily: '{task['name']}' at {value}")
                count += 1
            elif trigger == "hourly":
                schedule.every().hour.do(execute_task, task)
                print(f"Scheduled hourly: '{task['name']}'")
                count += 1
            elif trigger == "interval" and value:
                schedule.every(int(value)).minutes.do(execute_task, task)
                print(f"Scheduled every {value}min: '{task['name']}'")
                count += 1
        except Exception as e:
            print(f"Schedule error for '{task['name']}': {e}")

    print(f"Scheduler ready — {count} tasks scheduled")
    return count


def run_scheduler():
    """Runs scheduler loop in background"""
    print("Task scheduler running...")
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Scheduler error: {e}")
        time.sleep(30)


def start_scheduler_thread():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    return thread


# ============================================================
#  PART 5 — DEFAULT TASKS
# ============================================================

def setup_default_tasks():
    """Sets up useful default tasks"""
    print("Setting up default tasks...")
    save_tasks([])

    add_task(
        name    = "Boot Greeting",
        command = "say good morning and tell me the time and date",
        trigger = "boot",
        enabled = True
    )
    add_task(
        name          = "Morning Briefing",
        command       = "give me a morning briefing with time and date",
        trigger       = "daily",
        trigger_value = "08:00",
        enabled       = True
    )
    add_task(
        name          = "Evening Summary",
        command       = "give me a summary of what we did today",
        trigger       = "daily",
        trigger_value = "20:00",
        enabled       = True
    )
    add_task(
        name    = "Hourly Time",
        command = "tell me the current time",
        trigger = "hourly",
        enabled = False
    )

    print("Default tasks ready!")
    list_tasks()


# ============================================================
#  PART 6 — FULL BOOT SEQUENCE
# ============================================================

def run_full_boot_sequence():
    """Complete RS boot sequence — call this on startup"""
    print("\n" + "="*50)
    print("  RS BOOT SEQUENCE")
    print("="*50)

    threading.Thread(target=run_boot_tasks,   daemon=True).start()
    setup_scheduler()
    start_scheduler_thread()

    print("RS boot sequence complete!")
    print("="*50 + "\n")


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  RS Boot Tasks Manager")
    print("=" * 50)
    print()
    print("  1 -> View all tasks")
    print("  2 -> Add a new task")
    print("  3 -> Remove a task")
    print("  4 -> Enable/disable a task")
    print("  5 -> Run boot tasks now (test)")
    print("  6 -> Setup default tasks")
    print()

    choice = input("Enter choice: ").strip()

    if choice == "1":
        list_tasks()

    elif choice == "2":
        name    = input("Task name: ")
        command = input("Command: ")
        trigger = input("Trigger (boot/daily/hourly/interval): ")
        value   = None
        if trigger == "daily":
            value = input("Time (HH:MM): ")
        elif trigger == "interval":
            value = input("Every X minutes: ")
        add_task(name, command, trigger, value)

    elif choice == "3":
        list_tasks()
        task_id = int(input("Task ID to remove: "))
        remove_task(task_id)

    elif choice == "4":
        list_tasks()
        task_id = int(input("Task ID: "))
        enabled = input("Enable? (yes/no): ").lower() == "yes"
        toggle_task(task_id, enabled)

    elif choice == "5":
        print("Running boot tasks (server.py must be running)...")
        run_boot_tasks()

    elif choice == "6":
        confirm = input("Replace all tasks? (yes/no): ")
        if confirm.lower() == "yes":
            setup_default_tasks()