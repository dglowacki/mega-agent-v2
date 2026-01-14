#!/usr/bin/env python3.11
"""
Voice Service - Flask app for the /av voice assistant endpoint.

Provides:
- Password-protected login with long-lasting cookie
- Neo-brutal mobile-friendly interface
- WebSocket proxy to voice gateway
- Start/stop controls for voice agent

Run:
    python voice_service.py [--port PORT] [--voice-port VOICE_PORT]
"""

import argparse
import asyncio
import base64
import hashlib
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, redirect, url_for, make_response, render_template_string

# Configuration
PASSWORD = "TheVoiceYouWantToHearToday"
PASSWORD_HASH = hashlib.sha256(PASSWORD.encode()).hexdigest()
COOKIE_NAME = "av_session"
COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # 1 year in seconds
SECRET_KEY = os.getenv("AV_SECRET_KEY", secrets.token_hex(32))

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Store valid session tokens
valid_sessions = set()


def generate_session_token():
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)


def verify_session(token):
    """Verify if a session token is valid."""
    if not token:
        return False
    return token in valid_sessions


def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get(COOKIE_NAME)
        if not verify_session(token):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# LOGIN PAGE - Neo-Brutal Mobile-Friendly Design
# =============================================================================

LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Voice Assistant</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f5f5;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            width: 100%;
            max-width: 400px;
            background-color: white;
            border: 4px solid black;
        }

        .header {
            background-color: black;
            color: white;
            padding: 30px 20px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .header .subtitle {
            font-size: 14px;
            font-weight: 400;
            margin-top: 8px;
            opacity: 0.8;
        }

        .form-section {
            padding: 30px 20px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            font-size: 14px;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .form-group input {
            width: 100%;
            padding: 15px;
            font-size: 18px;
            border: 3px solid black;
            background-color: #f5f5f5;
            outline: none;
            transition: background-color 0.2s;
        }

        .form-group input:focus {
            background-color: #FFEB3B;
        }

        .form-group input::placeholder {
            color: #888;
        }

        .submit-btn {
            width: 100%;
            padding: 18px;
            font-size: 18px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            background-color: black;
            color: white;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
        }

        .submit-btn:hover {
            background-color: #333;
        }

        .submit-btn:active {
            transform: translateY(2px);
        }

        .error-message {
            background-color: #F44336;
            color: white;
            padding: 15px 20px;
            font-weight: 700;
            text-align: center;
            border-bottom: 3px solid black;
        }

        .footer {
            padding: 15px 20px;
            background-color: #f5f5f5;
            border-top: 3px solid black;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Voice Assistant</h1>
            <div class="subtitle">Powered by Claude + Grok</div>
        </div>

        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}

        <div class="form-section">
            <form method="POST" action="/av/login">
                <div class="form-group">
                    <label for="password">Enter Password</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        placeholder="&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;"
                        autocomplete="current-password"
                        autofocus
                        required
                    >
                </div>
                <button type="submit" class="submit-btn">Enter</button>
            </form>
        </div>

        <div class="footer">
            Secure voice-controlled assistant
        </div>
    </div>
</body>
</html>
'''


# =============================================================================
# VOICE PAGE - Neo-Brutal Mobile-Friendly with Start/Stop
# =============================================================================

VOICE_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Voice Assistant</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f5f5;
            min-height: 100vh;
            min-height: -webkit-fill-available;
            display: flex;
            flex-direction: column;
        }

        html {
            height: -webkit-fill-available;
        }

        .header {
            background-color: black;
            color: white;
            padding: 20px;
            text-align: center;
            border-bottom: 4px solid black;
        }

        .header h1 {
            font-size: 24px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
            background-color: white;
            border-left: 4px solid black;
            border-right: 4px solid black;
        }

        .status-bar {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 15px;
            background-color: #f5f5f5;
            border: 3px solid black;
            margin-bottom: 20px;
        }

        .status-dot {
            width: 16px;
            height: 16px;
            background-color: #888;
        }

        .status-dot.ready {
            background-color: #4CAF50;
        }

        .status-dot.listening {
            background-color: #2196F3;
            animation: pulse 1s infinite;
        }

        .status-dot.thinking {
            background-color: #FFEB3B;
            animation: pulse 0.5s infinite;
        }

        .status-dot.speaking {
            background-color: #9C27B0;
            animation: pulse 0.3s infinite;
        }

        .status-dot.error {
            background-color: #F44336;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .status-text {
            font-size: 16px;
            font-weight: 800;
            text-transform: uppercase;
        }

        .transcript-area {
            background-color: #f5f5f5;
            border: 3px solid black;
            padding: 15px;
            overflow-y: auto;
            margin-bottom: 20px;
            height: 300px;
            max-height: 300px;
        }

        .message {
            padding: 12px 15px;
            margin-bottom: 12px;
            border-left: 4px solid black;
            background-color: white;
        }

        .message.user {
            border-left-color: #2196F3;
        }

        .message.assistant {
            border-left-color: #4CAF50;
        }

        .message-label {
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 5px;
        }

        .message-text {
            font-size: 16px;
            line-height: 1.5;
        }

        .visualizer {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            height: 50px;
            margin-bottom: 20px;
        }

        .bar {
            width: 6px;
            height: 8px;
            background-color: black;
            transition: height 0.1s ease-out;
        }

        .bar.active {
            background-color: #2196F3;
        }

        .control-area {
            display: flex;
            gap: 15px;
        }

        .control-btn {
            flex: 1;
            padding: 20px;
            font-size: 18px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            border: 4px solid black;
            cursor: pointer;
            transition: all 0.2s;
        }

        .control-btn:active {
            transform: translateY(3px);
        }

        .start-btn {
            background-color: #4CAF50;
            color: white;
        }

        .start-btn:hover {
            background-color: #45a049;
        }

        .start-btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }

        .stop-btn {
            background-color: #F44336;
            color: white;
        }

        .stop-btn:hover {
            background-color: #da190b;
        }

        .stop-btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }

        .footer {
            padding: 15px 20px;
            background-color: black;
            color: white;
            text-align: center;
            font-size: 12px;
            border-top: 4px solid black;
        }

        .error-banner {
            background-color: #F44336;
            color: white;
            padding: 15px;
            text-align: center;
            font-weight: 700;
            display: none;
        }

        .error-banner.show {
            display: block;
        }

        /* Mobile optimizations */
        @media (max-width: 480px) {
            .header h1 {
                font-size: 20px;
            }

            .control-btn {
                padding: 18px 15px;
                font-size: 16px;
            }

            .message-text {
                font-size: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>VOICE ASSISTANT</h1>
    </div>

    <div id="errorBanner" class="error-banner"></div>

    <div class="main">
        <div class="status-bar">
            <div id="statusDot" class="status-dot"></div>
            <span id="statusText" class="status-text">Disconnected</span>
        </div>

        <div class="visualizer" id="visualizer"></div>

        <div class="transcript-area" id="transcript">
            <div class="message assistant">
                <div class="message-label">Assistant</div>
                <div class="message-text">Tap START to begin speaking with me.</div>
            </div>
        </div>

        <div class="control-area">
            <button id="startBtn" class="control-btn start-btn" disabled>Start</button>
            <button id="stopBtn" class="control-btn stop-btn" disabled>Stop</button>
        </div>
    </div>

    <div class="footer">
        Claude + Grok Voice &bull; Tap START to begin
    </div>

    <script>
        // Configuration - Version 2
        const WS_URL = '{{ ws_url }}';
        const VERSION = 'v2.1';

        // State
        let ws = null;
        let audioContext = null;
        let mediaStream = null;
        let processor = null;
        let isReady = false;
        let isListening = false;
        let isProcessing = false;
        let connectAttempts = 0;

        // DOM elements
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const transcript = document.getElementById('transcript');
        const errorBanner = document.getElementById('errorBanner');
        const visualizer = document.getElementById('visualizer');

        // Create visualizer bars
        for (let i = 0; i < 24; i++) {
            const bar = document.createElement('div');
            bar.className = 'bar';
            visualizer.appendChild(bar);
        }
        const bars = visualizer.querySelectorAll('.bar');

        // Debug logging - shows in transcript
        function log(msg) {
            console.log('[Voice ' + VERSION + '] ' + msg);
        }

        function updateStatus(dotClass, text) {
            statusDot.className = 'status-dot ' + dotClass;
            statusText.textContent = text;
        }

        function updateButtons() {
            startBtn.disabled = !isReady || isListening;
            stopBtn.disabled = !isListening;
        }

        function showError(message) {
            errorBanner.textContent = message;
            errorBanner.classList.add('show');
            setTimeout(function() { errorBanner.classList.remove('show'); }, 5000);
        }

        function addMessage(role, text) {
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.innerHTML = '<div class="message-label">' + (role === 'user' ? 'You' : 'Assistant') + '</div>' +
                           '<div class="message-text">' + text.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>';
            transcript.appendChild(div);
            transcript.scrollTop = transcript.scrollHeight;
        }

        // Simple WebSocket connection
        function connect() {
            connectAttempts++;
            log('Connect attempt ' + connectAttempts + ' to ' + WS_URL);

            if (ws) {
                try { ws.close(); } catch(e) {}
                ws = null;
            }

            updateStatus('', 'Connecting... (' + connectAttempts + ')');

            try {
                ws = new WebSocket(WS_URL);
                log('WebSocket created');
            } catch(e) {
                log('WebSocket creation failed: ' + e.message);
                showError('Connection failed: ' + e.message);
                setTimeout(connect, 3000);
                return;
            }

            ws.onopen = function() {
                log('WebSocket opened');
                updateStatus('', 'Connected, waiting for voice...');
            };

            ws.onclose = function(e) {
                log('WebSocket closed: code=' + e.code + ' reason=' + e.reason);
                isReady = false;
                updateStatus('', 'Disconnected (code: ' + e.code + ')');
                updateButtons();
                // Reconnect after 3 seconds
                setTimeout(connect, 3000);
            };

            ws.onerror = function(e) {
                log('WebSocket error event');
            };

            ws.onmessage = function(e) {
                try {
                    var msg = JSON.parse(e.data);
                    handleMessage(msg);
                } catch(err) {
                    log('Parse error: ' + err);
                }
            };
        }

        function handleMessage(msg) {
            log('Received: ' + msg.type);
            if (msg.type === 'grok_ready') {
                log('Voice API ready!');
                connectAttempts = 0;
                isReady = true;
                updateStatus('ready', 'Ready');
                updateButtons();
            }
            else if (msg.type === 'transcription') {
                addMessage('user', msg.text);
                isProcessing = true;
                updateStatus('thinking', 'Processing...');
            }
            else if (msg.type === 'response') {
                addMessage('assistant', msg.text);
                isProcessing = false;
                updateStatus(isListening ? 'listening' : 'ready', isListening ? 'Listening' : 'Ready');
            }
            else if (msg.type === 'thinking') {
                if (msg.active) {
                    isProcessing = true;
                    updateStatus('thinking', 'Processing...');
                } else {
                    isProcessing = false;
                    updateStatus(isListening ? 'listening' : 'ready', isListening ? 'Listening' : 'Ready');
                }
            }
            else if (msg.type === 'audio') {
                playAudio(msg.data);
            }
            else if (msg.type === 'pong') {
                // Keepalive response
            }
            else if (msg.type === 'error') {
                showError(msg.message || 'Server error');
            }
        }

        // Audio playback
        function playAudio(base64Data) {
            try {
                var binaryString = atob(base64Data);
                var bytes = new Uint8Array(binaryString.length);
                for (var i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }

                var int16 = new Int16Array(bytes.buffer);
                var float32 = new Float32Array(int16.length);
                for (var i = 0; i < int16.length; i++) {
                    float32[i] = int16[i] / 32768;
                }

                if (!audioContext) {
                    audioContext = new AudioContext({ sampleRate: 24000 });
                }

                var audioBuffer = audioContext.createBuffer(1, float32.length, 24000);
                audioBuffer.copyToChannel(float32, 0);

                var source = audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(audioContext.destination);
                source.start();
            } catch (err) {
                console.log('Audio error:', err);
            }
        }

        // Start listening
        function startListening() {
            if (!isReady || isListening) return;

            navigator.mediaDevices.getUserMedia({
                audio: { channelCount: 1, sampleRate: 24000, echoCancellation: true, noiseSuppression: true }
            }).then(function(stream) {
                mediaStream = stream;

                if (!audioContext) {
                    audioContext = new AudioContext({ sampleRate: 24000 });
                }

                if (audioContext.state === 'suspended') {
                    audioContext.resume();
                }

                var source = audioContext.createMediaStreamSource(stream);
                processor = audioContext.createScriptProcessor(4096, 1, 1);

                processor.onaudioprocess = function(e) {
                    if (!ws || ws.readyState !== WebSocket.OPEN) return;
                    if (!isListening) return;

                    var pcmFloat = e.inputBuffer.getChannelData(0);
                    var int16 = new Int16Array(pcmFloat.length);

                    for (var i = 0; i < pcmFloat.length; i++) {
                        var s = Math.max(-1, Math.min(1, pcmFloat[i]));
                        int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                    }

                    // Update visualizer
                    var step = Math.floor(pcmFloat.length / bars.length);
                    for (var i = 0; i < bars.length; i++) {
                        var value = Math.abs(pcmFloat[i * step]) * 150;
                        bars[i].style.height = Math.max(8, Math.min(50, value)) + 'px';
                    }

                    // Send audio
                    try {
                        var base64 = btoa(String.fromCharCode.apply(null, new Uint8Array(int16.buffer)));
                        ws.send(JSON.stringify({ type: 'audio', data: base64 }));
                    } catch(err) {
                        console.log('Send error:', err);
                    }
                };

                source.connect(processor);
                processor.connect(audioContext.destination);

                isListening = true;
                updateStatus('listening', 'Listening');
                updateButtons();
                bars.forEach(function(bar) { bar.classList.add('active'); });

            }).catch(function(err) {
                console.log('Mic error:', err);
                showError('Microphone access denied');
            });
        }

        // Stop listening
        function stopListening() {
            if (processor) {
                try { processor.disconnect(); } catch(e) {}
                processor = null;
            }
            if (mediaStream) {
                mediaStream.getTracks().forEach(function(track) { track.stop(); });
                mediaStream = null;
            }

            isListening = false;
            bars.forEach(function(bar) {
                bar.style.height = '8px';
                bar.classList.remove('active');
            });

            if (isReady) {
                updateStatus('ready', 'Ready');
            }
            updateButtons();
        }

        // Event listeners
        startBtn.addEventListener('click', startListening);
        stopBtn.addEventListener('click', stopListening);

        // Send periodic ping to keep connection alive
        setInterval(function() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);

        // Start
        console.log('Voice Agent starting, WS_URL:', WS_URL);
        connect();
    </script>
</body>
</html>
'''


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/av')
@app.route('/av/')
def index():
    """Main entry - redirect to voice page if authenticated, else login."""
    token = request.cookies.get(COOKIE_NAME)
    if verify_session(token):
        return redirect(url_for('voice'))
    return redirect(url_for('login'))


@app.route('/av/login', methods=['GET', 'POST'])
def login():
    """Login page with password authentication."""
    error = None

    if request.method == 'POST':
        password = request.form.get('password', '')
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if password_hash == PASSWORD_HASH:
            # Generate session token
            token = generate_session_token()
            valid_sessions.add(token)

            # Create response with cookie
            response = make_response(redirect(url_for('voice')))
            response.set_cookie(
                COOKIE_NAME,
                token,
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                samesite='Lax',
                secure=request.is_secure
            )
            return response
        else:
            error = "Invalid password"

    return render_template_string(LOGIN_PAGE, error=error)


@app.route('/av/voice')
@require_auth
def voice():
    """Voice assistant page."""
    # Check if behind proxy (nginx)
    forwarded_host = request.headers.get('X-Forwarded-Host') or request.headers.get('Host')
    forwarded_proto = request.headers.get('X-Forwarded-Proto', 'http')

    # Determine the actual host (prefer forwarded headers from nginx)
    if forwarded_host and '127.0.0.1' not in forwarded_host and 'localhost' not in forwarded_host:
        # Behind nginx proxy - use the forwarded host
        ws_protocol = 'wss' if forwarded_proto == 'https' else 'ws'
        ws_url = f'{ws_protocol}://{forwarded_host}/av/ws'
    else:
        # Direct access (local development)
        host = request.host.split(':')[0]
        ws_url = f'ws://{host}:8765'

    response = make_response(render_template_string(VOICE_PAGE, ws_url=ws_url))
    # Prevent caching to ensure latest JavaScript is loaded
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/av/logout')
def logout():
    """Logout and clear session."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        valid_sessions.discard(token)

    response = make_response(redirect(url_for('login')))
    response.delete_cookie(COOKIE_NAME)
    return response


@app.route('/av/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}


@app.route('/av/status')
def status():
    """Detailed status endpoint for debugging."""
    import socket

    # Check if gateway is reachable
    gateway_status = 'unknown'
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 8765))
        gateway_status = 'up' if result == 0 else 'down'
        sock.close()
    except:
        gateway_status = 'error'

    return {
        'version': 'v2.1',
        'status': 'ok',
        'gateway': gateway_status,
        'sessions': len(valid_sessions),
        'timestamp': datetime.utcnow().isoformat()
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Voice Service")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5050, help="Port for Flask app")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print(f"Voice Service starting on http://{args.host}:{args.port}/av")
    print(f"Password: {PASSWORD}")
    print()

    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()
