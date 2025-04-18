import os
import time
import datetime
import random
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

@dataclass
class NarrativeEntry:
    """Represents a single narrative entry in the agent's story"""
    timestamp: float
    date: str
    phase: str  # decision, movement, action, knowledge, dialogue, reasoning, emotion
    content: str
    location: Optional[str] = None
    emotion: Optional[str] = None
    emotion_intensity: Optional[float] = None
    items_involved: Optional[List[str]] = None
    skills_involved: Optional[List[str]] = None
    xp_gained: Optional[int] = None
    level_up: Optional[Dict[str, int]] = None
    quest_progress: Optional[Dict[str, Any]] = None
    goal_progress: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None

class NarrativeLogger:
    """
    Handles the narrative logging of RuneGPT's adventures.
    Creates immersive, story-like logs of the agent's journey.
    """
    def __init__(self, log_dir: str = "journal_logs", enabled: bool = True, 
                 verbosity: int = 2, include_timestamps: bool = True):
        """
        Initialize the narrative logger.
        
        Args:
            log_dir: Directory to store log files
            enabled: Whether narrative logging is enabled
            verbosity: Level of detail (0=minimal, 1=normal, 2=detailed, 3=verbose)
            include_timestamps: Whether to include timestamps in logs
        """
        self.log_dir = log_dir
        self.enabled = enabled
        self.verbosity = verbosity
        self.include_timestamps = include_timestamps
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize session log
        self.session_log = []
        self.session_start_time = time.time()
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Emotion tracking
        self.current_emotions = {
            "excitement": 0.5,
            "frustration": 0.3,
            "pride": 0.4,
            "curiosity": 0.7,
            "determination": 0.6,
            "caution": 0.5
        }
        
        # Personality influence on narrative style
        self.personality = {
            "curiosity": 0.8,
            "enthusiasm": 0.7,
            "humor": 0.5,
            "friendliness": 0.9,
            "determination": 0.8
        }
        
        # Load personality from file if it exists
        self._load_personality()
        
        # Narrative style variations
        self.narrative_styles = {
            "decision": [
                "I've decided to {content}",
                "After considering my options, I think I should {content}",
                "Based on my current situation, the best course of action is to {content}",
                "I'm going to {content} now",
                "It makes sense to {content} at this point"
            ],
            "movement": [
                "Heading {content}",
                "Moving {content}",
                "Walking {content}",
                "Making my way {content}",
                "Journeying {content}"
            ],
            "action": [
                "Now {content}",
                "I'm {content}",
                "Starting to {content}",
                "Attempting to {content}",
                "Working on {content}"
            ],
            "knowledge": [
                "Checking the wiki about {content}",
                "Looking up information on {content}",
                "Researching {content}",
                "Reading up on {content}",
                "Learning about {content}"
            ],
            "dialogue": [
                "Talking to {content}",
                "Having a conversation with {content}",
                "Discussing {content}",
                "Asking {content} about their needs",
                "Engaging in dialogue with {content}"
            ],
            "reasoning": [
                "I'm {content} because it's the logical next step",
                "This approach makes sense: {content}",
                "I need to {content} to progress efficiently",
                "The best strategy here is to {content}",
                "I should {content} to optimize my progress"
            ],
            "emotion": [
                "I feel {content}",
                "This is {content}",
                "I'm feeling quite {content}",
                "This situation is {content}",
                "I'm experiencing a sense of {content}"
            ]
        }
        
        # Emotion descriptors
        self.emotion_descriptors = {
            "excitement": ["excited", "thrilled", "energized", "enthusiastic", "eager"],
            "frustration": ["frustrated", "annoyed", "irritated", "disappointed", "bothered"],
            "pride": ["proud", "accomplished", "satisfied", "confident", "pleased"],
            "curiosity": ["curious", "intrigued", "interested", "fascinated", "inquisitive"],
            "determination": ["determined", "focused", "resolute", "committed", "steadfast"],
            "caution": ["cautious", "careful", "wary", "vigilant", "mindful"],
            "joy": ["happy", "joyful", "delighted", "cheerful", "content"],
            "surprise": ["surprised", "amazed", "astonished", "startled", "stunned"],
            "sadness": ["sad", "down", "disheartened", "disappointed", "discouraged"],
            "fear": ["afraid", "scared", "nervous", "anxious", "worried"]
        }
        
        # Start a new session log
        self._start_new_session()
    
    def _load_personality(self):
        """Load personality traits from file if it exists"""
        personality_file = os.path.join(self.log_dir, "personality.json")
        if os.path.exists(personality_file):
            try:
                with open(personality_file, "r") as f:
                    self.personality = json.load(f)
            except Exception as e:
                print(f"Error loading personality: {e}")
    
    def _save_personality(self):
        """Save current personality traits to file"""
        personality_file = os.path.join(self.log_dir, "personality.json")
        try:
            with open(personality_file, "w") as f:
                json.dump(self.personality, f, indent=2)
        except Exception as e:
            print(f"Error saving personality: {e}")
    
    def _start_new_session(self):
        """Start a new narrative session"""
        self.session_log = []
        self.session_start_time = time.time()
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Log session start
        self.log(
            phase="emotion",
            content="beginning a new adventure in Gielinor",
            emotion="excitement",
            emotion_intensity=0.8
        )
    
    def _format_timestamp(self) -> str:
        """Format current timestamp for log entries"""
        if not self.include_timestamps:
            return ""
        
        current_time = datetime.datetime.now()
        return f"[{current_time.strftime('%H:%M:%S')}] "
    
    def _get_narrative_style(self, phase: str, content: str) -> str:
        """Get a narrative style for the given phase and content"""
        if phase not in self.narrative_styles:
            return content
        
        # Select a random style template for this phase
        style_template = random.choice(self.narrative_styles[phase])
        
        # Format the content into the template
        return style_template.format(content=content)
    
    def _get_emotion_descriptor(self, emotion: str, intensity: float) -> str:
        """Get an emotion descriptor based on the emotion and intensity"""
        if emotion not in self.emotion_descriptors:
            return emotion
        
        # Select a descriptor based on intensity
        descriptors = self.emotion_descriptors[emotion]
        index = min(int(intensity * len(descriptors)), len(descriptors) - 1)
        return descriptors[index]
    
    def _update_emotions(self, emotion: str, intensity: float):
        """Update the current emotional state"""
        if emotion in self.current_emotions:
            # Gradually adjust the emotion
            self.current_emotions[emotion] = (self.current_emotions[emotion] * 0.7 + intensity * 0.3)
            
            # Ensure it stays within bounds
            self.current_emotions[emotion] = max(0.0, min(1.0, self.current_emotions[emotion]))
    
    def _get_dominant_emotion(self) -> tuple:
        """Get the currently dominant emotion and its intensity"""
        if not self.current_emotions:
            return ("neutral", 0.5)
        
        dominant_emotion = max(self.current_emotions.items(), key=lambda x: x[1])
        return dominant_emotion
    
    def _format_narrative_entry(self, entry: NarrativeEntry) -> str:
        """Format a narrative entry for display"""
        # Get the narrative style
        narrative_text = self._get_narrative_style(entry.phase, entry.content)
        
        # Add emotion if present
        if entry.emotion and entry.emotion_intensity:
            emotion_desc = self._get_emotion_descriptor(entry.emotion, entry.emotion_intensity)
            narrative_text += f" I'm feeling {emotion_desc}."
        
        # Add location if present
        if entry.location:
            narrative_text += f" (Location: {entry.location})"
        
        # Add items involved if present
        if entry.items_involved and len(entry.items_involved) > 0:
            items_text = ", ".join(entry.items_involved)
            narrative_text += f" Using: {items_text}."
        
        # Add skills involved if present
        if entry.skills_involved and len(entry.skills_involved) > 0:
            skills_text = ", ".join(entry.skills_involved)
            narrative_text += f" Skills: {skills_text}."
        
        # Add XP gained if present
        if entry.xp_gained:
            narrative_text += f" Gained {entry.xp_gained} XP."
        
        # Add level up if present
        if entry.level_up:
            for skill, level in entry.level_up.items():
                narrative_text += f" {skill.capitalize()} level up to {level}!"
        
        # Add quest progress if present
        if entry.quest_progress:
            quest_name = entry.quest_progress.get("name", "Unknown Quest")
            progress = entry.quest_progress.get("progress", 0)
            narrative_text += f" Quest progress: {quest_name} ({progress}% complete)."
        
        # Add goal progress if present
        if entry.goal_progress:
            for goal, progress in entry.goal_progress.items():
                narrative_text += f" Goal progress: {goal} ({progress}% complete)."
        
        return narrative_text
    
    def log(self, phase: str, content: str, location: Optional[str] = None,
            emotion: Optional[str] = None, emotion_intensity: Optional[float] = None,
            items_involved: Optional[List[str]] = None, skills_involved: Optional[List[str]] = None,
            xp_gained: Optional[int] = None, level_up: Optional[Dict[str, int]] = None,
            quest_progress: Optional[Dict[str, Any]] = None, goal_progress: Optional[Dict[str, float]] = None,
            metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a narrative entry.
        
        Args:
            phase: The phase of the narrative (decision, movement, action, etc.)
            content: The content of the narrative entry
            location: The location where the action took place
            emotion: The emotion felt during the action
            emotion_intensity: The intensity of the emotion (0.0 to 1.0)
            items_involved: List of items involved in the action
            skills_involved: List of skills involved in the action
            xp_gained: Amount of XP gained
            level_up: Dictionary of skills that leveled up
            quest_progress: Dictionary of quest progress
            goal_progress: Dictionary of goal progress
            metadata: Additional metadata for the entry
            
        Returns:
            The formatted narrative text
        """
        if not self.enabled:
            return ""
        
        # Create timestamp
        timestamp = time.time()
        date = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        # Update emotions if provided
        if emotion and emotion_intensity is not None:
            self._update_emotions(emotion, emotion_intensity)
        else:
            # Use dominant emotion if none provided
            emotion, emotion_intensity = self._get_dominant_emotion()
        
        # Create narrative entry
        entry = NarrativeEntry(
            timestamp=timestamp,
            date=date,
            phase=phase,
            content=content,
            location=location,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            items_involved=items_involved,
            skills_involved=skills_involved,
            xp_gained=xp_gained,
            level_up=level_up,
            quest_progress=quest_progress,
            goal_progress=goal_progress,
            metadata=metadata
        )
        
        # Add to session log
        self.session_log.append(asdict(entry))
        
        # Format the narrative text
        narrative_text = self._format_narrative_entry(entry)
        
        # Add timestamp if enabled
        if self.include_timestamps:
            narrative_text = self._format_timestamp() + narrative_text
        
        # Print the narrative text
        print(narrative_text)
        
        return narrative_text
    
    def log_decision(self, content: str, location: Optional[str] = None,
                    emotion: Optional[str] = None, emotion_intensity: Optional[float] = None,
                    items_involved: Optional[List[str]] = None, skills_involved: Optional[List[str]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a decision phase entry"""
        return self.log(
            phase="decision",
            content=content,
            location=location,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            items_involved=items_involved,
            skills_involved=skills_involved,
            metadata=metadata
        )
    
    def log_movement(self, content: str, location: Optional[str] = None,
                    emotion: Optional[str] = None, emotion_intensity: Optional[float] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a movement phase entry"""
        return self.log(
            phase="movement",
            content=content,
            location=location,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            metadata=metadata
        )
    
    def log_action(self, content: str, location: Optional[str] = None,
                  emotion: Optional[str] = None, emotion_intensity: Optional[float] = None,
                  items_involved: Optional[List[str]] = None, skills_involved: Optional[List[str]] = None,
                  xp_gained: Optional[int] = None, level_up: Optional[Dict[str, int]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log an action phase entry"""
        return self.log(
            phase="action",
            content=content,
            location=location,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            items_involved=items_involved,
            skills_involved=skills_involved,
            xp_gained=xp_gained,
            level_up=level_up,
            metadata=metadata
        )
    
    def log_knowledge(self, content: str, location: Optional[str] = None,
                     emotion: Optional[str] = None, emotion_intensity: Optional[float] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a knowledge phase entry"""
        return self.log(
            phase="knowledge",
            content=content,
            location=location,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            metadata=metadata
        )
    
    def log_dialogue(self, content: str, location: Optional[str] = None,
                    emotion: Optional[str] = None, emotion_intensity: Optional[float] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a dialogue phase entry"""
        return self.log(
            phase="dialogue",
            content=content,
            location=location,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            metadata=metadata
        )
    
    def log_reasoning(self, content: str, location: Optional[str] = None,
                     emotion: Optional[str] = None, emotion_intensity: Optional[float] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a reasoning phase entry"""
        return self.log(
            phase="reasoning",
            content=content,
            location=location,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            metadata=metadata
        )
    
    def log_emotion(self, content: str, location: Optional[str] = None,
                   emotion: Optional[str] = None, emotion_intensity: Optional[float] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log an emotion phase entry"""
        return self.log(
            phase="emotion",
            content=content,
            location=location,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            metadata=metadata
        )
    
    def save_session(self) -> str:
        """Save the current session log to a file"""
        if not self.session_log:
            return "No session log to save."
        
        # Create filename with session ID
        filename = f"session_{self.session_id}.md"
        filepath = os.path.join(self.log_dir, filename)
        
        try:
            with open(filepath, "w") as f:
                # Write header
                f.write(f"# RuneGPT Adventure Log - {self.session_id}\n\n")
                f.write(f"Session started: {datetime.datetime.fromtimestamp(self.session_start_time).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write entries
                for entry in self.session_log:
                    # Format the entry
                    phase = entry["phase"].capitalize()
                    content = entry["content"]
                    timestamp = datetime.datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S")
                    
                    # Write the entry
                    f.write(f"## {timestamp} - {phase}\n\n")
                    f.write(f"{content}\n\n")
                    
                    # Add details if present
                    if entry["location"]:
                        f.write(f"**Location:** {entry['location']}\n\n")
                    
                    if entry["emotion"] and entry["emotion_intensity"]:
                        emotion_desc = self._get_emotion_descriptor(entry["emotion"], entry["emotion_intensity"])
                        f.write(f"**Emotion:** {emotion_desc} ({entry['emotion_intensity']:.2f})\n\n")
                    
                    if entry["items_involved"] and len(entry["items_involved"]) > 0:
                        items_text = ", ".join(entry["items_involved"])
                        f.write(f"**Items:** {items_text}\n\n")
                    
                    if entry["skills_involved"] and len(entry["skills_involved"]) > 0:
                        skills_text = ", ".join(entry["skills_involved"])
                        f.write(f"**Skills:** {skills_text}\n\n")
                    
                    if entry["xp_gained"]:
                        f.write(f"**XP Gained:** {entry['xp_gained']}\n\n")
                    
                    if entry["level_up"]:
                        f.write("**Level Ups:**\n")
                        for skill, level in entry["level_up"].items():
                            f.write(f"- {skill.capitalize()}: {level}\n")
                        f.write("\n")
                    
                    if entry["quest_progress"]:
                        quest_name = entry["quest_progress"].get("name", "Unknown Quest")
                        progress = entry["quest_progress"].get("progress", 0)
                        f.write(f"**Quest Progress:** {quest_name} ({progress}% complete)\n\n")
                    
                    if entry["goal_progress"]:
                        f.write("**Goal Progress:**\n")
                        for goal, progress in entry["goal_progress"].items():
                            f.write(f"- {goal}: {progress}% complete\n")
                        f.write("\n")
                    
                    # Add separator
                    f.write("---\n\n")
            
            return f"Session log saved to {filepath}"
        except Exception as e:
            return f"Error saving session log: {e}"
    
    def end_session(self) -> str:
        """End the current session and save the log"""
        # Log session end
        self.log(
            phase="emotion",
            content="concluding this session of my adventure",
            emotion="reflection",
            emotion_intensity=0.6
        )
        
        # Save the session
        return self.save_session()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable narrative logging"""
        self.enabled = enabled
    
    def set_verbosity(self, verbosity: int):
        """Set the verbosity level"""
        self.verbosity = max(0, min(3, verbosity))
    
    def set_include_timestamps(self, include_timestamps: bool):
        """Set whether to include timestamps in logs"""
        self.include_timestamps = include_timestamps
    
    def update_personality(self, trait: str, value: float):
        """Update a personality trait"""
        if trait in self.personality:
            self.personality[trait] = max(0.0, min(1.0, value))
            self._save_personality()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session"""
        if not self.session_log:
            return {"message": "No session log available."}
        
        # Count entries by phase
        phase_counts = {}
        for entry in self.session_log:
            phase = entry["phase"]
            if phase not in phase_counts:
                phase_counts[phase] = 0
            phase_counts[phase] += 1
        
        # Count level ups
        level_ups = {}
        for entry in self.session_log:
            if entry["level_up"]:
                for skill, level in entry["level_up"].items():
                    if skill not in level_ups:
                        level_ups[skill] = 0
                    level_ups[skill] += 1
        
        # Calculate session duration
        duration = time.time() - self.session_start_time
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Create summary
        summary = {
            "session_id": self.session_id,
            "start_time": datetime.datetime.fromtimestamp(self.session_start_time).strftime("%Y-%m-%d %H:%M:%S"),
            "duration": f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
            "entry_count": len(self.session_log),
            "phase_counts": phase_counts,
            "level_ups": level_ups,
            "dominant_emotion": self._get_dominant_emotion()[0]
        }
        
        return summary

    def _apply_personality_style(self, text: str, personality_traits: PersonalityTraits) -> str:
        """
        Apply personality traits to narrative style.
        
        Args:
            text: Original narrative text
            personality_traits: Current personality traits
            
        Returns:
            Styled narrative text
        """
        # Apply tone based on personality
        if personality_traits.risk_tolerance > 0.7:
            text = self._add_excitement(text)
        elif personality_traits.risk_tolerance < 0.3:
            text = self._add_caution(text)
        
        # Apply social style
        if personality_traits.social_preference > 0.7:
            text = self._add_social_elements(text)
        elif personality_traits.social_preference < 0.3:
            text = self._add_solitary_elements(text)
        
        # Apply efficiency focus
        if personality_traits.efficiency_focus > 0.7:
            text = self._add_efficiency_details(text)
        elif personality_traits.efficiency_focus < 0.3:
            text = self._add_enjoyment_details(text)
        
        # Apply exploration style
        if personality_traits.exploration_preference > 0.7:
            text = self._add_discovery_elements(text)
        elif personality_traits.exploration_preference < 0.3:
            text = self._add_familiarity_elements(text)
        
        return text

    def _add_excitement(self, text: str) -> str:
        """Add excitement to narrative."""
        excitement_words = ["thrilling", "exciting", "daring", "bold", "adventurous"]
        return self._enhance_text(text, excitement_words)

    def _add_caution(self, text: str) -> str:
        """Add caution to narrative."""
        caution_words = ["careful", "cautious", "mindful", "prudent", "wary"]
        return self._enhance_text(text, caution_words)

    def _add_social_elements(self, text: str) -> str:
        """Add social elements to narrative."""
        social_elements = [
            "among fellow adventurers",
            "with companions",
            "in the company of others",
            "sharing the experience",
            "in a bustling area"
        ]
        return self._add_random_element(text, social_elements)

    def _add_solitary_elements(self, text: str) -> str:
        """Add solitary elements to narrative."""
        solitary_elements = [
            "alone in the wilderness",
            "in solitude",
            "away from others",
            "in a quiet corner",
            "in peaceful isolation"
        ]
        return self._add_random_element(text, solitary_elements)

    def _add_efficiency_details(self, text: str) -> str:
        """Add efficiency-focused details."""
        efficiency_details = [
            "methodically",
            "with precision",
            "efficiently",
            "systematically",
            "with optimal strategy"
        ]
        return self._add_random_element(text, efficiency_details)

    def _add_enjoyment_details(self, text: str) -> str:
        """Add enjoyment-focused details."""
        enjoyment_details = [
            "with joy",
            "taking time to appreciate",
            "enjoying the moment",
            "savoring the experience",
            "with a sense of wonder"
        ]
        return self._add_random_element(text, enjoyment_details)

    def _add_discovery_elements(self, text: str) -> str:
        """Add exploration and discovery elements."""
        discovery_elements = [
            "discovering new paths",
            "exploring uncharted territory",
            "finding hidden secrets",
            "uncovering mysteries",
            "venturing into the unknown"
        ]
        return self._add_random_element(text, discovery_elements)

    def _add_familiarity_elements(self, text: str) -> str:
        """Add familiarity and routine elements."""
        familiarity_elements = [
            "in familiar surroundings",
            "following established patterns",
            "sticking to known paths",
            "in well-trodden areas",
            "following routine"
        ]
        return self._add_random_element(text, familiarity_elements)

    def _enhance_text(self, text: str, word_list: List[str]) -> str:
        """Enhance text with words from the given list."""
        if random.random() < 0.3:  # 30% chance to enhance
            word = random.choice(word_list)
            if text.endswith("."):
                text = text[:-1] + f", {word}."
            else:
                text += f" {word}."
        return text

    def _add_random_element(self, text: str, elements: List[str]) -> str:
        """Add a random element from the list to the text."""
        if random.random() < 0.3:  # 30% chance to add element
            element = random.choice(elements)
            if text.endswith("."):
                text = text[:-1] + f", {element}."
            else:
                text += f" {element}."
        return text 