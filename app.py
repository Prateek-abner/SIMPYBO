"""
SIMPYBO - Flask Server
"""

from flask import Flask, request, jsonify
from groq_engine import SimpyboAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'simpybo-2025')

print("🚀 Initializing Simpybo...")
try:
    simpybo = SimpyboAI()
    print("✅ Simpybo ready!")
except Exception as e:
    print(f"❌ Failed: {e}")
    simpybo = None

user_sessions = {}

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "bot_name": "Simpybo",
        "version": "1.0",
        "powered_by": "Groq AI + Your Datasets",
        "datasets": "dictionary.json + hinglish_upload_v1.json"
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    if not simpybo:
        return jsonify({"replies": [{"text": "❌ Simpybo offline"}]}), 500
    
    try:
        data = request.get_json()
        user_id = data.get('user', {}).get('id', 'anon')
        user_message = data.get('message', {}).get('text', '').strip().lower()
        
        if not user_message:
            return get_welcome()
        
        if user_message in ['hi', 'hello', 'start', 'help']:
            user_sessions[user_id] = {'language': 'english'}
            return get_welcome()
        
        if 'hinglish' in user_message or 'hindi' in user_message:
            user_sessions[user_id] = {'language': 'hinglish'}
            return jsonify({
                "replies": [{
                    "text": "🇮🇳 Perfect! Ab Hinglish mein samjhaunga.\n\nKoi bhi word type karo!",
                    "suggestions": [
                        {"title": "Movie", "value": "movie"},
                        {"title": "COD", "value": "COD"},
                        {"title": "English", "value": "english"}
                    ]
                }]
            })
        
        if user_message == 'english':
            user_sessions[user_id] = {'language': 'english'}
            return jsonify({
                "replies": [{
                    "text": "✅ Switched to English!\n\nType any word!",
                    "suggestions": [
                        {"title": "Algorithm", "value": "algorithm"},
                        {"title": "Warranty", "value": "warranty"},
                        {"title": "Hinglish", "value": "hinglish"}
                    ]
                }]
            })
        
        language = user_sessions.get(user_id, {}).get('language', 'english')
        word = user_message.replace('what is', '').replace('explain', '').strip()
        
        result = simpybo.explain_word(word, language)
        
        if result['success']:
            return format_success(result, user_id)
        else:
            return format_error(word, language)
    
    except Exception as e:
        return jsonify({"replies": [{"text": f"😔 Error: {e}"}]}), 500

@app.route('/explain', methods=['POST'])
def explain_api():
    if not simpybo:
        return jsonify({"error": "Offline"}), 500
    
    try:
        data = request.get_json()
        word = data.get('word', '').strip()
        language = data.get('language', 'english').lower()
        
        if not word:
            return jsonify({"error": "Word required"}), 400
        
        result = simpybo.explain_word(word, language)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    if not simpybo:
        return jsonify({"error": "Offline"}), 500
    
    return jsonify({
        "bot_name": "Simpybo",
        "datasets": simpybo.examples.get('metadata', {}),
        "english_examples": len(simpybo.examples.get('english', [])),
        "hinglish_examples": len(simpybo.examples.get('hinglish', [])),
        "model": simpybo.model
    })

def get_welcome():
    return jsonify({
        "replies": [{
            "text": "👋 **Hi! I'm Simpybo!**\n\nI explain difficult words simply! ✨\n\n**Features:**\n• Simple explanations\n• Real examples\n• Hinglish support 🇮🇳\n\n**Powered by:**\n• Your dictionary.json\n• Your hinglish_upload_v1.json\n• Groq AI\n\nType any word! 🔤",
            "suggestions": [
                {"title": "Algorithm", "value": "algorithm"},
                {"title": "🇮🇳 Hinglish", "value": "hinglish"},
                {"title": "Stats", "value": "/stats"}
            ]
        }]
    })

def format_success(result, user_id):
    word = result['word'].upper()
    meaning = result['simple_meaning']
    example = result['example']
    full_form = result.get('full_form', '')
    language = result['language']
    
    flag = "🇮🇳" if language == "hinglish" else "📖"
    text = f"{flag} **{word}**\n\n"
    
    if full_form:
        text += f"**Full Form:** {full_form}\n\n"
    
    text += f"**✏️ Meaning:**\n{meaning}\n\n"
    text += f"**💡 Example:**\n{example}\n\n"
    text += "_- Simpybo 🤖_"
    
    suggestions = [
        {"title": "🔍 Another", "value": "explain"},
        {"title": "🔄 Switch", "value": "hinglish" if language == "english" else "english"},
        {"title": "🏠 Menu", "value": "start"}
    ]
    
    return jsonify({"replies": [{"text": text, "suggestions": suggestions}]})

def format_error(word, language):
    text = f"😔 Sorry! Couldn't explain **{word}**.\n\nCheck spelling or try another word!"
    return jsonify({"replies": [{"text": text}]})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Starting on port {port}...")
    print(f"📊 Status: {'Ready ✅' if simpybo else 'Offline ❌'}")
    print(f"🌐 URL: http://localhost:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=True)
