# ============================================================
#  R.S. - Red Shirt AI Assistant
#  vision.py — Screen vision + AI understanding
#  RS takes screenshot → sends to AI → AI reads screen
#  → decides what to do next
# ============================================================

import os
import base64
import requests
import json
import time
from PIL import ImageGrab, Image, ImageEnhance
import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Settings ─────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
SCREENSHOT_DIR     = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ── Vision model (supports images) ───────────────────────────
VISION_MODEL = "openai/gpt-4o"  # GPT-4o has vision built in


# ============================================================
#  PART 1 — SCREENSHOT TO BASE64
# ============================================================

def screenshot_to_base64(filepath=None):
    """
    Takes a screenshot and converts it to base64 string.
    Base64 is how we send images to the AI API.
    """
    try:
        # Take screenshot
        screenshot = ImageGrab.grab()

        # Resize to reduce API cost (1280x720 is enough)
        screenshot = screenshot.resize((1280, 720), Image.LANCZOS)

        # Enhance contrast slightly — easier for AI to read
        enhancer   = ImageEnhance.Contrast(screenshot)
        screenshot = enhancer.enhance(1.2)

        # Save if filepath given
        if filepath:
            screenshot.save(filepath)

        # Convert to base64
        import io
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode('utf-8')

        return b64

    except Exception as e:
        print(f"❌ Screenshot to base64 error: {e}")
        return None


# ============================================================
#  PART 2 — SEND SCREENSHOT TO AI
# ============================================================

def analyze_screen(question="What do you see on this screen?"):
    """
    Takes screenshot and sends it to AI vision model.
    AI reads the screen and answers the question.

    Examples:
        analyze_screen("What app is open?")
        analyze_screen("Where is the search box?")
        analyze_screen("Is there a button to click?")
        analyze_screen("What does the screen show?")
    """
    try:
        print(f"👁️  Taking screenshot and analyzing...")

        # Get screenshot as base64
        b64_image = screenshot_to_base64()
        if not b64_image:
            return "Could not take screenshot"

        # Build API request with image
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type" : "application/json"
        }

        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers = headers,
            json    = payload,
            timeout = 30
        )

        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"👁️  AI sees: {answer[:100]}...")
            return answer
        else:
            print(f"❌ Vision API error: {response.status_code}")
            return f"Vision API error: {response.status_code}"

    except Exception as e:
        print(f"❌ Analyze screen error: {e}")
        return f"Error: {str(e)}"


# ============================================================
#  PART 3 — FIND ELEMENT ON SCREEN
# ============================================================

def find_element(element_description):
    """
    Asks AI to find a specific element on screen.
    Returns (x, y) coordinates of the element.

    Examples:
        find_element("the search box")
        find_element("the submit button")
        find_element("the close button")
        find_element("the text input field")
    """
    try:
        print(f"🔍 Looking for: {element_description}")

        b64_image = screenshot_to_base64()
        if not b64_image:
            return None

        # Get screen size for coordinate context
        import pyautogui
        screen_w, screen_h = pyautogui.size()

        question = f"""
Look at this screenshot carefully.
Screen size is {screen_w} x {screen_h} pixels.

Find: {element_description}

Reply with ONLY a JSON object like this:
{{"found": true, "x": 500, "y": 300, "description": "what you found"}}

Or if not found:
{{"found": false, "x": 0, "y": 0, "description": "not found"}}

Reply with JSON only. No other text.
"""

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type" : "application/json"
        }

        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ],
            "max_tokens": 100
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers = headers,
            json    = payload,
            timeout = 30
        )

        if response.status_code == 200:
            result  = response.json()
            content = result['choices'][0]['message']['content']

            # Clean and parse JSON
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            data = json.loads(content)

            if data.get('found'):
                x, y = data['x'], data['y']
                print(f"✅ Found '{element_description}' at ({x}, {y})")
                return x, y
            else:
                print(f"❌ Could not find '{element_description}' on screen")
                return None

        return None

    except Exception as e:
        print(f"❌ Find element error: {e}")
        return None


# ============================================================
#  PART 4 — DECIDE NEXT ACTION
# ============================================================

