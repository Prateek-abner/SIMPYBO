"""
SIMPYBO - Groq AI Engine
"""

import os
from groq import Groq
from dotenv import load_dotenv
from dataset_loader import DatasetLoader

load_dotenv()

class SimpyboAI:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY not found")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        
        print("📚 Loading datasets...")
        loader = DatasetLoader()
        self.examples = loader.load_examples()
        print(f"✅ Loaded {len(self.examples['english'])} English + {len(self.examples['hinglish'])} Hinglish")
    
    def explain_word(self, word: str, language: str = "english") -> dict:
        prompt = self._create_prompt(word, language)
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are Simpybo, an AI that explains words in very simple language."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=400,
                top_p=0.9
            )
            
            explanation = response.choices[0].message.content
            parsed = self._parse_response(explanation)
            
            return {
                "success": True,
                "word": word,
                "language": language,
                **parsed
            }
            
        except Exception as e:
            return {"success": False, "word": word, "error": str(e)}
    
    def _create_prompt(self, word: str, language: str) -> str:
        examples = self.examples[language][:3]
        
        if language == "english":
            prompt = "You are Simpybo. Explain words in VERY simple English.\n\n"
            prompt += "Examples from dictionary.json:\n\n"
            
            for i, ex in enumerate(examples, 1):
                prompt += f"{i}. Word: {ex['word']}\n"
                prompt += f"   Meaning: {ex['definition']}\n"
                prompt += f"   Example: {ex['example']}\n\n"
            
            prompt += f"Now explain: {word}\n\n"
            prompt += "Format:\n"
            prompt += "Simple Meaning: [one clear sentence]\n"
            prompt += "Example: [one practical example]\n"
            prompt += "Full Form: [if abbreviation, else N/A]"
        
        else:  # hinglish
            prompt = "You are Simpybo. Explain in Hinglish (Hindi + English mix).\n\n"
            prompt += "Examples from hinglish_upload_v1.json:\n\n"
            
            for i, ex in enumerate(examples, 1):
                prompt += f"{i}. Word: {ex.get('word', 'example')}\n"
                prompt += f"   Meaning: {ex.get('definition', '')}\n"
                prompt += f"   Example: {ex.get('example', '')}\n\n"
            
            prompt += f"Now explain: {word}\n\n"
            prompt += "Format:\n"
            prompt += "Simple Meaning: [Hinglish mein]\n"
            prompt += "Example: [Indian example]\n"
            prompt += "Full Form: [agar abbreviation hai]"
        
        return prompt
    
    def _parse_response(self, text: str) -> dict:
        result = {"simple_meaning": "", "example": "", "full_form": ""}
        
        lines = text.split('\n')
        current_field = None
        
        for line in lines:
            line = line.strip()
            
            if "simple meaning:" in line.lower():
                current_field = "simple_meaning"
                content = line.split(':', 1)[-1].strip()
                if content:
                    result["simple_meaning"] = content
            
            elif "example:" in line.lower():
                current_field = "example"
                content = line.split(':', 1)[-1].strip()
                if content:
                    result["example"] = content
            
            elif "full form:" in line.lower():
                current_field = "full_form"
                content = line.split(':', 1)[-1].strip()
                if content and content.lower() != "n/a":
                    result["full_form"] = content
            
            elif current_field and line and not line.startswith(('Simple', 'Example', 'Full')):
                if result[current_field]:
                    result[current_field] += " " + line
                else:
                    result[current_field] = line
        
        for key in result:
            result[key] = result[key].strip().strip('*').strip()
        
        if not result["simple_meaning"]:
            result["simple_meaning"] = text[:200]
        
        return result


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SIMPYBO - AI ENGINE TEST")
    print("="*60 + "\n")
    
    simpybo = SimpyboAI()
    
    tests = [
        ("algorithm", "english"),
        ("movie", "hinglish"),
        ("warranty", "english"),
        ("film", "hinglish")
    ]
    
    for word, lang in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {word} ({lang})")
        print('='*50)
        
        result = simpybo.explain_word(word, lang)
        
        if result['success']:
            print(f"✅ {result['simple_meaning']}")
            print(f"💡 {result['example']}")
        else:
            print(f"❌ {result['error']}")
    
    print("\n✅ Test complete!")
