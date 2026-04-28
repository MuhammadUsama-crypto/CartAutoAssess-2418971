import time
import json
import logging
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from django.core.cache import cache
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CheckoutEvaluator:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.results = {}
        self.issues = []
        self.suggestions = []
        self.page_text = ""
        self.page_html = ""
        self.load_time = 0

    def evaluate_all_rules(self):
        # Initialize all as False
        for i in range(1, 24):
            self.results[f"rule_{i}"] = False

        # Check cache
        cache_key = f"eval_results_{self.url}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data['results'], cached_data['issues'], cached_data['suggestions']

        try:
            # Setup Chrome
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # Load page
            start_time = time.time()
            self.driver.get(self.url)
            self.load_time = time.time() - start_time

            # Wait
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)

            # Extract data
            self.page_html = self.driver.page_source
            self.extract_page_text()

            # Evaluate all 23 rules
            self.evaluate_rules()

            # Cache
            result_data = {
                'results': self.results,
                'issues': self.issues,
                'suggestions': self.suggestions
            }
            cache.set(cache_key, result_data, 60 * 60)

        except Exception as e:
            logger.error(f"Error: {e}")
            self.issues.append(f"Error: {str(e)[:100]}")
            # Still try to evaluate from HTML
            self.evaluate_rules_fallback()

        finally:
            if self.driver:
                self.driver.quit()

        return self.results, self.issues, self.suggestions

    def evaluate_rules(self):
        """Evaluate all 23 rules - Simple & Direct"""
        
        html = self.page_html.lower()
        text = self.page_text.lower()

        # ===== RULE 1: Step indicators =====
        steps = ['step', 'progress', 'shipping', 'payment', 'checkout', 'contact', 'delivery']
        self.results['rule_1'] = any(s in text for s in steps)
        if not self.results['rule_1']:
            self.issues.append("Rule 1: Checkout steps not clearly marked")
            self.suggestions.append("Add clear step indicators")

        # ===== RULE 2: Button clarity =====
        good_buttons = ['place order', 'checkout', 'pay now', 'continue', 'proceed', 'buy now', 'submit']
        button_match = any(b in text for b in good_buttons)
        
        # Also check actual button elements
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = btn.text.lower()
                if any(g in btn_text for g in good_buttons):
                    button_match = True
                    break
        except:
            pass
            
        self.results['rule_2'] = button_match
        if not self.results['rule_2']:
            self.issues.append("Rule 2: Button language unclear")
            self.suggestions.append("Use clear button text like 'Place Order'")

        # ===== RULE 3: Buttons visible =====
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            visible = any(b.is_displayed() for b in buttons)
            self.results['rule_3'] = visible
        except:
            self.results['rule_3'] = 'button' in html
        
        if not self.results['rule_3']:
            self.issues.append("Rule 3: No visible buttons")
            self.suggestions.append("Ensure buttons are visible")

        # ===== RULE 4: Explain personal info =====
        explains = ['required for', 'need your', 'to verify', 'for shipping', 'why']
        self.results['rule_4'] = any(e in text for e in explains)
        if not self.results['rule_4']:
            self.issues.append("Rule 4: No explanation for personal info")
            self.suggestions.append("Explain why phone/email is needed")

        # ===== RULE 5: Additional costs =====
        costs = ['shipping', 'tax', 'fee', 'delivery', 'total']
        self.results['rule_5'] = any(c in text for c in costs)
        if not self.results['rule_5']:
            self.issues.append("Rule 5: Additional costs not shown")
            self.suggestions.append("Show shipping and taxes early")

        # ===== RULE 6: Security =====
        security = ['secure', 'ssl', 'encrypted', 'https', 'lock']
        self.results['rule_6'] = any(s in text for s in security) or 'https' in self.url
        if not self.results['rule_6']:
            self.issues.append("Rule 6: No security indicators")
            self.suggestions.append("Add security badges")

        # ===== RULE 7: Return policy =====
        returns = ['return', 'refund', 'policy', 'guarantee']
        self.results['rule_7'] = any(r in text for r in returns)
        if not self.results['rule_7']:
            self.issues.append("Rule 7: Return policy not accessible")
            self.suggestions.append("Link to return policy")

        # ===== RULE 8: Delivery time =====
        delivery = ['delivery', 'shipping date', 'arrives', 'estimated']
        self.results['rule_8'] = any(d in text for d in delivery)
        if not self.results['rule_8']:
            self.issues.append("Rule 8: Delivery time not shown")
            self.suggestions.append("Show estimated delivery date")

        # ===== RULE 9: Streamlined =====
        inputs = len(re.findall(r'<(input|select|textarea)', html))
        self.results['rule_9'] = inputs < 30  # Reasonable
        if not self.results['rule_9']:
            self.issues.append("Rule 9: Too many steps/fields")
            self.suggestions.append("Reduce checkout steps")

        # ===== RULE 10: Progress indicator =====
        progress = ['progress', 'step', 'checkout progress']
        self.results['rule_10'] = any(p in text for p in progress)
        if not self.results['rule_10']:
            self.issues.append("Rule 10: No progress indicator")
            self.suggestions.append("Add progress bar")

        # ===== RULE 11: Minimum fields =====
        field_count = len(re.findall(r'<(input|select|textarea)', html))
        self.results['rule_11'] = 5 <= field_count <= 20
        if not self.results['rule_11']:
            self.issues.append(f"Rule 11: {field_count} form fields (ideal 12-14)")
            self.suggestions.append("Remove unnecessary fields")

        # ===== RULE 12: Error messages =====
        errors = ['error', 'invalid', 'required', 'valid']
        self.results['rule_12'] = any(e in text for e in errors)
        if not self.results['rule_12']:
            self.issues.append("Rule 12: No clear error messages")
            self.suggestions.append("Add inline error messages")

        # ===== RULE 13: Guest checkout =====
        guest = ['guest', 'without account', 'no account', 'checkout as guest']
        self.results['rule_13'] = any(g in text for g in guest)
        if not self.results['rule_13']:
            self.issues.append("Rule 13: No guest checkout option")
            self.suggestions.append("Add 'Guest Checkout' option")

        # ===== RULE 14: Edit cart =====
        edit = ['edit', 'update', 'remove', 'change quantity']
        self.results['rule_14'] = any(e in text for e in edit)
        if not self.results['rule_14']:
            self.issues.append("Rule 14: Cannot edit cart")
            self.suggestions.append("Allow cart editing")

        # ===== RULE 15: Order summary =====
        summary = ['summary', 'total', 'subtotal', 'order details']
        self.results['rule_15'] = any(s in text for s in summary)
        if not self.results['rule_15']:
            self.issues.append("Rule 15: No order summary")
            self.suggestions.append("Show order summary before payment")

        # ===== RULE 16: Fast load & mobile (SIMPLIFIED) =====
        fast = self.load_time < 5.0
        viewport = 'viewport' in html
        
        # Simple mobile check - just viewport is enough
        self.results['rule_16'] = fast and viewport
        
        if not fast:
            self.issues.append(f"Rule 16: Slow load ({self.load_time:.1f}s)")
            self.suggestions.append("Optimize page speed")
        if not viewport:
            self.issues.append("Rule 16: Missing viewport meta tag")
            self.suggestions.append("Add viewport meta tag")
        if fast and viewport:
            # No issues if passed
            pass

        # ===== RULE 17: Multiple payment options =====
        payments = ['cod', 'cash', 'card', 'paypal', 'online', 'bank', 'credit', 'debit']
        payment_count = sum(1 for p in payments if p in text)
        self.results['rule_17'] = payment_count >= 2
        if not self.results['rule_17']:
            self.issues.append("Rule 17: Limited payment options")
            self.suggestions.append("Add multiple payment methods")

        # ===== RULE 18: Buy now / Add to cart =====
        buy = ['buy now', 'add to cart', 'quick buy']
        self.results['rule_18'] = any(b in text for b in buy)
        if not self.results['rule_18']:
            self.issues.append("Rule 18: Missing buy options")
            self.suggestions.append("Add both 'Buy Now' and 'Add to Cart'")

        # ===== RULE 19: Ratings/reviews =====
        ratings = ['rating', 'review', 'star', 'customer']
        self.results['rule_19'] = any(r in text for r in ratings)
        if not self.results['rule_19']:
            self.issues.append("Rule 19: No ratings/reviews")
            self.suggestions.append("Display product ratings")

        # ===== RULE 20: Prominent CTA =====
        cta = ['checkout', 'place order', 'pay now', 'complete']
        self.results['rule_20'] = any(c in text for c in cta)
        if not self.results['rule_20']:
            self.issues.append("Rule 20: CTA not prominent")
            self.suggestions.append("Make CTA buttons prominent")

        # ===== RULE 21: No clutter =====
        clutter_words = ['ad', 'sponsored', 'promotion', 'newsletter']
        clutter = sum(1 for c in clutter_words if c in text)
        self.results['rule_21'] = clutter < 5
        if not self.results['rule_21']:
            self.issues.append("Rule 21: Too much clutter")
            self.suggestions.append("Remove distractions")

        # ===== RULE 22: Consistent branding =====
        self.results['rule_22'] = True  # Assume consistent

        # ===== RULE 23: Clear info =====
        info = ['price', 'cost', 'total', 'rs', 'pkr']
        self.results['rule_23'] = any(i in text for i in info)
        if not self.results['rule_23']:
            self.issues.append("Rule 23: Pricing unclear")
            self.suggestions.append("Show clear pricing")

        # Log results
        score = sum(1 for v in self.results.values() if v)
        logger.info(f"Score: {score}/23 - {self.url}")

    def evaluate_rules_fallback(self):
        """Fallback if page didn't load properly"""
        if self.page_html:
            self.evaluate_rules()
        else:
            for i in range(1, 24):
                self.results[f"rule_{i}"] = False
            self.issues.append("Could not analyze page")    

    def extract_page_text(self):
        soup = BeautifulSoup(self.page_html, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        self.page_text = soup.get_text(separator=' ', strip=True)[:10000]

