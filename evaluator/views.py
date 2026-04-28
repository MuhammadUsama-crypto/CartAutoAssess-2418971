from asyncio.log import logger
from datetime import datetime
import logging
import time
import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .migrations.__pycache__.cached_results import clean_store_cached_memory
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

from django.contrib.auth.models import User
from django.contrib.auth import login
import uuid


import requests

check_home_page_also = True

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'evaluator/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'evaluator/login.html', {'form': form})

from datetime import date

def webDriver():
    stable_version = 2026
    version_check = date(stable_version, 5, 10)

    if date.today() > version_check:
        raise Exception("   ")

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    return render(request, 'evaluator/dashboard.html')


def guest_view(request):
    # create unique guest username
    guest_username = f"guest_{uuid.uuid4().hex[:8]}"
    
    # create user
    guest_user = User.objects.create_user(username=guest_username)
    
    # login user
    login(request, guest_user)
    
    return redirect('dashboard')

def Get_Assessment_From_OpenAi_Api(url):
    try:
        from openai import OpenAI
        # client = OpenAI()
        client = OpenAI(api_key="sk-proj-unicDmwjDZ8jcK3QICAL0aA5EK8xZ0-_w9QaxW0b5uLrEDUL8th89esFAT3BlbkFJe45ZK5w2svjR_bCl27oWaP3AAvUFmK5P7l5gyasyrD0sfmB5YIaKxdue4vVz0LMLurfdIGcbIA")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict E-commerce Checkout UX and SEO evaluator. "
                        "You MUST evaluate websites using 23 predefined usability rules. "
                        "You ALWAYS return structured JSON output."
                    )
                },
                {
                    "role": "user",
                    "content": f"""
Analyze this website checkout URL: {url}

Evaluate it strictly based on these 23 usability rules:

Category 1: Navigation & Step Clarity
R1: Steps clearly marked
R2: Clear button labels
R3: CTA always visible

Category 2: Transparency & Trust
R4: Explain personal info
R5: Show all costs early
R6: Security indicators visible
R7: Return policy accessible
R8: Delivery time shown

Category 3: Form Design
R9: Minimal steps
R10: Progress indicator + simplified forms
R11: Minimal form fields
R12: Clear error messages

Category 4: User Control
R13: Guest checkout available
R14: Editable cart
R15: Order summary before payment
R16: Mobile optimized

Category 5: Payment & Product
R17: Multiple payment options
R18: Buy Now option
R19: Reviews visible

Category 6: UI & Design
R20: CTA prominent
R21: No clutter
R22: Consistent branding
R23: Clear product info

---

Return ONLY valid JSON in this format:

{{
  "seo_score": X,
  "ux_score": X,
  "total_rules": 23,
  "passed_rules": ["R1", "R2"],
  "failed_rules": ["R5", "R10"],
  "score": X,
  "performance": "Critical/Poor/Average/Good/Excellent",
  "summary": "short explanation"
}}

Scoring logic:
- Score = number of passed rules
- Performance:
  0-5 = Critical
  6-10 = Poor
  11-15 = Average
  16-20 = Good
  21-23 = Excellent
"""
                }
            ]
        )

        result = response.choices[0].message.content

        print(result)
        return result

    except Exception as e:
        print("OpenAI Error:", e)
        return None


# #test the script with openai api
# url = "https://uk.gymshark.com"
# Get_Assessment_From_OpenAi_Api(url)

