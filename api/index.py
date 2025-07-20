from flask import Flask, Response

app = Flask(__name__)

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
        }
        
        #voice-btn:hover {
            background: #38a169;
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
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
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <!-- 状态指示器 -->
    <div class="status-indicator">
        <span class="status-dot"></span>
        <span>在线</span>
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

    <script>
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
        }
        
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();
        
        // 手势动画类（与原代码相同，这里省略具体实现）
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
            
            // 以下是所有绘制方法（与原代码相同）
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
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm'
                });
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    audioChunks = [];
                    
                    // 发送音频到服务器进行转录
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.webm');
                    
                    try {
                        showTooltip('正在识别...');
                        const response = await fetch('/api/transcribe', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        if (data.text) {
                            userInput.value = data.text;
                            sendMessage();
                        } else if (data.error) {
                            showTooltip('识别失败：' + data.error);
                        }
                    } catch (error) {
                        console.error('转录错误:', error);
                        showTooltip('语音识别出错');
                    }
                };
                
                return true;
            } catch (error) {
                console.error('无法访问麦克风:', error);
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
                recordingTime.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
        }
        
        // 语音输入切换
        async function toggleVoiceInput() {
            if (!mediaRecorder) {
                const success = await setupMediaRecorder();
                if (!success) {
                    showTooltip('无法访问麦克风');
                    return;
                }
            }
            
            if (isRecording) {
                // 停止录音
                mediaRecorder.stop();
                isRecording = false;
                voiceBtn.classList.remove('recording');
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                recordingTime.classList.remove('show');
                clearInterval(recordingTimer);
                recordingStartTime = null;
            } else {
                // 开始录音
                audioChunks = [];
                mediaRecorder.start();
                isRecording = true;
                voiceBtn.classList.add('recording');
                voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
                recordingTime.classList.add('show');
                recordingStartTime = Date.now();
                updateRecordingTime();
                recordingTimer = setInterval(updateRecordingTime, 1000);
                showTooltip('正在录音...');
            }
        }
        
        // 工具提示
        function showTooltip(text) {
            tooltip.textContent = text;
            tooltip.classList.add('show');
            setTimeout(() => {
                tooltip.classList.remove('show');
            }, 3000);
        }
        
        // 发送消息
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message || sendBtn.classList.contains('loading')) return;
            
            // 保存消息到历史
            conversationHistory.push({role: 'user', content: message});
            
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
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: message,
                        history: conversationHistory
                    })
                });
                
                const data = await response.json();
                
                // 保存助手回复到历史（不显示）
                if (data.text) {
                    conversationHistory.push({role: 'assistant', content: data.text});
                }
                
                // 更新手势
                changeGesture(data.gesture);
                
            } catch (error) {
                console.error('Error:', error);
                changeGesture('facepalm');
                showTooltip('出错了，请稍后再试');
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
            }
        }
        
        // 更改手势
        function changeGesture(gesture) {
            currentGesture = gesture;
            gestureInfo.textContent = getGestureName(gesture);
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
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return Response(HTML_TEMPLATE, mimetype="text/html")


# Vercel需要的handler
handler = app
