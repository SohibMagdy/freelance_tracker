"""
truelancer.py — Scraper for Truelancer (truelancer.com) freelance platform.

Uses Playwright sync API with a persistent headless browser for JavaScript
rendering. The browser is reused across scrape cycles for performance.
Falls back to requests/BeautifulSoup if Playwright is unavailable.
"""

import re
from typing import List, Dict

from .base import BaseScraper
from src.utils.crash_logger import get_logger

# Flag to track Playwright availability
_PLAYWRIGHT_AVAILABLE = True
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False


class TruelancerScraper(BaseScraper):
    """
    Scraper for Truelancer freelance projects.
    Uses a persistent headless Chromium browser via Playwright.
    The browser instance is shared across all scrape cycles (class-level).
    """

    platform_name = "Truelancer"
    platform_key = "truelancer"
    base_url = "https://www.truelancer.com"

    # ==========================================
    # CLASS-LEVEL BROWSER MANAGEMENT
    # ==========================================
    # Shared across all instances — avoids launching a new browser every cycle.

    _playwright_instance = None
    _browser = None
    _context = None

    @classmethod
    def _get_context(cls):
        """
        Get or create the shared browser context.
        Launches headless Chromium on first call, reuses it after.
        """
        if cls._browser is None or not cls._browser.is_connected():
            # Close stale resources if any
            cls._cleanup()

            print("[TruelancerScraper] Launching headless browser...")
            cls._playwright_instance = sync_playwright().start()
            cls._browser = cls._playwright_instance.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-images",          # skip images for speed
                ]
            )
            cls._context = cls._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
            )
            print("[TruelancerScraper] Browser ready.")

        return cls._context

    @classmethod
    def _cleanup(cls):
        """Close browser and Playwright resources."""
        try:
            if cls._context:
                cls._context.close()
                cls._context = None
        except Exception:
            cls._context = None

        try:
            if cls._browser:
                cls._browser.close()
                cls._browser = None
        except Exception:
            cls._browser = None

        try:
            if cls._playwright_instance:
                cls._playwright_instance.stop()
                cls._playwright_instance = None
        except Exception:
            cls._playwright_instance = None

    @classmethod
    def shutdown(cls):
        """Public method for clean shutdown. Called by MonitorThread on stop."""
        if cls._browser is not None:
            print("[TruelancerScraper] Closing browser...")
            cls._cleanup()
            print("[TruelancerScraper] Browser closed.")

    # ==========================================
    # SCRAPE
    # ==========================================

    def scrape(self) -> List[Dict[str, str]]:
        """
        Scrape latest projects from Truelancer.

        Strategy:
          1. Try Playwright (headless browser) — handles JS-rendered content
          2. Fall back to requests/BeautifulSoup if Playwright is unavailable
        """
        if _PLAYWRIGHT_AVAILABLE:
            projects = self._scrape_with_playwright()
            if projects:
                return projects

        # Fallback: try simple HTTP request + HTML parsing
        projects = self._scrape_with_requests()
        if projects:
            return projects

        print("[TruelancerScraper] No projects found from any method.")
        return []

    # ==========================================
    # PLAYWRIGHT SCRAPING
    # ==========================================

    def _scrape_with_playwright(self) -> List[Dict[str, str]]:
        """Scrape Truelancer using headless Chromium via Playwright."""
        page = None
        try:
            context = self._get_context()
            page = context.new_page()

            url = f"{self.base_url}/freelance-jobs"
            print(f"[TruelancerScraper] Loading {url}...")

            # Navigate with timeout
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for job listings to appear
            # The page uses <a> tags with hrefs containing "freelance-project"
            page.wait_for_selector(
                'a[href*="freelance-project"]',
                timeout=15000,
                state="attached"
            )
            print("[TruelancerScraper] Page loaded, extracting projects...")

            # Extract project data from the rendered DOM
            projects = page.evaluate("""
                () => {
                    const results = [];
                    
                    // Find all project links
                    const projectLinks = document.querySelectorAll(
                        'a[href*="freelance-project"]'
                    );
                    
                    // Track seen hrefs to avoid duplicates
                    const seen = new Set();
                    
                    projectLinks.forEach(link => {
                        const href = link.href || '';
                        if (!href || seen.has(href)) return;
                        
                        // Skip "View & Apply" links — they duplicate the main card link
                        const linkText = (link.textContent || '').trim();
                        if (linkText === 'View & Apply' || linkText === 'View') return;
                        
                        seen.add(href);
                        
                        // The link text IS the title on Truelancer
                        const title = linkText;
                        if (!title || title.length < 5) return;
                        
                        // Find the parent card container and look for posted time
                        let parent = link.parentElement;
                        let postedTime = '';
                        let description = '';
                        
                        // Walk up to find sibling/child elements with metadata
                        for (let i = 0; i < 5 && parent; i++) {
                            const text = parent.textContent || '';
                            
                            // Extract "Posted: X ago" pattern
                            const timeMatch = text.match(/Posted:\\s*(.+?)(?:\\n|$)/i);
                            if (timeMatch && !postedTime) {
                                postedTime = timeMatch[1].trim();
                            }
                            
                            // Extract price/type info
                            const typeMatch = text.match(/(Fixed Price|Hourly)/i);
                            if (typeMatch && !description) {
                                description = typeMatch[1];
                                if (postedTime) {
                                    description += ' | ' + postedTime;
                                }
                            }
                            
                            parent = parent.parentElement;
                        }
                        
                        if (!description && postedTime) {
                            description = postedTime;
                        }
                        
                        results.push({
                            title: title,
                            link: href,
                            description: description || '',
                            posted: postedTime || ''
                        });
                    });
                    
                    return results;
                }
            """)

            # Format results
            formatted = []
            for p in projects:
                formatted.append({
                    "site": self.platform_name,
                    "title": p.get("title", ""),
                    "description": p.get("description", ""),
                    "link": p.get("link", ""),
                })

            print(f"[TruelancerScraper] Found {len(formatted)} projects.")
            return formatted

        except PWTimeoutError:
            print("[TruelancerScraper] Page load timed out (30s). Retrying next cycle.")
            get_logger().warning("Truelancer Playwright timeout (30s).")
            return []

        except Exception as e:
            print(f"[TruelancerScraper] Playwright error: {e}")
            get_logger().error("Truelancer Playwright error: %s", e, exc_info=True)
            # If browser crashed, reset for next attempt
            if "Target closed" in str(e) or "Browser" in str(e):
                print("[TruelancerScraper] Browser crashed. Will relaunch next cycle.")
                get_logger().warning("Truelancer browser crashed. Forcing cleanup.")
                self._cleanup()
            return []

        finally:
            # Always close the page to free memory, keep the browser alive
            if page:
                try:
                    page.close()
                except Exception:
                    pass

    # ==========================================
    # REQUESTS FALLBACK
    # ==========================================

    def _scrape_with_requests(self) -> List[Dict[str, str]]:
        """
        Fallback: parse Truelancer's server-rendered HTML with requests.
        Works if the page has SSR content.
        """
        import requests as req
        from bs4 import BeautifulSoup

        url = f"{self.base_url}/freelance-jobs"

        try:
            response = req.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"[TruelancerScraper] HTTP fallback failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        projects = []
        seen = set()

        # Find all links to freelance-project pages
        for link_tag in soup.find_all("a", href=True):
            href = link_tag["href"]
            if "freelance-project" not in href:
                continue

            full_url = self._fix_relative_link(href)
            if full_url in seen:
                continue

            title = link_tag.get_text(strip=True)

            # Skip "View & Apply" and very short/empty titles
            if not title or len(title) < 5 or title in ("View & Apply", "View"):
                continue

            seen.add(full_url)

            projects.append({
                "site": self.platform_name,
                "title": title,
                "description": "",
                "link": full_url,
            })

        if projects:
            print(f"[TruelancerScraper] Fallback found {len(projects)} projects.")

        return projects
