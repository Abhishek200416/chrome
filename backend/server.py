from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import asyncio
import json
import base64

from browser_manager import browser_manager
from automation_engine import AutomationEngine
from workflows.gmail_gemini_youtube import GmailGeminiYouTubeWorkflow

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")

manager = ConnectionManager()

# Models
class BrowserSettings(BaseModel):
    browser_type: Optional[str] = "chromium"
    headless: Optional[bool] = False
    viewport: Optional[Dict[str, int]] = {"width": 1920, "height": 1080}
    user_agent: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = "en-US"

class TabCreate(BaseModel):
    url: Optional[str] = "about:blank"
    profile: Optional[str] = "default"

class NavigateRequest(BaseModel):
    url: str

class AutomationSettings(BaseModel):
    human_delays: Optional[bool] = True
    step_timeout: Optional[int] = 30000
    retry_count: Optional[int] = 1
    screenshot_on_step: Optional[bool] = False

class WorkflowRequest(BaseModel):
    workflow_type: str  # "gmail_gemini_youtube"
    sender_filter: Optional[str] = "ChatGPT"
    page_id: str

class LLMConfig(BaseModel):
    api_key: str
    provider: str  # "openai", "anthropic", "gemini"
    model: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    page_id: str
    llm_config: Optional[LLMConfig] = None

# Store active tabs and contexts
active_tabs = {}  # page_id -> {context_id, page, title, url, favicon}
active_contexts = {}  # context_id -> {pages: []}

# Initialize browser on startup
@app.on_event("startup")
async def startup_event():
    await browser_manager.initialize()
    logger.info("Browser Manager initialized")
    
    # Create default context and page
    context_id, context = await browser_manager.create_context("default")
    page_id, page = await browser_manager.create_page(context_id)
    
    active_contexts[context_id] = {"pages": [page_id]}
    active_tabs[page_id] = {
        "context_id": context_id,
        "page": page,
        "title": "New Tab",
        "url": "about:blank",
        "favicon": ""
    }
    
    # Navigate to a default page
    await page.goto("about:blank")
    logger.info(f"Default tab created: {page_id}")

@app.on_event("shutdown")
async def shutdown_event():
    await browser_manager.cleanup()
    client.close()
    logger.info("Application shutdown complete")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Chrome Browser Automation API", "status": "running"}

@api_router.get("/browser/status")
async def get_browser_status():
    return {
        "browser_type": browser_manager.settings["browser_type"],
        "headless": browser_manager.settings["headless"],
        "active_contexts": len(browser_manager.contexts),
        "active_pages": len(browser_manager.pages),
        "settings": browser_manager.settings
    }

@api_router.post("/browser/settings")
async def update_browser_settings(settings: BrowserSettings):
    try:
        # Store current tab info before restart
        tabs_backup = []
        for page_id, tab_info in active_tabs.items():
            page = tab_info["page"]
            try:
                tabs_backup.append({
                    "url": page.url if page else tab_info["url"],
                    "title": await page.title() if page else tab_info["title"]
                })
            except:
                tabs_backup.append({
                    "url": tab_info.get("url", "about:blank"),
                    "title": tab_info.get("title", "New Tab")
                })
        
        # Update settings (this may restart browser)
        await browser_manager.update_settings(settings.dict(exclude_none=True))
        
        # Clear old tabs and contexts
        active_tabs.clear()
        active_contexts.clear()
        
        # Recreate default context
        context_id, context = await browser_manager.create_context("default")
        active_contexts[context_id] = {"pages": [], "profile": "default"}
        
        # Recreate tabs with backed up URLs
        for tab_data in tabs_backup[:3]:  # Limit to 3 tabs to avoid issues
            page_id, page = await browser_manager.create_page(context_id)
            active_contexts[context_id]["pages"].append(page_id)
            active_tabs[page_id] = {
                "context_id": context_id,
                "page": page,
                "title": tab_data["title"],
                "url": tab_data["url"],
                "favicon": ""
            }
            try:
                await page.goto(tab_data["url"], wait_until="domcontentloaded", timeout=10000)
            except:
                pass
        
        # If no tabs were backed up, create a default one
        if not tabs_backup:
            page_id, page = await browser_manager.create_page(context_id)
            active_contexts[context_id]["pages"].append(page_id)
            active_tabs[page_id] = {
                "context_id": context_id,
                "page": page,
                "title": "New Tab",
                "url": "about:blank",
                "favicon": ""
            }
            await page.goto("about:blank")
        
        return {"success": True, "settings": browser_manager.settings}
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tabs")
async def get_tabs():
    tabs_list = []
    for page_id, tab_info in active_tabs.items():
        page = tab_info["page"]
        tabs_list.append({
            "id": page_id,
            "title": await page.title() if page else tab_info["title"],
            "url": page.url if page else tab_info["url"],
            "favicon": tab_info.get("favicon", "")
        })
    return {"tabs": tabs_list}

