#!/usr/bin/env python3
"""
Chrome Browser Automation Backend Testing Suite
Tests all critical backend APIs for the browser automation platform
"""

import requests
import json
import time
import sys
from typing import Dict, List, Optional
import base64

# Configuration
BACKEND_URL = "https://autopilot-web.preview.emergentagent.com/api"
TIMEOUT = 10
TEST_URLS = [
    "https://www.google.com",
    "https://github.com",
    "https://playwright.dev",
    "https://www.youtube.com"
]

class BrowserAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.created_tabs = []
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        
        if success:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
    
    def test_api_root(self) -> bool:
        """Test GET /api/ - API status"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "status" in data:
                    self.log_result("API Root Status", True, f"Status: {data.get('status')}")
                    return True
                else:
                    self.log_result("API Root Status", False, "Missing required fields in response")
                    return False
            else:
                self.log_result("API Root Status", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("API Root Status", False, f"Exception: {str(e)}")
            return False
    
    def test_browser_status(self) -> bool:
        """Test GET /api/browser/status"""
        try:
            response = self.session.get(f"{self.base_url}/browser/status")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["browser_type", "headless", "active_contexts", "active_pages"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("Browser Status", True, 
                                  f"Browser: {data['browser_type']}, Headless: {data['headless']}, "
                                  f"Contexts: {data['active_contexts']}, Pages: {data['active_pages']}")
                    return True
                else:
                    self.log_result("Browser Status", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_result("Browser Status", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Browser Status", False, f"Exception: {str(e)}")
            return False
    
    def test_create_tab(self, url: Optional[str] = None) -> Optional[str]:
        """Test POST /api/tabs - Create new tab"""
        try:
            payload = {}
            if url:
                payload["url"] = url
            
            response = self.session.post(f"{self.base_url}/tabs", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "tab" in data:
                    tab_id = data["tab"]["id"]
                    tab_title = data["tab"]["title"]
                    tab_url = data["tab"]["url"]
                    self.created_tabs.append(tab_id)
                    self.log_result(f"Create Tab ({url or 'default'})", True, 
                                  f"ID: {tab_id}, Title: {tab_title}, URL: {tab_url}")
                    return tab_id
                else:
                    self.log_result(f"Create Tab ({url or 'default'})", False, "Invalid response format")
                    return None
            else:
                self.log_result(f"Create Tab ({url or 'default'})", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_result(f"Create Tab ({url or 'default'})", False, f"Exception: {str(e)}")
            return None
    
    def test_list_tabs(self) -> List[Dict]:
        """Test GET /api/tabs - List all tabs"""
        try:
            response = self.session.get(f"{self.base_url}/tabs")
            if response.status_code == 200:
                data = response.json()
                if "tabs" in data:
                    tabs = data["tabs"]
                    self.log_result("List Tabs", True, f"Found {len(tabs)} tabs")
                    for tab in tabs:
                        print(f"    Tab: {tab.get('id', 'N/A')} - {tab.get('title', 'N/A')} - {tab.get('url', 'N/A')}")
                    return tabs
                else:
                    self.log_result("List Tabs", False, "Missing 'tabs' field in response")
                    return []
            else:
                self.log_result("List Tabs", False, f"HTTP {response.status_code}: {response.text}")
                return []
        except Exception as e:
            self.log_result("List Tabs", False, f"Exception: {str(e)}")
            return []
    
    def test_navigate_tab(self, tab_id: str, url: str) -> bool:
        """Test POST /api/tabs/{page_id}/navigate"""
        try:
            payload = {"url": url}
            response = self.session.post(f"{self.base_url}/tabs/{tab_id}/navigate", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    final_url = data.get("url", "N/A")
                    title = data.get("title", "N/A")
                    self.log_result(f"Navigate Tab to {url}", True, f"Final URL: {final_url}, Title: {title}")
                    return True
                else:
                    self.log_result(f"Navigate Tab to {url}", False, "Navigation not successful")
                    return False
            else:
                self.log_result(f"Navigate Tab to {url}", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result(f"Navigate Tab to {url}", False, f"Exception: {str(e)}")
            return False
    
    def test_screenshot_tab(self, tab_id: str) -> bool:
        """Test GET /api/tabs/{page_id}/screenshot"""
        try:
            response = self.session.get(f"{self.base_url}/tabs/{tab_id}/screenshot")
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "image/jpeg" in content_type:
                    screenshot_size = len(response.content)
                    self.log_result(f"Screenshot Tab {tab_id}", True, f"JPEG image received, size: {screenshot_size} bytes")
                    return True
                else:
                    self.log_result(f"Screenshot Tab {tab_id}", False, f"Wrong content type: {content_type}")
                    return False
            else:
                self.log_result(f"Screenshot Tab {tab_id}", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result(f"Screenshot Tab {tab_id}", False, f"Exception: {str(e)}")
            return False
    
    def test_close_tab(self, tab_id: str) -> bool:
        """Test DELETE /api/tabs/{page_id}"""
        try:
            response = self.session.delete(f"{self.base_url}/tabs/{tab_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result(f"Close Tab {tab_id}", True)
                    if tab_id in self.created_tabs:
                        self.created_tabs.remove(tab_id)
                    return True
                else:
                    self.log_result(f"Close Tab {tab_id}", False, "Close not successful")
                    return False
            else:
                self.log_result(f"Close Tab {tab_id}", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result(f"Close Tab {tab_id}", False, f"Exception: {str(e)}")
            return False
    
    def test_error_cases(self):
        """Test error handling"""
        print("\n=== Testing Error Cases ===")
        
        # Test navigation to non-existent tab
        fake_tab_id = "fake-tab-id-12345"
        try:
            response = self.session.post(f"{self.base_url}/tabs/{fake_tab_id}/navigate", 
                                       json={"url": "https://google.com"})
            if response.status_code == 404:
                self.log_result("Navigate Non-existent Tab", True, "Correctly returned 404")
            else:
                self.log_result("Navigate Non-existent Tab", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("Navigate Non-existent Tab", False, f"Exception: {str(e)}")
        
        # Test screenshot of non-existent tab
        try:
            response = self.session.get(f"{self.base_url}/tabs/{fake_tab_id}/screenshot")
            if response.status_code == 404:
                self.log_result("Screenshot Non-existent Tab", True, "Correctly returned 404")
            else:
                self.log_result("Screenshot Non-existent Tab", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("Screenshot Non-existent Tab", False, f"Exception: {str(e)}")
        
        # Test closing non-existent tab
        try:
            response = self.session.delete(f"{self.base_url}/tabs/{fake_tab_id}")
            if response.status_code == 404:
                self.log_result("Close Non-existent Tab", True, "Correctly returned 404")
            else:
                self.log_result("Close Non-existent Tab", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("Close Non-existent Tab", False, f"Exception: {str(e)}")
    
    def test_performance(self):
        """Test performance with multiple rapid operations"""
        print("\n=== Performance Testing ===")
        
        # Rapid tab creation
        start_time = time.time()
        rapid_tabs = []
        for i in range(5):
            tab_id = self.test_create_tab(f"https://www.google.com/search?q=test{i}")
            if tab_id:
                rapid_tabs.append(tab_id)
        creation_time = time.time() - start_time
        
        self.log_result("Rapid Tab Creation (5 tabs)", len(rapid_tabs) == 5, 
                       f"Created {len(rapid_tabs)}/5 tabs in {creation_time:.2f}s")
        
        # Navigate all tabs
        start_time = time.time()
        navigation_success = 0
        for i, tab_id in enumerate(rapid_tabs):
            if self.test_navigate_tab(tab_id, TEST_URLS[i % len(TEST_URLS)]):
                navigation_success += 1
        navigation_time = time.time() - start_time
        
        self.log_result("Rapid Navigation", navigation_success == len(rapid_tabs),
                       f"Navigated {navigation_success}/{len(rapid_tabs)} tabs in {navigation_time:.2f}s")
        
        # Take screenshots
        start_time = time.time()
        screenshot_success = 0
        for tab_id in rapid_tabs:
            if self.test_screenshot_tab(tab_id):
                screenshot_success += 1
        screenshot_time = time.time() - start_time
        
        self.log_result("Rapid Screenshots", screenshot_success == len(rapid_tabs),
                       f"Captured {screenshot_success}/{len(rapid_tabs)} screenshots in {screenshot_time:.2f}s")
        
        # Close all tabs
        for tab_id in rapid_tabs:
            self.test_close_tab(tab_id)
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Chrome Browser Automation Backend Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic API tests
        print("\n=== Basic API Tests ===")
        self.test_api_root()
        self.test_browser_status()
        
        # Tab management tests
        print("\n=== Tab Management Tests ===")
        
        # Create tabs with different URLs
        tab1 = self.test_create_tab()  # Default tab
        tab2 = self.test_create_tab("https://www.google.com")
        tab3 = self.test_create_tab("https://github.com")
        
        # List tabs
        tabs = self.test_list_tabs()
        
        # Navigation tests
        print("\n=== Navigation Tests ===")
        if tab1:
            self.test_navigate_tab(tab1, "https://playwright.dev")
            time.sleep(2)  # Wait for navigation
        
        if tab2:
            self.test_navigate_tab(tab2, "https://www.youtube.com")
            time.sleep(2)  # Wait for navigation
        
        # Screenshot tests
        print("\n=== Screenshot Tests ===")
        for tab_id in [tab1, tab2, tab3]:
            if tab_id:
                self.test_screenshot_tab(tab_id)
                time.sleep(1)  # Brief pause between screenshots
        
        # Test invalid URL navigation
        if tab3:
            self.test_navigate_tab(tab3, "invalid-url-test")
        
        # Error case testing
        self.test_error_cases()
        
        # Performance testing
        self.test_performance()
        
        # Clean up remaining tabs
        print("\n=== Cleanup ===")
        for tab_id in self.created_tabs.copy():
            self.test_close_tab(tab_id)
        
        # Final summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📊 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"  • {error}")
        
        return self.test_results['failed'] == 0

def main():
    """Main test execution"""
    tester = BrowserAPITester(BACKEND_URL)
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! Backend is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()