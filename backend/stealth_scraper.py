"""
Advanced stealth scraper with comprehensive bot detection bypass.
Handles HTTP/2 protocol errors, Cloudflare, and other protection systems.
"""

import asyncio
import random
import time
import json
from typing import Optional, List, Dict, Tuple, Any
from urllib.parse import urlparse, urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class StealthScraperError(Exception):
    pass


class StealthScraper:
    """Advanced stealth scraper with multiple bypass techniques."""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.session = self._create_stealth_session()
    
    def _create_stealth_session(self) -> requests.Session:
        """Create a requests session with stealth configuration."""
        session = requests.Session()
        
        # Force HTTP/1.1 adapter with enhanced connection handling
        class HTTP11Adapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                from urllib3 import poolmanager
                import socket
                kwargs['socket_options'] = [
                    (socket.SOL_TCP, socket.TCP_NODELAY, 1),  # TCP_NODELAY
                    (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),  # Keep connections alive
                ]
                kwargs['ssl_version'] = None  # Let requests handle SSL version
                kwargs['cert_reqs'] = 'CERT_REQUIRED'
                kwargs['ca_certs'] = None
                return super().init_poolmanager(*args, **kwargs)
            
            def send(self, request, **kwargs):
                # Force HTTP/1.1 by modifying the request
                if hasattr(request, 'url') and request.url.startswith('https://'):
                    # Add connection close to prevent HTTP/2 upgrade
                    if 'Connection' not in request.headers:
                        request.headers['Connection'] = 'close'
                return super().send(request, **kwargs)
        
        # Configure retry strategy with better error handling
        retry_strategy = Retry(
            total=5,  # Increased retries for protected sites
            status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 523, 524],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=2,  # Exponential backoff
            raise_on_status=False  # Don't raise on status errors immediately
        )
        
        adapter = HTTP11Adapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set connection pool settings
        session.adapters['https://'].config['pool_connections'] = 1
        session.adapters['https://'].config['pool_maxsize'] = 1
        session.adapters['http://'].config['pool_connections'] = 1
        session.adapters['http://'].config['pool_maxsize'] = 1
        
        return session
    
    def _get_realistic_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Generate realistic HTTP headers."""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        
        if referer:
            headers['Referer'] = referer
        
        return headers
    
    async def scrape_with_playwright_stealth(self, url: str, timeout: int = 60000) -> str:
        """Scrape using Playwright with advanced stealth techniques."""
        print("🎭 Trying Playwright stealth mode...")
        
        async with async_playwright() as p:
            # Launch browser with maximum stealth and network stability
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--force-http1',  # Force HTTP/1.1
                    '--disable-http2',  # Disable HTTP/2
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--no-default-browser-check',
                    '--disable-software-rasterizer',
                    '--disable-background-networking',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-hang-monitor',
                    '--disable-popup-blocking',
                    '--disable-prompt-on-repost',
                    '--force-color-profile=srgb',
                    '--metrics-recording-only',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    # Network stability improvements
                    '--disable-features=VizDisplayCompositor,VizHitTestSurfaceLayer',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-ipc-flooding-protection',
                    '--max-connections-per-host=6',
                    '--aggressive-cache-discard',
                    '--disable-background-networking',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-sync',
                    '--no-pings',
                    '--no-proxy-server',
                    '--disable-client-side-phishing-detection'
                ]
            )
            
            # Create context with realistic fingerprint
            context = await browser.new_context(
                viewport={'width': random.randint(1366, 1920), 'height': random.randint(768, 1080)},
                user_agent=random.choice(self.user_agents),
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                extra_http_headers=self._get_realistic_headers()
            )
            
            # Add comprehensive stealth scripts
            await context.add_init_script("""
                // Remove webdriver traces
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock chrome runtime
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {
                        return {
                            commitLoadTime: Date.now() / 1000 - Math.random() * 100,
                            finishDocumentLoadTime: Date.now() / 1000 - Math.random() * 50,
                            finishLoadTime: Date.now() / 1000 - Math.random() * 10,
                            firstPaintAfterLoadTime: 0,
                            firstPaintTime: Date.now() / 1000 - Math.random() * 20,
                            navigationType: 'Other',
                            npnNegotiatedProtocol: 'h2',
                            requestTime: Date.now() / 1000 - Math.random() * 200,
                            startLoadTime: Date.now() / 1000 - Math.random() * 150,
                            wasAlternateProtocolAvailable: false,
                            wasFetchedViaSpdy: true,
                            wasNpnNegotiated: true
                        };
                    },
                    csi: function() {
                        return {
                            onloadT: Date.now(),
                            pageT: Date.now() - Math.random() * 1000,
                            startE: Date.now() - Math.random() * 2000,
                            tran: 15
                        };
                    }
                };
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                            description: "",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ],
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 4,
                });
                
                // Mock device memory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                });
                
                // Mock connection
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        downlink: 10,
                        effectiveType: '4g',
                        rtt: 50,
                        saveData: false
                    }),
                });
                
                // Override getContext to avoid canvas fingerprinting
                const getContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(contextType, contextAttributes) {
                    if (contextType === '2d') {
                        const context = getContext.call(this, contextType, contextAttributes);
                        const originalFillText = context.fillText;
                        context.fillText = function() {
                            return originalFillText.apply(this, arguments);
                        };
                        return context;
                    }
                    return getContext.call(this, contextType, contextAttributes);
                };
                
                // Mock screen properties
                Object.defineProperty(screen, 'availHeight', {
                    get: () => window.innerHeight,
                });
                Object.defineProperty(screen, 'availWidth', {
                    get: () => window.innerWidth,
                });
            """)
            
            page = await context.new_page()
            
            try:
                # Random delay before navigation
                await asyncio.sleep(random.uniform(1, 3))
                
                # Navigate with multiple strategies and retries
                navigation_strategies = [
                    ('networkidle', timeout),
                    ('domcontentloaded', timeout // 2),
                    ('load', timeout // 3),
                    ('commit', timeout // 4)
                ]
                
                success = False
                for strategy_name, strategy_timeout in navigation_strategies:
                    if success:
                        break
                        
                    print(f"📡 Trying navigation with {strategy_name} strategy...")
                    max_retries = 3
                    
                    for attempt in range(max_retries):
                        try:
                            await page.goto(url, wait_until=strategy_name, timeout=strategy_timeout)
                            success = True
                            break
                        except Exception as e:
                            error_msg = str(e).lower()
                            if 'net::err_network_io_suspended' in error_msg:
                                print(f"⚠ Network IO suspended, trying different approach...")
                                await asyncio.sleep(random.uniform(3, 8))
                            elif 'timeout' in error_msg:
                                print(f"⚠ Navigation timeout with {strategy_name}, will try next strategy...")
                                break  # Try next strategy
                            else:
                                print(f"⚠ Navigation attempt {attempt + 1} failed: {e}")
                                
                            if attempt == max_retries - 1:
                                print(f"❌ All retries failed for {strategy_name} strategy")
                            else:
                                await asyncio.sleep(random.uniform(2, 5))
                
                if not success:
                    raise StealthScraperError("All navigation strategies failed")
                
                # Wait and simulate human behavior
                await asyncio.sleep(random.uniform(2, 5))
                await self._simulate_human_behavior_async(page)
                
                # Get content
                html = await page.content()
                return self._extract_text_from_html(html)
                
            finally:
                await context.close()
                await browser.close()
    
    async def _simulate_human_behavior_async(self, page):
        """Simulate human-like behavior asynchronously."""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 5)):
                await page.mouse.move(
                    random.randint(100, 800), 
                    random.randint(100, 600)
                )
                await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Random scrolling
            for _ in range(random.randint(2, 4)):
                await page.evaluate(f"window.scrollBy(0, {random.randint(200, 500)})")
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Focus and blur events
            await page.evaluate("document.body.focus()")
            await asyncio.sleep(random.uniform(0.2, 0.8))
            
        except Exception:
            pass  # Ignore errors in simulation
    
    def scrape_with_undetected_chrome(self, url: str, timeout: int = 60) -> str:
        """Scrape using undetected-chromedriver."""
        print("🤖 Trying undetected Chrome driver...")
        
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--force-http1')  # Force HTTP/1.1
        options.add_argument('--disable-http2')  # Disable HTTP/2
        
        driver = None
        try:
            driver = uc.Chrome(options=options, version_main=None)
            driver.set_page_load_timeout(timeout)
            
            # Random delay
            time.sleep(random.uniform(1, 3))
            
            # Navigate
            driver.get(url)
            
            # Wait for page load
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Simulate human behavior
            self._simulate_human_behavior_selenium(driver)
            
            # Get page source
            html = driver.page_source
            return self._extract_text_from_html(html)
            
        except Exception as e:
            raise StealthScraperError(f"Undetected Chrome failed: {e}")
        finally:
            if driver:
                driver.quit()
    
    def _simulate_human_behavior_selenium(self, driver):
        """Simulate human behavior with Selenium."""
        try:
            # Random scrolling
            for _ in range(random.randint(2, 4)):
                scroll_amount = random.randint(200, 500)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Random delays
            time.sleep(random.uniform(1, 3))
            
        except Exception:
            pass
    
    def scrape_with_requests_advanced(self, url: str) -> str:
        """Advanced requests-based scraping with session management."""
        print("🌐 Trying advanced requests scraper...")
        
        headers = self._get_realistic_headers()
        
        # Add TLS fingerprint randomization
        self.session.headers.update(headers)
        
        # Multiple attempts with different configurations
        attempts = [
            {'timeout': 45, 'verify': True, 'stream': False},
            {'timeout': 60, 'verify': False, 'stream': False},  # Disable SSL verification
            {'timeout': 30, 'verify': True, 'stream': True},   # Use streaming
        ]
        
        for attempt_num, config in enumerate(attempts, 1):
            try:
                print(f"🔄 Request attempt {attempt_num} with timeout {config['timeout']}s...")
                
                # Random delay
                time.sleep(random.uniform(1, 3))
                
                # Make request with session
                response = self.session.get(
                    url,
                    timeout=config['timeout'],
                    allow_redirects=True,
                    verify=config['verify'],
                    stream=config['stream']
                )
                
                # Handle streaming response
                if config['stream']:
                    content = ''
                    for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                        if chunk:
                            content += chunk
                            # Stop if we have enough content
                            if len(content) > 100000:  # 100KB should be enough
                                break
                    response._content = content.encode('utf-8')
                
                response.raise_for_status()
                
                # Check for common bot detection responses
                if self._is_bot_detected(response):
                    if attempt_num < len(attempts):
                        print("⚠ Bot detection triggered, trying different configuration...")
                        continue
                    else:
                        raise StealthScraperError("Bot detection triggered in response")
                
                print(f"✅ Request succeeded with {len(response.text)} characters")
                return self._extract_text_from_html(response.text)
                
            except requests.exceptions.Timeout as e:
                print(f"⏰ Request timeout on attempt {attempt_num}: {e}")
                if attempt_num == len(attempts):
                    raise StealthScraperError(f"All request attempts timed out: {e}")
                continue
                
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 Connection error on attempt {attempt_num}: {e}")
                if attempt_num == len(attempts):
                    raise StealthScraperError(f"Connection failed after all attempts: {e}")
                time.sleep(random.uniform(2, 5))  # Wait before retry
                continue
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Request error on attempt {attempt_num}: {e}")
                if attempt_num == len(attempts):
                    raise StealthScraperError(f"Advanced requests failed: {e}")
                continue
        
        raise StealthScraperError("All request attempts failed")
    
    def _is_bot_detected(self, response: requests.Response) -> bool:
        """Check if the response indicates bot detection."""
        content = response.text.lower()
        
        bot_indicators = [
            'access denied', 'blocked', 'captcha', 'cloudflare',
            'bot detected', 'automated traffic', 'suspicious activity',
            'rate limited', 'too many requests', 'forbidden'
        ]
        
        return any(indicator in content for indicator in bot_indicators)
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract clean text from HTML."""
        try:
            parser = HTMLParser(html)
            
            # Remove noise elements
            noise_selectors = [
                'script', 'style', 'noscript', 'meta', 'link', 'title',
                'header', 'nav', 'footer', 'aside', 'form', 'iframe'
            ]
            
            for selector in noise_selectors:
                for element in parser.css(selector):
                    element.decompose()
            
            # Extract text from main content areas
            content_selectors = [
                'main', 'article', '.main', '.content', '.main-content',
                '[role="main"]', '#main', '#content'
            ]
            
            text_parts = []
            for selector in content_selectors:
                elements = parser.css(selector)
                if elements:
                    for element in elements:
                        text = element.text(separator=' ', strip=True)
                        if text and len(text) > 50:
                            text_parts.append(text)
                    break
            
            # Fallback to body if no main content found
            if not text_parts:
                body = parser.css_first('body')
                if body:
                    text_parts.append(body.text(separator=' ', strip=True))
            
            return '\n\n'.join(text_parts)
            
        except Exception:
            # Fallback to BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            return soup.get_text(separator='\n', strip=True)
    
    async def scrape_url_async(self, url: str) -> str:
        """Main async scraping method with multiple fallback strategies."""
        if not self._is_valid_url(url):
            raise StealthScraperError(f"Invalid URL: {url}")
        
        print(f"🚀 Stealth scraping: {url}")
        
        strategies = [
            ('Playwright Stealth', self.scrape_with_playwright_stealth),
            ('Undetected Chrome', self.scrape_with_undetected_chrome),
            ('Advanced Requests', self.scrape_with_requests_advanced)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                print(f"🔄 Trying {strategy_name}...")
                
                if asyncio.iscoroutinefunction(strategy_func):
                    content = await strategy_func(url)
                else:
                    content = strategy_func(url)
                
                if content and len(content.strip()) > 100:
                    print(f"✅ {strategy_name} succeeded: {len(content)} chars")
                    return content
                else:
                    print(f"⚠ {strategy_name} returned insufficient content")
                    
            except Exception as e:
                print(f"❌ {strategy_name} failed: {e}")
                continue
        
        raise StealthScraperError("All stealth scraping strategies failed")
    
    def scrape_url(self, url: str) -> str:
        """Synchronous wrapper for async scraping."""
        return asyncio.run(self.scrape_url_async(url))
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme in ("http", "https"), parsed.netloc])
        except Exception:
            return False


# Convenience function for backward compatibility
def enhanced_scrape_url_stealth(url: str) -> str:
    """Enhanced scraping with stealth techniques."""
    scraper = StealthScraper()
    return scraper.scrape_url(url)


if __name__ == "__main__":
    # Test with RedBus
    test_url = "https://www.redbus.in/"
    try:
        scraper = StealthScraper()
        content = scraper.scrape_url(test_url)
        print(f"✅ Scraped {len(content)} characters")
        print(f"📝 Sample content:\n{content[:500]}...")
    except Exception as e:
        print(f"❌ Test failed: {e}")
