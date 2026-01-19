#!/usr/bin/env python3.11
"""
Voice Service - Flask app for the /av voice assistant endpoint.

Provides:
- Password-protected login with long-lasting cookie
- Neo-brutal mobile-friendly interface
- ElevenLabs widget integration with signed URLs
- WebSocket proxy to voice gateway (legacy Grok support)

Run:
    python voice_service.py [--port PORT] [--voice-port VOICE_PORT]

Environment Variables:
    ELEVENLABS_API_KEY - Required for signed URL generation
    ELEVENLABS_AGENT_ID - Your ElevenLabs agent ID
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
import requests
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, redirect, url_for, make_response, render_template_string, jsonify

# Configuration
PASSWORD = "TheVoiceYouWantToHearToday"
PASSWORD_HASH = hashlib.sha256(PASSWORD.encode()).hexdigest()
COOKIE_NAME = "av_session"
COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # 1 year in seconds
SECRET_KEY = os.getenv("AV_SECRET_KEY", secrets.token_hex(32))

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "agent_2601kf1fmbnseaxvp5kvc4zc21bz")

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
            font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
            background-color: #0a0a0a;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            width: 100%;
            max-width: 420px;
            background-color: #141414;
            border-radius: 16px;
            border: 1px solid #2a2a2a;
            overflow: hidden;
        }

        .header {
            padding: 40px 30px 30px;
            text-align: center;
        }

        .logo {
            width: 64px;
            height: 64px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .logo svg {
            width: 32px;
            height: 32px;
            fill: white;
        }

        .header h1 {
            font-size: 24px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 8px;
        }

        .header .subtitle {
            font-size: 14px;
            font-weight: 400;
            color: #888;
        }

        .form-section {
            padding: 0 30px 30px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            color: #888;
            margin-bottom: 8px;
        }

        .form-group input {
            width: 100%;
            padding: 14px 16px;
            font-size: 16px;
            border: 1px solid #2a2a2a;
            border-radius: 10px;
            background-color: #1a1a1a;
            color: #fff;
            outline: none;
            transition: all 0.2s;
        }

        .form-group input:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }

        .form-group input::placeholder {
            color: #555;
        }

        .submit-btn {
            width: 100%;
            padding: 14px;
            font-size: 16px;
            font-weight: 600;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .submit-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }

        .submit-btn:active {
            transform: translateY(0);
        }

        .error-message {
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #ef4444;
            padding: 12px 16px;
            margin: 0 30px 20px;
            border-radius: 10px;
            font-size: 14px;
            text-align: center;
        }

        .footer {
            padding: 20px 30px;
            border-top: 1px solid #2a2a2a;
            text-align: center;
            font-size: 12px;
            color: #555;
        }

        .footer a {
            color: #6366f1;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2a1 1 0 0 0-2 0v2a9 9 0 0 0 8 8.94V22H8a1 1 0 0 0 0 2h8a1 1 0 0 0 0-2h-3v-1.06A9 9 0 0 0 21 12v-2a1 1 0 0 0-2 0z"/>
                </svg>
            </div>
            <h1>Voice Assistant</h1>
            <div class="subtitle">Powered by Claude + ElevenLabs</div>
        </div>

        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}

        <div class="form-section">
            <form method="POST" action="/av/login">
                <div class="form-group">
                    <label for="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        placeholder="Enter your password"
                        autocomplete="current-password"
                        autofocus
                        required
                    >
                </div>
                <button type="submit" class="submit-btn">Sign In</button>
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
# ELEVENLABS VOICE PAGE - Secure Widget Integration
# =============================================================================

ELEVENLABS_PAGE = '''
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

        html, body {
            height: 100%;
            width: 100%;
            overflow: hidden;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
            background-color: #0a0a0a;
            display: flex;
            flex-direction: column;
        }

        #loading-screen {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #0a0a0a;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            transition: opacity 0.3s ease;
        }

        #loading-screen.hidden {
            opacity: 0;
            pointer-events: none;
        }

        .loading-logo {
            width: 80px;
            height: 80px;
            margin-bottom: 24px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pulse-glow 2s ease-in-out infinite;
        }

        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.3); }
            50% { box-shadow: 0 0 40px rgba(139, 92, 246, 0.5); }
        }

        .loading-logo svg {
            width: 40px;
            height: 40px;
            fill: white;
        }

        .loading-text {
            color: #888;
            font-size: 14px;
            font-weight: 500;
        }

        .loading-spinner {
            width: 24px;
            height: 24px;
            border: 2px solid #333;
            border-top: 2px solid #6366f1;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-top: 16px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error-screen {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #0a0a0a;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1001;
        }

        .error-screen.show {
            display: flex;
        }

        .error-icon {
            width: 64px;
            height: 64px;
            background-color: rgba(239, 68, 68, 0.1);
            border: 2px solid rgba(239, 68, 68, 0.3);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }

        .error-icon svg {
            width: 32px;
            height: 32px;
            fill: #ef4444;
        }

        .error-title {
            color: #fff;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .error-message {
            color: #888;
            font-size: 14px;
            text-align: center;
            max-width: 300px;
        }

        .retry-btn {
            margin-top: 24px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .retry-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }

        #voice-container {
            flex: 1;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        elevenlabs-convai {
            width: 100% !important;
            height: 100% !important;
            max-width: none !important;
            max-height: none !important;
        }
    </style>
</head>
<body>
    <div id="loading-screen">
        <div class="loading-logo">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2a1 1 0 0 0-2 0v2a9 9 0 0 0 8 8.94V22H8a1 1 0 0 0 0 2h8a1 1 0 0 0 0-2h-3v-1.06A9 9 0 0 0 21 12v-2a1 1 0 0 0-2 0z"/>
            </svg>
        </div>
        <div class="loading-text" id="loadingText">Connecting...</div>
        <div class="loading-spinner"></div>
    </div>

    <div id="error-screen" class="error-screen">
        <div class="error-icon">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
        </div>
        <div class="error-title">Connection Error</div>
        <div class="error-message" id="errorMessage">Unable to connect to voice service.</div>
        <button class="retry-btn" onclick="location.reload()">Try Again</button>
    </div>

    <div id="voice-container"></div>

    <script src="https://unpkg.com/@elevenlabs/convai-widget-embed@beta" async type="text/javascript"></script>

    <script>
        const loadingScreen = document.getElementById('loading-screen');
        const loadingText = document.getElementById('loadingText');
        const errorScreen = document.getElementById('error-screen');
        const errorMessage = document.getElementById('errorMessage');
        const voiceContainer = document.getElementById('voice-container');

        function showError(message) {
            loadingScreen.classList.add('hidden');
            errorMessage.textContent = message;
            errorScreen.classList.add('show');
        }

        function hideLoading() {
            loadingScreen.classList.add('hidden');
        }

        async function initVoice() {
            try {
                loadingText.textContent = 'Authenticating...';

                const response = await fetch('/av/signed-url', {
                    credentials: 'include'
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Authentication failed');
                }

                const data = await response.json();
                const signedUrl = data.signed_url;

                if (!signedUrl) {
                    throw new Error('No signed URL received');
                }

                loadingText.textContent = 'Starting voice assistant...';

                voiceContainer.innerHTML = '<elevenlabs-convai signed-url="' + signedUrl + '" variant="expanded"></elevenlabs-convai>';

                setTimeout(hideLoading, 1500);

            } catch (err) {
                console.error('Voice init error:', err);
                showError(err.message);
            }
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(initVoice, 300);
            });
        } else {
            setTimeout(initVoice, 300);
        }
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
        return redirect(url_for('voice_eleven'))
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
            response = make_response(redirect(url_for('voice_eleven')))
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


@app.route('/av/eleven')
@require_auth
def voice_eleven():
    """ElevenLabs voice assistant page with secure widget."""
    response = make_response(render_template_string(ELEVENLABS_PAGE))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/av/signed-url')
@require_auth
def get_signed_url():
    """
    Get a signed URL for ElevenLabs conversation.

    Requires authentication. Returns a 15-minute signed URL that the
    client uses to establish a secure connection to ElevenLabs.
    """
    if not ELEVENLABS_API_KEY:
        return jsonify({
            'error': 'ElevenLabs API key not configured. Set ELEVENLABS_API_KEY environment variable.'
        }), 500

    if not ELEVENLABS_AGENT_ID:
        return jsonify({
            'error': 'ElevenLabs Agent ID not configured. Set ELEVENLABS_AGENT_ID environment variable.'
        }), 500

    try:
        # Request signed URL from ElevenLabs API
        response = requests.get(
            f'https://api.elevenlabs.io/v1/convai/conversation/get-signed-url',
            params={'agent_id': ELEVENLABS_AGENT_ID},
            headers={'xi-api-key': ELEVENLABS_API_KEY},
            timeout=10
        )

        if response.status_code != 200:
            error_msg = response.json().get('detail', {}).get('message', 'Unknown error')
            return jsonify({'error': f'ElevenLabs API error: {error_msg}'}), response.status_code

        data = response.json()
        return jsonify({'signed_url': data.get('signed_url')})

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout connecting to ElevenLabs API'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to connect to ElevenLabs: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


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


@app.route('/av/test-ws')
def test_ws():
    """Test page for WebSocket connection debugging."""
    return '''<!DOCTYPE html>
<html>
<head><title>WS Test</title></head>
<body>
<h1>WebSocket Test</h1>
<pre id="log"></pre>
<script>
var log = document.getElementById('log');
function l(msg) { log.textContent += new Date().toISOString() + ': ' + msg + '\\n'; }

l('Starting test...');
l('Creating WebSocket to wss://' + location.host + '/av/ws');

var ws = new WebSocket('wss://' + location.host + '/av/ws');

ws.onopen = function() { l('CONNECTED!'); };
ws.onclose = function(e) { l('CLOSED: code=' + e.code + ' reason=' + e.reason); };
ws.onerror = function(e) { l('ERROR: ' + JSON.stringify(e)); };
ws.onmessage = function(e) {
    try {
        var data = JSON.parse(e.data);
        l('MESSAGE: ' + data.type);
        if (data.type === 'grok_ready') {
            l('SUCCESS! Voice API is ready.');
        }
    } catch(err) {
        l('PARSE ERROR: ' + err);
    }
};

setTimeout(function() {
    if (ws.readyState !== WebSocket.OPEN) {
        l('TIMEOUT - WebSocket did not connect in 10s');
        l('readyState=' + ws.readyState + ' (0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED)');
    }
}, 10000);
</script>
</body>
</html>'''


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