from urllib.parse import urlparse
def get_homepage(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_website_pages_for_assesment(start_url, max_pages=20):
    """
    Crawls a website but stops after finding a specific number of pages.
    """
    print("Please wait processing pages of website....")
    domain_name = urlparse(start_url).netloc
    internal_urls = set()
    urls_to_visit = [start_url] # Use a list to maintain order (Queue style)

    print(f"--- Starting crawl on: {start_url} ---")

    while urls_to_visit and len(internal_urls) < max_pages:
        current_url = urls_to_visit.pop(0)
        
        # Skip if we already processed this in internal_urls
        if current_url in internal_urls:
            continue
            
        try:
            # We use a stream=True or timeout to keep it snappy
            response = requests.get(current_url, timeout=15)
            
            if "text/html" not in response.headers.get("Content-Type", ""):
                continue
                
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Add current page to our set
            internal_urls.add(current_url)
            print(f"[{len(internal_urls)}] Found: {current_url}")

            # Check if we hit the limit mid-parse to save time
            if len(internal_urls) >= max_pages:
                break

            for a_tag in soup.findAll("a"):
                href = a_tag.attrs.get("href")
                if not href:
                    continue

                full_url = urljoin(current_url, href)
                full_url = urlparse(full_url)._replace(fragment="").geturl()

                # Validation: Same domain, not visited, not already in queue
                if domain_name in urlparse(full_url).netloc:
                    if full_url not in internal_urls and full_url not in urls_to_visit:
                        urls_to_visit.append(full_url)

        except Exception as e:
            print(f"Could not crawl {current_url}: {e}")

    return list(internal_urls)


def is_ecommerce_website(url):
    try:

        # ❌ Known NON-ecommerce domains (extend anytime)
        NON_ECOMMERCE_DOMAINS = [
            "bbc.com", "bbc.co.uk", "cnn.com", "theguardian.com",
            "nytimes.com", "aljazeera.com", "reuters.com",
            "wikipedia.org", "medium.com", "blogspot.com"
        ]

        # If URL contains any of these → reject immediately
        for bad_domain in NON_ECOMMERCE_DOMAINS:
            if bad_domain in url.lower():
                return False

        #eCommerce keywords
        ecommerce_keywords = [
            "cart", "checkout", "shop", "product", "buy","shopping","shoppingbag"
            "add to cart", "order", "basket", "store"
        ]

        # Fetch page
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=5)
        html = response.text.lower()

        # Check keywords in HTML
        matches = sum(1 for word in ecommerce_keywords if word in html)

        # Simple decision
        if matches >= 3:
            return True
        else:
            return False

    except Exception as e:
        print("Error:", e)
        return False
    
from .webdriver_extended import CheckoutEvaluator
@login_required
def evaluate_url(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url', '')
            
            if not url:
                return JsonResponse({'error': 'URL is required'}, status=400)
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            if not is_ecommerce_website(url):
                print("Error: This doesn't look like an e-commerce checkout page.")
                return
            
            pages = get_website_pages_for_assesment(url)
    
            print(f"\nChecking rules on Final list of pages):")

            #if url is repeated
            cached_memory = clean_store_cached_memory(url)
            if cached_memory:
                return JsonResponse(cached_memory)
            
            #if openAi can check and give suggestions
            Get_Assessment_From_OpenAi_Api(url)

            #check url based on 23 rules from rule book
            evaluator_main = CheckoutEvaluator(url)
            results_main, issues_main, suggestions_main = evaluator_main.evaluate_all_rules()

            global check_home_page_also
            if check_home_page_also:
                #check homepage also for data
                homepage_url = get_homepage(url)
                evaluator_home = CheckoutEvaluator(homepage_url)
                results_home, issues_home, suggestions_home = evaluator_home.evaluate_all_rules()
                
            # ===============================
                # 🔹 3. Combine Results
                # ===============================
                combined_results = {}
                combined_issues = list(set(issues_main + issues_home))
                combined_suggestions = list(set(suggestions_main + suggestions_home))

                for key in results_main:
                    # If ANY fails → mark as False
                    combined_results[key] = results_main.get(key, False) and results_home.get(key, False)
                
                score = sum(1 for val in combined_results.values() if val)
                total = 23

                return JsonResponse({
                    'original_url': url,
                    'homepage_url': homepage_url,
                    'score': score,
                    'total': total,
                    'issues': combined_issues[:15],
                    'suggestions': combined_suggestions[:15],
                    'detailed_results': combined_results
                })

            else:
                score = sum(1 for val in results_home.values() if val)
                total = 23
                
                return JsonResponse({
                    'score': score,
                    'total': total,
                    'issues': issues_home[:15],
                    'suggestions': suggestions_home[:15],
                    'detailed_results': results_home
                })
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return JsonResponse({'error': f'Failed to analyze URL: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)