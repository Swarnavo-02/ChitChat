# ChitChat

ChitChat is a real-time chat application built with Flask and Socket.IO. It allows users to create and join chat rooms, send messages in real-time, and communicate with other users securely.

![ChitChat Screenshot](https://via.placeholder.com/800x400?text=ChitChat+Screenshot)

## Features

- **Real-time messaging** using WebSockets (Socket.IO)
- **Room creation** with custom room IDs
- **Password protection** for private rooms
- **User presence tracking** showing how many users are online
- **Responsive design** that works on desktop and mobile devices
- **System messages** for when users join or leave rooms
- **Beautiful UI** with smooth animations and gradients

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/chitchat.git
cd chitchat
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python goodchat_backend.py
```

4. Open your browser and navigate to:

```
http://localhost:5000
```

## Usage

### Creating a Room

1. Enter your username on the welcome screen
2. Click "Create Room"
3. Optionally set a custom room ID or leave blank for auto-generation
4. Optionally set a password for the room
5. Click "Create Room" to enter the chat

### Joining a Room

1. Enter your username on the welcome screen
2. Click "Join Room"
3. Enter the Room ID you want to join
4. Enter the room password (if required)
5. Click "Join Room" to enter the chat

### Chatting

- Type your message in the input field at the bottom of the screen
- Press Enter or click the send button to send your message
- All users in the room will receive your message in real-time
- Use the "Leave Room" button to exit the chat

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Real-time Communication**: Socket.IO
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **UI Design**: Modern CSS with gradients and subtle animations

## Project Structure

- `goodchat_backend.py`: Main application file containing both backend and frontend code
- `requirements.txt`: List of Python dependencies

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 