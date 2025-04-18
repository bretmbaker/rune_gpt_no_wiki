"""
Semantic Query Engine for RuneGPT
Handles semantic search and querying of OSRS wiki content
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class SemanticQueryEngine:
    """
    Handles semantic search and querying of OSRS wiki content.
    Uses pre-processed wiki data to answer questions and provide information.
    """
    
    def __init__(self, wiki_data_dir: str = "wiki_data"):
        """
        Initialize the semantic query engine.
        
        Args:
            wiki_data_dir: Directory containing wiki data files
        """
        self.wiki_data_dir = Path(wiki_data_dir)
        self.data = self._load_wiki_data()
        self.woodcutting_data = self._load_woodcutting_data()
        logger.info("Initialized semantic query engine")
    
    def _load_woodcutting_data(self) -> Dict[str, Any]:
        """
        Load woodcutting data directly from the Woodcutting.txt file.
        
        Returns:
            Dictionary containing woodcutting data
        """
        woodcutting_data = {
            "content": "",
            "trees": {},
            "axes": {},
            "guild": {},
            "training": {}
        }
        
        woodcutting_file = self.wiki_data_dir / "skills" / "txt" / "Woodcutting.txt"
        if not woodcutting_file.exists():
            logger.warning("Woodcutting.txt file not found")
            return woodcutting_data
        
        try:
            with open(woodcutting_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            woodcutting_data["content"] = content
            
            # Extract tree information from the table format
            tree_section = re.search(r'Types of trees\[edit\|edit source\](.*?)(?=Trees chopped in quests)', content, re.DOTALL)
            if tree_section:
                tree_content = tree_section.group(1)
                tree_entries = re.finditer(r'(\d+)\s*\|[^|]*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)', tree_content)
                
                for match in tree_entries:
                    try:
                        level = match.group(1)
                        tree_name = match.group(2).strip()
                        resource = match.group(3).strip()
                        xp = match.group(4)
                        chop_time = match.group(5).strip()
                        notes = match.group(6).strip()
                        members = match.group(7) == "1"
                        
                        # Clean up tree name
                        tree_name = re.sub(r'\s*\|.*', '', tree_name)  # Remove table formatting
                        tree_name = re.sub(r'\s+tree\s*$', '', tree_name, flags=re.IGNORECASE)  # Remove "tree" suffix
                        
                        if tree_name and tree_name.lower() not in ['light jungle', 'medium jungle', 'dense jungle', 'hollow', 'sulliuscep']:
                            woodcutting_data["trees"][tree_name] = {
                                "level": int(level),
                                "resource": resource,
                                "xp": float(xp),
                                "chop_time": chop_time,
                                "notes": notes,
                                "members": members,
                                "locations": []
                            }
                            
                            # Extract locations from notes
                            location_patterns = [
                                r'found (?:in|at|near|around) ([^\.]+)',
                                r'can be found (?:in|at|near|around) ([^\.]+)',
                                r'found throughout ([^\.]+)',
                                r'trees (?:are|can be found) (?:in|at|near|around) ([^\.]+)',
                                r'found only (?:in|at|near|around) ([^\.]+)'
                            ]
                            
                            for pattern in location_patterns:
                                location_matches = re.finditer(pattern, notes, re.IGNORECASE)
                                for loc_match in location_matches:
                                    locations = loc_match.group(1).split(',')
                                    woodcutting_data["trees"][tree_name]["locations"].extend([loc.strip() for loc in locations])
                            
                            # Clean up locations
                            woodcutting_data["trees"][tree_name]["locations"] = list(set(woodcutting_data["trees"][tree_name]["locations"]))
                            woodcutting_data["trees"][tree_name]["locations"] = [loc for loc in woodcutting_data["trees"][tree_name]["locations"] if loc]
                    except Exception as e:
                        logger.warning(f"Error parsing tree entry: {e}")
                        continue
            
            # Extract axe information from the Equipment section
            axe_section = re.search(r'Axes\[edit\|edit source\](.*?)(?=Felling axes\[edit\|edit source\])', content, re.DOTALL)
            if axe_section:
                axe_content = axe_section.group(1)
                axe_entries = re.finditer(r'(\d+)\s*\|[^|]*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)', axe_content)
                
                for match in axe_entries:
                    try:
                        level = match.group(1)
                        axe_name = match.group(2).strip()
                        description = match.group(3).strip()
                        members = match.group(4) == "1"
                        
                        # Clean up axe name
                        axe_name = re.sub(r'\s*\|.*', '', axe_name)  # Remove table formatting
                        axe_name = re.sub(r'\s+axe\s*$', '', axe_name, flags=re.IGNORECASE)  # Remove "axe" suffix
                        
                        if axe_name:
                            woodcutting_data["axes"][axe_name] = {
                                "level": int(level),
                                "description": description,
                                "members": members
                            }
                    except Exception as e:
                        logger.warning(f"Error parsing axe entry: {e}")
                        continue
            
            # Also extract tree information from the logs section for better coverage
            logs_section = re.search(r'Normal logs\[edit\|edit source\](.*?)(?=Construction logs\[edit\|edit source\])', content, re.DOTALL)
            if logs_section:
                logs_content = logs_section.group(1)
                logs_entries = re.finditer(r'\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*(\d+)\s*\|\s*(\d+)', logs_content)
                
                for match in logs_entries:
                    try:
                        log_name = match.group(1).strip()
                        level = match.group(2)
                        xp = match.group(3)
                        price = match.group(4)
                        members = match.group(5) == "1"
                        
                        # Convert log name to tree name
                        tree_name = log_name.replace(" logs", "").strip()
                        
                        if tree_name and tree_name not in woodcutting_data["trees"]:
                            woodcutting_data["trees"][tree_name] = {
                                "level": int(level),
                                "resource": log_name,
                                "xp": float(xp),
                                "price": int(price),
                                "members": members,
                                "locations": []
                            }
                    except Exception as e:
                        logger.warning(f"Error parsing logs entry: {e}")
                        continue
            
            # Extract guild information
            guild_match = re.search(r'level (\d+) Woodcutting and above.*?Woodcutting Guild', content)
            if guild_match:
                woodcutting_data["guild"] = {
                    "level": int(guild_match.group(1)),
                    "content": "The Woodcutting Guild requires level 60 Woodcutting to enter. It contains a variety of trees and resources for training the Woodcutting skill."
                }
            
            # Extract training information
            training_section = re.search(r'Training\[edit\|edit source\](.*?)(?=\n\n[A-Z])', content, re.DOTALL)
            if training_section:
                woodcutting_data["training"] = {
                    "content": training_section.group(1).strip()
                }
            else:
                # Create a comprehensive training guide from the tree data
                training_guide = ["Woodcutting training guide:"]
                
                # Sort trees by level and XP
                sorted_trees = sorted(woodcutting_data["trees"].items(), key=lambda x: (x[1]["level"], -x[1]["xp"]))
                
                # Group trees by member status
                f2p_trees = []
                p2p_trees = []
                for tree, data in sorted_trees:
                    if data["members"]:
                        p2p_trees.append((tree, data))
                    else:
                        f2p_trees.append((tree, data))
                
                # Add F2P section
                training_guide.append("\nFree-to-Play Training:")
                for tree, data in f2p_trees:
                    locations = ", ".join(data["locations"]) if data["locations"] else "Various locations"
                    training_guide.append(f"Level {data['level']}: Cut {tree} trees for {data['xp']} XP per log")
                    training_guide.append(f"  - Location: {locations}")
                
                # Add P2P section
                training_guide.append("\nMembers-Only Training:")
                for tree, data in p2p_trees:
                    locations = ", ".join(data["locations"]) if data["locations"] else "Various locations"
                    training_guide.append(f"Level {data['level']}: Cut {tree} trees for {data['xp']} XP per log")
                    training_guide.append(f"  - Location: {locations}")
                
                woodcutting_data["training"] = {
                    "content": "\n".join(training_guide)
                }
            
            logger.info(f"Loaded woodcutting data with {len(woodcutting_data['trees'])} trees and {len(woodcutting_data['axes'])} axes")
            logger.debug(f"Tree names: {list(woodcutting_data['trees'].keys())}")
            logger.debug(f"Axe names: {list(woodcutting_data['axes'].keys())}")
            
        except Exception as e:
            logger.error(f"Error loading woodcutting data: {e}")
        
        return woodcutting_data
    
    def _load_wiki_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load wiki data from files.
        
        Returns:
            Dictionary containing wiki data by category
        """
        data = {}
        
        # Define categories to load
        categories = [
            "quests",
            "skills",
            "items",
            "npcs",
            "locations",
            "minigames",
            "achievement_diaries",
            "combat_achievements",
            "training_guides",
            "bestiary",
            "equipment",
            "transportation"
        ]
        
        for category in categories:
            category_dir = self.wiki_data_dir / category
            if not category_dir.exists():
                logger.warning(f"Category directory not found: {category}")
                continue
            
            # Load metadata
            metadata_file = category_dir / "metadata.json"
            if not metadata_file.exists():
                logger.warning(f"Metadata file not found for category: {category}")
                continue
            
            try:
                # Load metadata with UTF-8 encoding
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                
                # Load text files referenced in metadata
                category_data = {}
                
                # Handle different metadata structures
                if isinstance(metadata, dict):
                    if any(isinstance(v, dict) and "txt" in v for v in metadata.values()):
                        # Structure: {name: {txt: path, ...}}
                        for entry_name, entry_data in metadata.items():
                            if isinstance(entry_data, dict) and "txt" in entry_data:
                                txt_path = entry_data["txt"]
                                txt_file = category_dir / txt_path
                                if txt_file.exists():
                                    try:
                                        with open(txt_file, "r", encoding="utf-8") as f:
                                            content = f.read()
                                        category_data[entry_name] = {
                                            "content": content,
                                            "metadata": entry_data,
                                            "sections": self._parse_sections(content)
                                        }
                                    except UnicodeDecodeError:
                                        # Try with a different encoding if UTF-8 fails
                                        with open(txt_file, "r", encoding="latin-1") as f:
                                            content = f.read()
                                        category_data[entry_name] = {
                                            "content": content,
                                            "metadata": entry_data,
                                            "sections": self._parse_sections(content)
                                        }
                    else:
                        # Structure: {name: {...}}
                        for entry_name, entry_data in metadata.items():
                            txt_file = category_dir / "txt" / f"{entry_name}.txt"
                            if txt_file.exists():
                                try:
                                    with open(txt_file, "r", encoding="utf-8") as f:
                                        content = f.read()
                                    category_data[entry_name] = {
                                        "content": content,
                                        "metadata": entry_data,
                                        "sections": self._parse_sections(content)
                                    }
                                except UnicodeDecodeError:
                                    # Try with a different encoding if UTF-8 fails
                                    with open(txt_file, "r", encoding="latin-1") as f:
                                        content = f.read()
                                    category_data[entry_name] = {
                                        "content": content,
                                        "metadata": entry_data,
                                        "sections": self._parse_sections(content)
                                    }
                
                data[category] = category_data
                logger.info(f"Loaded {len(category_data)} entries for category: {category}")
                
            except Exception as e:
                logger.error(f"Error loading data for category {category}: {e}")
        
        return data

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse content into sections based on headers and special markers."""
        sections = {}
        current_section = "Overview"
        current_content = []
        
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
            # Add woodcutting-specific markers
            "Tree types",
            "Trees",
            "Axes",
            "Training",
            "Locations",
            "Guild",
            "Woodcutting Guild",
            "Experience rates",
            "Money making",
            "Quests",
            "Achievements"
        ]
        
        # Split content into lines
        lines = content.split("\n")
        
        # First pass: identify section headers
        for i, line in enumerate(lines):
            # Check for section markers
            is_section = False
            for marker in section_markers:
                if marker in line:
                    if current_content:
                        sections[current_section] = "\n".join(current_content).strip()
                    current_section = line.split(marker)[0].strip()
                    if not current_section:
                        current_section = line.strip()
                    current_content = []
                    is_section = True
                    break
            
            # Special handling for woodcutting tree types
            if "Tree types" in line or "Trees" in line:
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "Tree Types"
                current_content = []
                is_section = True
            
            # Special handling for woodcutting axes
            if "Axes" in line:
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "Axes"
                current_content = []
                is_section = True
            
            # Special handling for woodcutting guild
            if "Woodcutting Guild" in line:
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "Woodcutting Guild"
                current_content = []
                is_section = True
            
            if not is_section:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()
        
        # Second pass: look for tree-specific information
        tree_section = ""
        for section_name, section_content in sections.items():
            if "Tree types" in section_name or "Trees" in section_name:
                tree_section = section_content
                break
        
        if tree_section:
            # Extract tree information
            tree_info = {}
            current_tree = None
            tree_content = []
            
            for line in tree_section.split("\n"):
                # Look for tree names (usually followed by level requirements)
                if re.search(r"(Normal|Oak|Willow|Maple|Yew|Magic|Redwood|Teak|Mahogany|Arctic pine|Crystal|Blighted|Elder|Cursed|Dramen|Achey|Hollow|Karamja|Jungle|Ivy|Celastrus|Redwood) (tree|logs)", line, re.IGNORECASE):
                    if current_tree and tree_content:
                        tree_info[current_tree] = "\n".join(tree_content)
                    current_tree = line.strip()
                    tree_content = []
                elif current_tree:
                    tree_content.append(line)
            
            if current_tree and tree_content:
                tree_info[current_tree] = "\n".join(tree_content)
            
            # Add tree information to sections
            for tree_name, tree_content in tree_info.items():
                sections[f"Tree: {tree_name}"] = tree_content
        
        return sections

    def _preprocess_query(self, query: str) -> Tuple[set, Dict[str, float]]:
        """
        Preprocess the query to extract key terms and weights.
        
        Returns:
            Tuple of (query terms, term weights)
        """
        # Common words to ignore
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        
        # Term importance multipliers with enhanced tree/woodcutting focus
        importance = {
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
            "where": 1.5,
            # Added weights for tree-related terms
            "tree": 2.0,
            "log": 1.8,
            "wood": 1.8,
            "woodcutting": 2.0,
            "chop": 1.8,
            "axe": 1.5,
            "guild": 1.5
        }
        
        # Extract terms and normalize
        terms = set()
        weights = defaultdict(float)
        
        # Split on spaces and punctuation
        query_terms = re.findall(r'\w+', query.lower())
        
        for term in query_terms:
            if term not in stop_words:
                terms.add(term)
                # Check for compound terms (e.g. "magic tree")
                if len(terms) >= 2:
                    prev_term = list(terms)[-2]
                    compound = f"{prev_term} {term}"
                    if compound in ["magic tree", "yew tree", "maple tree", "oak tree", "willow tree"]:
                        terms.add(compound)
                        weights[compound] = 2.5  # Higher weight for specific tree types
                
                # Apply importance multiplier
                weights[term] = importance.get(term, 1.0)
        
        return terms, weights

    def _score_section(self, section_name: str, content: str, query_terms: set, term_weights: Dict[str, float]) -> float:
        """
        Score a section based on query terms and weights.
        Enhanced to better handle tree and woodcutting related queries.
        """
        score = 0.0
        content_lower = content.lower()
        section_lower = section_name.lower()
        
        # Score based on section name relevance
        if any(term in section_lower for term in ["tree", "log", "woodcutting", "equipment", "axe", "guild"]):
            score += 0.5
        
        # Special handling for tree-specific sections
        if section_name.startswith("Tree: "):
            tree_name = section_name[6:].lower()
            # Boost score if query is about this specific tree
            for term in query_terms:
                if term in tree_name:
                    score += 2.0
        
        # Score based on term presence and frequency
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in content_lower:
                # Base score from term weight
                term_score = term_weights.get(term_lower, 1.0)
                
                # Boost score if term appears in level requirements
                if re.search(rf"level.*{term_lower}|{term_lower}.*level", content_lower):
                    term_score *= 1.5
                
                # Boost score if term appears in location information
                if re.search(rf"found.*{term_lower}|{term_lower}.*found", content_lower):
                    term_score *= 1.3
                
                # Boost score if term appears in experience information
                if re.search(rf"experience.*{term_lower}|{term_lower}.*experience|xp.*{term_lower}|{term_lower}.*xp", content_lower):
                    term_score *= 1.4
                
                # Count term frequency
                frequency = content_lower.count(term_lower)
                # Diminishing returns on frequency
                score += term_score * (1 + (frequency - 1) * 0.2)
        
        # Boost score if section contains relevant numerical information
        if re.search(r"level \d+|experience \d+|\d+ xp", content_lower):
            score *= 1.2
        
        # Special handling for woodcutting guild queries
        if "guild" in query_terms and "woodcutting guild" in content_lower:
            score *= 1.5
        
        # Special handling for axe queries
        if "axe" in query_terms and "axe" in content_lower:
            score *= 1.3
        
        return score

    def _format_result(self, category: str, entry_name: str, section_name: str, content: str) -> str:
        """Format a search result for output."""
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

    def query_woodcutting(self, query: str) -> str:
        """
        Specialized query method for woodcutting-related queries.
        
        Args:
            query: Query string
            
        Returns:
            Relevant woodcutting information
        """
        query_lower = query.lower()
        
        try:
            # Check for tree level queries
            tree_level_match = re.search(r"(?:level|levels?).*?(?:for|to cut) (?:the )?([a-z ]+?)(?:tree|logs)?(?:\s|$)", query_lower)
            if tree_level_match:
                tree_name = tree_level_match.group(1).strip()
                for tree, data in self.woodcutting_data["trees"].items():
                    if tree.lower() in tree_name or tree_name in tree.lower():
                        return f"Level {data['level']} is required to cut {tree} trees. You will receive {data['xp']} XP per log."
            
            # Check for tree location queries
            tree_location_match = re.search(r"where.*?(?:find|get|cut|chop).*?([a-z ]+?)(?:tree|logs)?(?:\s|$)", query_lower)
            if tree_location_match:
                tree_name = tree_location_match.group(1).strip()
                for tree, data in self.woodcutting_data["trees"].items():
                    if tree.lower() in tree_name or tree_name in tree.lower():
                        locations = ", ".join(data["locations"]) if data["locations"] else "Various locations throughout Gielinor"
                        return f"{tree} trees can be found in {locations}."
            
            # Check for axe queries
            if "axe" in query_lower and ("best" in query_lower or "highest" in query_lower):
                best_axe = None
                best_level = 0
                for axe, data in self.woodcutting_data["axes"].items():
                    level = data["level"]
                    if level > best_level:
                        best_level = level
                        best_axe = axe
                
                if best_axe:
                    return f"The {best_axe} axe is the best axe for woodcutting, requiring level {best_level} to use."
            
            # Check for guild queries
            if "guild" in query_lower:
                if "level" in query_lower or "require" in query_lower:
                    return f"The Woodcutting Guild requires level {self.woodcutting_data['guild'].get('level', 60)} to enter."
                else:
                    return f"The Woodcutting Guild: {self.woodcutting_data['guild'].get('content', 'A special guild for woodcutters.')}"
            
            # Check for training queries
            if any(term in query_lower for term in ["train", "fastest", "best way", "efficient"]):
                if "training" in self.woodcutting_data and "content" in self.woodcutting_data["training"]:
                    return f"Training woodcutting: {self.woodcutting_data['training']['content']}"
                else:
                    # Provide a general training guide based on tree data
                    training_guide = []
                    for tree, data in sorted(self.woodcutting_data["trees"].items(), key=lambda x: x[1]["level"]):
                        if not data["members"]:  # Only include F2P trees
                            training_guide.append(f"Level {data['level']}: Cut {tree} trees for {data['xp']} XP per log")
                    return "Woodcutting training guide:\n" + "\n".join(training_guide)
            
            # Check for XP queries
            xp_match = re.search(r"(?:xp|experience).*?(?:from|for|cutting).*?([a-z ]+?)(?:tree|logs)?(?:\s|$)", query_lower)
            if xp_match:
                tree_name = xp_match.group(1).strip()
                for tree, data in self.woodcutting_data["trees"].items():
                    if tree.lower() in tree_name or tree_name in tree.lower():
                        return f"You receive {data['xp']} XP per {tree} log."
            
            # Check for best tree at level queries
            level_match = re.search(r"best.*?(?:tree|logs?).*?(?:at )?level (\d+)", query_lower)
            if level_match:
                target_level = int(level_match.group(1))
                best_tree = None
                best_xp = 0
                for tree, data in self.woodcutting_data["trees"].items():
                    if data["level"] <= target_level and data["xp"] > best_xp:
                        best_tree = tree
                        best_xp = data["xp"]
                
                if best_tree:
                    return f"At level {target_level}, the best tree to cut is {best_tree} trees, giving {best_xp} XP per log."
            
        except Exception as e:
            logger.error(f"Error processing woodcutting query: {e}")
        
        # Default response
        return "I couldn't find specific information about that woodcutting query. Try asking about tree levels, locations, axes, the Woodcutting Guild, or training methods."
    
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
        # Check if this is a woodcutting query
        woodcutting_terms = ["woodcutting", "tree", "log", "axe", "woodcut", "chop", "yew", "oak", "willow", "maple", "magic"]
        if any(term in query.lower() for term in woodcutting_terms):
            return self.query_woodcutting(query)
        
        # Preprocess query
        query_terms, term_weights = self._preprocess_query(query)
        if not query_terms:
            return "Please provide a more specific query."
        
        # Track best results
        results = []
        categories_to_search = [category] if category else self.data.keys()
        
        for cat in categories_to_search:
            if cat not in self.data:
                continue
            
            # Search through entries in category
            for entry_name, entry_data in self.data[cat].items():
                # Score the entry name
                entry_score = sum(term_weights[term] * 10 
                                for term in query_terms 
                                if term in entry_name.lower())
                
                # Find best matching section
                best_section_score = 0
                best_section_name = ""
                best_section_content = ""
                
                for section_name, content in entry_data["sections"].items():
                    section_score = self._score_section(
                        section_name, content, query_terms, term_weights
                    )
                    if section_score > best_section_score:
                        best_section_score = section_score
                        best_section_name = section_name
                        best_section_content = content
                
                # Combine scores
                total_score = entry_score + best_section_score
                if total_score > 0:
                    results.append({
                        "category": cat,
                        "entry_name": entry_name,
                        "section_name": best_section_name,
                        "content": best_section_content,
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
                result["section_name"],
                result["content"]
            ))
        
        return "\n\n---\n\n".join(output)

    def get_entry(self, name: str, category: str) -> Optional[Dict[str, Any]]:
        """Get a specific entry by name and category."""
        if category not in self.data:
            return None
        return self.data[category].get(name)
    
    def get_categories(self) -> List[str]:
        """Get list of available categories."""
        return list(self.data.keys())
    
    def get_entry_names(self, category: str) -> List[str]:
        """Get list of entry names in a category."""
        if category not in self.data:
            return []
        return list(self.data[category].keys()) 