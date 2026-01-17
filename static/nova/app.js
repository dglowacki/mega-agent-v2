/**
 * Nova Sonic Voice Agent - Browser Client
 *
 * Handles:
 * - Microphone capture (16kHz PCM)
 * - WebSocket communication
 * - Audio playback (24kHz PCM)
 * - UI updates
 */

class NovaVoiceAgent {
    constructor() {
        // DOM elements
        this.micButton = document.getElementById('mic-button');
        this.micText = document.getElementById('mic-text');
        this.status = document.getElementById('status');
        this.waveform = document.getElementById('waveform');
        this.transcript = document.getElementById('transcript');
        this.transcriptContainer = document.getElementById('transcript-container');

        // State
        this.state = 'idle'; // idle, connecting, listening, processing, speaking
        this.ws = null;
        this.mediaStream = null;
        this.audioContext = null;
        this.processor = null;
        this.playbackQueue = [];
        this.isPlaying = false;

        // Audio settings
        this.inputSampleRate = 16000;
        this.outputSampleRate = 24000;

        // Bind event handlers
        this.micButton.addEventListener('click', () => this.handleMicClick());

        // Keep screen awake
        this.wakeLock = null;
        this.requestWakeLock();

        console.log('Nova Voice Agent initialized');
    }

    async requestWakeLock() {
        try {
            if ('wakeLock' in navigator) {
                this.wakeLock = await navigator.wakeLock.request('screen');
                console.log('Wake lock acquired');
            }
        } catch (err) {
            console.log('Wake lock not available:', err);
        }
    }

    async handleMicClick() {
        if (this.state === 'idle') {
            await this.startSession();
        } else if (this.state === 'listening') {
            this.stopListening();
        }
    }

    async startSession() {
        this.setState('connecting');

        try {
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: this.inputSampleRate,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            // Set up audio context for recording
            this.audioContext = new AudioContext({ sampleRate: this.inputSampleRate });
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // Create script processor for audio capture
            this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
            this.processor.onaudioprocess = (e) => this.handleAudioProcess(e);
            source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);

            // Connect WebSocket
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/nova/stream`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                // Send audio start signal
                this.ws.send(JSON.stringify({ type: 'audio_start' }));
                this.setState('listening');
            };

            this.ws.onmessage = (event) => this.handleMessage(event);

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.addMessage('system', 'Connection error. Please try again.');
                this.cleanup();
            };

            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this.cleanup();
            };

        } catch (err) {
            console.error('Failed to start session:', err);
            this.addMessage('system', 'Failed to access microphone. Please allow microphone access.');
            this.setState('idle');
        }
    }

    handleAudioProcess(event) {
        if (this.state !== 'listening' || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        const inputData = event.inputBuffer.getChannelData(0);

        // Convert float32 to int16
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Convert to base64
        const base64 = this.arrayBufferToBase64(int16Data.buffer);

        // Send to server
        this.ws.send(JSON.stringify({
            type: 'audio',
            data: base64
        }));
    }

    handleMessage(event) {
        const data = JSON.parse(event.data);

        switch (data.type) {
            case 'ready':
                console.log('Nova ready');
                break;

            case 'audio':
                this.queueAudio(data.data);
                break;

            case 'transcript':
                this.addMessage(data.role, data.content);
                break;

            case 'tool_use':
                this.addToolBadge(data.tool);
                break;

            case 'tool_result':
                if (!data.success) {
                    this.addMessage('system', `Tool error: ${data.error}`);
                }
                break;

            case 'turn_detected':
                this.setState('processing');
                break;

            case 'error':
                this.addMessage('system', `Error: ${data.message}`);
                break;

            case 'reset_confirmed':
                this.clearTranscript();
                this.addMessage('system', 'Conversation reset.');
                break;
        }
    }

    queueAudio(base64Data) {
        // Decode base64 to ArrayBuffer
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        // Convert to Int16Array
        const int16Data = new Int16Array(bytes.buffer);

        // Add to playback queue
        this.playbackQueue.push(int16Data);

        // Start playback if not already playing
        if (!this.isPlaying) {
            this.playNextAudio();
        }
    }

    async playNextAudio() {
        if (this.playbackQueue.length === 0) {
            this.isPlaying = false;
            if (this.state === 'speaking') {
                this.setState('listening');
            }
            return;
        }

        this.isPlaying = true;
        this.setState('speaking');

        const int16Data = this.playbackQueue.shift();

        // Create audio context for playback (24kHz)
        const playbackContext = new AudioContext({ sampleRate: this.outputSampleRate });

        // Convert Int16 to Float32
        const float32Data = new Float32Array(int16Data.length);
        for (let i = 0; i < int16Data.length; i++) {
            float32Data[i] = int16Data[i] / 32768.0;
        }

        // Create audio buffer
        const audioBuffer = playbackContext.createBuffer(1, float32Data.length, this.outputSampleRate);
        audioBuffer.getChannelData(0).set(float32Data);

        // Play audio
        const source = playbackContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(playbackContext.destination);

        source.onended = () => {
            playbackContext.close();
            this.playNextAudio();
        };

        source.start();
    }

    stopListening() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'audio_end' }));
        }
        this.cleanup();
    }

    cleanup() {
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.playbackQueue = [];
        this.isPlaying = false;
        this.setState('idle');
    }

    setState(state) {
        this.state = state;

        // Update status badge
        this.status.className = 'status';
        switch (state) {
            case 'idle':
                this.status.textContent = 'READY';
                this.micText.textContent = 'TAP TO SPEAK';
                this.micButton.className = 'mic-button';
                this.waveform.className = 'waveform';
                break;
            case 'connecting':
                this.status.textContent = 'CONNECTING';
                this.status.classList.add('processing');
                this.micText.textContent = 'CONNECTING...';
                this.micButton.className = 'mic-button disabled';
                break;
            case 'listening':
                this.status.textContent = 'LISTENING';
                this.status.classList.add('listening');
                this.micText.textContent = 'LISTENING...';
                this.micButton.className = 'mic-button listening';
                this.waveform.className = 'waveform active';
                break;
            case 'processing':
                this.status.textContent = 'THINKING';
                this.status.classList.add('processing');
                this.micText.textContent = 'THINKING...';
                this.waveform.className = 'waveform';
                break;
            case 'speaking':
                this.status.textContent = 'SPEAKING';
                this.status.classList.add('speaking');
                this.micText.textContent = 'SPEAKING...';
                this.micButton.className = 'mic-button speaking';
                this.waveform.className = 'waveform speaking';
                break;
        }
    }

    addMessage(role, content) {
        const div = document.createElement('div');
        div.className = `message ${role}`;

        if (role !== 'system') {
            const roleLabel = document.createElement('div');
            roleLabel.className = 'role';
            roleLabel.textContent = role === 'user' ? 'You' : 'Agent';
            div.appendChild(roleLabel);
        }

        const text = document.createElement('div');
        text.textContent = content;
        div.appendChild(text);

        this.transcript.appendChild(div);
        this.scrollToBottom();
    }

    addToolBadge(toolName) {
        const lastMessage = this.transcript.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('assistant')) {
            const badge = document.createElement('div');
            badge.className = 'tool-badge';
            badge.textContent = `🔧 ${toolName}`;
            lastMessage.appendChild(badge);
        }
    }

    clearTranscript() {
        this.transcript.innerHTML = '';
    }

    scrollToBottom() {
        this.transcriptContainer.scrollTop = this.transcriptContainer.scrollHeight;
    }

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.novaAgent = new NovaVoiceAgent();
});
