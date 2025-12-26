# Chrome-like Browser Automation Platform

A complete Chrome-like web interface that launches a real browser and provides both manual browsing and autonomous automation capabilities using Playwright.

## Features

### 🌐 Chrome-like Interface
- **Tab Management**: Create, switch, and close multiple tabs
- **Navigation**: Back, forward, refresh buttons
- **Address Bar**: Smart URL/search detection
- **Live Preview**: Real-time browser screenshots updating every 2 seconds

### ⚙️ Settings Panel (Slide-in from right)
- **Browser Settings**
  - Browser engine selection (Chromium/Firefox/WebKit)
  - Headless/headed mode toggle
  - Viewport size configuration
  - User agent customization
  - Timezone and language settings

- **LLM Configuration (Optional)**
  - Provider selection (OpenAI/Anthropic/Gemini)
  - Model specification
  - API key management
  - Secure key storage

- **Automation Controls**
  - Human-like delays toggle
  - Step timeout configuration
  - Retry count settings
  - Screenshot on every step option

### 💬 Chat Panel (Optional - requires LLM)
- Natural language browser control
- Real-time command execution
- Conversation history
- Context-aware automation

### 🤖 Autonomous Workflows

#### Gmail → Gemini → YouTube Workflow
Fully automated workflow that:
1. Opens Gmail and reads latest email from specified sender (e.g., ChatGPT)
2. Extracts fields:
   - Video Prompt
   - Title
   - Description
   - Tags
   - Visibility (Public/Private/Scheduled)
3. Opens Gemini in new tab
4. Selects VEO3 model
5. Pastes prompt and generates video
6. Downloads video when complete
7. Renames file with title
8. Opens YouTube Studio
9. Uploads video with metadata
10. Publishes and cleans up

## Architecture

### Backend (FastAPI + Playwright)
```
/app/backend/
├── server.py                          # Main FastAPI server with WebSocket support
├── browser_manager.py                 # Browser lifecycle management
├── automation_engine.py               # Core automation primitives
└── workflows/
    └── gmail_gemini_youtube.py       # Complete automation workflow
```

### Frontend (React + Tailwind)
```
/app/frontend/src/
├── App.js                             # Main application
├── components/
│   ├── BrowserView.js                # Chrome-like browser interface
│   ├── SettingsPanel.js              # Settings slide-in panel
│   └── ChatPanel.js                  # Chat assistant panel
└── App.css                           # Chrome-themed styling
```

## Tech Stack

**Backend:**
- FastAPI (REST + WebSocket)
- Playwright (Browser automation)
- Motor (MongoDB async driver)
- Python 3.11+

**Frontend:**
- React 19
- Tailwind CSS
- Radix UI components
- Socket.io-client
- Axios

## API Endpoints

### Browser Management
- `GET /api/browser/status` - Get browser status
- `POST /api/browser/settings` - Update browser settings

### Tab Management
- `GET /api/tabs` - List all tabs
- `POST /api/tabs` - Create new tab
- `DELETE /api/tabs/{page_id}` - Close tab
- `POST /api/tabs/{page_id}/navigate` - Navigate tab to URL
- `GET /api/tabs/{page_id}/screenshot` - Get live screenshot

### Automation
- `POST /api/automation/workflow` - Execute workflow
- `POST /api/automation/settings` - Update automation settings

### LLM Configuration
- `POST /api/llm/validate` - Validate and save API key
- `GET /api/llm/config` - Get current LLM config

### WebSocket
- `WS /ws` - Real-time updates for tabs, navigation, and automation

## Usage

### Manual Browsing
1. Application loads with one default tab
2. Enter URL in address bar or search term
3. Create new tabs with + button
4. Switch between tabs by clicking
5. Close tabs with X button

### Settings Configuration
1. Click Settings icon (gear) in toolbar
2. Configure browser settings as needed
3. Optionally add LLM API key for chat features
4. Adjust automation settings

### Chat Assistant (Optional)
1. Configure LLM API key in Settings first
2. Click Chat icon (message bubble) in toolbar
3. Type natural language commands
4. Browser executes actions automatically

### Running Workflows
```python
# Example: Execute Gmail → Gemini → YouTube workflow
POST /api/automation/workflow
{
  "workflow_type": "gmail_gemini_youtube",
  "sender_filter": "ChatGPT",
  "page_id": "active-tab-id"
}
```

## Key Design Principles

1. **Real Browser Control**: Uses actual Playwright browser, not API simulation
2. **Human-like Behavior**: Waits for elements, adds delays, scrolls naturally
3. **Error Handling**: Screenshots on failure, automatic retries
4. **Persistent Sessions**: Cookies and login states are maintained
5. **Multi-tab Support**: Independent tabs running simultaneously
6. **Live Preview**: Continuous screenshot updates for visibility
7. **Chrome UX**: Familiar interface for ease of use

## Environment Variables

### Backend (.env)
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
PLAYWRIGHT_BROWSERS_PATH="/pw-browsers"
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=<your-backend-url>
```

## Running the Application

### Backend
```bash
cd /app/backend
pip install -r requirements.txt
playwright install chromium
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend
```bash
cd /app/frontend
yarn install
yarn start
```

## Important Notes

### Headless Mode
- Currently configured for headless mode (no GUI)
- Required for server environments without X display
- Can be toggled in Settings for local development with GUI

### Browser Persistence
- Each profile maintains its own cookies, cache, and session
- Multiple profiles can be created for different use cases
- Default profile is created on startup

### Automation Rules
1. Never bypass security (CAPTCHA, 2FA)
2. Always wait for UI elements
3. Take screenshots on errors
4. Retry once before failing
5. Clean up temporary files after operations

### WebSocket Updates
- Tabs are synchronized across all connected clients
- Navigation events broadcast in real-time
- Automation progress streamed live

## Future Enhancements

1. **Multi-tab Grid View**: Visual preview of multiple tabs simultaneously
2. **Session Recording**: Video capture of automation runs
3. **Advanced Workflows**: More pre-built automation templates
4. **Profile Manager**: UI for creating and switching profiles
5. **Download Manager**: Built-in file download tracking
6. **Cookie Viewer**: Inspect and edit cookies directly
7. **Network Inspector**: Monitor HTTP requests
8. **Console Logs**: Real-time browser console output

## Security Considerations

- API keys are hashed before storage
- Browser runs in sandboxed environment
- CORS configured for specified origins only
- No external API calls (direct browser interaction only)
- User controls all automation actions

## Troubleshooting

### Browser won't start
- Ensure Playwright browsers are installed: `playwright install chromium`
- Check PLAYWRIGHT_BROWSERS_PATH environment variable
- For headed mode, ensure X server is running

### Screenshots not updating
- Check backend logs for errors
- Verify page_id is valid
- Ensure tab hasn't been closed

### Workflow fails
- Check automation logs in backend
- Verify selectors match current page structure
- Ensure sufficient timeout for slow-loading pages

## License

Built for autonomous browser control and automation tasks.

---

**Made with Emergent** 🚀
