from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import random
from string import ascii_uppercase
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "goodchat_secret_key_2024"
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

def generate_unique_code(length=6):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

# Read the HTML template
def get_goodchat_template():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChitChat - Real-time Chat Rooms</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
            position: relative;
            height: 100vh;
        }

        .background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            z-index: -1;
        }

        .background.welcome {
            background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
        }

        .background.join {
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #fd79a8 100%);
        }

        .background.create {
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #fd79a8 100%);
        }

        .background.chat {
            background: linear-gradient(135deg, #ddd6fe 0%, #c7d2fe 50%, #fed7d7 100%);
        }

        .container {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px 20px 120px 20px; /* Increased bottom padding by ~70px more */
        }

        .card {
            background: white;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            position: relative;
            backdrop-filter: blur(10px);
            max-width: 500px;
            width: 100%;
        }

        .chat-card {
            max-width: 900px;
            height: 700px;
            padding: 0;
            display: flex;
            flex-direction: column;
            margin-bottom: 140px; /* Increased bottom margin significantly */
        }

        .floating-icons {
            position: absolute;
            top: -15px;
            right: 20px;
            display: flex;
            gap: 10px;
        }

        .floating-icon {
            width: 50px;
            height: 50px;
            background: rgba(255,255,255,0.9);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }

        .floating-icon.notification {
            position: relative;
        }

        .floating-icon.notification::after {
            content: '';
            position: absolute;
            top: 8px;
            right: 8px;
            width: 12px;
            height: 12px;
            background: #ff6b6b;
            border-radius: 50%;
        }

        .brand {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .chat-header .brand {
            margin-bottom: 5px;
        }

        .brand h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .brand p {
            color: #666;
            font-size: 1.1rem;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }

        .input-field {
            width: 100%;
            padding: 16px 20px;
            border: 2px solid #f1f3f4;
            border-radius: 16px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #f8f9fa;
        }

        .input-field:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .input-field::placeholder {
            color: #999;
        }

        .button-group {
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }

        .btn {
            flex: 1;
            padding: 16px 24px;
            border: none;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(102, 126, 234, 0.4);
        }

        .btn-success {
            background: linear-gradient(135deg, #56c596, #4fd1c7);
            color: white;
            box-shadow: 0 8px 16px rgba(86, 197, 150, 0.3);
        }

        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(86, 197, 150, 0.4);
        }

        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b, #ee5253);
            color: white;
            box-shadow: 0 8px 16px rgba(255, 107, 107, 0.3);
        }
        
        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(255, 107, 107, 0.4);
        }

        .password-field {
            position: relative;
        }

        .password-toggle {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            cursor: pointer;
            color: #667eea;
            font-size: 20px;
        }

        .error-message {
            background: #fee;
            border: 1px solid #fcc;
            color: #c33;
            padding: 12px 16px;
            border-radius: 12px;
            margin: 15px 0;
            font-size: 14px;
        }

        .success-message {
            background: #efe;
            border: 1px solid #cfc;
            color: #3c3;
            padding: 12px 16px;
            border-radius: 12px;
            margin: 15px 0;
            font-size: 14px;
        }

        /* Chat Room Styles */
        .chat-header {
            background: white;
            padding: 10px 15px;
            border-bottom: 1px solid #eee;
            border-radius: 24px 24px 0 0;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .chat-header-actions {
            display: flex;
            gap: 10px;
            margin-top: 5px;
        }

        .room-id {
            display: inline-block;
            background: #f8f9fa;
            padding: 6px 12px;
            border-radius: 20px;
            font-family: monospace;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
            font-size: 14px;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px 30px;
            background: white;
            min-height: 600px; /* Ensure chat area takes up most space */
        }

        .message {
            margin-bottom: 16px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }

        .message.own {
            flex-direction: row-reverse;
        }

        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
            flex-shrink: 0;
        }

        .message-content {
            max-width: 70%;
        }

        .message-bubble {
            background: #f1f3f4;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }

        .message.own .message-bubble {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }

        .message-info {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
            font-size: 12px;
            color: #666;
        }

        .message.own .message-info {
            justify-content: flex-end;
        }

        .message-time {
            font-size: 11px;
            color: #999;
            margin-top: 4px;
        }

        .chat-input {
            background: white;
            padding: 20px 30px;
            border-top: 1px solid #eee;
            border-radius: 0 0 24px 24px;
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 20px;
        }

        .chat-input input {
            flex: 1;
            border: none;
            background: #f8f9fa;
            border-radius: 20px;
            padding: 12px 20px;
            font-size: 14px;
        }

        .chat-input input:focus {
            outline: none;
            background: white;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        }

        .send-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }

        .send-btn:hover {
            transform: scale(1.05);
        }

        .system-message {
            text-align: center;
            color: #666;
            font-size: 13px;
            font-style: italic;
            margin: 16px 0;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 12px;
        }

        /* Improved responsiveness for various screen sizes */
        @media (max-width: 1200px) {
            .chat-card {
                max-width: 800px;
            }
        }
        
        @media (max-width: 992px) {
            .chat-card {
                max-width: 700px;
                height: 650px;
            }
            
            .chat-messages {
                min-height: 500px;
            }
        }
        
        @media (max-width: 768px) {
            .card {
                margin: 10px;
                padding: 30px 20px;
            }
            
            .button-group {
                flex-direction: column;
            }
            
            .chat-card {
                height: calc(100vh - 180px);
                margin: 20px 10px 100px 10px;
                max-width: 100%;
            }
            
            .container {
                padding: 10px 10px 100px 10px;
            }
        }
        
        @media (max-width: 480px) {
            .input-field {
                padding: 12px 16px;
                font-size: 14px;
            }
            
            .btn {
                padding: 12px 18px;
                font-size: 14px;
            }
            
            .brand h1 {
                font-size: 2rem;
            }
            
            .chat-messages {
                padding: 15px 20px;
            }
            
            .message-bubble {
                padding: 10px 14px;
                font-size: 14px;
            }
        }

        .loading {
            display: none;
            justify-content: center;
            align-items: center;
            gap: 4px;
            margin: 10px 0;
        }

        .loading.show {
            display: flex;
        }

        .loading-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #667eea;
            animation: loading 1.4s infinite ease-in-out;
        }

        .loading-dot:nth-child(1) { animation-delay: -0.32s; }
        .loading-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes loading {
            0%, 80%, 100% {
                transform: scale(0);
            }
            40% {
                transform: scale(1);
            }
        }

        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="background welcome" id="background"></div>
    
    <!-- Welcome Screen -->
    <div class="container" id="welcomeScreen">
        <div class="card">
            <div class="floating-icons">
                <div class="floating-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                        <circle cx="12" cy="7" r="4"/>
                    </svg>
                </div>
                <div class="floating-icon notification">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                        <circle cx="12" cy="7" r="4"/>
                    </svg>
                </div>
            </div>
            
            <div class="brand">
                <h1>ChitChat</h1>
            </div>
            
            <div class="form-group">
                <input type="text" class="input-field" id="username" placeholder="Enter your Username" maxlength="20">
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="showCreateRoom()">Create Room</button>
                <button class="btn btn-success" onclick="showJoinRoom()">Join Room</button>
            </div>
            
            <div id="errorMessage"></div>
        </div>
    </div>

    <!-- Join Room Screen -->
    <div class="container hidden" id="joinScreen">
        <div class="card">
            <div class="brand">
                <h1>Join an Existing Room</h1>
            </div>
            
            <div class="form-group">
                <label>Username</label>
                <input type="text" class="input-field" id="joinUsername" placeholder="your Existing Name" readonly>
            </div>
            
            <div class="form-group">
                <label>Room ID</label>
                <input type="text" class="input-field" id="roomId" placeholder="Enter Room ID" maxlength="10">
            </div>
            
            <div class="form-group">
                <label>Password (if required)</label>
                <div class="password-field">
                    <input type="password" class="input-field" id="roomPassword" placeholder="Enter room password (optional)">
                    <button type="button" class="password-toggle" onclick="togglePassword('roomPassword')">👁️</button>
                </div>
            </div>
            
            <div class="loading" id="joinLoading">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="joinRoom()">Join Room</button>
            </div>
            
            <div class="button-group" style="margin-top: 15px;">
                <button class="btn" style="background: #f1f3f4; color: #333;" onclick="goBack()">← Back</button>
            </div>
            
            <div id="joinErrorMessage"></div>
        </div>
    </div>

    <!-- Create Room Screen -->
    <div class="container hidden" id="createScreen">
        <div class="card">
            <div class="brand">
                <h1>Create a New Room</h1>
            </div>
            
            <div class="form-group">
                <label>Username (Pre-filled)</label>
                <input type="text" class="input-field" id="createUsername" readonly>
            </div>
            
            <div class="form-group">
                <label>Room ID</label>
                <input type="text" class="input-field" id="newRoomId" placeholder="Enter custom room ID or leave blank for auto-generation" maxlength="10">
            </div>
            
            <div class="form-group">
                <label>Password (Optional)</label>
                <input type="password" class="input-field" id="newRoomPassword" placeholder="Set room password (optional)">
            </div>
            
            <div class="loading" id="createLoading">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="createRoom()">Create Room</button>
            </div>
            
            <div class="button-group" style="margin-top: 15px;">
                <button class="btn" style="background: #f1f3f4; color: #333;" onclick="goBack()">← Back</button>
            </div>
            
            <div id="createErrorMessage"></div>
        </div>
    </div>

    <!-- Chat Room Screen -->
    <div class="container hidden" id="chatScreen">
        <div class="card chat-card">
            <div class="chat-header">
                <div class="brand">
                    <h1 style="font-size: 1.5rem; margin-bottom: 0;">ChitChat</h1>
                </div>
                <div class="room-id">Room ID: #<span id="currentRoomId"></span></div>
                <div style="font-size: 11px; color: #666; margin-top: 3px; margin-bottom: 5px;">
                    <span id="userCount">1</span> user(s) online
                </div>
                <div class="chat-header-actions">
                    <button class="btn btn-danger" style="padding: 6px 12px; font-size: 12px;" onclick="leaveRoom()">Leave Room</button>
                </div>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <!-- Messages will be populated here -->
            </div>
            
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Type your message..." maxlength="500">
                <button class="send-btn" onclick="sendMessage()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="22" y1="2" x2="11" y2="13"/>
                        <polygon points="22,2 15,22 11,13 2,9"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <script>
        // App State
        let currentUser = '';
        let currentRoom = '';
        let currentPassword = '';
        let socket = null;

        // Initialize the app
        function init() {
            // Add enter key listeners
            document.getElementById('username').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    if (this.value.trim()) {
                        showCreateRoom();
                    }
                }
            });

            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            document.getElementById('roomId').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    joinRoom();
                }
            });

            document.getElementById('roomPassword').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    joinRoom();
                }
            });
        }

        // Navigation functions
        function showCreateRoom() {
            const username = document.getElementById('username').value.trim();
            if (!username) {
                showError('errorMessage', 'Please enter a username');
                return;
            }
            
            currentUser = username;
            document.getElementById('createUsername').value = username;
            
            switchScreen('welcomeScreen', 'createScreen');
            document.getElementById('background').className = 'background create';
        }

        function showJoinRoom() {
            const username = document.getElementById('username').value.trim();
            if (!username) {
                showError('errorMessage', 'Please enter a username');
                return;
            }
            
            currentUser = username;
            document.getElementById('joinUsername').value = username;
            
            switchScreen('welcomeScreen', 'joinScreen');
            document.getElementById('background').className = 'background join';
        }

        function goBack() {
            switchScreen(['createScreen', 'joinScreen'], 'welcomeScreen');
            document.getElementById('background').className = 'background welcome';
            clearErrors();
        }

        function switchScreen(from, to) {
            if (Array.isArray(from)) {
                from.forEach(screen => document.getElementById(screen).classList.add('hidden'));
            } else {
                document.getElementById(from).classList.add('hidden');
            }
            document.getElementById(to).classList.remove('hidden');
        }

        // Room management
        function createRoom() {
            const roomId = document.getElementById('newRoomId').value.trim().toUpperCase() || generateRoomId();
            const password = document.getElementById('newRoomPassword').value;
            
            if (roomId.length < 3) {
                showError('createErrorMessage', 'Room ID must be at least 3 characters');
                return;
            }
            
            showLoading('createLoading');
            
            // Send create room request to server
            fetch('/create_room', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: currentUser,
                    room_id: roomId,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading('createLoading');
                if (data.success) {
                    currentRoom = data.room_id;
                    currentPassword = password;
                    enterChatRoom(data.room_id);
                    showSuccess('createErrorMessage', 'Room created successfully!');
                } else {
                    showError('createErrorMessage', data.error);
                }
            })
            .catch(error => {
                hideLoading('createLoading');
                showError('createErrorMessage', 'Failed to create room. Please try again.');
            });
        }

        function joinRoom() {
            const roomId = document.getElementById('roomId').value.trim().toUpperCase();
            const password = document.getElementById('roomPassword').value;
            
            if (!roomId) {
                showError('joinErrorMessage', 'Please enter a room ID');
                return;
            }
            
            showLoading('joinLoading');
            
            // Send join room request to server
            fetch('/join_room', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: currentUser,
                    room_id: roomId,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading('joinLoading');
                if (data.success) {
                    currentRoom = roomId;
                    currentPassword = password;
                    enterChatRoom(roomId);
                    showSuccess('joinErrorMessage', 'Joined room successfully!');
                } else {
                    showError('joinErrorMessage', data.error);
                }
            })
            .catch(error => {
                hideLoading('joinLoading');
                showError('joinErrorMessage', 'Failed to join room. Please try again.');
            });
        }

        function leaveRoom() {
            if (socket) {
                socket.disconnect();
            }
            
            switchScreen('chatScreen', 'welcomeScreen');
            document.getElementById('background').className = 'background welcome';
            document.getElementById('chatMessages').innerHTML = '';
            
            currentRoom = '';
            currentPassword = '';
        }

        function generateRoomId() {
            return Math.random().toString(36).substr(2, 6).toUpperCase();
        }

        function enterChatRoom(roomId) {
            document.getElementById('currentRoomId').textContent = roomId;
            switchScreen(['createScreen', 'joinScreen'], 'chatScreen');
            document.getElementById('background').className = 'background chat';
            
            // Initialize Socket.IO
            initializeSocket();
        }

        // Socket.IO functionality
        function initializeSocket() {
            socket = io();
            
            // Join the room
            socket.emit('join_room', {
                username: currentUser,
                room: currentRoom,
                password: currentPassword
            });

            // Listen for messages
            socket.on('message', function(data) {
                if (data.username) {
                    addMessage(data.username, data.message, data.username === currentUser);
                } else {
                    addSystemMessage(data.message);
                }
            });

            // Listen for user count updates
            socket.on('user_count', function(data) {
                document.getElementById('userCount').textContent = data.count;
            });

            // Listen for connection events
            socket.on('connect', function() {
                console.log('Connected to server');
            });

            socket.on('disconnect', function() {
                console.log('Disconnected from server');
            });

            // Listen for errors
            socket.on('error', function(data) {
                showError('chatMessages', data.message);
            });
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !socket) return;
            
            // Send message via socket
            socket.emit('send_message', {
                message: message,
                room: currentRoom,
                username: currentUser
            });
            
            // Clear input
            input.value = '';
        }

        function addMessage(username, message, isOwn = false) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isOwn ? 'own' : ''}`;
            
            const avatarDiv = document.createElement('div');
            avatarDiv.className = 'message-avatar';
            avatarDiv.textContent = username.charAt(0).toUpperCase();
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            const infoDiv = document.createElement('div');
            infoDiv.className = 'message-info';
            infoDiv.innerHTML = `<strong style="color: ${isOwn ? '#667eea' : '#333'}">${username}</strong>`;
            
            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';
            bubbleDiv.textContent = message;
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            contentDiv.appendChild(infoDiv);
            contentDiv.appendChild(bubbleDiv);
            contentDiv.appendChild(timeDiv);
            
            messageDiv.appendChild(avatarDiv);
            messageDiv.appendChild(contentDiv);
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addSystemMessage(message) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'system-message';
            messageDiv.textContent = message;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Utility functions
        function showError(containerId, message) {
            const container = document.getElementById(containerId);
            container.innerHTML = `<div class="error-message">${message}</div>`;
        }

        function showSuccess(containerId, message) {
            const container = document.getElementById(containerId);
            container.innerHTML = `<div class="success-message">${message}</div>`;
        }

        function clearErrors() {
            ['errorMessage', 'joinErrorMessage', 'createErrorMessage'].forEach(id => {
                document.getElementById(id).innerHTML = '';
            });
        }

        function showLoading(loadingId) {
            document.getElementById(loadingId).classList.add('show');
        }

        function hideLoading(loadingId) {
            document.getElementById(loadingId).classList.remove('show');
        }

        function togglePassword(inputId) {
            const input = document.getElementById(inputId);
            const button = input.nextElementSibling;
            
            if (input.type === 'password') {
                input.type = 'text';
                button.textContent = '🙈';
            } else {
                input.type = 'password';
                button.textContent = '👁️';
            }
        }

        // Initialize app when DOM is loaded
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>'''

@app.route("/")
def home():
    return render_template_string(get_goodchat_template())

@app.route("/create_room", methods=["POST"])
def create_room_api():
    try:
        data = request.get_json()
        username = data.get('username')
        room_id = data.get('room_id')
        password = data.get('password', '')
        
        if not username:
            return jsonify({'success': False, 'error': 'Please enter a username'})

        # Check if provided room ID already exists
        if room_id in rooms:
            return jsonify({'success': False, 'error': 'Room ID already exists. Please choose another.'})
        
        # Create a new room
        rooms[room_id] = {
            "members": 0,
            "messages": [],
            "password": password
        }
        
        return jsonify({'success': True, 'room_id': room_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route("/join_room", methods=["POST"])
def join_room_api():
    try:
        data = request.get_json()
        username = data.get('username')
        room_id = data.get('room_id')
        password = data.get('password', '')
        
        if not username:
            return jsonify({'success': False, 'error': 'Please enter a username'})
            
        if not room_id:
            return jsonify({'success': False, 'error': 'Please enter a room ID'})
            
        # Check if the room exists
        if room_id not in rooms:
            return jsonify({'success': False, 'error': 'Room does not exist'})
            
        # Check if the password is correct
        if rooms[room_id]["password"] and rooms[room_id]["password"] != password:
            return jsonify({'success': False, 'error': 'Incorrect password'})
            
        return jsonify({'success': True, 'room_id': room_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@socketio.on("join_room")
def handle_join_room(data):
    room = data.get("room")
    username = data.get("username")
    password = data.get("password", "")
    
    # Validate the room again
    if room not in rooms:
        emit('error', {'message': 'Room does not exist'})
        return
    
    # Validate the password
    if rooms[room]["password"] and rooms[room]["password"] != password:
        emit('error', {'message': 'Incorrect password'})
        return
    
    # Join the room
    join_room(room)
    
    # Increment user count
    rooms[room]["members"] += 1
    
    # Send a system message to the room
    send({"message": f"{username} has joined the room"}, to=room)
    
    # Broadcast updated user count
    emit('user_count', {'count': rooms[room]["members"]}, to=room)
    
    print(f"{username} joined room {room}")

@socketio.on("send_message")
def handle_send_message(data):
    room = data.get("room")
    username = data.get("username")
    message = data.get("message")
    
    if not room or not username or not message:
        return
    
    if room not in rooms:
        emit('error', {'message': 'Room does not exist'})
        return
    
    # Create the message content
    content = {
        "username": username,
        "message": message
    }
    
    # Send the message to the room
    send(content, to=room)
    
    # Store the message
    rooms[room]["messages"].append(content)
    
    print(f"{username} said in {room}: {message}")

@socketio.on("disconnect")
def handle_disconnect():
    for room_id in rooms:
        if rooms[room_id]["members"] > 0:
            rooms[room_id]["members"] -= 1
            emit('user_count', {'count': rooms[room_id]["members"]}, to=room_id)
    
    print("User disconnected")

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 