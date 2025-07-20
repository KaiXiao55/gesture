from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import requests
import os
import re
import json
import tempfile
import base64
import traceback

app = Flask(__name__)
CORS(app)

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <title>手势助手</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        /* 调试信息面板 */
        .debug-panel {
            position: fixed;
            bottom: 70px;
            right: 20px;
            background: rgba(0, 0, 0, 0.85);
            color: #0f0;
            padding: 15px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-width: 350px;
            max-height: 300px;
            overflow-y: auto;
            display: none;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 255, 0, 0.3);
            z-index: 1000;
        }
        
        .debug-panel.show {
            display: block;
        }
        
        .debug-panel::-webkit-scrollbar {
            width: 8px;
        }
        
        .debug-panel::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 4px;
        }
        
        .debug-panel::-webkit-scrollbar-thumb {
            background: rgba(0, 255, 0, 0.5);
            border-radius: 4px;
        }
        
        .debug-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            z-index: 999;
        }
        
        .debug-toggle:hover {
            background: #444;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }
        
        .debug-log-entry {
            margin-bottom: 5px;
            padding-bottom: 5px;
            border-bottom: 1px solid rgba(0, 255, 0, 0.1);
        }
        
        .debug-time {
            color: #888;
            font-size: 11px;
        }
        
        .debug-message {
            color: #0f0;
            word-wrap: break-word;
        }
        
        .debug-error {
            color: #f44;
        }
        
        .debug-info {
            color: #4af;
        }
        
        /* 手势动画区域 */
        .gesture-section {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .animation-container {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 30px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            max-width: 90%;
            width: 500px;
        }
        
        #hand-canvas {
            border-radius: 20px;
            background: rgba(255,255,255,0.5);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        #gesture-info {
            font-size: 24px;
            color: #333;
            font-weight: bold;
            text-align: center;
        }
        
        /* 输入区域 */
        .input-section {
            padding: 20px;
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 -5px 20px rgba(0, 0, 0, 0.1);
        }
        
        .input-container {
            max-width: 600px;
            margin: 0 auto;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        #user-input {
            flex: 1;
            padding: 15px 25px;
            border: 2px solid #e0e0e0;
            border-radius: 30px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s;
            background: white;
        }
        
        #user-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .input-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
            font-size: 20px;
            color: white;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
        
        #send-btn {
            background: #667eea;
        }
        
        #send-btn:hover {
            background: #5a67d8;
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
        }
        
        #send-btn:active {
            transform: translateY(0);
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
        
        #voice-btn {
            background: #48bb78;
            position: relative;
        }
        
        #voice-btn:hover:not(:disabled) {
            background: #38a169;
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
        }
        
        #voice-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        #voice-btn.recording {
            background: #e53e3e;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { 
                box-shadow: 0 0 0 0 rgba(229, 62, 62, 0.7);
                transform: scale(1);
            }
            50% {
                transform: scale(1.05);
            }
            70% { 
                box-shadow: 0 0 0 15px rgba(229, 62, 62, 0);
                transform: scale(1);
            }
            100% { 
                box-shadow: 0 0 0 0 rgba(229, 62, 62, 0);
                transform: scale(1);
            }
        }
        
        #clear-btn {
            background: #718096;
        }
        
        #clear-btn:hover {
            background: #4a5568;
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
        }
        
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
        
        /* 录音时长显示 */
        .recording-time {
            position: absolute;
            top: -35px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(229, 62, 62, 0.9);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            display: none;
            white-space: nowrap;
        }
        
        .recording-time.show {
            display: block;
        }
        
        /* 提示信息 */
        .tooltip {
            position: fixed;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 14px;
            white-space: nowrap;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        .tooltip.show {
            opacity: 1;
        }
        
        /* 移动端优化 */
        @media (max-width: 768px) {
            #gesture-info {
                font-size: 20px;
            }
            
            .animation-container {
                width: 95%;
                padding: 15px;
            }
            
            #user-input {
                font-size: 16px;
                padding: 12px 20px;
            }
            
            .input-btn {
                width: 45px;
                height: 45px;
                font-size: 18px;
            }
            
            .debug-panel {
                max-width: 80%;
                right: 10px;
                bottom: 60px;
            }
            
            .debug-toggle {
                right: 10px;
                bottom: 10px;
            }
        }
        
        /* 状态指示器 */
        .status-indicator {
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 20px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #48bb78;
            animation: blink 2s infinite;
        }
        
        .status-dot.error {
            background: #e53e3e;
            animation: none;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <!-- 状态指示器 -->
    <div class="status-indicator">
        <span class="status-dot" id="status-dot"></span>
        <span id="status-text">在线</span>
    </div>
    
    <!-- 手势动画区域 -->
    <div class="gesture-section">
        <div class="animation-container">
            <canvas id="hand-canvas" width="400" height="300"></canvas>
            <div id="gesture-info">✨ 准备就绪</div>
        </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="input-section">
        <div class="input-container">
            <input type="text" id="user-input" placeholder="说点什么吧..." autocomplete="off">
            <button class="input-btn" id="voice-btn" onclick="toggleVoiceInput()" title="语音输入">
                <i class="fas fa-microphone"></i>
                <span class="recording-time" id="recording-time">0:00</span>
            </button>
            <button class="input-btn" id="send-btn" onclick="sendMessage()" title="发送">
                <i class="fas fa-paper-plane"></i>
            </button>
            <button class="input-btn" id="clear-btn" onclick="clearContext()" title="清空上下文">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <!-- 调试面板 -->
    <div class="debug-panel" id="debug-panel"></div>
    <button class="debug-toggle" onclick="toggleDebug()">调试信息</button>

    <script>
        // 调试功能
        let debugMode = false;
        const debugPanel = document.getElementById('debug-panel');
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        const MAX_DEBUG_LOGS = 100; // 最大日志条数
        let debugLogs = [];
        
        function toggleDebug() {
            debugMode = !debugMode;
            debugPanel.classList.toggle('show');
            if (debugMode) {
                debug('调试模式已开启', 'info');
            }
        }
        
        function debug(message, type = 'log') {
            console.log(`[${type.toUpperCase()}] ${message}`);
            
            const time = new Date().toLocaleTimeString();
            const logEntry = {
                time: time,
                message: message,
                type: type
            };
            
            debugLogs.push(logEntry);
            if (debugLogs.length > MAX_DEBUG_LOGS) {
                debugLogs.shift();
            }
            
            if (debugMode) {
                updateDebugPanel();
            }
        }
        
        function updateDebugPanel() {
            debugPanel.innerHTML = debugLogs.map(log => {
                const typeClass = log.type === 'error' ? 'debug-error' : 
                                 log.type === 'info' ? 'debug-info' : 'debug-message';
                return `
                    <div class="debug-log-entry">
                        <span class="debug-time">[${log.time}]</span>
                        <span class="${typeClass}">${log.message}</span>
                    </div>
                `;
            }).join('');
            debugPanel.scrollTop = debugPanel.scrollHeight;
        }
        
        function setStatus(online, text) {
            statusDot.classList.toggle('error', !online);
            statusText.textContent = text || (online ? '在线' : '离线');
            debug(`状态更新: ${text || (online ? '在线' : '离线')}`, online ? 'info' : 'error');
        }
        
        // 画布和手势动画相关
        const canvas = document.getElementById('hand-canvas');
        const ctx = canvas.getContext('2d');
        const gestureInfo = document.getElementById('gesture-info');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');
        const voiceBtn = document.getElementById('voice-btn');
        const tooltip = document.getElementById('tooltip');
        const recordingTime = document.getElementById('recording-time');
        
        let currentGesture = 'wave';
        let animationFrame = 0;
        let animationId;
        let isRecording = false;
        let mediaRecorder = null;
        let audioChunks = [];
        let recordingStartTime = null;
        let recordingTimer = null;
        let conversationHistory = [];
        
        // 调整画布大小
        function resizeCanvas() {
            const container = canvas.parentElement;
            const maxWidth = container.clientWidth - 40;
            const maxHeight = window.innerHeight * 0.4;
            const aspectRatio = 400 / 300;
            
            let width = maxWidth;
            let height = width / aspectRatio;
            
            if (height > maxHeight) {
                height = maxHeight;
                width = height * aspectRatio;
            }
            
            canvas.width = width;
            canvas.height = height;
            debug(`画布调整大小: ${width}x${height}`);
        }
        
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();
        
        // 手势动画类
        class HandAnimator {
            constructor() {
                this.updateDimensions();
            }
            
            updateDimensions() {
                this.centerX = canvas.width / 2;
                this.centerY = canvas.height / 2;
                this.scale = Math.min(canvas.width / 400, canvas.height / 300);
                this.skinColor = '#FDBCB4';
                this.skinShadow = '#E89F93';
                this.skinHighlight = '#FFD4C7';
            }
            
            draw() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                this.updateDimensions();
                
                ctx.save();
                ctx.scale(this.scale, this.scale);
                ctx.translate((canvas.width / this.scale - 400) / 2, (canvas.height / this.scale - 300) / 2);
                
                // 绘制手势
                if (!isNaN(currentGesture)) {
                    this.drawNumber(parseInt(currentGesture));
                } else {
                    switch(currentGesture) {
                        case 'wave':
                            this.drawWave();
                            break;
                        case 'thumbsUp':
                            this.drawThumbsUp();
                            break;
                        case 'heart':
                            this.drawHeart();
                            break;
                        case 'thinking':
                            this.drawThinking();
                            break;
                        case 'ok':
                            this.drawOK();
                            break;
                        case 'peace':
                            this.drawPeace();
                            break;
                        case 'clap':
                            this.drawClap();
                            break;
                        case 'rock':
                            this.drawRock();
                            break;
                        case 'facepalm':
                            this.drawFacepalm();
                            break;
                        case 'middleFinger':
                            this.drawMiddleFinger();
                            break;
                        default:
                            this.drawWave();
                    }
                }
                
                ctx.restore();
                animationFrame++;
            }
            
            // 绘制数字手势
            drawNumber(num) {
                if (num >= 0 && num <= 5) {
                    this.drawSingleHandNumber(num, 200, 150);
                } else if (num >= 6 && num <= 10) {
                    const leftNum = 5;
                    const rightNum = num - 5;
                    this.drawSingleHandNumber(leftNum, 100, 150, true);
                    this.drawSingleHandNumber(rightNum, 300, 150, false);
                }
            }
            
            drawSingleHandNumber(num, x, y, isLeft = true) {
                ctx.save();
                ctx.translate(x, y);
                
                this.drawPalm(-200, -150, 90, 110);
                
                switch(num) {
                    case 0:
                        this.drawFist(0, 0);
                        break;
                    case 1:
                        this.drawFinger(-200, -200, 80, 20, 0, 0);
                        this.drawBentFinger(-220, -180, 50, 18, 0.2, 1.5);
                        this.drawBentFinger(-180, -180, 50, 18, -0.2, 1.5);
                        this.drawBentFinger(-165, -175, 45, 16, -0.3, 1.5);
                        break;
                    case 2:
                        this.drawFinger(-215, -200, 80, 20, 0.15, 0);
                        this.drawFinger(-185, -200, 80, 20, -0.15, 0);
                        this.drawBentFinger(-165, -180, 50, 18, -0.3, 1.5);
                        this.drawBentFinger(-235, -180, 45, 16, 0.3, 1.5);
                        break;
                    case 3:
                        this.drawFinger(-220, -200, 80, 20, 0.2, 0);
                        this.drawFinger(-200, -202, 82, 20, 0, 0);
                        this.drawFinger(-180, -200, 80, 20, -0.2, 0);
                        this.drawBentFinger(-160, -180, 45, 16, -0.3, 1.5);
                        break;
                    case 4:
                        this.drawFinger(-230, -198, 75, 18, 0.2, 0);
                        this.drawFinger(-210, -202, 80, 20, 0.1, 0);
                        this.drawFinger(-190, -202, 80, 20, -0.1, 0);
                        this.drawFinger(-170, -198, 75, 18, -0.2, 0);
                        break;
                    case 5:
                        this.drawFinger(-235, -195, 70, 16, 0.3, 0);
                        this.drawFinger(-215, -200, 78, 18, 0.15, 0);
                        this.drawFinger(-200, -202, 82, 20, 0, 0);
                        this.drawFinger(-185, -200, 78, 18, -0.15, 0);
                        this.drawFinger(-165, -195, 70, 16, -0.3, 0);
                        break;
                }
                
                // 拇指
                if (num === 0) {
                    ctx.save();
                    ctx.translate(-230, -160);
                    ctx.rotate(-0.5);
                    this.drawFinger(0, 0, 50, 22, 0, 0.8);
                    ctx.restore();
                } else if (num <= 4) {
                    ctx.save();
                    ctx.translate(-235, -140);
                    ctx.rotate(-1.2);
                    this.drawFinger(0, 0, 50, 22, 0, 1.2);
                    ctx.restore();
                } else {
                    ctx.save();
                    ctx.translate(-245, -145);
                    ctx.rotate(-1);
                    this.drawFinger(0, 0, 60, 22, 0, 0.2);
                    ctx.restore();
                }
                
                ctx.restore();
            }
            
            drawFist(x, y) {
                ctx.save();
                ctx.translate(x, y);
                
                const gradient = ctx.createRadialGradient(-10, -10, 0, 0, 0, 70);
                gradient.addColorStop(0, this.skinHighlight);
                gradient.addColorStop(0.7, this.skinColor);
                gradient.addColorStop(1, this.skinShadow);
                ctx.fillStyle = gradient;
                
                ctx.beginPath();
                ctx.arc(0, 0, 70, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.strokeStyle = this.skinShadow;
                ctx.lineWidth = 1;
                for (let i = 0; i < 4; i++) {
                    ctx.beginPath();
                    ctx.arc(-30 + i * 20, -20, 10, 0, Math.PI);
                    ctx.stroke();
                }
                
                ctx.restore();
            }
            
            drawBentFinger(x, y, length, width, angle, bendAngle) {
                ctx.save();
                ctx.translate(x, y);
                ctx.rotate(angle);
                this.drawFingerAt(0, 0, length, width, 0, bendAngle);
                ctx.restore();
            }
            
            drawFingerAt(x, y, length, width, angle, bendAngle) {
                this.drawFinger(x, y, length, width, angle, bendAngle);
            }
            
            drawFinger(x, y, length, width, angle, bendAngle = 0) {
                ctx.save();
                ctx.translate(x + 200, y + 150);
                ctx.rotate(angle);
                
                const segment1 = length * 0.4;
                const segment2 = length * 0.35;
                const segment3 = length * 0.25;
                
                this.drawFingerSegment(0, 0, segment1, width);
                
                ctx.translate(0, -segment1);
                ctx.rotate(bendAngle);
                this.drawFingerSegment(0, 0, segment2, width * 0.9);
                
                ctx.translate(0, -segment2);
                ctx.rotate(bendAngle * 0.5);
                this.drawFingerSegment(0, 0, segment3, width * 0.8);
                
                ctx.beginPath();
                ctx.arc(0, -segment3, width * 0.4, 0, Math.PI * 2);
                ctx.fillStyle = this.skinColor;
                ctx.fill();
                
                ctx.restore();
            }
            
            drawFingerSegment(x, y, length, width) {
                ctx.fillStyle = this.skinColor;
                ctx.strokeStyle = this.skinShadow;
                ctx.lineWidth = 1;
                
                ctx.beginPath();
                ctx.moveTo(x - width/2, y);
                ctx.lineTo(x - width/2 + 2, y - length);
                ctx.arcTo(x, y - length - width/2, x + width/2 - 2, y - length, width/2);
                ctx.lineTo(x + width/2, y);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
                
                ctx.beginPath();
                ctx.moveTo(x - width/2, y);
                ctx.lineTo(x + width/2, y);
                ctx.strokeStyle = this.skinShadow;
                ctx.lineWidth = 0.5;
                ctx.stroke();
            }
            
            drawPalm(x, y, width, height, rotation = 0) {
                ctx.save();
                ctx.translate(x + 200, y + 150);
                ctx.rotate(rotation);
                
                ctx.fillStyle = 'rgba(0,0,0,0.1)';
                ctx.beginPath();
                ctx.ellipse(5, 5, width/2, height/2, 0, 0, Math.PI * 2);
                ctx.fill();
                
                const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, Math.max(width, height)/2);
                gradient.addColorStop(0, this.skinHighlight);
                gradient.addColorStop(0.7, this.skinColor);
                gradient.addColorStop(1, this.skinShadow);
                ctx.fillStyle = gradient;
                
                ctx.beginPath();
                ctx.ellipse(0, 0, width/2, height/2, 0, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.strokeStyle = this.skinShadow;
                ctx.lineWidth = 0.5;
                ctx.globalAlpha = 0.3;
                
                ctx.beginPath();
                ctx.moveTo(-width/3, -height/4);
                ctx.quadraticCurveTo(0, 0, -width/4, height/3);
                ctx.stroke();
                
                ctx.beginPath();
                ctx.moveTo(-width/3, -height/6);
                ctx.quadraticCurveTo(width/4, -height/8, width/3, 0);
                ctx.stroke();
                
                ctx.globalAlpha = 1;
                ctx.restore();
            }
            
            drawWave() {
                const waveAngle = Math.sin(animationFrame * 0.08) * 0.3;
                
                ctx.fillStyle = this.skinColor;
                ctx.fillRect(170, 230, 60, 100);
                
                ctx.beginPath();
                ctx.ellipse(200, 230, 35, 25, 0, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.save();
                ctx.translate(200, 150);
                ctx.rotate(waveAngle);
                
                this.drawPalm(-200, -150, 100, 120);
                
                this.drawFinger(-230, -200, 70, 18, 0.1, waveAngle * 0.5);
                this.drawFinger(-210, -205, 80, 20, 0.05, waveAngle * 0.3);
                this.drawFinger(-190, -208, 85, 20, 0, waveAngle * 0.2);
                this.drawFinger(-170, -205, 80, 20, -0.05, waveAngle * 0.3);
                
                ctx.save();
                ctx.translate(-240, -140);
                ctx.rotate(-0.8);
                this.drawFinger(0, 0, 60, 22, 0, 0.2);
                ctx.restore();
                
                ctx.restore();
            }
            
            drawThumbsUp() {
                const gradient = ctx.createRadialGradient(190, 140, 0, 200, 150, 80);
                gradient.addColorStop(0, this.skinHighlight);
                gradient.addColorStop(0.7, this.skinColor);
                gradient.addColorStop(1, this.skinShadow);
                ctx.fillStyle = gradient;
                
                ctx.beginPath();
                ctx.moveTo(140, 150);
                ctx.quadraticCurveTo(130, 110, 160, 90);
                ctx.lineTo(240, 90);
                ctx.quadraticCurveTo(270, 110, 260, 150);
                ctx.quadraticCurveTo(260, 210, 200, 220);
                ctx.quadraticCurveTo(140, 210, 140, 150);
                ctx.closePath();
                ctx.fill();
                
                ctx.strokeStyle = this.skinShadow;
                ctx.lineWidth = 1;
                for (let i = 0; i < 4; i++) {
                    ctx.beginPath();
                    ctx.moveTo(170 + i * 20, 110);
                    ctx.lineTo(170 + i * 20, 130);
                    ctx.stroke();
                }
                
                const thumbY = 110 - Math.sin(animationFrame * 0.1) * 10;
                ctx.save();
                ctx.translate(200, thumbY);
                
                ctx.fillStyle = this.skinColor;
                ctx.beginPath();
                ctx.moveTo(-15, 0);
                ctx.lineTo(-15, -40);
                ctx.quadraticCurveTo(-15, -50, -10, -55);
                ctx.arcTo(0, -60, 10, -55, 10);
                ctx.quadraticCurveTo(15, -50, 15, -40);
                ctx.lineTo(15, 0);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
                
                ctx.fillStyle = '#FFE8E0';
                ctx.beginPath();
                ctx.ellipse(0, -50, 12, 15, 0, Math.PI, 0);
                ctx.fill();
                
                ctx.restore();
            }
            
            drawPeace() {
                this.drawPalm(-200, -130, 100, 120);
                
                const spread = Math.sin(animationFrame * 0.05) * 0.05;
                
                this.drawFinger(-210, -190, 90, 20, -0.2 - spread, 0.1);
                this.drawFinger(-190, -190, 90, 20, 0.2 + spread, -0.1);
                
                ctx.save();
                ctx.translate(170, 130);
                ctx.rotate(0.3);
                this.drawFinger(0, 0, 50, 18, 0, 1.2);
                ctx.restore();
                
                ctx.save();
                ctx.translate(230, 130);
                ctx.rotate(-0.3);
                this.drawFinger(0, 0, 45, 16, 0, 1.2);
                ctx.restore();
                
                ctx.save();
                ctx.translate(160, 160);
                ctx.rotate(-0.8);
                this.drawFinger(0, 0, 60, 22, 0, 0.5);
                ctx.restore();
            }
            
            drawOK() {
                this.drawPalm(-200, -150, 100, 120);
                
                ctx.strokeStyle = this.skinColor;
                ctx.lineWidth = 20;
                ctx.lineCap = 'round';
                
                const radius = 35 + Math.sin(animationFrame * 0.1) * 3;
                
                ctx.beginPath();
                ctx.arc(180, 130, radius, 0.5, Math.PI * 1.8);
                ctx.stroke();
                
                this.drawFinger(-180, -200, 80, 20, -0.1, 0);
                this.drawFinger(-160, -195, 75, 18, -0.2, 0);
                this.drawFinger(-145, -190, 65, 16, -0.3, 0);
            }
            
            drawHeart() {
                const scale = 1 + Math.sin(animationFrame * 0.1) * 0.1;
                
                ctx.save();
                ctx.translate(200, 150);
                ctx.scale(scale, scale);
                
                ctx.fillStyle = this.skinColor;
                
                ctx.save();
                ctx.translate(-30, 0);
                ctx.rotate(0.3);
                
                ctx.beginPath();
                ctx.moveTo(0, 20);
                ctx.quadraticCurveTo(-40, -20, -30, -50);
                ctx.quadraticCurveTo(-20, -70, 0, -60);
                ctx.lineTo(0, 20);
                ctx.closePath();
                ctx.fill();
                
                ctx.beginPath();
                ctx.moveTo(0, 20);
                ctx.quadraticCurveTo(20, 10, 30, -10);
                ctx.quadraticCurveTo(35, -30, 20, -40);
                ctx.lineTo(0, -30);
                ctx.closePath();
                ctx.fill();
                
                ctx.restore();
                
                ctx.save();
                ctx.translate(30, 0);
                ctx.rotate(-0.3);
                ctx.scale(-1, 1);
                
                ctx.beginPath();
                ctx.moveTo(0, 20);
                ctx.quadraticCurveTo(-40, -20, -30, -50);
                ctx.quadraticCurveTo(-20, -70, 0, -60);
                ctx.lineTo(0, 20);
                ctx.closePath();
                ctx.fill();
                
                ctx.beginPath();
                ctx.moveTo(0, 20);
                ctx.quadraticCurveTo(20, 10, 30, -10);
                ctx.quadraticCurveTo(35, -30, 20, -40);
                ctx.lineTo(0, -30);
                ctx.closePath();
                ctx.fill();
                
                ctx.restore();
                
                ctx.restore();
                
                ctx.shadowColor = '#FF1744';
                ctx.shadowBlur = 20;
                ctx.strokeStyle = '#FF1744';
                ctx.lineWidth = 2;
                ctx.globalAlpha = 0.5;
                ctx.beginPath();
                ctx.arc(185, 120, 20, 0, Math.PI * 2);
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(215, 120, 20, 0, Math.PI * 2);
                ctx.stroke();
                ctx.globalAlpha = 1;
                ctx.shadowBlur = 0;
            }
            
            drawMiddleFinger() {
                const gradient = ctx.createRadialGradient(190, 170, 0, 200, 180, 70);
                gradient.addColorStop(0, this.skinHighlight);
                gradient.addColorStop(0.7, this.skinColor);
                gradient.addColorStop(1, this.skinShadow);
                ctx.fillStyle = gradient;
                
                ctx.beginPath();
                ctx.moveTo(150, 180);
                ctx.quadraticCurveTo(140, 150, 160, 130);
                ctx.lineTo(240, 130);
                ctx.quadraticCurveTo(260, 150, 250, 180);
                ctx.quadraticCurveTo(240, 220, 200, 225);
                ctx.quadraticCurveTo(160, 220, 150, 180);
                ctx.closePath();
                ctx.fill();
                
                ctx.strokeStyle = this.skinShadow;
                ctx.lineWidth = 1;
                for (let i = 0; i < 4; i++) {
                    ctx.beginPath();
                    ctx.arc(175 + i * 18, 160, 8, 0, Math.PI);
                    ctx.stroke();
                }
                
                const fingerHeight = Math.sin(animationFrame * 0.1) * 5;
                this.drawFinger(-200, -280 - fingerHeight, 90 + fingerHeight, 22, 0, 0.1);
                
                if (animationFrame % 40 < 20) {
                    ctx.strokeStyle = '#FF0000';
                    ctx.lineWidth = 3;
                    ctx.globalAlpha = 0.6;
                    for (let i = 0; i < 3; i++) {
                        ctx.beginPath();
                        ctx.moveTo(160 + i * 40, 50);
                        ctx.lineTo(170 + i * 40, 30);
                        ctx.stroke();
                    }
                    ctx.globalAlpha = 1;
                }
            }
            
            drawRock() {
                this.drawPalm(-200, -150, 100, 120);
                
                this.drawFinger(-230, -200, 85, 20, 0.2, 0);
                this.drawFinger(-170, -195, 75, 18, -0.2, 0);
                
                ctx.save();
                ctx.translate(195, 120);
                this.drawFinger(0, 0, 50, 20, 0, 1.5);
                ctx.restore();
                
                ctx.save();
                ctx.translate(215, 122);
                this.drawFinger(0, 0, 48, 18, 0, 1.5);
                ctx.restore();
                
                ctx.save();
                ctx.translate(160, 150);
                ctx.rotate(-0.9);
                this.drawFinger(0, 0, 60, 22, 0, 0.8);
                ctx.restore();
                
                if (animationFrame % 30 < 15) {
                    ctx.strokeStyle = '#FFEB3B';
                    ctx.lineWidth = 4;
                    ctx.shadowColor = '#FFEB3B';
                    ctx.shadowBlur = 10;
                    ctx.beginPath();
                    ctx.moveTo(140, 30);
                    ctx.lineTo(180, 50);
                    ctx.lineTo(170, 70);
                    ctx.lineTo(210, 90);
                    ctx.stroke();
                    ctx.shadowBlur = 0;
                }
            }
            
            drawThinking() {
                ctx.save();
                ctx.translate(200, 150);
                ctx.rotate(-0.2);
                
                this.drawPalm(-200, -150, 120, 100, 0.5);
                
                this.drawFinger(-240, -180, 60, 20, 0.3, 0.8);
                this.drawFinger(-220, -185, 65, 20, 0.2, 0.9);
                this.drawFinger(-200, -185, 65, 20, 0.1, 0.9);
                this.drawFinger(-180, -180, 55, 18, 0, 0.8);
                
                ctx.save();
                ctx.translate(-250, -130);
                ctx.rotate(-1.2);
                this.drawFinger(0, 0, 60, 22, 0, 0.3);
                ctx.restore();
                
                ctx.restore();
                
                ctx.fillStyle = '#666';
                for(let i = 0; i < 3; i++) {
                    if(animationFrame % 40 > i * 10) {
                        ctx.beginPath();
                        ctx.arc(280 + i * 25, 70, 6, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }
            }
            
            drawClap() {
                const offset = Math.abs(Math.sin(animationFrame * 0.15)) * 40;
                
                ctx.save();
                ctx.translate(160 - offset/2, 150);
                ctx.rotate(0.2);
                
                this.drawPalm(-200, -150, 90, 110);
                
                for(let i = 0; i < 4; i++) {
                    this.drawFinger(-230 + i * 20, -195, 70, 18, -0.1 + i * 0.05, 0.1);
                }
                
                ctx.save();
                ctx.translate(-235, -130);
                ctx.rotate(-0.8);
                this.drawFinger(0, 0, 55, 20, 0, 0.2);
                ctx.restore();
                
                ctx.restore();
                
                ctx.save();
                ctx.translate(240 + offset/2, 150);
                ctx.rotate(-0.2);
                ctx.scale(-1, 1);
                
                this.drawPalm(-200, -150, 90, 110);
                
                for(let i = 0; i < 4; i++) {
                    this.drawFinger(-230 + i * 20, -195, 70, 18, -0.1 + i * 0.05, 0.1);
                }
                
                ctx.save();
                ctx.translate(-235, -130);
                ctx.rotate(-0.8);
                this.drawFinger(0, 0, 55, 20, 0, 0.2);
                ctx.restore();
                
                ctx.restore();
                
                if(offset < 10) {
                    ctx.strokeStyle = '#FFA500';
                    ctx.lineWidth = 2;
                    ctx.globalAlpha = 0.6;
                    for(let i = 0; i < 3; i++) {
                        ctx.beginPath();
                        ctx.arc(200, 150, 80 + i * 20, 0, Math.PI * 2);
                        ctx.stroke();
                    }
                    ctx.globalAlpha = 1;
                    
                    ctx.fillStyle = '#FFD700';
                    const numStars = 5;
                    for(let i = 0; i < numStars; i++) {
                        const angle = (i / numStars) * Math.PI * 2;
                        const dist = 60 + Math.random() * 40;
                        const x = 200 + Math.cos(angle) * dist;
                        const y = 150 + Math.sin(angle) * dist;
                        this.drawStar(x, y, 8);
                    }
                }
            }
            
            drawFacepalm() {
                ctx.fillStyle = '#FFE0BD';
                ctx.beginPath();
                ctx.arc(200, 120, 70, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.fillStyle = '#000';
                ctx.beginPath();
                ctx.arc(175, 110, 3, 0, Math.PI * 2);
                ctx.arc(225, 110, 3, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(200, 150, 20, 0.2, Math.PI - 0.2);
                ctx.stroke();
                
                ctx.save();
                ctx.translate(200, 130);
                ctx.rotate(Math.sin(animationFrame * 0.05) * 0.05);
                
                ctx.globalAlpha = 0.9;
                this.drawPalm(-200, -150, 110, 130);
                
                for(let i = 0; i < 4; i++) {
                    this.drawFinger(-235 + i * 23, -205, 75, 19, -0.1 + i * 0.05, 0.2);
                }
                
                ctx.save();
                ctx.translate(-245, -130);
                ctx.rotate(-0.8);
                this.drawFinger(0, 0, 60, 22, 0, 0.3);
                ctx.restore();
                
                ctx.globalAlpha = 1;
                ctx.restore();
                
                const sweatY = 60 + (animationFrame % 40) * 2;
                ctx.fillStyle = '#4FC3F7';
                ctx.beginPath();
                ctx.moveTo(280, sweatY);
                ctx.quadraticCurveTo(285, sweatY + 10, 280, sweatY + 15);
                ctx.quadraticCurveTo(275, sweatY + 10, 280, sweatY);
                ctx.fill();
            }
            
            drawStar(x, y, size) {
                ctx.beginPath();
                for(let i = 0; i < 5; i++) {
                    const angle = (i * 4 * Math.PI) / 5 - Math.PI / 2;
                    const px = x + Math.cos(angle) * size;
                    const py = y + Math.sin(angle) * size;
                    if(i === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }
                ctx.closePath();
                ctx.fill();
            }
        }
        
        const handAnimator = new HandAnimator();
        
        function animate() {
            handAnimator.draw();
            animationId = requestAnimationFrame(animate);
        }
        
        animate();
        
        // 语音输入设置 - 使用MediaRecorder
        async function setupMediaRecorder() {
            try {
                debug('开始初始化麦克风...');
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                
                // 检查支持的MIME类型
                const mimeTypes = [
                    'audio/webm;codecs=opus',
                    'audio/webm',
                    'audio/ogg;codecs=opus',
                    'audio/mp4'
                ];
                
                let selectedMimeType = '';
                for (const mimeType of mimeTypes) {
                    if (MediaRecorder.isTypeSupported(mimeType)) {
                        selectedMimeType = mimeType;
                        break;
                    }
                }
                
                if (!selectedMimeType) {
                    debug('浏览器不支持音频录制', 'error');
                    return false;
                }
                
                debug(`使用MIME类型: ${selectedMimeType}`);
                
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: selectedMimeType
                });
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                        debug(`音频数据块: ${event.data.size} bytes`);
                    }
                };
                
                mediaRecorder.onstop = async () => {
                    debug('录音停止，开始处理音频数据...');
                    const audioBlob = new Blob(audioChunks, { type: selectedMimeType });
                    audioChunks = [];
                    
                    debug(`音频总大小: ${(audioBlob.size / 1024).toFixed(2)} KB`);
                    
                    // 发送音频到服务器进行转录
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.webm');
                    
                    try {
                        showTooltip('正在识别...');
                        debug('发送音频到服务器进行识别...');
                        
                        const startTime = Date.now();
                        const response = await fetch('/api/transcribe', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const endTime = Date.now();
                        debug(`语音识别响应时间: ${endTime - startTime}ms`);
                        
                        if (!response.ok) {
                            const errorText = await response.text();
                            debug(`服务器错误 (${response.status}): ${errorText}`, 'error');
                            showTooltip('识别失败：服务器错误');
                            return;
                        }
                        
                        const data = await response.json();
                        debug('语音识别结果：' + JSON.stringify(data));
                        
                        if (data.text) {
                            debug(`识别成功: "${data.text}"`);
                            userInput.value = data.text;
                            sendMessage();
                        } else if (data.error) {
                            debug(`识别失败: ${data.error}`, 'error');
                            showTooltip('识别失败：' + data.error);
                        } else {
                            debug('识别结果为空', 'error');
                            showTooltip('未能识别到语音内容');
                        }
                    } catch (error) {
                        debug('语音识别请求失败：' + error.message, 'error');
                        console.error('转录错误:', error);
                        showTooltip('语音识别出错');
                    }
                };
                
                mediaRecorder.onerror = (event) => {
                    debug('MediaRecorder错误：' + event.error, 'error');
                    console.error('MediaRecorder error:', event.error);
                };
                
                debug('麦克风初始化成功', 'info');
                return true;
            } catch (error) {
                debug('麦克风访问失败：' + error.message, 'error');
                console.error('无法访问麦克风:', error);
                
                if (error.name === 'NotAllowedError') {
                    showTooltip('请允许麦克风权限');
                } else if (error.name === 'NotFoundError') {
                    showTooltip('未找到麦克风设备');
                } else {
                    showTooltip('麦克风访问失败');
                }
                
                return false;
            }
        }
        
        // 初始化MediaRecorder
        setupMediaRecorder();
        
        // 更新录音时长显示
        function updateRecordingTime() {
            if (recordingStartTime) {
                const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                recordingTime.textContent = minutes + ':' + seconds.toString().padStart(2, '0');
            }
        }
        
        // 语音输入切换
        async function toggleVoiceInput() {
            if (!mediaRecorder || mediaRecorder.state === 'inactive') {
                const success = await setupMediaRecorder();
                if (!success) {
                    showTooltip('无法访问麦克风');
                    return;
                }
            }
            
            if (isRecording) {
                // 停止录音
                debug('停止录音');
                try {
                    mediaRecorder.stop();
                    // 停止所有音频轨道
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());
                } catch (e) {
                    debug('停止录音时出错：' + e.message, 'error');
                }
                
                isRecording = false;
                voiceBtn.classList.remove('recording');
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                recordingTime.classList.remove('show');
                clearInterval(recordingTimer);
                recordingStartTime = null;
            } else {
                // 开始录音
                debug('开始录音');
                audioChunks = [];
                
                try {
                    mediaRecorder.start(100); // 每100ms获取一次数据
                    isRecording = true;
                    voiceBtn.classList.add('recording');
                    voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
                    recordingTime.classList.add('show');
                    recordingStartTime = Date.now();
                    updateRecordingTime();
                    recordingTimer = setInterval(updateRecordingTime, 1000);
                    showTooltip('正在录音...');
                } catch (e) {
                    debug('开始录音失败：' + e.message, 'error');
                    showTooltip('无法开始录音');
                }
            }
        }
        
        // 工具提示
        function showTooltip(text) {
            tooltip.textContent = text;
            tooltip.classList.add('show');
            debug(`提示: ${text}`, 'info');
            setTimeout(() => {
                tooltip.classList.remove('show');
            }, 3000);
        }
        
        // 发送消息
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message || sendBtn.classList.contains('loading')) return;
            
            debug(`发送消息: "${message}"`);
            
            // 保存消息到历史
            conversationHistory.push({role: 'user', content: message});
            debug(`对话历史长度: ${conversationHistory.length}`);
            
            // 清空输入
            userInput.value = '';
            userInput.focus();
            
            // 禁用输入
            userInput.disabled = true;
            sendBtn.classList.add('loading');
            voiceBtn.disabled = true;
            
            // 显示思考动画
            changeGesture('thinking');
            
            try {
                debug('发送请求到服务器...');
                const startTime = Date.now();
                
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: message,
                        history: conversationHistory
                    })
                });
                
                const endTime = Date.now();
                debug(`服务器响应时间: ${endTime - startTime}ms`);
                
                if (!response.ok) {
                    debug(`服务器错误: ${response.status}`, 'error');
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                debug('收到响应：' + JSON.stringify(data));
                
                if (data.error) {
                    setStatus(false, '错误');
                    showTooltip('错误：' + data.error);
                    debug(`API错误: ${data.error}`, 'error');
                } else {
                    setStatus(true, '在线');
                    
                    // 保存助手回复到历史（不显示）
                    if (data.text) {
                        conversationHistory.push({role: 'assistant', content: data.text});
                        debug(`助手回复: "${data.text}"`);
                    }
                    
                    // 更新手势
                    changeGesture(data.gesture);
                }
                
            } catch (error) {
                debug('请求失败：' + error.message, 'error');
                console.error('Error:', error);
                changeGesture('facepalm');
                showTooltip('出错了，请稍后再试');
                setStatus(false, '连接错误');
            } finally {
                // 恢复输入
                userInput.disabled = false;
                sendBtn.classList.remove('loading');
                voiceBtn.disabled = false;
                userInput.focus();
            }
        }
        
        // 清空上下文
        function clearContext() {
            if (confirm('确定要清空对话上下文吗？')) {
                conversationHistory = [];
                changeGesture('wave');
                showTooltip('上下文已清空');
                debug('对话上下文已清空', 'info');
            }
        }
        
        // 更改手势
        function changeGesture(gesture) {
            currentGesture = gesture;
            gestureInfo.textContent = getGestureName(gesture);
            debug(`切换手势: ${gesture}`);
        }
        
        // 获取手势名称
        function getGestureName(gesture) {
            const names = {
                wave: "👋 挥手",
                thumbsUp: "👍 点赞", 
                heart: "❤️ 爱心",
                thinking: "🤔 思考中",
                middleFinger: "🖕 生气了",
                ok: "👌 OK",
                clap: "👏 鼓掌",
                peace: "✌️ 和平",
                rock: "🤘 摇滚",
                facepalm: "🤦 无语",
                "0": "0️⃣ 零",
                "1": "1️⃣ 一",
                "2": "2️⃣ 二",
                "3": "3️⃣ 三",
                "4": "4️⃣ 四",
                "5": "5️⃣ 五",
                "6": "6️⃣ 六",
                "7": "7️⃣ 七",
                "8": "8️⃣ 八",
                "9": "9️⃣ 九",
                "10": "🔟 十"
            };
            return names[gesture] || "✨ 准备就绪";
        }
        
        // 回车发送
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // 自动聚焦
        userInput.focus();
        
        // 防止iOS键盘问题
        if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) {
            document.addEventListener('touchstart', function(e) {
                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                    document.activeElement.blur();
                }
            });
        }
        
        // 页面加载完成后的初始化
        window.addEventListener('load', function() {
            debug('页面加载完成', 'info');
            debug(`用户代理: ${navigator.userAgent}`);
            debug(`画布大小: ${canvas.width}x${canvas.height}`);
            
            // 检查浏览器特性
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                debug('浏览器不支持getUserMedia API', 'error');
                voiceBtn.disabled = true;
                voiceBtn.title = '浏览器不支持语音输入';
            }
            
            if (typeof MediaRecorder === 'undefined') {
                debug('浏览器不支持MediaRecorder API', 'error');
                voiceBtn.disabled = true;
                voiceBtn.title = '浏览器不支持录音功能';
            }
            
            // 检查API状态
            fetch('/api/test')
                .then(res => res.json())
                .then(data => {
                    debug('API测试结果：' + JSON.stringify(data), 'info');
                    if (!data.has_token) {
                        setStatus(false, 'API未配置');
                        showTooltip('请配置DEEPSEEK_API_TOKEN');
                    } else {
                        debug('DeepSeek API已配置', 'info');
                    }
                    if (data.has_tts_token) {
                        debug('语音识别API已配置', 'info');
                    } else {
                        debug('语音识别API未配置', 'error');
                    }
                })
                .catch(err => {
                    debug('API测试失败：' + err.message, 'error');
                    setStatus(false, '离线');
                });
        });
        
        // 监听错误
        window.addEventListener('error', function(event) {
            debug(`全局错误: ${event.message} at ${event.filename}:${event.lineno}:${event.colno}`, 'error');
        });
        
        window.addEventListener('unhandledrejection', function(event) {
            debug(`未处理的Promise拒绝: ${event.reason}`, 'error');
        });
    </script>
