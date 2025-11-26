"""
SIMPYBO - Test Suite
"""

import requests
from groq_engine import SimpyboAI
from dataset_loader import DatasetLoader

BASE_URL = "http://localhost:5000"

def test_all():
    print("\n" + "="*70)
    print("🧪 SIMPYBO - COMPLETE TEST")
    print("="*70)
    
    # Test 1: Datasets
    print("\n[TEST 1] Datasets...")
    try:
        loader = DatasetLoader()
        examples = loader.load_examples()
        print(f"✅ English: {len(examples['english'])}")
        print(f"✅ Hinglish: {len(examples['hinglish'])}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: AI Engine
    print("\n[TEST 2] AI Engine...")
    try:
        simpybo = SimpyboAI()
        result = simpybo.explain_word("algorithm", "english")
        if result['success']:
            print(f"✅ {result['simple_meaning'][:50]}...")
        else:
            print(f"❌ {result['error']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: API (requires server running)
    print("\n[TEST 3] Flask API...")
    print("⚠️  Make sure server is running: python app.py")
    input("Press Enter when ready...")
    
    try:
        r = requests.get(f"{BASE_URL}/")
        if r.status_code == 200:
            print(f"✅ Health check: {r.json()['bot_name']}")
        
        r = requests.post(f"{BASE_URL}/explain", json={"word": "warranty", "language": "english"})
        if r.status_code == 200:
            print(f"✅ API test passed")
    except Exception as e:
        print(f"❌ API failed: {e}")
    
    print("\n✅ Testing complete!\n")

if __name__ == "__main__":
    test_all()