@api_router.post("/tabs")
async def create_tab(tab_request: TabCreate):
    try:
        # Get or create context
        profile = tab_request.profile or "default"
        context_id = None
        
        # Find existing context for this profile
        for cid, ctx_info in active_contexts.items():
            if ctx_info.get("profile") == profile:
                context_id = cid
                break
        
        # Create new context if not found
        if not context_id:
            context_id, context = await browser_manager.create_context(profile)
            active_contexts[context_id] = {"pages": [], "profile": profile}
        
        # Create new page
        page_id, page = await browser_manager.create_page(context_id)
        
        active_contexts[context_id]["pages"].append(page_id)
        active_tabs[page_id] = {
            "context_id": context_id,
            "page": page,
            "title": "New Tab",
            "url": tab_request.url or "about:blank",
            "favicon": ""
        }
        
        # Navigate if URL provided
        if tab_request.url and tab_request.url != "about:blank":
            await page.goto(tab_request.url, wait_until="domcontentloaded")
        
        # Broadcast tab creation
        await manager.broadcast({
            "type": "tab_created",
            "data": {
                "id": page_id,
                "title": await page.title(),
                "url": page.url
            }
        })
        
        return {
            "success": True,
            "tab": {
                "id": page_id,
                "title": await page.title(),
                "url": page.url
            }
        }
    except Exception as e:
        logger.error(f"Failed to create tab: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/tabs/{page_id}")
