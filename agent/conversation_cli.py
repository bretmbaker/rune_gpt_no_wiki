import os
import json
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
import psutil
import signal
import sys
from pathlib import Path

# ANSI color codes for terminal output
COLORS = {
    "header": "\033[1;36m",  # Cyan
    "success": "\033[1;32m",  # Green
    "warning": "\033[1;33m",  # Yellow
    "error": "\033[1;31m",    # Red
    "info": "\033[1;34m",     # Blue
    "reset": "\033[0m"        # Reset
}

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the RuneGPT CLI header."""
    clear_screen()
    print(f"{COLORS['header']}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                           RUNEGPT CONVERSATION CLI                          ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{COLORS['reset']}")

def print_help():
    """Print available commands."""
    print("\nAvailable commands:")
    print(f"{COLORS['info']}- help{COLORS['reset']}: Show this help message")
    print(f"{COLORS['info']}- exit{COLORS['reset']}: Exit the conversation CLI")
    print(f"{COLORS['info']}- journal{COLORS['reset']}: View recent memories and experiences")
    print(f"{COLORS['info']}- goals{COLORS['reset']}: View current goals and progress")
    print(f"{COLORS['info']}- stats{COLORS['reset']}: View character statistics")
    print(f"{COLORS['info']}- memory{COLORS['reset']}: View detailed memory information")
    print(f"{COLORS['info']}- clear{COLORS['reset']}: Clear the screen")
    print(f"{COLORS['info']}- sessions{COLORS['reset']}: List all available sessions")
    print(f"{COLORS['info']}- switch <session_id>{COLORS['reset']}: Switch to a different session")
    print(f"{COLORS['info']}- active{COLORS['reset']}: Show active game sessions")
    print(f"{COLORS['info']}- connect <session_id>{COLORS['reset']}: Connect to an active game session")
    print("\nOr simply type your message to chat with the current session.")

def print_typing(text: str, delay: float = 0.03):
    """Print text with a typing effect."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

