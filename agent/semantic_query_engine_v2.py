"""
Semantic Query Engine V2 for RuneGPT
Handles semantic search and querying of all OSRS wiki content
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import logging
import re
from collections import defaultdict
import fnmatch
import math

logger = logging.getLogger(__name__)

class SemanticQueryEngineV2:
    """
    Enhanced semantic query engine that handles all OSRS wiki content.
    Uses pre-processed wiki data to answer questions and provide information.
    """
    
    # Common words to ignore
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "must", "can", "could", "what", "where",
        "when", "why", "how", "which", "who", "whom", "whose", "that", "this",
        "these", "those", "there", "here", "now", "then", "just", "very"
    }
    
    # Term importance multipliers
    TERM_IMPORTANCE = {
        "level": 2.0,
        "require": 2.0,
        "need": 2.0,
        "skill": 1.5,
        "experience": 1.5,
        "xp": 1.5,
        "quest": 1.5,
        "item": 1.5,
        "equipment": 1.5,
        "location": 1.5,
        "stats": 2.0,
        "bonus": 2.0,
        "bonuses": 2.0,
        "best": 1.8,
        "strongest": 1.8,
        "powerful": 1.8,
        "requirements": 2.0,
        "defence": 1.5,
        "attack": 1.5,
        "strength": 1.5,
        "magic": 1.5,
        "ranged": 1.5,
        "prayer": 1.5
    }
    
    # Category-specific query patterns
    CATEGORY_PATTERNS = {
        "quests": [
            r"(?:how|what) (?:do|can|are|is) (?:i|the) (?:complete|finish|do|start|requirements|rewards|steps|guide|walkthrough) (?:for )?(?:the )?(?P<quest>[\w\s]+)(?: quest)?",
            r"where (?:do|can) i (?:find|get|obtain|begin|start) (?:the )?(?P<quest>[\w\s]+)(?: quest)?",
            r"what (?:do|should|items) (?:do )?i (?:need|wear|bring|use|have) (?:for|to start|to complete) (?:the )?(?P<quest>[\w\s]+)(?: quest)?",
            r"how (?:do|can) i (?:solve|get past|complete|finish) (?:the )?(?P<puzzle>[\w\s]+) (?:in|during|for) (?:the )?(?P<quest>[\w\s]+)(?: quest)?",
            r"what (?:level|levels|skills|requirements) (?:do )?i need (?:for|to start|to complete) (?:the )?(?P<quest>[\w\s]+)(?: quest)?"
        ],
        "bestiary": [
            r"where (?:do|can) i (?:find|kill|fight) .*",
            r"what (?:are|is) the (?:stats|combat level|drops) of .*",
            r"how (?:much|many) (?:hp|hitpoints|health) does .* have",
            r"what (?:is|are) the (?:weaknesses|strengths) of .*",
            r"what (?:is|are) the (?:drop rates|drops) for .*"
        ],
        "items": [
            r"what (?:does|is) .* (?:do|used for)",
            r"where (?:do|can) i (?:get|find|buy) .*",
            r"how (?:much|many) (?:does|do) .* (?:cost|costs)",
            r"what (?:are|is) the (?:stats|requirements) for .*",
            r"what (?:is|are) the (?:effects|benefits) of .*"
        ],
        "skills": [
            # Woodcutting specific patterns
            r"what level (?:do|can) i (?:cut|chop|need for) (?:down )?(?:a )?(?P<tree>\w+)(?: tree)?s?",
            r"where (?:do|can) i find (?:a )?(?P<tree>\w+)(?: tree)?s?",
            r"what (?:is|are) the best (?:tree|trees) to cut at level (?P<level>\d+)",
            r"how much xp (?:do|does) (?:a )?(?P<tree>\w+)(?: tree)? give",
            r"what (?:is|are) the requirements for (?:the )?woodcutting guild",
            r"what (?:is|are) the best (?:axe|axes) for woodcutting",
            r"how (?:do|can) i train woodcutting",
            r"what (?:is|are) the fastest (?:way|method) to train woodcutting",
            r"what (?:is|are) the best (?:locations?|spots?) (?:for|to) (?:cut|chop) (?:a )?(?P<tree>\w+)(?: tree)?s?",
            r"what (?:is|are) the (?:requirements?|levels?) (?:for|to use) (?:a )?(?P<axe>\w+)(?: axe)?",
            # General skill patterns
            r"how (?:do|can) i train .*",
            r"what (?:is|are) the (?:best|fastest) (?:way|method) to train .*",
            r"what level (?:do|can) i .* at",
            r"how much xp (?:do|does) .* give",
            r"what (?:are|is) the (?:requirements|items needed) for .*"
        ],
        "minigames": [
            r"how (?:do|can) i (?:play|start|enter) .*",
            r"what (?:are|is) the (?:rewards|requirements) for .*",
            r"where (?:is|can i find) the .* (?:minigame|area)",
            r"what (?:do|should) i (?:wear|bring) for .*",
            r"how (?:do|can) i (?:get|obtain) .* from .*"
        ],
        "equipment": [
            r"what (?:are|is) the (?:stats|bonuses) of .*",
            r"what (?:are|is) the (?:requirements|level needed) for .*",
            r"where (?:do|can) i (?:get|find|buy) .*",
            r"how (?:much|many) (?:does|do) .* (?:cost|costs)",
            r"what (?:is|are) the (?:effects|benefits) of .*",
            r"what (?:is|are) the best (?:.*) for (?:melee|ranged|magic)",
            r"what (?:is|are) the best (?:boots|helmet|body|legs|weapon|shield|cape|gloves|amulet|ring) for .*",
            r"can (?:i|you) wear (?:a )?(?:shield|defender) with (?:a )?(?:godsword|two-handed weapon)",
            r"what (?:stats|bonuses) does (?:a )?(?:berserker ring|dragon boots|abyssal whip) give",
            r"what (?:level|levels) (?:do|can) i (?:need|require) for (?:a )?(?:dragon boots|abyssal whip|bandos chestplate)"
        ],
        "npcs": [
            r"where (?:is|can i find) .*",
            r"what (?:does|is) .* (?:do|used for)",
            r"what (?:are|is) the (?:requirements|items needed) for .*",
            r"how (?:do|can) i (?:talk|speak) to .*",
            r"what (?:are|is) the (?:rewards|benefits) of .*"
        ],
        "transportation": [
            r"how (?:do|can) i (?:get|travel) to .*",
            r"where (?:is|can i find) the .* (?:teleport|transport)",
            r"what (?:are|is) the (?:requirements|cost) for .*",
            r"what (?:are|is) the (?:locations|destinations) of .*",
            r"how (?:much|many) (?:does|do) .* (?:cost|costs)"
        ]
    }
    
    WOODCUTTING_TERMS = {
        'tree': 2.0,
        'axe': 1.8,
        'chop': 1.5,
        'cut': 1.5,
        'log': 1.5,
        'woodcutting': 2.0,
        'guild': 1.8,
        'experience': 1.2,
        'xp': 1.2,
        'level': 1.5,
        'requirement': 1.5,
        'location': 1.2,
        'spot': 1.2
    }

    TREE_TYPES = {
        'normal': 1.0,
        'oak': 1.2,
        'willow': 1.3,
        'maple': 1.4,
        'yew': 1.5,
        'magic': 1.6,
        'redwood': 1.6,
        'teak': 1.4,
        'mahogany': 1.4
    }

    AXE_TYPES = {
        'bronze': 1.0,
        'iron': 1.1,
        'steel': 1.2,
        'black': 1.2,
        'mithril': 1.3,
        'adamant': 1.4,
        'rune': 1.5,
        'dragon': 1.6,
        'crystal': 1.6,
        'infernal': 1.6
    }
    
    # Equipment slot mapping
    EQUIPMENT_SLOTS = {
        'head': ['helmet', 'hat', 'hood', 'mask', 'coif'],
        'cape': ['cape', 'cloak'],
        'neck': ['amulet', 'necklace', 'scarf'],
        'ammunition': ['arrows', 'bolts', 'darts'],
        'weapon': ['sword', 'scimitar', 'whip', 'bow', 'staff', 'wand', 'dagger', 'mace', 'spear', 'axe', 'hammer', 'godsword'],
        'shield': ['shield', 'defender', 'book', 'orb'],
        'body': ['platebody', 'chestplate', 'robe top', 'torso', 'shirt'],
        'legs': ['platelegs', 'chaps', 'skirt', 'robe bottom', 'tassets'],
        'hands': ['gloves', 'bracers', 'vambraces', 'gauntlets'],
        'feet': ['boots', 'shoes'],
        'ring': ['ring']
    }
    
    # Equipment-specific terms with weights
    EQUIPMENT_TERMS = {
        'head': 2.0,
        'body': 2.0,
        'legs': 2.0,
        'feet': 2.0,
        'hands': 2.0,
        'cape': 2.0,
        'neck': 2.0,
        'ring': 2.0,
        'weapon': 2.0,
        'shield': 2.0,
        'ammunition': 2.0,
        'helmet': 1.8,
        'boots': 1.8,
        'gloves': 1.8,
        'amulet': 1.8,
        'platebody': 1.8,
        'platelegs': 1.8,
        'robes': 1.8,
        'defender': 1.8,
        'godsword': 1.8,
        'whip': 1.8,
        'scimitar': 1.8,
        'axe': 1.8,
        'staff': 1.8,
        'bow': 1.8,
        'crossbow': 1.8,
        'arrows': 1.8,
        'bolts': 1.8,
        'melee': 1.5,
        'ranged': 1.5,
        'magic': 1.5,
        'attack': 1.5,
        'strength': 1.5,
        'defence': 1.5,
        'prayer': 1.5,
        'requirements': 1.5,
        'level': 1.5,
        'bonus': 1.5,
        'stats': 1.5
    }
    
    # Equipment-specific query patterns
    EQUIPMENT_PATTERNS = {
        "head": [
            r"what (?:is|are) the best (?:helmet|hat|head|headgear) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:helmet|hat|head|headgear) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:helmet|hat|head|headgear)"
        ],
        "body": [
            r"what (?:is|are) the best (?:body|chestplate|platebody|robes) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:body|chestplate|platebody|robes) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:body|chestplate|platebody|robes)"
        ],
        "legs": [
            r"what (?:is|are) the best (?:legs|platelegs|tassets|chaps) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:legs|platelegs|tassets|chaps) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:legs|platelegs|tassets|chaps)"
        ],
        "feet": [
            r"what (?:is|are) the best (?:boots|shoes|feet) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:boots|shoes|feet) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:boots|shoes|feet)"
        ],
        "hands": [
            r"what (?:is|are) the best (?:gloves|gauntlets|hands) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:gloves|gauntlets|hands) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:gloves|gauntlets|hands)"
        ],
        "cape": [
            r"what (?:is|are) the best (?:cape|cloak) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:cape|cloak) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:cape|cloak)"
        ],
        "neck": [
            r"what (?:is|are) the best (?:amulet|necklace|neck) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:amulet|necklace|neck) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:amulet|necklace|neck)"
        ],
        "ring": [
            r"what (?:is|are) the best (?:ring) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:ring) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:ring)"
        ],
        "weapon": [
            r"what (?:is|are) the best (?:weapon|sword|scimitar|whip|staff|bow) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:weapon|sword|scimitar|whip|staff|bow) (?:should|do) i (?:use|wield) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:weapon|sword|scimitar|whip|staff|bow)"
        ],
        "shield": [
            r"what (?:is|are) the best (?:shield|defender) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:shield|defender) (?:should|do) i (?:wear|use) (?:for|in) (?:melee|ranged|magic)",
            r"what (?:is|are) the (?:stats|bonuses) of (?:the )?(?P<item>[\w\s]+) (?:shield|defender)"
        ]
    }
    
    # Add more specific equipment slot patterns
    EQUIPMENT_SLOT_PATTERNS = {
        'head': r'(helmet|hat|hood|coif|head|headgear)',
        'body': r'(body|chestplate|platebody|hauberk|top)',
        'legs': r'(legs|platelegs|chaps|bottom)',
        'feet': r'(boots|shoes|sandals|feet)',
        'hands': r'(gloves|gauntlets|vambraces|hands)',
        'cape': r'(cape|cloak|back)',
        'neck': r'(necklace|amulet|neck)',
        'ring': r'(ring|band)',
        'weapon': r'(weapon|sword|scimitar|whip|staff|bow|crossbow)',
        'shield': r'(shield|defender|book|offhand)'
    }

    # Add equipment slot-specific scoring boosts
    EQUIPMENT_SLOT_BOOSTS = {
        'head': 2.0,
        'body': 2.0,
        'legs': 2.0,
        'feet': 2.0,
        'hands': 2.0,
        'cape': 2.0,
        'neck': 2.0,
        'ring': 2.0,
        'weapon': 2.0,
        'shield': 2.0
    }
    
    COMBAT_STYLES = {
        'melee': ['attack', 'strength', 'defence', 'slash', 'stab', 'crush'],
        'ranged': ['ranged', 'archery', 'ammunition'],
        'magic': ['magic', 'spellcasting', 'mystic']
    }
    
    def __init__(self, wiki_data_dir: str = "wiki_data"):
        """
        Initialize the semantic query engine.
        
        Args:
            wiki_data_dir: Directory containing wiki data files
        """
        self.wiki_data_dir = Path(wiki_data_dir)
        self.data = self._load_wiki_data()
        self.category_index = self._build_category_index()
        logger.info("Initialized semantic query engine v2")
    
    def _load_wiki_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all wiki data from files.
        
        Returns:
            Dictionary containing wiki data by category
        """
        data = {}
        
        # Walk through all directories in wiki_data
        for root, dirs, files in os.walk(self.wiki_data_dir):
            # Skip html directories
            if "html" in root:
                continue
                
            # Get category from path
            rel_path = os.path.relpath(root, self.wiki_data_dir)
            category = rel_path.split(os.sep)[0]
            
            # Initialize category if not exists
            if category not in data:
                data[category] = {}
            
            # Process txt files
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    entry_name = os.path.splitext(file)[0]
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # Parse content into sections
                        sections = self._parse_sections(content)
                        
                        # Store entry data
                        data[category][entry_name] = {
                            "content": content,
                            "sections": sections,
                            "metadata": {
                                "category": category,
                                "subcategory": os.path.relpath(root, os.path.join(self.wiki_data_dir, category)),
                                "filename": file
                            }
                        }
                        
                        # Add equipment slot information if applicable
                        if category in self.EQUIPMENT_SLOTS:
                            data[category][entry_name]["metadata"]["equipment_slot"] = self.EQUIPMENT_SLOTS[category]
                        
                        logger.debug(f"Loaded {category}/{entry_name}")
                        
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
        
        return data
    
    def _build_category_index(self) -> Dict[str, Set[str]]:
        """
        Build an index of categories and their entries.
        
        Returns:
            Dictionary mapping categories to sets of entry names
        """
        index = defaultdict(set)
        
        for category, entries in self.data.items():
            index[category].update(entries.keys())
        
        return index
    
    def _parse_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Parse content into sections based on headers and special markers.
        
        Args:
            content: Raw content to parse
            
        Returns:
            List of dictionaries containing section data
        """
        sections = []
        current_section = {"name": "Overview", "content": []}
        
        # Common section markers
        section_markers = [
            "[edit|edit source]",
            "==",  # Wiki-style headers
            "Requirements",
            "Levels required",
            "Equipment required",
            "Items required",
            "Rewards",
            "Experience",
            "Statistics",
            "Combat stats",
            "Drops",
            "Location",
            "Strategy",
            "Tips",
            "Notes",
            "Trivia",
            "Gallery",
            "References",
            "See also",
            # Woodcutting specific markers
            "Tree types",
            "Trees",
            "Axes",
            "Training",
            "Locations",
            "Guild",
            "Woodcutting Guild",
            "Experience rates",
            "Money making"
        ]
        
        # Split content into lines
        lines = content.split('\n')
        
        for line in lines:
            # Check for section markers
            is_section_marker = False
            new_section = None
            
            # Check for wiki-style headers
            if line.startswith('==') and line.endswith('=='):
                new_section = line.strip('= ')
                is_section_marker = True
            
            # Check for other markers
            for marker in section_markers:
                if marker in line and not line.startswith('*') and not line.startswith('-'):
                    new_section = marker
                    is_section_marker = True
                    break
            
            if is_section_marker and new_section:
                # Save previous section
                if current_section["content"]:
                    current_section["content"] = '\n'.join(current_section["content"]).strip()
                    sections.append(current_section)
                
                # Start new section
                current_section = {"name": new_section, "content": []}
            else:
                current_section["content"].append(line)
        
        # Save last section
        if current_section["content"]:
            current_section["content"] = '\n'.join(current_section["content"]).strip()
            sections.append(current_section)
        
        # Special handling for tree types
        tree_sections = []
        for section in sections:
            content = section["content"]
            # Look for tree information patterns
            tree_matches = re.finditer(r'(?:^|\n)(?:\*|-)\s*(\w+)\s*(?:tree|logs?)?(?:\s*-\s*|\s*:\s*|\s*\(\s*)?(?:level\s*)?(\d+)', content)
            for match in tree_matches:
                tree_name = match.group(1).capitalize()
                level = match.group(2)
                tree_sections.append({
                    "name": f"Tree: {tree_name}",
                    "content": f"Level requirement: {level}\n{content}"
                })
        
        # Add tree sections
        sections.extend(tree_sections)
        
        return sections
    
    def _preprocess_query(self, query: str) -> List[str]:
        # Convert query to lowercase
        query = query.lower()
        
        # Remove stop words
        query_terms = [term for term in query.split() if term not in self.STOP_WORDS]
        
        # Check for equipment slot mentions
        slot_mentioned = None
        for slot, pattern in self.EQUIPMENT_SLOT_PATTERNS.items():
            if re.search(pattern, query):
                slot_mentioned = slot
                break
        
        # Check for combat style mentions
        style_mentioned = None
        for style in ['melee', 'ranged', 'magic']:
            if style in query:
                style_mentioned = style
                break
        
        # Add slot and style to important terms if mentioned
        if slot_mentioned:
            query_terms.append(slot_mentioned)
        if style_mentioned:
            query_terms.append(style_mentioned)
        
        return query_terms
    
    def _score_section(self, section: Dict[str, str], query: str) -> float:
        """
        Score a section based on its relevance to query terms.
        
        Args:
            section: Dictionary containing section data
            query: Original query string
            
        Returns:
            Relevance score for the section
        """
        score = 0.0
        query_lower = query.lower()
        content_lower = section.get('content', '').lower()
        name_lower = section.get('name', '').lower()
        
        # Identify equipment slot and combat style from query
        slot_mentioned = None
        for slot, pattern in self.EQUIPMENT_SLOT_PATTERNS.items():
            if re.search(pattern, query_lower):
                slot_mentioned = slot
                break
        
        style_mentioned = None
        for style in ['melee', 'ranged', 'magic']:
            if style in query_lower:
                style_mentioned = style
                break
        
        # Score based on equipment slot match
        if slot_mentioned:
            if re.search(self.EQUIPMENT_SLOT_PATTERNS[slot_mentioned], name_lower):
                score += self.EQUIPMENT_SLOT_BOOSTS[slot_mentioned] * 2.0
            if re.search(self.EQUIPMENT_SLOT_PATTERNS[slot_mentioned], content_lower):
                score += self.EQUIPMENT_SLOT_BOOSTS[slot_mentioned]
        
        # Score based on combat style match
        if style_mentioned:
            style_bonus = 1.5
            if style_mentioned in name_lower:
                score += style_bonus * 2.0
            if style_mentioned in content_lower:
                score += style_bonus
            
            # Additional boost for style-specific stats
            if style_mentioned == 'melee' and any(term in content_lower for term in ['attack', 'strength', 'slash', 'stab', 'crush']):
                score += style_bonus
            elif style_mentioned == 'ranged' and any(term in content_lower for term in ['ranged', 'ammunition', 'arrows', 'bolts']):
                score += style_bonus
            elif style_mentioned == 'magic' and any(term in content_lower for term in ['magic', 'spell', 'staff', 'runes']):
                score += style_bonus
        
        # Score based on equipment stats presence
        if any(term in content_lower for term in ['bonus', 'requirement', 'stats', 'level']):
            score += 1.0
        
        # Score based on term frequency and importance
        query_terms = self._preprocess_query(query)
        for term in query_terms:
            term_freq = content_lower.count(term)
            score += term_freq * self.TERM_IMPORTANCE.get(term, 1.0)
        
        return score
    
    def _format_result(self, category: str, entry_name: str, section_name: str, content: str) -> str:
        """
        Format a search result for output.
        
        Args:
            category: Category of the result
            entry_name: Name of the entry
            section_name: Name of the section
            content: Content of the section
            
        Returns:
            Formatted result string
        """
        # Clean up content
        content = re.sub(r'\s+', ' ', content).strip()
        content = re.sub(r'\[edit\|edit source\]', '', content)
        
        # Format the result
        result = f"Category: {category}\n"
        result += f"Entry: {entry_name}\n"
        if section_name != "Overview":
            result += f"Section: {section_name}\n"
        result += f"\n{content}\n"
        
        return result
    
    def _get_relevant_categories(self, query: str) -> List[str]:
        """
        Get relevant categories for a query based on patterns.
        
        Args:
            query: Query string
            
        Returns:
            List of relevant categories
        """
        relevant_categories = set()
        
        # Check each category's patterns
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query.lower()):
                    relevant_categories.add(category)
        
        # If no categories match, return all categories
        if not relevant_categories:
            return list(self.data.keys())
        
        return list(relevant_categories)
    
    def query(self, query: str, category: Optional[str] = None, max_results: int = 3) -> str:
        """
        Query the wiki data.
        
        Args:
            query: Query string
            category: Optional category to restrict search to
            max_results: Maximum number of results to return
            
        Returns:
            Most relevant information found
        """
        # Preprocess query
        query_terms = self._preprocess_query(query)
        if not query_terms:
            return "Please provide a more specific query."
        
        # Get relevant categories
        categories_to_search = [category] if category else self._get_relevant_categories(query)
        
        # Track best results
        results = []
        
        for cat in categories_to_search:
            if cat not in self.data:
                continue
            
            # Search through entries in category
            for entry_name, entry_data in self.data[cat].items():
                # Score the entry name
                entry_score = sum(self.TERM_IMPORTANCE.get(term, 1.0) * 10 
                                for term in query_terms 
                                if term in entry_name.lower())
                
                # Find best matching section
                best_section_score = 0
                best_section = None
                
                for section in entry_data["sections"]:
                    section_score = self._score_section(section, query)
                    if section_score > best_section_score:
                        best_section_score = section_score
                        best_section = section
                
                # Combine scores
                total_score = entry_score + best_section_score
                if total_score > 0 and best_section:
                    results.append({
                        "category": cat,
                        "entry_name": entry_name,
                        "section": best_section,
                        "score": total_score
                    })
        
        # Sort results by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Format output
        if not results:
            return "No relevant information found."
        
        output = []
        for result in results[:max_results]:
            output.append(self._format_result(
                result["category"],
                result["entry_name"],
                result["section"]["name"],
                result["section"]["content"]
            ))
        
        return "\n\n---\n\n".join(output)
    
    def get_entry(self, name: str, category: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific entry by name and category.
        
        Args:
            name: Name of the entry
            category: Category of the entry
            
        Returns:
            Entry data if found, None otherwise
        """
        if category not in self.data:
            return None
        return self.data[category].get(name)
    
    def get_categories(self) -> List[str]:
        """
        Get list of available categories.
        
        Returns:
            List of category names
        """
        return list(self.data.keys())
    
    def get_entry_names(self, category: str) -> List[str]:
        """
        Get list of entry names in a category.
        
        Args:
            category: Category to get entries from
            
        Returns:
            List of entry names
        """
        if category not in self.data:
            return []
        return list(self.data[category].keys()) 