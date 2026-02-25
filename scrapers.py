import os
import json
import time
import random
import asyncio
import hashlib
import requests
import feedparser
# import scrapy  # Will be imported optionally
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urlencode, urljoin, urlparse
from bs4 import BeautifulSoup

# Optional imports with error handling
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import scrapy
    from scrapy.crawler import CrawlerProcess
    SCRAPY_AVAILABLE = True
except ImportError:
    SCRAPY_AVAILABLE = False

class PlaywrightScraper:
    def __init__(self, headless=True):
        self.headless = headless
    
    def scrape(self, url, scroll_pages=3, wait_for_selector=None):
        if not PLAYWRIGHT_AVAILABLE:
            print("⚠️ Playwright not installed. Skipping.")
            return None
            
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                if wait_for_selector:
                    try:
                        page.wait_for_selector(wait_for_selector, timeout=5000)
                    except:
                        pass
                
                for _ in range(scroll_pages):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1000)
                
                # Create hash for filename
                url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
                screenshot_path = f"screenshot_{url_hash}.png"
                # Note: The caller should handle moving this to the research folder
                # page.screenshot(path=screenshot_path)
                
                content = page.content()
                title = page.title()
                
                # Extract clean text
                soup = BeautifulSoup(content, 'html.parser')
                for script in soup(["script", "style"]):
                    script.decompose()
                text_content = soup.get_text(separator=' ', strip=True)
                
                browser.close()
                return {
                    'title': title,
                    'content': content,
                    'text_content': text_content,
                    'tool': 'playwright'
                }
        except Exception as e:
            print(f"  ✗ Playwright error: {e}")
            return None

class SeleniumScraper:
    def __init__(self, headless=True):
        self.headless = headless
        
    def setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        ]
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def scrape(self, url, wait_for_element=None, scroll=True):
        if not SELENIUM_AVAILABLE:
            print("⚠️ Selenium not installed. Skipping.")
            return None
            
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(url)
            
            if wait_for_element:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                except:
                    pass
            
            if scroll:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            content = driver.page_source
            title = driver.title
            
            # Extract clean text
            soup = BeautifulSoup(content, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text(separator=' ', strip=True)
            
            return {
                'title': title,
                'content': content,
                'text_content': text_content,
                'tool': 'selenium'
            }
        except Exception as e:
            print(f"  ✗ Selenium error: {e}")
            return None
        finally:
            if driver:
                driver.quit()

class BeautifulSoupScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape(self, url):
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
                
            return {
                'title': soup.title.string if soup.title else '',
                'content': response.text,
                'text_content': soup.get_text(separator=' ', strip=True),
                'tool': 'beautifulsoup'
            }
        except Exception as e:
            print(f"  ✗ BeautifulSoup error: {e}")
            return None

if SCRAPY_AVAILABLE:
    class ResearchItem(scrapy.Item):
        url = scrapy.Field()
        title = scrapy.Field()
        content = scrapy.Field()
        timestamp = scrapy.Field()
else:
    class ResearchItem:
        pass

class ScrapyManager:
    def __init__(self, output_file='output.json'):
        self.output_file = output_file
        
    def crawl_site(self, start_urls, max_pages=10):
        # Programmatic Scrapy is tricky in a script that might run multiple times
        # Here we provide a simplified version that could be expanded
        pass

class SmartResearchAutomator:
    """Intelligently chooses the best scraping tool"""
    def __init__(self, headless=True):
        self.playwright = PlaywrightScraper(headless=headless)
        self.selenium = SeleniumScraper(headless=headless)
        self.bs4 = BeautifulSoupScraper()
        self.research_data = [] # For storing session results
        
    def analyze_complexity(self, url: str) -> str:
        js_heavy = ['twitter.com', 'facebook.com', 'instagram.com', 'reddit.com', 'medium.com', 'github.com', 'linkedin.com']
        url_lower = url.lower()
        
        if any(domain in url_lower for domain in js_heavy):
            return 'playwright' if PLAYWRIGHT_AVAILABLE else ('selenium' if SELENIUM_AVAILABLE else 'bs4')
        
        # Check for dynamic indicators in URL
        dynamic_indicators = ['spa', 'app', 'dynamic', 'search', 'filter']
        if any(ind in url_lower for ind in dynamic_indicators):
            return 'selenium' if SELENIUM_AVAILABLE else 'bs4'
            
        return 'bs4'

    def scrape_url(self, url: str, force_tool: str = None) -> Dict[str, Any]:
        """Scrape a URL using the best available tool or a forced selection."""
        print(f"  🌐 Analyzing & Scraping: {url[:60]}...")
        
        tool_type = force_tool if force_tool else self.analyze_complexity(url)
        
        result = None
        try:
            if tool_type == 'playwright' and PLAYWRIGHT_AVAILABLE:
                print(f"    ✓ Using Playwright (JS-heavy)")
                result = self.playwright.scrape(url)
            
            elif tool_type == 'selenium' and SELENIUM_AVAILABLE:
                print(f"    ✓ Using Selenium (Dynamic)")
                result = self.selenium.scrape(url)
                
            elif tool_type == 'bs4' or tool_type == 'static':
                print(f"    ✓ Using BeautifulSoup (Fast)")
                result = self.bs4.scrape(url)
            else:
                # Default smart behavior if tool_type is unrecognized or unavailable
                print(f"    ⚠ Tool '{tool_type}' unavailable, using fallback.")
                result = self.bs4.scrape(url)
        except Exception as e:
            print(f"    ✗ Error with {tool_type}: {e}")
            # Final fallback to BS4 if it wasn't the tool that failed
            if tool_type != 'bs4':
                try:
                    result = self.bs4.scrape(url)
                except:
                    result = None
            
        if result:
            result['url'] = url
            result['timestamp'] = datetime.now().isoformat()
            self.research_data.append(result)
            return result
        return {}