def decide_next_action(task, history=""):
    """
    RS's brain for autonomous tasks.
    Takes a screenshot, shows AI what's on screen,
    AI decides what action to take next to complete the task.

    Returns a dictionary with the next action to take.
    """
    try:
        print(f"🧠 Deciding next action for: {task}")

        b64_image = screenshot_to_base64()
        if not b64_image:
            return {"action": "error", "reason": "could not take screenshot"}

        import pyautogui
        screen_w, screen_h = pyautogui.size()

        prompt = f"""
You are RS, an AI controlling a Windows computer.
Screen size: {screen_w} x {screen_h}

Current task: {task}
{f"Previous actions taken: {history}" if history else ""}

Look at the current screenshot carefully.
Decide the SINGLE next action to take.

Reply with ONLY a JSON object. Choose one action type:

For clicking:
{{"action": "click", "x": 500, "y": 300, "reason": "clicking the search box"}}

For typing:
{{"action": "type", "text": "hello world", "reason": "typing the search query"}}

For pressing a key:
{{"action": "press", "key": "enter", "reason": "submitting the form"}}

For keyboard shortcut:
{{"action": "hotkey", "keys": ["ctrl", "t"], "reason": "opening new tab"}}

For scrolling:
{{"action": "scroll", "direction": "down", "amount": 3, "reason": "scrolling to see more"}}

For waiting:
{{"action": "wait", "seconds": 2, "reason": "waiting for page to load"}}

For task complete:
{{"action": "done", "reason": "task is complete"}}

Reply JSON only. No other text.
"""

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type" : "application/json"
        }

        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 150
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers = headers,
            json    = payload,
            timeout = 30
        )

        if response.status_code == 200:
            result  = response.json()
            content = result['choices'][0]['message']['content'].strip()

            # Clean JSON
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            action = json.loads(content)
            print(f"🧠 Next action: {action}")
            return action

        return {"action": "error", "reason": "API error"}

    except Exception as e:
        print(f"❌ Decide action error: {e}")
        return {"action": "error", "reason": str(e)}


# ============================================================
#  PART 5 — AUTONOMOUS TASK LOOP
# ============================================================

def run_task_autonomously(task, max_steps=15):
    """
    RS's full autonomous mode.
    Give it a task → it executes it step by step like a human.

    RS will:
    1. Take screenshot
    2. AI decides next action
    3. Execute action
    4. Repeat until task done or max steps reached

    Example:
        run_task_autonomously("Open Chrome and search for weather in Karachi")
        run_task_autonomously("Open Notepad and type Hello World")
    """
    from computer_use import execute_action

    print(f"\n🤖 RS AUTONOMOUS MODE")
    print(f"   Task: {task}")
    print(f"   Max steps: {max_steps}")
    print(f"   Move mouse to TOP-LEFT to emergency stop!")
    print()

    history = []
    step    = 0

    while step < max_steps:
        step += 1
        print(f"\n── Step {step}/{max_steps} ──────────────────")

        # Decide next action based on screen
        action = decide_next_action(task, history=str(history[-5:]))

        action_type = action.get('action', 'error')
        reason      = action.get('reason', '')

        print(f"   Action : {action_type}")
        print(f"   Reason : {reason}")

        # Task complete
        if action_type == 'done':
            print(f"\n✅ Task completed in {step} steps!")
            return True

        # Error
        if action_type == 'error':
            print(f"\n❌ Error: {reason}")
            return False

        # Execute the action
        if action_type == 'click':
            execute_action('click', x=action.get('x'), y=action.get('y'))

        elif action_type == 'type':
            execute_action('type', text=action.get('text', ''))

        elif action_type == 'press':
            execute_action('press', key=action.get('key', ''))

        elif action_type == 'hotkey':
            execute_action('hotkey', keys=action.get('keys', []))

        elif action_type == 'scroll':
            execute_action(
                f"scroll_{action.get('direction','down')}",
                amount=action.get('amount', 3)
            )

        elif action_type == 'wait':
            secs = action.get('seconds', 2)
            print(f"   Waiting {secs} seconds...")
            time.sleep(secs)

        # Save to history
        history.append(f"Step {step}: {action_type} - {reason}")

        # Small pause between actions (more human-like)
        time.sleep(0.8)

    print(f"\n⚠️  Max steps ({max_steps}) reached. Task may be incomplete.")
    return False


# ============================================================
#  MAIN — Test when run directly
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  RS Vision — Test Mode")
    print("=" * 50)
    print()
    print("What do you want to test?")
    print("  1 → Analyze current screen")
    print("  2 → Find element on screen")
    print("  3 → Run autonomous task")
    print()

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == "1":
        result = analyze_screen("Describe everything you see on this screen in detail")
        print(f"\nAI sees:\n{result}")

    elif choice == "2":
        element = input("What to find on screen? (e.g. 'the search box'): ")
        pos = find_element(element)
        if pos:
            print(f"Found at: {pos}")
        else:
            print("Not found")

    elif choice == "3":
        task = input("Enter task for RS to do autonomously: ")
        print("\n⚠️  RS will control your mouse and keyboard!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            run_task_autonomously(task)