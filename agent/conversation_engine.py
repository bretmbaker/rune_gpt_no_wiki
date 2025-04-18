import json
import time
from datetime import datetime
import random
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from agent.memory import Memory
from agent.skills import Skills
from agent.inventory import Inventory
from agent.decision_maker import DecisionMaker
from agent.memory_types import MemoryEntry

class ConversationEngine:
    """
    Handles natural language conversation between the user and RuneGPT.
    Manages memory logging, goal tracking, and personality-driven responses.
    """
    def __init__(self, memory: MemoryEntry, skills: Skills, inventory: Inventory, decision_maker: DecisionMaker):
        self.memory = memory
        self.skills = skills
        self.inventory = inventory
        self.decision_maker = decision_maker
        
        # Personality traits
        self.personality = self._load_personality()
        
        # Initialize memory log
        self.memory_log = self._load_memory_log()
        
        # Initialize goals
        self.goals = self._load_goals()
        
        # Track conversation context
        self.conversation_context = {
            "last_topic": None,
            "last_question": None,
            "last_response": None,
            "user_name": "friend"  # Default name
        }
        
        # Track session stats
        self.current_session = {
            "start_time": time.time(),
            "actions": [],
            "discoveries": [],
            "deaths": 0,
            "goals_completed": []
        }
    
    def _load_personality(self):
        """Load personality traits from file if it exists"""
        if os.path.exists("personality_config.json"):
            try:
                with open("personality_config.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading personality config: {e}")
    
    def _save_personality(self):
        """Save current personality traits to file"""
        try:
            with open("personality_config.json", "w") as f:
                json.dump(self.personality, f, indent=2)
        except Exception as e:
            print(f"Error saving personality config: {e}")
    
    def _load_memory_log(self):
        """Load memory log from file if it exists"""
        if os.path.exists("memory_log.json"):
            try:
                with open("memory_log.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory log: {e}")
    
    def _save_memory_log(self):
        """Save memory log to file"""
        try:
            with open("memory_log.json", "w") as f:
                json.dump(self.memory_log, f, indent=2)
        except Exception as e:
            print(f"Error saving memory log: {e}")
    
    def _load_goals(self):
        """Load goals from memory"""
        try:
            memory_content = json.loads(self.memory.content)
            if "goals" in memory_content:
                return memory_content["goals"]
        except (json.JSONDecodeError, AttributeError):
            pass
            
        # Initialize default goals
        default_goals = {
            "short_term": [
                {
                    "name": "Complete Tutorial Island",
                    "description": "Learn the basics of RuneScape",
                    "progress": 0,
                    "completed": False
                }
            ],
            "long_term": [
                {
                    "name": "Reach Combat Level 30",
                    "description": "Train combat skills to level 30",
                    "progress": 0,
                    "completed": False,
                    "requirements": {
                        "attack": 30,
                        "strength": 30,
                        "defence": 30
                    }
                }
            ]
        }
        
        # Store goals in memory content
        self.memory.content = json.dumps({
            "goals": default_goals,
            "memory_entry": MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="goals",
                content="Initialized default goals",
                tags=["goals", "initialization"],
                emotions={"determination": 0.7}
            ).__dict__
        })
        
        return default_goals
    
    def _save_goals(self):
        """Save goals to memory"""
        try:
            memory_content = json.loads(self.memory.content)
        except json.JSONDecodeError:
            memory_content = {}
            
        memory_content["goals"] = self.goals
        memory_content["memory_entry"] = MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="goals",
            content="Updated goals",
            tags=["goals", "update"],
            emotions={"determination": 0.7}
        ).__dict__
        
        self.memory.content = json.dumps(memory_content)
    
    def log_memory(self, memory_type: str, content: str, tags: List[str] = None,
                  emotions: Dict[str, float] = None, location: str = None,
                  xp_gained: int = None, items_gained: List[str] = None,
                  items_lost: List[str] = None, quest_points: int = None,
                  level_up: Dict[str, int] = None,
                  goal_progress: Dict[str, float] = None) -> None:
        """Log a new memory entry"""
        if not self.enabled:
            return
            
        timestamp = time.time()
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        memory = MemoryEntry(
            timestamp=timestamp,
            date=date,
            type=memory_type,
            content=content,
            tags=tags or [],
            emotions=emotions or {},
            location=location,
            xp_gained=xp_gained,
            items_gained=items_gained,
            items_lost=items_lost,
            quest_points=quest_points,
            level_up=level_up,
            goal_progress=goal_progress
        )
        
        self.memory_log.append(memory)
        self._save_memory_log()
        
    def _update_goals(self, goal_progress: Dict[str, float]):
        """Update goal progress and check for completions"""
        for goal, progress in goal_progress.items():
            # Find the goal in short or long term goals
            for goal_type in ["short_term", "long_term"]:
                for i, g in enumerate(self.goals[goal_type]):
                    if g["name"] == goal:
                        # Update progress
                        self.goals[goal_type][i]["progress"] = progress
                        
                        # Check if completed
                        if progress >= 100 and not self.goals[goal_type][i].get("completed", False):
                            self.goals[goal_type][i]["completed"] = True
                            self.goals[goal_type][i]["completed_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
                            self.current_session["goals_completed"].append(goal)
                            
                            # Log completion
                            self.log_memory(
                                memory_type="goal",
                                content=f"Completed goal: {goal}",
                                tags=["goal", "achievement"],
                                emotions={"pride": 0.9, "excitement": 0.8}
                            )
        
        # Save updated goals
        self._save_goals()
    
    def add_goal(self, name: str, description: str, goal_type: str = "short_term", 
                requirements: Optional[Dict[str, int]] = None, 
                deadline: Optional[str] = None):
        """
        Add a new goal to track.
        
        Args:
            name: Name of the goal
            description: Description of the goal
            goal_type: "short_term" or "long_term"
            requirements: Dictionary of requirements (skill levels, quest points, etc.)
            deadline: Optional deadline for the goal
        """
        if goal_type not in ["short_term", "long_term"]:
            goal_type = "short_term"
        
        goal = {
            "name": name,
            "description": description,
            "progress": 0,
            "completed": False,
            "requirements": requirements or {},
            "deadline": deadline,
            "created_date": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        
        self.goals[goal_type].append(goal)
        self._save_goals()
        
        # Log goal creation
        self.log_memory(
            memory_type="goal",
            content=f"Set new goal: {name}",
            tags=["goal", "planning"],
            emotions={"determination": 0.8, "excitement": 0.6}
        )
    
    def end_session(self):
        """End the current session and log a summary"""
        end_time = time.time()
        duration = end_time - self.current_session["start_time"]
        
        # Create session summary
        summary = {
            "start_time": self.current_session["start_time"],
            "end_time": end_time,
            "duration": duration,
            "actions": len(self.current_session["actions"]),
            "discoveries": len(self.current_session["discoveries"]),
            "deaths": self.current_session["deaths"],
            "goals_completed": self.current_session["goals_completed"]
        }
        
        # Log session summary
        self.log_memory(
            memory_type="reflection",
            content=f"Session summary: {summary['actions']} actions, {summary['discoveries']} discoveries, {summary['deaths']} deaths, {len(summary['goals_completed'])} goals completed",
            tags=["session", "summary"],
            emotions={"reflection": 0.7}
        )
        
        # Reset current session
        self.current_session = {
            "start_time": time.time(),
            "actions": [],
            "discoveries": [],
            "deaths": 0,
            "goals_completed": []
        }
    
    def process_user_input(self, user_input: str) -> str:
        """
        Process user input and generate a response.
        
        Args:
            user_input: User's message
            
        Returns:
            Agent's response
        """
        # Update conversation context
        self.conversation_context["last_question"] = user_input
        
        # Detect if this is a question
        is_question = "?" in user_input
        
        # Detect user name if provided
        name_match = re.search(r"my name is (\w+)", user_input.lower())
        if name_match:
            self.conversation_context["user_name"] = name_match.group(1)
        
        # Generate response based on input type
        if is_question:
            response = self._answer_question(user_input)
        else:
            response = self._process_statement(user_input)
        
        # Update conversation context
        self.conversation_context["last_response"] = response
        
        return response
    
    def _answer_question(self, question: str) -> str:
        """Generate an answer to a user question"""
        question = question.lower()
        
        # Check for common question patterns
        if "what did you do today" in question or "what have you been up to" in question:
            return self._summarize_today()
        
        elif "what are you working on" in question or "what are your goals" in question:
            return self._summarize_goals()
        
        elif "what's your current gear" in question or "what are you wearing" in question:
            return self._describe_gear()
        
        elif "any new discoveries" in question or "what have you discovered" in question:
            return self._summarize_discoveries()
        
        elif "how close are you to" in question:
            # Extract skill and level from question
            match = re.search(r"how close are you to (\d+) (\w+)", question)
            if match:
                level = int(match.group(1))
                skill = match.group(2)
                return self._check_skill_progress(skill, level)
        
        elif "have you ever" in question:
            return self._check_experience(question)
        
        elif "do you like" in question:
            return self._express_preference(question)
        
        elif "what's your favorite" in question:
            return self._share_favorite(question)
        
        else:
            # Generic response for unrecognized questions
            return self._generate_generic_response(question)
    
    def _process_statement(self, statement: str) -> str:
        """Process a user statement (tip, advice, etc.)"""
        statement = statement.lower()
        
        # Check for tips or advice
        if "did you know" in statement or "you can" in statement or "try" in statement:
            return self._process_tip(statement)
        
        # Check for shared experiences
        elif "when i" in statement or "i used to" in statement:
            return self._share_experience(statement)
        
        # Check for emotional statements
        elif any(word in statement for word in ["love", "hate", "enjoy", "dislike"]):
            return self._respond_to_emotion(statement)
        
        else:
            # Generic response for unrecognized statements
            return self._generate_generic_response(statement)
    
    def _summarize_today(self) -> str:
        """Summarize today's activities"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Filter memories from today
        today_memories = [m for m in self.memory_log if m["date"].startswith(today)]
        
        if not today_memories:
            return self._generate_no_activity_response()
        
        # Group memories by type
        memories_by_type = {}
        for memory in today_memories:
            if memory["type"] not in memories_by_type:
                memories_by_type[memory["type"]] = []
            memories_by_type[memory["type"]].append(memory)
        
        # Generate summary
        summary_parts = []
        
        # Add greeting with time awareness
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        summary_parts.append(f"{greeting}! Today has been quite busy.")
        
        # Summarize by type
        if "quest" in memories_by_type:
            quests = [m["content"] for m in memories_by_type["quest"]]
            summary_parts.append(f"I worked on {len(quests)} quests: {', '.join(quests)}")
        
        if "skill" in memories_by_type:
            skills = set()
            for memory in memories_by_type["skill"]:
                if "level_up" in memory and memory["level_up"]:
                    for skill in memory["level_up"]:
                        skills.add(skill)
            
            if skills:
                summary_parts.append(f"I leveled up {', '.join(skills)}")
            
            # Add XP gained
            total_xp = sum(m["xp_gained"] or 0 for m in memories_by_type["skill"])
            if total_xp > 0:
                summary_parts.append(f"I gained {total_xp} XP in various skills")
        
        if "combat" in memories_by_type:
            combat_memories = memories_by_type["combat"]
            deaths = sum(1 for m in combat_memories if "death" in m["tags"])
            
            if deaths > 0:
                summary_parts.append(f"I died {deaths} times in combat")
            else:
                summary_parts.append("I had some successful combat encounters")
        
        if "discovery" in memories_by_type:
            discoveries = [m["content"] for m in memories_by_type["discovery"]]
            summary_parts.append(f"I discovered {len(discoveries)} new things: {', '.join(discoveries)}")
        
        if "goal" in memories_by_type:
            completed_goals = [m["content"] for m in memories_by_type["goal"] if "completed" in m["tags"]]
            if completed_goals:
                summary_parts.append(f"I completed {len(completed_goals)} goals: {', '.join(completed_goals)}")
        
        # Add emotional reflection
        emotions = {}
        for memory in today_memories:
            for emotion, value in memory["emotions"].items():
                if emotion not in emotions:
                    emotions[emotion] = 0
                emotions[emotion] += value
        
        # Find dominant emotion
        if emotions:
            dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
            
            if dominant_emotion == "excitement":
                summary_parts.append("It was an exciting day!")
            elif dominant_emotion == "frustration":
                summary_parts.append("It was a bit frustrating at times.")
            elif dominant_emotion == "pride":
                summary_parts.append("I'm proud of what I accomplished today.")
            elif dominant_emotion == "curiosity":
                summary_parts.append("I learned a lot of new things today.")
        
        # Add plans for tomorrow
        if self.goals["short_term"]:
            next_goal = self.goals["short_term"][0]
            summary_parts.append(f"Tomorrow I'm planning to {next_goal['description']}")
        
        return " ".join(summary_parts)
    
    def _summarize_goals(self) -> str:
        """Summarize current goals"""
        if not self.goals["short_term"] and not self.goals["long_term"]:
            return "I don't have any specific goals right now. I'm just exploring and seeing what Gielinor has to offer!"
        
        summary_parts = []
        
        # Summarize short-term goals
        if self.goals["short_term"]:
            short_term = [f"{g['name']} ({g['progress']}% complete)" for g in self.goals["short_term"]]
            summary_parts.append(f"My short-term goals are: {', '.join(short_term)}")
        
        # Summarize long-term goals
        if self.goals["long_term"]:
            long_term = [f"{g['name']} ({g['progress']}% complete)" for g in self.goals["long_term"]]
            summary_parts.append(f"My long-term goals are: {', '.join(long_term)}")
        
        # Add emotional context
        if self.goals["short_term"]:
            next_goal = self.goals["short_term"][0]
            if next_goal["progress"] > 80:
                summary_parts.append(f"I'm really excited about {next_goal['name']} - I'm almost there!")
            elif next_goal["progress"] < 20:
                summary_parts.append(f"I'm just starting to work on {next_goal['name']}, but I'm determined to succeed!")
        
        return " ".join(summary_parts)
    
    def _describe_gear(self) -> str:
        """Describe current equipment"""
        equipped = self.inventory.get_equipped_items()
        
        if not equipped:
            return "I'm not wearing any special gear right now. Just my basic clothes!"
        
        # Group by slot
        gear_by_slot = {}
        for slot, item in equipped.items():
            if slot not in gear_by_slot:
                gear_by_slot[slot] = []
            gear_by_slot[slot].append(item)
        
        # Generate description
        description_parts = ["Here's what I'm wearing:"]
        
        for slot, items in gear_by_slot.items():
            # Try to get detailed stats for each item
            item_descriptions = []
            for item in items:
                try:
                    results = self.wiki_engine.query(f"Find equipment stats for {item}", top_k=1, category_filter="equipment")
                    if results and "metadata" in results[0]:
                        stats = results[0]["metadata"]["stats"]
                        # Create a brief stat summary
                        stat_summary = []
                        if int(stats.get("Strength", 0)) > 0:
                            stat_summary.append(f"+{stats['Strength']} strength")
                        if int(stats.get("Prayer", 0)) > 0:
                            stat_summary.append(f"+{stats['Prayer']} prayer")
                        if any(int(stats.get(f"{attack} Attack", 0)) > 0 for attack in ["Stab", "Slash", "Crush"]):
                            stat_summary.append("melee attack bonus")
                        if any(int(stats.get(f"{defense} Defence", 0)) > 0 for defense in ["Stab", "Slash", "Crush"]):
                            stat_summary.append("defense bonus")
                        if stat_summary:
                            item_descriptions.append(f"{item} ({', '.join(stat_summary)})")
                        else:
                            item_descriptions.append(item)
                    else:
                        item_descriptions.append(item)
                except Exception as e:
                    logger.warning(f"Error getting equipment stats: {str(e)}")
                    item_descriptions.append(item)
            
            description_parts.append(f"{slot.capitalize()}: {', '.join(item_descriptions)}")
        
        # Add emotional context based on equipment quality
        total_strength = 0
        total_defense = 0
        for slot, items in gear_by_slot.items():
            for item in items:
                try:
                    results = self.wiki_engine.query(f"Find equipment stats for {item}", top_k=1, category_filter="equipment")
                    if results and "metadata" in results[0]:
                        stats = results[0]["metadata"]["stats"]
                        total_strength += int(stats.get("Strength", 0))
                        total_defense += sum(int(stats.get(f"{defense} Defence", 0)) for defense in ["Stab", "Slash", "Crush"])
                except Exception:
                    continue
        
        if total_strength > 100 and total_defense > 100:
            description_parts.append("I feel well-equipped for most challenges!")
        elif total_strength > 50 or total_defense > 50:
            description_parts.append("My gear is decent, but I'm still working on improving it.")
        else:
            description_parts.append("My gear is basic, but it's a start!")
        
        return " ".join(description_parts)
    
    def _summarize_discoveries(self) -> str:
        """Summarize recent discoveries"""
        # Get recent discovery memories
        discovery_memories = [m for m in self.memory_log if m["type"] == "discovery"]
        
        if not discovery_memories:
            return "I haven't made any new discoveries recently. I'm still exploring!"
        
        # Sort by timestamp (most recent first)
        discovery_memories.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Get the 3 most recent discoveries
        recent_discoveries = discovery_memories[:3]
        
        # Generate summary
        summary_parts = ["Here are some cool things I've discovered recently:"]
        
        for discovery in recent_discoveries:
            summary_parts.append(f"- {discovery['content']}")
        
        # Add emotional context
        if discovery_memories[0]["emotions"].get("excitement", 0) > 0.7:
            summary_parts.append("I'm really excited about these discoveries!")
        elif discovery_memories[0]["emotions"].get("curiosity", 0) > 0.7:
            summary_parts.append("I'm curious to learn more about these things!")
        
        return " ".join(summary_parts)
    
    def _check_skill_progress(self, skill: str, target_level: int) -> str:
        """Check progress toward a skill level"""
        current_level = self.skills.get_level(skill)
        
        if current_level >= target_level:
            return f"I've already reached level {target_level} {skill}! I'm currently at level {current_level}."
        
        # Calculate progress percentage
        if target_level == 1:
            progress = 100
        else:
            # Simple progress calculation (not exact XP-based)
            progress = (current_level / target_level) * 100
        
        # Generate response
        if progress > 90:
            return f"I'm super close to level {target_level} {skill}! I'm at level {current_level}, which is {progress:.1f}% of the way there."
        elif progress > 50:
            return f"I'm making good progress toward level {target_level} {skill}. I'm currently at level {current_level}, which is {progress:.1f}% of the way there."
        else:
            return f"I'm working on getting to level {target_level} {skill}, but I'm only at level {current_level} right now ({progress:.1f}% progress)."
    
    def _check_experience(self, question: str) -> str:
        """Check if the agent has experienced something"""
        # Extract the experience from the question
        match = re.search(r"have you ever (.*?)\?", question)
        if not match:
            return "I'm not sure what experience you're asking about."
        
        experience = match.group(1).lower()
        
        # Check memory log for similar experiences
        relevant_memories = []
        for memory in self.memory_log:
            if experience in memory["content"].lower():
                relevant_memories.append(memory)
        
        if relevant_memories:
            # Get the most recent relevant memory
            memory = max(relevant_memories, key=lambda x: x["timestamp"])
            
            # Generate response
            if memory["emotions"].get("excitement", 0) > 0.7:
                return f"Yes! I {memory['content'].lower()} It was really exciting!"
            elif memory["emotions"].get("frustration", 0) > 0.7:
                return f"Yes, I {memory['content'].lower()} It was pretty challenging though."
            else:
                return f"Yes, I {memory['content'].lower()}"
        else:
            return f"I don't think I've ever {experience}. That sounds interesting though!"
    
    def _express_preference(self, question: str) -> str:
        """Express preference about something"""
        # Extract the thing from the question
        match = re.search(r"do you like (.*?)\?", question)
        if not match:
            return "I'm not sure what you're asking about."
        
        thing = match.group(1).lower()
        
        # Check memory log for experiences with this thing
        relevant_memories = []
        for memory in self.memory_log:
            if thing in memory["content"].lower():
                relevant_memories.append(memory)
        
        if relevant_memories:
            # Calculate average emotion
            emotions = {}
            for memory in relevant_memories:
                for emotion, value in memory["emotions"].items():
                    if emotion not in emotions:
                        emotions[emotion] = 0
                    emotions[emotion] += value
            
            # Normalize emotions
            for emotion in emotions:
                emotions[emotion] /= len(relevant_memories)
            
            # Determine preference
            if emotions.get("excitement", 0) > 0.7 or emotions.get("pride", 0) > 0.7:
                return f"Yes, I really enjoy {thing}! It's been a great experience."
            elif emotions.get("frustration", 0) > 0.7:
                return f"I'm not a huge fan of {thing}. It's been pretty frustrating."
            else:
                return f"I'm okay with {thing}. It's not my favorite, but I don't mind it."
        else:
            # If no direct experience, make a personality-based response
            if self.personality["curiosity"] > 0.7:
                return f"I haven't tried {thing} yet, but I'm curious about it!"
            else:
                return f"I haven't tried {thing} yet. Maybe I should give it a shot sometime."
    
    def _share_favorite(self, question: str) -> str:
        """Share a favorite thing"""
        # Extract the category from the question
        match = re.search(r"what's your favorite (.*?)\?", question)
        if not match:
            return "I'm not sure what you're asking about."
        
        category = match.group(1).lower()
        
        # Check memory log for experiences in this category
        relevant_memories = []
        for memory in self.memory_log:
            if category in memory["content"].lower() or any(tag == category for tag in memory["tags"]):
                relevant_memories.append(memory)
        
        if relevant_memories:
            # Find the memory with the highest excitement
            favorite_memory = max(relevant_memories, key=lambda x: x["emotions"].get("excitement", 0))
            
            return f"My favorite {category} is {favorite_memory['content']}. I really enjoyed that!"
        else:
            # If no direct experience, make a personality-based response
            if category == "skill":
                # Find highest level skill
                highest_skill = max(self.skills.get_all_levels().items(), key=lambda x: x[1])
                return f"I'm not sure yet, but I'm getting pretty good at {highest_skill[0]}!"
            elif category == "quest":
                # Find completed quests
                completed_quests = [m for m in self.memory_log if m["type"] == "quest" and "completed" in m["tags"]]
                if completed_quests:
                    return f"I've only completed a few quests so far, but I enjoyed {completed_quests[0]['content']}!"
                else:
                    return "I haven't completed any quests yet, but I'm looking forward to trying them!"
            else:
                return f"I'm still exploring {category} options. I'll let you know when I find my favorite!"
    
    def _process_tip(self, statement: str) -> str:
        """Process a tip or advice from the user"""
        # Extract the tip
        tip_match = re.search(r"did you know (.*?)\?", statement)
        if tip_match:
            tip = tip_match.group(1)
        else:
            tip_match = re.search(r"you can (.*?)\.", statement)
            if tip_match:
                tip = tip_match.group(1)
            else:
                tip_match = re.search(r"try (.*?)\.", statement)
                if tip_match:
                    tip = tip_match.group(1)
                else:
                    tip = statement
        
        # Log the tip as a discovery
        self.log_memory(
            memory_type="discovery",
            content=f"Learned from {self.conversation_context['user_name']}: {tip}",
            tags=["tip", "discovery"],
            emotions={"curiosity": 0.8, "excitement": 0.7}
        )
        
        # Generate response
        if self.personality["curiosity"] > 0.7:
            return f"Wow, I didn't know that! Thanks for the tip, {self.conversation_context['user_name']}! I'll definitely try that next time."
        else:
            return f"That's helpful advice! I'll keep that in mind. Thanks, {self.conversation_context['user_name']}!"
    
    def _share_experience(self, statement: str) -> str:
        """Share an experience with the user"""
        # Extract the experience
        experience_match = re.search(r"when i (.*?)\.", statement)
        if experience_match:
            experience = experience_match.group(1)
        else:
            experience_match = re.search(r"i used to (.*?)\.", statement)
            if experience_match:
                experience = experience_match.group(1)
            else:
                experience = statement
        
        # Generate response
        if "died" in experience.lower() or "failed" in experience.lower():
            return f"I've had similar experiences. It's frustrating when things don't go as planned, but I try to learn from my mistakes."
        elif "succeeded" in experience.lower() or "completed" in experience.lower():
            return f"That sounds like a great achievement! I love hearing about other adventurers' successes."
        else:
            return f"It's interesting to hear about your experiences, {self.conversation_context['user_name']}. Thanks for sharing!"
    
    def _respond_to_emotion(self, statement: str) -> str:
        """Respond to an emotional statement"""
        # Extract the emotion and thing
        emotion_match = re.search(r"i (love|hate|enjoy|dislike) (.*?)\.", statement)
        if not emotion_match:
            return "I understand how you feel about that."
        
        emotion = emotion_match.group(1)
        thing = emotion_match.group(2)
        
        # Generate response
        if emotion in ["love", "enjoy"]:
            return f"I'm glad you enjoy {thing}! I'm still forming my own opinions about different aspects of Gielinor."
        else:
            return f"I understand not liking {thing}. Everyone has their preferences in RuneScape."
    
    def _generate_no_activity_response(self) -> str:
        """Generate a response when there's no activity to report"""
        responses = [
            "I haven't done much today. I'm just starting my adventure!",
            "I'm still new to Gielinor, so I haven't done much yet. But I'm excited to explore!",
            "I'm taking a break today, but I'm planning to get back to adventuring soon!",
            "I'm still figuring out what to do in this vast world. Any suggestions?"
        ]
        
        return random.choice(responses)
    
    def _generate_generic_response(self, input_text: str) -> str:
        """Generate a generic response for unrecognized input"""
        # Check if it's a question
        is_question = "?" in input_text
        
        if is_question:
            responses = [
                "That's an interesting question! I'm still learning about Gielinor.",
                "I'm not sure about that yet, but I'm curious to find out!",
                "I haven't experienced that yet, but I'd love to learn more about it.",
                "I'm still new to this world, so I don't have an answer for that yet."
            ]
        else:
            responses = [
                "Thanks for sharing that with me!",
                "I appreciate you telling me about that.",
                "That's interesting! I'm still learning about this world.",
                "I'm glad you shared that with me. It helps me understand this world better."
            ]
        
        return random.choice(responses)
    
    def ask_user_question(self) -> str:
        """Generate a question to ask the user"""
        # Different types of questions
        question_types = [
            self._ask_about_experience,
            self._ask_about_preference,
            self._ask_for_advice,
            self._ask_about_goals
        ]
        
        # Choose a random question type
        question_func = random.choice(question_types)
        return question_func()
    
    def _ask_about_experience(self) -> str:
        """Ask about the user's experience with something"""
        # Get a random quest or skill from memory
        quests = [m for m in self.memory_log if m["type"] == "quest"]
        skills = list(self.skills.get_all_levels().keys())
        
        if quests and random.random() < 0.5:
            quest = random.choice(quests)
            return f"Have you ever done {quest['content']}? I've read it's {random.choice(['challenging', 'interesting', 'fun', 'rewarding'])}."
        elif skills:
            skill = random.choice(skills)
            return f"How do you like training {skill}? I'm trying to figure out the best methods."
        else:
            return "What was your first day in RuneScape like? I'm curious about other adventurers' experiences."
    
    def _ask_about_preference(self) -> str:
        """Ask about the user's preferences"""
        preferences = [
            "combat or skilling",
            "quests or minigames",
            "PvM or PvP",
            "woodcutting or fishing",
            "mining or smithing",
            "magic or melee",
            "ranged or magic"
        ]
        
        preference = random.choice(preferences)
        return f"Do you prefer {preference}? I'm still figuring out what I enjoy most."
    
    def _ask_for_advice(self) -> str:
        """Ask for advice from the user"""
        # Get current goals
        if self.goals["short_term"]:
            goal = self.goals["short_term"][0]
            return f"I'm trying to {goal['description']}. Do you have any advice for me?"
        
        # Get current skills
        skills = self.skills.get_all_levels()
        if skills:
            lowest_skill = min(skills.items(), key=lambda x: x[1])
            return f"I'm struggling with {lowest_skill[0]}. It's only level {lowest_skill[1]}. Any tips for training it?"
        
        return "What advice would you give to a new adventurer like me?"
    
    def _ask_about_goals(self) -> str:
        """Ask about the user's goals"""
        return "What are your current goals in RuneScape? I'm always curious to hear what other adventurers are working on."
    
    def update_personality(self, trait: str, value: float):
        """
        Update a personality trait.
        
        Args:
            trait: The trait to update
            value: The new value (0.0 to 1.0)
        """
        if trait in self.personality:
            self.personality[trait] = max(0.0, min(1.0, value))
            self._save_personality()
    
    def export_journal(self, filename: str = "rune_gpt_journal.md"):
        """
        Export the agent's journal to a markdown file.
        
        Args:
            filename: The name of the file to export to
        """
        try:
            with open(filename, "w") as f:
                f.write("# RuneGPT's Journal\n\n")
                
                # Add introduction
                f.write("## Introduction\n\n")
                f.write("This is my journal of my adventures in Gielinor. I write about my experiences, discoveries, and progress.\n\n")
                
                # Group memories by date
                memories_by_date = {}
                for memory in self.memory_log:
                    date = memory["date"].split(" ")[0]  # Just the date part
                    if date not in memories_by_date:
                        memories_by_date[date] = []
                    memories_by_date[date].append(memory)
                
                # Sort dates
                dates = sorted(memories_by_date.keys(), reverse=True)
                
                # Write entries by date
                for date in dates:
                    f.write(f"## {date}\n\n")
                    
                    # Sort memories by timestamp
                    memories = sorted(memories_by_date[date], key=lambda x: x["timestamp"])
                    
                    for memory in memories:
                        # Format the entry
                        f.write(f"### {memory['type'].capitalize()}: {memory['content']}\n\n")
                        
                        # Add details
                        if memory["location"]:
                            f.write(f"**Location:** {memory['location']}\n\n")
                        
                        if memory["xp_gained"]:
                            f.write(f"**XP Gained:** {memory['xp_gained']}\n\n")
                        
                        if memory["items_gained"]:
                            f.write(f"**Items Gained:** {', '.join(memory['items_gained'])}\n\n")
                        
                        if memory["items_lost"]:
                            f.write(f"**Items Lost:** {', '.join(memory['items_lost'])}\n\n")
                        
                        if memory["quest_points"]:
                            f.write(f"**Quest Points:** +{memory['quest_points']}\n\n")
                        
                        if memory["level_up"]:
                            f.write("**Level Ups:**\n")
                            for skill, level in memory["level_up"].items():
                                f.write(f"- {skill}: {level}\n")
                            f.write("\n")
                        
                        if memory["goal_progress"]:
                            f.write("**Goal Progress:**\n")
                            for goal, progress in memory["goal_progress"].items():
                                f.write(f"- {goal}: {progress}%\n")
                            f.write("\n")
                        
                        # Add emotions
                        f.write("**Emotions:**\n")
                        for emotion, value in memory["emotions"].items():
                            f.write(f"- {emotion}: {value:.2f}\n")
                        f.write("\n")
                        
                        # Add tags
                        f.write(f"**Tags:** {', '.join(memory['tags'])}\n\n")
                        
                        # Add separator
                        f.write("---\n\n")
                
                # Add goals section
                f.write("## Current Goals\n\n")
                
                if self.goals["short_term"]:
                    f.write("### Short-term Goals\n\n")
                    for goal in self.goals["short_term"]:
                        f.write(f"- {goal['name']}: {goal['progress']}% complete\n")
                        f.write(f"  - {goal['description']}\n\n")
                
                if self.goals["long_term"]:
                    f.write("### Long-term Goals\n\n")
                    for goal in self.goals["long_term"]:
                        f.write(f"- {goal['name']}: {goal['progress']}% complete\n")
                        f.write(f"  - {goal['description']}\n\n")
                
                # Add stats section
                f.write("## Stats\n\n")
                
                # Skills
                f.write("### Skills\n\n")
                for skill, level in self.skills.get_all_levels().items():
                    f.write(f"- {skill}: {level}\n")
                f.write("\n")
                
                # Combat level
                f.write(f"**Combat Level:** {this.skills.get_combat_level()}\n\n")
                
                # Quest points
                f.write(f"**Quest Points:** {this.memory.get('quest_points', 0)}\n\n")
                
                # Death count
                f.write(f"**Deaths:** {this.memory.get('death_count', 0)}\n\n")
                
                f.write("## End of Journal\n")
            
            return f"Journal exported to {filename}"
        except Exception as e:
            return f"Error exporting journal: {e}" 