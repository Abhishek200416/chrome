import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FiChevronLeft, FiChevronRight, FiRotateCw, FiX, FiPlus, FiSettings, FiMessageSquare, FiLock } from 'react-icons/fi';
import VNCViewer from './VNCViewer';

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
  const [isLoading, setIsLoading] = useState(false);
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (activeTab && activeTab.url !== addressBarValue) {
      setAddressBarValue(activeTab.url);
    }
  }, [activeTabId, activeTab?.url]);

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
      <div 
        className="browser-content" 
        data-testid="browser-content"
        tabIndex={0}
        style={{ outline: 'none' }}
      >
        {activeTab ? (
          <>
            <VNCViewer 
              tabId={activeTabId}
              backendUrl={BACKEND_URL}
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