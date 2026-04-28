from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

url = "https://www.gymshark.com/"
start = time.time()
driver.get(url)

# Wait for page body to load
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.TAG_NAME, "body"))
)

load_time = time.time() - start
html_length = len(driver.page_source)
title = driver.title

print(f"URL: {url}")
print(f"Load time: {load_time:.2f}s")
print(f"Page title: {title}")
print(f"HTML length: {html_length} chars")
print(f"First 200 chars of HTML: {driver.page_source[:200]}")

driver.quit()