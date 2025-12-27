import React, { useEffect, useRef, useState } from 'react';

const VNCViewer = ({ backendUrl }) => {
  const iframeRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);

  useEffect(() => {
    // VNC is accessed via noVNC web interface running on port 6080
    // The websockify proxy forwards to VNC server on port 5900
    setConnected(true);
    
    // Monitor iframe load status
    const iframe = iframeRef.current;
    if (iframe) {
      iframe.onload = () => {
        console.log('✅ VNC iframe loaded successfully');
        setConnected(true);
        setConnectionError(null);
      };
      iframe.onerror = (e) => {
        console.error('❌ VNC iframe load error:', e);
        setConnectionError('Failed to load VNC viewer');
      };
    }
  }, []);

  // Construct the noVNC URL - it runs on port 6080 with websockify
  const vncUrl = `http://localhost:6080/vnc.html?autoconnect=true&resize=scale`;

  return (
    <div className="relative w-full h-full bg-gray-900">
      {/* VNC iframe - shows real browser via noVNC web interface */}
      <iframe
        ref={iframeRef}
        src={vncUrl}
        title="Real Browser Display (VNC)"
        className="w-full h-full border-0"
        style={{
          display: 'block',
          backgroundColor: '#1a1a1a'
        }}
        allow="fullscreen"
      />
      
      {/* Connection Error Overlay */}
      {connectionError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-90">
          <div className="text-center">
            <div className="text-red-400">
              <div className="text-xl mb-2">❌ Connection Error</div>
              <div className="text-sm">{connectionError}</div>
              <div className="text-xs mt-2">VNC URL: {vncUrl}</div>
            </div>
          </div>
        </div>
      )}
      
      {/* Connected Indicator */}
      {connected && !connectionError && (
        <div className="absolute top-4 right-4 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-medium flex items-center gap-2 shadow-lg z-50">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          LIVE BROWSER
        </div>
      )}
    </div>
  );
};

export default VNCViewer;
