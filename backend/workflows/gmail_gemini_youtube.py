from automation_engine import AutomationEngine
import asyncio
import re
from pathlib import Path
import os

class GmailGeminiYouTubeWorkflow:
    def __init__(self, automation: AutomationEngine):
        self.automation = automation
        self.extracted_data = {}

    async def read_gmail_latest(self, sender_filter: str = "ChatGPT"):
        """Read latest email from specific sender"""
        try:
            self.automation.log(f"Opening Gmail to read email from {sender_filter}")
            
            # Navigate to Gmail
            await self.automation.page.goto("https://mail.google.com", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Wait for inbox
            found = await self.automation.wait_for_selector('div[role="main"]', timeout=10000)
            if not found:
                self.automation.log("Gmail inbox not loaded", level="error")
                return False
            
            # Find latest email from sender
            email_selector = f'tr.zA:has-text("{sender_filter}")'
            found = await self.automation.wait_for_selector(email_selector, timeout=5000)
            
            if not found:
                self.automation.log(f"No email found from {sender_filter}", level="warning")
                return False
            
            # Click to open email
            await self.automation.click(email_selector)
            await asyncio.sleep(2)
            
            # Extract email content
            content_selector = 'div[data-message-id]'
            found = await self.automation.wait_for_selector(content_selector, timeout=5000)
            
            if found:
                content = await self.automation.get_text(content_selector)
                await self.extract_fields_from_email(content)
                self.automation.log("Email content extracted successfully")
                return True
            
            return False
            
        except Exception as e:
            self.automation.log(f"Gmail reading failed: {str(e)}", level="error")
            await self.automation.take_screenshot("gmail_error")
            return False

    async def extract_fields_from_email(self, content: str):
        """Extract structured fields from email content"""
        # Extract video prompt
        prompt_match = re.search(r'(?:Video Prompt|Prompt):\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if prompt_match:
            self.extracted_data['prompt'] = prompt_match.group(1).strip()
        
        # Extract title
        title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if title_match:
            self.extracted_data['title'] = title_match.group(1).strip()
        
        # Extract description
        desc_match = re.search(r'Description:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if desc_match:
            self.extracted_data['description'] = desc_match.group(1).strip()
        
        # Extract tags
        tags_match = re.search(r'Tags:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if tags_match:
            self.extracted_data['tags'] = tags_match.group(1).strip()
        
        # Extract visibility
        visibility_match = re.search(r'Visibility:\s*(Public|Private|Unlisted|Scheduled)', content, re.IGNORECASE)
        if visibility_match:
            self.extracted_data['visibility'] = visibility_match.group(1).strip()
        
        self.automation.log(f"Extracted data: {self.extracted_data}")

    async def generate_video_gemini(self):
        """Generate video using Gemini VEO3"""
        try:
            if 'prompt' not in self.extracted_data:
                self.automation.log("No prompt found for video generation", level="error")
                return False
            
            self.automation.log("Opening Gemini for video generation")
            
            # Navigate to Gemini (assuming it's available)
            await self.automation.page.goto("https://gemini.google.com", wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Look for VEO3 model selector (this is a placeholder - actual selector may vary)
            model_selector = 'button:has-text("VEO"), select[aria-label="Model"]'
            found = await self.automation.wait_for_selector(model_selector, timeout=5000)
            
            if found:
                await self.automation.click(model_selector)
                await asyncio.sleep(1)
                
                # Select VEO3 (placeholder selector)
                veo3_option = 'div[role="option"]:has-text("VEO3"), li:has-text("VEO3")'
                found_veo3 = await self.automation.wait_for_selector(veo3_option, timeout=3000)
                if found_veo3:
                    await self.automation.click(veo3_option)
                    await asyncio.sleep(1)
            
            # Find input field and paste prompt
            input_selector = 'textarea[placeholder], div[contenteditable="true"]'
            found = await self.automation.wait_for_selector(input_selector, timeout=5000)
            
            if not found:
                self.automation.log("Gemini input field not found", level="error")
                return False
            
            # Paste the prompt
            await self.automation.type_text(input_selector, self.extracted_data['prompt'], clear=True)
            await asyncio.sleep(1)
            
            # Click generate button
            generate_button = 'button:has-text("Generate"), button[aria-label="Send"]'
            await self.automation.click(generate_button)
            
            self.automation.log("Video generation started, waiting for completion...")
            
            # Wait for video generation to complete (this may take several minutes)
            # Look for download button or completion indicator
            await asyncio.sleep(5)
            
            # Wait for completion indicator (placeholder)
            completion_indicator = 'button:has-text("Download"), div:has-text("Video ready")'
            found = await self.automation.wait_for_selector(completion_indicator, timeout=300000)  # 5 min timeout
            
            if not found:
                self.automation.log("Video generation timeout", level="error")
                return False
            
            self.automation.log("Video generation completed")
            return True
            
        except Exception as e:
            self.automation.log(f"Gemini video generation failed: {str(e)}", level="error")
            await self.automation.take_screenshot("gemini_error")
            return False

    async def download_video(self) -> str:
        """Download generated video"""
        try:
            self.automation.log("Downloading video...")
            
            # Click download button
            download_button = 'button:has-text("Download"), a[download]'
            
            async def trigger_download():
                await self.automation.click(download_button)
            
            video_path = await self.automation.wait_for_download(trigger_download, timeout=60000)
            
            if video_path:
                # Rename with title if available
                if 'title' in self.extracted_data:
                    new_name = f"/tmp/downloads/{self.extracted_data['title']}.mp4"
                    os.rename(video_path, new_name)
                    video_path = new_name
                
                self.automation.log(f"Video downloaded: {video_path}")
                return video_path
            
            return ""
            
        except Exception as e:
            self.automation.log(f"Video download failed: {str(e)}", level="error")
            return ""

    async def upload_to_youtube(self, video_path: str):
        """Upload video to YouTube Studio"""
        try:
            self.automation.log("Opening YouTube Studio for upload")
            
            # Navigate to YouTube Studio
            await self.automation.page.goto("https://studio.youtube.com", wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Click upload button
            upload_button = 'button[aria-label="Create"], ytcp-button#create-icon'
            found = await self.automation.wait_for_selector(upload_button, timeout=10000)
            
            if not found:
                self.automation.log("YouTube upload button not found", level="error")
                return False
            
            await self.automation.click(upload_button)
            await asyncio.sleep(1)
            
            # Click "Upload videos"
            upload_videos_option = 'tp-yt-paper-item:has-text("Upload videos")'
            await self.automation.click(upload_videos_option)
            await asyncio.sleep(2)
            
            # Upload file
            file_input = 'input[type="file"]'
            await self.automation.page.set_input_files(file_input, video_path)
            
            self.automation.log("Video file uploaded, filling metadata...")
            await asyncio.sleep(5)
            
            # Fill title
            if 'title' in self.extracted_data:
                title_input = 'div#textbox[aria-label="Add a title"]'
                found = await self.automation.wait_for_selector(title_input, timeout=10000)
                if found:
                    await self.automation.type_text(title_input, self.extracted_data['title'])
            
            # Fill description
            if 'description' in self.extracted_data:
                desc_input = 'div#textbox[aria-label="Tell viewers about your video"]'
                found = await self.automation.wait_for_selector(desc_input, timeout=5000)
                if found:
                    await self.automation.type_text(desc_input, self.extracted_data['description'])
            
            # Add tags (if field is available)
            if 'tags' in self.extracted_data:
                # Tags might be in a different section, scroll if needed
                pass
            
            # Click "Next" through the steps
            for step in range(3):
                next_button = 'button:has-text("Next")'
                found = await self.automation.wait_for_selector(next_button, timeout=5000)
                if found:
                    await self.automation.click(next_button)
                    await asyncio.sleep(2)
            
            # Set visibility
            if 'visibility' in self.extracted_data:
                visibility = self.extracted_data['visibility'].lower()
                visibility_radio = f'tp-yt-paper-radio-button[name="{visibility}"]'
                found = await self.automation.wait_for_selector(visibility_radio, timeout=5000)
                if found:
                    await self.automation.click(visibility_radio)
                    await asyncio.sleep(1)
            
            # Click "Publish"
            publish_button = 'button:has-text("Publish")'
            found = await self.automation.wait_for_selector(publish_button, timeout=5000)
            
            if found:
                await self.automation.click(publish_button)
                await asyncio.sleep(3)
                
                self.automation.log("Video published successfully!")
                return True
            
            return False
            
        except Exception as e:
            self.automation.log(f"YouTube upload failed: {str(e)}", level="error")
            await self.automation.take_screenshot("youtube_error")
            return False

    async def cleanup_video(self, video_path: str):
        """Delete video file after upload"""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                self.automation.log(f"Deleted video file: {video_path}")
        except Exception as e:
            self.automation.log(f"Failed to delete video: {str(e)}", level="warning")

    async def run_full_workflow(self, sender_filter: str = "ChatGPT"):
        """Execute the complete workflow"""
        self.automation.log("Starting Gmail → Gemini → YouTube workflow")
        
        # Step 1: Read email
        success = await self.read_gmail_latest(sender_filter)
        if not success:
            return {"success": False, "error": "Failed to read Gmail"}
        
        # Step 2: Generate video
        success = await self.generate_video_gemini()
        if not success:
            return {"success": False, "error": "Failed to generate video"}
        
        # Step 3: Download video
        video_path = await self.download_video()
        if not video_path:
            return {"success": False, "error": "Failed to download video"}
        
        # Step 4: Upload to YouTube
        success = await self.upload_to_youtube(video_path)
        if not success:
            return {"success": False, "error": "Failed to upload to YouTube"}
        
        # Step 5: Cleanup
        await self.cleanup_video(video_path)
        
        self.automation.log("Workflow completed successfully!")
        return {
            "success": True,
            "data": self.extracted_data,
            "logs": self.automation.get_logs()
        }