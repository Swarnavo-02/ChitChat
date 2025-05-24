from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import random
from string import ascii_uppercase
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "goodchat_secret_key_2024"
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}
user_sessions = {}  # Track user sessions by room

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
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #667eea;
            --accent-color-transparent: rgba(102, 126, 234, 0.2);
            --background-color: #f8f9fa;
            --card-color: #ffffff;
            --text-color: #333333;
            --border-color: #e1e4e8;
            --message-own-bg: linear-gradient(135deg, #667eea, #764ba2);
            --message-other-bg: #f1f3f4;
            --sidebar-bg: #ffffff;
            --input-bg: #f8f9fa;
            --input-focus-bg: #ffffff;
            --emoji-panel-bg: #ffffff;
            --typing-indicator-color: #667eea;
            --system-message-bg: #f8f9fa;
            --system-message-color: #666666;
            --theme-toggle-bg: rgba(255, 255, 255, 0.2);
            --theme-toggle-color: #333333;
        }
        
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
            background-color: var(--background-color);
            color: var(--text-color);
            transition: background-color 0.3s ease, color 0.3s ease;
            margin: 0;
            padding: 0;
        }

        html {
            height: 100%;
            box-sizing: border-box;
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
            padding: 10px;
            flex-direction: column;
            gap: 0;
            height: 100%;
            overflow: hidden;
            width: 100%;
            max-width: 100%;
            padding-bottom: 30px; /* Add gap at the bottom of the page */
        }
        
        .chat-container {
            display: flex;
            flex-direction: row;
            align-items: flex-start;
            justify-content: center;
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            gap: 10px; /* Reduce space between chat and user list */
            margin-bottom: 0; /* Remove space as message box is now connected */
            flex: 1;
            height: 100%;
        }

        .card {
            background: var(--card-color);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            position: relative;
            backdrop-filter: blur(10px);
            max-width: 500px;
            width: 100%;
            transition: background-color 0.3s ease, box-shadow 0.3s ease;
        }

        .chat-card {
            max-width: 900px;
            height: calc(100vh - 60px); /* Make it almost full height but leave gap */
            padding: 0;
            display: flex;
            flex-direction: column;
            margin-bottom: 20px;
            flex: 1;
            border-radius: 24px;
            overflow: hidden;
            background-color: var(--card-color);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            transition: background-color 0.3s ease;
            width: 75%;
            min-width: 600px;
        }

        .chat-input-container {
            max-width: 900px;
            width: 100%;
            margin-bottom: 10px;
            flex: 0;
        }

        .chat-main {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
        }

        .user-card {
            width: 20%;
            background: var(--card-color);
            border-radius: 24px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            height: calc(100vh - 60px); /* Match chat card height */
            padding: 0;
            transition: background-color 0.3s ease;
            max-width: 200px;
        }

        .user-sidebar {
            flex: 1;
            background: var(--sidebar-bg);
            border-radius: 0 0 24px 24px;
            display: flex;
            flex-direction: column;
            transition: background-color 0.3s ease;
        }

        .user-sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            background: var(--card-color);
            transition: background-color 0.3s ease;
        }

        .user-sidebar-header h3 {
            margin: 0;
            font-size: 16px;
            color: #333;
            font-weight: 600;
        }

        .user-list {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
        }

        .user-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: 24px;
            margin-bottom: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            font-size: 13px;
            max-width: 100%;
            box-sizing: border-box;
        }

        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 12px;
            flex-shrink: 0;
        }

        .user-name {
            font-size: 13px;
            color: #333;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100px;
        }

        .online-indicator {
            width: 8px;
            height: 8px;
            background: #4CAF50;
            border-radius: 50%;
            margin-left: auto;
        }

        .emoji-picker {
            position: relative;
        }

        .emoji-btn {
            background: #f8f9fa;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: all 0.3s ease;
        }

        .emoji-btn:hover {
            background: #e9ecef;
            transform: scale(1.05);
        }

        .emoji-panel {
            position: absolute;
            bottom: 60px;
            left: 0;
            background: var(--emoji-panel-bg);
            border-radius: 24px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            padding: 15px;
            display: none;
            z-index: 1000;
            width: 280px;
            max-height: 300px;
            overflow-y: auto;
            overflow-x: hidden;
            scrollbar-width: thin;
            scrollbar-color: rgba(102, 126, 234, 0.5) transparent;
            transition: background-color 0.3s ease;
        }

        .emoji-panel.show {
            display: block;
        }

        .emoji-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 8px;
            padding-right: 5px;
        }

        .emoji-item {
            background: none;
            border: none;
            font-size: 20px;
            padding: 8px;
            border-radius: 16px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .emoji-item:hover {
            background: #f1f3f4;
            transform: scale(1.1);
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
            border: 2px solid var(--border-color);
            border-radius: 16px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: var(--input-bg);
            color: var(--text-color);
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
            background: var(--input-bg);
            padding: 6px 12px;
            border-radius: 20px;
            font-family: monospace;
            font-weight: 600;
            color: var(--text-color);
            margin-bottom: 5px;
            font-size: 14px;
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px 30px;
            background: var(--card-color);
            transition: background-color 0.3s ease;
            height: calc(100% - 60px); /* Make room for input at bottom */
            -webkit-overflow-scrolling: touch;
            overscroll-behavior: contain;
            display: flex;
            flex-direction: column;
            overflow-anchor: auto;
            padding-bottom: 30px; /* Add extra padding at bottom */
            width: 100%;
        }

        .message {
            margin-bottom: 8px; // Further reduced
            display: flex;
            align-items: flex-start;
            gap: 8px;
            position: relative;
            transition: transform 0.3s ease;
            touch-action: pan-x;
            padding: 2px 3px;
            border-radius: 12px;
            width: 100%;
            box-sizing: border-box;
            justify-content: flex-start; // Default for other users' messages
        }

        .message.own {
            flex-direction: row-reverse;
            justify-content: flex-end;
            width: 100%;
            display: flex;
            text-align: right;
        }
        
        .message.selected {
            background-color: rgba(102, 126, 234, 0.1);
            border-radius: 12px;
            padding: 5px;
        }
        
        .reply-actions {
            position: absolute;
            right: 10px;
            top: -30px;
            background: var(--card-color);
            border-radius: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 5px 10px;
            display: none;
            z-index: 10;
            transition: background-color 0.3s ease;
        }
        
        .message.selected .reply-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .reply-btn {
            background: none;
            border: none;
            color: var(--accent-color);
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: color 0.3s ease;
        }
        
        .reply-indicator {
            background: var(--message-other-bg);
            border-left: 3px solid var(--accent-color);
            padding: 5px 10px;
            margin-bottom: 5px;
            border-radius: 0 8px 8px 0;
            font-size: 12px;
            color: var(--text-color);
            transition: background-color 0.3s ease, color 0.3s ease;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--avatar-bg);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 12px;
            flex-shrink: 0;
            transition: background 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .message-content {
            max-width: 85%;
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 1px;
            align-items: flex-start; // Default for other users' messages
        }

        .message.own .message-content {
            max-width: 85%;
            width: auto;
            margin-right: 0;
            align-items: flex-end;
            margin-left: auto; /* Push content to the right */
            text-align: right;
        }

        .message-bubble {
            background: var(--message-other-bg);
            padding: 6px 10px;
            border-radius: 24px;
            word-wrap: break-word;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: background-color 0.3s ease;
            display: inline-block;
            width: auto;
            max-width: 100%;
            align-self: flex-start;
            white-space: pre-wrap;
            line-height: 1.3;
            font-size: 14px;
            margin-bottom: 2px;
            text-align: left; /* Keep text left-aligned inside bubble */
        }

        .message.own .message-bubble {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            align-self: flex-end;
            margin-left: auto;
            float: right; /* Force bubble to the right */
        }

        .message-info {
            display: flex;
            align-items: center;
            gap: 5px;
            margin-bottom: 2px;
            font-size: 11px;
            color: #666;
            justify-content: flex-start; // Default for other users' messages
        }

        .message.own .message-info {
            justify-content: flex-end;
            width: 100%;
            text-align: right;
        }

        .message-time {
            font-size: 12px;
            color: #999;
            margin-top: 2px;
            display: flex;
            align-items: center;
            gap: 5px;
            align-self: flex-start;
        }
        
        .read-receipt {
            color: #667eea;
            font-size: 14px;
        }
        
        /* Theme options */
        :root {
            --bg-color: #f8f9fa;
            --card-color: white;
            --text-color: #333;
            --secondary-text: #666;
            --accent-color: #667eea;
            --accent-color-transparent: rgba(102, 126, 234, 0.2);
            --border-color: #eee;
            --message-other-bg: #f1f3f4;
            --message-own-bg: #667eea;
            --input-bg: #f8f9fa;
            --input-focus-bg: white;
            --card-bg: white;
            --sidebar-bg: #f8f9fa;
            --avatar-bg: linear-gradient(135deg, #667eea, #764ba2);
            --system-message-color: #666;
            --system-message-bg: rgba(0,0,0,0.05);
            --emoji-panel-bg: white;
            --theme-toggle-bg: white;
            --theme-toggle-color: #333;
        }
        
        body.dark-theme {
            --bg-color: #121212;
            --card-color: #1e1e1e;
            --card-bg: #1e1e1e;
            --text-color: #e0e0e0;
            --secondary-text: #aaa;
            --accent-color: #667eea;
            --accent-color-transparent: rgba(102, 126, 234, 0.2);
            --border-color: #333;
            --message-other-bg: #2a2a2a;
            --message-own-bg: #3a4a8c;
            --input-bg: #2a2a2a;
            --input-focus-bg: #333;
            --sidebar-bg: #1a1a1a;
            --avatar-bg: linear-gradient(135deg, #667eea, #764ba2);
            --system-message-color: #aaa;
            --system-message-bg: rgba(255,255,255,0.05);
            --emoji-panel-bg: #2a2a2a;
            --theme-toggle-bg: #2a2a2a;
            --theme-toggle-color: #e0e0e0;
        }
        
        body.dark-theme .chat-card,
        body.dark-theme .user-card,
        body.dark-theme .user-sidebar-header,
        body.dark-theme .user-item,
        body.dark-theme .emoji-panel,
        body.dark-theme .message-bubble,
        body.dark-theme .input-container {
            background-color: var(--card-bg);
            color: var(--text-color);
        }
        
        body.dark-theme .message-bubble {
            background-color: var(--message-bg);
        }
        
        body.dark-theme .message.own .message-bubble {
            background-color: var(--own-message-bg);
        }
        
        body.dark-theme .user-sidebar {
            background-color: var(--bg-color);
        }
        
        body.dark-theme .emoji-btn {
            background-color: #2a2a2a;
            color: var(--text-color);
        }
        
        body.dark-theme .emoji-btn:hover {
            background-color: #3a3a3a;
        }
        
        body.dark-theme input,
        body.dark-theme button {
            background-color: var(--card-bg);
            color: var(--text-color);
            border-color: var(--border-color);
        }
        
        .theme-toggle {
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--theme-toggle-bg);
            border: none;
            font-size: 24px;
            cursor: pointer;
            z-index: 1000;
            color: var(--theme-toggle-color);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.3s ease, color 0.3s ease, transform 0.3s ease;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .theme-toggle:hover {
            transform: scale(1.1);
            background: var(--accent-color);
            color: white;
        }
        
        body.dark-theme .theme-toggle {
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }

        .chat-input {
            background: var(--card-color);
            padding: 15px;
            border-top: 1px solid var(--border-color);
            border-radius: 0;
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 0;
            transition: background-color 0.3s ease, border-color 0.3s ease;
            position: relative;
            z-index: 10;
            width: 100%;
            height: 60px;
            box-sizing: border-box;
        }

        .chat-input input {
            flex: 1;
            border: 1px solid var(--border-color);
            background: var(--input-bg);
            border-radius: 20px;
            padding: 12px 20px;
            font-size: 14px;
            color: var(--text-color);
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
            display: block !important;
            width: 100% !important;
            min-height: 44px;
            outline: none;
            box-shadow: 0 0 0 1px rgba(0,0,0,0.05);
        }

        .chat-input input:focus {
            outline: none;
            background: var(--input-focus-bg);
            box-shadow: 0 0 0 2px var(--accent-color-transparent);
            border-color: var(--accent-color);
        }

        .send-btn {
            background: var(--accent-color);
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
            z-index: 10;
        }

        .send-btn:hover {
            transform: scale(1.05);
        }

        .system-message {
            text-align: center;
            color: var(--system-message-color);
            font-size: 13px;
            font-style: italic;
            margin: 8px 0;
            padding: 8px;
            background: var(--system-message-bg);
            border-radius: 12px;
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        /* Improved responsiveness for various screen sizes */
        @media (max-width: 1200px) {
            .chat-card {
                max-width: 800px;
            }
            
            .user-card {
                width: 220px;
            }
        }
        
        @media (max-width: 992px) {
            .chat-card {
                max-width: 800px;
            }
            /* Removed fixed min-height for chat-messages on medium screens */
            /* .chat-messages { min-height: 500px; } */
            .user-card {
                width: 200px;
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
            
            .chat-container {
                flex-direction: column;
                align-items: center;
                overflow: hidden;
                height: calc(100% - 20px);
            }
            
            .chat-card {
                height: calc(100vh - 40px);
                margin: 20px 10px 20px 10px;
                max-width: 100%;
                width: 100%;
                min-width: unset;
                margin-bottom: 10px;
            }
            
            .user-card {
                width: 100%;
                max-width: 100%;
                height: auto;
                margin: 0 10px 100px 10px;
            }
            
            .user-sidebar {
                height: 150px;
                border-radius: 0 0 24px 24px;
            }
            
            .user-list {
                display: flex;
                flex-direction: row;
                gap: 10px;
                overflow-x: auto;
                padding: 10px 15px;
            }
            
            .user-item {
                flex-shrink: 0;
                margin-bottom: 0;
            }
            
            .container {
                padding: 10px;
                max-width: 100%;
                height: 100%;
                overflow: hidden;
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
        /* Avatar selection styles */
        .avatar-selection {
            margin-bottom: 20px;
        }
        .avatar-options {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
            margin: 10px 0;
        }
        .avatar-option {
            font-size: 24px;
            cursor: pointer;
            padding: 8px;
            border-radius: 50%;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            margin: 0 auto;
            border: 2px solid transparent;
            background-color: #f8f9fa;
        }
        .avatar-option.selected {
            background-color: var(--accent-color-transparent);
            transform: scale(1.1);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-color: var(--accent-color);
        }
        .avatar-preview {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--accent-color);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin: 0 auto 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 2px solid var(--accent-color-transparent);
        }
        /* Hide online section on mobile */
        @media (max-width: 768px) {
            .user-card {
                display: none;
            }
            .user-count-display {
                display: none;
            }
        }

        .message-box-wrapper {
            width: 100%;
            max-width: 900px;
            margin: -20px auto 0;
            padding: 0 10px;
            z-index: 100;
            flex-shrink: 0;
        }

        /* Add CSS for scrollbar styling */
        .chat-messages::-webkit-scrollbar {
            width: 8px;
        }

        .chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background-color: rgba(0,0,0,0.1);
            border-radius: 20px;
        }

        .user-list::-webkit-scrollbar {
            width: 6px;
        }

        .user-list::-webkit-scrollbar-track {
            background: transparent;
        }

        .user-list::-webkit-scrollbar-thumb {
            background-color: rgba(0,0,0,0.1);
            border-radius: 20px;
        }

        /* Fix message box display on mobile */
        @media (max-width: 768px) {
            .message-box-wrapper {
                padding: 0 5px;
                margin-top: -10px;
                width: 100%;
                position: static;
                bottom: auto;
                left: auto;
                right: auto;
            }
            
            .chat-card {
                height: calc(100% - 60px);
                margin: 20px 10px 20px 10px;
                max-width: 100%;
                width: 100%;
                min-width: unset;
                margin-bottom: 10px;
            }
            
            .chat-input {
                padding: 10px;
                height: 60px;
            }
            
            .chat-input input {
                padding: 10px 15px;
                font-size: 14px;
            }
        }

        // Add missing CSS for user-info
        .user-info {
            display: flex;
            flex-direction: column;
            min-width: 0;
            flex: 1;
            overflow: hidden;
        }

        // Further improve message alignment for own messages
        .message.own {
            flex-direction: row-reverse;
            justify-content: flex-end;
            width: 100%;
            display: flex;
            text-align: right;
        }

        .message.own .message-content {
            max-width: 85%;
            width: auto;
            margin-right: 0;
            align-items: flex-end;
            margin-left: auto; /* Push content to the right */
            text-align: right;
        }

        // Fix the message bubble for own messages to ensure proper alignment
        .message.own .message-bubble {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            align-self: flex-end;
            margin-left: auto;
            float: right; /* Force bubble to the right */
        }

        // Fix message info alignment
        .message-info {
            display: flex;
            align-items: center;
            gap: 5px;
            margin-bottom: 2px;
            font-size: 11px;
            color: #666;
        }

        .message.own .message-info {
            justify-content: flex-end;
            width: 100%;
            text-align: right;
        }

        // Fix message time alignment
        .message-time {
            font-size: 12px;
            color: #999;
            margin-top: 2px;
            display: flex;
            align-items: center;
            gap: 5px;
            align-self: flex-start;
            align-self: flex-end;
            text-align: right;
            width: 100%;
        }

        .message.own .message-time {
            align-self: flex-end;
            justify-content: flex-end;
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
            <div class="form-group avatar-selection">
                <label>Select Avatar:</label>
                <div id="avatarPreview" class="avatar-preview"></div>
                <div class="avatar-options">
                    <span class="avatar-option">😀</span>
                    <span class="avatar-option">😃</span>
                    <span class="avatar-option">😄</span>
                    <span class="avatar-option">😁</span>
                    <span class="avatar-option">😆</span>
                    <span class="avatar-option">😅</span>
                    <span class="avatar-option">😂</span>
                    <span class="avatar-option">🤣</span>
                    <span class="avatar-option">😊</span>
                    <span class="avatar-option">😇</span>
                </div>
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
                <button class="btn" style="background: var(--input-bg); color: var(--text-color); transition: background-color 0.3s ease, color 0.3s ease;" onclick="goBack()">← Back</button>
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
                <button class="btn" style="background: var(--input-bg); color: var(--text-color); transition: background-color 0.3s ease, color 0.3s ease;" onclick="goBack()">← Back</button>
            </div>
            
            <div id="createErrorMessage"></div>
        </div>
    </div>

    <!-- Chat Room Screen -->
    <div class="container hidden" id="chatScreen">
        <div class="chat-container">
            <div class="card chat-card">
                <div class="chat-main">
                    <div class="chat-header">
                        <div class="brand">
                            <h1 style="font-size: 1.5rem; margin-bottom: 0;">ChitChat</h1>
                        </div>
                        <div class="room-id">Room ID: #<span id="currentRoomId"></span></div>
                        <div class="user-count-display" style="font-size: 11px; color: #666; margin-top: 3px; margin-bottom: 5px;">
                            <span id="userCount">1</span> user(s) online
                        </div>
                        <div class="chat-header-actions">
                            <button class="btn btn-danger" style="padding: 6px 12px; font-size: 12px;" onclick="leaveRoom()">Leave Room</button>
                        </div>
                    </div>
                
                    <div class="chat-messages" id="chatMessages">
                        <!-- Messages will be populated here -->
                    </div>
                    
                    <!-- Chat input moved inside chat-card -->
                    <div class="chat-input">
                        <div class="emoji-picker">
                            <button class="emoji-btn" onclick="toggleEmojiPicker()">
                                😊
                            </button>
                            <div class="emoji-panel" id="emojiPanel">
                                <div class="emoji-grid">
                                    <!-- Smileys & Emotion -->
                                    <button class="emoji-item" onclick="insertEmoji('😀')">😀</button>
                                    <button class="emoji-item" onclick="insertEmoji('😃')">😃</button>
                                    <button class="emoji-item" onclick="insertEmoji('😄')">😄</button>
                                    <button class="emoji-item" onclick="insertEmoji('😁')">😁</button>
                                    <button class="emoji-item" onclick="insertEmoji('😆')">😆</button>
                                    <button class="emoji-item" onclick="insertEmoji('😅')">😅</button>
                                    <button class="emoji-item" onclick="insertEmoji('😂')">😂</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤣')">🤣</button>
                                    <button class="emoji-item" onclick="insertEmoji('😊')">😊</button>
                                    <button class="emoji-item" onclick="insertEmoji('😇')">😇</button>
                                    <button class="emoji-item" onclick="insertEmoji('🙂')">🙂</button>
                                    <button class="emoji-item" onclick="insertEmoji('🙃')">🙃</button>
                                    <button class="emoji-item" onclick="insertEmoji('😉')">😉</button>
                                    <button class="emoji-item" onclick="insertEmoji('😌')">😌</button>
                                    <button class="emoji-item" onclick="insertEmoji('😍')">😍</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥰')">🥰</button>
                                    <button class="emoji-item" onclick="insertEmoji('😘')">😘</button>
                                    <button class="emoji-item" onclick="insertEmoji('😗')">😗</button>
                                    <button class="emoji-item" onclick="insertEmoji('😙')">😙</button>
                                    <button class="emoji-item" onclick="insertEmoji('😚')">😚</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥲')">🥲</button>
                                    <button class="emoji-item" onclick="insertEmoji('😋')">😋</button>
                                    <button class="emoji-item" onclick="insertEmoji('😛')">😛</button>
                                    <button class="emoji-item" onclick="insertEmoji('😜')">😜</button>
                                    <button class="emoji-item" onclick="insertEmoji('😝')">😝</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤪')">🤪</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤨')">🤨</button>
                                    <button class="emoji-item" onclick="insertEmoji('🧐')">🧐</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤓')">🤓</button>
                                    <button class="emoji-item" onclick="insertEmoji('😎')">😎</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥸')">🥸</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤩')">🤩</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥳')">🥳</button>
                                    <button class="emoji-item" onclick="insertEmoji('😏')">😏</button>
                                    <button class="emoji-item" onclick="insertEmoji('😒')">😒</button>
                                    <button class="emoji-item" onclick="insertEmoji('😞')">😞</button>
                                    <button class="emoji-item" onclick="insertEmoji('😔')">😔</button>
                                    <button class="emoji-item" onclick="insertEmoji('😟')">😟</button>
                                    <button class="emoji-item" onclick="insertEmoji('😕')">😕</button>
                                    <button class="emoji-item" onclick="insertEmoji('🙁')">🙁</button>
                                    <button class="emoji-item" onclick="insertEmoji('☹️')">☹️</button>
                                    <button class="emoji-item" onclick="insertEmoji('😣')">😣</button>
                                    <button class="emoji-item" onclick="insertEmoji('😖')">😖</button>
                                    <button class="emoji-item" onclick="insertEmoji('😫')">😫</button>
                                    <button class="emoji-item" onclick="insertEmoji('😩')">😩</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥺')">🥺</button>
                                    <button class="emoji-item" onclick="insertEmoji('😢')">😢</button>
                                    <button class="emoji-item" onclick="insertEmoji('😭')">😭</button>
                                    <button class="emoji-item" onclick="insertEmoji('😤')">😤</button>
                                    <button class="emoji-item" onclick="insertEmoji('😠')">😠</button>
                                    <button class="emoji-item" onclick="insertEmoji('😡')">😡</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤬')">🤬</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤯')">🤯</button>
                                    <button class="emoji-item" onclick="insertEmoji('😳')">😳</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥵')">🥵</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥶')">🥶</button>
                                    <button class="emoji-item" onclick="insertEmoji('😱')">😱</button>
                                    <button class="emoji-item" onclick="insertEmoji('😨')">😨</button>
                                    
                                    <!-- Gestures & People -->
                                    <button class="emoji-item" onclick="insertEmoji('👍')">👍</button>
                                    <button class="emoji-item" onclick="insertEmoji('👎')">👎</button>
                                    <button class="emoji-item" onclick="insertEmoji('👌')">👌</button>
                                    <button class="emoji-item" onclick="insertEmoji('✌️')">✌️</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤞')">🤞</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤟')">🤟</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤘')">🤘</button>
                                    <button class="emoji-item" onclick="insertEmoji('👋')">👋</button>
                                    <button class="emoji-item" onclick="insertEmoji('🙌')">🙌</button>
                                    <button class="emoji-item" onclick="insertEmoji('👏')">👏</button>
                                    <button class="emoji-item" onclick="insertEmoji('🙏')">🙏</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤝')">🤝</button>
                                    <button class="emoji-item" onclick="insertEmoji('👊')">👊</button>
                                    <button class="emoji-item" onclick="insertEmoji('✊')">✊</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤛')">🤛</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤜')">🤜</button>
                                    <button class="emoji-item" onclick="insertEmoji('👈')">👈</button>
                                    <button class="emoji-item" onclick="insertEmoji('👉')">👉</button>
                                    <button class="emoji-item" onclick="insertEmoji('👆')">👆</button>
                                    <button class="emoji-item" onclick="insertEmoji('👇')">👇</button>
                                    <button class="emoji-item" onclick="insertEmoji('🖐️')">🖐️</button>
                                    <button class="emoji-item" onclick="insertEmoji('🖖')">🖖</button>
                                    <button class="emoji-item" onclick="insertEmoji('👨')">👨</button>
                                    <button class="emoji-item" onclick="insertEmoji('👩')">👩</button>
                                    <button class="emoji-item" onclick="insertEmoji('🧑')">🧑</button>
                                    
                                    <!-- Animals & Nature -->
                                    <button class="emoji-item" onclick="insertEmoji('🐶')">🐶</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐱')">🐱</button>
                                    <button class="emoji-item" onclick="insertEmoji('🦊')">🦊</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐼')">🐼</button>
                                    <button class="emoji-item" onclick="insertEmoji('🦁')">🦁</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐮')">🐮</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐷')">🐷</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐸')">🐸</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐵')">🐵</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐔')">🐔</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐧')">🐧</button>
                                    <button class="emoji-item" onclick="insertEmoji('🦄')">🦄</button>
                                    <button class="emoji-item" onclick="insertEmoji('🦓')">🦓</button>
                                    <button class="emoji-item" onclick="insertEmoji('🦍')">🦍</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐢')">🐢</button>
                                    <button class="emoji-item" onclick="insertEmoji('🐙')">🐙</button>
                                    <button class="emoji-item" onclick="insertEmoji('🦋')">🦋</button>
                                    <button class="emoji-item" onclick="insertEmoji('🌸')">🌸</button>
                                    <button class="emoji-item" onclick="insertEmoji('🌹')">🌹</button>
                                    <button class="emoji-item" onclick="insertEmoji('🌺')">🌺</button>
                                    <button class="emoji-item" onclick="insertEmoji('🌻')">🌻</button>
                                    <button class="emoji-item" onclick="insertEmoji('🌼')">🌼</button>
                                    <button class="emoji-item" onclick="insertEmoji('🌷')">🌷</button>
                                    
                                    <!-- Food & Drink -->
                                    <button class="emoji-item" onclick="insertEmoji('🍕')">🍕</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍔')">🍔</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍟')">🍟</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍦')">🍦</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍩')">🍩</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍺')">🍺</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍷')">🍷</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍹')">🍹</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍰')">🍰</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍫')">🍫</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍬')">🍬</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍭')">🍭</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍪')">🍪</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍿')">🍿</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍣')">🍣</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍜')">🍜</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍝')">🍝</button>
                                    <button class="emoji-item" onclick="insertEmoji('🍱')">🍱</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥗')">🥗</button>
                                    <button class="emoji-item" onclick="insertEmoji('🥪')">🥪</button>
                                    
                                    <!-- Activities & Objects -->
                                    <button class="emoji-item" onclick="insertEmoji('⚽')">⚽</button>
                                    <button class="emoji-item" onclick="insertEmoji('🏀')">🏀</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎮')">🎮</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎯')">🎯</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎲')">🎲</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎭')">🎭</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎬')">🎬</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎤')">🎤</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎧')">🎧</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎸')">🎸</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎹')">🎹</button>
                                    <button class="emoji-item" onclick="insertEmoji('🎨')">🎨</button>
                                    <button class="emoji-item" onclick="insertEmoji('🚗')">🚗</button>
                                    <button class="emoji-item" onclick="insertEmoji('✈️')">✈️</button>
                                    <button class="emoji-item" onclick="insertEmoji('🚀')">🚀</button>
                                    <button class="emoji-item" onclick="insertEmoji('🏠')">🏠</button>
                                    <button class="emoji-item" onclick="insertEmoji('⌚')">⌚</button>
                                    <button class="emoji-item" onclick="insertEmoji('📱')">📱</button>
                                    <button class="emoji-item" onclick="insertEmoji('💻')">💻</button>
                                    <button class="emoji-item" onclick="insertEmoji('📷')">📷</button>
                                    
                                    <!-- Symbols -->
                                    <button class="emoji-item" onclick="insertEmoji('❤️')">❤️</button>
                                    <button class="emoji-item" onclick="insertEmoji('🧡')">🧡</button>
                                    <button class="emoji-item" onclick="insertEmoji('💛')">💛</button>
                                    <button class="emoji-item" onclick="insertEmoji('💚')">💚</button>
                                    <button class="emoji-item" onclick="insertEmoji('💙')">💙</button>
                                    <button class="emoji-item" onclick="insertEmoji('💜')">💜</button>
                                    <button class="emoji-item" onclick="insertEmoji('🖤')">🖤</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤍')">🤍</button>
                                    <button class="emoji-item" onclick="insertEmoji('🤎')">🤎</button>
                                    <button class="emoji-item" onclick="insertEmoji('💔')">💔</button>
                                    <button class="emoji-item" onclick="insertEmoji('💕')">💕</button>
                                    <button class="emoji-item" onclick="insertEmoji('💞')">💞</button>
                                    <button class="emoji-item" onclick="insertEmoji('💓')">💓</button>
                                    <button class="emoji-item" onclick="insertEmoji('💗')">💗</button>
                                    <button class="emoji-item" onclick="insertEmoji('💖')">💖</button>
                                    <button class="emoji-item" onclick="insertEmoji('💘')">💘</button>
                                    <button class="emoji-item" onclick="insertEmoji('💝')">💝</button>
                                    <button class="emoji-item" onclick="insertEmoji('💯')">💯</button>
                                    <button class="emoji-item" onclick="insertEmoji('💢')">💢</button>
                                    <button class="emoji-item" onclick="insertEmoji('💥')">💥</button>
                                    <button class="emoji-item" onclick="insertEmoji('✨')">✨</button>
                                    <button class="emoji-item" onclick="insertEmoji('⭐')">⭐</button>
                                    <button class="emoji-item" onclick="insertEmoji('🌟')">🌟</button>
                                    <button class="emoji-item" onclick="insertEmoji('💫')">💫</button>
                                    <button class="emoji-item" onclick="insertEmoji('🌈')">🌈</button>
                                </div>
                            </div>
                        </div>
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
            
            <div class="card user-card">
                <div class="user-sidebar">
                    <div class="user-sidebar-header">
                        <h3>Online Users (<span id="userCountSidebar">0</span>)</h3>
                    </div>
                    <div class="user-list" id="userList">
                        <!-- Users will be populated here -->
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Remove message-box-wrapper since input is now inside chat-card -->
    </div>

    <script>
        // App State
        let currentUser = '';
        let currentRoom = '';
        let currentPassword = '';
        let socket = null;
        let currentAvatar = '';
        
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
            // Avatar selection functionality
            document.querySelectorAll('.avatar-option').forEach(option => {
                option.addEventListener('click', function() {
                    document.querySelectorAll('.avatar-option').forEach(o => o.classList.remove('selected'));
                    option.classList.add('selected');
                    currentAvatar = option.textContent;
                    // Update avatar preview
                    const avatarPreview = document.getElementById('avatarPreview');
                    if (avatarPreview) {
                        avatarPreview.textContent = currentAvatar;
                    }
                });
            });
        }

        // Navigation functions
        function showCreateRoom() {
            const usernameInput = document.getElementById('username').value.trim();
            if (!usernameInput) {
                showError('errorMessage', 'Please enter a username');
                return;
            }
            const username = currentAvatar ? currentAvatar + ' ' + usernameInput : usernameInput;
            currentUser = username;
            document.getElementById('createUsername').value = username;
            switchScreen('welcomeScreen', 'createScreen');
            document.getElementById('background').className = 'background create';
        }

        function showJoinRoom() {
            const usernameInput = document.getElementById('username').value.trim();
            if (!usernameInput) {
                showError('errorMessage', 'Please enter a username');
                return;
            }
            const username = currentAvatar ? currentAvatar + ' ' + usernameInput : usernameInput;
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
                    // Check if this is a reply message
                    if (data.replyTo) {
                        addMessage(data.username, data.message, data.username === currentUser, data.replyTo);
                    } else {
                        addMessage(data.username, data.message, data.username === currentUser);
                    }
                    
                    // Hide typing indicator when message is received
                    if (data.username !== currentUser) {
                        hideTypingIndicator(data.username);
                    }
                } else {
                    addSystemMessage(data.message);
                }
            });

            // Listen for user count updates
            socket.on('user_count', function(data) {
                document.getElementById('userCount').textContent = data.count;
                document.getElementById('userCountSidebar').textContent = data.count;
            });

            // Listen for user list updates
            socket.on('user_list', function(data) {
                updateUserList(data.users);
            });
            
            // Listen for typing indicators
            socket.on('typing', function(data) {
                if (data.username !== currentUser) {
                    showTypingIndicator(data.username);
                    
                    // Auto-hide typing indicator after 3 seconds
                    setTimeout(() => {
                        hideTypingIndicator(data.username);
                    }, 3000);
                }
            });
            
            // Listen for stopped typing
            socket.on('stopped_typing', function(data) {
                if (data.username !== currentUser) {
                    hideTypingIndicator(data.username);
                }
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
            
            // Set up typing indicator for message input
            const messageInput = document.getElementById('messageInput');
            let typingTimeout = null;
            
            messageInput.addEventListener('input', function() {
                if (!socket) return;
                
                // Emit typing event
                socket.emit('typing', {
                    username: currentUser,
                    room: currentRoom
                });
                
                // Clear existing timeout
                if (typingTimeout) {
                    clearTimeout(typingTimeout);
                }
                
                // Set new timeout to emit stopped typing after 2 seconds of inactivity
                typingTimeout = setTimeout(() => {
                    socket.emit('stopped_typing', {
                        username: currentUser,
                        room: currentRoom
                    });
                }, 2000);
            });
        }
        
        function showTypingIndicator(username) {
            const sanitizedUsername = username.replace(/\s+/g, '-');
            const indicator = document.getElementById(`typing-${sanitizedUsername}`);
            if (indicator) {
                indicator.style.display = 'block';
            }
        }
        
        function hideTypingIndicator(username) {
            const sanitizedUsername = username.replace(/\s+/g, '-');
            const indicator = document.getElementById(`typing-${sanitizedUsername}`);
            if (indicator) {
                indicator.style.display = 'none';
            }
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !socket) return;
            
            // Prepare message data
            const messageData = {
                message: message,
                room: currentRoom,
                username: currentUser
            };
            
            // Add reply data if replying to a message
            if (replyingTo) {
                messageData.replyTo = replyingTo;
            }
            
            // Send message via socket
            socket.emit('send_message', messageData);
            
            // Clear input and reset reply
            input.value = '';
            cancelReply();
        }

        let replyingTo = null;
        let touchStartX = 0;
        let touchEndX = 0;
        let selectedMessage = null;
        
        function addMessage(username, message, isOwn = false, replyToData = null) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isOwn ? 'own' : ''}`;
            messageDiv.dataset.username = username;
            messageDiv.dataset.message = message;
            messageDiv.dataset.id = Date.now().toString() + Math.random().toString(36).substr(2, 5);
            
            // Add touch event listeners for swipe to reply
            messageDiv.addEventListener('touchstart', handleTouchStart);
            messageDiv.addEventListener('touchend', handleTouchEnd);
            messageDiv.addEventListener('touchmove', handleTouchMove);
            
            // Add mouse events for desktop users
            messageDiv.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                selectMessageForReply(messageDiv);
            });
            
            // Also add click event for mobile and desktop
            messageDiv.addEventListener('click', function(e) {
                // Only select if not already selected
                if (!messageDiv.classList.contains('selected')) {
                    selectMessageForReply(messageDiv);
                }
            });
            
            // Only add avatar for other users' messages, not own messages
            let avatarDiv;
            if (!isOwn) {
                avatarDiv = document.createElement('div');
                avatarDiv.className = 'message-avatar';
                
                // Extract first part if it's an emoji (space-separated)
                const parts = username.trim().split(' ');
                if (parts.length > 1 && /\p{Emoji}/u.test(parts[0])) {
                    avatarDiv.textContent = parts[0];
                    avatarDiv.style.background = 'var(--accent-color-transparent)';
                    avatarDiv.style.color = 'inherit';
                } else {
                    avatarDiv.textContent = username.charAt(0).toUpperCase();
                }
            }
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            // Add reply actions
            const replyActionsDiv = document.createElement('div');
            replyActionsDiv.className = 'reply-actions';
            
            const replyBtn = document.createElement('button');
            replyBtn.className = 'reply-btn';
            replyBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 14 4 9 9 4"></polyline><path d="M20 20v-7a4 4 0 0 0-4-4H4"></path></svg> Reply';
            replyBtn.addEventListener('click', function() {
                setReplyingTo(username, message);
                document.getElementById('messageInput').focus();
                unselectMessage();
            });
            
            replyActionsDiv.appendChild(replyBtn);
            messageDiv.appendChild(replyActionsDiv);
            
            // If this is a reply to another message, add the reply indicator
            if (replyToData) {
                const replyIndicator = document.createElement('div');
                replyIndicator.className = 'reply-indicator';
                replyIndicator.style.display = 'flex';
                replyIndicator.style.alignItems = 'center';
                replyIndicator.style.gap = '5px';
                
                // Add avatar for replied user
                const replyAvatar = document.createElement('span');
                const replyParts = replyToData.username.trim().split(' ');
                if (replyParts.length > 1 && /\p{Emoji}/u.test(replyParts[0])) {
                    replyAvatar.textContent = replyParts[0];
                } else {
                    replyAvatar.textContent = replyToData.username.charAt(0).toUpperCase();
                }
                replyAvatar.style.width = '18px';
                replyAvatar.style.height = '18px';
                replyAvatar.style.borderRadius = '50%';
                replyAvatar.style.background = 'var(--accent-color-transparent)';
                replyAvatar.style.display = 'flex';
                replyAvatar.style.alignItems = 'center';
                replyAvatar.style.justifyContent = 'center';
                replyAvatar.style.fontSize = '10px';
                
                replyIndicator.appendChild(replyAvatar);
                
                const replyText = document.createElement('span');
                replyText.textContent = `${replyToData.username}: ${replyToData.message.substring(0, 30)}${replyToData.message.length > 30 ? '...' : ''}`;
                replyIndicator.appendChild(replyText);
                
                contentDiv.appendChild(replyIndicator);
            }
            
            const infoDiv = document.createElement('div');
            infoDiv.className = 'message-info';
            infoDiv.innerHTML = `<strong style="color: ${isOwn ? 'var(--accent-color)' : 'var(--text-color)'}">${username}</strong>`;
            
            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';
            bubbleDiv.textContent = message;
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            
            // Add timestamp
            const timeSpan = document.createElement('span');
            timeSpan.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            timeDiv.appendChild(timeSpan);
            
            // Add read receipt for own messages
            if (isOwn) {
                const readReceipt = document.createElement('span');
                readReceipt.className = 'read-receipt';
                readReceipt.innerHTML = '✓'; // Single check for sent
                readReceipt.dataset.messageId = messageDiv.dataset.id;
                timeDiv.appendChild(readReceipt);
                
                // Simulate message being read after 2 seconds
                setTimeout(() => {
                    if (readReceipt) {
                        readReceipt.innerHTML = '✓✓'; // Double check for read
                    }
                }, 2000);
            }
            
            contentDiv.appendChild(infoDiv);
            contentDiv.appendChild(bubbleDiv);
            contentDiv.appendChild(timeDiv);
            
            // Only add avatar for others' messages
            if (!isOwn) {
                messageDiv.appendChild(avatarDiv);
            }
            messageDiv.appendChild(contentDiv);
            
            messagesContainer.appendChild(messageDiv);
            
            // Use setTimeout to ensure DOM has updated
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 0);
            
            // If this is a new message and not from the current user, play notification sound
            if (!isOwn) {
                playNotificationSound();
            }
        }
        
        // Notification sound
        function playNotificationSound() {
            // Create audio element for notification
            const audio = new Audio('data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAASAAAeMwAUFBQUFCIiIiIiIjAwMDAwMD4+Pj4+PkxMTExMTFpaWlpaWmhoaGhoaHZ2dnZ2doSEhISEhJKSkpKSkqCgoKCgoK6urq6urrKysrKysr6+vr6+vsbGxsbGxtLS0tLS0tra2tra2uLi4uLi4urq6urq6vLy8vLy8vr6+vr6+v///////////////8BZHQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//sQZAAP8AAAaQAAAAgAAA0gAAABAAABpAAAACAAADSAAAAETEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV');
            audio.play();
        }
        
        function handleTouchStart(e) {
            touchStartX = e.touches[0].clientX;
        }
        
        function handleTouchMove(e) {
            touchEndX = e.touches[0].clientX;
            const diffX = touchEndX - touchStartX;
            
            // If swiping right (for reply)
            if (diffX > 50) {
                // Don't actually move the message, just show we're selecting it
                if (!e.currentTarget.classList.contains('selected')) {
                    selectMessageForReply(e.currentTarget);
                }
            }
        }
        
        function handleTouchEnd(e) {
            const diffX = touchEndX - touchStartX;
            
            // Reset touch positions
            touchStartX = 0;
            touchEndX = 0;
        }
        
        function selectMessageForReply(messageElement) {
            // Unselect any previously selected message
            if (selectedMessage && selectedMessage !== messageElement) {
                unselectMessage();
            }
            
            // Select this message
            messageElement.classList.add('selected');
            selectedMessage = messageElement;
        }
        
        function unselectMessage() {
            if (selectedMessage) {
                selectedMessage.classList.remove('selected');
                selectedMessage = null;
            }
        }
        
        function setReplyingTo(username, message) {
            replyingTo = { username, message };
            
            // Show reply indicator in the input area
            // Create a floating reply indicator
            let replyIndicator = document.getElementById('replyIndicator');
            if (replyIndicator) {
                replyIndicator.remove();
            }
            
            replyIndicator = document.createElement('div');
            replyIndicator.id = 'replyIndicator';
            replyIndicator.className = 'reply-indicator floating-reply';
            replyIndicator.style.display = 'flex';
            replyIndicator.style.justifyContent = 'space-between';
            replyIndicator.style.alignItems = 'center';
            replyIndicator.style.padding = '8px 12px';
            replyIndicator.style.borderRadius = '12px';
            replyIndicator.style.backgroundColor = 'var(--card-color)';
            replyIndicator.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            replyIndicator.style.position = 'absolute';
            replyIndicator.style.top = '-40px';
            replyIndicator.style.left = '0';
            replyIndicator.style.right = '0';
            replyIndicator.style.width = 'auto';
            replyIndicator.style.marginLeft = '15px';
            replyIndicator.style.marginRight = '15px';
            replyIndicator.style.zIndex = '100';
            
            // Create a flex container for the left side (avatar + text)
            const leftSide = document.createElement('div');
            leftSide.style.display = 'flex';
            leftSide.style.alignItems = 'center';
            leftSide.style.gap = '8px';
            
            // Add avatar for replied user
            const replyAvatar = document.createElement('span');
            const replyParts = username.trim().split(' ');
            if (replyParts.length > 1 && /\p{Emoji}/u.test(replyParts[0])) {
                replyAvatar.textContent = replyParts[0];
            } else {
                replyAvatar.textContent = username.charAt(0).toUpperCase();
            }
            replyAvatar.style.width = '24px';
            replyAvatar.style.height = '24px';
            replyAvatar.style.borderRadius = '50%';
            replyAvatar.style.background = 'var(--accent-color-transparent)';
            replyAvatar.style.display = 'flex';
            replyAvatar.style.alignItems = 'center';
            replyAvatar.style.justifyContent = 'center';
            replyAvatar.style.fontSize = '12px';
            
            leftSide.appendChild(replyAvatar);
            
            // Add text
            const replyText = document.createElement('span');
            replyText.textContent = `Replying to ${username}: ${message.substring(0, 30)}${message.length > 30 ? '...' : ''}`;
            leftSide.appendChild(replyText);
            
            // Create close button
            const closeBtn = document.createElement('button');
            closeBtn.id = 'cancelReply';
            closeBtn.style.background = 'none';
            closeBtn.style.border = 'none';
            closeBtn.style.color = '#667eea';
            closeBtn.style.cursor = 'pointer';
            closeBtn.textContent = '✕';
            
            // Append both to the indicator
            replyIndicator.appendChild(leftSide);
            replyIndicator.appendChild(closeBtn);
            
            const inputContainer = document.querySelector('.chat-input');
            inputContainer.appendChild(replyIndicator);
            document.getElementById('cancelReply').addEventListener('click', cancelReply);
            
            // Make sure the input is visible when replying
            document.getElementById('messageInput').focus();
            
            // Scroll to the bottom of chat if needed
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function cancelReply() {
            replyingTo = null;
            const replyIndicator = document.getElementById('replyIndicator');
            if (replyIndicator) {
                replyIndicator.remove();
            }
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

        // Emoji picker functionality
        function toggleEmojiPicker() {
            const panel = document.getElementById('emojiPanel');
            panel.classList.toggle('show');
        }

        function insertEmoji(emoji) {
            const input = document.getElementById('messageInput');
            const cursorPos = input.selectionStart;
            const textBefore = input.value.substring(0, cursorPos);
            const textAfter = input.value.substring(cursorPos);
            input.value = textBefore + emoji + textAfter;
            input.focus();
            input.setSelectionRange(cursorPos + emoji.length, cursorPos + emoji.length);
            
            // Keep emoji panel open for multiple selections
            // Removed: document.getElementById('emojiPanel').classList.remove('show');
        }

        // Close emoji panel when clicking outside
        document.addEventListener('click', function(event) {
            const emojiPicker = document.querySelector('.emoji-picker');
            const emojiPanel = document.getElementById('emojiPanel');
            
            if (emojiPicker && !emojiPicker.contains(event.target)) {
                emojiPanel.classList.remove('show');
            }
        });

        // User list management
        function updateUserList(users) {
            const userList = document.getElementById('userList');
            const userCountSidebar = document.getElementById('userCountSidebar');
            
            userList.innerHTML = '';
            userCountSidebar.textContent = users.length;
            
            users.forEach(username => {
                const userItem = document.createElement('div');
                userItem.className = 'user-item';
                userItem.id = `user-${username.replace(/\s+/g, '-')}`;
                
                const userAvatar = document.createElement('div');
                userAvatar.className = 'user-avatar';
                
                // Extract first part if it's an emoji (space-separated)
                const parts = username.trim().split(' ');
                if (parts.length > 1 && /\p{Emoji}/u.test(parts[0])) {
                    userAvatar.textContent = parts[0];
                    userAvatar.style.background = 'var(--accent-color-transparent)';
                    userAvatar.style.color = 'inherit';
                } else {
                    userAvatar.textContent = username.charAt(0).toUpperCase();
                }
                
                const userInfo = document.createElement('div');
                userInfo.className = 'user-info';
                userInfo.style.display = 'flex';
                userInfo.style.flexDirection = 'column';
                
                const userName = document.createElement('div');
                userName.className = 'user-name';
                // If username has emoji, display only the text part
                if (parts.length > 1 && /\p{Emoji}/u.test(parts[0])) {
                    userName.textContent = parts.slice(1).join(' ');
                } else {
                    userName.textContent = username;
                }
                
                const typingIndicator = document.createElement('div');
                typingIndicator.className = 'typing-indicator';
                typingIndicator.id = `typing-${username.replace(/\s+/g, '-')}`;
                typingIndicator.style.fontSize = '12px';
                typingIndicator.style.color = '#667eea';
                typingIndicator.style.fontStyle = 'italic';
                typingIndicator.style.display = 'none';
                typingIndicator.textContent = 'typing...';
                
                userInfo.appendChild(userName);
                userInfo.appendChild(typingIndicator);
                
                const onlineIndicator = document.createElement('div');
                onlineIndicator.className = 'online-indicator';
                
                userItem.appendChild(userAvatar);
                userItem.appendChild(userInfo);
                userItem.appendChild(onlineIndicator);
                
                userList.appendChild(userItem);
            });
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
    
    # Track user session
    if room not in user_sessions:
        user_sessions[room] = {}
    user_sessions[room][request.sid] = username
    
    # Update user count
    rooms[room]["members"] = len(user_sessions[room])
    
    # Send a system message to the room
    send({"message": f"{username} has joined the room"}, to=room)
    
    # Broadcast updated user count and user list
    emit('user_count', {'count': rooms[room]["members"]}, to=room)
    emit('user_list', {'users': list(user_sessions[room].values())}, to=room)
    
    print(f"{username} joined room {room}")

@socketio.on("send_message")
def handle_send_message(data):
    room = data.get("room")
    username = data.get("username")
    message = data.get("message")
    reply_to = data.get("replyTo")
    
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
    
    # Add reply data if present
    if reply_to:
        content["replyTo"] = reply_to
    
    # Send the message to the room
    send(content, to=room)
    
    # Store the message
    rooms[room]["messages"].append(content)
    
    print(f"{username} said in {room}: {message}")

@socketio.on("typing")
def handle_typing(data):
    room = data.get("room")
    username = data.get("username")
    
    if not room or not username:
        return
    
    if room not in rooms:
        return
    
    # Broadcast typing indicator to the room
    emit('typing', {'username': username}, to=room, include_self=False)

@socketio.on("stopped_typing")
def handle_stopped_typing(data):
    room = data.get("room")
    username = data.get("username")
    
    if not room or not username:
        return
    
    if room not in rooms:
        return
    
    # Broadcast stopped typing to the room
    emit('stopped_typing', {'username': username}, to=room, include_self=False)

@socketio.on("disconnect")
def handle_disconnect():
    # Find which room the user was in
    disconnected_user = None
    disconnected_room = None
    
    for room_id in user_sessions:
        if request.sid in user_sessions[room_id]:
            disconnected_user = user_sessions[room_id][request.sid]
            disconnected_room = room_id
            del user_sessions[room_id][request.sid]
            break
    
    if disconnected_room and disconnected_room in rooms:
        # Update user count
        rooms[disconnected_room]["members"] = len(user_sessions[disconnected_room])
        
        # Send system message
        if disconnected_user:
            send({"message": f"{disconnected_user} has left the room"}, to=disconnected_room)
        
        # Broadcast updated user count and user list
        emit('user_count', {'count': rooms[disconnected_room]["members"]}, to=disconnected_room)
        emit('user_list', {'users': list(user_sessions[disconnected_room].values())}, to=disconnected_room)
    
    print(f"User {disconnected_user} disconnected from room {disconnected_room}")

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
