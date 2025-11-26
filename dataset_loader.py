"""
SIMPYBO - Dataset Loader
Loads dictionary.json + hinglish_upload_v1.json
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import random

class DatasetLoader:
    def __init__(self):
        self.datasets_dir = Path("datasets")
        self.dictionary_path = self.datasets_dir / "dictionary.json"
        self.hinglish_path = self.datasets_dir / "hinglish_upload_v1.json"
        self.examples_path = self.datasets_dir / "examples.json"
    
    def load_english_dictionary(self, limit=100) -> List[Dict]:
        """Load dictionary.json (Webster's format)"""
        print("📚 Loading dictionary.json...")
        
        examples = []
        
        try:
            if not self.dictionary_path.exists():
                print("⚠️  dictionary.json not found!")
                return self._fallback_english()
            
            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ Found {len(data)} words in dictionary.json")
            
            count = 0
            for word, definition in data.items():
                if count >= limit:
                    break
                
                clean_def = definition.replace('\n', ' ').strip()
                if len(clean_def) > 150:
                    clean_def = clean_def[:147] + "..."
                
                examples.append({
                    'word': word.lower(),
                    'definition': clean_def,
                    'example': f"Example: The {word} is important."
                })
                count += 1
            
            print(f"✅ Loaded {len(examples)} words")
            return examples
            
        except Exception as e:
            print(f"⚠️  Error: {e}")
            return self._fallback_english()
    
    def load_hinglish_dataset(self, limit=100) -> List[Dict]:
        """Load hinglish_upload_v1.json"""
        print("🇮🇳 Loading hinglish_upload_v1.json...")
        
        examples = []
        
        try:
            if not self.hinglish_path.exists():
                print("⚠️  hinglish_upload_v1.json not found!")
                return self._fallback_hinglish()
            
            with open(self.hinglish_path, 'r', encoding='utf-8') as f:
                count = 0
                for line in f:
                    if count >= limit:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        if 'translation' in data:
                            trans = data['translation']
                            english = trans.get('en', '').strip()
                            hinglish = trans.get('hi_ng', '').strip()
                            
                            if english and hinglish:
                                words = english.lower().split()
                                meaningful = [w for w in words if len(w) > 3 and w not in ['what', 'whats', 'when', 'where', 'does', 'have', 'this', 'that', 'kind', 'name']]
                                word = meaningful[0] if meaningful else 'example'
                                
                                examples.append({
                                    'word': word,
                                    'input': english,
                                    'output': hinglish,
                                    'definition': hinglish,
                                    'example': english
                                })
                                count += 1
                    except json.JSONDecodeError:
                        continue
            
            print(f"✅ Loaded {len(examples)} Hinglish pairs")
            return examples
            
        except Exception as e:
            print(f"⚠️  Error: {e}")
            return self._fallback_hinglish()
    
    def _fallback_english(self) -> List[Dict]:
        return [
            {'word': 'algorithm', 'definition': 'Step-by-step procedure to solve a problem', 'example': 'A recipe is an algorithm'},
            {'word': 'warranty', 'definition': 'Promise to fix product if it breaks', 'example': '1 year warranty'},
            {'word': 'refund', 'definition': 'Money returned when product is returned', 'example': 'Full refund in 7 days'},
            {'word': 'discount', 'definition': 'Reduction in price', 'example': '50% discount'},
            {'word': 'invoice', 'definition': 'Bill showing what you bought', 'example': 'Save the invoice'}
        ]
    
    def _fallback_hinglish(self) -> List[Dict]:
        return [
            {'word': 'movie', 'definition': 'Film ka matlab picture hai jo cinema hall mein dikhate hain', 'example': 'What is the movie name', 'input': 'What is movie', 'output': 'Film matlab cinema'},
            {'word': 'COD', 'definition': 'Cash on Delivery - jab samaan aaye tab paise do', 'example': 'COD option choose karo', 'input': 'What is COD', 'output': 'COD matlab jab delivery aaye tab cash do'},
            {'word': 'EMI', 'definition': 'Easy Monthly Installment - har mahine thoda pay karo', 'example': 'EMI option available hai', 'input': 'Explain EMI', 'output': 'EMI matlab har mahine thoda thoda pay karo'},
            {'word': 'warranty', 'definition': 'Agar kharab ho toh company free theek karegi', 'example': 'Warranty period kitna hai', 'input': 'What is warranty', 'output': 'Warranty matlab agar kharab ho toh free repair'},
            {'word': 'discount', 'definition': 'Discount matlab kam price - asli price se kam', 'example': 'Discount kitna hai', 'input': 'What is discount', 'output': 'Discount matlab price kam ho gaya'}
        ]
    
    def create_few_shot_examples(self, num_examples=5):
        """Create examples for AI prompts"""
        print("\n🎯 Creating few-shot examples...")
        
        english_data = self.load_english_dictionary(limit=200)
        hinglish_data = self.load_hinglish_dataset(limit=200)
        
        english_examples = random.sample(english_data, min(num_examples, len(english_data)))
        hinglish_examples = random.sample(hinglish_data, min(num_examples, len(hinglish_data)))
        
        examples_data = {
            'english': english_examples[:num_examples],
            'hinglish': hinglish_examples[:num_examples],
            'metadata': {
                'bot_name': 'simpybo',
                'total_english': len(english_data),
                'total_hinglish': len(hinglish_data),
                'source': 'dictionary.json + hinglish_upload_v1.json'
            }
        }
        
        self.datasets_dir.mkdir(exist_ok=True)
        with open(self.examples_path, 'w', encoding='utf-8') as f:
            json.dump(examples_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Created examples.json with {num_examples} examples")
        print(f"📊 Total: {len(english_data)} English, {len(hinglish_data)} Hinglish")
        
        return examples_data
    
    def load_examples(self) -> Dict:
        """Load or create examples"""
        if self.examples_path.exists():
            with open(self.examples_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self.create_few_shot_examples()


if __name__ == "__main__":
    print("="*60)
    print("SIMPYBO - DATASET LOADER TEST")
    print("="*60)
    
    loader = DatasetLoader()
    examples = loader.create_few_shot_examples(num_examples=5)
    
    print("\n" + "="*60)
    print("ENGLISH EXAMPLES:")
    print("="*60)
    for ex in examples['english'][:3]:
        print(f"\n📖 {ex['word']}: {ex['definition'][:60]}...")
    
    print("\n" + "="*60)
    print("HINGLISH EXAMPLES:")
    print("="*60)
    for ex in examples['hinglish'][:3]:
        print(f"\n🇮🇳 {ex['word']}: {ex['definition'][:60]}...")
    
    print("\n✅ Dataset test complete!")