</body>
</html>
"""


# 聊天逻辑类
class ChatLogic:
    def __init__(self):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_token = os.getenv("DEEPSEEK_API_TOKEN", "")

        # 语音识别API配置
        self.tts_api_url = "https://api.uomn.cn/v1/audio/transcriptions"
        self.tts_api_key = "sk-9Q11KSLosBdSRvy8164f697c233c41E680F9FeE26dD26084"

        # 调试输出
        print(f"[启动] API Token 已加载: {'是' if self.api_token else '否'}")
        print(f"[启动] Token 长度: {len(self.api_token) if self.api_token else 0}")
        print(f"[启动] TTS API 已配置: 是")

        self.system_prompt = """你是一个手势助手。用户会向你发送消息，你需要理解用户的情感和意图，
然后用一个合适的手势来回应。你的回复应该简短友好，像朋友之间的对话。
记住：你的主要任务是选择合适的手势，而不是长篇大论。"""

    def _clean_response(self, content: str) -> str:
        """清理模型的回复内容"""
        content = re.sub(r"\*\*.*?\*\*", "", content)
        content = re.sub(r"\n\s*\n", "\n", content)
        return content.strip()

    def get_response(self, messages):
        """获取模型回复"""
        full_messages = [{"role": "system", "content": self.system_prompt}] + messages

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        payload = {
            "model": "deepseek-chat",
            "messages": full_messages,
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False,
        }

        try:
            print(f"[调试] 调用DeepSeek API")
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=15
            )
            response.raise_for_status()
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"].get("content", "")
                cleaned_content = self._clean_response(content)

                return {"text": cleaned_content or "明白了！", "success": True}

        except Exception as e:
            print(f"[错误] API Error: {e}")
            return {"text": "抱歉，我现在无法回复。", "success": False}


# 手势选择器
class GestureSelector:
    """根据回复内容选择合适的手势"""

    @staticmethod
    def select_gesture(text):
        text = text.lower()

        # 检查问句
        if any(
            word in text
            for word in [
                "怎么样",
                "什么",
                "为什么",
                "如何",
                "哪里",
                "多少",
                "？",
                "吗",
                "呢",
            ]
        ):
            if any(greeting in text for greeting in ["你好", "嗨", "hello", "hi"]):
                return "wave"
            return "thinking"

        # 检查数字
        numbers = re.findall(r"([0-9]|10)", text)
        if numbers:
            return numbers[-1]

        # 中文数字
        chinese_numbers = {
            "零": "0",
            "一": "1",
            "二": "2",
            "三": "3",
            "四": "4",
            "五": "5",
            "六": "6",
            "七": "7",
            "八": "8",
            "九": "9",
            "十": "10",
        }
        for cn, num in chinese_numbers.items():
            if cn in text:
                return num

        # 关键词映射
        gesture_keywords = {
            "heart": [
                "爱",
                "喜欢",
                "亲",
                "么么",
                "想你",
                "爱你",
                "心",
                "宝贝",
                "❤",
                "💕",
            ],
            "thumbsUp": [
                "好",
                "棒",
                "赞",
                "厉害",
                "优秀",
                "不错",
                "真好",
                "太好了",
                "great",
                "excellent",
            ],
            "clap": ["恭喜", "祝贺", "太棒了", "鼓掌", "精彩", "加油"],
            "ok": [
                "ok",
                "好的",
                "没问题",
                "可以",
                "行",
                "明白",
                "了解",
                "知道了",
                "收到",
            ],
            "peace": ["和平", "友好", "冷静", "友谊", "平静", "peace", "calm"],
            "wave": ["你好", "嗨", "再见", "拜拜", "hello", "hi", "bye", "欢迎"],
            "facepalm": [
                "无语",
                "晕",
                "无奈",
                "崩溃",
                "受不了",
                "天啊",
                "醉了",
                "尴尬",
            ],
            "middleFinger": ["傻", "笨", "蠢", "烦", "滚", "讨厌", "恶心"],
            "thinking": ["想", "思考", "考虑", "琢磨", "分析", "嗯", "不确定", "或许"],
            "rock": ["摇滚", "酷", "炫", "燃", "激情", "rock", "cool", "awesome"],
        }

        # 检查关键词
        for gesture, keywords in gesture_keywords.items():
            if any(keyword in text for keyword in keywords):
                return gesture

        # 默认手势
        return "ok" if len(text) > 20 else "wave"


# 创建全局实例
chat_logic = ChatLogic()


# 路由
@app.route("/", methods=["GET"])
def index():
    return Response(HTML_TEMPLATE, mimetype="text/html")


@app.route("/api/test", methods=["GET"])
def test():
    """测试接口"""
    return jsonify(
        {
            "status": "ok",
            "has_token": bool(chat_logic.api_token),
            "has_tts_token": bool(chat_logic.tts_api_key),
            "token_length": len(chat_logic.api_token) if chat_logic.api_token else 0,
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        history = data.get("history", [])

        print(f"[聊天] 收到消息: {user_message}")

        # 获取回复
        response = chat_logic.get_response(history)

        # 选择手势
        gesture = GestureSelector.select_gesture(response["text"])

        print(f"[聊天] 回复: {response['text']}")
        print(f"[聊天] 手势: {gesture}")

        return jsonify({"text": response["text"], "gesture": gesture})

    except Exception as e:
        print(f"[错误] 聊天处理错误: {e}")
        traceback.print_exc()
        return jsonify({"text": "抱歉，出现了一些问题。", "gesture": "facepalm"})


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    """语音转文字接口"""
    try:
        print("[语音识别] 开始处理语音请求")

        if "audio" not in request.files:
            print("[语音识别] 错误：未找到音频文件")
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]
        print(f"[语音识别] 接收到音频文件: {audio_file.filename}")
        print(f"[语音识别] 音频文件类型: {audio_file.content_type}")

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_filename = tmp_file.name
            file_size = os.path.getsize(tmp_filename)
            print(f"[语音识别] 临时文件保存至: {tmp_filename}")
            print(f"[语音识别] 文件大小: {file_size / 1024:.2f} KB")

        try:
            # 调用语音转文字API
            print(f"[语音识别] 准备发送到API: {chat_logic.tts_api_url}")

            headers = {"Authorization": f"Bearer {chat_logic.tts_api_key}"}

            with open(tmp_filename, "rb") as f:
                files = {"file": ("audio.webm", f, "audio/webm")}
                data = {"model": "whisper-1", "language": "zh"}

                print("[语音识别] 发送请求到语音识别API...")
                response = requests.post(
                    chat_logic.tts_api_url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30,
                )

                print(f"[语音识别] API响应状态码: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"[语音识别] API响应内容: {result}")

                    text = result.get("text", "")
                    if text:
                        print(f"[语音识别] 识别成功: {text}")
                        return jsonify({"text": text})
                    else:
                        print("[语音识别] 错误：API返回空文本")
                        return jsonify({"error": "No text recognized"}), 400
                else:
                    print(f"[语音识别] API错误响应: {response.text}")
                    error_msg = f"API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get(
                            "message", error_msg
                        )
                    except:
                        pass
                    return jsonify({"error": error_msg}), response.status_code

        finally:
            # 清理临时文件
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
                print(f"[语音识别] 已删除临时文件: {tmp_filename}")

    except Exception as e:
        print(f"[语音识别] 未知错误: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 这是最重要的部分 - Vercel需要的
app = app