class ConversationCLI:
    """Command-line interface for interacting with RuneGPT."""
    
    def __init__(self):
        """Initialize the conversation CLI."""
        self.state_dir = Path("state")
        self.sessions = {}
        self.current_session = None
        
        # Create state directory if it doesn't exist
        self.state_dir.mkdir(exist_ok=True)
        
        # Load existing sessions
        self.load_sessions()
        
        # Check for active game sessions
        self.detect_active_sessions()
    
    def detect_active_sessions(self):
        """Detect active RuneGPT game sessions."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if this is a RuneGPT process
                if proc.info['name'] == 'python' and any('rune_adventure.py' in cmd for cmd in proc.info['cmdline'] if cmd):
                    # Extract session ID from command line
                    cmdline = proc.info['cmdline']
                    session_arg = next((arg for arg in cmdline if arg.startswith('--session=')), None)
                    
                    if session_arg:
                        session_id = session_arg.split('=')[1]
                        
                        # Check if this session exists in our sessions
                        if session_id in self.sessions:
                            # Mark as active game session
                            self.sessions[session_id]["is_active_game"] = True
                            self.sessions[session_id]["last_active"] = time.time()
                            self.sessions[session_id]["pid"] = proc.info['pid']
                            print(f"{COLORS['success']}Detected active game session: {session_id} (PID: {proc.info['pid']}){COLORS['reset']}")
                        else:
                            # Try to load this session
                            if self.load_session(session_id):
                                self.sessions[session_id]["is_active_game"] = True
                                self.sessions[session_id]["last_active"] = time.time()
                                self.sessions[session_id]["pid"] = proc.info['pid']
                                print(f"{COLORS['success']}Loaded and connected to active game session: {session_id} (PID: {proc.info['pid']}){COLORS['reset']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    
    def load_sessions(self):
        """Load existing sessions from the state directory."""
        if not self.state_dir.exists():
            return
        
        for session_dir in self.state_dir.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith("Player_"):
                self.load_session(session_dir.name)
    
    def load_session(self, session_id: str) -> bool:
        """Load a specific session by ID."""
        session_path = self.state_dir / session_id
        if not session_path.exists():
            return False
        
        try:
            # Load game state
            state_file = session_path / "game_state.json"
            if not state_file.exists():
                return False
                
            with open(state_file, 'r') as f:
                state = json.load(f)
                
            # Store session
            self.sessions[session_id] = {
                "state": state,
                "is_active_game": False,
                "last_active": time.time()
            }
            
            return True
        except Exception as e:
            print(f"{COLORS['error']}Error loading session {session_id}: {str(e)}{COLORS['reset']}")
            return False
    
    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session."""
        if session_id in self.sessions:
            self.current_session = session_id
            print(f"{COLORS['success']}Switched to session: {session_id}{COLORS['reset']}")
            
            # Show session info
            session = self.sessions[session_id]
            if session["is_active_game"]:
                print(f"{COLORS['info']}This is an active game session (PID: {session.get('pid', 'unknown')}){COLORS['reset']}")
            
            return True
        else:
            print(f"{COLORS['error']}Session not found: {session_id}{COLORS['reset']}")
            return False
    
    def connect_to_active_session(self, session_id: str) -> bool:
        """Connect to an active game session."""
        if session_id not in self.sessions:
            if not self.load_session(session_id):
                print(f"{COLORS['error']}Session not found: {session_id}{COLORS['reset']}")
                return False
        
        session = self.sessions[session_id]
        if not session["is_active_game"]:
            print(f"{COLORS['error']}Session is not an active game: {session_id}{COLORS['reset']}")
            return False
        
        self.current_session = session_id
        print(f"{COLORS['success']}Connected to active game session: {session_id}{COLORS['reset']}")
        return True
    
    def list_sessions(self):
        """List all available sessions."""
        if not self.sessions:
            print(f"{COLORS['warning']}No sessions found{COLORS['reset']}")
            return
        
        print("\nAvailable sessions:")
        for session_id, session in self.sessions.items():
            status = "ACTIVE" if session["is_active_game"] else "inactive"
            print(f"- {session_id} ({status})")
    
    def list_active_sessions(self):
        """List only active game sessions."""
        active_sessions = {sid: sess for sid, sess in self.sessions.items() if sess["is_active_game"]}
        
        if not active_sessions:
            print(f"{COLORS['warning']}No active game sessions found{COLORS['reset']}")
            return
        
        print("\nActive game sessions:")
        for session_id, session in active_sessions.items():
            print(f"- {session_id} (PID: {session.get('pid', 'unknown')})")
    
    def show_goals(self):
        """Show current goals and progress."""
        if not self.current_session:
            print(f"{COLORS['error']}No active session{COLORS['reset']}")
            return
        
        session = self.sessions[self.current_session]
        state = session["state"]
        
        print("\nCurrent Goals:")
        tutorial_progress = state["tutorial_progress"]
        print(f"Tutorial Island Progress: {tutorial_progress['completed_steps']}/{tutorial_progress['total_steps']} steps")
        
        if tutorial_progress["current_step"] < tutorial_progress["total_steps"]:
            current_step = state["tutorial_steps"][tutorial_progress["current_step"]]
            print(f"Current Task: {current_step['name']}")
            print(f"Location: {current_step['location']}")
            print(f"Description: {current_step['description']}")
        else:
            print("Tutorial Island completed! Ready for adventure!")
    
    def show_stats(self):
        """Show character statistics."""
        if not self.current_session:
            print(f"{COLORS['error']}No active session{COLORS['reset']}")
            return
        
        session = self.sessions[self.current_session]
        state = session["state"]
        player = state["player"]
        
        print("\nCharacter Statistics:")
        print(f"Name: {player['name']}")
        print(f"Total Level: {player['total_level']}")
        print(f"Combat Level: {player['combat_level']}")
        print(f"Quest Points: {player['quest_points']}")
        
        print("\nSkills:")
        for skill, level in player['skills'].items():
            print(f"{skill.capitalize()}: {level}")
    
    def show_memories(self):
        """Show recent memories and experiences."""
        if not self.current_session:
            print(f"{COLORS['error']}No active session{COLORS['reset']}")
            return
        
        session = self.sessions[self.current_session]
        state = session["state"]
        
        if "memory_log" not in state:
            print(f"{COLORS['warning']}No memories found{COLORS['reset']}")
            return
        
        print("\nRecent Memories:")
        for memory in state["memory_log"][-10:]:  # Show last 10 memories
            timestamp = datetime.fromtimestamp(memory['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] {memory['action']}: {memory['details']}")
            print(f"Location: {memory['location']}")
            print()
    
    def run(self):
        """Run the conversation CLI."""
        print_header()
        print_help()
        
        while True:
            try:
                if self.current_session:
                    prompt = f"\n{COLORS['info']}RuneGPT ({self.current_session}){COLORS['reset']}> "
                else:
                    prompt = f"\n{COLORS['info']}RuneGPT{COLORS['reset']}> "
                
                command = input(prompt).strip()
                
                if not command:
                    continue
                
                if command.lower() == 'exit':
                    break
                elif command.lower() == 'help':
                    print_help()
                elif command.lower() == 'clear':
                    clear_screen()
                    print_header()
                elif command.lower() == 'sessions':
                    self.list_sessions()
                elif command.lower() == 'active':
                    self.list_active_sessions()
                elif command.lower().startswith('switch '):
                    session_id = command[7:].strip()
                    self.switch_session(session_id)
                elif command.lower().startswith('connect '):
                    session_id = command[8:].strip()
                    self.connect_to_active_session(session_id)
                elif command.lower() == 'goals':
                    self.show_goals()
                elif command.lower() == 'stats':
                    self.show_stats()
                elif command.lower() == 'memory':
                    self.show_memories()
                elif command.lower() == 'journal':
                    self.show_memories()
                else:
                    if not self.current_session:
                        print(f"{COLORS['error']}No active session. Use 'sessions' to list available sessions and 'switch' to select one.{COLORS['reset']}")
                        continue
                    
                    # Process the message
                    session = self.sessions[self.current_session]
                    state = session["state"]
                    
                    # Generate a contextual response
                    response = self.generate_response(command, state)
                    print_typing(response)
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"{COLORS['error']}Error: {str(e)}{COLORS['reset']}")
    
    def generate_response(self, message: str, state: Dict[str, Any]) -> str:
        """Generate a contextual response based on the current game state."""
        # Simple response generation based on game state
        if "tutorial" in message.lower():
            tutorial_progress = state["tutorial_progress"]
            if tutorial_progress["current_step"] < tutorial_progress["total_steps"]:
                current_step = state["tutorial_steps"][tutorial_progress["current_step"]]
                return f"I'm currently working on the {current_step['name']} at {current_step['location']}. {current_step['description']}"
            else:
                return "I've completed the Tutorial Island! I'm ready to begin my adventure in Gielinor!"
        
        elif "location" in message.lower():
            return f"I'm currently at {state['location']}."
        
        elif "stats" in message.lower() or "level" in message.lower():
            skills = state["player"]["skills"]
            return f"My total level is {state['player']['total_level']} and combat level is {state['player']['combat_level']}. My highest skills are: " + \
                   ", ".join(f"{skill.capitalize()} ({level})" for skill, level in sorted(skills.items(), key=lambda x: x[1], reverse=True)[:5])
        
        elif "inventory" in message.lower():
            if not state["inventory"]:
                return "My inventory is empty."
            return f"I have {len(state['inventory'])} items in my inventory."
        
        else:
            return "I'm focused on completing my current tasks. How can I help you?"

def main():
    """Main entry point for the conversation CLI."""
    cli = ConversationCLI()
    cli.run()

if __name__ == "__main__":
    main() 