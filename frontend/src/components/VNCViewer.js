import React, { useEffect, useRef, useState } from 'react';
import RFB from '@novnc/novnc/lib/rfb';

const VNCViewer = ({ backendUrl }) => {
  const vncRef = useRef(null);
  const rfbRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);

  useEffect(() => {
    if (!vncRef.current) return;

    try {
      // Clear any existing connection
      if (rfbRef.current) {
        rfbRef.current.disconnect();
        rfbRef.current = null;
      }

      // Create WebSocket URL for VNC connection
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = backendUrl 
        ? `${wsProtocol}//${backendUrl.replace(/^https?:\/\//, '')}/vnc`
        : `${wsProtocol}//${window.location.host}/vnc`;

      console.log('🔗 Connecting to VNC:', wsUrl);

      // Create RFB connection
      const rfb = new RFB(vncRef.current, wsUrl, {
        credentials: { password: '' }
      });

      // Event handlers
      rfb.addEventListener('connect', () => {
        console.log('✅ VNC Connected');
        setConnected(true);
        setConnectionError(null);
        
        // Set quality and compression
        rfb.qualityLevel = 6;
        rfb.compressionLevel = 2;
        
        // Scale to fit
        rfb.scaleViewport = true;
        rfb.resizeSession = false;
      });

      rfb.addEventListener('disconnect', (e) => {
        console.log('❌ VNC Disconnected:', e.detail);
        setConnected(false);
        if (e.detail.clean === false) {
          setConnectionError('Connection lost. Retrying...');
          // Retry after 2 seconds
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        }
      });

      rfb.addEventListener('credentialsrequired', () => {
        console.log('🔑 VNC Credentials Required');
        setConnectionError('Authentication required');
      });

      rfb.addEventListener('securityfailure', (e) => {
        console.error('🔒 VNC Security Failure:', e.detail);
        setConnectionError(`Security error: ${e.detail.reason}`);
      });

      rfbRef.current = rfb;

    } catch (error) {
      console.error('❌ VNC Connection Error:', error);
      setConnectionError(`Connection error: ${error.message}`);
    }

    // Cleanup on unmount
    return () => {
      if (rfbRef.current) {
        rfbRef.current.disconnect();
        rfbRef.current = null;
      }
    };
  }, [backendUrl]);

  return (
    <div className="relative w-full h-full bg-gray-900">
      {/* VNC Canvas Container */}
      <div 
        ref={vncRef} 
        className="w-full h-full"
        style={{ 
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}
      />
      
      {/* Connection Status Overlay */}
      {!connected && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-90">
          <div className="text-center">
            {connectionError ? (
              <div className="text-red-400">
                <div className="text-xl mb-2">❌ Connection Error</div>
                <div className="text-sm">{connectionError}</div>
              </div>
            ) : (
              <div className="text-blue-400">
                <div className="text-xl mb-2">🔄 Connecting to Browser...</div>
                <div className="animate-pulse text-sm">Establishing VNC connection</div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Connected Indicator */}
      {connected && (
        <div className="absolute top-4 right-4 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-medium flex items-center gap-2 shadow-lg">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          LIVE
        </div>
      )}
    </div>
  );
};

export default VNCViewer;
