"""

BoDH-S - Flask Server

"""

from flask import Flask, request, jsonify
from groq_engine import SimpyboAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "bodhs-2025")

print("🚀 Initializing BoDH-S...")
try:
    engine = SimpyboAI()
    print("✅ BoDH-S ready!")
except Exception as e:
    print(f"❌ Failed to initialize BoDH-S: {e}")
    engine = None

# In-memory user mode: { user_id: {"language": "english" | "hinglish"} }
user_sessions = {}

@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "status": "online",
            "bot_name": "BoDH-S",
            "version": "1.0",
            "powered_by": "Groq AI + Your Datasets",
            "datasets": "dictionary.json + hinglish_upload_v1.json",
        }
    )

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def is_greeting(text: str):
    """
    Detect if the text is a greeting.
    Returns True for: hi, hii, hiii, hello, hey, whatsup, wassup, start, help, menu, etc.
    """
    if not text:
        return False
    
    t = text.strip().lower()
    
    # Common greetings
    greetings = [
        "hi", "hii", "hiii", "hiiii",
        "hello", "helo", "hallo",
        "hey", "heyy", "heyyy",
        "whatsup", "whats up", "wassup", "watsup", "sup",
        "namaste", "namaskar",
        "start", "begin", "help", "menu",
        "hola", "yo"
    ]
    
    # Check exact match
    if t in greetings:
        return True
    
    # Check if starts with greeting (like "hiii there", "hello bot")
    for greeting in greetings:
        if t.startswith(greeting):
            return True
    
    return False


def detect_language_choice(text: str):
    """
    Map user input to a language choice.
    Accepted examples:
    - "1", "option 1", "easy english", "go with option 1", "english"
    - "2", "option 2", "hinglish", "ok go with option 2", "switch to option 2"
    Returns "english", "hinglish" or None.
    """
    if not text:
        return None
    
    t = text.strip().lower()
    
    # Exact matches first (buttons, plain numbers, single words)
    english_exact = {
        "1",
        "1.",
        "one",
        "mode_english",
        "easy english",
        "english",
        "english mode",
    }
    
    hinglish_exact = {
        "2",
        "2.",
        "two",
        "mode_hinglish",
        "hinglish",
        "hindi",
        "hinglish mode",
    }
    
    if t in english_exact:
        return "english"
    if t in hinglish_exact:
        return "hinglish"
    
    # Phrase-based detection (user types sentences)
    english_keywords = [
        "option 1",
        "go with 1",
        "go with option 1",
        "switch to option 1",
        "easy english",
        "english only",
    ]
    
    hinglish_keywords = [
        "option 2",
        "go with 2",
        "go with option 2",
        "switch to option 2",
        "hinglish",
        "hindi english",
        "indian users",
    ]
    
    if any(kw in t for kw in english_keywords):
        return "english"
    if any(kw in t for kw in hinglish_keywords):
        return "hinglish"
    
    return None


def get_mode_selection(remind: bool = False):
    """
    Ask user to choose between Easy English and Hinglish modes.
    Shows clickable buttons for option selection.
    """
    if remind:
        intro = (
            "⚠️ Please choose your preferred mode first:\n\n"
            "1️⃣ Easy English\n"
            "2️⃣ Hinglish for Indian users\n\n"
            "Tap a button below or type 1 / 2."
        )
    else:
        intro = (
            "👋 **Hi! I'm BoDH-S!**\n\n"
            "I turn tough words into easy explanations with examples.\n\n"
            "🌟 Choose how you want answers:\n\n"
            "1️⃣ **Easy English** - Simple meaning + example\n"
            "2️⃣ **Hinglish** - Hindi + English meaning + example\n\n"
            "Tap a button below or type 1 / 2."
        )
    
    return jsonify(
        {
            "replies": [
                {
                    "text": intro,
                    "suggestions": [
                        {"title": "1️⃣ Easy English", "value": "1"},
                        {"title": "2️⃣ Hinglish for Indian users", "value": "2"},
                    ],
                }
            ]
        }
    )


def mode_selected_reply(language: str):
    """
    Reply after the user selects a mode successfully.
    """
    if language == "english":
        text = (
            "✅ **Mode set to Easy English**.\n\n"
            "Now type any difficult word and I'll explain it in simple English "
            "with a short example.\n\n"
            "📝 For example: algorithm, warranty, refund, cryptocurrency."
        )
    else:
        text = (
            "✅ **Mode set to Hinglish**.\n\n"
            "Ab se main words ko Hinglish mein simple meaning + example ke saath "
            "samjhaunga.\n\n"
            "📝 For example: movie, EMI, warranty, COD."
        )
    
    return jsonify(
        {
            "replies": [
                {
                    "text": text,
                    "suggestions": [
                        {"title": "algorithm", "value": "algorithm"},
                        {"title": "warranty", "value": "warranty"},
                        {"title": "COD", "value": "COD"},
                    ],
                }
            ]
        }
    )


