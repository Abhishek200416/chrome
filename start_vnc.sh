#!/bin/bash
# Start Virtual Display and VNC Server

export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
sleep 2
x11vnc -display :99 -forever -nopw -listen 127.0.0.1 -xkb -rfbport 5900 &
websockify --web=/usr/share/novnc 6080 127.0.0.1:5900 &

echo "✅ VNC Server started on :99"
echo "✅ noVNC web interface on http://localhost:6080"
echo "✅ DISPLAY=:99 for Playwright"
