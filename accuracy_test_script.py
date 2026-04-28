import time
import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI

# ==========================================
# CONFIGURATION
# ==========================================
TARGET_URL = "https://www.darimooch.com/cart"


OPENAI_API_KEY = "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"


client = OpenAI(api_key=OPENAI_API_KEY)

class IndependentEvaluator:
    def __init__(self, url):
        self.url = url
        self.results = {}
        self.issues = []
        self.suggestions = []
        self.page_html = ""
        self.page_text = ""
        self.load_time = 0
        
        # Initialize results as False 
        for i in range(1, 24):
            self.results[f"R{i}"] = False

    def is_ecommerce(self):
        """Validates if the site is e-commerce before full audit."""
        indicators = ['cart', 'checkout', 'price', 'shipping', 'buy now', 'total', 'tax']
        matches = sum(1 for word in indicators if word in self.page_text.lower())
        return matches >= 2

    def run_dom_checks(self, driver):
        """Checks structural rules (DOM-based)."""
        html = self.page_html.lower()
        
        # Rule 11: Minimum form fields (Ideal 12-14) 
        visible_inputs = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), select, textarea")
        field_count = len([el for el in visible_inputs if el.is_displayed()])
        self.results['R11'] = 12 <= field_count <= 14
        if not self.results['R11']:
            self.issues.append(f"R11: Found {field_count} fields. Document recommends 12-14.")

        # Rule 16: Load time & Mobile optimization 
        has_viewport = 'name="viewport"' in html
        self.results['R16'] = (self.load_time < 3.0) and has_viewport # Threshold based on usability 

        # Rule 6: Security Indicators (HTTPS) 
        self.results['R6'] = self.url.startswith('https')
        
        # Rule 3: Primary CTA visibility 
        buttons = driver.find_elements(By.TAG_NAME, "button")
        self.results['R3'] = any(b.is_displayed() for b in buttons)

    def run_ai_checks(self):
        """Checks qualitative rules (OpenAI-based)."""
        prompt = f"""
        Analyze the text content of this e-commerce checkout page:
        ---
        {self.page_text[:4000]}
        ---
        Evaluate these specific rules from the usability guide:
        R2: Is button language clear/unambiguous?
        R4: Is there an explanation for why personal info (phone/DOB) is needed?
        R7: Is a return/refund policy mentioned or linked?
        R13: Is there a guest checkout option?
        R21: Is the page free from clutter and promotional distractions?

        Return ONLY a JSON object:
        {{
          "passed_rules": ["R2", "R13"], 
          "failed_rules": ["R4", "R7", "R21"],
          "reasoning": {{ "R4": "No explanation for phone field", ... }}
        }}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            ai_data = json.loads(response.choices[0].message.content)
            
            for r_code in ai_data.get("passed_rules", []):
                self.results[r_code] = True
            for r_code, reason in ai_data.get("reasoning", {}).items():
                if r_code in ai_data.get("failed_rules", []):
                    self.issues.append(f"{r_code}: {reason}")
        except Exception as e:
            print(f"AI Analysis Error: {e}")

    def perform_audit(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            print(f"Starting audit for: {self.url}...")
            start = time.time()
            driver.get(self.url)
            self.load_time = time.time() - start
            
            self.page_html = driver.page_source
            soup = BeautifulSoup(self.page_html, 'html.parser')
            self.page_text = soup.get_text(separator=' ', strip=True)

            if not self.is_ecommerce():
                print("Error: This doesn't look like an e-commerce checkout page.")
                return

            self.run_dom_checks(driver)
            self.run_ai_checks()
            self.print_report()

        finally:
            driver.quit()

    def print_report(self):
        score = sum(1 for v in self.results.values() if v)
        # High-priority rules check (5, 6, 9, 10, 11, 15) 
        hp_failed = [r for r in [5, 6, 9, 10, 11, 15] if not self.results.get(f"R{r}")]
        
        print("\n" + "="*30)
        print(f"AUDIT SCORE: {score}/23")
        print(f"HIGH-PRIORITY FAILURES: {hp_failed}")
        print("="*30)
        for issue in self.issues:
            print(f"- {issue}")

if __name__ == "__main__":
    auditor = IndependentEvaluator(TARGET_URL)
    auditor.perform_audit()