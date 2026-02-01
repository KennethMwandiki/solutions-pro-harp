"""
Dashboard UI Verification Script
Captures screenshots of the Streamlit dashboard for manual verification.
"""
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# Configuration
DASHBOARD_URL = "http://localhost:8501"
SCREENSHOT_DIR = "dashboard_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def check_dashboard_health():
    """Verify dashboard is accessible"""
    try:
        response = requests.get(DASHBOARD_URL, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Dashboard not accessible: {e}")
        return False

def capture_dashboard_screenshots():
    """Capture screenshots of dashboard pages using Selenium"""
    
    # Setup Chrome in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("[INFO] Loading Home page...")
        driver.get(DASHBOARD_URL)
        time.sleep(5)  # Wait for Streamlit to fully render
        
        # Capture Home page
        home_screenshot = os.path.join(SCREENSHOT_DIR, "01_home_page.png")
        driver.save_screenshot(home_screenshot)
        print(f"[OK] Saved: {home_screenshot}")
        
        # Try to find and interact with tenant selector
        try:
            tenant_selector = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select, div[data-baseweb='select']"))
            )
            print(f"[OK] Found tenant selector")
            
            # Capture after tenant interaction
            time.sleep(2)
            tenant_screenshot = os.path.join(SCREENSHOT_DIR, "02_tenant_selector.png")
            driver.save_screenshot(tenant_screenshot)
            print(f"[OK] Saved: {tenant_screenshot}")
        except Exception as e:
            print(f"[WARN] Tenant selector not found: {e}")
        
        # Navigate to Entity Management page
        try:
            print("[INFO] Attempting to navigate to Entities page...")
            # Streamlit uses sidebar links
            entities_link = driver.find_element(By.LINK_TEXT, "Entities")
            entities_link.click()
            time.sleep(5)
            
            entities_screenshot = os.path.join(SCREENSHOT_DIR, "03_entities_page.png")
            driver.save_screenshot(entities_screenshot)
            print(f"[OK] Saved: {entities_screenshot}")
        except Exception as e:
            print(f"[WARN] Could not navigate to Entities: {e}")
        
        # Navigate to Incidents page
        try:
            print("[INFO] Attempting to navigate to Incidents page...")
            incidents_link = driver.find_element(By.LINK_TEXT, "Incidents")
            incidents_link.click()
            time.sleep(5)
            
            incidents_screenshot = os.path.join(SCREENSHOT_DIR, "04_incidents_page.png")
            driver.save_screenshot(incidents_screenshot)
            print(f"[OK] Saved: {incidents_screenshot}")
        except Exception as e:
            print(f"[WARN] Could not navigate to Incidents: {e}")
        
        driver.quit()
        
        print(f"\n[OK] Screenshot capture complete! Check {SCREENSHOT_DIR}/")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error during screenshot capture: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Pro-Harp Dashboard UI Verification")
    print("=" * 60)
    
    if check_dashboard_health():
        print("[OK] Dashboard is accessible\n")
        capture_dashboard_screenshots()
    else:
        print("[ERROR] Dashboard is not running. Start it with:")
        print("   cd ops/dashboard && streamlit run Home.py")
