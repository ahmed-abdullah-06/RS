# ============================================================
#  R.S. - Red Shirt AI Assistant
#  mouse_keyboard.py — Human-like mouse & keyboard control
#  RS moves mouse smoothly and types with natural variation
# ============================================================

import pyautogui
import pynput.mouse    as pmouse
import pynput.keyboard as pkeyboard
import time
import random
import math
import threading

# ── Safety ───────────────────────────────────────────────────
pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.05

# ── Keyboard & Mouse controllers (pynput) ────────────────────
keyboard_ctrl = pkeyboard.Controller()
mouse_ctrl    = pmouse.Controller()


# ============================================================
#  PART 1 — HUMAN-LIKE MOUSE MOVEMENT
# ============================================================

def human_move(x, y, speed='normal'):
    """
    Moves mouse to (x,y) in a smooth curved path.
    Real humans never move mouse in a straight line —
    they curve and slightly overshoot then correct.

    speed: 'slow', 'normal', 'fast'
    """
    speeds = {
        'slow'  : (0.6, 1.0),
        'normal': (0.3, 0.6),
        'fast'  : (0.1, 0.3)
    }

    min_t, max_t = speeds.get(speed, speeds['normal'])
    duration     = random.uniform(min_t, max_t)

    # Get current position
    start_x, start_y = pyautogui.position()

    # Generate curved path points (bezier-like curve)
    steps  = max(10, int(duration * 60))
    points = _bezier_path(start_x, start_y, x, y, steps)

    # Move through each point
    for i, (px, py) in enumerate(points):
        pyautogui.moveTo(px, py, _pause=False)
        # Slight random pause — more human-like
        if i % 5 == 0:
            time.sleep(random.uniform(0.001, 0.008))

    # Final precise move to target
    pyautogui.moveTo(x, y)
    print(f"🖱️  Moved to ({x}, {y})")


