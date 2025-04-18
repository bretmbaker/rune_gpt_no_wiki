# screen_parser.py - Interprets OSRS in-game text and converts to actionable intents

import re
from typing import Dict, List, Tuple, Optional

class ScreenParser:
    """Class for parsing OSRS in-game text and converting to actionable intents."""
    
    def __init__(self):
        # Common action patterns with their corresponding intents
        self.ACTION_PATTERNS = [
            # NPC interaction patterns
            (r"talk to (?:the )?([A-Za-z\s]+)(?: to begin)?", "talk to NPC {0}"),
            (r"speak to (?:the )?([A-Za-z\s]+)", "talk to NPC {0}"),
            (r"ask (?:the )?([A-Za-z\s]+) about", "talk to NPC {0}"),
            
            # Object interaction patterns
            (r"open (?:the )?([a-z\s]+)(?: and head outside)?", "open {0}"),
            (r"click on (?:the )?([a-z\s]+) icon", "open {0} tab"),
            (r"click on (?:the )?([a-z\s]+)", "click on {0}"),
            (r"use (?:the )?([a-z\s]+)", "use {0}"),
            
            # Skill action patterns
            (r"chop down (?:a )?([a-z\s]+)", "chop {0}"),
            (r"mine (?:the )?([a-z\s]+)", "mine {0}"),
            (r"take (?:some )?raw ([a-z\s]+) from (?:the )?fishing spot", "fish {0}"),
            (r"fish (?:for )?(?:some )?([a-z\s]+)", "fish {0}"),
            (r"craft (?:a )?([a-z\s]+)", "craft {0}"),
            (r"cook (?:the )?raw ([a-z\s]+) (?:on|in) (?:the )?([a-z\s]+)", "cook {0}"),
            (r"eat (?:the )?(?:cooked )?([a-z\s]+)", "eat {0}"),
            (r"light (?:the )?([a-z\s]+)", "light {0}"),
            (r"extinguish (?:the )?([a-z\s]+)", "extinguish {0}"),
            
            # Movement patterns
            (r"walk to (?:the )?([a-z\s]+)", "walk to {0}"),
            (r"go to (?:the )?([a-z\s]+)", "walk to {0}"),
            (r"head to (?:the )?([a-z\s]+)", "walk to {0}"),
            
            # UI interaction patterns
            (r"open (?:your )?inventory", "open inventory tab"),
            (r"open (?:your )?equipment", "open equipment tab"),
            (r"open (?:your )?prayer", "open prayer tab"),
            (r"open (?:your )?magic", "open magic tab"),
            (r"open (?:your )?combat", "open combat tab"),
            (r"open (?:your )?skills", "open skills tab"),
            (r"open (?:your )?quest", "open quest tab"),
            (r"open (?:your )?minimap", "open minimap"),
            (r"open (?:your )?map", "open map"),
            (r"open (?:your )?bank", "open bank"),
            
            # Combat patterns
            (r"attack (?:the )?([a-z\s]+)", "attack {0}"),
            (r"fight (?:the )?([a-z\s]+)", "attack {0}"),
            (r"cast ([a-z\s]+) on (?:the )?([a-z\s]+)", "cast {0} {1}"),
            
            # Item interaction patterns
            (r"take (?:some )?([a-z\s]+)(?: from (?:the )?([a-z\s]+))?", "take {0}"),
            (r"drink (?:the )?([a-z\s]+)", "drink {0}"),
            (r"equip (?:the )?([a-z\s]+)", "equip {0}"),
            (r"wield (?:the )?([a-z\s]+)", "equip {0}")
        ]
        
        # Special case patterns that need custom handling
        self.SPECIAL_CASES = [
            (r"you can now open the door and head outside", "open nearby door"),
            (r"you can now open the door", "open nearby door"),
            (r"you can now leave", "exit area"),
            (r"you can now proceed", "continue"),
            (r"you can now continue", "continue"),
            (r"you can now move on", "continue"),
            (r"click here to continue", "continue dialogue"),
            (r"click here to proceed", "continue dialogue"),
            (r"click here to skip", "skip dialogue"),
            (r"click here to close", "close dialogue"),
        ]
    
    def parse_screen_text(self, screen_text: str) -> str:
        """
        Parse the screen text to determine the action to take.
        
        Args:
            screen_text: The text displayed on the game screen
            
        Returns:
            The action to take
        """
        # Convert to lowercase for easier matching
        text = screen_text.lower()
        
        # Common action patterns
        patterns = {
            "talk": r"talk to|speak to|chat with",
            "click": r"click|select|choose",
            "use": r"use|equip|wear",
            "move": r"walk to|go to|move to",
            "wait": r"wait|stay|remain",
            "complete": r"complete|finish|done"
        }
        
        # Find matching pattern
        for action, pattern in patterns.items():
            if re.search(pattern, text):
                return action
        
        return "wait"
    
    def extract_entities(self, screen_text: str) -> Dict:
        """
        Extract entities from screen text including location, skills, inventory, and equipment.
        
        Args:
            screen_text: The text displayed on the game screen
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        # Extract location
        location_match = re.search(r"in ([\w\s]+)", screen_text)
        if location_match:
            entities["location"] = location_match.group(1).strip()
        
        # Extract skills
        skills = {}
        skill_pattern = r"(\w+): (\d+)"
        for match in re.finditer(skill_pattern, screen_text):
            skill, level = match.groups()
            skills[skill.lower()] = int(level)
        if skills:
            entities["skills"] = skills
        
        # Extract inventory
        inventory = []
        if "inventory:" in screen_text.lower():
            # Find the inventory section
            inv_start = screen_text.lower().find("inventory:")
            inv_end = screen_text.find("\n\n", inv_start)
            if inv_end == -1:
                inv_end = len(screen_text)
            
            inv_text = screen_text[inv_start:inv_end]
            
            # Extract items
            item_pattern = r"- ([\w\s]+)(?: x(\d+))?"
            for match in re.finditer(item_pattern, inv_text):
                item, count = match.groups()
                count = int(count) if count else 1
                inventory.append({"name": item.strip(), "count": count})
        if inventory:
            entities["inventory"] = inventory
        
        # Extract equipment
        equipment = {}
        if "equipment:" in screen_text.lower():
            # Find the equipment section
            equip_start = screen_text.lower().find("equipment:")
            equip_end = screen_text.find("\n\n", equip_start)
            if equip_end == -1:
                equip_end = len(screen_text)
            
            equip_text = screen_text[equip_start:equip_end]
            
            # Extract equipped items
            slot_pattern = r"(\w+): ([\w\s]+)"
            for match in re.finditer(slot_pattern, equip_text):
                slot, item = match.groups()
                equipment[slot.lower()] = item.strip()
        if equipment:
            entities["equipment"] = equipment
        
        # Extract quest points
        qp_match = re.search(r"quest points: (\d+)", screen_text.lower())
        if qp_match:
            entities["quest_points"] = int(qp_match.group(1))
        
        # Extract combat level
        combat_match = re.search(r"combat level: (\d+)", screen_text.lower())
        if combat_match:
            entities["combat_level"] = int(combat_match.group(1))
        
        # Extract health
        health_match = re.search(r"health: (\d+)/(\d+)", screen_text.lower())
        if health_match:
            entities["health"] = {
                "current": int(health_match.group(1)),
                "maximum": int(health_match.group(2))
            }
        
        # Extract prayer
        prayer_match = re.search(r"prayer: (\d+)/(\d+)", screen_text.lower())
        if prayer_match:
            entities["prayer"] = {
                "current": int(prayer_match.group(1)),
                "maximum": int(prayer_match.group(2))
            }
        
        # Extract run energy
        energy_match = re.search(r"run energy: (\d+)%", screen_text.lower())
        if energy_match:
            entities["run_energy"] = int(energy_match.group(1))
        
        # Extract weight
        weight_match = re.search(r"weight: ([\d.]+) kg", screen_text.lower())
        if weight_match:
            entities["weight"] = float(weight_match.group(1))
        
        return entities

def extract_combat_info(screen_text: str) -> Dict:
    """
    Extract combat-related information from screen text.
    
    Args:
        screen_text: The text displayed on the game screen
        
    Returns:
        Dictionary of combat information
    """
    combat_info = {}
    
    # Extract target information
    target_match = re.search(r"fighting: ([\w\s]+)", screen_text.lower())
    if target_match:
        combat_info["target"] = target_match.group(1).strip()
    
    # Extract target health
    target_health_match = re.search(r"target health: (\d+)/(\d+)", screen_text.lower())
    if target_health_match:
        combat_info["target_health"] = {
            "current": int(target_health_match.group(1)),
            "maximum": int(target_health_match.group(2))
        }
    
    # Extract combat style
    style_match = re.search(r"combat style: ([\w\s]+)", screen_text.lower())
    if style_match:
        combat_info["style"] = style_match.group(1).strip()
    
    # Extract auto-retaliate status
    if "auto-retaliate: on" in screen_text.lower():
        combat_info["auto_retaliate"] = True
    elif "auto-retaliate: off" in screen_text.lower():
        combat_info["auto_retaliate"] = False
    
    return combat_info

def extract_interface_info(screen_text: str) -> Dict:
    """
    Extract interface information from screen text.
    
    Args:
        screen_text: The text displayed on the game screen
        
    Returns:
        Dictionary of interface information
    """
    interface_info = {}
    
    # Extract current interface
    interface_match = re.search(r"interface: ([\w\s]+)", screen_text.lower())
    if interface_match:
        interface_info["current"] = interface_match.group(1).strip()
    
    # Extract dialog information
    if "dialog:" in screen_text.lower():
        dialog_start = screen_text.lower().find("dialog:")
        dialog_end = screen_text.find("\n\n", dialog_start)
        if dialog_end == -1:
            dialog_end = len(screen_text)
        
        dialog_text = screen_text[dialog_start:dialog_end]
        interface_info["dialog"] = dialog_text.strip()
    
    # Extract menu options
    if "menu:" in screen_text.lower():
        menu_start = screen_text.lower().find("menu:")
        menu_end = screen_text.find("\n\n", menu_start)
        if menu_end == -1:
            menu_end = len(screen_text)
        
        menu_text = screen_text[menu_start:menu_end]
        options = []
        for line in menu_text.split("\n"):
            if line.strip().startswith("-"):
                options.append(line.strip()[2:])
        interface_info["menu_options"] = options
    
    return interface_info

# Test the parser
if __name__ == "__main__":
    test_cases = [
        "Talk to the Gielinor Guide to begin.",
        "You can now open the door and head outside.",
        "Chop down a tree.",
        "Click on the inventory icon.",
        "Speak to the Master Chef about cooking.",
        "Mine the copper ore.",
        "Walk to the bank.",
        "Attack the goblin.",
        "Open your prayer tab.",
        "Click here to continue."
    ]
    
    for test in test_cases:
        intent = parse_screen_text(test)
        print(f"Input: '{test}'")
        print(f"Intent: '{intent}'")
        print("-" * 50) 