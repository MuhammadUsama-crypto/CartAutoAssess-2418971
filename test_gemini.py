# # test_gemini.py
# import google.generativeai as genai

# # Your API key
# API_KEY = "AQ.Ab8RN6JZNdJ9oyBpln6Rtc_OJPxUFBDqMPL-z1Q4P9ovYYDl4w"

# print("Testing Gemini API...")
# print("=" * 40)

# # Configure the API
# genai.configure(api_key=API_KEY)

# # Try to list available models first
# print("\n1. Checking available models...")
# try:
#     models = genai.list_models()
#     available = []
#     for m in models:
#         if 'generateContent' in m.supported_generation_methods:
#             available.append(m.name)
#             print(f"   ✓ {m.name}")
    
#     if not available:
#         print("   ✗ No models found! Your API key might be invalid.")
#         exit()
        
# except Exception as e:
#     print(f"   ✗ Failed to list models: {e}")
#     print("   Your API key is likely INVALID or EXPIRED")
#     exit()

# # Try to generate content with gemini-pro
# print("\n2. Testing text generation with gemini-pro...")
# try:
#     model = genai.GenerativeModel('gemini-pro')
#     response = model.generate_content("Say 'API is working' in exactly 3 words")
#     print(f"   ✓ Success! Response: {response.text}")
#     print("   API IS WORKING FINE ✅")
    
# except Exception as e:
#     print(f"   ✗ Failed: {e}")
    
#     # Try alternative model names
#     print("\n3. Trying alternative model names...")
#     alt_models = ['gemini-1.5-pro', 'gemini-1.0-pro', 'models/gemini-pro']
    
#     for alt in alt_models:
#         try:
#             print(f"   Trying {alt}...")
#             model = genai.GenerativeModel(alt)
#             response = model.generate_content("Say 'OK'")
#             print(f"   ✓ WORKING with {alt} ✅")
#             print(f"   Use this model name: {alt}")
#             break
#         except:
#             print(f"   ✗ {alt} failed")
#     else:
#         print("\n   ❌ NO MODEL WORKING. Your API key is INVALID.")
#         print("   Get a new key from: https://makersuite.google.com/app/apikey")



# ----------------------------------------------------------------------------

# test_gemini_fixed.py
import google.generativeai as genai

API_KEY = "AQ.Ab8RN6JZNdJ9oyBpln6Rtc_OJPxUFBDqMPL-z1Q4P9ovYYDl4w"
genai.configure(api_key=API_KEY)

# Working model names from your list
working_models = [
    'gemini-2.0-flash',
    'gemini-2.5-flash', 
    'gemini-flash-latest',
    'gemini-2.0-flash-lite'
]

print("Testing working models...")
print("=" * 40)

for model_name in working_models:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Working' in one word")
        print(f"✓ {model_name} - SUCCESS: {response.text}")
        print(f"\nUSE THIS MODEL NAME: {model_name}")
        break
    except Exception as e:
        print(f"✗ {model_name} - Failed: {e}")