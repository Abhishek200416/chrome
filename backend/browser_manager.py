from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import asyncio
import os
from pathlib import Path
import logging
from typing import Dict, Optional, List
import uuid

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.user_data_dir = Path("/tmp/browser_profiles")
        self.user_data_dir.mkdir(exist_ok=True)
        self.settings = {
            "browser_type": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": None,
            "timezone": None,
            "language": "en-US"
        }

    async def initialize(self):
        """Initialize Playwright and launch browser"""
        try:
            self.playwright = await async_playwright().start()
            await self.launch_browser()
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def launch_browser(self):
        """Launch browser with current settings"""
        try:
            browser_type = getattr(self.playwright, self.settings["browser_type"])
            
            # Launch args for VNC display support
            launch_args = [
                "--no-sandbox", 
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
            
            # If headed mode, use VNC display
            if not self.settings["headless"]:
                os.environ["DISPLAY"] = ":99"
            
            self.browser = await browser_type.launch(
                headless=self.settings["headless"],
                args=launch_args
            )
            logger.info(f"Browser launched: {self.settings['browser_type']} (headless={self.settings['headless']}, DISPLAY={os.environ.get('DISPLAY', 'None')})")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    async def create_context(self, profile_name: str = "default", **kwargs):
        """Create a new browser context (profile)"""
        context_id = str(uuid.uuid4())
        
        context_options = {
            "viewport": self.settings["viewport"],
            "user_agent": self.settings["user_agent"],
            "timezone_id": self.settings["timezone"],
            "locale": self.settings["language"],
        }
        
        # Add persistent storage
        profile_dir = self.user_data_dir / profile_name
        profile_dir.mkdir(exist_ok=True)
        
        context_options.update(kwargs)
        
        context = await self.browser.new_context(**context_options)
        self.contexts[context_id] = context
        
        logger.info(f"Created context: {context_id} with profile: {profile_name}")
        return context_id, context

    async def create_page(self, context_id: str):
        """Create a new page in a context"""
        if context_id not in self.contexts:
            raise ValueError(f"Context {context_id} not found")
        
        page_id = str(uuid.uuid4())
        context = self.contexts[context_id]
        page = await context.new_page()
        
        self.pages[page_id] = page
        logger.info(f"Created page: {page_id} in context: {context_id}")
        
        return page_id, page

    async def navigate(self, page_id: str, url: str):
        """Navigate page to URL"""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        
        page = self.pages[page_id]
        await page.goto(url, wait_until="domcontentloaded")
        logger.info(f"Navigated page {page_id} to {url}")

    async def get_page(self, page_id: str) -> Optional[Page]:
        """Get page by ID"""
        return self.pages.get(page_id)

    async def close_page(self, page_id: str):
        """Close a page"""
        if page_id in self.pages:
            await self.pages[page_id].close()
            del self.pages[page_id]
            logger.info(f"Closed page: {page_id}")

    async def close_context(self, context_id: str):
        """Close a context"""
        if context_id in self.contexts:
            # Close all pages in this context
            pages_to_close = [pid for pid, page in self.pages.items() 
                            if page.context == self.contexts[context_id]]
            for pid in pages_to_close:
                await self.close_page(pid)
            
            await self.contexts[context_id].close()
            del self.contexts[context_id]
            logger.info(f"Closed context: {context_id}")

    async def take_screenshot(self, page_id: str, path: Optional[str] = None) -> bytes:
        """Take screenshot of page"""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        
        page = self.pages[page_id]
        # Optimize screenshot: reduce quality for faster loading, use JPEG
        screenshot = await page.screenshot(
            full_page=False, 
            type="jpeg", 
            quality=75,
            animations="disabled"  # Disable animations for consistent screenshots
        )
        
        if path:
            with open(path, "wb") as f:
                f.write(screenshot)
        
        return screenshot

    async def update_settings(self, new_settings: dict):
        """Update browser settings and restart if needed"""
        restart_required = False
        
        for key in ["browser_type", "headless"]:
            if key in new_settings and new_settings[key] != self.settings[key]:
                restart_required = True
        
        self.settings.update(new_settings)
        
        if restart_required and self.browser:
            await self.browser.close()
            await self.launch_browser()
            logger.info("Browser restarted with new settings")

    async def cleanup(self):
        """Cleanup all resources"""
        for page_id in list(self.pages.keys()):
            await self.close_page(page_id)
        
        for context_id in list(self.contexts.keys()):
            await self.close_context(context_id)
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Browser manager cleaned up")

# Global browser manager instance
browser_manager = BrowserManager()