import React, { useState } from 'react';
import { FiX } from 'react-icons/fi';
import axios from 'axios';
import { toast } from 'sonner';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

const SettingsPanel = ({ isOpen, onClose, browserSettings, onSettingsUpdate, onLLMConfigured }) => {
  const [llmProvider, setLlmProvider] = useState('openai');
  const [llmApiKey, setLlmApiKey] = useState('');
  const [llmModel, setLlmModel] = useState('');
  const [isSavingLLM, setIsSavingLLM] = useState(false);
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  const handleBrowserSettingChange = async (key, value) => {
    const newSettings = { ...browserSettings, [key]: value };
    onSettingsUpdate(newSettings);

    try {
      await axios.post(`${API}/browser/settings`, { [key]: value });
      toast.success('Settings updated');
    } catch (error) {
      toast.error('Failed to update settings');
    }
  };

  const handleSaveLLMKey = async () => {
    if (!llmApiKey.trim()) {
      toast.error('Please enter an API key');
      return;
    }

    setIsSavingLLM(true);
    try {
      const response = await axios.post(`${API}/llm/validate`, {
        api_key: llmApiKey,
        provider: llmProvider,
        model: llmModel || undefined
      });

      if (response.data.success) {
        toast.success('LLM API key saved successfully');
        onLLMConfigured();
        setLlmApiKey('');
      }
    } catch (error) {
      toast.error('Failed to validate API key');
    } finally {
      setIsSavingLLM(false);
    }
  };

  return (
    <>
      <div
        className={`panel-overlay ${isOpen ? 'open' : ''}`}
        onClick={onClose}
        data-testid="panel-overlay"
      />
      <div className={`side-panel ${isOpen ? 'open' : ''}`} data-testid="settings-panel">
        <div className="panel-header">
          <h2 className="panel-title">Settings</h2>
          <button className="close-panel" onClick={onClose} data-testid="close-settings">
            <FiX size={20} />
          </button>
        </div>

        <div className="panel-content">
          {/* Browser Settings */}
          <div className="settings-section">
            <h3 className="section-title">Browser Settings</h3>

            <div className="setting-item">
              <Label htmlFor="browser-type" className="setting-label">
                Browser Engine
              </Label>
              <Select
                value={browserSettings.browser_type}
                onValueChange={(value) => handleBrowserSettingChange('browser_type', value)}
              >
                <SelectTrigger data-testid="browser-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="chromium">Chromium</SelectItem>
                  <SelectItem value="firefox">Firefox</SelectItem>
                  <SelectItem value="webkit">WebKit</SelectItem>
                </SelectContent>
              </Select>
              <p className="setting-description">
                Choose the browser engine for automation
              </p>
            </div>

            <div className="setting-item">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Label htmlFor="headless" className="setting-label">
                  Headless Mode
                </Label>
                <Switch
                  id="headless"
                  checked={browserSettings.headless}
                  onCheckedChange={(checked) => handleBrowserSettingChange('headless', checked)}
                  data-testid="headless-switch"
                />
              </div>
              <p className="setting-description">
                Run browser without visible UI (better performance)
              </p>
            </div>

            <div className="setting-item">
              <Label htmlFor="viewport-width" className="setting-label">
                Viewport Size
              </Label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <Input
                  type="number"
                  value={browserSettings.viewport?.width || 1920}
                  onChange={(e) =>
                    handleBrowserSettingChange('viewport', {
                      ...browserSettings.viewport,
                      width: parseInt(e.target.value)
                    })
                  }
                  placeholder="Width"
                  data-testid="viewport-width-input"
                />
                <Input
                  type="number"
                  value={browserSettings.viewport?.height || 1080}
                  onChange={(e) =>
                    handleBrowserSettingChange('viewport', {
                      ...browserSettings.viewport,
                      height: parseInt(e.target.value)
                    })
                  }
                  placeholder="Height"
                  data-testid="viewport-height-input"
                />
              </div>
            </div>
          </div>

          {/* LLM Configuration */}
          <div className="settings-section">
            <h3 className="section-title">LLM Configuration (Optional)</h3>

            <div className="setting-item">
              <Label className="setting-label">Provider</Label>
              <Select value={llmProvider} onValueChange={setLlmProvider}>
                <SelectTrigger data-testid="llm-provider-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                  <SelectItem value="gemini">Google Gemini</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="setting-item">
              <Label className="setting-label">Model (Optional)</Label>
              <Input
                type="text"
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                placeholder="e.g., gpt-4, claude-3"
                data-testid="llm-model-input"
              />
              <p className="setting-description">
                Leave empty to use default model
              </p>
            </div>

            <div className="setting-item">
              <Label className="setting-label">API Key</Label>
              <Input
                type="password"
                value={llmApiKey}
                onChange={(e) => setLlmApiKey(e.target.value)}
                placeholder="Enter your API key"
                data-testid="llm-api-key-input"
              />
              <p className="setting-description">
                Your API key is securely stored and never shared
              </p>
            </div>

            <Button
              onClick={handleSaveLLMKey}
              disabled={isSavingLLM || !llmApiKey.trim()}
              className="w-full"
              data-testid="save-llm-key-button"
            >
              {isSavingLLM ? 'Validating...' : 'Save API Key'}
            </Button>
          </div>

          {/* Automation Settings */}
          <div className="settings-section">
            <h3 className="section-title">Automation Settings</h3>

            <div className="setting-item">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Label className="setting-label">Human-like Delays</Label>
                <Switch defaultChecked data-testid="human-delays-switch" />
              </div>
              <p className="setting-description">
                Add realistic delays between actions
              </p>
            </div>

            <div className="setting-item">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Label className="setting-label">Screenshot on Every Step</Label>
                <Switch data-testid="screenshot-step-switch" />
              </div>
              <p className="setting-description">
                Capture screenshots for debugging
              </p>
            </div>

            <div className="setting-item">
              <Label className="setting-label">Step Timeout (ms)</Label>
              <Input
                type="number"
                defaultValue="30000"
                placeholder="30000"
                data-testid="step-timeout-input"
              />
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default SettingsPanel;