def format_success(result: dict):
    """
    Build Zoho-style response for a successful explanation.
    """
    word = (result.get("word") or "").upper()
    meaning = result.get("simple_meaning") or "Meaning not available."
    example = result.get("example") or "Example not available."
    full_form = result.get("full_form") or ""
    language = result.get("language") or "english"
    
    flag = "🇮🇳" if language == "hinglish" else "📖"
    
    text = f"{flag} **{word}**\n\n"
    if full_form:
        text += f"**Full Form:** {full_form}\n\n"
    text += f"**✏️ Simple Meaning:**\n{meaning}\n\n"
    text += f"**💡 Example:**\n{example}\n\n"
    text += "_- BoDH-S 🤖_"
    
    suggestions = [
        {"title": "🔍 Another word", "value": "start"},
        {"title": "Change mode", "value": "menu"},
    ]
    
    return jsonify({"replies": [{"text": text, "suggestions": suggestions}]})


def format_error(word: str):
    msg = (
        f"😔 Sorry! I couldn't explain **{word}**.\n\n"
        "Please check the spelling or try a different word."
    )
    return jsonify({"replies": [{"text": msg}]})


# ---------------------------------------------------------------------
# Webhook logic
# ---------------------------------------------------------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Main webhook endpoint for Zoho SalesIQ.
    Flow:
    1. If greeting detected -> Always show welcome + options if mode not set
    2. If mode choice detected (1/2) -> Set mode and show confirmation
    3. If mode is set -> Explain the word user typed
    """
    if not engine:
        return jsonify({"replies": [{"text": "❌ BoDH-S is currently offline."}]}), 500
    
    data = request.get_json() or {}
    user = data.get("user", {}) or {}
    user_id = user.get("id", "anon")
    message = data.get("message", {}) or {}
    raw_text = (message.get("text") or "").strip()
    text = raw_text.lower()
    
    # ============================================================
    # STEP 1: Check if it's a greeting first (hi, hello, whatsup, menu, etc.)
    # ============================================================
    if is_greeting(text):
        # Always reset and show options when greeting is detected
        user_sessions[user_id] = {"language": None}
        return get_mode_selection()
    
    # ============================================================
    # STEP 2: Check if this message is a mode choice (1 or 2)
    # ============================================================
    choice = detect_language_choice(text)
    if choice:
        user_sessions[user_id] = {"language": choice}
        return mode_selected_reply(choice)
    
    # ============================================================
    # STEP 3: If no text at all -> show welcome options
    # ============================================================
    if not text:
        return get_mode_selection()
    
    # ============================================================
    # STEP 4: Check if user has selected mode yet
    # ============================================================
    session = user_sessions.get(user_id, {})
    language = session.get("language")
    
    if language not in ["english", "hinglish"]:
        # Mode not selected yet, remind user to select mode first
        return get_mode_selection(remind=True)
    
    # ============================================================
    # STEP 5: Treat this message as the word/phrase to explain
    # ============================================================
    word = (
        text.replace("what is", "")
        .replace("meaning of", "")
        .replace("explain", "")
        .strip()
    )
    
    if not word:
        return jsonify(
            {
                "replies": [
                    {
                        "text": (
                            "Please type the word you want me to explain.\n\n"
                            "📝 Example: algorithm, warranty, COD."
                        )
                    }
                ]
            }
        )
    
    result = engine.explain_word(word, language)
    
    if result.get("success"):
        return format_success(result)
    else:
        return format_error(word)


# ---------------------------------------------------------------------
# Extra endpoints for debugging / API use
# ---------------------------------------------------------------------

@app.route("/explain", methods=["POST"])
def explain_api():
    """Direct HTTP API to test BoDH-S without Zoho."""
    if not engine:
        return jsonify({"error": "BoDH-S offline"}), 500
    
    try:
        data = request.get_json() or {}
        word = (data.get("word") or "").strip()
        language = (data.get("language") or "english").lower()
        
        if not word:
            return jsonify({"error": "Word required"}), 400
        
        if language not in ["english", "hinglish"]:
            language = "english"
        
        result = engine.explain_word(word, language)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def stats():
    if not engine:
        return jsonify({"error": "BoDH-S offline"}), 500
    
    return jsonify(
        {
            "bot_name": "BoDH-S",
            "datasets": engine.examples.get("metadata", {}),
            "english_examples": len(engine.examples.get("english", [])),
            "hinglish_examples": len(engine.examples.get("hinglish", [])),
            "model": engine.model,
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n🚀 Starting BoDH-S on port {port}...")
    print(f"📊 Status: {'Ready ✅' if engine else 'Offline ❌'}")
    print(f"🌐 URL: http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
