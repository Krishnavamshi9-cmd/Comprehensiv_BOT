"""
Enhanced aggressive scraper with multiple extraction strategies and content validation.
Addresses root cause issues in content extraction.
"""

import re
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse, urljoin
from collections import Counter

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from selectolax.parser import HTMLParser
import requests
from bs4 import BeautifulSoup


class ScraperError(Exception):
    pass


def _is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ("http", "https"), parsed.netloc])
    except Exception:
        return False


def _validate_content_quality(content: str, min_length: int = 100) -> Tuple[bool, str]:
    """Validate if scraped content meets quality thresholds."""
    if not content or len(content.strip()) < min_length:
        return False, f"Content too short: {len(content)} chars (min: {min_length})"
    
    # Check for common scraping failures
    failure_indicators = [
        "access denied", "403 forbidden", "404 not found", "500 internal server",
        "javascript required", "please enable javascript", "captcha",
        "bot detected", "access blocked", "cloudflare", "rate limited"
    ]
    
    content_lower = content.lower()
    for indicator in failure_indicators:
        if indicator in content_lower:
            return False, f"Scraping failure detected: {indicator}"
    
    # Check content diversity (not just repeated text)
    words = content.split()
    word_count = len(words)
    word_freq = Counter(word.lower() for word in words if word.isalpha())
    most_common_freq = word_freq.most_common(1)[0][1] if word_freq else 0
    repetition_ratio = most_common_freq / max(word_count, 1)
    
    if repetition_ratio > 0.5:  
        return False, "Content appears to be repetitive/low quality"
    
    return True, "Content quality acceptable"


