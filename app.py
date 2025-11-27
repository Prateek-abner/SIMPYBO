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


def detect_language_choice(text: str):
    """
    Map user input to a language choice.
    Accepts:
      - suggestion values
      - numbers: 1 / 2
      - words: english / hinglish / hindi
    Returns "english", "hinglish" or None.
    """
    t = (text or "").strip().lower()

    english_tokens = {
        "1",
        "1.",
        "one",
        "mode_english",
        "easy english",
        "english",
        "english mode",
        "option 1",
        "1 easy english",
    }
    hinglish_tokens = {
        "2",
        "2.",
        "two",
        "mode_hinglish",
        "hinglish",
        "hindi",
        "hinglish mode",
        "option 2",
        "2 hinglish",
        "2 hinglish for indian users",
    }

    if t in english_tokens:
        return "english"
    if t in hinglish_tokens:
        return "hinglish"
    return None


def get_mode_selection(remind: bool = False):
    """
    Ask user to choose between Easy English and Hinglish modes.
    """
    if remind:
        intro = (
            "First choose how you want me to explain words:\n\n"
            "1️⃣ Easy English\n"
            "2️⃣ Hinglish for Indian users\n\n"
        )
    else:
        intro = (
            "👋 **Hi! I'm BoDH-S!**\n\n"
            "I turn tough words into easy explanations with examples.\n\n"
            "First, choose how you want answers:\n\n"
            "1️⃣ Easy English (simple meaning + example)\n"
            "2️⃣ Hinglish (Hindi + English meaning + example)\n\n"
        )

    return jsonify(
        {
            "replies": [
                {
                    "text": intro + "Tap an option below or type 1 / 2.",
                    "suggestions": [
                        {
                            "title": "1️⃣ Easy English",
                            "value": "1",
                        },
                        {
                            "title": "2️⃣ Hinglish for Indian users",
                            "value": "2",
                        },
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
            "✅ Mode set to **Easy English**.\n\n"
            "Now type any difficult word and I’ll explain it in simple English "
            "with a short example.\n\n"
            "Try: algorithm, warranty, refund, cryptocurrency."
        )
    else:
        text = (
            "✅ Mode set to **Hinglish**.\n\n"
            "Ab se main words ko Hinglish mein simple meaning + example ke saath "
            "samjhaunga.\n\n"
            "Try: movie, EMI, warranty, COD."
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
      - If mode not chosen, ask user to choose.
      - If user sends 1/2/english/hinglish, set mode.
      - Otherwise, treat message as word and explain in chosen mode.
    """
    if not engine:
        return jsonify({"replies": [{"text": "❌ BoDH-S is currently offline."}]}), 500

    data = request.get_json() or {}
    user = data.get("user", {}) or {}
    user_id = user.get("id", "anon")

    message = data.get("message", {}) or {}
    raw_text = (message.get("text") or "").strip()
    text = raw_text.lower()

    # Reset / menu
    if text in ["hi", "hello", "start", "help", "menu"]:
        user_sessions[user_id] = {"language": None}
        return get_mode_selection()

    # Language choice check first
    choice = detect_language_choice(text)
    if choice:
        user_sessions[user_id] = {"language": choice}
        return mode_selected_reply(choice)

    # If no text at all -> ask for mode
    if not text:
        return get_mode_selection()

    # Get user mode
    session = user_sessions.get(user_id, {})
    language = session.get("language")

    # If mode not chosen yet, force mode selection
    if language not in ["english", "hinglish"]:
        return get_mode_selection(remind=True)

    # Treat this as the word to explain
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
                            "Please type the word you want me to explain.\n"
                            "Example: algorithm, warranty, COD."
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
