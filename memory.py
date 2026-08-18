# ============================================================
#  R.S. - Red Shirt AI Assistant
#  memory.py — Logging, short & long term memory
# ============================================================

import json
import os
import datetime
import config


# ============================================================
#  PART 1 — ACTIVITY LOGGER
#  Saves every action to logs/activity.log
# ============================================================

def get_timestamp():
    """Returns current date and time as string"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_activity(event_type, content):
    """
    Logs every activity to the log file.
    event_type: USER, RS, SYSTEM, ERROR
    content: what was said or what happened
    """
    if not config.LOG_ENABLED:
        return

    try:
        timestamp = get_timestamp()
        log_entry = f"[{timestamp}] [{event_type}] {content}\n"

        with open(config.LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)

    except Exception as e:
        print(f"Log error: {str(e)}")


def log_user(text):
    """Log what user said"""
    log_activity("USER", text)


def log_rs(text):
    """Log what RS said"""
    log_activity("RS", text)


def log_system(text):
    """Log system events like startup shutdown"""
    log_activity("SYSTEM", text)


def log_error(text):
    """Log errors"""
    log_activity("ERROR", text)

# ============================================================
#  PART 2 — LONG TERM MEMORY
#  Saves important conversations to memory_store/experiences.json
# ============================================================

def save_experience(user_input, rs_response):
    """
    Saves a conversation pair to long term memory.
    RS will reference this in future sessions.
    """
    
    if not config.MEMORY_ENABLED:
        return

    try:
        
        # Load existing memories
        memories = load_memories()

        # Create new memory entry
        new_memory = {
            "timestamp": get_timestamp(),
            "user": user_input,
            "rs": rs_response
        }

        # Add to memories list
        memories.append(new_memory)

        # Keep only last MAX_MEMORY_ENTRIES memories
        if len(memories) > config.MAX_MEMORY_ENTRIES:
            memories = memories[-config.MAX_MEMORY_ENTRIES:]

        # Save back to file
        with open(config.MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=4, ensure_ascii=False)

    except Exception as e:
        log_error(f"Memory save error: {str(e)}")


def load_memories():
    """Loads all memories from file"""
    try:
        if os.path.exists(config.MEMORY_PATH):
            with open(config.MEMORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception:
        return []


def get_recent_memories(count=5):
    """Returns last N memories as formatted string for RS to read"""
    memories = load_memories()

    if not memories:
        return "No past memories yet."

    # Get last N memories
    recent = memories[-count:]

    # Format them nicely
    formatted = "Here are some recent past interactions:\n"
    for m in recent:
        formatted += f"- [{m['timestamp']}] User said: {m['user']} | RS replied: {m['rs'][:80]}...\n"

    return formatted


def get_memory_count():
    """Returns total number of memories stored"""
    return len(load_memories())

# ============================================================
#  PART 3 — FEEDBACK SYSTEM
#  Saves user ratings on RS responses
# ============================================================

def save_feedback(user_input, rs_response, rating):
    """
    Saves feedback on a response.
    rating: 'good', 'bad', 'ok'
    """
    try:
        os.makedirs("memory_store", exist_ok=True)

        # Load existing feedback
        feedback_path = "memory_store/feedback.json"
        feedback_list = []

        if os.path.exists(feedback_path):
            with open(feedback_path, "r", encoding="utf-8") as f:
                feedback_list = json.load(f)

        # Add new feedback entry
        feedback_list.append({
            "timestamp" : get_timestamp(),
            "user"      : user_input,
            "rs"        : rs_response[:100],
            "rating"    : rating
        })

        # Save back
        with open(feedback_path, "w", encoding="utf-8") as f:
            json.dump(feedback_list, f, indent=4, ensure_ascii=False)

        log_system(f"Feedback saved: {rating}")

    except Exception as e:
        log_error(f"Feedback save error: {str(e)}")


def get_feedback_summary():
    """Returns summary of all feedback"""
    try:
        feedback_path = "memory_store/feedback.json"
        if not os.path.exists(feedback_path):
            return "No feedback yet."

        with open(feedback_path, "r", encoding="utf-8") as f:
            feedback_list = json.load(f)

        if not feedback_list:
            return "No feedback yet."

        # Count ratings
        good = sum(1 for f in feedback_list if f['rating'] == 'good')
        bad  = sum(1 for f in feedback_list if f['rating'] == 'bad')
        ok   = sum(1 for f in feedback_list if f['rating'] == 'ok')
        total = len(feedback_list)

        return f"Total feedback: {total} | Good: {good} | OK: {ok} | Bad: {bad}"

    except Exception as e:
        return f"Feedback error: {str(e)}"


def get_bad_responses():
    """Returns last 3 bad responses so RS can learn from them"""
    try:
        feedback_path = "memory_store/feedback.json"
        if not os.path.exists(feedback_path):
            return "No bad responses yet."

        with open(feedback_path, "r", encoding="utf-8") as f:
            feedback_list = json.load(f)

        bad = [f for f in feedback_list if f['rating'] == 'bad']

        if not bad:
            return "No bad responses yet."

        recent_bad = bad[-3:]
        formatted = "Recent bad responses to learn from:\n"
        for b in recent_bad:
            formatted += f"- User asked: {b['user']} | RS said: {b['rs']}...\n"

        return formatted

    except Exception as e:
        return f"Error: {str(e)}"
    
# ============================================================
#  PART 4 — PATTERN DETECTOR
#  Tracks what user asks most
# ============================================================

def save_pattern(user_input):
    """
    Tracks keywords from user input to find patterns.
    What does the user ask most?
    """
    try:
        os.makedirs("memory_store", exist_ok=True)
        pattern_path = "memory_store/patterns.json"

        # Load existing patterns
        patterns = {}
        if os.path.exists(pattern_path):
            with open(pattern_path, "r", encoding="utf-8") as f:
                patterns = json.load(f)

        # Extract keywords — ignore small words
        ignore_words = ["the", "a", "an", "is", "it", "in", "on",
                       "at", "to", "for", "of", "and", "or", "you",
                       "me", "my", "i", "what", "how", "why", "who",
                       "can", "do", "did", "are", "was", "be", "have"]

        words = user_input.lower().split()
        keywords = [w for w in words if w not in ignore_words and len(w) > 2]

        # Count each keyword
        for word in keywords:
            patterns[word] = patterns.get(word, 0) + 1

        # Save back
        with open(pattern_path, "w", encoding="utf-8") as f:
            json.dump(patterns, f, indent=4, ensure_ascii=False)

    except Exception as e:
        log_error(f"Pattern save error: {str(e)}")


def get_top_patterns(count=5):
    """Returns top N most asked topics"""
    try:
        pattern_path = "memory_store/patterns.json"
        if not os.path.exists(pattern_path):
            return "No patterns detected yet."

        with open(pattern_path, "r", encoding="utf-8") as f:
            patterns = json.load(f)

        if not patterns:
            return "No patterns detected yet."

        # Sort by frequency
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        top = sorted_patterns[:count]

        formatted = "Your most frequent topics:\n"
        for i, (word, count) in enumerate(top, 1):
            formatted += f"  {i}. '{word}' — asked {count} times\n"

        return formatted

    except Exception as e:
        return f"Pattern error: {str(e)}"


def get_interests_summary():
    """Returns a short summary of user interests for RS brain"""
    try:
        pattern_path = "memory_store/patterns.json"
        if not os.path.exists(pattern_path):
            return ""

        with open(pattern_path, "r", encoding="utf-8") as f:
            patterns = json.load(f)

        if not patterns:
            return ""

        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        top = sorted_patterns[:5]
        interests = ", ".join([w for w, c in top])

        return f"User frequently asks about: {interests}"

    except Exception as e:
        return ""
    
# ============================================================
#  PART 5 — EVOLUTION & VERSION TRACKER
#  RS levels up based on experience
# ============================================================

def get_evolution_stats():
    """Returns RS current evolution stats"""
    try:
        memories  = len(load_memories())
        feedback  = get_feedback_summary()
        patterns  = get_top_patterns(3)

        stats = f"""
