#!/usr/bin/env python3
"""
Test script for the enhanced stealth scraper.
Tests the fixes for RedBus and other protected sites.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from stealth_scraper import StealthScraper, StealthScraperError


async def test_stealth_scraper():
    """Test the stealth scraper with RedBus and other sites."""
    
    test_sites = [
        "https://www.redbus.in/",
        "https://httpbin.org/user-agent",  # Simple test site
        "https://example.com"  # Basic test
    ]
    
    scraper = StealthScraper()
    
    for url in test_sites:
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {url}")
        print(f"{'='*60}")
        
        try:
            content = await scraper.scrape_url_async(url)
            
            if content and len(content.strip()) > 50:
                print(f"✅ SUCCESS: Scraped {len(content)} characters")
                print(f"📝 Sample content (first 200 chars):")
                print(f"{content[:200]}...")
            else:
                print(f"⚠ WARNING: Content too short ({len(content) if content else 0} chars)")
                
        except StealthScraperError as e:
            print(f"❌ STEALTH ERROR: {e}")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
        
        print(f"\n{'─'*60}")


def test_sync_scraper():
    """Test the synchronous wrapper."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing synchronous wrapper")
    print(f"{'='*60}")
    
    scraper = StealthScraper()
    
    try:
        content = scraper.scrape_url("https://httpbin.org/user-agent")
        print(f"✅ SYNC SUCCESS: Scraped {len(content)} characters")
        print(f"📝 Content: {content[:200]}...")
    except Exception as e:
        print(f"❌ SYNC ERROR: {e}")


if __name__ == "__main__":
    print("🚀 Starting Stealth Scraper Tests")
    print("🔧 Testing fixes for:")
    print("   - Retry dependency issue (method_whitelist -> allowed_methods)")
    print("   - Network IO suspension errors")
    print("   - HTTP/2 protocol errors")
    print("   - Connection timeouts")
    
    # Test async scraper
    asyncio.run(test_stealth_scraper())
    
    # Test sync wrapper
    test_sync_scraper()
    
    print(f"\n🏁 Test completed!")