async def close_tab(page_id: str):
    try:
        if page_id not in active_tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        tab_info = active_tabs[page_id]
        context_id = tab_info["context_id"]
        
        await browser_manager.close_page(page_id)
        
        # Remove from active tabs
        del active_tabs[page_id]
        
        # Remove from context pages list
        if context_id in active_contexts:
            active_contexts[context_id]["pages"].remove(page_id)
        
        # Broadcast tab closure
        await manager.broadcast({
            "type": "tab_closed",
            "data": {"id": page_id}
        })
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to close tab: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/tabs/{page_id}/navigate")
async def navigate_tab(page_id: str, request: NavigateRequest):
    try:
        if page_id not in active_tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        page = active_tabs[page_id]["page"]
        await page.goto(request.url, wait_until="domcontentloaded")
        
        # Update tab info
        active_tabs[page_id]["url"] = page.url
        active_tabs[page_id]["title"] = await page.title()
        
        # Broadcast navigation
        await manager.broadcast({
            "type": "tab_navigated",
            "data": {
                "id": page_id,
                "url": page.url,
                "title": await page.title()
            }
        })
        
        return {
            "success": True,
            "url": page.url,
            "title": await page.title()
        }
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tabs/{page_id}/screenshot")
async def get_tab_screenshot(page_id: str):
    try:
        if page_id not in active_tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        page = active_tabs[page_id].get("page")
        if not page or page.is_closed():
            raise HTTPException(status_code=404, detail="Page is closed")
        
        screenshot = await browser_manager.take_screenshot(page_id)
        
        return StreamingResponse(
            iter([screenshot]),
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        raise HTTPException(status_code=500, detail=f"Screenshot error: {str(e)}")

# Mouse and Keyboard Interaction APIs
class MouseClick(BaseModel):
    x: int
    y: int
    button: Optional[str] = "left"  # left, right, middle
    click_count: Optional[int] = 1

class KeyboardInput(BaseModel):
    text: str
    delay: Optional[int] = 50  # milliseconds between keystrokes

class ScrollInput(BaseModel):
    delta_x: Optional[int] = 0
    delta_y: int = 100

@api_router.post("/tabs/{page_id}/click")
async def click_on_page(page_id: str, click_data: MouseClick):
    """Send mouse click to the browser at specified coordinates"""
    try:
        if page_id not in active_tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        page = active_tabs[page_id].get("page")
        if not page or page.is_closed():
            raise HTTPException(status_code=404, detail="Page is closed")
        
        # Perform mouse click at coordinates
        await page.mouse.click(
            click_data.x, 
            click_data.y,
            button=click_data.button,
            click_count=click_data.click_count
        )
        
        logger.info(f"Clicked at ({click_data.x}, {click_data.y}) on tab {page_id}")
        
        return {"success": True, "x": click_data.x, "y": click_data.y}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Click failed: {e}")
        raise HTTPException(status_code=500, detail=f"Click error: {str(e)}")

@api_router.post("/tabs/{page_id}/type")
async def type_on_page(page_id: str, keyboard_data: KeyboardInput):
    """Send keyboard input to the browser"""
    try:
        if page_id not in active_tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        page = active_tabs[page_id].get("page")
        if not page or page.is_closed():
            raise HTTPException(status_code=404, detail="Page is closed")
        
        # Type text with human-like delays
        await page.keyboard.type(keyboard_data.text, delay=keyboard_data.delay)
        
        logger.info(f"Typed text on tab {page_id}")
        
        return {"success": True, "text_length": len(keyboard_data.text)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Typing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Typing error: {str(e)}")

@api_router.post("/tabs/{page_id}/keypress")
async def press_key(page_id: str, key: str):
    """Press a specific key (Enter, Backspace, etc.)"""
    try:
        if page_id not in active_tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        page = active_tabs[page_id].get("page")
        if not page or page.is_closed():
            raise HTTPException(status_code=404, detail="Page is closed")
        
        # Press the specified key
        await page.keyboard.press(key)
        
        logger.info(f"Pressed key '{key}' on tab {page_id}")
        
        return {"success": True, "key": key}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Key press failed: {e}")
        raise HTTPException(status_code=500, detail=f"Key press error: {str(e)}")

@api_router.post("/tabs/{page_id}/scroll")
async def scroll_page(page_id: str, scroll_data: ScrollInput):
    """Scroll the page"""
    try:
        if page_id not in active_tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        page = active_tabs[page_id].get("page")
        if not page or page.is_closed():
            raise HTTPException(status_code=404, detail="Page is closed")
        
        # Scroll using mouse wheel
        await page.mouse.wheel(scroll_data.delta_x, scroll_data.delta_y)
        
        logger.info(f"Scrolled page {page_id}")
        
        return {"success": True, "delta_y": scroll_data.delta_y}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scroll failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scroll error: {str(e)}")

@api_router.post("/automation/workflow")
async def run_workflow(workflow_request: WorkflowRequest):
    try:
        page_id = workflow_request.page_id
        
        if page_id not in active_tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        page = active_tabs[page_id]["page"]
        automation = AutomationEngine(page)
        
        if workflow_request.workflow_type == "gmail_gemini_youtube":
            workflow = GmailGeminiYouTubeWorkflow(automation)
            result = await workflow.run_full_workflow(workflow_request.sender_filter)
            
            return result
        else:
            raise HTTPException(status_code=400, detail="Unknown workflow type")
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/automation/settings")
async def update_automation_settings(settings: AutomationSettings):
    # Store settings globally (can be per-page later)
    return {"success": True, "settings": settings.dict()}

@api_router.post("/llm/validate")
async def validate_llm_key(config: LLMConfig):
    """Validate LLM API key"""
    # This is a placeholder - actual validation would test the API
    try:
        # Store in database if valid
        llm_doc = {
            "id": str(uuid.uuid4()),
            "provider": config.provider,
            "model": config.model,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "api_key_hash": config.api_key[:8] + "*" * 20  # Store only partial for security
        }
        
        await db.llm_configs.insert_one(llm_doc)
        
        return {
            "success": True,
            "provider": config.provider,
            "model": config.model
        }
    except Exception as e:
        logger.error(f"LLM key validation failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid API key")

@api_router.get("/llm/config")
async def get_llm_config():
    """Get stored LLM configuration"""
    config = await db.llm_configs.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if config:
        return {"success": True, "config": config}
    return {"success": False, "config": None}

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "get_tabs":
                tabs_list = []
                for page_id, tab_info in active_tabs.items():
                    page = tab_info["page"]
                    tabs_list.append({
                        "id": page_id,
                        "title": await page.title() if page else tab_info["title"],
                        "url": page.url if page else tab_info["url"],
                    })
                await websocket.send_json({"type": "tabs_update", "data": tabs_list})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)