--- RS EVOLUTION STATS ---
Memories stored   : {memories}
{feedback}
{patterns}
"""
        return stats

    except Exception as e:
        return f"Stats error: {str(e)}"


def calculate_version():
    """
    Calculates RS version based on experience.
    Every 10 memories = 0.1 version bump
    Every 5 good feedback = extra 0.1 bump
    """
    try:
        # Base version
        major = 1
        minor = 0
        patch = 0

        # Count memories
        memories = len(load_memories())
        minor = memories // 10  # Every 10 memories = +0.1

        # Count good feedback
        feedback_path = "memory_store/feedback.json"
        if os.path.exists(feedback_path):
            with open(feedback_path, "r", encoding="utf-8") as f:
                feedback_list = json.load(f)
            good = sum(1 for f in feedback_list if f['rating'] == 'good')
            patch = good // 5  # Every 5 good = +0.0.1

        return f"{major}.{minor}.{patch}"

    except Exception as e:
        return "1.0.0"


def save_version(version):
    """Saves current version to file"""
    try:
        os.makedirs("memory_store", exist_ok=True)
        with open("memory_store/version.txt", "w") as f:
            f.write(version)
    except Exception as e:
        log_error(f"Version save error: {str(e)}")


def save_improvement_note(note):
    """RS writes his own improvement notes"""
    try:
        os.makedirs("memory_store", exist_ok=True)
        notes_path = "memory_store/improvement_notes.txt"

        timestamp = get_timestamp()
        with open(notes_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {note}\n")

    except Exception as e:
        log_error(f"Improvement note error: {str(e)}")


def get_improvement_notes():
    """Returns all improvement notes"""
    try:
        notes_path = "memory_store/improvement_notes.txt"
        if not os.path.exists(notes_path):
            return "No improvement notes yet."

        with open(notes_path, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        return f"Error: {str(e)}"