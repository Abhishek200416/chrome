import React, { useState, useEffect, useRef } from 'react';
import { FiX, FiSend } from 'react-icons/fi';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Input } from './ui/input';

const ChatPanel = ({ isOpen, onClose, activeTabId }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !activeTabId) return;

    const userMessage = inputValue.trim();
    setInputValue('');

    // Add user message to chat
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    setIsSending(true);

    try {
      // For now, this is a placeholder
      // In a real implementation, this would call an LLM API to interpret
      // the command and execute browser actions
      
      const response = {
        role: 'assistant',
        content: `I understand you want me to: "${userMessage}". However, LLM-based chat control is currently in development. Please use the manual automation workflows from the toolbar for now.`
      };

      setMessages((prev) => [...prev, response]);
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to process message');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      <div
        className={`panel-overlay ${isOpen ? 'open' : ''}`}
        onClick={onClose}
        data-testid="chat-overlay"
      />
      <div className={`side-panel ${isOpen ? 'open' : ''}`} data-testid="chat-panel">
        <div className="panel-header">
          <h2 className="panel-title">Chat Assistant</h2>
          <button className="close-panel" onClick={onClose} data-testid="close-chat">
            <FiX size={20} />
          </button>
        </div>

        <div className="chat-messages" data-testid="chat-messages">
          {messages.length === 0 ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#9aa0a6',
              textAlign: 'center',
              padding: '40px'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>💬</div>
              <h3 style={{ fontSize: '18px', marginBottom: '8px', color: '#e8eaed' }}>
                Chat with Browser AI
              </h3>
              <p style={{ fontSize: '14px' }}>
                Control your browser using natural language.
                <br />
                Try: "Open Gmail and check my latest email"
              </p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`chat-message ${message.role}`}
                data-testid={`chat-message-${message.role}`}
              >
                {message.content}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a command..."
            disabled={!activeTabId || isSending}
            className="chat-input"
            data-testid="chat-input"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || !activeTabId || isSending}
            className="send-button"
            data-testid="send-button"
          >
            <FiSend size={18} />
          </Button>
        </div>
      </div>
    </>
  );
};

export default ChatPanel;