import os
import socket
import ssl
import threading
import time
import json
from datetime import datetime
from typing import List

from app.io_jsonl import append_jsonl
from app.analysis.signals import extract_signals
from app.analysis.rollups import update_profiles


class TwitchLiveClient:
    def __init__(self, channels: List[str]):
        token = os.getenv("TWITCH_OAUTH_TOKEN")
        nick = os.getenv("TWITCH_NICK")
        
        if not token or not nick:
            raise ValueError("TWITCH_OAUTH_TOKEN and TWITCH_NICK environment variables are required")
        
        self.nick = nick
        self.token = token
        self.channels = channels
        self.messages_file = "data/logs/messages.jsonl"
        self.running = False
        self.sock = None
    
    def connect_to_twitch(self):
        """Connect to Twitch IRC"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect to Twitch IRC
            self.sock = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            self.sock.connect(('irc.chat.twitch.tv', 6697))
            
            # Authenticate
            self.sock.send(f'PASS {self.token}\r\n'.encode('utf-8'))
            self.sock.send(f'NICK {self.nick}\r\n'.encode('utf-8'))
            
            # Join channels
            for channel in self.channels:
                self.sock.send(f'JOIN #{channel}\r\n'.encode('utf-8'))
                print(f"Joined channel: #{channel}")
            
            print(f"Connected to Twitch IRC as {self.nick}")
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def listen_for_messages(self):
        """Listen for incoming messages"""
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                lines = buffer.split('\r\n')
                buffer = lines.pop()
                
                for line in lines:
                    print(f"DEBUG: Received line: {line}")  # Debug output
                    if line.startswith('PING'):
                        # Respond to ping
                        self.sock.send(f'PONG {line[5:]}\r\n'.encode('utf-8'))
                        print("DEBUG: Sent PONG response")
                    elif 'PRIVMSG' in line:
                        # Parse chat message - look for any PRIVMSG, not just from tmi.twitch.tv
                        print(f"DEBUG: Found chat message: {line}")
                        self.parse_message(line)
                    elif 'JOIN' in line:
                        print(f"DEBUG: Join confirmation: {line}")
                    elif 'MODE' in line:
                        print(f"DEBUG: Mode info: {line}")
                        
            except Exception as e:
                print(f"Error reading messages: {e}")
                break
    
    def parse_message(self, line):
        """Parse IRC message and extract chat data"""
        print(f"DEBUG: parse_message called with: {line}")
        try:
            # Parse IRC format: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message
            parts = line.split(' PRIVMSG ')
            if len(parts) != 2:
                print(f"DEBUG: Failed to split PRIVMSG: {line}")
                return
            
            user_part = parts[0].split('!')[0][1:]  # Remove leading ':'
            channel_part = parts[1].split(' :')[0]
            message_text = parts[1].split(' :')[1] if ' :' in parts[1] else ''
            
            channel = channel_part[1:]  # Remove leading '#'
            
            print(f"DEBUG: Parsed - User: {user_part}, Channel: {channel}, Text: {message_text}")
            
            # Create message data
            message_data = {
                "ts": datetime.now().isoformat() + "Z",
                "channel": channel,
                "message_id": f"{channel}_{user_part}_{int(time.time())}",
                "user_name": user_part,
                "text": message_text,
                "mentions": self.extract_mentions(message_text),
                "urls": self.extract_urls(message_text),
                "emotes": [],
                "source": "twitch-irc"
            }
            
            print(f"DEBUG: About to save message: {message_data}")
            
            # Save message
            print(f"DEBUG: File path: {self.messages_file}")
            print(f"DEBUG: Message data: {message_data}")
            
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(self.messages_file), exist_ok=True)
            
            success = append_jsonl(self.messages_file, message_data, "message_id")
            print(f"DEBUG: Save result: {success}")
            
            # Also try direct file write as backup
            try:
                with open(self.messages_file, 'a', encoding='utf-8') as f:
                    f.write(f"{json.dumps(message_data)}\n")
                print("DEBUG: Direct file write successful")
            except Exception as e:
                print(f"DEBUG: Direct file write failed: {e}")
            
            # Extract signals and update profiles
            signals = extract_signals(message_data)
            update_profiles(message_data, signals)
            
            print(f"[{channel}] {user_part}: {message_text}")
            
        except Exception as e:
            print(f"Error parsing message: {e}")
            import traceback
            traceback.print_exc()
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text"""
        import re
        mention_pattern = r'@(\w+)'
        return re.findall(mention_pattern, text)
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        import re
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, text)
    
    def run(self, duration_seconds: int):
        """Run the bot for a specified duration"""
        if not self.connect_to_twitch():
            return
        
        self.running = True
        
        # Start listening in a separate thread
        listen_thread = threading.Thread(target=self.listen_for_messages)
        listen_thread.daemon = True
        listen_thread.start()
        
        print(f"Monitoring channels: {self.channels}")
        print("Bot is ready and listening for messages...")
        
        # Run for specified duration
        time.sleep(duration_seconds)
        self.running = False
        
        if self.sock:
            self.sock.close()
        print("Bot stopped.")