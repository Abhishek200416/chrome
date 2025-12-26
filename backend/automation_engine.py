from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
import asyncio
import logging
from typing import Dict, Any, Optional, List
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class AutomationEngine:
    def __init__(self, page: Page):
        self.page = page
        self.logs: List[Dict[str, Any]] = []
        self.screenshots: List[str] = []
        self.settings = {
            "human_delays": True,
            "step_timeout": 30000,
            "retry_count": 1,
            "screenshot_on_step": False
        }

    def log(self, message: str, level: str = "info", **kwargs):
        """Add log entry"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logs.append(log_entry)
        getattr(logger, level)(message)

    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None):
        """Wait for element with retry"""
        timeout = timeout or self.settings["step_timeout"]
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            self.log(f"Element found: {selector}")
            return True
        except PlaywrightTimeout:
            self.log(f"Element not found: {selector}", level="warning")
            return False

    async def click(self, selector: str, retry: bool = True):
        """Click element with human-like delay"""
        try:
            if self.settings["human_delays"]:
                await asyncio.sleep(0.5)
            
            await self.page.click(selector, timeout=self.settings["step_timeout"])
            self.log(f"Clicked: {selector}")
            
            if self.settings["screenshot_on_step"]:
                await self.take_screenshot(f"click_{selector}")
            
            return True
        except Exception as e:
            self.log(f"Click failed on {selector}: {str(e)}", level="error")
            if retry and self.settings["retry_count"] > 0:
                self.log("Retrying click...")
                await asyncio.sleep(1)
                return await self.click(selector, retry=False)
            return False

    async def type_text(self, selector: str, text: str, clear: bool = True):
        """Type text with human-like delay"""
        try:
            if clear:
                await self.page.fill(selector, "")
            
            if self.settings["human_delays"]:
                # Type character by character with delays
                for char in text:
                    await self.page.type(selector, char, delay=50)
                    await asyncio.sleep(0.05)
            else:
                await self.page.fill(selector, text)
            
            self.log(f"Typed text into: {selector}")
            
            if self.settings["screenshot_on_step"]:
                await self.take_screenshot(f"type_{selector}")
            
            return True
        except Exception as e:
            self.log(f"Type failed on {selector}: {str(e)}", level="error")
            return False

    async def scroll_to(self, selector: Optional[str] = None, y: Optional[int] = None):
        """Scroll to element or position"""
        try:
            if selector:
                await self.page.evaluate(f'document.querySelector("{selector}").scrollIntoView()')
            elif y is not None:
                await self.page.evaluate(f'window.scrollTo(0, {y})')
            
            if self.settings["human_delays"]:
                await asyncio.sleep(0.3)
            
            self.log(f"Scrolled to: {selector or y}")
            return True
        except Exception as e:
            self.log(f"Scroll failed: {str(e)}", level="error")
            return False

    async def wait_for_navigation(self, timeout: Optional[int] = None):
        """Wait for page navigation"""
        timeout = timeout or self.settings["step_timeout"]
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            self.log("Navigation completed")
            return True
        except PlaywrightTimeout:
            self.log("Navigation timeout", level="warning")
            return False

    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content from element"""
        try:
            text = await self.page.text_content(selector, timeout=self.settings["step_timeout"])
            self.log(f"Got text from {selector}: {text[:50]}...")
            return text
        except Exception as e:
            self.log(f"Get text failed on {selector}: {str(e)}", level="error")
            return None

    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get attribute value from element"""
        try:
            value = await self.page.get_attribute(selector, attribute, timeout=self.settings["step_timeout"])
            self.log(f"Got attribute {attribute} from {selector}: {value}")
            return value
        except Exception as e:
            self.log(f"Get attribute failed: {str(e)}", level="error")
            return None

    async def take_screenshot(self, name: str = "step") -> str:
        """Take screenshot and return path"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/tmp/screenshots/{name}_{timestamp}.png"
            Path("/tmp/screenshots").mkdir(exist_ok=True)
            
            await self.page.screenshot(path=filename, full_page=False)
            self.screenshots.append(filename)
            self.log(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            self.log(f"Screenshot failed: {str(e)}", level="error")
            return ""

    async def wait_for_download(self, trigger_action, timeout: int = 30000) -> Optional[str]:
        """Wait for file download"""
        try:
            async with self.page.expect_download(timeout=timeout) as download_info:
                await trigger_action()
            
            download = await download_info.value
            filename = download.suggested_filename
            save_path = f"/tmp/downloads/{filename}"
            
            Path("/tmp/downloads").mkdir(exist_ok=True)
            await download.save_as(save_path)
            
            self.log(f"File downloaded: {filename}")
            return save_path
        except Exception as e:
            self.log(f"Download failed: {str(e)}", level="error")
            return None

    def update_settings(self, new_settings: dict):
        """Update automation settings"""
        self.settings.update(new_settings)
        self.log(f"Settings updated: {new_settings}")

    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all logs"""
        return self.logs

    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
        self.screenshots = []
        self.log("Logs cleared")