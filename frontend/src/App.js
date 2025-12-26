import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import BrowserView from './components/BrowserView';
import SettingsPanel from './components/SettingsPanel';
import ChatPanel from './components/ChatPanel';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [tabs, setTabs] = useState([]);
  const [activeTabId, setActiveTabId] = useState(null);
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false);
  const [chatPanelOpen, setChatPanelOpen] = useState(false);
  const [llmConfigured, setLlmConfigured] = useState(false);
  const [socket, setSocket] = useState(null);
  const [browserSettings, setBrowserSettings] = useState({
    browser_type: 'chromium',
    headless: false,
    viewport: { width: 1920, height: 1080 }
  });

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io(BACKEND_URL, {
      transports: ['websocket'],
      reconnection: true
    });

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
    });

    newSocket.on('tab_created', (data) => {
      loadTabs();
    });

    newSocket.on('tab_closed', (data) => {
      loadTabs();
    });

    newSocket.on('tab_navigated', (data) => {
      loadTabs();
    });

    setSocket(newSocket);

    return () => newSocket.close();
  }, []);

  // Load tabs on mount
  useEffect(() => {
    loadTabs();
    checkLLMConfig();
  }, []);

  const loadTabs = async () => {
    try {
      const response = await axios.get(`${API}/tabs`);
      const tabsList = response.data.tabs;
      setTabs(tabsList);
      
      if (tabsList.length > 0 && !activeTabId) {
        setActiveTabId(tabsList[0].id);
      }
    } catch (error) {
      console.error('Failed to load tabs:', error);
      toast.error('Failed to load tabs');
    }
  };

  const checkLLMConfig = async () => {
    try {
      const response = await axios.get(`${API}/llm/config`);
      setLlmConfigured(response.data.success && response.data.config !== null);
    } catch (error) {
      console.error('Failed to check LLM config:', error);
    }
  };

  const createNewTab = async (url = 'https://www.google.com') => {
    try {
      const response = await axios.post(`${API}/tabs`, { url });
      if (response.data.success) {
        const newTab = response.data.tab;
        setActiveTabId(newTab.id);
        toast.success('New tab created');
      }
    } catch (error) {
      console.error('Failed to create tab:', error);
      toast.error('Failed to create tab');
    }
  };

  const closeTab = async (tabId) => {
    try {
      await axios.delete(`${API}/tabs/${tabId}`);
      
      if (activeTabId === tabId) {
        const remainingTabs = tabs.filter(t => t.id !== tabId);
        if (remainingTabs.length > 0) {
          setActiveTabId(remainingTabs[0].id);
        } else {
          setActiveTabId(null);
        }
      }
      toast.success('Tab closed');
    } catch (error) {
      console.error('Failed to close tab:', error);
      toast.error('Failed to close tab');
    }
  };

  const navigateTab = async (tabId, url) => {
    try {
      await axios.post(`${API}/tabs/${tabId}/navigate`, { url });
      toast.success('Navigated successfully');
    } catch (error) {
      console.error('Failed to navigate:', error);
      toast.error('Failed to navigate');
    }
  };

  const openSettings = () => {
    setChatPanelOpen(false);
    setSettingsPanelOpen(true);
  };

  const openChat = () => {
    if (!llmConfigured) {
      toast.error('Please configure LLM API key in Settings first');
      openSettings();
      return;
    }
    setSettingsPanelOpen(false);
    setChatPanelOpen(true);
  };

  const activeTab = tabs.find(t => t.id === activeTabId);

  return (
    <div className="app-container" data-testid="app-container">
      <BrowserView
        tabs={tabs}
        activeTabId={activeTabId}
        activeTab={activeTab}
        onTabSelect={setActiveTabId}
        onTabClose={closeTab}
        onNewTab={createNewTab}
        onNavigate={navigateTab}
        onOpenSettings={openSettings}
        onOpenChat={openChat}
        llmConfigured={llmConfigured}
      />

      <SettingsPanel
        isOpen={settingsPanelOpen}
        onClose={() => setSettingsPanelOpen(false)}
        browserSettings={browserSettings}
        onSettingsUpdate={setBrowserSettings}
        onLLMConfigured={() => {
          setLlmConfigured(true);
          toast.success('LLM configured successfully');
        }}
      />

      <ChatPanel
        isOpen={chatPanelOpen}
        onClose={() => setChatPanelOpen(false)}
        activeTabId={activeTabId}
      />

      <Toaster position="bottom-right" />
    </div>
  );
}

export default App;