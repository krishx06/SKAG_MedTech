#!/usr/bin/env python3
"""
Simple test for Gemini API using direct REST API (most reliable).
"""
import os
import requests
from pathlib import Path

def test_gemini_rest():
    """Test Gemini using REST API directly"""
    
    print("🔍 Testing Google Gemini API (REST)...\n")
    
    # Load .env
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"📂 Loaded .env from: {env_path}\n")
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found")
        print("Get your free API key from: https://aistudio.google.com/api key")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Test with gemini-2.5-flash (fast and available in v1 API)
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Explain in one sentence what a hospital tri age system does."
            }]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 100
        }
    }
    
    print(f"\n🧪 Sending test request to {model}...")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                
                print(f"\n✅ Success! Gemini Response:")
                print(f"📝 {text}")
                
                print("\n" + "="*60)
                print("✨ Gemini API is working correctly!")
                print("="*60)
                print("\n💡 Recommended models for AdaptiveCare:")
                print("   ✓ gemini-2.5-flash (Fastest, latest)")
                print("   ✓ gemini-2.0-flash (Fast, stable)")
                print("   ✓ gemini-2.5-pro (Most capable)")
                print("\n🔥 Free Tier: 15 requests/min, 1500/day")
                
                return True
            else:
                print(f"❌ Unexpected response format: {data}")
                return False
        else:
            print(f"❌ API Error ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = test_gemini_rest()
    sys.exit(0 if success else 1)
