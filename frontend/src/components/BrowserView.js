import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FiChevronLeft, FiChevronRight, FiRotateCw, FiX, FiPlus, FiSettings, FiMessageSquare, FiLock } from 'react-icons/fi';

const BrowserView = ({
  tabs,
  activeTabId,
  activeTab,
  onTabSelect,
  onTabClose,
  onNewTab,
  onNavigate,
  onOpenSettings,
  onOpenChat,
  llmConfigured,
  isCreatingTab,
  closingTabs
}) => {
  const [addressBarValue, setAddressBarValue] = useState('');
  const [screenshotUrl, setScreenshotUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const refreshIntervalRef = useRef(null);
  const imageRef = useRef(null);
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  useEffect(() => {
    if (activeTab) {
      setAddressBarValue(activeTab.url);
      setImageLoaded(false);
      loadScreenshot();
    }
  }, [activeTabId, activeTab]);

  const loadScreenshot = useCallback(async () => {
    if (!activeTabId) return;
    
    try {
      const timestamp = Date.now();
      setScreenshotUrl(`${API}/tabs/${activeTabId}/screenshot?t=${timestamp}`);
    } catch (error) {
      console.error('Failed to load screenshot:', error);
    }
  }, [activeTabId, API]);

  useEffect(() => {
    // Clear existing interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }

    // Refresh screenshot every 2 seconds for live preview
    if (activeTabId) {
      refreshIntervalRef.current = setInterval(() => {
        loadScreenshot();
      }, 2000);
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [activeTabId, loadScreenshot]);

  const handleAddressBarSubmit = (e) => {
    e.preventDefault();
    if (!activeTabId || !addressBarValue) return;

    let url = addressBarValue;
    
    // Add protocol if missing
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      // Check if it's a search query or URL
      if (url.includes(' ') || !url.includes('.')) {
        url = `https://www.google.com/search?q=${encodeURIComponent(url)}`;
      } else {
        url = `https://${url}`;
      }
    }

    setIsLoading(true);
    onNavigate(activeTabId, url);
    setTimeout(() => setIsLoading(false), 2000);
  };

  const handleRefresh = () => {
    if (activeTab && activeTabId) {
      setIsLoading(true);
      onNavigate(activeTabId, activeTab.url);
      setTimeout(() => setIsLoading(false), 2000);
    }
  };

  // Mouse click handler for browser interaction
  const handleBrowserClick = async (e) => {
    if (!activeTabId || !imageRef.current) return;
    
    const rect = imageRef.current.getBoundingClientRect();
    const x = Math.round((e.clientX - rect.left) * (1920 / rect.width));
    const y = Math.round((e.clientY - rect.top) * (1080 / rect.height));
    
    try {
      await fetch(`${API}/tabs/${activeTabId}/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y, button: 'left', click_count: 1 })
      });
      
      // Refresh screenshot after click
      setTimeout(() => loadScreenshot(), 500);
    } catch (error) {
      console.error('Click failed:', error);
    }
  };

  // Keyboard handler for browser interaction
  const handleBrowserKeyDown = async (e) => {
    if (!activeTabId) return;
    
    // Don't interfere with address bar
    if (e.target.tagName === 'INPUT') return;
    
    try {
      if (e.key.length === 1) {
        // Regular character
        await fetch(`${API}/tabs/${activeTabId}/type`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: e.key, delay: 50 })
        });
      } else {
        // Special keys (Enter, Backspace, etc.)
        await fetch(`${API}/tabs/${activeTabId}/keypress?key=${e.key}`, {
          method: 'POST'
        });
      }
      
      // Refresh screenshot after typing
      setTimeout(() => loadScreenshot(), 300);
    } catch (error) {
      console.error('Keyboard input failed:', error);
    }
  };

  // Scroll handler for browser interaction
  const handleBrowserScroll = async (e) => {
    if (!activeTabId) return;
    
    e.preventDefault();
    
    try {
      await fetch(`${API}/tabs/${activeTabId}/scroll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delta_x: 0, delta_y: e.deltaY })
      });
      
      // Refresh screenshot after scroll
      setTimeout(() => loadScreenshot(), 200);
    } catch (error) {
      console.error('Scroll failed:', error);
    }
  };

  // Add keyboard event listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Only handle keyboard when browser content is focused
      if (document.activeElement.tagName !== 'INPUT' && activeTabId) {
        handleBrowserKeyDown(e);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeTabId]);

  return (
    <div className="browser-chrome" data-testid="browser-chrome">
      {/* Tab Bar */}
      <div className="browser-header">
        <div className="tab-bar" data-testid="tab-bar">
          {tabs.map((tab) => (
            <div
              key={tab.id}
              className={`tab ${tab.id === activeTabId ? 'active' : ''} ${closingTabs.has(tab.id) ? 'closing' : ''}`}
              onClick={() => !closingTabs.has(tab.id) && onTabSelect(tab.id)}
              data-testid={`tab-${tab.id}`}
            >
              <div className="tab-favicon" data-testid="tab-favicon">
                {tab.favicon ? (
                  <img src={tab.favicon} alt="" width="16" height="16" />
                ) : (
                  <div style={{ width: 16, height: 16, background: '#5f6368', borderRadius: '50%' }} />
                )}
              </div>
              <div className="tab-title" data-testid="tab-title">
                {tab.title || 'New Tab'}
              </div>
              <button
                className="tab-close"
                onClick={(e) => {
                  e.stopPropagation();
                  onTabClose(tab.id);
                }}
                disabled={closingTabs.has(tab.id)}
                data-testid={`tab-close-${tab.id}`}
              >
                <FiX size={14} />
              </button>
            </div>
          ))}
          <button
            className="new-tab-button"
            onClick={() => onNewTab()}
            disabled={isCreatingTab}
            title="New tab"
            data-testid="new-tab-button"
          >
            {isCreatingTab ? (
              <FiRotateCw size={16} className="spinner" />
            ) : (
              <FiPlus size={18} />
            )}
          </button>
        </div>

        {/* Toolbar */}
        <div className="toolbar" data-testid="toolbar">
          <div className="nav-buttons">
            <button
              className="nav-button"
              disabled={!activeTab}
              title="Back"
              data-testid="back-button"
            >
              <FiChevronLeft size={20} />
            </button>
            <button
              className="nav-button"
              disabled={!activeTab}
              title="Forward"
              data-testid="forward-button"
            >
              <FiChevronRight size={20} />
            </button>
            <button
              className="nav-button"
              onClick={handleRefresh}
              disabled={!activeTab || isLoading}
              title="Refresh"
              data-testid="refresh-button"
            >
              <FiRotateCw size={18} className={isLoading ? 'spinner' : ''} />
            </button>
          </div>

          <form onSubmit={handleAddressBarSubmit} style={{ flex: 1 }}>
            <div className="address-bar" data-testid="address-bar">
              <FiLock size={16} color="#5f6368" />
              <input
                type="text"
                className="address-input"
                value={addressBarValue}
                onChange={(e) => setAddressBarValue(e.target.value)}
                placeholder="Search or enter URL"
                disabled={!activeTab}
                data-testid="address-input"
              />
            </div>
          </form>

          <div className="toolbar-actions">
            <button
              className="action-button"
              onClick={onOpenChat}
              title="Chat Assistant"
              data-testid="chat-button"
            >
              <FiMessageSquare size={18} />
              {llmConfigured && <div className="llm-indicator" data-testid="llm-indicator" />}
            </button>
            <button
              className="action-button"
              onClick={onOpenSettings}
              title="Settings"
              data-testid="settings-button"
            >
              <FiSettings size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Browser Content */}
      <div className="browser-content" data-testid="browser-content">
        {activeTab && screenshotUrl ? (
          <>
            <img
              src={screenshotUrl}
              alt="Page preview"
              className="page-preview"
              data-testid="page-preview"
              style={{ opacity: imageLoaded ? 1 : 0.7 }}
              onLoad={() => setImageLoaded(true)}
              onError={() => {
                setScreenshotUrl(null);
                setImageLoaded(false);
              }}
            />
            {isLoading && (
              <div className="loading-overlay" data-testid="loading-overlay">
                <FiRotateCw size={32} className="spinner" color="#5f6368" />
              </div>
            )}
          </>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            background: '#fff',
            color: '#5f6368',
            fontSize: '16px'
          }}>
            {tabs.length === 0 ? 'No tabs open - Click + to create a new tab' : 'Loading...'}
          </div>
        )}
      </div>
    </div>
  );
};

export default BrowserView;