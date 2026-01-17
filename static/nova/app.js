/**
 * Nova Sonic Voice Agent - Browser Client
 *
 * Optimized for low-latency bidirectional audio streaming.
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
        this.state = 'idle';
        this.ws = null;
        this.mediaStream = null;

        // Audio contexts - reuse for efficiency
        this.inputContext = null;
        this.outputContext = null;
        this.processor = null;

        // Audio playback - buffered for smooth playback
        this.audioQueue = [];
        this.isPlaying = false;
        this.nextPlayTime = 0;
        this.gainNode = null;

        // Audio settings
        this.inputSampleRate = 16000;
        this.outputSampleRate = 24000;

        // Message deduplication
        this.lastAssistantMessage = '';
        this.currentAssistantDiv = null;

        // Bind events
        this.micButton.addEventListener('click', () => this.handleMicClick());

        // Initialize output context early
        this.initOutputContext();

        console.log('Nova Voice Agent initialized');
    }

    initOutputContext() {
        // Pre-create output context for faster playback start
        this.outputContext = new AudioContext({ sampleRate: this.outputSampleRate });
        this.gainNode = this.outputContext.createGain();
        this.gainNode.connect(this.outputContext.destination);
    }

    async handleMicClick() {
        if (this.state === 'idle') {
            await this.startSession();
        } else {
            this.stopSession();
        }
    }

    async startSession() {
        this.setState('connecting');

        try {
            // Resume audio context if suspended (required by browsers)
            if (this.outputContext.state === 'suspended') {
                await this.outputContext.resume();
            }

            // Request microphone
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: this.inputSampleRate,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Set up input audio processing
            this.inputContext = new AudioContext({ sampleRate: this.inputSampleRate });
            const source = this.inputContext.createMediaStreamSource(this.mediaStream);

            // Use smaller buffer for lower latency (2048 instead of 4096)
            this.processor = this.inputContext.createScriptProcessor(2048, 1, 1);
            this.processor.onaudioprocess = (e) => this.processAudioInput(e);
            source.connect(this.processor);
            this.processor.connect(this.inputContext.destination);

            // Connect WebSocket
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.ws = new WebSocket(`${wsProtocol}//${window.location.host}/nova/stream`);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.ws.send(JSON.stringify({ type: 'audio_start' }));
                this.setState('listening');
            };

            this.ws.onmessage = (e) => this.handleMessage(e);
            this.ws.onerror = (e) => {
                console.error('WebSocket error:', e);
                this.addSystemMessage('Connection error');
                this.cleanup();
            };
            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this.cleanup();
            };

        } catch (err) {
            console.error('Session start failed:', err);
            this.addSystemMessage('Microphone access denied');
            this.setState('idle');
        }
    }

    processAudioInput(event) {
        if (this.state !== 'listening' || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        const input = event.inputBuffer.getChannelData(0);

        // Convert float32 to int16 PCM
        const pcm = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send as base64
        this.ws.send(JSON.stringify({
            type: 'audio',
            data: this.arrayBufferToBase64(pcm.buffer)
        }));
    }

    handleMessage(event) {
        const data = JSON.parse(event.data);

        switch (data.type) {
            case 'ready':
                console.log('Nova ready');
                break;

            case 'audio':
                this.queueAudioChunk(data.data);
                break;

            case 'transcript':
                this.handleTranscript(data.role, data.content);
                break;

            case 'tool_use':
                this.addToolBadge(data.tool);
                break;

            case 'tool_result':
                if (!data.success) {
                    this.addSystemMessage(`Tool error: ${data.error}`);
                }
                break;

            case 'turn_detected':
                if (data.interrupted) {
                    // Stop current playback on interruption
                    this.clearAudioQueue();
                }
                this.setState('processing');
                break;

            case 'error':
                this.addSystemMessage(`Error: ${data.message}`);
                break;
        }
    }

    handleTranscript(role, content) {
        // Skip JSON-like content (turn detection noise)
        if (content.trim().startsWith('{') && content.trim().endsWith('}')) {
            return;
        }

        if (role === 'user') {
            // User messages are always new
            this.currentAssistantDiv = null;
            this.lastAssistantMessage = '';
            this.addMessage('user', content);
        } else {
            // For assistant, append to existing message if it's a continuation
            const trimmedContent = content.trim();

            // Skip if this is a duplicate or substring of what we already have
            if (this.lastAssistantMessage.includes(trimmedContent)) {
                return;
            }

            // Check if this is a continuation (starts similarly to last)
            if (this.currentAssistantDiv && this.lastAssistantMessage.length > 0) {
                // Append new content
                const textDiv = this.currentAssistantDiv.querySelector('div:last-child');
                if (textDiv) {
                    textDiv.textContent = (textDiv.textContent + ' ' + trimmedContent).trim();
                    this.lastAssistantMessage = textDiv.textContent;
                }
            } else {
                // New assistant message
                this.addMessage('assistant', trimmedContent);
                this.lastAssistantMessage = trimmedContent;
            }

            this.scrollToBottom();
        }
    }

    queueAudioChunk(base64Data) {
        // Decode base64 to PCM
        const binary = atob(base64Data);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        const pcm = new Int16Array(bytes.buffer);

        // Convert to float32
        const float32 = new Float32Array(pcm.length);
        for (let i = 0; i < pcm.length; i++) {
            float32[i] = pcm[i] / 32768.0;
        }

        // Queue for playback
        this.audioQueue.push(float32);

        // Start playback if not already playing
        if (!this.isPlaying) {
            this.startPlayback();
        }
    }

    startPlayback() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            if (this.state === 'speaking') {
                this.setState('listening');
            }
            return;
        }

        this.isPlaying = true;
        this.setState('speaking');

        // Schedule all queued audio for gapless playback
        const now = this.outputContext.currentTime;
        if (this.nextPlayTime < now) {
            this.nextPlayTime = now;
        }

        while (this.audioQueue.length > 0) {
            const samples = this.audioQueue.shift();

            // Create buffer
            const buffer = this.outputContext.createBuffer(1, samples.length, this.outputSampleRate);
            buffer.getChannelData(0).set(samples);

            // Create source and schedule
            const source = this.outputContext.createBufferSource();
            source.buffer = buffer;
            source.connect(this.gainNode);
            source.start(this.nextPlayTime);

            // Track when this chunk ends
            this.nextPlayTime += buffer.duration;
        }

        // Check for more audio after current queue finishes
        const checkTime = (this.nextPlayTime - this.outputContext.currentTime) * 1000 + 50;
        setTimeout(() => this.startPlayback(), checkTime);
    }

    clearAudioQueue() {
        this.audioQueue = [];
        this.nextPlayTime = 0;
    }

    stopSession() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'audio_end' }));
            this.ws.send(JSON.stringify({ type: 'close' }));
        }
        this.cleanup();
    }

    cleanup() {
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        if (this.inputContext) {
            this.inputContext.close();
            this.inputContext = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(t => t.stop());
            this.mediaStream = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.audioQueue = [];
        this.isPlaying = false;
        this.nextPlayTime = 0;
        this.currentAssistantDiv = null;
        this.lastAssistantMessage = '';
        this.setState('idle');
    }

    setState(state) {
        this.state = state;
        this.status.className = 'status';

        const states = {
            idle: { text: 'READY', btn: 'TAP TO SPEAK', btnClass: '', waveClass: '' },
            connecting: { text: 'CONNECTING', btn: 'CONNECTING...', btnClass: 'disabled', waveClass: '', statusClass: 'processing' },
            listening: { text: 'LISTENING', btn: 'TAP TO STOP', btnClass: 'listening', waveClass: 'active', statusClass: 'listening' },
            processing: { text: 'THINKING', btn: 'THINKING...', btnClass: '', waveClass: '', statusClass: 'processing' },
            speaking: { text: 'SPEAKING', btn: 'SPEAKING...', btnClass: 'speaking', waveClass: 'speaking', statusClass: 'speaking' }
        };

        const s = states[state] || states.idle;
        this.status.textContent = s.text;
        if (s.statusClass) this.status.classList.add(s.statusClass);
        this.micText.textContent = s.btn;
        this.micButton.className = 'mic-button' + (s.btnClass ? ' ' + s.btnClass : '');
        this.waveform.className = 'waveform' + (s.waveClass ? ' ' + s.waveClass : '');
    }

    addMessage(role, content) {
        const div = document.createElement('div');
        div.className = `message ${role}`;

        if (role !== 'system') {
            const label = document.createElement('div');
            label.className = 'role';
            label.textContent = role === 'user' ? 'You' : 'Agent';
            div.appendChild(label);
        }

        const text = document.createElement('div');
        text.textContent = content;
        div.appendChild(text);

        this.transcript.appendChild(div);

        if (role === 'assistant') {
            this.currentAssistantDiv = div;
        }

        this.scrollToBottom();
    }

    addSystemMessage(content) {
        this.addMessage('system', content);
    }

    addToolBadge(tool) {
        if (this.currentAssistantDiv) {
            const badge = document.createElement('div');
            badge.className = 'tool-badge';
            badge.textContent = tool;
            this.currentAssistantDiv.appendChild(badge);
        }
    }

    scrollToBottom() {
        this.transcriptContainer.scrollTop = this.transcriptContainer.scrollHeight;
    }

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.novaAgent = new NovaVoiceAgent();
});