def _aggressive_text_extraction(html: str) -> str:
    """Multiple extraction strategies with fallbacks."""
    parser = HTMLParser(html)
    
    # Strategy 1: Remove noise aggressively
    noise_selectors = [
        "script", "style", "noscript", "meta", "link", "title",
        "header", "nav", "footer", "aside", "form", "iframe", "svg", "canvas",
        "[role='navigation']", "[role='banner']", "[role='contentinfo']",
        "[aria-label*='nav']", "[aria-label*='menu']", "[aria-label*='breadcrumb']",
        ".nav", ".navbar", ".navigation", ".menu", ".header", ".footer",
        ".sidebar", ".advertisement", ".ad", ".ads", ".cookie", ".popup",
        ".modal", ".overlay", ".social", ".share", ".comment", ".related",
        "#nav", "#navbar", "#header", "#footer", "#sidebar", "#ads",
        "[class*='nav-']", "[class*='menu-']", "[class*='header-']", "[class*='footer-']",
        "[class*='ad-']", "[class*='ads-']", "[class*='cookie-']", "[class*='popup-']",
        "[id*='nav-']", "[id*='menu-']", "[id*='header-']", "[id*='footer-']",
        "[id*='ad-']", "[id*='ads-']", "[id*='cookie-']", "[id*='popup-']"
    ]
    
    for sel in noise_selectors:
        for node in parser.css(sel):
            node.decompose()
    
    # Strategy 2: Priority-based content extraction
    content_strategies = [
        # FAQ/Help content (highest priority)
        {
            "name": "FAQ/Help Content",
            "selectors": [
                ".faq", ".faqs", ".help", ".support", ".qa", ".questions",
                "[class*='faq']", "[class*='help']", "[class*='support']", "[class*='question']",
                "[id*='faq']", "[id*='help']", "[id*='support']", "[id*='question']",
                "section[aria-label*='faq']", "section[aria-label*='help']"
            ]
        },
        # Main content areas
        {
            "name": "Main Content",
            "selectors": [
                "main", "article", ".main", ".content", ".main-content",
                "[role='main']", "#main", "#content", "#main-content",
                ".page-content", ".post-content", ".entry-content"
            ]
        },
        # Documentation/Info sections
        {
            "name": "Documentation",
            "selectors": [
                ".documentation", ".docs", ".info", ".information", ".details",
                "[class*='doc']", "[class*='info']", "[id*='doc']", "[id*='info']"
            ]
        },
        # Fallback to body
        {
            "name": "Full Body",
            "selectors": ["body"]
        }
    ]
    
    extracted_texts = []
    
    for strategy in content_strategies:
        for selector in strategy["selectors"]:
            elements = parser.css(selector)
            if elements:
                print(f"✓ Found content using {strategy['name']} strategy: {selector}")
                for elem in elements:
                    text = _extract_structured_text(elem)
                    if text and len(text.strip()) > 50:
                        extracted_texts.append(f"[{strategy['name']}] {text}")
                break
        if extracted_texts:
            break
    
    # Strategy 3: Aggressive fallback - extract from all text nodes
    if not extracted_texts:
        print("⚠ Using aggressive fallback extraction")
        all_text_nodes = []
        for node in parser.css("*"):
            if node.tag in ["p", "div", "span", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6"]:
                text = node.text(separator=" ", strip=True)
                if text and len(text) > 20:
                    all_text_nodes.append(text)
        
        if all_text_nodes:
            extracted_texts = all_text_nodes
    
    # Combine and clean
    combined_text = "\n".join(extracted_texts)
    return _clean_extracted_text(combined_text)


def _extract_structured_text(element) -> str:
    """Extract text while preserving structure for Q&A patterns."""
    texts = []
    
    # Look for Q&A patterns first
    qa_patterns = [
        ".faq-item", ".qa-item", ".question-answer", ".help-item",
        ".accordion-item", ".collapsible", ".toggle", ".expandable",
        "dt", "dd", "details", "summary"
    ]
    
    qa_found = False
    for pattern in qa_patterns:
        qa_elements = element.css(pattern)
        if qa_elements:
            qa_found = True
            for qa_elem in qa_elements:
                text = qa_elem.text(separator=" ", strip=True)
                if text and len(text) > 10:
                    texts.append(f"Q&A: {text}")
    
    # If no Q&A structure, extract all meaningful content
    if not qa_found:
        content_tags = ["p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th"]
        for tag in content_tags:
            elements = element.css(tag)
            for elem in elements:
                text = elem.text(separator=" ", strip=True)
                if text and len(text) > 5:
                    if elem.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        texts.append(f"HEADING: {text}")
                    else:
                        texts.append(text)
    
    return "\n".join(texts)


def _clean_extracted_text(text: str) -> str:
    """Aggressive text cleaning and normalization."""
    if not text:
        return ""
    
    # Normalize whitespace
    text = re.sub(r'\r\n|\r|\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # Remove common noise patterns
    noise_patterns = [
        r'Cookie Policy.*?Accept',
        r'This website uses cookies.*?(?:\n|$)',
        r'Subscribe to.*?newsletter.*?(?:\n|$)',
        r'Follow us on.*?(?:\n|$)',
        r'Share this.*?(?:\n|$)',
        r'Print this page.*?(?:\n|$)',
        r'Last updated.*?(?:\n|$)',
        r'Copyright.*?(?:\n|$)',
        r'All rights reserved.*?(?:\n|$)'
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Split into lines and clean
    lines = [line.strip() for line in text.splitlines()]
    
    # Remove very short lines and duplicates
    cleaned_lines = []
    seen_lines = set()
    
    for line in lines:
        if (line and len(line) > 3 and 
            line not in seen_lines and 
            not re.match(r'^[\W\d]{1,5}$', line)):  # Skip lines with only symbols/numbers
            cleaned_lines.append(line)
            seen_lines.add(line)
    
    return '\n'.join(cleaned_lines)


def _fallback_requests_scraper(url: str) -> str:
    """Fallback scraper using requests + BeautifulSoup."""
    print("🔄 Trying fallback requests-based scraper...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove noise
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        return _clean_extracted_text(text)
        
    except Exception as e:
        raise ScraperError(f"Fallback scraper failed: {e}")


def enhanced_scrape_url(url: str, 
                       wait_until: str = "networkidle", 
                       timeout_ms: int = 60000, 
                       scroll_pages: int = 5,
                       validate_quality: bool = True,
                       min_content_length: int = 200,
                       *,
                       crawl: bool = False,
                       max_depth: int = 1,
                       max_pages: int = 20,
                       same_domain_only: bool = True) -> str:
    """
    Enhanced scraper with multiple strategies and quality validation.
    """
    if not _is_valid_url(url):
        raise ScraperError(f"Invalid URL: {url}")
    
    print(f"🚀 Enhanced scraping: {url}")
    
    # Strategy 1: Playwright with multiple wait strategies
    wait_strategies = ["networkidle", "domcontentloaded", "load"]
    
    first_page_links: List[str] = []
    for strategy in wait_strategies:
        try:
            print(f"📡 Trying Playwright with {strategy} strategy...")
            content, links = _playwright_scraper(url, strategy, timeout_ms, scroll_pages)
            # capture links from the best-rendered page
            if links:
                first_page_links = links
            
            if validate_quality:
                is_valid, message = _validate_content_quality(content, min_content_length)
                if is_valid:
                    print(f"✅ Quality content extracted: {len(content)} chars")
                    main_content = content
                    break
                else:
                    print(f"⚠ Quality check failed: {message}")
                    continue
            else:
                main_content = content
                break
                
        except Exception as e:
            print(f"❌ Playwright {strategy} failed: {e}")
            continue

    # If Playwright failed to produce acceptable content, fallback to requests
    if 'main_content' not in locals():
        try:
            content = _fallback_requests_scraper(url)
            if validate_quality:
                is_valid, message = _validate_content_quality(content, min_content_length)
                if is_valid:
                    print(f"✅ Fallback scraper succeeded: {len(content)} chars")
                    main_content = content
                else:
                    print(f"⚠ Fallback quality check failed: {message}")
            else:
                main_content = content
        except Exception as e:
            print(f"❌ Fallback scraper failed: {e}")

    if 'main_content' not in locals():
        raise ScraperError("All scraping strategies failed to extract quality content")

    # Optional: Crawl hyperlinks to expand content coverage
    if not crawl:
        return main_content

    print("🌐 Crawling hyperlinks from the page...")
    seed_host = urlparse(url).netloc
    visited = set([url])
    aggregated_texts: List[str] = [main_content]

    # Seed queue with first-page links (if any); otherwise try to extract again via requests HTML
    frontier: List[Tuple[str, int]] = []
    for link in first_page_links:
        if link and link.startswith("http"):
            frontier.append((link, 1))

    # Safety: limit total pages
    while frontier and len(visited) < max_pages:
        current_url, depth = frontier.pop(0)
        if current_url in visited:
            continue
        if same_domain_only and urlparse(current_url).netloc != seed_host:
            continue
        if depth > max_depth:
            continue
        visited.add(current_url)
        print(f"🔗 [{len(visited)}/{max_pages}] Crawling (d={depth}): {current_url}")
        try:
            page_text = _fallback_requests_scraper(current_url)
            if page_text:
                aggregated_texts.append(page_text)
        except Exception as e:
            print(f"⚠ Failed to crawl {current_url}: {e}")
            continue

        # Extract more links from this page (best-effort via requests HTML)
        try:
            import requests
            from bs4 import BeautifulSoup
            resp = requests.get(current_url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                abs_url = urljoin(current_url, href)
                if not abs_url.startswith('http'):
                    continue
                if abs_url not in visited and len(visited) + len(frontier) < max_pages:
                    next_depth = depth + 1
                    if next_depth <= max_depth:
                        frontier.append((abs_url, next_depth))
        except Exception:
            pass

    combined = "\n\n".join(aggregated_texts)
    print(f"✅ Crawling complete. Aggregated length: {len(combined)} chars from {len(visited)} pages")
    return combined


def _playwright_scraper(url: str, wait_strategy: str, timeout_ms: int, scroll_pages: int) -> Tuple[str, List[str]]:
    """Playwright-based scraper with aggressive content loading.
    Returns a tuple: (extracted_text, links)
    """
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
        )
        
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            java_script_enabled=True
        )
        
        page = context.new_page()
        page.set_default_timeout(timeout_ms)
        
        try:
            # Navigate to page
            page.goto(url, wait_until=wait_strategy, timeout=timeout_ms)
            
            # Wait for initial content
            page.wait_for_timeout(3000)
            
            # Aggressive content loading
            _aggressive_content_loading(page, scroll_pages)
            
            # Get final HTML
            html = page.content()

            # Extract text using enhanced strategy
            text = _aggressive_text_extraction(html)

            # Extract hyperlinks from rendered HTML
            links = _extract_links_from_html(html, base_url=url)

            return text, links
            
        finally:
            context.close()
            browser.close()


def _aggressive_content_loading(page, scroll_pages: int):
    """Aggressively load all possible content."""
    
    # 1. Scroll to load lazy content
    for i in range(scroll_pages):
        print(f"📜 Scrolling {i+1}/{scroll_pages}")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        # Try to click load more buttons
        load_more_selectors = [
            "button:has-text('Load More')", "button:has-text('Show More')", 
            "button:has-text('View More')", "button:has-text('See More')",
            "a:has-text('Load More')", "a:has-text('Show More')",
            ".load-more", ".show-more", ".view-more", ".see-more",
            "[data-testid*='load']", "[data-testid*='more']"
        ]
        
        for selector in load_more_selectors:
            try:
                element = page.query_selector(selector)
                if element and element.is_visible():
                    element.click()
                    page.wait_for_timeout(2000)
                    break
            except:
                pass
    
    # 2. Expand all collapsible content
    expandable_selectors = [
        "details:not([open])",
        "button[aria-expanded='false']",
        "summary",
        "[role='button'][aria-expanded='false']",
        ".accordion-button:not(.collapsed)",
        ".collapsible:not(.active)",
        ".expandable:not(.expanded)",
        "[data-toggle='collapse']",
        ".faq-question",
        ".toggle",
        "[class*='expand']",
        "[class*='toggle']",
        "[class*='accordion']",
        "[class*='collaps']"
    ]
    
    print("🔧 Expanding collapsible content...")
    for selector in expandable_selectors:
        elements = page.query_selector_all(selector)
        for element in elements[:20]:  # Limit to prevent infinite loops
            try:
                if element.is_visible():
                    element.click()
                    page.wait_for_timeout(500)
            except:
                pass
    
    # 3. Handle common dynamic content patterns
    page.evaluate("""
        // Trigger common dynamic content loaders
        const events = ['scroll', 'resize', 'focus', 'mouseover'];
        events.forEach(event => {
            window.dispatchEvent(new Event(event));
        });
        
        // Try to expand FAQ sections
        const faqTriggers = document.querySelectorAll('[class*="faq"], [class*="question"], [class*="accordion"]');
        faqTriggers.forEach(trigger => {
            if (trigger.click) trigger.click();
        });
    """)
    
    page.wait_for_timeout(2000)
    
    # 4. Final scroll to top
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)


def _extract_links_from_html(html: str, base_url: str) -> List[str]:
    """Extract absolute HTTP(S) links from HTML content."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        links: List[str] = []
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith('#'):
                continue
            abs_url = urljoin(base_url, href)
            if abs_url.startswith('http'):
                links.append(abs_url)
        # De-duplicate while preserving order
        seen = set()
        unique_links = []
        for l in links:
            if l not in seen:
                seen.add(l)
                unique_links.append(l)
        return unique_links
    except Exception:
        return []


# Wrapper function for backward compatibility
def scrape_url(url: str, wait_until: str = "networkidle", timeout_ms: int = 60000, scroll_pages: int = 5) -> str:
    """Backward compatible wrapper for enhanced scraper."""
    return enhanced_scrape_url(url, wait_until, timeout_ms, scroll_pages, validate_quality=True)


if __name__ == "__main__":
    # Test the enhanced scraper
    test_url = "https://help.shopify.com/en/manual"
    try:
        content = enhanced_scrape_url(test_url)
        print(f"✅ Scraped {len(content)} characters")
        print(f"📝 Sample content:\n{content[:500]}...")
    except Exception as e:
        print(f"❌ Test failed: {e}")