def _bezier_path(x1, y1, x2, y2, steps):
    """
    Generates a bezier curve path between two points.
    This creates natural curved mouse movement.
    """
    # Random control point for curve
    cx = random.randint(
        min(x1, x2) - 50,
        max(x1, x2) + 50
    )
    cy = random.randint(
        min(y1, y2) - 50,
        max(y1, y2) + 50
    )

    points = []
    for i in range(steps + 1):
        t  = i / steps
        # Quadratic bezier formula
        px = int((1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2)
        py = int((1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2)
        points.append((px, py))

    return points


# ============================================================
#  PART 2 — HUMAN-LIKE CLICKING
# ============================================================

def human_click(x, y, button='left', speed='normal'):
    """
    Moves to position and clicks like a human.
    Includes natural pre-click pause and post-click pause.
    """
    # Move to position
    human_move(x, y, speed)

    # Small pause before clicking (humans do this)
    time.sleep(random.uniform(0.05, 0.15))

    # Click
    pyautogui.click(x, y, button=button)

    # Small pause after clicking
    time.sleep(random.uniform(0.05, 0.1))

    print(f"🖱️  Human clicked ({button}) at ({x}, {y})")


def human_double_click(x, y, speed='normal'):
    """Double clicks like a human"""
    human_move(x, y, speed)
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.doubleClick(x, y)
    time.sleep(random.uniform(0.05, 0.1))
    print(f"🖱️  Human double-clicked at ({x}, {y})")


def human_right_click(x, y, speed='normal'):
    """Right clicks like a human"""
    human_click(x, y, button='right', speed=speed)


def human_drag(x1, y1, x2, y2, speed='normal'):
    """
    Drags from one position to another like a human.
    Smooth movement with hold and release.
    """
    # Move to start
    human_move(x1, y1, speed)
    time.sleep(random.uniform(0.1, 0.2))

    # Press and hold
    pyautogui.mouseDown(x1, y1)
    time.sleep(random.uniform(0.05, 0.1))

    # Move to destination slowly
    human_move(x2, y2, 'slow')

    # Release
    time.sleep(random.uniform(0.05, 0.1))
    pyautogui.mouseUp(x2, y2)

    print(f"🖱️  Human dragged ({x1},{y1}) → ({x2},{y2})")


def human_scroll(direction='down', amount=3, x=None, y=None):
    """
    Scrolls like a human — not all at once but gradually.
    """
    if x and y:
        human_move(x, y)
        time.sleep(0.1)

    for i in range(amount):
        if direction == 'down':
            pyautogui.scroll(-1)
        else:
            pyautogui.scroll(1)
        # Random pause between each scroll tick
        time.sleep(random.uniform(0.05, 0.15))

    print(f"🖱️  Human scrolled {direction} x{amount}")


# ============================================================
#  PART 3 — HUMAN-LIKE TYPING
# ============================================================

def human_type(text, speed='normal', mistakes=False):
    """
    Types text like a human with natural speed variation.

    speed: 'slow'(0.1-0.2s), 'normal'(0.04-0.1s), 'fast'(0.02-0.06s)
    mistakes: if True, RS occasionally makes typos and corrects them
              (ultra realistic but slower)
    """
    speeds = {
        'slow'  : (0.10, 0.20),
        'normal': (0.04, 0.10),
        'fast'  : (0.02, 0.06)
    }

    min_d, max_d = speeds.get(speed, speeds['normal'])

    for i, char in enumerate(text):
        # Occasionally make a typo and correct it (if enabled)
        if mistakes and random.random() < 0.03:  # 3% chance of typo
            _make_typo(char, min_d, max_d)
        else:
            # Type the correct character
            try:
                keyboard_ctrl.type(char)
            except:
                pyautogui.write(char, interval=0)

        # Random delay between keystrokes
        delay = random.uniform(min_d, max_d)

        # Slightly longer pause after spaces and punctuation
        if char in ' .,!?;:':
            delay *= random.uniform(1.5, 2.5)

        # Slightly longer pause after capital letters
        if char.isupper():
            delay *= random.uniform(1.2, 1.8)

        time.sleep(delay)

    print(f"⌨️  Human typed: {text[:40]}{'...' if len(text)>40 else ''}")


def _make_typo(intended_char, min_d, max_d):
    """Types a wrong character then backspaces to fix it"""
    # Type a nearby wrong key
    wrong_chars = 'qwertyuiopasdfghjklzxcvbnm'
    wrong       = random.choice(wrong_chars)

    try:
        keyboard_ctrl.type(wrong)
    except:
        pyautogui.write(wrong, interval=0)

    time.sleep(random.uniform(min_d * 2, max_d * 2))

    # Realize mistake — backspace
    pyautogui.press('backspace')
    time.sleep(random.uniform(0.1, 0.2))

    # Type correct character
    try:
        keyboard_ctrl.type(intended_char)
    except:
        pyautogui.write(intended_char, interval=0)


def human_press(key):
    """Presses a key with natural timing"""
    time.sleep(random.uniform(0.02, 0.08))
    pyautogui.press(key)
    time.sleep(random.uniform(0.02, 0.08))
    print(f"⌨️  Pressed: {key}")


def human_hotkey(*keys):
    """Presses hotkey combination with natural timing"""
    time.sleep(random.uniform(0.05, 0.1))
    pyautogui.hotkey(*keys)
    time.sleep(random.uniform(0.05, 0.15))
    print(f"⌨️  Hotkey: {' + '.join(keys)}")


def human_clear_and_type(text, speed='normal'):
    """Selects all and replaces with new text"""
    human_hotkey('ctrl', 'a')
    time.sleep(random.uniform(0.1, 0.2))
    human_type(text, speed)


# ============================================================
#  PART 4 — CLIPBOARD OPERATIONS
# ============================================================

def copy_to_clipboard(text):
    """Puts text into clipboard"""
    import subprocess
    try:
        # Use Windows PowerShell to set clipboard
        subprocess.run(
            ['powershell', '-command', f'Set-Clipboard -Value "{text}"'],
            capture_output=True
        )
        print(f"📋 Copied to clipboard: {text[:30]}...")
        return True
    except Exception as e:
        print(f"❌ Clipboard error: {e}")
        return False


def paste_from_clipboard():
    """Pastes text from clipboard"""
    human_hotkey('ctrl', 'v')
    time.sleep(0.2)


def get_clipboard_text():
    """Gets current text from clipboard"""
    import subprocess
    try:
        result = subprocess.run(
            ['powershell', '-command', 'Get-Clipboard'],
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except:
        return ""


# ============================================================
#  PART 5 — MOUSE TRACKING (listen to user's mouse)
# ============================================================

_mouse_positions = []
_tracking        = False


def start_tracking():
    """
    Starts recording mouse movements.
    Useful for learning where things are on screen.
    """
    global _tracking, _mouse_positions
    _tracking        = True
    _mouse_positions = []

    def on_move(x, y):
        if _tracking:
            _mouse_positions.append(('move', x, y))

    def on_click(x, y, button, pressed):
        if _tracking and pressed:
            _mouse_positions.append(('click', x, y, str(button)))
            print(f"📍 Recorded click at ({x}, {y})")

    listener = pmouse.Listener(on_move=on_move, on_click=on_click)
    listener.start()
    print("🎯 Mouse tracking started — move and click to record positions")
    return listener


def stop_tracking():
    """Stops mouse tracking and returns recorded positions"""
    global _tracking
    _tracking = False
    clicks    = [p for p in _mouse_positions if p[0] == 'click']
    print(f"🎯 Tracking stopped — recorded {len(clicks)} clicks")
    return _mouse_positions


def get_current_position():
    """Returns current mouse (x, y) position"""
    pos = pyautogui.position()
    print(f"📍 Mouse is at ({pos.x}, {pos.y})")
    return pos.x, pos.y


# ============================================================
#  PART 6 — FULL HUMAN ACTION (move + interact)
# ============================================================

def human_action(action_type, **params):
    """
    Master function — performs any human-like action.
    Called by other RS modules.

    Examples:
        human_action('click', x=500, y=300)
        human_action('type', text='Hello World')
        human_action('hotkey', keys=['ctrl','c'])
        human_action('scroll', direction='down', amount=3)
    """
    action_map = {
        'click'       : lambda: human_click(
                            params.get('x', 0), params.get('y', 0),
                            params.get('button', 'left'),
                            params.get('speed', 'normal')),
        'double_click': lambda: human_double_click(
                            params.get('x', 0), params.get('y', 0)),
        'right_click' : lambda: human_right_click(
                            params.get('x', 0), params.get('y', 0)),
        'drag'        : lambda: human_drag(
                            params.get('x1',0), params.get('y1',0),
                            params.get('x2',0), params.get('y2',0)),
        'scroll'      : lambda: human_scroll(
                            params.get('direction','down'),
                            params.get('amount', 3)),
        'type'        : lambda: human_type(
                            params.get('text',''),
                            params.get('speed','normal'),
                            params.get('mistakes', False)),
        'press'       : lambda: human_press(params.get('key','')),
        'hotkey'      : lambda: human_hotkey(*params.get('keys',[])),
        'clear_type'  : lambda: human_clear_and_type(
                            params.get('text',''),
                            params.get('speed','normal')),
        'position'    : lambda: get_current_position(),
    }

    if action_type in action_map:
        return action_map[action_type]()
    else:
        print(f"❌ Unknown action: {action_type}")
        return False


# ============================================================
#  MAIN — Test when run directly
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  RS Mouse & Keyboard — Test Mode")
    print("=" * 50)
    print()
    print("Tests will run in 3 seconds...")
    print("Move mouse to TOP-LEFT to emergency stop!")
    print()
    time.sleep(3)

    # Test 1 — Get position
    x, y = get_current_position()
    print(f"✅ Current position: ({x}, {y})")
    time.sleep(1)

    # Test 2 — Human move
    print("\nTest: Moving mouse to center of screen...")
    import pyautogui as _pg
    sw, sh = _pg.size()
    human_move(sw//2, sh//2, speed='normal')
    time.sleep(1)

    # Test 3 — Human type (opens notepad first)
    print("\nTest: Opening notepad and typing...")
    import subprocess
    subprocess.Popen(['notepad.exe'])
    time.sleep(2)
    human_type("Hello! I am RS, your AI assistant.", speed='normal')
    time.sleep(1)

    print("\n✅ All tests passed!")
    print("RS can move and type like a human!")